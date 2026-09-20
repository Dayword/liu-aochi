"""AI 客户端：接入 OpenAI 兼容协议（豆包/DeepSeek/通义千问等）。

未配置 API Key 时进入「离线演示模式」：基于内置知识库 + 规则引擎生成回答，
保证无 Key 也能完整演示全部玩法。配置后自动升级为真实大模型 + RAG 检索增强。
"""
from __future__ import annotations

import json
import random
import re
from typing import Any

import httpx

from ..config import settings
from ..models import KnowledgeEntry, Question, QuizRecord


def ai_enabled() -> bool:
    return bool(settings.AI_API_KEY and settings.AI_BASE_URL)


# ---------- 基础调用 ----------
_http: httpx.AsyncClient | None = None


def _http_client() -> httpx.AsyncClient:
    """复用同一个连接池。每次新建 AsyncClient 都要重做 DNS + TLS 握手，
    实测会给每轮对话平白多出 2~4 秒，是首响超时的主要来源之一。"""
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(
            timeout=settings.AI_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=8, keepalive_expiry=300),
        )
    return _http


async def llm_chat(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096,
                   timeout: float | None = None) -> str:
    """调用 OpenAI 兼容 chat/completions 接口。

    max_tokens 需给足：推理模型（如 glm-5.3）的思考过程同样计入该预算，
    预留过小会导致 content 为空串。
    timeout 不传则用全局 AI_TIMEOUT；后台预取类调用（用户不在等）可以单独放宽。
    """
    if not ai_enabled():
        raise RuntimeError("AI 未配置")
    url = settings.AI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": settings.AI_MODEL, "messages": messages,
               "temperature": temperature, "max_tokens": max_tokens}
    resp = await _http_client().post(
        url, json=payload, headers=headers,
        timeout=timeout if timeout is not None else settings.AI_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    choice = data["choices"][0]
    content = ((choice.get("message") or {}).get("content") or "").strip()
    if not content and choice.get("finish_reason") == "length":
        # 推理模型的思考过程也占用 max_tokens，预算不够时 content 会是空串，
        # 这里主动抛错，让各调用方走各自的兜底逻辑，而不是返回空结果。
        raise RuntimeError("模型输出被 max_tokens 截断，请调大该次调用的 max_tokens")
    return content


def _extract_json(text: str) -> Any:
    """从模型输出中稳健地取出 JSON（容忍 ``` 围栏与前后说明文字）。"""
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1].rstrip("`").strip()
        if s.startswith("json"):
            s = s[4:].strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    start, end = s.find("{"), s.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(s[start:end + 1])
        except Exception:
            return None
    return None


# ---------- RAG-lite 检索 ----------
def _tokenize(query: str) -> list[str]:
    return [w for w in re.split(r"[\s，。、？?！!：:；;()（）\[\]【】/\\\-,.]", query.lower())
            if len(w) >= 2]


def retrieve_knowledge(db: Session, query: str, top_k: int = 3) -> list[KnowledgeEntry]:
    """关键词检索知识库（伪 RAG；生产可替换为向量检索 Milvus）。"""
    words = _tokenize(query)
    entries = db.query(KnowledgeEntry).all()
    scored: list[tuple[int, KnowledgeEntry]] = []
    for e in entries:
        score = 0
        kw = set(k.lower() for k in (e.keywords or []))
        for w in words:
            if w in kw:
                score += 3
            if w in e.topic.lower():
                score += 2
            if w in e.content.lower():
                score += 1
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:top_k]]


def knowledge_context(db: Session, query: str) -> str:
    hits = retrieve_knowledge(db, query)
    if not hits:
        return ""
    parts = [f"【{e.subject}·{e.topic}】{e.content}" for e in hits]
    return "\n\n".join(parts)


# ---------- AI 导师对话 ----------
MENTOR_SYSTEM = {
    "老架构师": "你是「老架构师」，一位从业 15 年的资深后端架构师。用生活化比喻、故事和案例讲解技术概念，"
               "回答专业准确、通俗易懂。说话简短有力，可用少量代码示例。",
    "大厂面试官": "你是「大厂面试官」，擅长技术面试与求职辅导。回答注重面试考察点、加分回答话术与避坑指南，"
                 "喜欢从面试官视角追问。",
    "学霸学长": "你是「学霸学长」，名校 CS 学神，擅长数据结构、算法与学习路径规划，讲题清晰、循循善诱。",
    "Python 全栈导师": "你是「Python 全栈导师」，Python 技术栈专家，擅长 Python 语法、FastAPI/Django、"
                    "数据处理与工程化实践，讲解形象生动。",
    "测试大师": "你是「测试大师」，资深测试专家，擅长测试理论、自动化测试、性能测试与用例设计。",
    "运维骑士长": "你是「运维骑士长」，资深运维与云原生专家，擅长 Linux、网络、Docker、K8s 与高可用架构。",
}


