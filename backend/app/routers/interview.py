"""面试闯关路由：模拟 一面→二面→三面→HR面 全流程。"""
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import InterviewMessage, InterviewQuestion, InterviewSession, User
from ..schemas import (InterviewAnswerIn, InterviewAnswerOut, InterviewStartIn,
                       InterviewStartOut)
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/interview", tags=["interview"])

ROUND_NAMES = {1: "一面·基础面", 2: "二面·深度面", 3: "三面·主管面", 4: "HR面"}
ROUND_QUESTIONS = {1: 3, 2: 3, 3: 2, 4: 3}
INTERVIEWERS = {1: "技术面试官·王工", 2: "资深工程师·李工", 3: "技术总监·陈总", 4: "HR·林女士"}
COMPANIES = ["字节跳动", "腾讯", "阿里巴巴", "美团", "百度", "京东"]


def _next_question(db: Session, session: InterviewSession,
                   asked: set[str]) -> InterviewQuestion:
    """按当前轮次取一道没问过的题；本轮题面问完则放宽到整轮。"""
    q = db.query(InterviewQuestion).filter(
        InterviewQuestion.class_key.in_([session.class_key, "common"]),
        InterviewQuestion.round_no == session.round_no,
        InterviewQuestion.difficulty <= session.difficulty + 2).all()
    pool = [x for x in q if x.question not in asked]
    if not pool:
        pool = q
    if not pool:
        raise HTTPException(400, f"{ROUND_NAMES.get(session.round_no, '该轮')}暂无可用题目，"
                                 f"请换一个职业方向或降低难度后重试")
    return random.choice(pool)


