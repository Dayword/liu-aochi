"""选择题教练的 AI 层：按知识点连续出题。

一份契约，一条铁律。

**契约**：一次出一题，单选 4 项。每个错误项必须带 `belief` —— 它模拟的是哪种误解。
少了这个，答错时只能告诉学生「答案是 A」，说不出他到底信了什么，
整个教练模式就退化成一个普通做题 App。

**铁律**：代码题出完以后**服务端真跑一遍，用执行结果校正标准答案**，不信任模型自述。
实测抓到过：题目考「遍历中删元素会漏项」，模型自己给出 `[1, 3]`，
真实执行是 `[1, 3, 2]` —— 它自己掉进了这道题要考的那个坑，
还把正确项标成了错误项。学生选对反被判错，比不出题更糟。

关于模型（deepseek-v4.1-flash-1017，推理模型）—— 实测数据，代码在这里兜：
- 默认开启思考：一题 26~62 秒，思考 700~1200 字，偶尔把 max_tokens 吃光
  → HTTP 200 但正文为空。同一个 prompt 5 次里挂 1 次。
- `thinking={"type":"disabled"}`：一题 **2.7~4.9 秒**、思考 0 字、321 token，JSON 仍然合法。
  token 消耗降到 1/12。选择题不需要长链路推理，这个档位是对的。
  其它写法都无效或直接 400：`thinking=false` → 400；`reasoning_effort=low` → 15s（还是慢）；
  `enable_thinking=false` / `chat_template_kwargs` → 参数被忽略，思考照旧。
"""
from __future__ import annotations

import asyncio
import logging
import re
import random
from typing import Any

from ..services.code_runner import run_python
from .client import _extract_json, ai_enabled, llm_chat

# ⚠️ 必须挂 uvicorn.error：自定义 logger 名没有 handler，warning 会静默消失
log = logging.getLogger("uvicorn.error")

# 难度档位。1=基础(★☆☆) 3=中级(★★★) 4=进阶(★★★★)
LEVELS = {1: "基础", 3: "中级", 4: "进阶"}

# 关掉思考后一题只吃 300~500 token，2000 足够；留余量给「带代码 + 长解析」的题
MAX_TOKENS = 2000

# 关思考的开关。写错一个字符就会被静默忽略（实测 enable_thinking 就是这样），
# 所以只认这一个已验证有效的形态。
NO_THINK = {"thinking": {"type": "disabled"}}

# 需要真跑代码核对的科目
CODE_SUBJECTS = ("Python", "数据分析", "数据结构", "算法", "RAG")


class CoachAIError(RuntimeError):
    """AI 不可用或输出不可解析。调用方负责降级，别把 500 抛给前端。"""


async def _ask_json(prompt: str, temperature: float = 0.7,
                    retries: int = 2) -> Any:
    """要一段 JSON 出来。

    两类失败都要重试，不是偶发：
    - **截断**：即使关了思考，长解析也可能吃满预算，`llm_chat` 会抛 RuntimeError。
    - **空正文 / 缺括号**：HTTP 200 但 content="" 或 JSON 不完整，降温度重试。
    """
    if not ai_enabled():
        raise CoachAIError("AI 未配置")
    last = ""
    for attempt in range(retries):
        try:
            text = await llm_chat(
                [{"role": "user", "content": prompt}],
                temperature=temperature if attempt == 0 else 0.2,
                max_tokens=MAX_TOKENS + attempt * 1500,
                extra_body=NO_THINK,
            )
        except Exception as e:   # 截断 / 上游超时 / 5xx，都当可重试
            last = f"{type(e).__name__}: {e}"
            continue
        last = text or ""
        if last.strip():
            data = _extract_json(last)
            if data is not None:
                return data
    raise CoachAIError(f"模型未返回可解析的 JSON（末次：{last[:120]!r}）")


# ---------------------------------------------------------------- 范围规划
# 用户给「Python」这种大范围时不能直接开考：先把范围拆成由易到难的若干
# 知识点，每个连对 3 题过关。文案由后端拼，模型只负责判断 + 拆分，
# 免得它自由发挥写出一堆「为什么」「建议你」之类的废话。
PLAN_PROMPT = """你是一位课程规划师。用户想练一个知识点，请判断它的**范围是否过大**，
过大就把它拆成由易到难的若干子知识点。

用户输入：{topic}

判断标准：
- 过大 = 一门语言、一个技术栈、一个宽泛领域、一整门课
  （如「Python」「MySQL」「机器学习」「前端」「数据结构」「RAG」）
- 适中 = 一个具体语法点、一个 API、一个算法、一个能在一道题里考完的概念
  （如「列表切片」「B+ 树索引」「闭包」「HTTP 状态码」「快速排序」）

若过大：need_split=true，points 给 3~6 个**由易到难**排列的子知识点。
  每个名字 ≤14 字，必须能用单选题考察（不要「环境搭建」「项目实战」「学习路线」），
  彼此不重叠，合起来覆盖这个范围的主干。
若适中：need_split=false，points 只放原知识点本身。

只输出 JSON，不要解释文字、不要 markdown 围栏：
{{"need_split":true,"points":["...","...","..."]}}"""