# 正文与配套练习题之间的分隔符（放在 system 里告诉模型，解析时用它切分）
QUIZ_MARK = "@@QUIZ@@"

CHAT_MAX_TOKENS = 1600

# 硬性约束：全项目只用 Python，代码示例不许出现其他语言
PYTHON_ONLY_RULE = (
    "【语言约束｜最高优先级】所有代码示例、伪代码、配置示例一律使用 Python，"
    "禁止出现 JavaScript、TypeScript、Java、C/C++、Go、Rust、PHP、CSS 等其他语言。"
    "涉及前端、运维、数据库等话题时也用 Python 生态来说明"
    "（Web 用 FastAPI/Flask/Jinja2，测试用 pytest，数据处理用标准库或 NumPy/Pandas，"
    "数据库用 sqlite3/SQLAlchemy，脚本用 Python 而不是 Shell）。"
)

_QUIZ_RULES = (
    "\n\n输出要求（务必严格遵守）：\n"
    "1) 正文用 Markdown，精炼，控制在 250 字以内，不要长篇大论；\n"
    f"2) 正文写完后另起一行，原样输出分隔符 {QUIZ_MARK}；\n"
    "3) 分隔符之后紧接着输出一段 JSON，不要加代码围栏、不要加任何解释，格式为：\n"
    '{"summary":"一句话总结本次对话的知识点","questions":['
    '{"stem":"题干","options":["选项1","选项2","选项3","选项4"],"answer_index":0,"explanation":"解析"},'
    '{"stem":"题干","options":["选项1","选项2","选项3","选项4"],"answer_index":1,"explanation":"解析"}]}\n'
    "4) questions 恰好 2 道单选题，必须直接考查你上面正文刚讲过的内容，答案能在正文里找到。"
)


def build_chat_messages(db: Session, mentor: str, message: str, history: list[dict],
                        avoid: list[str] | None = None) -> list[dict]:
    """组装导师对话 messages：人设 + Python 语言约束 + 输出格式 + 知识库 + 近期已出题目 + 历史。"""
    system = f"{MENTOR_SYSTEM.get(mentor, MENTOR_SYSTEM['老架构师'])}\n\n{PYTHON_ONLY_RULE}{_QUIZ_RULES}"
    ctx = knowledge_context(db, message)
    if ctx:
        system += "\n\n可参考的内部知识库资料：\n" + ctx
    if avoid:
        system += "\n\n近期已出过的题目（新题必须与它们明显不同）：\n" + \
                  "\n".join(f"- {s}" for s in avoid[:12])
    messages = [{"role": "system", "content": system}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": message})
    return messages


async def stream_llm(messages: list[dict], temperature: float = 0.6,
                     max_tokens: int = CHAT_MAX_TOKENS):
    """流式调用，逐块产出 ('reasoning'|'content', 增量文本)。"""
    if not ai_enabled():
        raise RuntimeError("AI 未配置")
    url = settings.AI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": settings.AI_MODEL, "messages": messages, "stream": True,
               "temperature": temperature, "max_tokens": max_tokens}
    async with _http_client().stream("POST", url, json=payload, headers=headers) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            if not chunk:
                continue
            try:
                delta = (json.loads(chunk).get("choices") or [{}])[0].get("delta") or {}
            except Exception:
                continue
            if delta.get("reasoning_content"):
                yield "reasoning", delta["reasoning_content"]
            if delta.get("content"):
                yield "content", delta["content"]