@router.post("/start", response_model=InterviewStartOut)
def start(body: InterviewStartIn, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    if not user.character or not user.character.onboarding_done:
        raise HTTPException(400, "请先完成新手引导")
    if body.class_key not in growth.CLASSES:
        raise HTTPException(400, "未知职业方向")
    session = InterviewSession(user_id=user.id, class_key=body.class_key,
                               company=body.company, difficulty=body.difficulty)
    db.add(session)
    db.flush()
    q = _next_question(db, session, set())
    db.add(InterviewMessage(session_id=session.id, round_no=1, role="interviewer",
                            content=q.question, scores={"category": q.category}))
    db.commit()
    return InterviewStartOut(session_id=session.id, round_no=1, total_rounds=4,
                             interviewer_name=INTERVIEWERS[1], question=q.question,
                             category=q.category)


@router.post("/answer", response_model=InterviewAnswerOut)
async def answer(body: InterviewAnswerIn, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    session = db.get(InterviewSession, body.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "面试会话不存在")
    if session.status == "finished":
        raise HTTPException(400, "面试已结束")

    from ..ai import client as ai

    # 取当前面试官问题并评分
    qs = db.query(InterviewMessage).filter(
        InterviewMessage.session_id == session.id,
        InterviewMessage.role == "interviewer",
        InterviewMessage.round_no == session.round_no).all()
    current_q = qs[-1].content if qs else ""
    keywords = []
    iq = db.query(InterviewQuestion).filter(
        InterviewQuestion.round_no == session.round_no).all()
    for x in iq:
        if x.question == current_q:
            keywords = x.keywords or []
            break
    scored = await ai.interview_score(current_q, body.answer, keywords)

    db.add(InterviewMessage(session_id=session.id, round_no=session.round_no,
                            role="candidate", content=body.answer, scores=scored.get("scores", {})))
    db.flush()

    round_msgs = db.query(InterviewMessage).filter(
        InterviewMessage.session_id == session.id,
        InterviewMessage.round_no == session.round_no).all()
    answered = sum(1 for m in round_msgs if m.role == "candidate")

    round_finished = answered >= ROUND_QUESTIONS.get(session.round_no, 3)
    if round_finished:
        # 计算本轮平均分
        dims = ["技术准确性", "逻辑清晰度", "表达流畅度", "STAR法则"]
        round_scores = {}
        for d in dims:
            vals = [m.scores.get(d, 0) for m in round_msgs if m.role == "candidate"]
            round_scores[d] = round(sum(vals) / len(vals)) if vals else 0
        round_scores["平均分"] = round(sum(round_scores.values()) / 4)
        round_scores["点评"] = scored.get("comment", "")
        round_scores["建议"] = scored.get("advice", "")
        # 存一轮汇总消息
        db.add(InterviewMessage(session_id=session.id, round_no=session.round_no,
                                role="interviewer", content="【本轮小结】" + scored.get("comment", ""),
                                scores={"summary": round_scores}))
        finished_round = session.round_no

        if finished_round >= 4:
            # 全部结束 → 生成报告
            all_msgs = db.query(InterviewMessage).filter(
                InterviewMessage.session_id == session.id,
                InterviewMessage.role == "candidate").all()
            rounds_data = []
            for rn in range(1, 5):
                rms = [m for m in all_msgs if m.round_no == rn]
                if rms:
                    sd = {}
                    for d in dims:
                        vals = [m.scores.get(d, 0) for m in rms]
                        sd[d] = round(sum(vals) / len(vals))
                    rounds_data.append({"round": rn, "scores": sd})
            report = await ai.interview_report(rounds_data)
            session.status = "finished"
            session.report = report
            session.finished_at = datetime.now()
            char = user.character
            char.total_interviews += 1
            exp_gain = 60 if report["overall"] >= 75 else 30
            growth.add_exp(db, char, exp_gain)
            growth.add_coins(db, char, 30)
            new_ach = growth.check_achievements(db, user)
            db.commit()
            growth.rebuild_leaderboard(db, user)
            return InterviewAnswerOut(
                session_id=session.id, round_no=finished_round,
                round_finished=True, round_scores=round_scores,
                interview_finished=True, report=report)

        # 进入下一轮：立刻取出下一轮第一题，避免出现「无题可答」
        session.round_no = finished_round + 1
        db.flush()
        nxt = _next_question(db, session, set())
        db.add(InterviewMessage(session_id=session.id, round_no=session.round_no,
                                role="interviewer", content=nxt.question,
                                scores={"category": nxt.category}))
        db.commit()
        return InterviewAnswerOut(
            session_id=session.id, round_no=finished_round,
            next_question=nxt.question, next_category=nxt.category,
            round_finished=True, round_scores=round_scores,
            interview_finished=False)

    # 未结束本轮 → 出下一题（避开本轮已经问过的题面）
    asked = {m.content for m in round_msgs if m.role == "interviewer"}
    q = _next_question(db, session, asked)
    db.add(InterviewMessage(session_id=session.id, round_no=session.round_no,
                            role="interviewer", content=q.question,
                            scores={"category": q.category}))
    db.commit()
    return InterviewAnswerOut(
        session_id=session.id, round_no=session.round_no,
        next_question=q.question, next_category=q.category,
        round_finished=False,
        round_scores={**scored.get("scores", {}), "点评": scored.get("comment", ""),
                      "建议": scored.get("advice", "")})


@router.get("/detail/{session_id}")
def detail(session_id: int, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    session = db.get(InterviewSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "面试会话不存在")
    msgs = db.query(InterviewMessage).filter(
        InterviewMessage.session_id == session.id).order_by(InterviewMessage.id).all()
    return {"session_id": session.id, "class_key": session.class_key,
            "company": session.company, "difficulty": session.difficulty,
            "status": session.status, "report": session.report,
            "messages": [{"round_no": m.round_no, "role": m.role, "content": m.content,
                          "scores": m.scores} for m in msgs]}


@router.get("/sessions")
def sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(InterviewSession).filter(
        InterviewSession.user_id == user.id).order_by(InterviewSession.id.desc()).limit(20).all()
    return [{"id": s.id, "company": s.company, "class_key": s.class_key,
             "status": s.status, "grade": s.report.get("grade", "") if s.report else "",
             "created_at": s.created_at.strftime("%m-%d %H:%M")} for s in rows]
