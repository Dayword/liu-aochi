"""成长相关路由：错题本、成就墙、每日任务、排行榜、能力雷达。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, User, WrongAnswer
from ..schemas import (AchievementOut, DailyTaskOut, LeaderboardEntry,
                       WrongAnswerOut)
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/growth", tags=["growth"])


@router.get("/achievements", response_model=list[AchievementOut])
def achievements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..models import Achievement, UserAchievement
    unlocked = {ua.achievement_code for ua in db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id).all()}
    at_map = {ua.achievement_code: ua for ua in db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id).all()}
    out = []
    for ach in db.query(Achievement).order_by(Achievement.id).all():
        ua = at_map.get(ach.code)
        out.append({"code": ach.code, "name": ach.name, "description": ach.description,
                    "icon": ach.icon, "category": ach.category,
                    "unlocked": ach.code in unlocked,
                    "unlocked_at": ua.unlocked_at if ua else None,
                    "exp_reward": ach.exp_reward, "coin_reward": ach.coin_reward})
    return out


@router.get("/daily-tasks", response_model=list[DailyTaskOut])
def daily_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.character:
        return []
    growth.ensure_daily_tasks(db, user)
    day = growth.today_str()
    out = []
    from ..models import DailyTask, UserDailyTask
    for ut in db.query(UserDailyTask).filter(
            UserDailyTask.user_id == user.id, UserDailyTask.task_date == day).all():
        task = db.query(DailyTask).filter(DailyTask.code == ut.task_code).first()
        if task:
            out.append({"code": task.code, "name": task.name, "description": task.description,
                        "progress": ut.progress, "target": task.target_value,
                        "done": ut.done, "claimed": ut.claimed,
                        "exp_reward": task.exp_reward, "coin_reward": task.coin_reward})
    return out


@router.post("/daily-tasks/{code}/claim")
def claim(code: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    result = growth.claim_daily_task(db, user, code)
    if not result["ok"]:
        raise HTTPException(400, result["msg"])
    return result


@router.get("/wrong-book", response_model=list[WrongAnswerOut])
def wrong_book(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(WrongAnswer).filter(WrongAnswer.user_id == user.id).order_by(
        WrongAnswer.id.desc()).limit(100).all()
    out = []
    for w in rows:
        q = db.get(Question, w.question_id)
        if not q:
            continue
        ans = q.answer or {}
        correct_answer = ans.get("correct_index") if q.type == "choice" else ans.get("answer", "")
        out.append({"id": w.id, "question_id": q.id, "stem": q.stem,
                    "subject": q.subject, "difficulty": q.difficulty,
                    "user_answer": w.user_answer, "correct_answer": correct_answer,
                    "explanation": q.explanation, "knowledge_point": q.knowledge_point,
                    "reason": w.reason, "resolved": w.resolved,
                    "created_at": w.created_at})
    return out


@router.post("/wrong-book/{wid}/resolve")
def resolve_wrong(wid: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    w = db.get(WrongAnswer, wid)
    if not w or w.user_id != user.id:
        raise HTTPException(404, "记录不存在")
    w.resolved = True
    db.commit()
    return {"ok": True}


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(board: str = "total", limit: int = 20,
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    class_key = user.character.class_key if user.character else None
    return growth.leaderboard(db, board, min(limit, 50), class_key=class_key)


@router.post("/share")
def share(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """每日任务「分享」事件。"""
    if not user.character:
        raise HTTPException(400, "请先创建角色")
    growth.report_daily_event(db, user, "share")
    return {"ok": True}


@router.get("/radar")
def radar(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return growth.radar_data(db, user)
