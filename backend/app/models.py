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
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    nickname: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    character: Mapped["Character"] = relationship(back_populates="user", uselist=False)


class Character(Base):
    """玩家角色（代码冒险者）。"""
    __tablename__ = "characters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), default="代码冒险者")
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


# ---------- AI 对话 ----------
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mentor: Mapped[str] = mapped_column(String(32), default="老架构师")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


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