async def plan_points(topic: str) -> dict:
    """返回 {need_split, points}。解析不出来就抛，调用方负责降级成单知识点。

    模型偶尔会把「适中」也拆出 1~2 个点，或给出重复/过长的名字，
    这里统一收敛：少于 2 个可用点一律按「不用拆」处理。
    """
    data = await _ask_json(PLAN_PROMPT.format(topic=topic), temperature=0.3)
    if not isinstance(data, dict):
        raise CoachAIError("范围规划返回的不是对象")
    raw = [str(p).strip() for p in (data.get("points") or []) if str(p).strip()]
    if not bool(data.get("need_split")):
        return {"need_split": False, "points": [topic]}

    seen: set[str] = set()
    points: list[str] = []
    for p in raw:
        name = _strip_md(p)[:14]
        if name in seen:
            continue
        seen.add(name)
        points.append(name)
        if len(points) >= 6:
            break
    if len(points) < 2:
        return {"need_split": False, "points": [topic]}
    return {"need_split": True, "points": points}


# ---------------------------------------------------------------- 出题
# 「不要重复已考的」这条必须给：同一知识点内连出好几题时，避免重复只能靠传历史考点。
QUESTION_PROMPT = """你是一位出选择题的教练。请出一道**单选**题。

知识点：{topic}
{point_block}{history}本次难度：{level_name}

硬性要求：

1. **恰好 4 个选项**，1 个正确、3 个错误。
2. 3 个错误项必须对应**学习者真实会犯的误解**，不能是明显荒谬的凑数项。
   判断标准：一个学过但没学透的人，会因为哪三种错误认知选错？就写这三种。
3. 题型优先用这三类：**预测输出**（给代码问结果）、**判断结果**（给操作问状态）、
   **概念辨析**（两个相似概念的区别）。
4. 如果出代码题，`code` 字段必须是**可直接运行的完整片段**，能用一个 `print`
   输出与某个选项**完全一致**的文本。不要伪代码，不要依赖外部数据。
   做不到就不要出代码题，改成概念辨析。
   ⚠️ 代码**只放 `code` 字段**，`stem` 里只写「执行以下代码，输出是什么」，
   不要把代码再抄一遍到题干里（前端会把两处都渲染出来，看起来是重复的）。
5. 题干里的引号内容、变量名、输出值必须精确，不得出现「大约」「可能」。
6. `explanation` 写 3~8 行：先说为什么对，再逐个点出错项错在哪。
7. **正确项必须放在第 {answer_slot_1} 个选项**（`answer_index={answer_slot}`），
   其余 3 个位置放错误项。不要图省事把正确项固定放在第一个。
8. 题干、选项、解析都是纯文本：**不要用 markdown 加粗、列表等符号**
   （前端按纯文本渲染，`**` 会原样露出来）。
{reverse_block}
只输出 JSON，不要解释文字，不要 markdown 围栏：
{{"stem":"题干","options":["选项1","选项2","选项3","选项4"],"answer_index":{answer_slot},
"explanation":"解析","point":"这道题考的具体考点，8 字以内",
"traps":[{{"index":1,"belief":"选它的人以为……"}},{{"index":2,"belief":"……"}},{{"index":3,"belief":"……"}}],
"code":"代码题的完整可运行片段；概念题填空串"}}

`traps` 必须覆盖**全部 3 个错误项**（下标是除 `answer_index` 外的另外 3 个），
`belief` 一句话写清「他信了什么」。示例里的 traps 下标只是格式示意，按实际答案位置改。"""

REVERSE_BLOCK = """
⚠️ 这是**反向题**：题干必须明确写「下列说法**错误**的是」或「下列哪项**不正确**」。
4 个选项里 3 个是**正确说法**、1 个是**错误说法**，`answer_index` 指向那个错误说法。
另需返回 `fact_check`：长度 4 的布尔数组，逐项标出每个选项本身对不对（顺序与 options 一致）。

"""

REVERSE_SCHEMA = """
附加字段：`fact_check` = [true, true, false, true]（顺序与 options 一致，true=该说法正确）"""


