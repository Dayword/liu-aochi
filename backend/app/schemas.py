"""Pydantic 请求/响应模型。"""
import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------- 认证 ----------
# 学号 11 位：前 4 位年级 / 5~9 位班级 / 后 2 位班内座号
STUDENT_ID_RE = re.compile(r"\d{11}")
# 姓名必须是中文：2~10 个汉字，允许少数民族姓名的间隔号「·」
NAME_RE = re.compile(r"[\u4e00-\u9fa5·]{2,10}")
NAME_RULE_TEXT = "姓名必须是中文（2~10 个汉字），不能填数字或英文"
PASSWORD_RULE_TEXT = "密码需 8~64 位，且同时含大写字母、小写字母、数字、特殊符号"


def password_problems(pwd: str) -> list[str]:
    """返回缺失的字符类别，供前后端共用同一套规则文案。"""
    missing = []
    if not re.search(r"[A-Z]", pwd):
        missing.append("大写字母")
    if not re.search(r"[a-z]", pwd):
        missing.append("小写字母")
    if not re.search(r"\d", pwd):
        missing.append("数字")
    if not re.search(r"[^A-Za-z0-9\s]", pwd):
        missing.append("特殊符号")
    return missing


class RegisterIn(BaseModel):
    student_id: str = Field(description="11 位学号")
    real_name: str = Field(description="真实姓名，排行榜展示用")
    password: str
    confirm_password: str

    @field_validator("student_id")
    @classmethod
    def _check_student_id(cls, v: str) -> str:
        v = (v or "").strip()
        if not STUDENT_ID_RE.fullmatch(v):
            raise ValueError("学号必须是 11 位数字")
        return v

    @field_validator("real_name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        v = (v or "").strip()
        if not NAME_RE.fullmatch(v):
            raise ValueError(NAME_RULE_TEXT)
        return v

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        if not 8 <= len(v) <= 64:
            raise ValueError(PASSWORD_RULE_TEXT)
        missing = password_problems(v)
        if missing:
            raise ValueError(f"密码缺少：{'、'.join(missing)}")
        return v

    @model_validator(mode="after")
    def _check_confirm(self):
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


class LoginIn(BaseModel):
    # 学号登录；兼容老账号（原用户名）
    student_id: str
    password: str

    @field_validator("student_id")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("请输入学号")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- 角色 ----------
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
    exp_gained: int
    difficulty_now: int
    finished: bool = False         # 10 题答完


class SettlementOut(BaseModel):
    run_id: str
    level_code: str
    correct_count: int
    wrong_count: int
    accuracy: float
    total_exp: int
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


class SketchNode(BaseModel):
    """手绘知识图上的一个节点。"""

    id: str
    label: str
    kind: str            # core 本课知识点 / prev 前置课 / next 后续课 / side 跨科目旁支
    zone: str            # t tr r br b bl l tl —— 挂在中心的哪个方向
    code: str = ""       # 非空 = 可以点，跳到那一课


class SketchEdge(BaseModel):
    a: str               # 起点节点 id；"center" 表示中心节点
    b: str
    label: str = ""      # 关系词，例如「条件为真才进」


class LessonSketch(BaseModel):
    center: str
    nodes: list[SketchNode]
    edges: list[SketchEdge]


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
    # 本课开头的一句话：讲什么 + 学完能做什么。
    # 没铺到的课留空，前端自动退回 summary（见 seed/learn_sketch.py 的覆盖进度说明）。
    oneliner: str = ""
    # 手绘知识图：本课知识点之间、以及和前后课/跨科目的联系。没铺到就是 None。
    sketch: Optional[LessonSketch] = None
    # 讲解视频的分镜脚本；由 build_lesson_videos.py 在构建期生成，
    # 缺失（比如还没跑过构建脚本）时为 None，前端就不显示视频入口。
    video: Optional[dict] = None
    # 「项目实地」：这个知识点在鸭先知 RAG 项目里的真实落点。
    # 结构见 app/seed/learn_project_base.py；kind=used/absent，缺数据时前端不显示。
    project: Optional[dict] = None


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


# ---------- 面试题引导学习 ----------
class InterviewGuideBrief(BaseModel):
    code: str
    order_no: int
    stage: str            # 分类（9 类之一），也是分类内的解锁分组
    title: str            # 面试官原话
    summary: str
    status: str           # locked / unlocked / completed
    best_score: int = 0
    min_score: int = 70


class InterviewGuideDetail(InterviewGuideBrief):
    definition: str       # 考察点
    plain: str            # 大白话拆解
    example: str          # 满分回答（前端在提交后才展示）
    pitfalls: list[str]   # 4 条「这么说会减分」
    followups: list[dict] # 2~3 条追问链
    answer_hint: str      # 卡住时的一句话提示
    last_answer: str = ""
    next_code: Optional[str] = None


class InterviewGuideAnswerIn(BaseModel):
    code: str
    answer: str


class InterviewGuideAnswerOut(BaseModel):
    score: int
    passed: bool           # 本次是否达标
    min_score: int
    hit_keywords: list[str]     # 踩中的要点
    missed_keywords: list[str]  # 漏掉的要点 —— 也是「你漏了什么」的反馈来源
    comment: str           # 点评
    attempts: int
    best_score: int
    already_passed: bool = False   # 这题在此前是否已过关
    next_code: Optional[str] = None


class InterviewGuideHintIn(BaseModel):
    code: str
    answer: str = ""


class InterviewGuideHintOut(BaseModel):
    hint: str


# ---------- 知识小游戏 ----------
class GameStartIn(BaseModel):
    level_code: str


class GameStartOut(BaseModel):
    round_id: int
    level_code: str
    name: str
    subject: str
    difficulty: int
    mode: str                  # match / order / speed / grid
    mode_name: str             # 中文玩法名
    rule: str                  # 一句话规则
    time_limit: int            # 秒，0 = 不限时
    # 各玩法自己的题面，结构见 routers/games.py 顶部注释
    payload: dict


class GameSubmitIn(BaseModel):
    round_id: int
    # match/grid: {"pairs": [{"l": token, "r": token}, ...]}
    # order:      {"steps": [token, ...]}
    # speed:      {"picks": [{"qid": 1, "picked": 0}, ...]}
    data: dict
    elapsed: int = 0           # 前端计时秒数，仅用于展示


class GamePairResult(BaseModel):
    """每对/每步的对错，前端用来高亮。"""

    key: str
    correct: bool


class GameSubmitOut(BaseModel):
    passed: bool
    stars: int                 # 0~3
    accuracy: float            # 0~100
    correct: int
    total: int
    detail: list[GamePairResult] = []
    answers: dict = {}         # 正确答案（错题讲解用）
    unlocked_next: Optional[str] = None
    best_stars: int = 0


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


class AchievementTierOut(BaseModel):
    code: str
    tier: str                  # 铜 / 银 / 金
    tier_index: int            # 0/1/2
    name: str
    description: str
    target: int
    unlocked: bool


class AchievementFamilyOut(BaseModel):
    """成就家族：一个主题下铜-银-金三档递进。"""

    key: str
    name: str
    icon: str
    category: str
    metric: str                # 对应 Character 上的统计字段
    metric_label: str          # 「完成课时」「累计答对」…
    current: int               # 当前值
    tiers: list[AchievementTierOut]
    unlocked_count: int
    next_target: Optional[int] = None   # 下一档目标，全解锁为 None



class DailyTaskOut(BaseModel):
    code: str
    name: str
    description: str
    progress: int
    target: int
    done: bool
    claimed: bool
    exp_reward: int


class WrongAnswerOut(BaseModel):
    id: int
    question_id: int
    stem: str
    type: str = "choice"
    subject: str
    difficulty: int
    options: list = []
    user_answer: Any
    correct_answer: Any
    explanation: str
    knowledge_point: str
    reason: str
    resolved: bool
    created_at: datetime


class FavoriteOut(BaseModel):
    """收藏的题目（结构对齐错题本，前端可以复用同一套卡片）。"""

    id: int
    question_id: int
    stem: str
    type: str
    subject: str
    difficulty: int
    options: list = []
    correct_answer: Any = None
    explanation: str = ""
    knowledge_point: str = ""
    created_at: datetime


class LeaderboardEntry(BaseModel):
    rank: int                 # 组内名次
    student_id: str           # 学号（11 位）
    name: str                 # 姓名
    seat_no: str              # 学号后两位（同分时的默认座次）
    grade: str                # 年级 = 学号前 4 位
    class_code: str           # 班级 = 学号 5~9 位
    completed: int            # 已完成课时数（主排序）
    total: int                # 课时总数
    level: int
    is_me: bool = False


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
    # 学号体系（2026-10-26 新增）
    student: dict = {}
    learn: dict = {}
    rank: dict = {}
    # 成就墙（2026-10-27）：按家族聚合的铜/银/金阶梯
    achievement_families: list[AchievementFamilyOut] = []
    favorites_count: int = 0


class ProfileUpdateIn(BaseModel):
    """个人资料修改。

    ⚠️ 学号与姓名**注册后不可修改**（要求见 2026-10-27 需求）：
    这里保留字段只为兼容老账号「首次绑定」（库里为空时才允许写一次），
    已有值再传会被路由明确拒绝。
    """
    real_name: Optional[str] = None
    nickname: Optional[str] = None
    student_id: Optional[str] = None
    identity: Optional[str] = None
