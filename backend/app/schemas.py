"""Pydantic 请求/响应模型。"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- 认证 ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=32)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- 角色 ----------
class OnboardIn(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    identity: str = "在校学生"          # 在校学生 / 求职中
    class_key: str = "backend"
    answers: list[int] = []            # 3 道入门测试题的选项索引


class ClassInfo(BaseModel):
    key: str
    name: str
    emoji: str
    desc: str
    stack: list[str]
    mentors: list[str]


class CharacterOut(BaseModel):
    name: str
    identity: str
    class_key: str
    class_name: str
    level: int
    exp: int
    exp_to_next: int
    coins: int
    hp: int
    max_hp: int
    title: str
    weekly_exp: int
    total_exp: int
    total_quests: int
    total_correct: int
    total_wrong: int
    total_chats: int
    total_bugs: int
    total_interviews: int
    streak_days: int
    onboarding_done: bool


# ---------- 关卡 ----------
class LevelOut(BaseModel):
    code: str
    name: str
    scene: str
    description: str
    difficulty: int
    order_no: int
    unlock_prev: str
    subject: str
    tags: list
    recommended_class: str
    base_exp: int
    base_coins: int
    hp: int
    icon: str
    status: str = "locked"   # locked/unlocked/completed
    best_score: int = 0
    attempts: int = 0
    completed: bool = False


class LevelMapOut(BaseModel):
    scenes: list[dict]
    levels: list[LevelOut]


# ---------- 闯关 ----------
class QuestStartIn(BaseModel):
    level_code: str
    mode: str = "normal"   # normal / wrong_review / speed


class QuestStartOut(BaseModel):
    run_id: str
    level_code: str
    total: int = 10
    hp: int = 3
    mode: str = "normal"


class QuestQuestionOut(BaseModel):
    question_id: int
    type: str
    stem: str
    options: list
    difficulty: int
    subject: str
    index: int          # 第几题（1-based）
    is_code: bool = False
    starter_code: str = ""


class AnswerIn(BaseModel):
    run_id: str
    question_id: int
    answer: Any = None   # choice: 选项索引; blank/code: 文本; short: 文本


class AnswerOut(BaseModel):
    correct: bool
    explanation: str
    knowledge_point: str
    user_answer: Any = None
    expected_answer: Any = None
    ai_analysis: str = ""          # 追问/AI 解析
    hp_left: int
    coins_gained: int
    exp_gained: int
    difficulty_now: int
    finished: bool = False         # 10 题答完
    level_failed: bool = False     # HP 耗尽


class SettlementOut(BaseModel):
    run_id: str
    level_code: str
    correct_count: int
    wrong_count: int
    accuracy: float
    total_exp: int
    total_coins: int
    level_completed: bool
    unlocked_next: Optional[str] = None
    new_achievements: list[dict] = []
    score: int


# ---------- AI 对话 ----------
class ChatIn(BaseModel):
    mentor: str = "老架构师"
    message: str
    session_id: Optional[int] = None


# ---------- 面试 ----------
class InterviewStartIn(BaseModel):
    class_key: str = "backend"
    company: str = "字节跳动"
    difficulty: int = 2


class InterviewStartOut(BaseModel):
    session_id: int
    round_no: int = 1
    total_rounds: int = 4
    interviewer_name: str
    question: str
    category: str


class InterviewAnswerIn(BaseModel):
    session_id: int
    answer: str


class InterviewAnswerOut(BaseModel):
    session_id: int
    round_no: int
    next_question: str = ""
    next_category: str = ""
    round_finished: bool = False
    round_scores: dict = {}
    interview_finished: bool = False
    report: dict = {}


# ---------- Bug 猎人 ----------
class BugListOut(BaseModel):
    code: str
    title: str
    description: str
    bug_type: str
    difficulty: int
    hint: str
    language: str


class BugChallengeOut(BaseModel):
    code: str
    title: str
    description: str
    bug_type: str
    difficulty: int
    language: str
    buggy_code: str
    hint: str
    test_cases_preview: list


class BugSubmitIn(BaseModel):
    bug_code: str
    code: str


class BugSubmitOut(BaseModel):
    score: int
    accuracy: float
    speed_ms: int
    quality: float
    tests_passed: int
    tests_total: int
    passed: bool
    results: list[dict]
    explanation: str
    exp_gained: int
    coins_gained: int
    new_achievements: list[dict] = []


# ---------- 代码运行 ----------
class CodeRunIn(BaseModel):
    language: str = "python"
    code: str
    stdin: str = ""


class CodeRunOut(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    time_ms: int


# ---------- 成长 ----------
class AchievementOut(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    category: str
    unlocked: bool
    unlocked_at: Optional[datetime] = None
    exp_reward: int = 0
    coin_reward: int = 0


class DailyTaskOut(BaseModel):
    code: str
    name: str
    description: str
    progress: int
    target: int
    done: bool
    claimed: bool
    exp_reward: int
    coin_reward: int


class WrongAnswerOut(BaseModel):
    id: int
    question_id: int
    stem: str
    subject: str
    difficulty: int
    user_answer: Any
    correct_answer: Any
    explanation: str
    knowledge_point: str
    reason: str
    resolved: bool
    created_at: datetime


class LeaderboardEntry(BaseModel):
    rank: int
    nickname: str
    character_name: str
    class_name: str
    level: int
    total_exp: int
    weekly_exp: int = 0


class RadarOut(BaseModel):
    subjects: list[str]
    scores: list[float]


class ProfileOut(BaseModel):
    character: CharacterOut
    achievements: list[AchievementOut]
    daily_tasks: list[DailyTaskOut]
    wrong_count: int
    radar: RadarOut
    recent_levels: list[dict]
