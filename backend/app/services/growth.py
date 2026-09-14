"""成长体系核心逻辑：等级/经验/代码币/称号、成就判定、每日任务、排行榜。"""
from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models import (Achievement, Character, DailyTask, KnowledgeEntry,
                      Level, UserAchievement, UserDailyTask, UserLevelProgress,
                      User)

# 等级标题（对应 实习生→初级→中级→高级→架构师）
TITLES = [(1, "实习生"), (10, "初级工程师"), (30, "中级工程师"), (50, "高级工程师"), (80, "架构师")]

CLASSES = {
    "frontend": {"name": "前端法师", "emoji": "🧙", "desc": "掌控 HTML/CSS/JS 与框架魔法，构建精美界面",
                 "stack": ["HTML/CSS", "JavaScript", "React/Vue", "工程化"], "mentors": ["前端导师·魔法师", "大厂面试官"]},
    "backend": {"name": "后端战士", "emoji": "⚔️", "desc": "Java/Python/Go 铁壁，数据库与微服务守护者",
                "stack": ["Java/Python/Go", "数据库", "Spring", "微服务"], "mentors": ["老架构师", "大厂面试官"]},
    "algorithm": {"name": "算法刺客", "emoji": "🗡️", "desc": "数据结构与算法之刃，LeetCode 王者",
                  "stack": ["数据结构", "算法", "LeetCode", "逻辑思维"], "mentors": ["学霸学长", "大厂面试官"]},
    "testing": {"name": "测试牧师", "emoji": "🛡️", "desc": "测试理论与自动化，质量守护神",
                "stack": ["测试理论", "自动化", "性能测试", "用例设计"], "mentors": ["测试大师", "大厂面试官"]},
    "devops": {"name": "运维骑士", "emoji": "🐴", "desc": "Linux/网络/云原生骑士，Docker/K8s 驾驭者",
               "stack": ["Linux", "网络", "云原生", "Docker/K8s"], "mentors": ["运维骑士长", "大厂面试官"]},
}


def class_info(key: str) -> dict:
    return {"key": key, **CLASSES.get(key, CLASSES["backend"])}


def title_of(level: int) -> str:
    t = TITLES[0][1]
    for lv, name in TITLES:
        if level >= lv:
            t = name
    return t


def exp_to_next(level: int) -> int:
    """升到下一级所需经验（当前级内）。"""
    return 100 + (level - 1) * 40


def add_exp(db: Session, char: Character, amount: int) -> int:
    """加经验并处理升级，返回升级次数。"""
    char.exp += max(0, int(amount))
    char.total_exp += max(0, int(amount))
    char.weekly_exp += max(0, int(amount))
    ups = 0
    while char.exp >= exp_to_next(char.level):
        char.exp -= exp_to_next(char.level)
        char.level += 1
        char.max_hp = 3 + char.level // 20  # 等级越高生命上限越高
        ups += 1
    return ups


def add_coins(db: Session, char: Character, amount: int) -> None:
    char.coins += max(0, int(amount))


# ---------- 成就 ----------
def _ach_trigger_type(db: Session, user: User) -> dict:
    char = user.character
    return {
        "level_reach": char.level,
        "total_exp": char.total_exp,
        "total_quests": char.total_quests,
        "total_correct": char.total_correct,
        "total_wrong": char.total_wrong,
        "total_chats": char.total_chats,
        "total_bugs": char.total_bugs,
        "total_interviews": char.total_interviews,
        "streak_days": char.streak_days,
        "coins": char.coins,
        "class_quests": db.query(UserLevelProgress).filter(
            UserLevelProgress.user_id == user.id,
            UserLevelProgress.status == "completed").count(),
    }


def check_achievements(db: Session, user: User) -> list[Achievement]:
    """检查并发放新成就，返回本次新解锁列表。"""
    if user.character is None:
        return []
    unlocked = {ua.achievement_code for ua in db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id).all()}
    triggers = _ach_trigger_type(db, user)
    new: list[Achievement] = []
    for ach in db.query(Achievement).all():
        if ach.code in unlocked:
            continue
        value = triggers.get(ach.condition_type)
        if value is None:
            continue
        if value >= ach.condition_value:
            db.add(UserAchievement(user_id=user.id, achievement_code=ach.code))
            add_exp(db, user.character, ach.exp_reward)
            add_coins(db, user.character, ach.coin_reward)
            new.append(ach)
    if new:
        db.commit()
    return new


