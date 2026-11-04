"""成长相关路由：错题本、收藏、成就墙、每日任务、排行榜、能力雷达。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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


@router.get("/weekly-report")
def weekly_report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """本周学习报告：周一到周日。

    数据全部来自已有表，不新建「报告表」——报告是聚合视图，
    存一份下来只会和真实进度对不上。
    """
    from datetime import date, datetime, time, timedelta

    from ..models import Character, FocusSession, LearnProgress
    from ..seed import learn as seed_learn
    from ..services import growth as growth_svc

    today = date.today()
    start = today - timedelta(days=today.weekday())          # 本周一
    start_dt = datetime.combine(start, time.min)
    WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    rows = db.query(LearnProgress).filter(
        LearnProgress.user_id == user.id,
        LearnProgress.completed_at.is_not(None),
        LearnProgress.completed_at >= start_dt).all()

    per_day = [0] * 7
    subject_count: dict[str, int] = {}
    for r in rows:
        d = r.completed_at.date() if r.completed_at else None
        if d and 0 <= (d - start).days < 7:
            per_day[(d - start).days] += 1
        info = seed_learn.BY_CODE.get(r.point_code) or {}
        subject = info.get("subject") or "其他"
        subject_count[subject] = subject_count.get(subject, 0) + 1

    completed_total = db.query(func.count(LearnProgress.id)).filter(
        LearnProgress.user_id == user.id,
        LearnProgress.completed_at.is_not(None)).scalar() or 0

    wrong_rows = db.query(WrongAnswer).filter(
        WrongAnswer.user_id == user.id,
        WrongAnswer.created_at >= start_dt).all()
    wrong_total = db.query(func.count(WrongAnswer.id)).filter(
        WrongAnswer.user_id == user.id).scalar() or 0
    wrong_open = db.query(func.count(WrongAnswer.id)).filter(
        WrongAnswer.user_id == user.id,
        WrongAnswer.resolved.is_(False)).scalar() or 0

    focus_min = db.query(func.coalesce(func.sum(FocusSession.minutes), 0)).filter(
        FocusSession.user_id == user.id,
        FocusSession.started_at >= start_dt).scalar() or 0
    focus_days = db.query(func.count(func.distinct(func.date(FocusSession.started_at)))).filter(
        FocusSession.user_id == user.id,
        FocusSession.started_at >= start_dt).scalar() or 0

    ch = db.query(Character).filter(Character.user_id == user.id).first()

    # 连续学习天数：完成课程或专注任一件都算「这天有学」
    day_set = {str(r.completed_at.date()) for r in rows if r.completed_at}
    focus_day_rows = db.query(func.date(FocusSession.started_at)).filter(
        FocusSession.user_id == user.id).group_by(func.date(FocusSession.started_at)).all()
    day_set |= {str(r[0]) for r in focus_day_rows}
    streak, cursor = 0, today
    if str(cursor) not in day_set:
        cursor = today - timedelta(days=1)
    while str(cursor) in day_set:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "start": str(start),
        "end": str(start + timedelta(days=6)),
        "days": [{"date": str(start + timedelta(days=i)), "label": WEEK[i], "count": per_day[i]}
                 for i in range(7)],
        "completed": len(rows),
        "completed_total": int(completed_total),
        "total_lessons": len(seed_learn.BY_CODE),
        "subjects": [{"subject": s, "count": c}
                     for s, c in sorted(subject_count.items(), key=lambda kv: -kv[1])],
        "wrong_new": len(wrong_rows),
        "wrong_total": int(wrong_total),
        "wrong_open": int(wrong_open),
        "focus_minutes": int(focus_min),
        "focus_days": int(focus_days),
        "streak": streak,
        "level": ch.level if ch else 1,
        "title": growth_svc.title_of(ch.level) if ch else "拾荒者",
        "weekly_exp": ch.weekly_exp if ch else 0,
        "total_exp": ch.total_exp if ch else 0,
    }
