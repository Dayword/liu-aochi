"""选择题教练：按知识点连续出题、即时判分、错因归到具体误解。

这个功能完全依赖外部大模型，所以**稳定性不是附加项，是主体**。三层设计：

1. **超时**：单次出题 30s 硬上限。模型正常 3~5s，超过 30s 的不是慢，是死了。
2. **降级**：AI 挂了就从课程里的 238 道现成选择题按关键词捞一道顶上，
   标 `fallback=true`，前端照常能练。宁可题目普通，也不给白屏。
3. **不抛 500**：所有失败路径都返回可读中文 + 可重试，前端不会卡死在转圈。

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

# 出题总超时。模型 3~5s 出完，30s 还没回来说明上游出问题了，重试更快
GEN_TIMEOUT = 30
# 档位阶梯，升/降都按这个走
LADDER = [1, 3, 4]
# 每几题插一道反向题（第 4、8、12… 题）
REVERSE_EVERY = 4
# 一个 session 保留的考点记忆上限，太多会把 prompt 撑长
MAX_ASKED = 14


def _session_or_404(db: Session, user: User, sid: int) -> CoachSession:
    s = db.get(CoachSession, sid)
    if s is None or s.user_id != user.id:
        raise HTTPException(404, "这个练习不存在，或者不是你的")
    return s


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
def start(body: CoachStartIn, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    """开一个练习。不调 AI，所以一定成功。"""
    s = CoachSession(user_id=user.id, topic=body.topic, level=1, asked=[])
    db.add(s)
    db.commit()
    db.refresh(s)
    return CoachStartOut(session_id=s.id, topic=s.topic, level=s.level)


def _next_level(cur: int, streak: int, correct: bool | None) -> tuple[int, str]:
    """难度调度：连对 2 题升一档，答错降一档。中间档位按 LADDER 走。"""
    i = LADDER.index(cur) if cur in LADDER else 0
    if correct:
        if streak + 1 >= 2 and i < len(LADDER) - 1:
            return LADDER[i + 1], "up"
        return cur, ""
    if i > 0:
        return LADDER[i - 1], "down"
    return cur, ""


@router.post("/next", response_model=CoachQuestionOut)
async def next_question(session_id: int, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    """出下一题。

    失败一定给出可理解的原因（503 + 中文），绝不空转；
    能降级就降级，只有连兜底题库都捞不到才报错。
    """
    s = _session_or_404(db, user, session_id)
    asked = [str(a) for a in (s.asked or [])]

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
                s.topic, level=s.level, reverse=reverse,
                history=asked, subject="Python",
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
        log.warning("教练出题降级 session=%s topic=%s reverse=%s 原因=%s",
                    s.id, s.topic, reverse, why or "空结果")
        fb = _fallback_question(s.topic, asked)
        if fb is None:
            raise HTTPException(
                503, "出题服务暂时不可用，请稍等几秒点「再来一题」重试")
        q = {
            "stem": fb["stem"], "options": fb["options"],
            "answer_index": fb["answer_index"],
            "explanation": fb["explanation"], "traps": [],
            "fact_check": None, "code": None,
            "level": s.level, "reverse": False,
            "point": fb["title"][:20], "verified": None,
        }
        fallback = True

    att = CoachAttempt(
        session_id=s.id,
        point=q["point"][:40],
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

    # 记住这道题考了什么，下次出题避开
    key = (q["point"] or q["stem"])[:40]
    if fallback:
        key = q["stem"][:20]
    asked.append(key)
    s.asked = asked[-MAX_ASKED:]
    db.commit()
    db.refresh(att)

    return CoachQuestionOut(
        attempt_id=att.id, stem=q["stem"], options=q["options"],
        code=q.get("code"), level=q["level"], reverse=q["reverse"],
        point=q["point"], verified=q.get("verified"), fallback=fallback,
    )


@router.post("/answer", response_model=CoachAnswerOut)
def answer(body: CoachAnswerIn, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    """判一题。纯本地计算，不调 AI，所以不会因为上游抖动而失败。"""
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

    # 连击：最近连续答对几题（含本次）
    recent = (db.query(CoachAttempt)
              .filter(CoachAttempt.session_id == s.id, CoachAttempt.correct.isnot(None))
              .order_by(CoachAttempt.id.desc()).limit(6).all())
    streak = 0
    for a in recent:                    # 已按 id 倒序，第一条就是包含本次
        if a.correct:
            streak += 1
        else:
            break
    if not correct:
        streak = 0

    level, changed = _next_level(s.level, streak if correct else 0, correct)
    # 升级后连击清零，否则「连对 2 题」会在每次答对后重复触发
    if changed == "up":
        streak = 0
    s.level = level
    # 必须先落库再统计：MySQL 里 att.correct 还是 None，
    # 早一步查询就会得到 total=0，前端显示「第 0 题 · 答对 0/0」。
    db.commit()

    total = db.query(CoachAttempt).filter(
        CoachAttempt.session_id == s.id, CoachAttempt.correct.isnot(None)).count()
    right = db.query(CoachAttempt).filter(
        CoachAttempt.session_id == s.id, CoachAttempt.correct.is_(True)).count()

    return CoachAnswerOut(
        correct=correct, answer_index=att.answer_index,
        explanation=att.explanation or "", fact_check=att.fact_check,
        belief=belief, level=level, level_changed=changed,
        streak=streak, total=total, right=right,
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
                    "total": total, "right": right})
    return out