# ---------- 每日任务 ----------
def today_str() -> str:
    return date.today().isoformat()


def ensure_daily_tasks(db: Session, user: User) -> None:
    """为新的一天初始化任务记录（同时重置任务进度）。"""
    day = today_str()
    for task in db.query(DailyTask).order_by(DailyTask.sort).all():
        exists = db.query(UserDailyTask).filter(
            UserDailyTask.user_id == user.id,
            UserDailyTask.task_code == task.code,
            UserDailyTask.task_date == day).first()
        if not exists:
            db.add(UserDailyTask(user_id=user.id, task_code=task.code, task_date=day,
                                 progress=0, done=False, claimed=False))
    db.commit()


def report_daily_event(db: Session, user: User, event_type: str, amount: int = 1) -> None:
    """按事件推进每日任务进度（event_type: signin/quest_questions/chat/quest_pass/share）。"""
    ensure_daily_tasks(db, user)
    day = today_str()
    for ut in db.query(UserDailyTask).filter(
            UserDailyTask.user_id == user.id, UserDailyTask.task_date == day).all():
        task = db.get(DailyTask, None) if False else db.query(DailyTask).filter(
            DailyTask.code == ut.task_code).first()
        if task and task.target_type == event_type and not ut.done:
            ut.progress = min(ut.progress + amount, task.target_value)
            if ut.progress >= task.target_value:
                ut.done = True
    db.commit()


def claim_daily_task(db: Session, user: User, task_code: str) -> dict:
    ensure_daily_tasks(db, user)
    day = today_str()
    ut = db.query(UserDailyTask).filter(
        UserDailyTask.user_id == user.id, UserDailyTask.task_code == task_code,
        UserDailyTask.task_date == day).first()
    if not ut or not ut.done:
        return {"ok": False, "msg": "任务尚未完成"}
    if ut.claimed:
        return {"ok": False, "msg": "已领取过奖励"}
    task = db.query(DailyTask).filter(DailyTask.code == task_code).first()
    if task:
        add_exp(db, user.character, task.exp_reward)
        add_coins(db, user.character, task.coin_reward)
    ut.claimed = True
    db.commit()
    return {"ok": True, "msg": "领取成功", "exp": task.exp_reward if task else 0,
            "coins": task.coin_reward if task else 0}


def sign_in(db: Session, user: User) -> dict:
    """每日签到：维护连续天数。"""
    char = user.character
    day = today_str()
    if char.last_sign_date == day:
        return {"ok": False, "msg": "今天已签到"}
    import datetime as dt
    yesterday = (date.today() - dt.timedelta(days=1)).isoformat()
    char.streak_days = char.streak_days + 1 if char.last_sign_date == yesterday else 1
    char.last_sign_date = day
    add_exp(db, char, 15)
    add_coins(db, char, 10)
    report_daily_event(db, user, "signin")
    new = check_achievements(db, user)
    db.commit()
    return {"ok": True, "msg": "签到成功", "exp": 15, "coins": 10,
            "streak": char.streak_days, "new_achievements": [a.code for a in new]}


# ---------- 关卡 ----------
def unlock_levels(db: Session, user: User) -> None:
    """依据前置关系批量解锁关卡（首关默认解锁）。"""
    all_levels = db.query(Level).order_by(Level.order_no).all()
    completed = {p.level_code for p in db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.status == "completed").all()}
    existing = {p.level_code: p for p in db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id).all()}
    for lv in all_levels:
        prog = existing.get(lv.code)
        if prog is None:
            prog = UserLevelProgress(user_id=user.id, level_code=lv.code, status="locked")
            db.add(prog)
            existing[lv.code] = prog
        if prog.status == "completed":
            continue
        if lv.unlock_prev in ("", None) or lv.unlock_prev in completed:
            if prog.status == "locked":
                prog.status = "unlocked"
    db.commit()


