"""引导式学习路由：按顺序解锁知识点，写完代码点运行，判定通过才进下一个。

判定放在服务端做（而不是前端），这样：
- 判定逻辑和「给定的预置数据」不会泄漏到浏览器里；
- 每组用例都会换一组输入再跑一遍，防止把答案直接 print 出来蒙过去。

解锁是**按科目独立**的：每个科目的第一课默认解锁，本科目上一课通过才解锁下一课；
科目之间互不阻塞（学 Python 卡住了，不影响去学 MySQL）。
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import client as ai
from ..database import get_db
from ..models import LearnProgress, User, now
from ..schemas import (LearnCheckIn, LearnCheckOut, LearnHintIn, LearnHintOut,
                       LearnPointBrief, LearnPointDetail, LearnQuizItem,
                       LearnQuizResult, LearnQuizSubmitIn)
from ..security import get_current_user
from ..seed.learn import BY_CODE, BY_SUBJECT, SUBJECTS, next_code
from ..services import sql_runner
from ..services.code_runner import run_python

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
    """按科目分别算状态：每个科目第一课解锁，本科目上一课通过才解锁下一课。"""
    prog = _progress(db, user)
    out: list[tuple[dict, str]] = []
    for subject in SUBJECTS:
        prev_done = True                      # 每科第一课默认解锁
        for point in BY_SUBJECT[subject]:
            st = _status_of(prog.get(point["code"]), prev_done)
            out.append((point, st))
            prev_done = st == "completed"
    return out


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
    """
    def soft(s: object) -> str:
        return re.sub(r"\s+", "", str(s or "")).lower()

    def hard(s: object) -> str:
        return re.sub(r"[\s,，。、.;；:：!！?？'\"“”‘’()（）]", "", str(s or "")).lower()

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
        accepted = q.get("accept") or [q["answer"]]
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


def _refresh_completion(db: Session, prog: LearnProgress, point: dict) -> tuple[bool, str | None]:
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
        db.commit()

    nxt = next_code(point["code"]) if done else None
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


@router.get("/points/{code}", response_model=LearnPointDetail)
def point_detail(code: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    point = _require(db, user, code)
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
        next_code=next_code(point["code"]),
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
            r = run_python((c.get("setup") or "") + user_code)
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
            solo = run_python(setup + user_code)
            if solo["exit_code"] != 0:
                reason = _runtime_reason(solo, user_code)
                error, output = solo["stderr"], solo["stdout"]
            else:
                r = run_python(setup + user_code + "\n\n" + checker)
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
    done, nxt = _refresh_completion(db, prog, point)

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

    done, next_code = _refresh_completion(db, prog, point)
    return LearnQuizResult(**graded, lesson_completed=done, next_code=next_code)


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