def split_reply(text: str) -> tuple[str, list[dict], str]:
    """把「正文 + 分隔符 + JSON」拆成 (正文, 题目, 总结)。"""
    if not text:
        return "", [], ""
    body, tail = text.split(QUIZ_MARK, 1) if QUIZ_MARK in text else (text, "")
    data = _extract_json(tail) if tail.strip() else None
    if not (isinstance(data, dict) and data.get("questions")):
        # 兜底：模型漏了分隔符，但仍把 JSON 附在正文尾部
        key = text.find('"questions"')
        start = text.rfind("{", 0, key) if key > 0 else -1
        if start >= 0:
            cand = _extract_json(text[start:])
            if isinstance(cand, dict) and cand.get("questions"):
                data, body = cand, text[:start]
    if not isinstance(data, dict):
        data = {}
    return body.strip(), _normalize_quiz(data.get("questions")), str(data.get("summary") or "").strip()


def fallback_reply(db: Session, mentor: str, message: str) -> str:
    """离线演示模式的规则回复：先查知识库，命中则基于知识生成讲解；否则按指令模板回复。"""
    hits = retrieve_knowledge(db, message)
    msg = message.lower()

    if any(k in msg for k in ("画流程图", "流程图", "架构图")):
        return ("流程拆解如下（Mermaid 图示可放入笔记）：\n\n"
                "```mermaid\ngraph LR\nA[用户请求] --> B[网关]\nB --> C[业务服务]\nC --> D[数据库]\n"
                "C --> E[缓存]\nE --> D\n```\n\n" + _mock_explain(hits, message))

    if any(k in msg for k in ("写代码", "代码实现", "怎么实现", "代码示例")):
        code = _mock_code(message)
        return ("给你一段可直接运行的示例代码：\n\n```python\n" + code + "\n```\n\n"
                "核心思路：先明确数据结构，再写主流程，最后处理边界条件。需要我逐行讲解吗？")

    if any(k in msg for k in ("考点", "总结", "面试怎么答", "面试")):
        return ("**核心考点**：\n"
                "1. 先答结论，再展开原理，最后给实践建议\n"
                "2. 面试官考察的是「为什么」而非「是什么」\n"
                "3. 用 STAR 法则组织项目经历\n\n"
                "**建议话术**：\"我一般从三个层面来理解这个问题：概念、原理、工程实践……\"\n\n"
                "追问练习：你能举一个实际踩坑的例子吗？")

    if any(k in msg for k in ("学习路径", "学习计划", "怎么学", "转行", "入门")):
        return ("给你一份分阶段学习路径（以你当前职业方向为例）：\n\n"
                "**阶段 1（1-2 周）**：夯实语言基础 + 核心概念，每天 1 关知识闯关\n"
                "**阶段 2（3-4 周）**：学主流框架 + 做 2 个小项目，配合 AI 导师答疑\n"
                "**阶段 3（5-8 周）**：刷高频面试题 + 每周 2 次模拟面试，用 Bug 猎人练手感\n\n"
                "关键不是堆时间，而是「学-练-复盘」闭环。我可以根据你的错题帮你调计划。")

    if any(k in msg for k in ("你好", "在吗", "hi", "hello")):
        return ("你好呀，我是你的 AI 导师。可以问我任何软件工程问题：概念讲解、代码答疑、学习路径、"
                "面试准备都可以。试试对我说「画流程图」或「考点总结」？")

    if hits:
        e = hits[0]
        return (f"这个问题属于 **{e.subject}·{e.topic}**，我帮你梳理一下：\n\n{e.content}\n\n"
                "想深入了解，可以追问「举例子」「写代码」「考点总结」。" + _mock_explain(hits, message))

    return ("这个问题我先帮你拆解一下思路：\n\n"
            "**1. 明确本质**：先判断它在问概念、原理还是实践\n"
            "**2. 分点回答**：概念解释 → 工作原理 → 工程实践\n"
            "**3. 举例验证**：用一个具体场景检验理解\n\n"
            "你可以把问题说得更具体些（比如带上知识点关键词），或者用「写代码」「画流程图」「考点总结」"
            "让我换个角度讲。")


def _mock_explain(hits: list, message: str) -> str:
    return ""  # 知识库内容已足够


_CODE_TEMPLATES = {
    "链表": "class Node:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\ndef reverse_list(head):\n    prev = None\n    cur = head\n    while cur:\n        nxt = cur.next\n        cur.next = prev\n        prev = cur\n        cur = nxt\n    return prev",
    "排序": "def quick_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)",
    "递归": "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)",
    "去重": "def dedup(nums):\n    return list(dict.fromkeys(nums))",
}


