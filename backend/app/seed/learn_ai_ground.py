"""科目：AI 工程质量（3 课）。

前两个科目解决「检索得准」和「服务能跑」，这三课解决「答得可信、路由不拖慢、图能画出来」。
它们对应项目里最容易被忽略、但线上最要命的三块：防幻觉、意图路由、服务端出图。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）
"""

GROUND_CHECKER = """
try:
    ok, why = verify_citation("旋转木马票价十元[1]，夜场八点开始[2]。", 2)
    assert ok is True and why == "ok", "引用 1、2 都在 2 条来源范围内，应该通过，现在是 (%r, %r)" % (ok, why)

    ok2, why2 = verify_citation("旋转木马票价十元。", 2)
    assert ok2 is False and why2 == "no_citation", "整段没有任何引用标记，属于「无依据」，必须判不通过"

    ok3, why3 = verify_citation("票价十元[1]，退票要手续费[5]。", 2)
    assert ok3 is False and why3 == "bad_citation", "引用了第 5 条但只有 2 条来源，属于伪造引用"

    ok4, why4 = verify_citation("参见[0]。", 2)
    assert ok4 is False and why4 == "bad_citation", "引用编号从 1 开始，[0] 是越界"

    ok5, why5 = verify_citation("多来源对比见[1][2][1]。", 2)
    assert ok5 is True, "重复引用同一来源是允许的"

    assert should_refuse(0.2, 0.5) is True, "相关度 0.2 低于阈值 0.5，应该拒答而不是硬编"
    assert should_refuse(0.5, 0.5) is False, "正好等于阈值算通过（判定用严格小于）"
    assert should_refuse(0.9, 0.5) is False, "高于阈值正常回答"
    assert should_refuse(0.0, 0.0) is False, "阈值设成 0 表示不拦任何检索结果"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError, AttributeError) as e:
    print("__FAIL__ 返回结构不对（verify_citation 返回 (bool, str)，should_refuse 返回 bool）：" + str(e))
"""

ROUTER_CHECKER = """
try:
    rules = {"map": ["在哪", "怎么走"], "business": ["办卡", "退卡"]}

    def never(q):
        raise AssertionError("规则命中时不应该调用模型")

    assert route("旋转木马在哪", rules, never) == ("map", "rule"), "命中 map 的关键词，L1 直接返回，连模型都不该调"
    assert route("我要退卡", rules, never) == ("business", "rule"), "命中 business 的关键词"

    cache = {}
    calls = {"n": 0}

    def classify(q):
        calls["n"] += 1
        return "rag"

    assert route("今天天气如何", rules, classify, cache) == ("rag", "model"), "规则没命中，走小模型分类"
    assert calls["n"] == 1, "第一次必须真的调模型"
    assert cache.get("今天天气如何") == "rag", "分类结果要写进缓存，供下次复用"

    assert route("今天天气如何", rules, classify, cache) == ("rag", "cache"), "第二次同样的问题应该命中缓存"
    assert calls["n"] == 1, "命中缓存时不能再调模型，现在是 %d 次" % calls["n"]

    def boom(q):
        raise TimeoutError("小模型超时")

    assert route("一个规则和缓存都没命中的问题", rules, boom, {}) == ("default", "fallback"), "分类器抛异常（超时）时要降级到 default，不能把异常抛给主链路"

    assert route("我想办卡", rules, never, {"我想办卡": "cached"}) == ("business", "rule"), "规则优先于缓存：规则是 0ms，缓存还要查一次"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, AttributeError) as e:
    print("__FAIL__ 返回结构不对（约定返回 (agent, level) 二元组）：" + str(e))
"""

