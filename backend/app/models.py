"""SQLAlchemy ORM 模型：用户、角色、关卡、题库、成长体系等。"""
from datetime import datetime

from sqlalchemy import (JSON, Boolean, DateTime, ForeignKey, Integer, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now() -> datetime:
    return datetime.now()


# ---------- 用户与角色 ----------
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # username 是登录名：新账号直接用 11 位学号，老账号保留原用户名（双轨兼容）
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    nickname: Mapped[str] = mapped_column(String(64), default="")
    # 学号 11 位：前 4 位=年级，5~9 位=班级，后 2 位=班内座号（排行榜分组用）
    student_id: Mapped[str] = mapped_column(String(16), default="", index=True)
    real_name: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    @property
    def grade(self) -> str:
        """年级：学号前 4 位（如 2023）。"""
        return self.student_id[:4] if len(self.student_id) >= 11 else ""

    @property
    def class_code(self) -> str:
        """班级：学号第 5~9 位（5 位数字）。"""
        return self.student_id[4:9] if len(self.student_id) >= 11 else ""

    @property
    def seat_no(self) -> str:
        """班内座号：学号后 2 位。"""
        return self.student_id[-2:] if len(self.student_id) >= 11 else ""

    character: Mapped["Character"] = relationship(back_populates="user", uselist=False)


class Character(Base):
    """玩家角色（码境）。"""
    __tablename__ = "characters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), default="冒险者")
    identity: Mapped[str] = mapped_column(String(16), default="在校学生")  # 在校学生 / 求职中
    class_key: Mapped[str] = mapped_column(String(32), default="backend")  # 职业分支
    class_name: Mapped[str] = mapped_column(String(32), default="后端战士")
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)          # 当前等级内经验
    total_exp: Mapped[int] = mapped_column(Integer, default=0)    # 累计经验（排行榜用）
    coins: Mapped[int] = mapped_column(Integer, default=100)
    hp: Mapped[int] = mapped_column(Integer, default=3)
    max_hp: Mapped[int] = mapped_column(Integer, default=3)

    # 统计
    weekly_exp: Mapped[int] = mapped_column(Integer, default=0)
    total_quests: Mapped[int] = mapped_column(Integer, default=0)      # 完成闯关次数
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    total_wrong: Mapped[int] = mapped_column(Integer, default=0)
    total_chats: Mapped[int] = mapped_column(Integer, default=0)
    total_bugs: Mapped[int] = mapped_column(Integer, default=0)
    total_interviews: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)       # 连续签到
    last_sign_date: Mapped[str] = mapped_column(String(10), default="")  # yyyy-mm-dd
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False)
    # 上次打开的那一课。下次进「引导式学习」直接回到这里，而不是退回第一门没学完的课
    # （学生学到第 40 课，隔天进来又被扔回第 27 课，会以为进度丢了）。
    last_point_code: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    user: Mapped["User"] = relationship(back_populates="character")


# ---------- 关卡 ----------
class Level(Base):
    __tablename__ = "levels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    scene: Mapped[str] = mapped_column(String(64))          # 场景（章节）
    description: Mapped[str] = mapped_column(String(256), default="")
    difficulty: Mapped[int] = mapped_column(Integer, default=1)   # 1~5
    order_no: Mapped[int] = mapped_column(Integer, default=0)
    unlock_prev: Mapped[str] = mapped_column(String(32), default="")  # 前置关卡 code，空=新手村可直达
    subject: Mapped[str] = mapped_column(String(64), default="")      # 绑定学科/知识域
    tags: Mapped[list] = mapped_column(JSON, default=list)            # 知识点标签
    recommended_class: Mapped[str] = mapped_column(String(32), default="")  # 推荐职业
    base_exp: Mapped[int] = mapped_column(Integer, default=50)
    base_coins: Mapped[int] = mapped_column(Integer, default=20)
    hp: Mapped[int] = mapped_column(Integer, default=3)
    icon: Mapped[str] = mapped_column(String(32), default="🏰")


