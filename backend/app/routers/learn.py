"""引导式学习路由：按顺序解锁知识点，写完代码点运行，判定通过才进下一个。

判定放在服务端做（而不是前端），这样：
- 判定逻辑和「给定的预置数据」不会泄漏到浏览器里；
- 每组用例都会换一组输入再跑一遍，防止把答案直接 print 出来蒙过去。

解锁是**按科目独立**的：每个科目的第一课默认解锁，本科目上一课通过才解锁下一课；
科目之间互不阻塞（学 Python 卡住了，不影响去学 MySQL）。
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import client as ai
from ..database import get_db
from ..learn_video import load_videos
from ..models import LearnProgress, User, now
from ..schemas import (LearnCheckIn, LearnCheckOut, LearnHintIn, LearnHintOut,
                       LearnPointBrief, LearnPointDetail, LearnQuizItem,
                       LearnQuizResult, LearnQuizSubmitIn, LearnResume,
                       MindMapBranch, MindMapItem, MindMapSubject,
                       QBankItem, QBankLesson, QBankModule, QBankSubject)
from ..security import get_current_user
from ..seed.learn import BY_CODE, BY_SUBJECT, SUBJECTS, next_code
from ..seed.learn_video_bili import SERIES as BILI_SERIES, VIDEO as BILI_VIDEO
from ..seed.learn_mindmap import MINDMAPS
from ..seed.learn_roadmap import ROADMAP
from ..seed.learn_sketch import sketch_of
from ..services import growth, sql_runner
from ..services.code_runner import run_python

# 讲解视频脚本是构建期产物，启动时读一次常驻内存（394KB，解析几毫秒）。
# ⚠️ 重新跑 build_lesson_videos.py 之后要重启后端才生效 —— 和改 seed 一样，
#    reload 不会因为一个 json 变化就重载。
VIDEOS: dict = load_videos()


def _sketch(code: str) -> dict | None:
    """取某课的手绘知识图；没铺到就返回 None（前端不渲染这块）。

    节点上如果写了不存在的课程 code，就把「可点」摘掉而不是整张图丢掉 ——
    图画错了不该让学生看到一个空区块。
    """
    data = sketch_of(code)
    if not data:
        return None
    nodes = []
    for n in data["nodes"]:
        node = dict(n)
        if node.get("code") and node["code"] not in BY_CODE:
            node["code"] = ""
        nodes.append(node)
    return {"center": data["center"], "nodes": nodes, "edges": data["edges"]}


def _oneliner(code: str) -> str:
    """本课开头的一句话；没铺到的课返回空串，前端退回 summary。"""
    return (sketch_of(code) or {}).get("oneliner", "") or ""


def _bili(code: str) -> dict | None:
    """本课对应的 B站 视频（分 P 级）；没映射到就返回 None。

    只在后端拼好「系列 + 分P + 直链」，前端不重复拼 URL —— 万一以后要换
    player.bilibili.com 的参数（比如加 &t= 时间戳），只改这一处。
    """
    hit = BILI_VIDEO.get(code)
    if not hit:
        return None
    bv, page, part = hit
    series = BILI_SERIES.get(bv) or {}
    return {
        "bvid": bv,
        "page": page,
        "part": part,
        "up": series.get("up", ""),
        "series": series.get("title", ""),
        # isOutside=true 必带：不带的话外站嵌入会提示「该视频无法播放」
        # autoplay=1：iframe 是我们点完封面才挂的，用户手势还在，能直接开播。
        # 写 0 的话播放器只画出 00:00 的静止首帧、播放键是底部一个不起眼的小三角，
        # 用户点完封面以为坏了（2026-11-06 用户报「打不开」实测就是这个）。
        "embed": ("https://player.bilibili.com/player.html"
                  f"?bvid={bv}&page={page}&autoplay=1&danmaku=0"
                  "&high_quality=1&isOutside=true"),
        "url": f"https://www.bilibili.com/video/{bv}?p={page}",
    }


def _bili_fallback(subject: str) -> dict | None:
    """这一科没有逐课映射时的兜底：给该科目的推荐系列（整系列链接）。

    RAG / 后端服务 / 多模态 / AI 工程质量这四科是自编内容，B站 上没有对应
    讲解，前端只能给「系列入口」，不给假视频。
    """
    for bv, info in BILI_SERIES.items():
        if info.get("subject") == subject:
            return {"bvid": bv, "up": info.get("up", ""),
                    "series": info.get("title", ""),
                    "url": f"https://www.bilibili.com/video/{bv}"}
    return None

router = APIRouter(prefix="/api/learn", tags=["learn"])

MAX_CODE = 8 * 1024


# 中文输入法下极易误打的全角符号。只在**真的报语法错**时才提示，
# 因为我们没法可靠区分「字符串里的中文标点」（合法）和「代码里的全角标点」（非法）。
_FULLWIDTH = {
    "（": "(", "）": ")", "“": '"', "”": '"', "‘": "'", "’": "'",
    "：": ":", "，": ",", "；": ";", "【": "[", "】": "]", "。": ".",
    "＝": "=", "　": " ", "！": "!", "？": "?", "＜": "<", "＞": ">",
}


def _fullwidth_hint(code: str, lang: str = "Python") -> str:
    """把引号里的内容去掉后再找全角标点，尽量避免把中文文本误报成符号错误。"""
    stripped = re.sub(r'"[^"\n]*"|\'[^\'\n]*\'', '""', code)
    bad = [c for c in dict.fromkeys(stripped) if c in _FULLWIDTH]
    if not bad:
        return ""
    fixes = "、".join(f"`{c}` 改成 `{_FULLWIDTH[c]}`" for c in bad[:4])
    return (f"\n\n💡 检测到 **中文全角符号**（{fixes}）。"
            f"{lang} 只认英文半角符号，这是最常见的原因之一。")


BUSY_EXIT_CODE = 125


def _run_or_busy(code: str) -> dict:
    """跑一次沙箱；并发名额满了就抛 503，绝不混进「答案判定」。

    `code_runner` 用 exit_code=125 表示没抢到并发名额（服务器忙），不是学生代码的问题。
    如果让它落进下面的判定分支，学生写得全对也会被判错，提示还是「你的代码运行出错」，
    属于最坏的一种误导。宁可让他看到「稍后再试」，也不能给假判定。
    """
    r = run_python(code)
    if r.get("exit_code") == BUSY_EXIT_CODE:
        raise HTTPException(
            503,
            r.get("stderr") or "当前同时运行代码的人有点多，请等几秒再提交",
            headers={"Retry-After": "3"},
        )
    return r


def _runtime_reason(result: dict, code: str = "") -> str:
    """运行失败时给一句新手看得懂的话（超时＝死循环、全角符号，是两个最高频的坑）。"""
    err = result.get("stderr") or ""
    if result.get("exit_code") == 124:
        return ("代码运行超时了（超过 5 秒还没跑完）。多半是**死循环** —— "
                "检查一下循环条件会不会永远为真，比如忘了让计数变量每轮加 1。")
    if "SyntaxError" in err or "IndentationError" in err or "TabError" in err:
        base = ("代码有语法错误，Python 读不懂。看下面的报错信息里最后一行的 "
                "`SyntaxError` / `IndentationError`，它会告诉你第几行有问题。")
        if "IndentationError" in err or "TabError" in err:
            base = ("缩进出问题了。Python 用缩进表示「谁属于谁」，要注意："
                    "同一层代码的缩进必须完全一致（建议统一用 4 个空格，不要混用 Tab）。")
        return base + _fullwidth_hint(code)
    if "NameError" in err:
        return ("用到了一个还没定义的名字。检查变量名是不是拼错了，"
                "或者是不是忘了先给它赋值。")
    if "TypeError" in err:
        return ("类型对不上 —— 最常见的是把字符串和数字混在一起算，"
                "比如 `\"7\" + 1`。先用 `int()` 或 `str()` 转换一下再运算。")
    if "IndexError" in err:
        return "下标越界了。记住下标从 0 开始，长度是 3 的列表合法下标只有 0、1、2。"
    if "KeyError" in err:
        return "字典里没有这个键。先用 `in` 判断一下，或者用 `.get()` 取。"
    return "代码运行报错了，先看下面的错误信息，把报错解决掉再提交。"


def _sql_reason(err: str, sql: str = "") -> str:
    """SQL 执行失败时给一句新手看得懂的话。"""
    e = err or ""
    fw = _fullwidth_hint(sql, lang="SQL")

    if "no such table" in e:
        base = ("用到了不存在的表名。题目里已经给了表结构，检查一下表名有没有写错"
                "（也可以对照左边「题目已给好的代码」里的建表语句）。")
    elif "no such column" in e:
        base = "用到了不存在的列名。对照题目给的列名，检查一下拼写。"
    elif "syntax error" in e or "near" in e:
        base = ("SQL 语法有误 —— 这是最常见的一类错误，多半出在这几处：\n"
                "1. 字符串要用**英文单引号**：`WHERE name = '小明'`；\n"
                "2. 多列之间要加逗号：`SELECT name, score`；\n"
                "3. 子句顺序是 `WHERE` → `GROUP BY` → `HAVING` → `ORDER BY` → `LIMIT`。\n"
                "看下面的报错信息里 `near` 后面跟着的位置，就是出错的地方。")
    elif "incomplete input" in e:
        base = "SQL 没写完 —— 检查是不是少了 `FROM`、括号没闭合，或者引号只写了一半。"
    elif "misuse of aggregate" in e:
        base = ("聚合函数放错位置了。`COUNT`/`SUM`/`MAX` 不能写在 `WHERE` 里，"
                "要筛聚合结果请用 `HAVING`。")
    elif "no such function" in e:
        base = "用到了 SQLite 不支持的函数。先看看题目说明里给出的可用写法。"
    else:
        base = "SQL 执行报错了，先看下面的报错信息，把报错解决掉再提交。"

    # 全角符号很常见、而且报错信息会把人带偏（`“北京”` 会报成 no such column，
    # 让人以为列名写错了），所以只要检测到就直接点出来。
    if fw:
        return fw.strip() + "\n" + base
    return base


def _progress(db: Session, user: User) -> dict[str, LearnProgress]:
    rows = db.query(LearnProgress).filter(LearnProgress.user_id == user.id).all()
    return {r.point_code: r for r in rows}


def _status_of(prog: LearnProgress | None, prev_done: bool) -> str:
    if prog and prog.status == "completed":
        return "completed"
    return "unlocked" if prev_done else "locked"


def _statuses(db: Session, user: User) -> list[tuple[dict, str]]:
    """按科目分别算状态。

    主线：每个科目第一课解锁，本科目上一课通过才解锁下一课。

    补充课（`point["supplementary"]`）：**不参与主线链条** —— 永远可学，
    也不改变它后面那节课的解锁状态。这是为了「后加内容不打断老进度」：
    如果把新增课直接插进链条，学生上次已解锁的那节课会因为
    「它的前一课变成了新加的、还没过」而被重新锁上。
    """
    prog = _progress(db, user)
    out: list[tuple[dict, str]] = []
    for subject in SUBJECTS:
        prev_done = True                      # 每科第一课默认解锁
        for point in BY_SUBJECT[subject]:
            row = prog.get(point["code"])
            if point.get("supplementary"):
                done = bool(row and row.status == "completed")
                out.append((point, "completed" if done else "unlocked"))
                continue                      # 不写回 prev_done，主线链条不受影响
            st = _status_of(row, prev_done)
            out.append((point, st))
            prev_done = st == "completed"
    return out


def _next_unlocked(db: Session, user: User, code: str) -> str | None:
    """下一课的 code，但**必须是这个学生当前就能进的**。

    补充课之间自成一条链（见 `next_code`），而补充课永远解锁，所以正常都会返回；
    这里兜底是为了避免出现「点了下一课却 403」。
    """
    nxt = next_code(code)
    if not nxt:
        return None
    for p, st in _statuses(db, user):
        if p["code"] == nxt:
            return nxt if st != "locked" else None
    return None


OBJECTIVE = ("choice", "judge", "blank")   # 客观题：必须全对
SUBJECTIVE = ("short", "applied")          # 主观题：不阻塞通过，只给对照


def _runner(point: dict) -> str:
    return point.get("runner") or "python"


def _has_task(point: dict) -> bool:
    """这一课有没有「动手写」的题（写代码，或者写 SQL）。"""
    r = _runner(point)
    if r == "none":
        return False
    if r == "sql":
        return bool(point.get("sql_setup"))
    return bool(point.get("checker") or point.get("cases"))


def _blank_match(answer: object, accepted: list) -> bool:
    """填空题判分：先严格比（只忽略空白和大小写），再宽松比（连标点也忽略）。

    不能一上来就去标点 —— 有些题的标准答案**本身就是标点**（比如 `:`、`,`、`/`），
    去掉标点后两边都变成空串，会被误判成答错。

    NFKC 归一化是必须的：手机中文输入法打出来的「１」「：」「（）」是全角，
    和题干里的半角不是一个码位，直接比字符串会把标准答案判成错。
    """
    def norm(s: object) -> str:
        return unicodedata.normalize("NFKC", str(s or ""))

    def soft(s: object) -> str:
        return re.sub(r"\s+", "", norm(s)).lower()

    def hard(s: object) -> str:
        return re.sub(r"[\s,，。、.;；:：!！?？'\"“”‘’()（）]", "", norm(s)).lower()

    got_soft, got_hard = soft(answer), hard(answer)
    for a in accepted:
        if got_soft == soft(a):
            return True
        if got_hard and got_hard == hard(a):
            return True
    return False


def _grade_quiz(q: dict, answer) -> dict:
    """判一道习题。主观题返回 correct=None（不阻塞），只给覆盖率和参考答案。"""
    t = q.get("type")
    if t == "choice":
        idx = q["answer_index"]
        ok = isinstance(answer, int) and answer == idx
        return {"correct": ok, "correct_answer": q["options"][idx],
                "explanation": q.get("explanation", "")}
    if t == "judge":
        ok = bool(answer) == bool(q["answer"])
        return {"correct": ok, "correct_answer": "对" if q["answer"] else "错",
                "explanation": q.get("explanation", "")}
    if t == "blank":
        # ⚠️ 标准答案必须一起进白名单：accept 是「另外还接受的写法」，
        # 不是「替代标准答案的写法」。之前直接 `q.get("accept") or [answer]`，
        # 凡是写了 accept 的题，考生老老实实填标准答案反而判错（线上踩过）。
        accepted = [q["answer"]] + [x for x in (q.get("accept") or []) if x]
        ok = bool(str(answer or "").strip()) and _blank_match(answer, accepted)
        return {"correct": ok, "correct_answer": q["answer"],
                "explanation": q.get("explanation", "")}

    # ---- 主观题：关键词覆盖 + 参考答案，交给学生自己对照 ----
    kws = q.get("keywords") or []
    text = str(answer or "")
    hit = [k for k in kws if k.lower() in text.lower()]
    missing = [k for k in kws if k not in hit]
    return {"correct": None, "coverage": round(len(hit) / len(kws), 2) if kws else 0.0,
            "missing": missing, "reference": q.get("reference", ""),
            "explanation": q.get("explanation", "")}


def _refresh_completion(db: Session, user: User, prog: LearnProgress,
                        point: dict) -> tuple[bool, str | None]:
    """动手题通过 + 客观题全对 ⇒ 这一课完成，返回是否完成与下一个知识点。

    注意：已完成的知识点**不会因为内容更新而回退**，否则会连带把后面已解锁的课重新锁上。
    """
    task_ok = (not _has_task(point)) or bool(prog.code_passed)
    state = prog.quiz_json or {}
    objective = [i for i, q in enumerate(point.get("quizzes") or [])
                 if q.get("type") in OBJECTIVE]
    quiz_ok = all((state.get(str(i)) or {}).get("correct") for i in objective)
    done = task_ok and quiz_ok

    if done and prog.status != "completed":
        prog.status = "completed"
        prog.completed_at = now()
        # ⚠️ 全站唯一的经验来源：每完成一个课时 +10 点（services/growth.py 文件头）。
        # 只在这一处发经验，且只在「从未完成 → 完成」时发一次，
        # 反复刷同一课不会重复拿分（否则刷一门课就能刷满级）。
        if user.character:
            growth.add_exp(db, user.character, growth.LESSON_EXP)
        db.commit()
        growth.check_achievements(db, user)

    nxt = _next_unlocked(db, user, point["code"]) if done else None
    return done, nxt


def _require(db: Session, user: User, code: str) -> dict:
    point = BY_CODE.get(code)
    if not point:
        raise HTTPException(404, "知识点不存在")
    for p, st in _statuses(db, user):
        if p["code"] == code:
            if st == "locked":
                raise HTTPException(403, "先完成前一个知识点再学这个")
            return p
    raise HTTPException(404, "知识点不存在")


@router.get("/points", response_model=list[LearnPointBrief])
def points(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """全部科目、全部知识点的状态。前端按 subject 分 Tab、按 stage 分组展示。"""
    return [LearnPointBrief(code=p["code"], order_no=p["order_no"], title=p["title"],
                            summary=p["summary"], stage=p.get("stage", ""),
                            subject=p["subject"], runner=_runner(p), status=st)
            for p, st in _statuses(db, user)]


def _build_mindmap(subject: str, tree: dict, st: dict[str, str],
                   kind: str = "subject", lesson_total: int = 0) -> MindMapSubject:
    """把 seed 里的裸 dict 转成响应模型，顺带算覆盖率和必问数。

    code 写错就摘掉「可点」，而不是整棵树报错 —— 图上少一个入口，
    总比让学生看到 500 更合适。
    """
    branches: list[MindMapBranch] = []
    covered: set[str] = set()
    node_total = hot_total = 0
    for br in tree.get("branches") or []:
        items: list[MindMapItem] = []
        for it in br.get("items") or []:
            code = it.get("code")
            p = BY_CODE.get(code) if code else None
            if code and not p:
                code = None
            if p:
                covered.add(code)
            items.append(MindMapItem(name=it["name"], code=code,
                                     kp=it.get("kp", ""), answer=it.get("answer", ""),
                                     hot=it.get("hot", 2),
                                     lesson_title=p["title"] if p else "",
                                     status=st.get(code, "locked"),
                                     kind=it.get("kind", "lesson")))
        node_total += len(items)
        hot_total += sum(1 for x in items if x.hot == 3)
        branches.append(MindMapBranch(name=br["name"], items=items))
    return MindMapSubject(subject=subject, intro=tree.get("intro", ""),
                          branches=branches,
                          lesson_total=lesson_total,
                          lesson_covered=len(covered),
                          node_total=node_total, hot_total=hot_total,
                          kind=kind)


@router.get("/resume", response_model=LearnResume)
def resume(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """上次停留的课时。

    存在 characters.last_point_code（服务端），不是浏览器本地存储 ——
    学生白天在机房电脑上学、晚上用手机接着看，本地存储一换设备就没了。
    记录失效（课程下线/进度被重置后已锁）时返回空对象，前端退回「第一门没学完的」。
    """
    code = (user.character.last_point_code if user.character else "") or ""
    point = BY_CODE.get(code)
    if not point:
        return LearnResume()
    status = next((st for p, st in _statuses(db, user) if p["code"] == code), "locked")
    if status == "locked":
        return LearnResume()
    return LearnResume(code=point["code"], title=point["title"],
                       subject=point["subject"], stage=point.get("stage", ""))


@router.get("/interview-bank", response_model=list[QBankSubject])
def interview_bank(db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """面试考题：按「科目 → 模块（课程阶段）→ 课程 → 题目」组织，和引导式学习同一套结构。

    题目来自 seed/learn_mindmap.py 的考点树：那里的一条考点就等于一道面试题，
    自带标准答案和它对应的课程 code。这里只做重新归组 ——
    按课程阶段分模块、按课程聚合，学生看完题能顺手点进那门课补。

    `code` 为 None 的考点（会考但站内还没课）收进「课程未覆盖」模块，不丢。
    """
    st = {p["code"]: s for p, s in _statuses(db, user)}
    out: list[QBankSubject] = []
    for subject in SUBJECTS:
        tree = MINDMAPS.get(subject) or {}
        lessons: dict[str, QBankLesson] = {}
        loose: list[QBankItem] = []
        for br in tree.get("branches") or []:
            for it in br.get("items") or []:
                item = QBankItem(q=it["name"], kp=it.get("kp", ""),
                                 answer=it.get("answer", ""), hot=it.get("hot", 2))
                code = it.get("code")
                if code and code in BY_CODE:
                    les = lessons.get(code)
                    if les is None:
                        p = BY_CODE[code]
                        les = QBankLesson(code=code, title=p["title"],
                                          order_no=p["order_no"],
                                          status=st.get(code, "locked"))
                        lessons[code] = les
                    les.items.append(item)
                else:
                    loose.append(item)

        # 模块 = 课程阶段。跨科目引用的课（数据结构里引了 RAG 的向量库课）
        # 按它自己所属科目的顺序排，靠 subject 序号 + 科目内序号保证稳定。
        ordered = sorted(lessons.values(),
                         key=lambda x: (SUBJECTS.index(BY_CODE[x.code]["subject"]),
                                        x.order_no))
        modules: list[QBankModule] = []
        index: dict[str, QBankModule] = {}
        for les in ordered:
            stage = BY_CODE[les.code].get("stage") or "其他"
            mod = index.get(stage)
            if mod is None:
                mod = QBankModule(name=stage)
                index[stage] = mod
                modules.append(mod)
            mod.lessons.append(les)
        if loose:
            modules.append(QBankModule(name="课程未覆盖", items=loose))

        total = sum(len(l.items) for m in modules for l in m.lessons) + \
            sum(len(m.items) for m in modules)
        hot_total = sum(1 for m in modules for l in m.lessons for x in l.items if x.hot == 3) + \
            sum(1 for m in modules for x in m.items if x.hot == 3)
        out.append(QBankSubject(subject=subject, intro=tree.get("intro", ""),
                                modules=modules, total=total, hot_total=hot_total,
                                lesson_covered=len(lessons),
                                lesson_total=len(BY_SUBJECT[subject])))
    return out


@router.get("/mindmaps", response_model=list[MindMapSubject])
def mindmaps(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """12 棵面试知识树 + 1 张大学三年路径图，一次全返回。

    数据量很小（约 440 个节点，序列化后 70KB 左右），比「切一次科目请求一次」
    少 12 次往返；前端在科目间切换时也不用等。

    带上每门课的解锁状态：图上点一个 locked 的考点，Learn 页会退回第一课，
    学生看到的是「点了 A 却打开 B」。前端据此拦住并提示先学前面的。

    12 棵科目树排在前面：这个页面的主线是「某一科的知识点长什么样」，
    进来默认停在 Python，而不是先看到学期路径图。
    路径图放最后 —— 它是另一条线（什么时候学什么），需要时再切过去。
    """
    st = {p["code"]: s for p, s in _statuses(db, user)}
    out: list[MindMapSubject] = []
    for subject in SUBJECTS:
        out.append(_build_mindmap(subject, MINDMAPS.get(subject) or {}, st,
                                  lesson_total=len(BY_SUBJECT[subject])))
    out.append(_build_mindmap("大学三年路径", ROADMAP, st, kind="roadmap"))
    return out


@router.get("/points/{code}", response_model=LearnPointDetail)
def point_detail(code: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    point = _require(db, user, code)
    # 记下「当前停在哪一课」：下次进引导式学习直接回到这里。
    # 写在详情接口里而不是单开一个上报接口 —— 打开一课是这个接口唯一的调用场景，
    # 前端每切一次课必然打一次，不会漏记。
    if user.character and user.character.last_point_code != code:
        user.character.last_point_code = code
        db.commit()
    prog = _progress(db, user).get(code)
    # 习题只下发题干和选项，答案与解析留在服务端
    quizzes = [
        LearnQuizItem(index=i, type=q["type"], stem=q["stem"],
                      options=q.get("options") or [], hint=q.get("hint", ""))
        for i, q in enumerate(point.get("quizzes") or [])
    ]
    return LearnPointDetail(
        code=point["code"], order_no=point["order_no"], title=point["title"],
        summary=point["summary"], stage=point.get("stage", ""),
        subject=point["subject"], runner=_runner(point),
        status="completed" if prog and prog.status == "completed" else "unlocked",
        definition=point.get("definition", ""), plain=point.get("plain", ""),
        example=point.get("example", ""), example_output=point.get("example_output", ""),
        pitfalls=point.get("pitfalls") or [], task=point.get("task", ""),
        setup=point.get("setup", ""), starter=point.get("starter", ""),
        hint=point.get("hint", ""),
        last_code=(prog.last_code if prog and prog.last_code else ""),
        has_task=_has_task(point),
        code_passed=bool(prog and prog.code_passed),
        quizzes=quizzes,
        quiz_state=(prog.quiz_json or {}) if prog else {},
        next_code=_next_unlocked(db, user, point["code"]),
        oneliner=_oneliner(point["code"]),
        sketch=_sketch(point["code"]),
        bili=_bili(point["code"]),
        bili_series=_bili_fallback(point["subject"]),
        # 自制动图分镜（video）2026-11-06 起不再返回：视频区已改成播 B站 原片。
        # 数据还在（lesson_videos.json + learn_video.py + schema 字段），
        # 要回滚就把下面这行解开、同时恢复 LessonVideo 的旧组件。
        # video=VIDEOS.get(point["code"]),
        project=point.get("project"),
    )


@router.post("/check", response_model=LearnCheckOut)
def check(body: LearnCheckIn, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    point = _require(db, user, body.code)

    prog = _progress(db, user).get(body.code)
    if prog is None:
        # attempts 要显式给 0：SQLAlchemy 的 default 只在 INSERT 时生效，
        # 新建对象还没落库时字段是 None，直接 += 会报错。
        prog = LearnProgress(user_id=user.id, point_code=body.code, attempts=0)
        db.add(prog)
    prog.attempts = (prog.attempts or 0) + 1
    prog.last_code = body.user_code
    db.commit()

    user_code = body.user_code
    empty_tip = ("编辑器还是空的，先动手写点 SQL 吧。" if _runner(point) == "sql"
                 else "编辑器还是空的，先动手写点代码吧。")
    if not user_code.strip():
        return LearnCheckOut(passed=False, reason=empty_tip, total=0, solved=0)
    if len(user_code.encode("utf-8")) > MAX_CODE:
        return LearnCheckOut(passed=False, reason="太长了，这次练习不需要这么多。", total=0, solved=0)

    solved = 0
    reason = ""
    output = ""
    error = ""

    if _runner(point) == "sql":
        # ---- SQL 科目：跑一遍查询，比对结果集 ----
        total = 1
        res = sql_runner.run_sql(point.get("sql_setup", ""), user_code,
                                 point.get("sql_verify", ""))
        if res.get("setup_error"):
            reason = res["setup_error"]
        elif not res["ok"]:
            error = res["error"]
            if res.get("phase") == "verify":
                # 学生的语句都跑通了，是那条固定校验查询失败 —— 说明"该建的没建出来"。
                # 这里绝不能复用"表名写错了"的提示：学生压根没写过表名，会把人带偏。
                cols = "、".join(point.get("sql_hint_cols") or [])
                reason = (
                    "你写的语句都能正常执行，但**题目要求的表还没按要求建出来**。\n"
                    "这一课要你自己 `CREATE TABLE` 建表、再 `INSERT` 插几行样例数据，"
                    "系统最后会用一条固定查询来检查。\n"
                    + (f"它要查的列是：{cols}。\n" if cols else "")
                    + "常见就两种情况：1. 表根本没建；2. 表建了，但字段名和题目对不上。"
                    "对照左边「题目已给好的代码」里的表结构逐项核对。"
                )
            else:
                reason = _sql_reason(error, user_code)
        else:
            output = sql_runner.format_table(res["cols"], res["rows"])
            expect = point.get("sql_expect") or []
            if sql_runner.compare_rows(res["rows"], expect, bool(point.get("sql_ordered"))):
                solved = 1
            else:
                cols = "、".join(point.get("sql_hint_cols") or []) or "（题目没给）"
                reason = (
                    f"结果不对：期望 **{len(expect)} 行**，你查出来 **{len(res['rows'])} 行**。\n"
                    f"期望的列是：{cols}。\n"
                    "判定不只看内容 —— **行数、列数、行序**都会比。"
                    "多查了字段、少了 WHERE 条件、该排序没排序，都会不通过。"
                    "对照上面的「你的输出」逐行看一遍。"
                )
    else:
        # ---- Python 科目：输出用例 + 断言 ----
        setup = point.get("setup", "")
        cases = point.get("cases") or []
        checker = point.get("checker")
        total = len(cases) + (1 if checker else 0)

        # ---- 一、输出用例：换不同的输入各跑一遍 ----
        for idx, c in enumerate(cases):
            r = _run_or_busy((c.get("setup") or "") + user_code)
            output, error = r["stdout"], r["stderr"]
            if r["exit_code"] != 0:
                reason = _runtime_reason(r, user_code)
                break
            got = r["stdout"].strip()
            want = (c.get("expect_stdout") or "").strip()
            if got == want:
                solved += 1
            else:
                tip = ""
                if not got:
                    tip = "你的代码这次没有输出任何东西 —— 检查是不是漏了 `print(...)`。"
                elif want and want in got:
                    tip = ("你多输出了额外的文字。题目只要求输出那个值本身，"
                           "别写 `print(\"和是\", total)` 这种，直接 `print(total)` 就行。")
                else:
                    tip = ("判定会换一组输入再跑一遍，所以不能直接把答案 print 出来 —— "
                           "要让程序真的算出来。")
                reason = (f"第 {idx + 1} 组数据没通过：期望输出 `{want}`，实际得到 "
                          f"`{got or '（无）'}`。\n{tip}")
                break

        # ---- 二、断言：检查变量/函数是否真的写对 ----
        if not reason and checker:
            # 先单独跑一遍学生的代码。这一步就报错，说明问题出在他自己写的代码上
            # （语法错、名字拼错、死循环），可以给对症的解释。
            solo = _run_or_busy(setup + user_code)
            if solo["exit_code"] != 0:
                reason = _runtime_reason(solo, user_code)
                error, output = solo["stderr"], solo["stdout"]
            else:
                r = _run_or_busy(setup + user_code + "\n\n" + checker)
                raw, error = r["stdout"], r["stderr"]
                output = raw
                if r["exit_code"] != 0:
                    # 学生的代码自己能跑通，却在断言环节炸了 —— 多半是"结果不对"：
                    # 函数忘了 return（于是返回 None）、返回类型不对、变量名和题目不一致。
                    # 这种情况**不能**报成"类型算错了"，那会把人带偏。
                    reason = ("你的代码能跑通，但结果还不符合题目要求。最常见的三个原因：\n"
                              "1. 函数忘了 `return`，于是返回了 `None`；\n"
                              "2. 返回的类型不对（题目要列表，你给了元组或字符串）；\n"
                              "3. 变量名/函数名和题目要求的不一致。\n"
                              "看下面的报错信息，对着题目里的名字再检查一遍。")
                elif "__PASS__" in raw:
                    solved += 1
                    output = raw.split("__PASS__")[0]
                elif "__FAIL__" in raw:
                    last = [line for line in raw.splitlines() if "__FAIL__" in line][-1]
                    reason = last.replace("__FAIL__", "").strip()
                    output = raw.split("__FAIL__")[0]
                else:
                    reason = "没有检测到预期结果，检查一下代码是不是写完整了。"

    passed = reason == "" and total > 0 and solved == total

    if passed:
        prog.code_passed = True
        db.commit()
    done, nxt = _refresh_completion(db, user, prog, point)

    return LearnCheckOut(passed=passed, output=output, error=error, reason=reason,
                         solved=solved, total=total, lesson_completed=done,
                         next_code=nxt)


@router.post("/quiz", response_model=LearnQuizResult)
def quiz(body: LearnQuizSubmitIn, db: Session = Depends(get_db),
         user: User = Depends(get_current_user)):
    """判一道习题。

    客观题（选择/判断/填空）答对才计入完成；主观题（简答/应用）只返回
    关键词覆盖与参考答案 —— **不阻塞通过**，免得表达方式不同就被误判卡住。
    """
    point = _require(db, user, body.code)
    quizzes = point.get("quizzes") or []
    if not (0 <= body.index < len(quizzes)):
        raise HTTPException(404, "习题不存在")
    q = quizzes[body.index]

    graded = _grade_quiz(q, body.answer)

    prog = _progress(db, user).get(body.code)
    if prog is None:
        prog = LearnProgress(user_id=user.id, point_code=body.code, attempts=0)
        db.add(prog)
    state = dict(prog.quiz_json or {})
    record = {"correct": graded.get("correct"), "seen": True}
    # 主观题记 seen；客观题记是否答对（答错了不覆盖已答对的记录）
    prev = state.get(str(body.index)) or {}
    if graded.get("correct") is None:
        state[str(body.index)] = {**prev, **record}
    else:
        state[str(body.index)] = {"correct": bool(prev.get("correct")) or bool(graded["correct"]),
                                  "seen": True}
    prog.quiz_json = state
    db.commit()

    done, nxt = _refresh_completion(db, user, prog, point)
    return LearnQuizResult(**graded, lesson_completed=done, next_code=nxt)


@router.post("/hint", response_model=LearnHintOut)
async def hint(body: LearnHintIn, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    """卡住时找 AI 导师要点提示（不直接给答案，引导他自己想）。"""
    point = _require(db, user, body.code)
    fallback = point.get("hint") or "再读一遍题目要求，把任务拆成几步分别完成。"
    if not ai.ai_enabled():
        return LearnHintOut(hint=fallback)

    subject = point.get("subject", "Python")
    runner = _runner(point)
    if runner == "sql":
        mentor = "一位带过很多新人的资深 DBA，讲 SQL 只讲能落到执行计划和索引上的东西"
        block, code_kind = "sql", "SQL"
    elif subject == "Python":
        mentor = "一位耐心、鼓励型的 Python 启蒙老师"
        block, code_kind = "python", "代码"
    else:
        mentor = f"一位擅长把「{subject}」讲成大白话的技术面试官"
        block, code_kind = "python", "代码"
    submitted = f"```{block}\n{body.user_code or '（还没写）'}\n```" if _has_task(point) \
        else f"{body.user_code or '（还没写）'}"

    prompt = (
        f"你是一位{mentor}。学生正在学「{subject}」里的"
        f"「{point['title']}」这个知识点。\n\n"
        f"练习要求：{point['task']}\n\n"
        f"学生写的{code_kind}：\n{submitted}\n\n"
        f"判定没通过，原因是：{body.reason or '（还没提交运行）'}\n\n"
        "请用 2~3 句中文指出他卡在哪里，并用**提问**的方式引导他自己改对。"
        f"不要直接给出完整答案，最多给一个关键写法的{code_kind}小片段。只输出这段引导语。"
    )
    try:
        reply = await ai.llm_chat([{"role": "user", "content": prompt}],
                                  temperature=0.4, max_tokens=3072)
        return LearnHintOut(hint=reply.strip() or fallback)
    except Exception:
        return LearnHintOut(hint=fallback)
