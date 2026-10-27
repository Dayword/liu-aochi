"""知识小游戏路由：4 种玩法共用「开局 → 提交 → 结算」。

| mode  | 玩法         | 题面                                        | 判分依据           |
|-------|--------------|---------------------------------------------|--------------------|
| match | 知识连连看   | 左栏术语、右栏释义，各 5~8 张               | 提交的配对表       |
| grid  | 知识网格消除 | 术语与释义混在一个 4 列网格里，配对即消除    | 提交的配对表       |
| order | 知识排序     | 一个被打算顺序的流程，4~7 步                | 提交的步骤序列     |
| speed | 知识竞速     | N 道单选题，限时抢答                        | 提交的选项         |

为什么 match/grid 的对应关系会下发到前端：这两种玩法要「点下去立刻知道对错」，
不给映射就没法做即时反馈。学习应用里作弊没收益，判分仍以服务端复核为准。

为什么 order 不下发顺序：排序的乐趣就在于提交前的悬念，下发了整道题就白送。

奖励口径：**通关不经验**（经验只来自完成课时，见 services/growth.py 文件头），
这里只记星级 + 通关状态 + 解锁下一关。
"""
import random
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import client as ai
from ..database import get_db
from ..models import (GameRound, Level, Question, User, UserLevelProgress,
                      WrongAnswer, now)
from ..schemas import (GamePairResult, GameStartIn, GameStartOut,
                       GameSubmitIn, GameSubmitOut)
from ..security import get_current_user
from ..seed import game_bank
from ..services import growth

router = APIRouter(prefix="/api/games", tags=["games"])

# 关卡场景 → 玩法。放代码里而不是加数据库字段：加字段要 ALTER 线上表，
# 而玩法分配只是一张映射表，改起来没风险。
MODE_BY_SCENE = {
    "新手村": "match",
    "数据结构森林": "grid",
    "算法峡谷": "order",
    "操作系统城堡": "speed",
    "计算机网络迷宫": "match",
    "数据库神庙": "grid",
    "技术栈之域": "speed",
    "面试试炼场": "match",
    "架构师王座": "order",
}

MODE_META = {
    "match": ("知识连连看", "把左边的术语和右边的释义两两配对，配对越多星越多"),
    "grid": ("知识网格消除", "术语和释义混在一起，点中一对就消除，全部消完为止"),
    "order": ("知识排序", "把打乱的流程步骤排回正确顺序，提交后逐条判分"),
    "speed": ("知识竞速", "限时抢答单选题，答错会立刻给解析"),
}


def _mode_of(level: Level) -> str:
    return MODE_BY_SCENE.get(level.scene, "match")


def _level_config(level: Level, mode: str) -> tuple[int, int]:
    """按难度给出 (题量, 限时秒数)。

    题量刻意压在 5~10：手机一屏能看完，一局 1~2 分钟，
    课间也能来一局；题量再大就变成作业了。
    """
    d = max(1, min(5, level.difficulty))
    if mode in ("match", "grid"):
        return min(8, 4 + d), 70 + 10 * d
    if mode == "order":
        return 1, 80 + 10 * d
    return min(10, 6 + d), 60 + 12 * d


def _get_level(db: Session, code: str) -> Level:
    level = db.query(Level).filter(Level.code == code).first()
    if not level:
        raise HTTPException(404, "关卡不存在")
    return level


def _tok() -> str:
    return secrets.token_hex(4)