async def gen_question(topic: str, level: int = 1, reverse: bool = False,
                       history: list[str] | None = None,
                       subject: str = "Python",
                       point_name: str = "", point_rank: str = "") -> dict:
    """出一道单选题，代码题会用真实执行结果核对答案。

    point_name / point_rank 非空时，题目被约束在规划里的当前知识点内，
    不会跨主题出成综合题 —— 否则「按知识点闯关」就名存实亡。

    返回：{stem, options[4], answer_index, explanation, traps[{index,belief}],
           fact_check(仅反向题), code, level, reverse, point, verified}
    """
    hist = [h for h in (history or []) if h][-12:]
    history_block = (f"已经考过的考点（新题不要重复）：{'、'.join(hist)}\n\n" if hist else "")
    point_block = (
        f"⚠️ 本轮只练「{point_name}」（由易到难的第 {point_rank} 个知识点）："
        "题目必须只考这个点，不要跨到别的主题，不要出成综合题。\n\n"
        if point_name else ""
    )
    focus = f"{topic} / {point_name}" if point_name else topic
    # 每题随机指定正确项的位置。只靠口头要求「别总放第一个」不够 ——
    # 实测 8 道题答案全在 A，模型把 JSON 示例里的 answer_index:0 抄了过去。
    answer_slot = random.randint(0, 3)
    prompt = QUESTION_PROMPT.format(
        topic=focus, point_block=point_block, history=history_block,
        level_name=LEVELS.get(level, "基础"),
        reverse_block=REVERSE_BLOCK if reverse else "",
        answer_slot=answer_slot, answer_slot_1=answer_slot + 1,
    )
    if reverse:
        prompt += REVERSE_SCHEMA

    q: dict | None = None
    for attempt in range(3):
        # 重试逐次降温度：第一次要多样性，重试说明标签不全，稳定优先。
        # 实测两轮仍有 ~1/8 概率只给 2/3 条 belief（2026-11-11 线上抓到：
        # 缺的恰好是学生选的那项，「误解定位」整段消失），所以放到 3 轮；
        # 只有标签不全才多花这几秒，正常情况一次就过。
        data = await _ask_json(prompt, temperature=(0.85, 0.6, 0.5)[attempt])
        q = _normalize(data, level=level, reverse=reverse)
        # 误解标签是这套模式的核心：3 个错误项都标上，答错才能说出「你信了什么」。
        # 缺一条就退化成普通做题 App，所以宁可多花一次 3 秒重出。
        if sum(1 for t in q["traps"] if t["belief"]) >= 3:
            break
    if q is None:          # 三轮都没出成（_ask_json 抛错的话不会走到这）
        raise CoachAIError("出题失败：三轮都没有拿到可用的题")
    miss = 3 - sum(1 for t in q["traps"] if t["belief"])
    if miss:
        # 接受了不完整的题也要留痕：连续出现说明 prompt 或模型在退化
        log.warning("教练出题误解标签不全(%d/3) point=%s", 3 - miss, q["point"])
    # 服务端再洗一次牌：就算模型还是把答案放在指定位置，学生看到的也是随机的。
    q = shuffle_options(q)
    # run_python 会起子进程（阻塞），必须丢线程池，否则一个出题请求把事件循环卡死
    return await asyncio.to_thread(verify_code_answer, q, subject)


# ---------------------------------------------------------------- 工具
# 模型爱在题干/选项/解析里写 markdown 加粗，前端按纯文本渲染就露出「**错误**」。
# 只剥内含中文的 `**x**`：代码里的幂运算 `a ** 2 ** 2` 不含中文，不会被误伤。
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_MD_BOLD_RE = re.compile(r"\*\*([^*\n]{1,40}?)\*\*")


def _strip_md(s: str) -> str:
    return _MD_BOLD_RE.sub(
        lambda m: m.group(1) if _CJK_RE.search(m.group(1)) else m.group(0), s)


def shuffle_options(q: dict) -> dict:
    """随机重排 4 个选项，同步搬移 answer_index / traps / fact_check。

    ⚠️ 必须在 verify_code_answer **之前**调用：它按选项文本匹配 stdout，
    重排后依然能找到正确项，并会基于新下标修正答案。
    """
    order = list(range(4))
    random.shuffle(order)          # order[新位置] = 旧下标
    q["options"] = [q["options"][j] for j in order]
    q["answer_index"] = order.index(q["answer_index"])
    q["traps"] = sorted(
        ({"index": order.index(t["index"]), "belief": t["belief"]}
         for t in q["traps"] if t["index"] in order),
        key=lambda t: t["index"],
    )
    if q.get("fact_check"):
        q["fact_check"] = [q["fact_check"][j] for j in order]
    return q


