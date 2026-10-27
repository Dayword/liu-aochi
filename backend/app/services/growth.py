"""成长体系核心逻辑：等级/经验/称号、成就判定、每日任务、排行榜。

⚠️ 经验规则（2026-10-27 定）：**全站经验只有「完成课时」一个来源**，每课 10 点。
闯关答题、关卡通关、成就、每日任务、Bug 猎人、面试都不再发经验 ——
`add_exp` 只剩 learn 路由一个调用方，改/加来源必须同步 `migrate_exp.py` 的重算口径，
否则用户的 total_exp 会和「已完成课时 × 10」对不上。
"""
from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models import (Achievement, Character, DailyTask, KnowledgeEntry,
                      Level, UserAchievement, UserDailyTask, UserLevelProgress,
                      User)

# 等级标题：满级 13（135 课全部学完 = 架构师）
TITLES = [(1, "实习生"), (5, "初级工程师"), (8, "中级工程师"),
          (11, "高级工程师"), (13, "架构师")]

# 每完成一个课时获得的经验
LESSON_EXP = 10

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
    """升到下一级所需经验（当前级内）。

    曲线按「135 课 × 10 点 = 1350 点刚好满级」反推：
    Σ(50 + 10(k-1)) for k=1..12 = 1260，加上最后一级的一点点正好 13 级。
    别随手改大 —— 改大之后没人能升到「架构师」，等级会变成一条死线。
    """
    return 50 + (level - 1) * 10


def level_of_total_exp(total: int) -> tuple[int, int]:
    """把累计经验折算成 (等级, 当前级内剩余经验)。"""
    level, rest = 1, max(0, int(total))
    while level < 99 and rest >= exp_to_next(level):
        rest -= exp_to_next(level)
        level += 1
    return level, rest


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
# 成就按「家族」组织：每个家族铜 → 银 → 金三档递进，同一指标不同门槛。
# 前端成就墙一个卡片 = 一个家族，点开弹窗看三档阶梯与当前进度。
# (code, 档位名, 描述, 目标值) —— 档位顺序即 铜/银/金
ACH_FAMILIES: list[dict] = [
    {"key": "lesson", "name": "课程进度", "icon": "📚", "category": "学习",
     "metric": "completed_lessons", "metric_label": "完成课时",
     "tiers": [
         ("lesson_10", "启程", "完成 10 个课时", 10),
         ("lesson_50", "过半", "完成 50 个课时", 50),
         ("lesson_100", "全书通关", "完成 100 个课时", 100),
     ]},
    {"key": "correct", "name": "刷题能手", "icon": "🎯", "category": "刷题",
     "metric": "total_correct", "metric_label": "累计答对",
     "tiers": [
         ("correct_10", "小试牛刀", "累计答对 10 道题", 10),
         ("correct_50", "刷题达人", "累计答对 50 道题", 50),
         ("correct_100", "百题斩", "累计答对 100 道题", 100),
     ]},
    {"key": "quest", "name": "闯关次数", "icon": "🗡️", "category": "学习",
     "metric": "total_quests", "metric_label": "通关次数",
     "tiers": [
         ("first_step", "初入江湖", "第一次通关关卡", 1),
         ("quest_10", "轻车熟路", "累计通关 10 次", 10),
         ("quest_50", "身经百战", "累计通关 50 次", 50),
     ]},
    {"key": "level", "name": "等级成长", "icon": "🚀", "category": "学习",
     "metric": "level_reach", "metric_label": "当前等级",
     "tiers": [
         ("level_5", "初级工程师", "等级达到 5 级", 5),
         ("level_8", "中级工程师", "等级达到 8 级", 8),
         ("level_13", "架构师", "等级达到 13 级（满级）", 13),
     ]},
    {"key": "chat", "name": "AI 陪练", "icon": "💬", "category": "社交",
     "metric": "total_chats", "metric_label": "对话次数",
     "tiers": [
         ("chat_5", "话痨养成", "与 AI 导师对话 5 次", 5),
         ("chat_20", "常驻对话", "与 AI 导师对话 20 次", 20),
         ("chat_50", "导师挚友", "与 AI 导师对话 50 次", 50),
     ]},
    {"key": "bug", "name": "Bug 猎人", "icon": "🐛", "category": "刷题",
     "metric": "total_bugs", "metric_label": "排查次数",
     "tiers": [
         ("bug_1", "Bug 猎手", "完成 1 次 Bug 猎人挑战", 1),
         ("bug_5", "Bug 终结者", "完成 5 次 Bug 猎人挑战", 5),
         ("bug_10", "代码清道夫", "完成 10 次 Bug 猎人挑战", 10),
     ]},
    {"key": "interview", "name": "模拟面试", "icon": "🎤", "category": "面试",
     "metric": "total_interviews", "metric_label": "面试场次",
     "tiers": [
         ("interview_1", "初面体验", "完成 1 次模拟面试", 1),
         ("interview_3", "面霸养成", "完成 3 次模拟面试", 3),
         ("interview_5", "Offer 收割机", "完成 5 次模拟面试", 5),
     ]},
    {"key": "class", "name": "关卡收集", "icon": "🌐", "category": "学习",
     "metric": "class_quests", "metric_label": "已通关关卡",
     "tiers": [
         ("class_5", "全栈挑战者", "通关 5 个不同关卡", 5),
         ("class_10", "地图探索家", "通关 10 个不同关卡", 10),
         ("class_20", "大陆征服者", "通关 20 个不同关卡", 20),
     ]},
]