def _mock_code(message: str) -> str:
    for kw, code in _CODE_TEMPLATES.items():
        if kw in message:
            return code
    return ("def solve(data):\n"
            "    # 你的实现\n"
            "    result = []\n"
            "    for item in data:\n"
            "        if item:  # 处理逻辑\n"
            "            result.append(item)\n"
            "    return result")


# ---------- 配套练习题：解析与题库兜底 ----------
# 模型常把选项写成 "A. xxx" / "(A) xxx"，而前端会自己加上 A/B/C/D 前缀，
# 需要剥掉，避免界面上出现 "A.A. xxx"。只匹配「字母+分隔符」这种明显的形式。
_OPTION_PREFIX = re.compile(r"^(?:[（(]\s*[A-Ha-h]\s*[）)]|[A-Ha-h]\s*[.、)．:：])\s*")


def strip_option_prefix(options: list) -> list[str]:
    """剥掉选项文本自带的 "A. " 前缀（前端会自己加 A/B/C/D，重复会出现 "A.A. xxx"）。"""
    return [_OPTION_PREFIX.sub("", str(o)).strip() or str(o).strip() for o in options]


def _normalize_quiz(raw: Any) -> list[dict]:
    """校验并规整模型出的题目，丢弃结构不合法的条目。"""
    out: list[dict] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        stem = str(item.get("stem") or "").strip()
        options = []
        for o in (item.get("options") or []):
            text = str(o).strip()
            if not text:
                continue
            stripped = _OPTION_PREFIX.sub("", text)
            options.append(stripped or text)  # 剥完为空就保留原样，避免索引错位
        try:
            index = int(item.get("answer_index"))
        except (TypeError, ValueError):
            continue
        if not stem or len(options) < 2 or not 0 <= index < len(options):
            continue
        out.append({"stem": stem, "options": options, "answer_index": index,
                    "explanation": str(item.get("explanation") or "").strip()})
    return out


def recent_quiz_stems(db: Session, user_id: int, limit: int = 12) -> list[str]:
    """该用户最近做过的练习题题面（拿去告诉模型别重复）。"""
    rows = db.query(QuizRecord).filter(QuizRecord.user_id == user_id).order_by(
        QuizRecord.id.desc()).limit(limit).all()
    return [r.stem for r in rows]


def remember_quiz(db: Session, user_id: int, quiz: list[dict]) -> None:
    """记录本次出的题目，供后续查重。"""
    for q in quiz:
        stem = (q.get("stem") or "").strip()[:255]
        if stem:
            db.add(QuizRecord(user_id=user_id, stem=stem))


def _match_grams(text: str) -> list[str]:
    """把提问切成可匹配的片段：英文/数字按词切，中文按 2 字滑窗。

    中文没有空格，整句切出来是一个长 token，跟题干做子串匹配永远命中不了；
    切成 2 字滑窗后「索引」「装饰」「握手」这类关键片段才能匹配上。
    """
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text.lower())
    grams: list[str] = []
    for part in cleaned.split():
        if re.fullmatch(r"[a-z0-9_]+", part):
            if len(part) >= 2:
                grams.append(part)
        else:
            grams.extend(part[i:i + 2] for i in range(len(part) - 1))
    return grams


def _rank_by_relevance(pool: list[Question], text: str, limit: int = 15) -> list[Question]:
    """按关键词相关度挑候选池：IDF 加权 + 只保留得分 ≥ 最高分一半的题。

    IDF 让「python」这种到处都是的词权重低、「索引」「握手」这种专有片段权重高。
    """
    grams = set(_match_grams(text))
    if not grams:
        return []
    blobs = {q.id: " ".join([q.stem or "", q.subject or "",
                             " ".join(q.tags or [])]).lower() for q in pool}
    df = {g: sum(1 for b in blobs.values() if g in b) for g in grams}
    scored = []
    for q in pool:
        score = sum(1.0 / (1.0 + df[g]) for g in grams if g in blobs[q.id])
        if score > 0:
            scored.append((score, q))
    if not scored:
        return []
    top = max(s for s, _ in scored)
    return [q for s, q in scored if s >= top * 0.5][:limit]


