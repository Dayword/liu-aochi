"""选择题教练：规划知识点 → 由易到难逐点闯关 → 连对 3 题过关。

一轮练习的顺序是固定的：

1. `/start` 不直接出题，先让 AI 判断用户给的范围**还能不能再分**。
   「Python」这种大范围拆成 3~6 个由易到难的知识点；「列表切片」这种就不拆。
   规划结果（说明 + 清单）先返回给前端展示，用户看完才出第一题。
2. `/next` 只考当前知识点，难度由**该知识点内第几题**决定（基础→中级→进阶），
   不再靠连对/答错动态升降。答错不降难度，只把连对计数清零。
3. `/answer` 连对满 3 题就过关：还有下一个知识点就切过去，
   已经是最后一个就 finished=true 并返回总结，前端停止出题。

这个功能完全依赖外部大模型，所以**稳定性不是附加项，是主体**：
规划 30s 硬超时（失败降级成单知识点，照常能练）、出题 30s 硬超时
（失败从课程 238 道现成选择题捞一道，标 fallback）、所有失败都给中文提示。

标准答案**只存服务端**（`CoachAttempt.answer_index`），下发给前端的题不含答案。
"""
from __future__ import annotations

import asyncio
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import coach as ai_coach
from ..database import get_db
from ..models import CoachAttempt, CoachSession, User
from ..schemas import (CoachAnswerIn, CoachAnswerOut, CoachQuestionOut,
                       CoachStartIn, CoachStartOut)
from ..security import get_current_user
from ..seed import learn

router = APIRouter(prefix="/api/coach", tags=["coach"])
# 挂在 uvicorn 的 logger 上：自定义 logger 没有 handler，warning 会静默消失，
# 那样降级就成了「看不见的故障」——出过一次，线上只能看到题库老题，查不出原因。
log = logging.getLogger("uvicorn.error")

# 出题 / 规划总超时。模型正常 3~5s，超过 30s 的不是慢，是死了
GEN_TIMEOUT = 30
PLAN_TIMEOUT = 30
# 每个知识点连对几题过关
PASS_STREAK = 3
# 知识点内第 1/2/3 题起的难度：由易到难，答错不回退
LEVEL_BY_STEP = (1, 3, 4)
# 每几题插一道反向题（第 4、8、12… 题，全局计数）
REVERSE_EVERY = 4
# 一个 session 保留的考点记忆上限，太多会把 prompt 撑长
MAX_ASKED = 14


def _session_or_404(db: Session, user: User, sid: int) -> CoachSession:
    s = db.get(CoachSession, sid)
    if s is None or s.user_id != user.id:
        raise HTTPException(404, "这个练习不存在，或者不是你的")
    return s


def _points(s: CoachSession) -> list[str]:
    """旧 session 的 plan 可能是 NULL，一律兜成单知识点。"""
    p = [str(x).strip() for x in (s.plan or []) if str(x).strip()]
    return p or [s.topic]


def _point_name(s: CoachSession) -> str:
    ps = _points(s)
    return ps[min(int(s.point_index or 0), len(ps) - 1)]


# ---------------------------------------------------------------- 状态推进
def advance(s: CoachSession, correct: bool) -> dict:
    """判完一题后推进闯关状态（纯逻辑，不碰 DB，方便单测）。

    答错：连对计数清零，**难度不降**（q_in_point 继续涨）。
    连对满 PASS_STREAK：切到下一个知识点并重置题序/连对；
    已经是最后一个就标 finished。
    """
    total = len(_points(s))
    if correct:
        s.streak_in_point = int(s.streak_in_point or 0) + 1
    else:
        s.streak_in_point = 0

    passed = finished = False
    if s.streak_in_point >= PASS_STREAK:
        if int(s.point_index or 0) + 1 < total:
            s.point_index = int(s.point_index or 0) + 1
            s.q_in_point = 0
            s.streak_in_point = 0
            s.asked = []          # 换知识点，旧考点的去重记录不该限制新点
            passed = True
        else:
            s.finished = True
            finished = True

    return {
        "passed": passed,
        "finished": finished,
        "streak": int(s.streak_in_point or 0),
        "point_index": int(s.point_index or 0),
        "points_total": total,
        "point_name": _point_name(s),
    }