CHART_CHECKER = """
try:
    items = [
        {"name": "旋转木马", "value": 120},
        {"name": "过山车", "value": 90},
        {"name": "蹦床", "value": 60},
        {"name": "秋千", "value": 30},
        {"name": "大炮乐园", "value": 20},
    ]
    r = top_n_with_other(items, 3)
    assert len(r) == 4, "Top3 加一个「其他」共 4 项，现在是 %d 项" % len(r)
    assert [x["name"] for x in r[:3]] == ["旋转木马", "过山车", "蹦床"], "前三项要按 value 从大到小排"
    assert r[3] == {"name": "其他", "value": 50}, "剩下的 30+20 要合并成「其他」，现在是 %r" % (r[3],)

    r2 = top_n_with_other(items, 10)
    assert r2 == items, "n 大于条目数时原样返回，不能凭空造一个「其他」"

    r3 = top_n_with_other(items, 5)
    assert len(r3) == 5 and all(x["name"] != "其他" for x in r3), "正好等于条目数时也不该有「其他」"

    assert top_n_with_other([], 3) == [], "空列表返回空列表"

    r4 = top_n_with_other([
        {"name": "A", "value": 10},
        {"name": "B", "value": 10},
        {"name": "C", "value": 10},
    ], 2)
    assert [x["name"] for x in r4[:2]] == ["A", "B"], "value 相同时要保持原顺序（稳定排序），现在是 %r" % ([x["name"] for x in r4],)
    assert r4[2] == {"name": "其他", "value": 10}, "同分情况下被挤到「其他」的是 C"

    try:
        top_n_with_other(items, 0)
        assert False, "n 小于 1 时应该抛 ValueError —— 「Top 0」没有意义，静默返回会让调用方拿到空图"
    except ValueError:
        pass
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, AttributeError) as e:
    print("__FAIL__ 参数或返回结构不对：" + str(e))
"""