class UserLevelProgress(Base):
    __tablename__ = "user_level_progress"
    __table_args__ = (UniqueConstraint("user_id", "level_code", name="uq_user_level"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    level_code: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16), default="locked")  # locked/unlocked/completed
    best_score: Mapped[int] = mapped_column(Integer, default=0)        # 正确题目数
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LearnProgress(Base):
    """引导式学习的知识点进度：按顺序解锁，只有判定通过才算完成。"""

    __tablename__ = "learn_progress"
    __table_args__ = (UniqueConstraint("user_id", "point_code", name="uq_user_learn"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    point_code: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16), default="unlocked")  # unlocked/completed
    attempts: Mapped[int] = mapped_column(Integer, default=0)            # 运行判定的次数
    last_code: Mapped[str] = mapped_column(Text, default="")             # 上次写的代码，刷新后还能接着改
    code_passed: Mapped[bool] = mapped_column(Boolean, default=False)    # 动手题是否已通过
    quiz_json: Mapped[dict] = mapped_column(JSON, default=dict)          # 习题作答：{"0": {"correct": true}}
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewGuideProgress(Base):
    """面试题引导学习的进度：自己写的答案踩中要点到达阈值才算过关，分类内顺序解锁。"""

    __tablename__ = "interview_guide_progress"
    __table_args__ = (UniqueConstraint("user_id", "question_code", name="uq_user_interview_guide"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_code: Mapped[str] = mapped_column(String(32), index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    best_score: Mapped[int] = mapped_column(Integer, default=0)   # 历次最高分，只看这一项判定过关
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_answer: Mapped[str] = mapped_column(Text, default="")    # 上次写的回答，刷新后还能接着改
    passed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


# ---------- 题库 ----------
class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(16))   # choice/blank/short/code
    subject: Mapped[str] = mapped_column(String(64), index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1~5
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)   # 选择题选项
    answer: Mapped[dict] = mapped_column(JSON, default=dict)    # 见各题型
    explanation: Mapped[str] = mapped_column(Text, default="")
    knowledge_point: Mapped[str] = mapped_column(String(128), default="")
    source: Mapped[str] = mapped_column(String(64), default="seed")


class WrongAnswer(Base):
    __tablename__ = "wrong_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    user_answer: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(String(32), default="")  # 概念不清/计算错误/思路偏差
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class QuestionFavorite(Base):
    """题目收藏：用户手动点星标收藏，独立于错题本。"""

    __tablename__ = "question_favorites"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_favorite"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class GameRound(Base):
    """一局知识小游戏：题面与标准答案都留在服务端，前端只拿题面。

    payload 下发（含答对所需信息，让前端能即时反馈），answer 只用于判分。
    mode: match(连连看) / order(排序) / speed(竞速) / grid(网格消除)
    """

    __tablename__ = "game_rounds"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    level_code: Mapped[str] = mapped_column(String(32), index=True)
    mode: Mapped[str] = mapped_column(String(16), default="match")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    answer: Mapped[dict] = mapped_column(JSON, default=dict)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


# ---------- AI 对话 ----------
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mentor: Mapped[str] = mapped_column(String(32), default="老架构师")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    # 长期记忆：滑出对话窗口的旧轮次压缩成的一段事实清单，拼进 system 使用
    summary: Mapped[str] = mapped_column(Text, default="")
    # 已经压进 summary 的最后一条消息 id —— 增量摘要的游标，避免重复压缩同一段历史
    summary_upto_id: Mapped[int] = mapped_column(Integer, default=0)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user/assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class QuizRecord(Base):
    """AI 导师出过的练习题题面，用于保证同一个用户不会反复抽到同一道题。"""
    __tablename__ = "quiz_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stem: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


# ---------- 成就 / 每日任务 ----------
class Achievement(Base):
    __tablename__ = "achievements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(256), default="")
    icon: Mapped[str] = mapped_column(String(16), default="🏅")
    category: Mapped[str] = mapped_column(String(16), default="学习")  # 刷题/面试/学习/社交
    condition_type: Mapped[str] = mapped_column(String(32))  # 见 growth 服务
    condition_value: Mapped[int] = mapped_column(Integer, default=1)
    exp_reward: Mapped[int] = mapped_column(Integer, default=0)
    coin_reward: Mapped[int] = mapped_column(Integer, default=0)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_code", name="uq_user_ach"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    achievement_code: Mapped[str] = mapped_column(String(64))
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(256), default="")
    target_type: Mapped[str] = mapped_column(String(32))  # signin/quest_questions/chat/quest_pass/share
    target_value: Mapped[int] = mapped_column(Integer, default=1)
    exp_reward: Mapped[int] = mapped_column(Integer, default=20)
    coin_reward: Mapped[int] = mapped_column(Integer, default=10)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class UserDailyTask(Base):
    __tablename__ = "user_daily_tasks"
    __table_args__ = (UniqueConstraint("user_id", "task_code", "task_date", name="uq_user_task_date"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_code: Mapped[str] = mapped_column(String(64))
    task_date: Mapped[str] = mapped_column(String(10))  # yyyy-mm-dd
    progress: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    claimed: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------- 面试 ----------
class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    class_key: Mapped[str] = mapped_column(String(32), default="backend")
    company: Mapped[str] = mapped_column(String(64), default="字节跳动")
    difficulty: Mapped[int] = mapped_column(Integer, default=2)
    round_no: Mapped[int] = mapped_column(Integer, default=1)  # 1~4
    status: Mapped[str] = mapped_column(String(16), default="ongoing")  # ongoing/finished
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewMessage(Base):
    __tablename__ = "interview_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"), index=True)
    round_no: Mapped[int] = mapped_column(Integer, default=1)
    role: Mapped[str] = mapped_column(String(16))  # interviewer/candidate
    content: Mapped[str] = mapped_column(Text)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)  # 维度评分
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_key: Mapped[str] = mapped_column(String(32), default="common")
    round_no: Mapped[int] = mapped_column(Integer, default=1)
    category: Mapped[str] = mapped_column(String(32), default="技术")
    question: Mapped[str] = mapped_column(Text)
    sample_answer: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)  # 评分关键词
    difficulty: Mapped[int] = mapped_column(Integer, default=2)


