"""成长相关路由：错题本、收藏、成就墙、每日任务、排行榜、能力雷达。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, QuestionFavorite, User, WrongAnswer
from ..schemas import (AchievementFamilyOut, AchievementOut, DailyTaskOut,
                       FavoriteOut, LeaderboardEntry, WrongAnswerOut)
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/growth", tags=["growth"])


@router.get("/achievements", response_model=list[AchievementOut])
def achievements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from ..models import Achievement, UserAchievement
    at_map = {ua.achievement_code: ua for ua in db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id).all()}
    out = []
    for ach in db.query(Achievement).order_by(Achievement.id).all():
        ua = at_map.get(ach.code)
        out.append({"code": ach.code, "name": ach.name, "description": ach.description,
                    "icon": ach.icon, "category": ach.category,
                    "unlocked": ua is not None,
                    "unlocked_at": ua.unlocked_at if ua else None,
                    "exp_reward": ach.exp_reward})
    return out


@router.get("/achievement-families", response_model=list[AchievementFamilyOut])
def achievement_families(db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    """成就墙：8 个家族 × 铜/银/金三档，带当前进度。"""
    growth.ensure_character(db, user)
    return growth.achievement_families(db, user)


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
                        "exp_reward": task.exp_reward})
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
                    "type": q.type, "subject": q.subject, "difficulty": q.difficulty,
                    "options": q.options or [],
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


@router.delete("/wrong-book/{wid}")
def delete_wrong(wid: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    """手动从错题本移除（答对了但不想留着的题）。"""
    w = db.get(WrongAnswer, wid)
    if not w or w.user_id != user.id:
        raise HTTPException(404, "记录不存在")
    db.delete(w)
    db.commit()
    return {"ok": True}


# ---------- 题目收藏 ----------
def _fav_out(q: Question, fav_id: int, created_at) -> dict:
    ans = q.answer or {}
    correct = ans.get("correct_index") if q.type == "choice" else ans.get("answer", "")
    return {"id": fav_id, "question_id": q.id, "stem": q.stem, "type": q.type,
            "subject": q.subject, "difficulty": q.difficulty,
            "options": q.options or [], "correct_answer": correct,
            "explanation": q.explanation or "",
            "knowledge_point": q.knowledge_point or "",
            "created_at": created_at}


@router.get("/favorites", response_model=list[FavoriteOut])
def favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(QuestionFavorite).filter(
        QuestionFavorite.user_id == user.id).order_by(
        QuestionFavorite.id.desc()).all()
    out = []
    for f in rows:
        q = db.get(Question, f.question_id)
        if q:
            out.append(_fav_out(q, f.id, f.created_at))
    return out


@router.get("/favorites/ids")
def favorite_ids(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """前端批量标星用：只回题目 id，省一次全量拉取。"""
    return [qid for (qid,) in db.query(QuestionFavorite.question_id).filter(
        QuestionFavorite.user_id == user.id).all()]


@router.post("/favorites/{qid}")
def toggle_favorite(qid: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    """收藏 / 取消收藏（同一个接口切换，前端不用记状态）。"""
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404, "题目不存在")
    row = db.query(QuestionFavorite).filter(
        QuestionFavorite.user_id == user.id,
        QuestionFavorite.question_id == qid).first()
    if row:
        db.delete(row)
        db.commit()
        return {"favored": False}
    db.add(QuestionFavorite(user_id=user.id, question_id=qid))
    db.commit()
    return {"favored": True}


@router.get("/leaderboard")
def leaderboard(scope: str = "class", grade: str = "", class_code: str = "",
                limit: int = 200,
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """排行榜：按年级/班级分组，组内按课程进度排名（同分看学号后两位）。

    scope=class 看指定班级；scope=grade 看整个年级。
    grade/class_code 不传时默认取当前登录人自己的年级和班级。
    """
    if scope not in ("class", "grade"):
        scope = "class"
    return growth.leaderboard(db, scope=scope, grade=grade, class_code=class_code,
                              me=user, limit=min(max(limit, 1), 500))


@router.get("/leaderboard/groups")
def leaderboard_groups(db: Session = Depends(get_db)):
    """年级 → 班级清单（筛选器用）。"""
    return growth.leaderboard_groups(db)


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