LESSONS = [
    {
        "code": "ai-grounding",
        "subject": "AI 工程质量",
        "stage": "可信与调度",
        "runner": "python",
        "title": "防幻觉与答案溯源",
        "summary": "允许模型说「不知道」，比让它硬编强一百倍",
        "definition": """**RAG 不能消除幻觉，只能降低幻觉。** 检索到的内容可能不相关、可能互相矛盾，模型仍然会「根据资料」编出一段资料里没有的话。

所以要建**四道防线**，缺一道都可能漏：

**① 检索层：相似度阈值**

检索分数低于阈值，就不要把这段内容塞进 prompt。塞进去等于给模型递了一份「看起来像资料」的噪声。

```
if top_score < SIMILARITY_THRESHOLD:
    → 不注入上下文，走兜底话术
```

**② Prompt 层：约束 + 允许拒答**

系统提示里必须写清三件事：

- **只能依据给定资料回答**，不许引入资料外的知识
- **每句结论要标来源编号** `[1]` `[2]`
- **资料里没有就说「没有找到相关信息」**

第三条最关键。很多幻觉的根源是 prompt 逼着模型「必须回答」——它答不出来就只能编。

**③ 答案层：引用校验**

生成完了要检查：答案里出现的 `[n]` 是否都在实际来源条数范围内？整段答案一条引用都没有，说明它很可能是自由发挥。

这是**确定性的、可自动化的**检查，不依赖另一个模型。项目里就是靠它做质量门禁。

**④ 兜底层：拒答话术**

拒答不是失败，是正确行为。用户问「明天会不会下雨」而知识库里只有票价，答「不知道，请咨询客服」远好过编一个天气。

**评测时要把「该拒答」当成一个独立指标**：只看「回答率」会奖励那些什么都敢答的模型。

**项目落点**：`agents/verification_agent.py` 的 `VerificationAgent` 负责四件事——检索结果相关性校验、答案溯源标注、防幻觉 prompt 约束、答案质量评分。`SIMILARITY_THRESHOLD` / `VERIFY_MIN_SCORE` 都在 `config.py` 里可调。""",
        "plain": """考试时老师给了你一份参考资料，要求「只能根据这份资料答题」。

- **好学生**：资料里有就答，还标上「见资料第 2 段」；资料里没有就说「这份资料没写」
- **坏学生**：资料里没有也硬编一个，听起来还挺像

RAG 的防幻觉就是三件事：**不给坏学生递无关的小抄**（阈值）、**考前明确说「可以答不知道」**（prompt）、**考完检查他标的出处是不是真的存在**（引用校验）。""",
        "example": """import re

answer = "旋转木马票价十元[1]，夜场八点开始[2]。"
n_sources = 2
cites = [int(x) for x in re.findall(r"\\[(\\d+)\\]", answer)]
print("答案里的引用编号:", cites)
print("实际来源条数:", n_sources)
print("越界的引用:", [c for c in cites if c < 1 or c > n_sources])""",
        "example_output": """答案里的引用编号: [1, 2]
实际来源条数: 2
越界的引用: []""",
        "pitfalls": [
            "prompt 里写「请务必回答用户问题」：逼着模型答，它答不出来就只能编",
            "检索分数很低也照样注入上下文：等于给模型递了一份噪声小抄，幻觉率反而更高",
            "不校验引用编号：模型引用 [5] 但只有 2 条来源，前端却照常渲染出一个假出处",
            "把「拒答率」当成负面指标：越敢答的模型看起来越好，实际最危险",
        ],
        "task": """请实现两个函数：

1. `verify_citation(answer, n_sources)` → `(ok, reason)`
   - 用正则找出答案里所有 `[数字]` 形式的引用编号
   - 一个引用都没有 → `(False, "no_citation")`
   - 任一编号 `< 1` 或 `> n_sources` → `(False, "bad_citation")`
   - 否则 → `(True, "ok")`

2. `should_refuse(score, threshold)` → `bool`
   - `score` **严格小于** `threshold` 时返回 `True`（该拒答）""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """用 `re.findall(r"\\[(\\d+)\\]", answer)` 拿到字符串编号，再 `int()`。注意空列表要单独判「无引用」，否则 `all()` 对空列表返回 True 会误判成通过。""",
        "checker": GROUND_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "防幻觉最有效的一招是什么？",
                "options": [
                    "把 temperature 调到 0",
                    "在 prompt 里明确允许模型说「资料里没有」",
                    "把模型换成更大的",
                    "增加检索条数",
                ],
                "answer_index": 1,
                "explanation": "temperature=0 只降低随机性，不阻止编造。明确允许拒答，才能解除「必须回答」的压力——这是幻觉最主要的来源。",
            },
            {
                "type": "choice",
                "stem": "答案里出现 `[5]`，但实际只检索到 2 条来源，说明什么？",
                "options": [
                    "模型引用格式写错了，可以忽略",
                    "这是伪造引用，答案很可能包含编造内容",
                    "检索条数太少，应该加大 top_k",
                    "前端渲染问题",
                ],
                "answer_index": 1,
                "explanation": "引用编号越界意味着模型在「假装有出处」。这类答案应该被校验拦住，而不是直接展示给用户。",
            },
            {
                "type": "judge",
                "stem": "RAG 只要检索到了相关资料，模型就不会产生幻觉。",
                "answer": False,
                "explanation": "检索到不代表模型会严格依据它。资料可能不相关、可能互相矛盾，模型仍可能自由发挥。所以还需要 prompt 约束和答案校验。",
            },
            {
                "type": "blank",
                "stem": "检索结果的相关度低于某个值时就不注入上下文、直接兜底，这个值叫相似度______。",
                "answer": "阈值",
                "hint": "填两个字，英文 threshold",
                "explanation": "相似度阈值是第一道防线。设得太低会注入噪声，设得太高会漏掉有用信息，需要按业务调。",
            },
        ],
    },
    {
        "code": "ai-router",
        "subject": "AI 工程质量",
        "stage": "可信与调度",
        "runner": "python",
        "title": "Agent 三级路由：规则、小模型与兜底",
        "summary": "把 LLM 决策放在不拖慢热路径的位置",
        "definition": """**路由（routing）= 判断用户这句话该交给哪个 Agent 处理。**

最原始的做法是关键词表：含「在哪」「怎么走」→ 地图 Agent，含「办卡」「退卡」→ 业务 Agent。

**关键词表的死穴是漏召**，而且漏得毫无征兆：

- 「这张卡还能用吗」—— 一个关键词都不含，掉进通用 RAG
- 「今天适合带 5 岁孩子去吗」—— 也不含，同样掉进去
- 每加一个新 Agent，都要回头往所有词表里补词，词表越长越脆

**三级路由**（核心思路：把贵的决策放在不拖慢主链路的位置）：

```
L1 规则快速通道
   命中现有关键词表 → 直接返回
   0 次 LLM、0ms 新增耗时

L2 小模型单次分类
   仅当 L1 全未命中，且问句带「行动/实时数据」标记时才触发
   硬超时 1.5 秒，结果进 Redis 缓存 1 小时

L3 兜底
   小模型超时 / 抛异常 / 置信度低 → 走通用 RAG 或默认 Agent
```

**三个设计要点**：

1. **规则优先于缓存和模型**。规则是内存里的字符串匹配，0ms；缓存要查一次 Redis；模型要几百毫秒。顺序反了就是白白变慢。
2. **L2 必须有硬超时**。小模型卡住不能把整个请求拖死，超时就直接降级。降级后的答案可能不那么精准，但至少用户拿到了回复。
3. **缓存的是「问句 → Agent」的映射**。同一个问句重复问很常见（尤其是客服场景），缓存命中率不低。

**别把路由做成第四个大模型调用**：如果「判断走哪个 Agent」本身就要 3 秒，那还不如不做路由，直接让通用 RAG 处理。

**项目落点**：`agents/router_agent.py` 的 `RouterAgent` 就是这三级——L1 复用 `map_agent` / `business_agent` 的关键词表，L2 用小模型单次分类（硬超时 1.5s、结果进 Redis 缓存 1h），L3 落到 `orchestrator` 的通用链路。""",
        "plain": """公司前台分诊：

- **L1 规则**：你说「我要报销」，前台立刻指财务部 —— 看关键词就行，0 秒
- **L2 小模型**：你说「我上个月的差旅费怎么还没到」，没关键词，前台得想一下（但最多想 1.5 秒）→ 技术部/财务部
- **L3 兜底**：前台想了 1.5 秒还没想明白，或者系统卡住了 → 先带你到综合服务台

**为什么不能全用大模型判断**：如果前台每句话都要打电话问总部（3 秒），队伍早排到门外了。常见的话用规则秒判，罕见的才动脑子。""",
        "example": """rules = {"map": ["在哪", "怎么走"], "business": ["办卡", "退卡"]}
query = "旋转木马在哪"
hit = [agent for agent, kws in rules.items() if any(k in query for k in kws)]
print("规则命中:", hit)""",
        "example_output": "规则命中: ['map']",
        "pitfalls": [
            "把规则判断放在缓存和模型之后：明明 0ms 能出结果，非要多走两次 IO",
            "L2 小模型不设超时：模型卡住时整个请求挂起，用户等到白屏",
            "小模型抛异常直接冒到上层：本该降级到通用链路，结果整个接口 500",
            "路由结果不缓存：客服场景同一句话被反复问，每次都重新分类一遍",
        ],
        "task": """请实现 `route(query, rules, classify, cache=None)`，返回 `(agent, level)`：

- `rules`：`{agent: [关键词, ...]}`，按字典顺序检查
- 优先级从高到低：
  1. **规则**：`query` 里含某个 agent 的任一关键词 → `(agent, "rule")`
  2. **缓存**：`cache` 是 dict，`query in cache` → `(cache[query], "cache")`
  3. **模型**：调用 `classify(query)` 得到 agent → 写入 `cache[query]` → `(agent, "model")`
  4. **兜底**：`classify` 抛任何异常 → `("default", "fallback")`，异常不能往外抛
- `cache` 为 `None` 时跳过缓存读写（不要报错）""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先 `for agent, kws in rules.items():` 里 `if any(k in query for k in kws): return (agent, "rule")`。缓存判 `if cache is not None and query in cache`。模型调用包在 `try/except Exception` 里，成功时记得 `cache[query] = agent`（先判 cache 不为 None）。""",
        "checker": ROUTER_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "三级路由为什么要把「规则」放在最前面？",
                "options": [
                    "规则判断最准",
                    "规则是内存匹配，0ms 且不花钱，能用便宜方式解决的就别调模型",
                    "规则能覆盖所有情况",
                    "因为缓存不可靠",
                ],
                "answer_index": 1,
                "explanation": "规则不追求「最准」，追求「最快最便宜」。常见问句占大多数，用规则秒判就能省下大量模型调用和延迟。",
            },
            {
                "type": "choice",
                "stem": "小模型分类超时后，正确做法是什么？",
                "options": [
                    "让请求一直等到模型返回",
                    "直接降级到默认链路，先给用户一个回复",
                    "返回 500 让前端重试",
                    "把超时时间调大到 30 秒",
                ],
                "answer_index": 1,
                "explanation": "路由是「优化项」不是「必需项」。超时就退回通用链路，答案可能不够精准但可用；死等或报错都是把优化项变成了故障点。",
            },
            {
                "type": "judge",
                "stem": "路由判断本身也值得用一次大模型调用来做，这样最准确。",
                "answer": False,
                "explanation": "如果路由本身要 3 秒，就违背了它的初衷——省时间。路由必须比它优化的流程更便宜，否则不如不路由。",
            },
            {
                "type": "blank",
                "stem": "第三级降级时返回的 Agent 名字，本课约定为______。",
                "answer": "default",
                "hint": "填一个英文单词，意思是「默认」",
                "explanation": "`classify` 超时或抛异常时返回 `(\"default\", \"fallback\")`，交给默认链路处理，保证接口永远有响应。",
            },
        ],
    },
    {
        "code": "ai-chart",
        "subject": "AI 工程质量",
        "stage": "可信与调度",
        "runner": "python",
        "title": "服务端图表渲染与数据整形",
        "summary": "二十根柱子的图，没人看得懂",
        "definition": """**图表的第一个问题是「数据太多」，不是「画得好不好看」。**

游乐园的消费统计有几十个项目，全画进柱状图会变成一堆牙签。标准做法是 **Top N + 其他**：

```
旋转木马  120
过山车     90
蹦床       60
其他       50   ← 剩下所有项求和，合并成一根
```

为什么合并而不是「只画前 3 个」：直接丢掉剩余数据会让读者以为总量就是前 3 之和。合并成「其他」保留了总量信息，也诚实。

**N 怎么定**：

- 柱状图：5~8 根（人眼一次能比较的数量级）
- 饼图：**最多 5 份**，再多就分不清扇形角度了
- 折线图：不合并，按时间轴画

**服务端出图 vs 前端出图**：

| | 前端（ECharts） | 服务端（PIL / matplotlib） |
|---|---|---|
| 交互 | 可缩放、可悬浮 | 静态图片 |
| 分享 | 要截图 | 直接发 PNG 链接 |
| 依赖 | 浏览器 | 服务器要有绘图库 |
| 场景 | 管理后台 | **对话里直接发图**、报告附件、小程序 |

项目的场景是「客服对话里直接回一张图」，所以必须服务端渲染。

**一个现实约束**：项目环境没有 matplotlib，`services/chart_render.py` 用 **PIL 手绘**（画矩形、写文字）。这不是最优解，但是在「不能联网装包」的环境里能跑通的解。

**项目落点**：`services/chart_render.py` 画三类图——项目游玩排行（横向条形）、办卡类型统计（横向条形）、消费月度趋势（纵向条形），输出 PNG 到 `static/charts/`，返回可访问 URL；任何单图失败都不阻塞整体回答。""",
        "plain": """给领导汇报「哪个项目最受欢迎」：

你把 30 个项目全画进一张柱状图 —— 领导看到的是一片密密麻麻的牙签，一个字都读不出来。

正确做法：**只画最火的 5 个，剩下 25 个合成一根「其他」**。领导一眼就知道「旋转木马占大头，长尾一大堆」。

**为什么不能只画前 5 个**：那样图上的总和只有真实总量的 60%，领导会误判规模。「其他」这一根就是在说「还有这么多，只是不展开了」。""",
        "example": """items = [("旋转木马", 120), ("过山车", 90), ("蹦床", 60),
         ("秋千", 30), ("大炮乐园", 20), ("浴室大作战", 10)]
n = 3
top = items[:n]
other = sum(v for _, v in items[n:])
print("Top3:", top)
print("其他合并为:", ("其他", other))
print("画图时只画", len(top) + 1, "根柱子，而不是", len(items), "根")""",
        "example_output": """Top3: [('旋转木马', 120), ('过山车', 90), ('蹦床', 60)]
其他合并为: ('其他', 60)
画图时只画 4 根柱子，而不是 6 根""",
        "pitfalls": [
            "把所有类别都画进图里：几十根柱子挤在一起，读者一个数都读不出来",
            "只取 Top N 而丢掉其余：图上总量与真实总量不符，属于误导性图表",
            "饼图放超过 5 个类别：扇形角度太接近，肉眼根本分不出大小",
            "服务端渲染失败就抛异常：一张图画不出来，整条回答也跟着失败",
        ],
        "task": """请实现 `top_n_with_other(items, n)`：

- `items`：`[{"name": str, "value": int}, ...]`
- 按 `value` **从大到小**排序（`value` 相同时保持原顺序）
- 取前 `n` 项；如果还有剩余，把剩余项的 `value` 求和，追加一项 `{"name": "其他", "value": 总和}`
- 总条数 `<= n` 时原样返回（不要造「其他」）
- 空列表返回 `[]`
- `n < 1` 时抛 `ValueError`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先 `if n < 1: raise ValueError(...)`。用 `sorted(items, key=lambda x: -x["value"])`（Python 的 sort 是稳定的，同分会保持原序）。切片后判 `if len(rest) > 0` 再追加「其他」。""",
        "checker": CHART_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "为什么热门排行图要用「Top N + 其他」而不是「只画 Top N」？",
                "options": [
                    "颜色更好看",
                    "保留总量信息，避免读者误以为图上几项就是全部",
                    "减少数据库查询量",
                    "因为「其他」这一项数值最大",
                ],
                "answer_index": 1,
                "explanation": "只画前 N 项会让图上总和远小于真实总量，属于误导性可视化。「其他」这根柱子诚实地表示「剩余的都在这儿」。",
            },
            {
                "type": "choice",
                "stem": "饼图最多放几个类别比较合适？",
                "options": ["2 个", "5 个左右", "15 个", "越多越好"],
                "answer_index": 1,
                "explanation": "饼图靠角度对比，超过 5 份后人眼几乎分不出大小差异。类别多应该换柱状图或直接上表格。",
            },
            {
                "type": "judge",
                "stem": "服务端渲染图表时，某一张图失败应该让整个回答也失败，这样用户能明确知道出问题了。",
                "answer": False,
                "explanation": "图表是增强信息，不是主内容。单图失败应该跳过并记录日志，文字回答照常返回——否则一个绘图 bug 会让整个客服功能不可用。",
            },
            {
                "type": "blank",
                "stem": "类别太多时，把长尾合并成一项，这一项通常命名为「______」。",
                "answer": "其他",
                "hint": "填两个字",
                "explanation": "「其他」是可视化里的标准做法，既压缩了维度，又保留了总量信息。",
            },
        ],
    },
]
