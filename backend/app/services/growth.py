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


def ensure_character(db: Session, user: User) -> Character:
    """取角色；没有就补一个默认角色。

    2026-10-26 起新手引导（选职业方向 + 3 道能力初测）整体下线，
    注册成功即视为引导完成，登录后直接进首页。这里给存量账号兜底：
    老账号只要发过任何一次请求，就会补上角色，不会再被卡在 /welcome。
    """
    if user.character:
        # 老账号可能停在「引导未完成」状态（引导已下线），直接放行
        if not user.character.onboarding_done:
            user.character.onboarding_done = True
            db.commit()
        return user.character
    char = Character(
        user_id=user.id,
        name=(user.real_name or user.nickname or "冒险者")[:64],
        identity="在校学生",
        # 方向已不可选，统一用默认值；面试等模块仍按它取题库
        class_key="backend",
        class_name=CLASSES["backend"]["name"],
        onboarding_done=True,
    )
    db.add(char)
    db.commit()
    db.refresh(user)
    unlock_levels(db, user)
    return user.character


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
        ups += 1
    return ups


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
    ut.claimed = True
    db.commit()
    return {"ok": True, "msg": "领取成功", "exp": task.exp_reward if task else 0}


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


# ---------- 排行榜（学号体系） ----------
def learn_total() -> int:
    """课时总数（引导式学习 135 课，注册中心在 seed/learn.py）。"""
    from ..seed.learn import BY_CODE
    return len(BY_CODE)


def completed_map(db: Session) -> dict[int, int]:
    """每个用户已完成的课时数。"""
    from ..models import LearnProgress
    rows = (db.query(LearnProgress.user_id, func.count(LearnProgress.id))
            .filter(LearnProgress.status == "completed")
            .group_by(LearnProgress.user_id).all())
    return {int(uid): int(n) for uid, n in rows}


def _ranked_rows(db: Session, grade: str = "", class_code: str = "",
                 done: dict[int, int] | None = None,
                 total: int | None = None) -> list[dict]:
    """取一组人并按「进度降序 → 学号后两位升序」排好名次。

    只统计绑了 11 位学号的账号：老账号（用户名登录）不参与榜单。
    """
    done = completed_map(db) if done is None else done
    total = learn_total() if total is None else total
    q = (db.query(User, Character)
         .outerjoin(Character, Character.user_id == User.id)
         .filter(User.student_id != ""))
    if grade:
        q = q.filter(User.student_id.like(f"{grade}%"))
    if class_code:
        # 学号第 5~9 位 = 班级（MySQL SUBSTR 从 1 开始计数）
        q = q.filter(func.substr(User.student_id, 5, 5) == class_code)

    rows = []
    for u, c in q.all():
        rows.append({
            "student_id": u.student_id,
            "name": u.real_name or u.nickname or u.student_id,
            "seat_no": u.seat_no,
            "grade": u.grade,
            "class_code": u.class_code,
            "completed": done.get(u.id, 0),
            "total": total,
            "level": c.level if c else 1,
        })
    # 排序：进度优先；同分按学号后两位（默认座次）从小到大
    rows.sort(key=lambda r: (-r["completed"], int(r["seat_no"] or 99), r["student_id"]))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    return rows


def leaderboard(db: Session, scope: str = "class", grade: str = "",
                class_code: str = "", me: User | None = None,
                limit: int = 200) -> dict:
    """排行榜：scope=class 看本班，scope=grade 看本年级。"""
    total = learn_total()
    done = completed_map(db)

    me_grade = grade or (me.grade if me else "")
    me_class = class_code or (me.class_code if me and scope == "class" else "")

    items = _ranked_rows(db, grade=me_grade,
                         class_code=me_class if scope == "class" else "",
                         done=done, total=total)

    me_info: dict = {}
    if me and me.student_id:
        cls = _ranked_rows(db, grade=me.grade, class_code=me.class_code,
                           done=done, total=total)
        grd = _ranked_rows(db, grade=me.grade, done=done, total=total)
        cls_rank = next((r["rank"] for r in cls if r["student_id"] == me.student_id), 0)
        grd_rank = next((r["rank"] for r in grd if r["student_id"] == me.student_id), 0)
        me_info = {
            "student_id": me.student_id,
            "name": me.real_name or me.nickname,
            "grade": me.grade, "class_code": me.class_code, "seat_no": me.seat_no,
            "completed": done.get(me.id, 0), "total": total,
            "class_rank": cls_rank, "class_size": len(cls),
            "grade_rank": grd_rank, "grade_size": len(grd),
        }

    for r in items:
        r["is_me"] = bool(me and r["student_id"] == me.student_id)

    return {"scope": scope, "grade": me_grade,
            "class_code": me_class if scope == "class" else "",
            "total_lessons": total,
            "items": items[:limit], "me": me_info,
            "groups": leaderboard_groups(db)}


def leaderboard_groups(db: Session) -> list[dict]:
    """所有年级 → 班级 → 人数，供前端做筛选器。"""
    out: dict[str, dict[str, int]] = {}
    for (sid,) in db.query(User.student_id).filter(User.student_id != "").all():
        if len(sid) < 11:
            continue
        g, c = sid[:4], sid[4:9]
        out.setdefault(g, {})
        out[g][c] = out[g].get(c, 0) + 1
    return [{"grade": g,
             "classes": [{"code": c, "count": n} for c, n in sorted(v.items())]}
            for g, v in sorted(out.items(), reverse=True)]


# ---------- 能力雷达 ----------
# 六个维度 → 课程科目分组。雷达口径是**课时覆盖率**（该维度已完成课时 / 该维度总课时）。
#
# 为什么不用「答题正确率」：题目只记了错题（WrongAnswer），答对的没留痕，
# 旧实现把「没做过的题」当成答对，分母还算错成 1，导致 3100% 这种数把雷达撑爆画布。
# 课时进度是确定的数据，且与「学习进度」主指标一致。
RADAR_DIMENSIONS: list[tuple[str, list[str]]] = [
    ("数据结构", ["数据结构"]),
    ("算法", ["Python"]),                   # Python 主线含递归/排序/查找等算法内容
    ("操作系统", ["操作系统"]),
    ("计算机网络", ["计算机网络"]),
    ("数据库", ["MySQL", "Redis"]),
    ("软件工程", ["后端服务工程", "AI 工程质量", "多模态与部署",
                  "RAG 检索工程", "Transformer", "数据分析与处理"]),
]


def radar_data(db: Session, user: User) -> dict:
    """按科目课时完成率生成能力雷达（每个维度恒为 0~100）。"""
    from ..models import LearnProgress
    from ..seed.learn import BY_SUBJECT

    done_codes = {code for (code,) in db.query(LearnProgress.point_code).filter(
        LearnProgress.user_id == user.id,
        LearnProgress.status == "completed").all()}

    subjects, scores = [], []
    for label, group in RADAR_DIMENSIONS:
        total = sum(len(BY_SUBJECT.get(s, [])) for s in group)
        done = sum(1 for s in group for p in BY_SUBJECT.get(s, [])
                   if p["code"] in done_codes)
        subjects.append(label)
        scores.append(round(done / total * 100, 1) if total else 0)
    return {"subjects": subjects, "scores": scores}