def pick_bank_quiz(db: Session, text: str, user_id: int | None = None,
                   count: int = 2) -> list[dict]:
    """题库兜底出题：相关性优先，其次才是不重复。

    优先级：没做过的相关题 > 做过的相关题 > 没做过的随机题。
    宁可偶尔重复，也不出跑题的题。
    """
    pool = [q for q in db.query(Question).filter(Question.type == "choice").all()
            if q.options and isinstance((q.answer or {}).get("correct_index"), int)]
    if not pool:
        return []
    used = set(recent_quiz_stems(db, user_id, 40)) if user_id else set()
    relevant = _rank_by_relevance(pool, text)
    unused_relevant = [q for q in relevant if q.stem not in used]
    if unused_relevant:
        candidates = unused_relevant
    elif relevant:
        candidates = relevant
    else:  # 提问没有可匹配的知识点（如"你好"）→ 全池随机，尽量避开做过的
        candidates = [q for q in pool if q.stem not in used] or list(pool)
    random.shuffle(candidates)

    out: list[dict] = []

    def _append(q: Question) -> None:
        out.append({"stem": q.stem, "options": strip_option_prefix(q.options),
                    "answer_index": q.answer["correct_index"],
                    "explanation": q.explanation or ""})

    for q in candidates:
        if len(out) >= count:
            break
        _append(q)
    if len(out) < count:  # 候选不够就全池随机补齐
        picked = {o["stem"] for o in out}
        rest = [q for q in pool if q.stem not in picked and q.stem not in used]
        random.shuffle(rest)
        for q in rest[: count - len(out)]:
            _append(q)
    return out


# ---------- 错题 AI 解析 ----------
async def wrong_answer_analysis(db: Session, question: dict, user_answer: Any) -> str:
    """答错后生成解析：优先 AI，其次知识库/内置解析。"""
    if ai_enabled():
        try:
            messages = [
                {"role": "system", "content": "你是软件工程学习助教。用户答错了一道题，请用 80 字以内给出："
                                              "错因归类（概念不清/计算错误/思路偏差）+ 一句关键点拨，口语化。"},
                {"role": "user", "content": f"题目：{question.get('stem')}\n正确答案：{question.get('expected')}\n"
                                            f"用户答案：{user_answer}\n解析参考：{question.get('explanation', '')}"},
            ]
            # 推理模型的思考过程也占 max_tokens，预算给不够会直接返回空串
            return await llm_chat(messages, temperature=0.4, max_tokens=3072)
        except Exception:
            pass
    return _mock_wrong_analysis(question, user_answer)


def _mock_wrong_analysis(question: dict, user_answer: Any) -> str:
    qtype = question.get("type")
    if qtype in ("choice", "blank"):
        return ("错因分析：这题更偏向「概念不清」——题干和考点挂钩的知识点没有完全吃透。"
                "建议回到对应知识点的闯关关卡再刷一遍，配合错题本复习效果更好。")
    return ("错因分析：可能是「思路偏差」——方向对了但细节没扣准。"
            "建议先看解析里的考点，再尝试用「追问讲解」把原理弄清楚。")


# ---------- 动态出题（AI） ----------
async def ai_generate_question(db: Session, tags: list[str], difficulty: int,
                               exclude_ids: list[int],
                               avoid: list[str] | None = None) -> dict | None:
    """AI 实时生成题目；失败或无配置时返回 None，由题库兜底。

    avoid 传入近期已出过的题干，避免连续失败时反复刷到雷同的题。
    """
    if not ai_enabled():
        return None
    try:
        avoid_hint = ""
        if avoid:
            avoid_hint = ("不要与下面这些题重复或高度相似：\n"
                          + "\n".join(f"- {s[:60]}" for s in avoid[:8]) + "\n")
        prompt = (f"为软件工程学习平台生成 1 道{difficulty}星难度、知识点为「{'、'.join(tags[:3])}」的单选题。\n"
                  f"{PYTHON_ONLY_RULE}"
                  "涉及代码示例时一律用 Python，不要出其它语言相关的题目。\n"
                  f"{avoid_hint}"
                  "格式（JSON）：{\"type\":\"choice\",\"stem\":\"...\",\"options\":[\"A\",\"B\",\"C\",\"D\"],"
                  "\"answer\":\"正确选项文本\",\"explanation\":\"解析\",\"knowledge_point\":\"...\"} 只输出 JSON。")
        # 2048 实测会截断（思考过程吃掉大半），导致出题失败退回题库兜底。
        # 出题是在后台预取的、用户不在等，所以超时单独放宽到 90s 提高成功率。
        text = await llm_chat([{"role": "user", "content": prompt}],
                              temperature=0.9, max_tokens=4096, timeout=90)
        data = _extract_json(text) or {}
        options = data.get("options", [])
        answer = data.get("answer", "")
        # 模型常把选项写成 "A. xxx"，而前端会自己加 A/B/C/D 前缀，需要剥掉
        options = strip_option_prefix(options)
        answer = strip_option_prefix([answer])[0] if answer else answer
        if answer in options and len(options) >= 2:
            return {"type": "choice", "subject": "AI动态", "tags": tags, "difficulty": difficulty,
                    "stem": data.get("stem", ""), "options": options,
                    "answer": {"correct_index": options.index(answer)},
                    "explanation": data.get("explanation", ""),
                    "knowledge_point": data.get("knowledge_point", ""), "source": "ai"}
    except Exception:
        return None
    return None


