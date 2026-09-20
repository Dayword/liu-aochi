"""面试题引导学习路由：读考察点 → 自己写一段回答 → 踩中要点到阈值才过关。

和 `learn.py`（写代码判定）同源，只是判定对象从「代码跑不跑得对」换成
「回答有没有踩到面试官想听的点」：

- 过关判定**完全由关键词覆盖决定**（确定性、可解释），阈值取题目自带的
  `answer_min_score`（默认 70）。学生看到的是一句「踩中 7/10 个要点」，
  而不是一个说不清怎么来的分数 —— 这和写代码那套「几组用例全对」是同一个思路。
- AI **只负责点评这段回答**（哪儿说对了、最该补什么）。即使模型抽风，
  判定结果也不会跟着抖：AI 失败就退回规则文案。
- 解锁按**分类独立**：每个分类第一题默认解锁，分类内上一题过关才开下一题；
  分类之间互不阻塞。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import client as ai
from ..database import get_db
from ..models import InterviewGuideProgress, User, now
from ..schemas import (InterviewGuideAnswerIn, InterviewGuideAnswerOut,
                       InterviewGuideBrief, InterviewGuideDetail,
                       InterviewGuideHintIn, InterviewGuideHintOut)
from ..security import get_current_user
from ..seed import agent_interview as bank

router = APIRouter(prefix="/api/interview/guide", tags=["interview-guide"])

# 防「堆词蒙分」：关键词匹配本身挡不住把踩分词用顿号连起来交上去，
# 所以除覆盖率外还要求回答**像一段话**（见 _has_substance）。
MIN_ANSWER_LEN = 60     # 回答整体长度下限
MIN_PROSE_LEN = 40      # 扣掉踩中的要点词之后，剩下的「自己的话」的长度下限


def _progress(db: Session, user: User) -> dict[str, InterviewGuideProgress]:
    rows = db.query(InterviewGuideProgress).filter(
        InterviewGuideProgress.user_id == user.id).all()
    return {r.question_code: r for r in rows}


def _status_of(prog: InterviewGuideProgress | None, prev_passed: bool) -> str:
    if prog and prog.passed:
        return "completed"
    return "unlocked" if prev_passed else "locked"


def _statuses(db: Session, user: User) -> list[tuple[dict, str]]:
    """按分类分别算状态：每个分类第一题解锁，本科目上一题过关才解锁下一题。"""
    prog = _progress(db, user)
    out: list[tuple[dict, str]] = []
    for stage in bank.STAGES:
        prev_passed = True                     # 每个分类第一题默认解锁
        for question in bank.BY_STAGE[stage]:
            st = _status_of(prog.get(question["code"]), prev_passed)
            out.append((question, st))
            prev_passed = st == "completed"
    return out


def _require(db: Session, user: User, code: str) -> tuple[dict, str]:
    question = bank.BY_CODE.get(code)
    if not question:
        raise HTTPException(404, "题目不存在")
    for item, st in _statuses(db, user):
        if item["code"] == code:
            if st == "locked":
                raise HTTPException(403, "先把这一分类的上一题答过关")
            return item, st
    raise HTTPException(404, "题目不存在")


def _grade(answer: str, keywords: list[str]) -> tuple[int, list[str], list[str]]:
    """按关键词覆盖率打分，返回 (分数, 踩中的, 漏掉的)。"""
    text = answer.lower()
    hit = [k for k in keywords if k.lower() in text]
    missed = [k for k in keywords if k not in hit]
    score = round(len(hit) / max(len(keywords), 1) * 100)
    return score, hit, missed


def _has_substance(answer: str, hit: list[str]) -> bool:
    """回答得「像一段话」，而不只是把要点词罗列出来。

    做法：把踩中的要点词整词扣掉，看剩下的自有内容还够不够长。
    纯堆词的答案（`a、b、c、d…`）扣完就只剩顿号了，会被挡下来。
    """
    if len(answer.strip()) < MIN_ANSWER_LEN:
        return False
    rest = answer.lower()
    for k in hit:
        rest = rest.replace(k.lower(), "")
    return len(rest.strip(" \t\n、,，。;；:：.!！?？")) >= MIN_PROSE_LEN


def _rule_comment(score: int, passed: bool, hit: list[str], missed: list[str],
                  threshold: int, substance: bool) -> str:
    total = len(hit) + len(missed)
    if not substance:
        return (f"这像是在罗列要点词（踩中 {len(hit)}/{total} 个），不像一段回答。"
                "面试时是要**说出一段话**的：用完整句子把要点串起来，说清「是什么 + 为什么 + 怎么做」，"
                "再提交一次试试。")
    if passed:
        text = f"踩中 {len(hit)}/{total} 个要点，{score} 分，这题过关。"
        if missed:
            text += f" 想答得更稳可以再补上：{'、'.join(missed[:3])}。"
        return text
    text = f"只踩中 {len(hit)}/{total} 个要点，{score} 分，离过关线（{threshold} 分）还差 {threshold - score} 分。"
    if missed:
        text += f" 面试官想听到的是：{'、'.join(missed[:4])}。"
    return text


async def _ai_comment(question: dict, answer: str, hit: list[str],
                      missed: list[str]) -> str:
    """让模型点评这段回答；不可用时返回空串，由调用方退回规则文案。"""
    if not ai.ai_enabled():
        return ""
    prompt = (
        "你是一位 AI Agent 方向的面试官。候选人在练这道面试题：\n"
        f"题目：{question['title']}\n\n"
        f"他的回答：\n{answer}\n\n"
        f"他没提到的要点：{'、'.join(missed) if missed else '（要点基本都覆盖了）'}\n\n"
        "请用 2~3 句中文点评：先说他说对了什么，再指出**最该补的一个**点，"
        "并给出面试官想听到的说法。不要复述原题，不要输出完整范文，只输出这段点评。"
    )
    try:
        text = await ai.llm_chat([{"role": "user", "content": prompt}],
                                 temperature=0.4, max_tokens=1024, timeout=30)
        return text.strip()
    except Exception:
        return ""


@router.get("/points", response_model=list[InterviewGuideBrief])
def points(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prog = _progress(db, user)
    return [
        InterviewGuideBrief(
            code=q["code"], order_no=q["order_no"], stage=q["stage"], title=q["title"],
            summary=q.get("summary", ""), status=st,
            best_score=prog[q["code"]].best_score if q["code"] in prog else 0,
            min_score=bank.min_score(q))
        for q, st in _statuses(db, user)
    ]


@router.get("/points/{code}", response_model=InterviewGuideDetail)
def point_detail(code: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    question, st = _require(db, user, code)
    prog = _progress(db, user).get(code)
    return InterviewGuideDetail(
        code=question["code"], order_no=question["order_no"], stage=question["stage"],
        title=question["title"], summary=question.get("summary", ""), status=st,
        best_score=prog.best_score if prog else 0, min_score=bank.min_score(question),
        definition=question.get("definition", ""), plain=question.get("plain", ""),
        example=question.get("example", ""), pitfalls=list(question.get("pitfalls") or []),
        followups=list(question.get("followups") or []),
        answer_hint=question.get("answer_hint", ""),
        last_answer=prog.last_answer if prog else "",
        next_code=bank.next_code(code) if st == "completed" else None,
    )


@router.post("/answer", response_model=InterviewGuideAnswerOut)
async def answer(body: InterviewGuideAnswerIn, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    question, _ = _require(db, user, body.code)
    text = (body.answer or "").strip()
    if not text:
        raise HTTPException(400, "先写下你的回答再提交")

    keywords = list(question.get("answer_keywords") or [])
    threshold = bank.min_score(question)
    score, hit, missed = _grade(text, keywords)
    substance = _has_substance(text, hit)
    if not substance:
        # 堆词不给高分：否则「关键词背一遍」就能把 best_score 刷到 100 并解锁下一题
        score = min(score, 40)
    passed = score >= threshold

    prog = db.query(InterviewGuideProgress).filter(
        InterviewGuideProgress.user_id == user.id,
        InterviewGuideProgress.question_code == question["code"]).first()
    already_passed = bool(prog and prog.passed)
    if prog is None:
        prog = InterviewGuideProgress(user_id=user.id, question_code=question["code"])
        db.add(prog)
        db.flush()   # 列默认值（attempts/best_score/last_answer）要 flush 后才落到对象上

    prog.attempts += 1
    prog.last_answer = text
    prog.best_score = max(prog.best_score, score)
    if passed and not prog.passed:
        prog.passed = True
        prog.passed_at = now()
    db.commit()

    # 一眼能看出是堆词的，直接给规则文案，不必浪费一次模型调用
    comment = await _ai_comment(question, text, hit, missed) if substance else ""
    if not comment:
        comment = _rule_comment(score, passed, hit, missed, threshold, substance)

    return InterviewGuideAnswerOut(
        score=score, passed=passed, min_score=threshold, hit_keywords=hit,
        missed_keywords=missed, comment=comment, attempts=prog.attempts,
        best_score=prog.best_score, already_passed=already_passed,
        next_code=bank.next_code(question["code"]) if passed else None)


@router.post("/hint", response_model=InterviewGuideHintOut)
async def hint(body: InterviewGuideHintIn, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    """卡住时给一句思考方向（不直接给答案）。"""
    question, _ = _require(db, user, body.code)
    fallback = question.get("answer_hint") or \
        "先想清楚面试官真正想验证哪种能力，再按「结论先行 + 分点 + 例子」组织答案。"
    if not ai.ai_enabled():
        return InterviewGuideHintOut(hint=fallback)

    prompt = (
        "你是一位 AI Agent 方向的面试官。候选人卡在这道面试题上：\n"
        f"题目：{question['title']}\n\n"
        f"他目前写的：\n{body.answer or '（还没开始写）'}\n\n"
        "请用 2~3 句中文告诉他该往哪个方向想，不要直接给出完整答案，"
        "最多给一个关键要点词。只输出这段提示。"
    )
    try:
        text = await ai.llm_chat([{"role": "user", "content": prompt}],
                                 temperature=0.4, max_tokens=1024, timeout=30)
        return InterviewGuideHintOut(hint=text.strip() or fallback)
    except Exception:
        return InterviewGuideHintOut(hint=fallback)