def _build_payload(db: Session, level: Level, mode: str, size: int) -> tuple[dict, dict]:
    """生成题面与标准答案。"""
    subject = level.subject or game_bank.FALLBACK_SUBJECT

    if mode in ("match", "grid"):
        pool = list(game_bank.pairs_of(subject))
        random.shuffle(pool)
        pool = pool[:size]
        # 左右两侧各发一套独立 token，前端只按 token 配对，看不出对应关系以外的信息
        left = [{"k": _tok(), "text": term} for term, _ in pool]
        right = [{"k": _tok(), "text": desc} for _, desc in pool]
        for i, item in enumerate(left):
            item["id"] = i
        for i, item in enumerate(right):
            item["id"] = i
        random.shuffle(left)
        random.shuffle(right)
        key = {left[i]["k"]: next(r["k"] for r in right if r["id"] == left[i]["id"])
               for i in range(len(left))}
        payload = {"left": [{"k": x["k"], "text": x["text"]} for x in left],
                   "right": [{"k": x["k"], "text": x["text"]} for x in right],
                   # 前端做即时反馈用；服务端判分用下面 answer 里的同一份
                   "key": key}
        return payload, {"key": key, "pairs": len(left)}

    if mode == "order":
        flows = game_bank.flows_of(subject)
        flow = random.choice(flows)
        order = [{"k": _tok(), "text": t} for t in flow["steps"]]
        shuffled = order[:]
        random.shuffle(shuffled)
        payload = {"title": flow["title"],
                   "steps": [{"k": s["k"], "text": s["text"]} for s in shuffled]}
        return payload, {"order": [s["k"] for s in order], "pairs": len(order)}

    # speed：先取本科目的选择题，不够再按相关度补其它科目的
    pool = db.query(Question).filter(Question.type == "choice",
                                     Question.subject == subject).all()
    if len(pool) < size:
        rest = db.query(Question).filter(Question.type == "choice",
                                         Question.subject != subject).all()
        ranked = ai._rank_by_relevance(
            rest, f"{subject} {' '.join(level.tags or [])}", limit=size * 3)
        pool = pool + ranked
    random.shuffle(pool)
    picked = pool[:size]
    if not picked:
        raise HTTPException(500, "题库暂不可用，请稍后再试")
    questions, answer = [], {}
    for q in picked:
        idx = (q.answer or {}).get("correct_index")
        if not isinstance(idx, int) or not q.options:
            continue
        questions.append({"qid": q.id, "stem": q.stem,
                          "options": ai.strip_option_prefix(q.options),
                          "correct_index": idx,
                          "explanation": q.explanation or ""})
        answer[str(q.id)] = idx
    return {"questions": questions}, {"key": answer, "pairs": len(questions)}


@router.post("/start", response_model=GameStartOut)
def start(body: GameStartIn, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    level = _get_level(db, body.level_code)
    growth.unlock_levels(db, user)
    prog = db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.level_code == level.code).first()
    if prog and prog.status == "locked":
        raise HTTPException(403, "先通关前面的关卡再来挑战这里")

    mode = _mode_of(level)
    size, limit = _level_config(level, mode)
    payload, answer = _build_payload(db, level, mode, size)
    rounds = GameRound(user_id=user.id, level_code=level.code, mode=mode,
                       payload=payload, answer=answer)
    db.add(rounds)
    db.commit()
    db.refresh(rounds)

    name, rule = MODE_META[mode]
    return GameStartOut(round_id=rounds.id, level_code=level.code,
                        name=level.name, subject=level.subject or "",
                        difficulty=level.difficulty, mode=mode, mode_name=name,
                        rule=rule, time_limit=limit, payload=payload)


def _grade(mode: str, answer: dict, data: dict) -> tuple[int, int, list[dict]]:
    """返回 (答对数, 总题数, 逐项对错)。"""
    if mode in ("match", "grid"):
        key = answer.get("key") or {}
        pairs = data.get("pairs") or []
        total = int(answer.get("pairs") or len(key))
        detail, got = [], 0
        for p in pairs:
            lk, rk = str(p.get("l")), str(p.get("r"))
            ok = key.get(lk) == rk
            got += 1 if ok else 0
            detail.append({"key": lk, "correct": ok})
        return got, total, detail

    if mode == "order":
        want = answer.get("order") or []
        got_steps = [str(s) for s in (data.get("steps") or [])]
        detail, got = [], 0
        for i, k in enumerate(want):
            ok = i < len(got_steps) and got_steps[i] == k
            got += 1 if ok else 0
            detail.append({"key": k, "correct": ok})
        return got, len(want), detail

    # speed
    key = answer.get("key") or {}
    picks = {str(p.get("qid")): p.get("picked") for p in (data.get("picks") or [])}
    detail, got = [], 0
    for qid, right in key.items():
        ok = picks.get(qid) == right
        got += 1 if ok else 0
        detail.append({"key": qid, "correct": ok})
    return got, len(key), detail