# ---------- 面试评分 ----------
async def interview_score(question: str, answer: str, keywords: list[str]) -> dict:
    """四维评分：技术准确性/逻辑清晰度/表达流畅度/STAR。AI 优先，规则兜底。"""
    if ai_enabled():
        try:
            messages = [{"role": "system", "content": "你是面试评分系统。按四维度各 0-100 打分，只输出 JSON："
                          "{\"技术准确性\":80,\"逻辑清晰度\":70,\"表达流畅度\":85,\"STAR法则\":60,\"点评\":\"...\",\"建议\":\"...\"}"},
                        {"role": "user", "content": f"问题：{question}\n关键词：{keywords}\n回答：{answer}"}]
            text = await llm_chat(messages, temperature=0.3, max_tokens=3072)
            data = _extract_json(text) or {}
            dims = {k: max(0, min(100, int(v))) for k, v in data.items() if k in
                    ("技术准确性", "逻辑清晰度", "表达流畅度", "STAR法则")}
            if dims:
                return {"scores": dims, "comment": data.get("点评", ""), "advice": data.get("建议", "")}
        except Exception:
            pass
    return _mock_interview_score(answer, keywords)


def _mock_interview_score(answer: str, keywords: list[str]) -> dict:
    answer_l = answer.lower()
    hit = sum(1 for k in keywords if k and k.lower() in answer_l)
    rate = hit / max(len(keywords), 1)
    tech = 40 + int(rate * 50)
    logic = 55 + min(35, int(len(answer) / 30))
    fluency = 60 + min(30, int(len(answer) / 40))
    star = 45 + (25 if any(w in answer_l for w in ("situation", "任务", "背景", "结果", "成果", "action")) else 0)
    if len(answer) < 30:
        comment = "回答偏简短，建议补充关键术语和具体例子。"
        advice = "按「结论先行 + 术语支撑 + 例子佐证」的结构重答一遍。"
    elif rate < 0.4:
        comment = "覆盖了部分要点，但关键术语缺失。"
        advice = f"尝试在回答中带入这些关键词：{'、'.join(keywords[:3])}。"
    else:
        comment = "回答结构完整，关键点覆盖良好。"
        advice = "可以再加一个真实项目/场景例子提升说服力。"
    return {"scores": {"技术准确性": tech, "逻辑清晰度": min(100, logic),
                       "表达流畅度": min(100, fluency), "STAR法则": min(100, star)},
            "comment": comment, "advice": advice}


# ---------- 面试报告生成 ----------
async def interview_report(rounds_scores: list[dict]) -> dict:
    dims = ["技术准确性", "逻辑清晰度", "表达流畅度", "STAR法则"]
    avg = {d: round(sum(r.get("scores", {}).get(d, 0) for r in rounds_scores) / max(len(rounds_scores), 1))
           for d in dims}
    weak = sorted(dims, key=lambda d: avg[d])[0]
    strong = sorted(dims, key=lambda d: -avg[d])[0]
    overall = round(sum(avg.values()) / 4)
    grade = "S" if overall >= 85 else "A" if overall >= 75 else "B" if overall >= 60 else "C"
    return {
        "overall": overall, "grade": grade,
        "dimensions": avg,
        "strong_point": strong,
        "weak_point": weak,
        "advice": (f"你的{strong}表现突出，继续保持；{weak}是主要短板，建议按「结论先行+术语+STAR」结构多练。"
                   f"推荐回到对应知识关卡巩固，并隔天重做本轮面试题。"),
        "offer": "虚拟 Offer" if overall >= 75 else "待提升",
    }