def mark_level_completed(db: Session, user: User, level_code: str, score: int) -> str | None:
    """标记通关并返回新解锁的关卡 code。"""
    prog = db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.level_code == level_code).first()
    if prog is None:
        prog = UserLevelProgress(user_id=user.id, level_code=level_code, status="completed")
        db.add(prog)
    prog.status = "completed"
    prog.best_score = max(prog.best_score, score)
    prog.completed_at = datetime.now()
    db.commit()
    unlock_levels(db, user)
    newly = db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.status == "unlocked").order_by(UserLevelProgress.id.desc()).limit(1).first()
    return newly.level_code if newly else None


# ---------- 排行榜 ----------
def rebuild_leaderboard(db: Session, user: User) -> None:
    """按本周累计经验写入 Redis ZSet（周榜），失败则静默降级为 DB 计算。"""
    try:
        from ..config import settings
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, decode_responses=True)
        iso = date.today().isocalendar()
        week_key = f"lb:week:{iso[0]}-{iso[1]}"
        r.zadd(week_key, {str(user.id): user.character.weekly_exp})
        r.expire(week_key, 60 * 60 * 24 * 8)
    except Exception:
        pass


def leaderboard(db: Session, board: str = "total", limit: int = 20,
                class_key: str | None = None) -> list[dict]:
    """排行榜：total=总榜 class=方向榜（限定某个职业方向）week=周榜。"""
    q = db.query(Character).join(User).filter(Character.onboarding_done.is_(True))
    if board == "class" and class_key:
        q = q.filter(Character.class_key == class_key)
    q = q.order_by(Character.total_exp.desc())
    if board == "week":
        # 周榜优先取 Redis，失败取 DB weekly_exp
        try:
            from ..config import settings
            import redis
            r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, decode_responses=True)
            iso = date.today().isocalendar()
            week_key = f"lb:week:{iso[0]}-{iso[1]}"
            ids = r.zrevrange(week_key, 0, limit - 1)
            if ids:
                chars = {str(c.user_id): c for c in db.query(Character).filter(
                    Character.user_id.in_([int(i) for i in ids])).all()}
                rows = []
                for i, uid in enumerate(ids):
                    c = chars.get(uid)
                    if c:
                        rows.append(_entry(c, i + 1, weekly=c.weekly_exp))
                if rows:
                    return rows
        except Exception:
            pass
        q = q.order_by(Character.weekly_exp.desc())
    rows = q.limit(limit).all()
    return [_entry(c, i + 1, weekly=c.weekly_exp) for i, c in enumerate(rows)]


def _entry(c: Character, rank: int, weekly: int = 0) -> dict:
    return {"rank": rank, "nickname": c.user.nickname or c.user.username,
            "character_name": c.name, "class_name": c.class_name,
            "level": c.level, "total_exp": c.total_exp, "weekly_exp": weekly}


# ---------- 能力雷达 ----------
def radar_data(db: Session, user: User) -> dict:
    """按学科正确率生成能力雷达（无数据学科给 0）。"""
    from ..models import Question, WrongAnswer
    char = user.character
    if char.total_correct + char.total_wrong == 0:
        subjects = ["数据结构", "算法", "操作系统", "计算机网络", "数据库", "软件工程"]
        return {"subjects": subjects, "scores": [0] * 6}
    wrong_qids = {w.question_id for w in db.query(WrongAnswer).filter(
        WrongAnswer.user_id == user.id).all()}
    qs = db.query(Question).all()
    stats: dict[str, list[int]] = {}
    for q in qs:
        if q.id in wrong_qids:
            stats.setdefault(q.subject, [0, 1])[1] += 1
        else:
            stats.setdefault(q.subject, [0, 1])[0] += 1
    subjects = ["数据结构", "算法", "操作系统", "计算机网络", "数据库", "软件工程"]
    scores = []
    for s in subjects:
        right, total = stats.get(s, (0, 0))
        scores.append(round(right / total * 100, 1) if total else 0)
    return {"subjects": subjects, "scores": scores}
