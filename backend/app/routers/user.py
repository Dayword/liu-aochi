"""用户与角色路由：新手引导、角色信息、个人中心。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (Achievement, Character, DailyTask, LearnProgress, Level,
                      User, UserAchievement, UserDailyTask,
                      UserLevelProgress, WrongAnswer)
from ..schemas import (CharacterOut, ClassInfo, LevelOut, ProfileOut,
                       ProfileUpdateIn, RadarOut, NAME_RE,
                       NAME_RULE_TEXT, STUDENT_ID_RE)
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/user", tags=["user"])

# 身份只允许这两个值（Onboarding 里的 Segmented 同款）
IDENTITY_OPTIONS = ("在校学生", "求职中")


@router.get("/classes", response_model=list[ClassInfo])
def classes():
    return [growth.class_info(k) for k in growth.CLASSES]


def _char_out(char: Character) -> CharacterOut:
    return CharacterOut(
        name=char.name, identity=char.identity, class_key=char.class_key,
        class_name=char.class_name, level=char.level, exp=char.exp,
        exp_to_next=growth.exp_to_next(char.level),
        title=growth.title_of(char.level),
        weekly_exp=char.weekly_exp, total_exp=char.total_exp,
        total_quests=char.total_quests,
        total_correct=char.total_correct, total_wrong=char.total_wrong,
        total_chats=char.total_chats, total_bugs=char.total_bugs,
        total_interviews=char.total_interviews, streak_days=char.streak_days,
        onboarding_done=char.onboarding_done)


@router.get("/character", response_model=CharacterOut)
def character(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 引导已下线：没有角色就现补一个，不再抛 400
    return _char_out(growth.ensure_character(db, user))


@router.get("/profile", response_model=ProfileOut)
def profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    growth.ensure_character(db, user)
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
                             "exp_reward": ach.exp_reward})
    daily_tasks = []
    day = growth.today_str()
    for ut in db.query(UserDailyTask).filter(
            UserDailyTask.user_id == user.id, UserDailyTask.task_date == day).all():
        task = db.query(DailyTask).filter(DailyTask.code == ut.task_code).first()
        if task:
            daily_tasks.append({"code": task.code, "name": task.name,
                                "description": task.description, "progress": ut.progress,
                                "target": task.target_value, "done": ut.done,
                                "claimed": ut.claimed,
                                "exp_reward": task.exp_reward})
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
    # 学习进度：已完成课时 / 总课时
    total_lessons = growth.learn_total()
    done_lessons = db.query(LearnProgress).filter(
        LearnProgress.user_id == user.id,
        LearnProgress.status == "completed").count()
    # 排名：班级 + 年级（没有学号的老账号返回空 dict）
    lb = growth.leaderboard(db, scope="class", me=user, limit=1)
    from ..models import QuestionFavorite
    fav_count = db.query(QuestionFavorite).filter(
        QuestionFavorite.user_id == user.id).count()
    return ProfileOut(character=_char_out(char), achievements=achievements,
                      daily_tasks=daily_tasks, wrong_count=wrong_count,
                      radar=RadarOut(**radar), recent_levels=recent,
                      student={"student_id": user.student_id,
                               "real_name": user.real_name or user.nickname,
                               "nickname": user.nickname,
                               "grade": user.grade, "class_code": user.class_code,
                               "seat_no": user.seat_no},
                      learn={"completed": done_lessons, "total": total_lessons,
                             "pct": round(done_lessons * 100 / total_lessons, 1) if total_lessons else 0},
                      rank=lb.get("me", {}),
                      achievement_families=growth.achievement_families(db, user),
                      favorites_count=fav_count)


@router.patch("/profile")
def update_profile(body: ProfileUpdateIn, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """修改个人资料。

    ⚠️ 2026-10-27 规则：**学号与姓名注册后不可修改**。
    - 已有值 → 传上来也直接 400，避免前端绕过校验悄悄改掉；
    - 只有库里为空时才允许写一次：这是给「改名之前注册的老账号」留的
      首次绑定口子（否则他们永远进不了班级排行榜）。
    - 昵称 / 身份随时可改。
    """
    if body.real_name is not None:
        name = body.real_name.strip()
        if user.real_name and name != user.real_name:
            raise HTTPException(400, "姓名注册后不可修改，如需更正请联系老师")
        if not NAME_RE.fullmatch(name):
            raise HTTPException(400, NAME_RULE_TEXT)
        user.real_name = name
    if body.student_id is not None:
        sid = body.student_id.strip()
        if user.student_id and sid != user.student_id:
            raise HTTPException(400, "学号注册后不可修改，如需更正请联系老师")
        if not STUDENT_ID_RE.fullmatch(sid):
            raise HTTPException(400, "学号必须是 11 位数字")
        if sid != user.student_id:
            dup = db.query(User).filter(User.student_id == sid,
                                        User.id != user.id).first()
            if dup:
                raise HTTPException(400, "该学号已被其他同学使用")
            if user.username == user.student_id:   # 新账号：用户名即学号，同步
                user.username = sid
            user.student_id = sid
    if body.nickname is not None:
        nick = body.nickname.strip()
        if len(nick) > 20:
            raise HTTPException(400, "昵称最多 20 个字")
        user.nickname = nick or user.real_name or "冒险者"
        if user.character:
            user.character.name = user.nickname
    if body.identity is not None:
        if body.identity not in IDENTITY_OPTIONS:
            raise HTTPException(400, "身份只能是「在校学生」或「求职中」")
        if user.character:
            user.character.identity = body.identity
    db.commit()
    db.refresh(user)
    return {"ok": True,
            "student": {"student_id": user.student_id,
                        "real_name": user.real_name or user.nickname,
                        "nickname": user.nickname,
                        "grade": user.grade, "class_code": user.class_code,
                        "seat_no": user.seat_no},
            "identity": user.character.identity if user.character else ""}