# ---------- Bug 猎人 ----------
class BugChallenge(Base):
    __tablename__ = "bug_challenges"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    language: Mapped[str] = mapped_column(String(16), default="python")
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    bug_type: Mapped[str] = mapped_column(String(32))  # 语法/逻辑/性能/安全
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    buggy_code: Mapped[str] = mapped_column(Text)
    fixed_code: Mapped[str] = mapped_column(Text)
    test_cases: Mapped[list] = mapped_column(JSON, default=list)  # [{input, expected}]
    explanation: Mapped[str] = mapped_column(Text, default="")
    hint: Mapped[str] = mapped_column(String(256), default="")
    base_exp: Mapped[int] = mapped_column(Integer, default=40)
    base_coins: Mapped[int] = mapped_column(Integer, default=15)


class BugRound(Base):
    __tablename__ = "bug_rounds"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    bug_code: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    submitted_code: Mapped[str] = mapped_column(Text)
    accuracy: Mapped[float] = mapped_column(default=0.0)   # 测试通过率
    speed_ms: Mapped[int] = mapped_column(Integer, default=0)
    quality: Mapped[float] = mapped_column(default=0.0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


# ---------- 知识库（RAG-lite） ----------
class KnowledgeEntry(Base):
    __tablename__ = "knowledge_base"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    topic: Mapped[str] = mapped_column(String(128))
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(128), default="软件工程学习资料")


class FocusSession(Base):
    """一次番茄钟。只记时长，不参与经验/等级（经验只认课程完成）。"""

    __tablename__ = "focus_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CoachSession(Base):
    """一轮「选择题教练」练习：先规划知识点，再逐点闯关。

    用户给一个大范围（如「Python」）时，先由 AI 拆成由易到难的若干知识点，
    每个知识点连对 3 题过关，全部过关即结束。范围够小就只有一个知识点。
    """

    __tablename__ = "coach_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(80))
    # level 保留兼容：现在难度由「知识点内第几题」决定，不再靠连对/答错动态调
    level: Mapped[int] = mapped_column(Integer, default=1)
    # 已考过的考点，出题时传给模型避免重复
    asked: Mapped[list] = mapped_column(JSON, default=list)
    # ---- 知识点规划（2026-11-11）----
    # 由易到难的知识点名列表；至少 1 个（不拆时就是原 topic）
    plan: Mapped[list] = mapped_column(JSON, default=list)
    # 给用户看的那句「范围能不能再分」的说明
    plan_note: Mapped[str] = mapped_column(Text, default="")
    need_split: Mapped[bool] = mapped_column(Boolean, default=False)
    point_index: Mapped[int] = mapped_column(Integer, default=0)
    # 当前知识点已出过几题（决定本题难度：第 1 题基础 → 第 3 题起进阶）
    q_in_point: Mapped[int] = mapped_column(Integer, default=0)
    # 当前知识点内连续答对几题，满 3 过关；答错清零
    streak_in_point: Mapped[int] = mapped_column(Integer, default=0)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class CoachAttempt(Base):
    """一道题 + 用户的作答。

    ⚠️ 标准答案存这里，**不下发给前端** —— 前端只拿题干和选项，
    否则 F12 看一眼就把答案抄走了，整个判分失去意义。
    """

    __tablename__ = "coach_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("coach_sessions.id"), index=True)
    point: Mapped[str] = mapped_column(String(40), default="")
    # 这题属于规划里的第几个知识点，用于按知识点统计与生成总结
    point_index: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    reverse: Mapped[bool] = mapped_column(Boolean, default=False)
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_index: Mapped[int] = mapped_column(Integer, default=0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    # [{"index":1,"belief":"选它的人以为……"}]
    traps: Mapped[list] = mapped_column(JSON, default=list)
    # 反向题才有：逐项对错
    fact_check: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 代码题的答案是否经过真实执行核对
    verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    chosen: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # 选中错误项时，那一项对应的误解（trap.belief），用于错题清单
    belief: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