def _summary(db: Session, s: CoachSession) -> dict:
    """结束时按知识点统计，给前端画总结卡片。"""
    rows = (db.query(CoachAttempt)
            .filter(CoachAttempt.session_id == s.id,
                    CoachAttempt.correct.isnot(None)).all())
    per = []
    for i, name in enumerate(_points(s)):
        rs = [r for r in rows if int(r.point_index or 0) == i]
        per.append({"name": name, "total": len(rs),
                    "right": sum(1 for r in rs if r.correct)})
    right = sum(p["right"] for p in per)
    return {"topic": s.topic, "points": per,
            "total": len(rows), "right": right, "wrong": len(rows) - right}


# ---------------------------------------------------------------- 本地题库兜底
_choice_bank: list[dict] | None = None


def _bank() -> list[dict]:
    """把课程里 238 道选择题拍平成一张表。首次调用后缓存在进程内。"""
    global _choice_bank
    if _choice_bank is not None:
        return _choice_bank
    out: list[dict] = []
    for p in learn.CURRICULUM:
        for q in (p.get("quizzes") or []):
            if q.get("type") != "choice":
                continue
            opts = [str(o) for o in (q.get("options") or [])]
            if len(opts) != 4:
                continue
            out.append({
                "subject": p.get("subject", ""),
                "title": p.get("title", ""),
                "stem": q.get("stem", ""),
                "options": opts,
                "answer_index": int(q.get("answer_index") or 0),
                "explanation": q.get("explanation", ""),
            })
    _choice_bank = out
    return out


def _fallback_question(topic: str, asked: list[str]) -> dict | None:
    """按关键词从现成题库捞一道没用过的题。捞不到就 None，由上层报错。"""
    words = [w for w in re.split(r"[\s，,、/·]+", topic) if len(w) >= 2]
    if not words:
        words = [topic]
    scored: list[tuple[int, dict]] = []
    for item in _bank():
        # 已经考过同一道题就跳过（用题干前 20 字比对）
        if item["stem"][:20] in asked:
            continue
        score = 0
        for w in words:
            if w in item["subject"]:
                score += 6
            if w in item["title"]:
                score += 4
            if w in item["stem"]:
                score += 2
        if score:
            scored.append((score, item))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