def _normalize(d: Any, *, level: int, reverse: bool) -> dict:
    """把模型输出收敛成前端能直接用的形状。

    模型偶尔会给 3 个或 5 个选项、把 answer_index 给成字符串、traps 少一条。
    这里不抛错而是修：修不了才抛。宁可少一条 trap，也别让整道题作废。
    """
    if not isinstance(d, dict):
        raise CoachAIError("出题返回的不是对象")

    stem = _strip_md(str(d.get("stem") or "").strip())
    options = [_strip_md(str(o).strip()) for o in (d.get("options") or [])]
    if not stem or len(options) != 4 or len(set(options)) != 4:
        raise CoachAIError(f"题目结构不合法：题干{len(stem)}字 选项{len(options)}个")

    try:
        idx = int(d.get("answer_index"))
    except (TypeError, ValueError):
        raise CoachAIError("answer_index 不是整数") from None
    if not 0 <= idx < 4:
        raise CoachAIError(f"answer_index 越界：{idx}")

    traps: list[dict] = []
    for t in (d.get("traps") or []):
        try:
            ti = int(t.get("index"))
        except (TypeError, ValueError):
            continue
        if ti == idx or not 0 <= ti < 4:
            continue
        belief = _strip_md(str(t.get("belief") or "").strip())
        # 前端标签是「选这项的人以为：」，模型常把 belief 写成「以为 X」
        # → 渲染成「以为：以为 X」。剥掉开头的「以为」，别的措辞不动。
        belief = re.sub(r"^以为", "", belief).strip()
        if belief:
            traps.append({"index": ti, "belief": belief[:120]})
    seen = {t["index"] for t in traps}
    for i in range(4):
        if i != idx and i not in seen:
            traps.append({"index": i, "belief": ""})
    traps.sort(key=lambda t: t["index"])

    fact_check = d.get("fact_check")
    if reverse:
        if not (isinstance(fact_check, list) and len(fact_check) == 4):
            fact_check = [i != idx for i in range(4)]
        else:
            fact_check = [bool(x) for x in fact_check]
    else:
        fact_check = None

    return {
        "stem": stem,
        "options": options,
        "answer_index": idx,
        "explanation": _strip_md(str(d.get("explanation") or "").strip()),
        "traps": traps,
        "fact_check": fact_check,
        "code": str(d.get("code") or "").strip() or None,
        "level": level,
        "reverse": bool(reverse),
        "point": str(d.get("point") or "").strip()[:20] or "未标注考点",
        "verified": None,   # None=没有代码无从核对 / True=执行结果一致 / False=模型原答案被改
    }


def _same(a: str, b: str) -> bool:
    """选项文本与程序输出是否算「一致」。

    允许三种差异：首尾空白、全角半角、引号风格。
    不做模糊匹配 —— 匹配错了就会把错误选项扶正，那是最坏的结果。
    """
    def norm(s: str) -> str:
        s = (s or "").strip()
        for q in ("'", '"', "“", "”", "‘", "’"):
            s = s.replace(q, '"')
        return "".join(s.split())
    return norm(a) == norm(b)


def verify_code_answer(q: dict, subject: str = "Python") -> dict:
    """代码题：跑一遍，用真实 stdout 校正 answer_index。

    只在「恰好一个选项与输出一致」时才改答案，其余情况保持模型原答案并标 verified=None：
    - 一个都不一致：可能是题目在问「会报什么错」，输出比对不适用
    - 多个一致：选项设计本身有问题，改了也不对
    这两种情况宁可不改，也不猜。
    """
    code = q.get("code")
    if not code or subject not in CODE_SUBJECTS:
        return q
    try:
        # strict 用默认 True：题目代码也是用户会看到并运行的东西，
        # 安全限制跟学生提交走同一套，不给例外。
        r = run_python(code, timeout=12)
    except Exception:
        return q
    out = (r.get("stdout") or "").strip()
    if r.get("exit_code") != 0 or not out:
        return q

    hits = [i for i, o in enumerate(q["options"]) if _same(o, out)]
    if len(hits) != 1:
        return q

    real = hits[0]
    q["verified"] = real == q["answer_index"]
    if not q["verified"]:
        # 模型把错项当成了答案：把原答案降级成误解项，真答案扶正
        old = q["answer_index"]
        q["traps"] = [t for t in q["traps"] if t["index"] != real]
        if not any(t["index"] == old for t in q["traps"]):
            q["traps"].append({"index": old, "belief": ""})
        q["traps"].sort(key=lambda t: t["index"])
        q["answer_index"] = real
        if q.get("fact_check"):
            q["fact_check"] = [i != real for i in range(4)]
    return q
