"""AI Agent 岗面试题 · 引导式学习总入口。

与 `learn.py`（知识点引导学习）是一套思路的两种内容：
题目不是「知识点」，而是**面试官会问的原话**；学生先看考察点和大白话拆解，
再**自己写一段回答**，踩中 `answer_keywords` 到 `answer_min_score` 才算过关，
过关才解锁同一分类的下一题。

内容按分类拆在 9 个文件里，这里统一汇总。**分类顺序 = 学习链顺序**：
先懂模型原理，再学怎么指挥它（Prompt/RAG/记忆/工具），然后才是怎么把它组装成
Agent、怎么评测、怎么上线，最后才是行为面（行为面永远排最后）。
"""

from .agent_interview_agent import QUESTIONS as AGENT
from .agent_interview_behavioral import QUESTIONS as BEHAVIORAL
from .agent_interview_eng import QUESTIONS as ENG
from .agent_interview_eval import QUESTIONS as EVAL
from .agent_interview_llm import QUESTIONS as LLM
from .agent_interview_memory import QUESTIONS as MEMORY
from .agent_interview_prompt import QUESTIONS as PROMPT
from .agent_interview_rag import QUESTIONS as RAG
from .agent_interview_tool import QUESTIONS as TOOL

# 分类键 → 该分类的题目。顺序即学习顺序，前端 Tab 与进度都按它走。
TRACKS: list[tuple[str, list[dict]]] = [
    ("LLM 基础与原理", LLM),
    ("Prompt 工程与上下文", PROMPT),
    ("RAG 与知识检索", RAG),
    ("记忆与状态管理", MEMORY),
    ("Function Calling 与工具设计", TOOL),
    ("Agent 架构与循环", AGENT),
    ("评测与可观测性", EVAL),
    ("工程化与安全合规", ENG),
    ("项目复盘与行为面", BEHAVIORAL),
]

# 分类名 → 该分类的题目，order_no 在分类内从 1 重新编号
BY_STAGE: dict[str, list[dict]] = {
    name: [{**q, "order_no": i + 1} for i, q in enumerate(questions)]
    for name, questions in TRACKS
}

STAGES: list[str] = [name for name, _ in TRACKS]

QUESTIONS: list[dict] = [q for stage in STAGES for q in BY_STAGE[stage]]

BY_CODE: dict[str, dict] = {q["code"]: q for q in QUESTIONS}

# 全部题目共用一套阈值语义，但阈值本身来自题目自己的 answer_min_score
DEFAULT_MIN_SCORE = 70


def min_score(question: dict) -> int:
    return int(question.get("answer_min_score") or DEFAULT_MIN_SCORE)


def next_code(code: str) -> str | None:
    """同一分类里的下一题；已经是该分类最后一题就返回 None。"""
    question = BY_CODE.get(code)
    if not question:
        return None
    codes = [q["code"] for q in BY_STAGE[question["stage"]]]
    i = codes.index(code)
    return codes[i + 1] if i + 1 < len(codes) else None