def _stars(ratio: float) -> int:
    if ratio >= 0.95:
        return 3
    if ratio >= 0.8:
        return 2
    if ratio >= 0.6:
        return 1
    return 0


@router.post("/submit", response_model=GameSubmitOut)
def submit(body: GameSubmitIn, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    rnd = db.get(GameRound, body.round_id)
    if not rnd or rnd.user_id != user.id:
        raise HTTPException(404, "这局游戏不存在或已失效，请重新开始")
    level = _get_level(db, rnd.level_code)

    if not rnd.finished:
        correct, total, detail = _grade(rnd.mode, rnd.answer or {}, body.data or {})
        ratio = correct / total if total else 0
        stars = _stars(ratio)
        passed = stars >= 1
        rnd.finished = True

        prog = db.query(UserLevelProgress).filter(
            UserLevelProgress.user_id == user.id,
            UserLevelProgress.level_code == level.code).first()
        if prog is None:
            prog = UserLevelProgress(user_id=user.id, level_code=level.code,
                                     attempts=0, best_score=0)
            db.add(prog)
        prog.attempts = (prog.attempts or 0) + 1
        # best_score 现在存星级（0~3），不是分数
        prog.best_score = max(prog.best_score or 0, stars)

        unlocked_next = None
        if passed:
            first_time = prog.status != "completed"
            prog.status = "completed"
            prog.completed_at = prog.completed_at or datetime.now()
            if first_time:
                # 「通关次数」只算第一次通关，重复刷同一关不该刷出 50 次成就
                user.character.total_quests = (user.character.total_quests or 0) + 1
            growth.report_daily_event(db, user, "quest_pass")
            growth.unlock_levels(db, user)
            newly = db.query(UserLevelProgress).filter(
                UserLevelProgress.user_id == user.id,
                UserLevelProgress.status == "unlocked").order_by(
                UserLevelProgress.id.desc()).first()
            if newly and newly.level_code != level.code:
                unlocked_next = newly.level_code

        # 竞速里答错的选择题自动进错题本
        if rnd.mode == "speed":
            key = (rnd.answer or {}).get("key") or {}
            for p in body.data.get("picks") or []:
                qid = str(p.get("qid"))
                if qid in key and p.get("picked") != key[qid]:
                    exists = db.query(WrongAnswer).filter(
                        WrongAnswer.user_id == user.id,
                        WrongAnswer.question_id == int(qid),
                        WrongAnswer.resolved.is_(False)).first()
                    if exists is None:
                        db.add(WrongAnswer(user_id=user.id, question_id=int(qid),
                                           user_answer=str(p.get("picked")),
                                           reason="知识竞速答错"))
                    user.character.total_wrong = (user.character.total_wrong or 0) + 1
                elif qid in key:
                    user.character.total_correct = (user.character.total_correct or 0) + 1

        db.commit()
        growth.check_achievements(db, user)
        growth.rebuild_leaderboard(db, user)
        return GameSubmitOut(passed=passed, stars=stars, accuracy=round(ratio * 100, 1),
                             correct=correct, total=total, detail=detail,
                             answers=(rnd.answer or {}).get("key") or {},
                             unlocked_next=unlocked_next,
                             best_stars=prog.best_score or 0)

    # 重复提交：原样回放上次结果，避免刷新页面后 500
    prog = db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.level_code == level.code).first()
    return GameSubmitOut(passed=(prog.status == "completed" if prog else False),
                         stars=prog.best_score if prog else 0, accuracy=0,
                         correct=0, total=0, detail=[], answers={},
                         unlocked_next=None, best_stars=prog.best_score if prog else 0)