TIER_NAMES = ["铜", "银", "金"]
TIER_ICONS = ["🥉", "🥈", "🥇"]


def _ach_trigger_type(db: Session, user: User) -> dict:
    char = user.character
    from ..models import LearnProgress
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
        "class_quests": db.query(UserLevelProgress).filter(
            UserLevelProgress.user_id == user.id,
            UserLevelProgress.status == "completed").count(),
        "completed_lessons": db.query(LearnProgress).filter(
            LearnProgress.user_id == user.id,
            LearnProgress.status == "completed").count(),
    }


def check_achievements(db: Session, user: User) -> list[Achievement]:
    """检查并发放新成就，返回本次新解锁列表。

    ⚠️ 解锁**不发经验**：经验只来自完成课时（见文件头注释）。
    """
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
            new.append(ach)
    if new:
        db.commit()
    return new


def achievement_families(db: Session, user: User) -> list[dict]:
    """成就墙数据：按家族聚合，带铜/银/金三档、当前值与下一档目标。"""
    triggers = _ach_trigger_type(db, user) if user.character else {}
    unlocked = {ua.achievement_code for ua in db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id).all()}
    out = []
    for fam in ACH_FAMILIES:
        current = int(triggers.get(fam["metric"], 0) or 0)
        tiers, next_target, got = [], None, 0
        for i, (code, name, desc, target) in enumerate(fam["tiers"]):
            got_tier = code in unlocked
            # 达标即视为解锁：成就记录要等下一次事件才补发（check_achievements），
            # 只看记录会让刚达成的人看到「目标 N」，和上面的进度条自相矛盾。
            reached = got_tier or current >= target
            got += 1 if reached else 0
            tiers.append({
                "code": code, "tier": TIER_NAMES[i], "tier_index": i,
                "icon": TIER_ICONS[i],
                "name": name, "description": desc, "target": target,
                "unlocked": reached,
            })
            if not reached and next_target is None:
                next_target = target
        out.append({"key": fam["key"], "name": fam["name"], "icon": fam["icon"],
                    "category": fam["category"], "metric": fam["metric"],
                    "metric_label": fam["metric_label"], "current": current,
                    "tiers": tiers, "unlocked_count": got,
                    "next_target": next_target})
    return out


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
    """领取每日任务。

    ⚠️ 2026-10-27 起**不再发经验**（经验只来自完成课时），领取只记录状态。
    任务系统本身先留着，等规则的其它经验来源确定后再接。
    """
    ensure_daily_tasks(db, user)
    day = today_str()
    ut = db.query(UserDailyTask).filter(
        UserDailyTask.user_id == user.id, UserDailyTask.task_code == task_code,
        UserDailyTask.task_date == day).first()
    if not ut or not ut.done:
        return {"ok": False, "msg": "任务尚未完成"}
    if ut.claimed:
        return {"ok": False, "msg": "已领取过奖励"}
    ut.claimed = True
    db.commit()
    return {"ok": True, "msg": "已完成", "exp": 0}


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