# ---------------------------------------------------------------- 接口
@router.post("/start", response_model=CoachStartOut)
async def start(body: CoachStartIn, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    """开一轮练习：先判断范围能不能再分，**不直接出题**。

    规划失败不能拖垮整轮练习：降级成单知识点，note 里如实说明，
    并打 warning —— 否则「范围判断全挂」在线上会静默成「从来不拆分」。
    """
    topic = body.topic
    need_split, points = False, [topic]
    plan_failed = False
    try:
        p = await asyncio.wait_for(
            ai_coach.plan_points(topic), timeout=PLAN_TIMEOUT)
        need_split, points = bool(p["need_split"]), list(p["points"])
    except asyncio.TimeoutError:
        plan_failed = True
        log.warning("教练规划超时 topic=%s", topic)
    except Exception as e:      # 未预期异常也降级，不把 500 抛给前端
        plan_failed = True
        log.warning("教练规划降级 topic=%s 原因=%s", topic,
                    f"{type(e).__name__}: {e}")

    if plan_failed:
        note = (f"「{topic}」的范围判断暂时没成功，先按你输入的知识点练；"
                f"连对 {PASS_STREAK} 题过关。")
    elif need_split:
        note = (f"「{topic}」范围偏大，已按由易到难拆成 {len(points)} 个知识点；"
                f"每个连对 {PASS_STREAK} 题就进入下一个。")
    else:
        note = (f"「{topic}」范围适中，不用再分；"
                f"连对 {PASS_STREAK} 题就过关。")

    s = CoachSession(
        user_id=user.id, topic=topic, level=1, asked=[],
        plan=points, plan_note=note, need_split=need_split,
        point_index=0, q_in_point=0, streak_in_point=0, finished=False,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return CoachStartOut(session_id=s.id, topic=s.topic, level=1,
                         need_split=need_split, note=note, points=points)


@router.post("/next", response_model=CoachQuestionOut)
async def next_question(session_id: int, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    """出当前知识点的下一题。

    失败一定给出可理解的原因（503 + 中文），绝不空转；
    能降级就降级，只有连兜底题库都捞不到才报错。
    """
    s = _session_or_404(db, user, session_id)
    if s.finished:
        raise HTTPException(409, "这一轮已经全部过关了，换个知识点再来一轮吧")
    asked = [str(a) for a in (s.asked or [])]
    points = _points(s)
    idx = int(s.point_index or 0)
    point_name = points[min(idx, len(points) - 1)]
    rank = f"{idx + 1}/{len(points)}"

    # 难度只由「本知识点第几题」决定，答错不回退
    step = min(int(s.q_in_point or 0), len(LEVEL_BY_STEP) - 1)
    level = LEVEL_BY_STEP[step]

    # 第几题（含已答和未答），决定要不要插反向题
    done = db.query(CoachAttempt).filter(CoachAttempt.session_id == s.id).count()
    nxt_num = done + 1
    reverse = nxt_num % REVERSE_EVERY == 0 and nxt_num > 0

    q: dict | None = None
    fallback = False
    why = ""
    try:
        q = await asyncio.wait_for(
            ai_coach.gen_question(
                s.topic, level=level, reverse=reverse,
                history=asked, subject="Python",
                point_name=point_name, point_rank=rank,
            ),
            timeout=GEN_TIMEOUT,
        )
    except asyncio.TimeoutError:
        why = f"出题超时（>{GEN_TIMEOUT}s）"
    except ai_coach.CoachAIError as e:
        why = f"AI 输出不可用：{e}"
    except Exception as e:      # 未预期异常也降级，不把 500 抛给前端
        why = f"未预期异常：{type(e).__name__}: {e}"

    if q is None:
        # 一定要留痕：降级本身是正常兜底，但**连续降级就是故障**，
        # 不打日志的话线上只会看到「题目怎么老是那几道老的」，查不出原因。
        log.warning("教练出题降级 session=%s topic=%s point=%s reverse=%s 原因=%s",
                    s.id, s.topic, point_name, reverse, why or "空结果")
        # 先按当前子知识点捞，捞不到再退回大范围（「面向对象」这种窄词
        # 在课程题库里常常一个都匹配不上）
        fb = (_fallback_question(point_name, asked)
              or _fallback_question(s.topic, asked))
        if fb is None:
            raise HTTPException(
                503, "出题服务暂时不可用，请稍等几秒点「重试」再试一次")
        q = {
            "stem": fb["stem"], "options": fb["options"],
            "answer_index": fb["answer_index"],
            "explanation": fb["explanation"], "traps": [],
            "fact_check": None, "code": None,
            "level": level, "reverse": False,
            "point": fb["title"][:20], "verified": None,
        }
        fallback = True

    # AI 题和题库题统一在落库前重排：模型出题偏爱把正确答案放 A（实测
    # 6 题里 5 题在 0 位），只靠 prompt 约束不够。verify_code_answer
    # 在 gen_question 内部已用真实执行结果校正过 answer_index，重排放
    # 它之后才是安全的（重排会同步搬 traps 下标和 fact_check）。
    q = ai_coach.shuffle_options(q)

    att = CoachAttempt(
        session_id=s.id,
        point=q["point"][:40],
        point_index=idx,
        level=q["level"],
        reverse=q["reverse"],
        stem=q["stem"],
        options=q["options"],
        code=q.get("code"),
        answer_index=q["answer_index"],
        explanation=q["explanation"],
        traps=q["traps"],
        fact_check=q.get("fact_check"),
        verified=q.get("verified"),
    )
    db.add(att)

    # 记住这道题考了什么，同一点内不重复
    key = (q["point"] or q["stem"])[:40]
    if fallback:
        key = q["stem"][:20]
    asked.append(key)
    s.asked = asked[-MAX_ASKED:]
    s.q_in_point = int(s.q_in_point or 0) + 1
    s.level = level
    db.commit()
    db.refresh(att)

    return CoachQuestionOut(
        attempt_id=att.id, stem=q["stem"], options=q["options"],
        code=q.get("code"), level=q["level"], reverse=q["reverse"],
        point=q["point"], verified=q.get("verified"), fallback=fallback,
        point_index=idx, points_total=len(points),
        point_name=point_name, q_in_point=int(s.q_in_point),
    )


@router.post("/answer", response_model=CoachAnswerOut)
def answer(body: CoachAnswerIn, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    """判一题 + 推进闯关。纯本地计算，不调 AI，所以不会因为上游抖动而失败。"""
    att = db.get(CoachAttempt, body.attempt_id)
    if att is None:
        raise HTTPException(404, "题目不存在")
    s = _session_or_404(db, user, att.session_id)
    if att.chosen is not None:
        raise HTTPException(409, "这道题已经答过了")

    correct = body.chosen == att.answer_index
    # 答错时把他选的那一项对应的误解取出来 —— 这是「定位误解」的数据来源
    belief = ""
    if not correct:
        for t in (att.traps or []):
            if int(t.get("index", -1)) == body.chosen:
                belief = str(t.get("belief") or "")
                break

    att.chosen = body.chosen
    att.correct = correct
    att.belief = belief

    state = advance(s, correct)
    # 必须先落库再统计：MySQL 里 att.correct 还是 None，
    # 早一步查询就会得到 total=0，前端显示「答对 0/0」。
    db.commit()

    total = db.query(CoachAttempt).filter(
        CoachAttempt.session_id == s.id, CoachAttempt.correct.isnot(None)).count()
    right = db.query(CoachAttempt).filter(
        CoachAttempt.session_id == s.id, CoachAttempt.correct.is_(True)).count()

    return CoachAnswerOut(
        correct=correct, answer_index=att.answer_index,
        explanation=att.explanation or "", fact_check=att.fact_check,
        belief=belief, level=att.level, level_changed="",
        streak=state["streak"], total=total, right=right,
        point_index=state["point_index"], points_total=state["points_total"],
        point_name=state["point_name"],
        passed=state["passed"], finished=state["finished"],
        summary=_summary(db, s) if state["finished"] else None,
    )


@router.get("/mistakes")
def mistakes(session_id: int | None = None, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    """错题清单。不传 session_id 就是这个人全部练过的错题。"""
    q = (db.query(CoachAttempt, CoachSession)
         .join(CoachSession, CoachAttempt.session_id == CoachSession.id)
         .filter(CoachSession.user_id == user.id,
                 CoachAttempt.correct.is_(False)))
    if session_id:
        q = q.filter(CoachAttempt.session_id == session_id)
    rows = q.order_by(CoachAttempt.id.desc()).limit(200).all()
    return [{
        "attempt_id": a.id,
        "session_id": a.session_id,
        "topic": s.topic,
        "point": a.point,
        "stem": a.stem,
        "options": a.options,
        "chosen": a.chosen,
        "answer_index": a.answer_index,
        "belief": a.belief,
        "explanation": a.explanation,
    } for a, s in rows]


@router.get("/sessions")
def sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """练过哪些知识点，带进度，用于「继续练」。"""
    rows = (db.query(CoachSession)
            .filter(CoachSession.user_id == user.id)
            .order_by(CoachSession.id.desc()).limit(30).all())
    out = []
    for s in rows:
        total = db.query(CoachAttempt).filter(
            CoachAttempt.session_id == s.id, CoachAttempt.correct.isnot(None)).count()
        right = db.query(CoachAttempt).filter(
            CoachAttempt.session_id == s.id, CoachAttempt.correct.is_(True)).count()
        out.append({"session_id": s.id, "topic": s.topic, "level": s.level,
                    "total": total, "right": right,
                    "points": _points(s), "point_index": int(s.point_index or 0),
                    "finished": bool(s.finished)})
    return out
