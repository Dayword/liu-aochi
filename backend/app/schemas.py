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


# ---------- 引导式学习 ----------
class LearnPointBrief(BaseModel):
    code: str
    order_no: int        # 科目内序号
    title: str
    summary: str
    stage: str = ""      # 科目内的分组
    subject: str = ""    # 所属科目（前端按它分 Tab）
    runner: str = "python"   # python / sql / none —— 决定右侧写代码还是写 SQL
    status: str          # locked / unlocked / completed


class LearnQuizItem(BaseModel):
    """下发给前端的习题（不含答案与解析，判定在服务端做）。"""

    index: int
    type: str            # choice / judge / blank / short / applied
    stem: str
    options: list[str] = []
    hint: str = ""       # 填空提示，例如「一个单词」


class LearnQuizSubmitIn(BaseModel):
    code: str
    index: int
    answer: Any          # choice/判断用 int|bool，填空与主观题用 str


class LearnQuizResult(BaseModel):
    correct: Optional[bool] = None   # 主观题为 None —— 不阻塞通过，只给对照
    correct_answer: str = ""
    explanation: str = ""
    coverage: Optional[float] = None  # 主观题：提到了多少比例的关键要点
    missing: list[str] = []
    reference: str = ""              # 参考答案 / 答题要点
    lesson_completed: bool = False
    next_code: Optional[str] = None


class LearnPointDetail(LearnPointBrief):
    definition: str
    plain: str
    example: str
    example_output: str
    pitfalls: list[str]
    task: str
    setup: str           # 题目预置代码（用户不能改）
    starter: str         # 编辑器初始内容
    hint: str
    last_code: str = ""  # 上次写的代码
    has_task: bool = False       # 是否有动手写代码的题
    code_passed: bool = False
    quizzes: list[LearnQuizItem] = []
    quiz_state: dict = {}
    next_code: Optional[str] = None   # 课程里的下一个知识点（用于「已完成」时的跳转）


class LearnCheckIn(BaseModel):
    code: str
    user_code: str


class LearnCheckOut(BaseModel):
    passed: bool
    output: str = ""
    error: str = ""
    reason: str = ""     # 未通过时的可读原因
    solved: int = 0      # 通过了几组用例 / 共几组
    total: int = 0
    lesson_completed: bool = False    # 动手题与客观题都过关，整个知识点才算完成
    next_code: Optional[str] = None   # 通过后解锁的下一个知识点


class LearnHintIn(BaseModel):
    code: str
    user_code: str
    reason: str = ""


class LearnHintOut(BaseModel):
    hint: str


# ---------- 消消乐闯关 ----------
class Match3StartIn(BaseModel):
    level_code: str


class Match3StartOut(BaseModel):
    level_code: str
    name: str
    subject: str
    difficulty: int
    rows: int
    cols: int
    gem_types: int
    moves: int                 # 可用步数
    target_score: int          # 过关目标分


class Match3QuestionOut(BaseModel):
    question_id: int
    stem: str
    options: list[str]
    subject: str
    source: str                # ai / seed


class Match3AnswerIn(BaseModel):
    question_id: int
    answer_index: int


class Match3AnswerOut(BaseModel):
    correct: bool
    correct_index: int
    explanation: str


class Match3CompleteIn(BaseModel):
    level_code: str
    score: int
    moves_used: int


class Match3CompleteOut(BaseModel):
    completed: bool
    exp_gained: int
    coins_gained: int
    unlocked_next: Optional[str] = None


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
