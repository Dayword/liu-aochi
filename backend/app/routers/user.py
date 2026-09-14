"""用户与角色路由：新手引导、角色信息、个人中心。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (Achievement, Character, DailyTask, Level, Question,
                      User, UserAchievement, UserDailyTask, UserLevelProgress,
                      WrongAnswer)
from ..schemas import (CharacterOut, ClassInfo, LevelOut, OnboardIn, ProfileOut,
                       RadarOut)
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/classes", response_model=list[ClassInfo])
def classes():
    return [growth.class_info(k) for k in growth.CLASSES]


def _char_out(char: Character) -> CharacterOut:
    return CharacterOut(
        name=char.name, identity=char.identity, class_key=char.class_key,
        class_name=char.class_name, level=char.level, exp=char.exp,
        exp_to_next=growth.exp_to_next(char.level), coins=char.coins,
        hp=char.hp, max_hp=char.max_hp, title=growth.title_of(char.level),
        weekly_exp=char.weekly_exp, total_exp=char.total_exp,
        total_quests=char.total_quests,
        total_correct=char.total_correct, total_wrong=char.total_wrong,
        total_chats=char.total_chats, total_bugs=char.total_bugs,
        total_interviews=char.total_interviews, streak_days=char.streak_days,
        onboarding_done=char.onboarding_done)


@router.get("/character", response_model=CharacterOut)
def character(user: User = Depends(get_current_user)):
    if not user.character:
        raise HTTPException(400, "尚未创建角色，请先完成新手引导")
    return _char_out(user.character)


@router.get("/onboard-questions")
def onboard_questions(db: Session = Depends(get_db)):
    """3 道入门测试题（新手引导用，答对 2 道初始 2 级）。"""
    qs = db.query(Question).filter(Question.type == "choice",
                                   Question.difficulty == 1).limit(3).all()
    return [{"question_id": q.id, "type": q.type, "stem": q.stem,
             "options": q.options or [], "difficulty": q.difficulty,
             "subject": q.subject, "index": i + 1, "is_code": False,
             "starter_code": ""} for i, q in enumerate(qs)]


@router.post("/onboard", response_model=CharacterOut)
def onboard(body: OnboardIn, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    if user.character and user.character.onboarding_done:
        raise HTTPException(400, "已完成新手引导")
    if body.class_key not in growth.CLASSES:
        raise HTTPException(400, "未知职业方向")
    info = growth.class_info(body.class_key)
    if user.character is None:
        char = Character(user_id=user.id)
        db.add(char)
        db.flush()
    else:
        char = user.character
    char.name = body.name
    char.identity = body.identity if body.identity in ("在校学生", "求职中") else "在校学生"
    char.class_key = body.class_key
    char.class_name = info["name"]

    # 3 道入门测试题：评估初始等级（答对 2 道以上 → 2 级，否则 1 级）
    test_qs = db.query(Question).filter(Question.type == "choice",
                                        Question.difficulty == 1).limit(3).all()
    score = 0
    for i, q in enumerate(test_qs[:3]):
        ans = body.answers[i] if i < len(body.answers) else -1
        if q.answer.get("correct_index") == ans:
            score += 1
    char.level = 2 if score >= 2 else 1
    char.max_hp = 3 + char.level // 20
    char.hp = char.max_hp
    char.onboarding_done = True
    char.coins = max(char.coins, 100)
    db.commit()
    growth.unlock_levels(db, user)
    return _char_out(char)


@router.get("/profile", response_model=ProfileOut)
def profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.character or not user.character.onboarding_done:
        raise HTTPException(400, "尚未完成新手引导")
    growth.ensure_daily_tasks(db, user)
    char = user.character
    achievements = []
    unlocked = {ua.achievement_code: ua for ua in db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id).all()}
    for ach in db.query(Achievement).order_by(Achievement.id).all():
        ua = unlocked.get(ach.code)
        achievements.append({"code": ach.code, "name": ach.name,
                             "description": ach.description, "icon": ach.icon,
                             "category": ach.category,
                             "unlocked": ua is not None,
                             "unlocked_at": ua.unlocked_at if ua else None,
                             "exp_reward": ach.exp_reward, "coin_reward": ach.coin_reward})
    daily_tasks = []
    day = growth.today_str()
    for ut in db.query(UserDailyTask).filter(
            UserDailyTask.user_id == user.id, UserDailyTask.task_date == day).all():
        task = db.query(DailyTask).filter(DailyTask.code == ut.task_code).first()
        if task:
            daily_tasks.append({"code": task.code, "name": task.name,
                                "description": task.description, "progress": ut.progress,
                                "target": task.target_value, "done": ut.done,
                                "claimed": ut.claimed, "exp_reward": task.exp_reward,
                                "coin_reward": task.coin_reward})
    wrong_count = db.query(WrongAnswer).filter(WrongAnswer.user_id == user.id).count()
    radar = growth.radar_data(db, user)
    recent = []
    for prog in db.query(UserLevelProgress).filter(
            UserLevelProgress.user_id == user.id,
            UserLevelProgress.status == "completed").order_by(
            UserLevelProgress.completed_at.desc()).limit(5).all():
        lv = db.query(Level).filter(Level.code == prog.level_code).first()
        if lv:
            recent.append({"code": lv.code, "name": lv.name, "icon": lv.icon,
                           "best_score": prog.best_score})
    return ProfileOut(character=_char_out(char), achievements=achievements,
                      daily_tasks=daily_tasks, wrong_count=wrong_count,
                      radar=RadarOut(**radar), recent_levels=recent)


@router.post("/signin")
def signin(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return growth.sign_in(db, user)
