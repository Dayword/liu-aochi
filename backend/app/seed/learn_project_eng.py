"""Python 工程 10 课 + AI Agent 10 课在鸭先知项目里的真实落点。"""

from .learn_project_base import absent, choice, judge, used

REFS: dict[str, dict] = {
    "eng-json": used(
        "core/cache.py", "178",
        "self._client.setex(key, ttl or CACHE_TTL, json.dumps(payload, ensure_ascii=False))",
        "把问答结果（含正文、引用文档、耗时）序列化成 JSON 字符串，再塞进 Redis。",
        "Redis 只能存字符串/字节，不能直接存 dict，所以进出都要序列化：写入 `json.dumps`，读出 `json.loads`。"
        "`ensure_ascii=False` 让中文原样存，否则一条中文回答会膨胀成 `\\uXXXX` 形式，既占空间又没法用 redis-cli 直接看。"
        "注意 `json.dumps` 不支持 datetime、set、自定义对象，遇到就抛 TypeError——"
        "存时间要先转成 `isoformat()` 字符串，项目里所有缓存 payload 都是这么处理的。",
        [
            choice("把 dict 存进 Redis 之前必须做什么？",
                   ["直接存，Redis 支持 dict", "先 json.dumps 序列化成字符串", "先转成 bytes 再 base64", "先计算哈希"],
                   1, "Redis 的值是二进制安全的字符串，dict 必须先序列化。读出时再 json.loads 还原。"),
            judge("json.dumps 能直接把 datetime 对象序列化成字符串。", 0,
                  "错。它会抛 TypeError: Object of type datetime is not JSON serializable。要先 .isoformat() 转成字符串。"),
        ],
    ),
    "eng-env": used(
        "config.py", "218-226",
        'AMAP_WEB_SERVICE_KEY = os.getenv("AMAP_WEB_SERVICE_KEY", "")\nAMAP_TIMEOUT = float(os.getenv("AMAP_TIMEOUT", "5"))\n...\nREDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")   # 从 .env 读取；凭据一律不入库',
        "所有密钥、地址、超时都从环境变量读，代码里只留默认值和安全兜底。",
        "`os.getenv(key, default)` 的第二个参数很重要：本地没配 .env 时程序还能起来，而不是 KeyError 直接崩。"
        "环境变量读回来**永远是字符串**，要参与计算必须显式转换（`float(...)`、`int(...)`），"
        "忘了转就会出现「超时 5 秒」变成字符串比较的诡异 bug。"
        "最要紧的是注释里那句「凭据一律不入库」——密钥只能放 .env，而 .env 必须在 .gitignore 里，"
        "一旦提交进 Git 历史，删掉文件也救不回来。",
        [
            choice("从环境变量读到 AMAP_TIMEOUT=5，直接写 `if elapsed > AMAP_TIMEOUT` 会有什么问题？",
                   ["没问题", "字符串和数字比较会抛 TypeError", "结果永远为真", "自动转成数字"],
                   1, "getenv 返回的是字符串 \"5\"，Python 3 里字符串和 float 比较直接 TypeError，所以项目里显式写成 float(...)。"),
            judge("把 .env 提交进 Git 之后，只要再删掉文件并提交一次，密钥就安全了。", 0,
                  "错。Git 保留完整历史，任何人 clone 后都能翻出旧提交。密钥泄露必须立刻去平台轮换，而不是删文件。"),
        ],
    ),
    "eng-log": used(
        "core/cache.py", "19",
        '_logger = logging.getLogger("redis")',
        "缓存模块单独拿一个名为 redis 的 logger，记录连接失败与降级。",
        "`logging.getLogger(name)` 按名字取 logger，同名拿到的是同一个对象，所以可以按模块/组件分别控制级别。"
        "用 `__name__` 时日志里会带上完整模块路径，排查时能直接定位到文件；这里手写 \"redis\" 是为了让缓存日志独立成一路。"
        "不要用 print：print 没有级别、没有时间戳、不能按环境关掉，线上没法用。"
        "另外 logger 要**惰性格式化**（`logger.info(\"%s\", x)`），别提前拼好字符串——那条日志被级别过滤掉时，拼接的开销就白花了。",
        [
            choice("为什么推荐 `logging.getLogger(__name__)` 而不是 `logging.getLogger()`？",
                   ["性能更好", "日志里会带上模块名，能直接定位来源", "能自动写文件", "可以避免重复日志"],
                   1, "__name__ 是模块的完整路径，日志记录里带上它，出问题一眼知道是哪个文件打的。"),
            judge("生产代码里用 print 输出调试信息，和 logging 效果等价。", 0,
                  "错。print 没有级别、时间戳、来源，也不能被统一关闭或转到文件，线上无法管理和检索。"),
        ],
    ),
    "eng-typing": used(
        "agents/retrieval_agent.py", "31-33",
        "def search(self, query: str, top_k: int = None, use_cache: bool = True,\n           alpha: float = None, report: dict = None,\n           rerank: bool = True) -> List[Tuple[str, str, float]]:",
        "检索入口标清参数类型和返回值结构：返回的每条是 (正文, 来源, 分数)。",
        "`List[Tuple[str, str, float]]` 这一行胜过三行注释——调用方不用翻实现就知道怎么解包。"
        "类型注解**运行时不检查**（除非你用 pydantic 或 mypy），它的价值在 IDE 补全、静态检查和文档。"
        "注意 `top_k: int = None` 这种写法其实不严谨（None 不是 int），更规范的写法是 `Optional[int]`；"
        "项目里两种都有，读的时候别被绕进去。",
        [
            choice("`-> List[Tuple[str, str, float]]` 这条注解在运行时起什么作用？",
                   ["强制校验类型，不符就抛异常", "基本不做检查，主要给 IDE 和静态工具看", "自动转换成对应类型", "没有作用"],
                   1, "注解默认不被强制检查（Python 不做运行时类型校验），除非借助 pydantic 或 mypy 这类工具。"),
            judge("参数写成 `top_k: int = None` 在类型上是严谨的，因为 None 也是合法默认值。", 0,
                  "错。严谨写法是 Optional[int]。注解写成 int 却传 None，mypy 会直接报错，属于「能跑但类型不干净」。"),
        ],
    ),
    "eng-http": used(
        "api/amap.py", "44-46",
        'resp = requests.get(f"{AMAP_BASE_URL}/staticmap", params=params, timeout=AMAP_TIMEOUT)\n...\nexcept requests.exceptions.Timeout:',
        "调高德地图的静态图接口，超时单独捕获并降级。",
        "`timeout=AMAP_TIMEOUT` 是必须的：requests 默认**不超时**，对端不响应时你的线程会永远挂着，"
        "高并发下很快就打满线程池。超时要分成「连接超时」和「读超时」两段来设，生产环境常用 `(3, 10)` 元组。"
        "`params=` 交给 requests 做 URL 编码，别自己拼字符串——中文和特殊字符会拼错。"
        "另外记得 `raise_for_status()`：HTTP 4xx/5xx 默认不抛异常，只看 `resp.text` 会把错误当成功。",
        [
            choice("requests.get 不写 timeout 的主要风险是什么？",
                   ["返回内容变短", "对端不响应时线程永久挂起", "无法发送请求", "自动重试三次"],
                   1, "默认无超时，连接或读取会一直等，线程被占满后整个服务不可用。"),
            judge("HTTP 返回 404/500 时，requests.get 会抛异常，所以必须 try/except。", 0,
                  "错。4xx/5xx 默认不抛异常，需要显式 resp.raise_for_status() 才会抛。"),
        ],
    ),
    "eng-async": used(
        "api/chat.py", "85",
        "async def chat_stream(req: AskRequest,",
        "流式问答接口写成 async 函数，内部用 async 生成器逐帧 yield 给前端。",
        "`async def` 调用后返回的是协程对象，不 await 就不执行；用 FastAPI 时框架负责调度。"
        "关键纪律：**async 函数里不能做阻塞调用**。写 `time.sleep(1)`、`requests.get(...)` 或同步数据库驱动，"
        "会把整个事件循环卡住，同一进程的其他请求全部排队——"
        "该用 `await asyncio.sleep(1)`、`httpx.AsyncClient`，或者把阻塞操作丢进线程池 `run_in_executor`。",
        [
            choice("在 async 函数里调用 `time.sleep(2)` 会发生什么？",
                   ["只阻塞当前协程", "阻塞整个事件循环，其他请求一起卡住", "自动转成异步", "报 RuntimeError"],
                   1, "time.sleep 是阻塞调用，事件循环被它占住，期间所有协程都无法推进。要写 await asyncio.sleep(2)。"),
            judge("定义成 async def 的函数，调用时会立刻开始执行函数体。", 0,
                  "错。调用只得到协程对象，必须 await 或交给事件循环调度才执行。"),
        ],
    ),
    "eng-pydantic": used(
        "api/admin.py", "207",
        "class CardUpsertRequest(_BaseModel):",
        "后台接口的请求体用 pydantic 模型声明，进函数前就完成校验。",
        "pydantic 在**实例化时**按类型注解校验并转换：传 `\"100\"` 给 int 字段会转成 100，传 `\"abc\"` 直接抛 422，"
        "根本进不到你的业务代码。这比手写一堆 `if not isinstance(...)` 可靠得多。"
        "配合 `Field(..., ge=0)` 还能加取值范围约束。"
        "注意默认的 BaseModel 会**忽略**多余字段，要求严格拒绝时要设 `model_config = ConfigDict(extra=\"forbid\")`，"
        "否则前端多传的字段会被静默丢弃，排查起来很费劲。",
        [
            choice("前端给 pydantic 模型的 int 字段传了字符串 \"100\"，默认会发生什么？",
                   ["直接 422 报错", "自动转换为 100 并通过校验", "变成字符串保留", "静默设为 None"],
                   1, "pydantic 会做宽松类型转换，能转就转；转不了才报校验错误。"),
            judge("pydantic 默认会拒绝请求体里出现模型未声明的多余字段。", 0,
                  "错。默认是忽略（extra='ignore'），要多传就报错得显式配置 extra='forbid'。"),
        ],
    ),
    "ai-llm-api": used(
        "core/llm_client.py", "224-229",
        "stream = self.client.chat.completions.create(\n    model=model or LLM_TEXT_MODEL,\n    messages=messages,\n    temperature=LLM_TEMPERATURE,\n    stream=True,\n    **kwargs,\n)",
        "一次对话补全调用：指定模型、消息列表、温度、是否流式。",
        "四个参数各有讲究：`model` 决定能力和价格；`messages` 是 `[{\"role\": ..., \"content\": ...}]` 的列表；"
        "`temperature=0.1` 让输出稳定可复现——问答场景不需要创造力，调高只会让同一问题每次答得不一样；"
        "`stream=True` 打开流式。项目里 `**kwargs` 透传是为了不锁死签名。"
        "另外 `model or LLM_TEXT_MODEL` 是「没传就用默认」，比在函数里写 if 判断简洁。",
        [
            choice("问答类应用把 temperature 调到 0.1 而不是 1.0，主要为了什么？",
                   ["降低成本", "让回答稳定、可复现，减少胡编", "提高速度", "支持流式输出"],
                   1, "temperature 控制采样随机性。问答要的是稳定准确，低温度更合适；创意写作用高温度。"),
            judge("调用大模型时 messages 里 role 只能是 system 和 user。", 0,
                  "错。常见还有 assistant（历史回复）和 tool（工具结果）。多轮对话必须把 assistant 的历史回复也带上。"),
        ],
    ),
    "ai-prompt": used(
        "agents/business_agent.py", "351",
        'SYSTEM_PROMPT = f"""你是"{PARK_NAME}"微信小程序里的智能业务助手，能够直接帮用户"办成一件事"：查储值卡余额、每日签到、查失物招领、查游乐项目价目、按余额与偏好排游玩组合、推荐办卡方案。',
        "业务 Agent 的系统提示词：先定身份，再列能力边界，最后给输出要求。",
        "system 消息定义「你是谁、能做什么、不能做什么」，user 消息才是本次需求——这个分工决定了模型的行为基调。"
        "写好提示词的三个要点都在这段里：**身份具体**（不是「助手」而是「园区业务助手」）、**能力枚举**（把能办的事逐条列出）、"
        "**边界明确**（办不到时怎么说）。"
        "工程上注意它被提到模块级常量（只构一次），而不是每次请求重新拼字符串——既省开销，也避免拼错。",
        [
            choice("把「你是园区业务助手，能办这些事…」放在 system 而不是 user，主要区别是什么？",
                   ["没区别", "system 定义角色与规则，对整个会话持续生效；user 是本次具体需求", "system 更省 token", "user 不能包含中文"],
                   1, "system 定基调、user 提需求。把角色写进 user 会导致多轮对话里角色约束逐渐失效。"),
            judge("提示词写得越抽象越好，比如「你是智能助手」，给模型留发挥空间。", 0,
                  "错。身份越具体、边界越清楚，模型越不容易跑偏。抽象提示词只会让输出不可控。"),
        ],
    ),
    "ai-structured": used(
        "agents/admin_assistant.py", "265-270",
        'if text.startswith("⛔ "):\n    try:\n        card = json.loads(text[2:])\n    except Exception:\n        card = {"tool": name, "args": args, "preview": text[2:120],\n                "token": "", "impact": ""}',
        "约定「⛔ 前缀 + JSON」的协议：模型要确认高危操作时按这个格式输出，解析失败就降级成兜底卡片。",
        "这是让 LLM 输出结构化数据的实战写法：**用前缀标记类型 + 只对标记后的部分做 json.loads**，"
        "而不是指望整段回答都是合法 JSON。关键是那段 except——模型漏个引号、多写一句话都很常见，"
        "解析失败必须能降级（这里用工具名和参数拼一个最小可用卡片），否则整个功能直接 500。"
        "更稳的做法是用模型的原生 JSON mode / function calling，让服务端保证结构合法，"
        "但**下游仍然要 try/except**：网络截断、max_tokens 截断都会产出半截 JSON。",
        [
            choice("从模型输出里解析 JSON，为什么外面必须包 try/except？",
                   ["为了性能", "模型可能输出半截 JSON 或夹带解释文字，解析会抛异常", "json.loads 需要捕获所有异常才返回", "为了记录日志"],
                   1, "LLM 输出不受你控制，截断、夹带说明都很常见，解析失败是常态而不是意外。"),
            judge("用了模型的 JSON mode，下游就不需要再做异常处理了。", 0,
                  "错。JSON mode 只提升合法率，不保证 100%；而且 max_tokens 截断照旧会产出半截 JSON，兜底不能省。"),
        ],
    ),
    "ai-tools": used(
        "agents/business_agent.py", "426-438",
        "tools = get_business_tools(user, ctx=ctx)\n...\n    tools = tools + get_account_tools(user, ctx=ctx)\n...\n    tools = tools + get_service_tools(user, ctx=ctx)",
        "按用户身份和意图动态拼装本次可用的工具列表，再交给模型。",
        "function calling 的本质：你把一组「工具说明书」（名字、用途、参数 schema）随请求发给模型，"
        "模型不执行任何代码，只回一个「我要调哪个工具、参数是什么」，真正执行由你的代码完成。"
        "所以**工具的描述写得准不准，直接决定模型选得对不对**——参数说明含糊，模型就会瞎填。"
        "这里按权限裁剪工具列表也是安全设计：普通用户根本拿不到退款工具，模型想调也没有这个选项。",
        [
            choice("function calling 中，真正执行工具函数的是谁？",
                   ["模型自己", "你的后端代码", "OpenAI 服务器", "前端浏览器"],
                   1, "模型只输出「调用意图 + 参数」，执行和结果回传都由你的程序完成。"),
            judge("工具列表里保留用户无权使用的工具没关系，模型不会乱调。", 0,
                  "错。模型可能被诱导去调，而且权限判断不该依赖模型守规矩。按身份裁剪工具列表才是正确做法。"),
        ],
    ),
    "ai-agent-loop": used(
        "agents/orchestrator.py", "1009-1017",
        "while True:\n    try:\n        item = q.get(timeout=60)  # AgentExecutor 自限 45s，此处 60s 兜底\n    except _queue.Empty:\n        map_result = map_agent._fallback_result(user_query, history, start_time, \"agent_timeout\")\n        break\n    if \"__result__\" in item:\n        map_result = item[\"__result__\"]\n        break",
        "等子 Agent 返回结果的主循环：三种出口——拿到结果、拿到错误、超时降级。",
        "Agent 循环必须有**明确的退出条件**，否则就是死循环。这段代码把出口写全了："
        "`__result__` 正常结束、`__error__` 异常结束、`queue.Empty` 超时结束，每条路都会 break。"
        "超时值还有讲究：子 Agent 自己限 45 秒，这里等 60 秒，留出 15 秒缓冲——"
        "如果两处都设 45 秒，边界上会互相抢跑，日志里就会出现「明明成功了却报超时」。"
        "这也是 ReAct 类循环的通用纪律：迭代次数上限 + 单步超时 + 失败降级，三样缺一不可。",
        [
            choice("子 Agent 内部限时 45 秒，外层等待设 60 秒，为什么外层要更长？",
                   ["随便设的", "留缓冲，避免边界同时超时导致误判失败", "为了省资源", "queue 最小单位是 60 秒"],
                   1, "外层比内层长，内层才有机会正常返回错误信息；两层相等会在边界互相抢跑。"),
            judge("写 Agent 循环时只要有 while True 就够了，退出靠模型自己判断。", 0,
                  "错。必须有硬性的迭代上限和超时兜底。模型可能反复调工具不收敛，没有硬限制就会烧钱。"),
        ],
    ),
    "ai-stream": used(
        "api/chat.py", "94-98",
        'async def greet_gen():\n    resp = query_agent.get_greeting_response()\n    yield f"data: {json.dumps({\'type\': \'meta\', \'reference_doc\': []}, ensure_ascii=False)}\\n\\n"\n    yield f"data: {json.dumps({\'type\': \'chunk\', \'content\': resp}, ensure_ascii=False)}\\n\\n"\n    yield f"data: {json.dumps({\'type\': \'done\'}, ensure_ascii=False)}\\n\\n"',
        "流式接口的三种帧：meta（引用文档）、chunk（正文片段）、done（结束）。",
        "把流式协议设计成带 `type` 的信封，是为了让前端知道「这一帧该干什么」："
        "meta 先把引用文档渲染出来，chunk 不断追加文字，done 收起加载状态。"
        "少一个 done 前端就会一直转圈——这类「协议缺一帧」的 bug 在流式里特别常见。"
        "技术上它走的是 `StreamingResponse(..., media_type=\"text/event-stream\")`，"
        "HTTP 层面是分块传输（chunked），所以响应头里没有 Content-Length，代理要是开了缓冲会把流式变成「一次性吐完」。",
        [
            choice("SSE 流式响应里 meta / chunk / done 三种帧的作用是什么？",
                   ["压缩传输", "让前端按类型分别处理：引用、正文增量、结束状态", "加密", "重连标识"],
                   1, "带 type 的信封让前端知道每帧语义，缺了 done 前端无法判断流是否结束。"),
            judge("流式响应经过开启了缓冲的 Nginx 时，可能会变成「等全部生成完才一次性返回」。", 1,
                  "对。代理缓冲会攒够一段再转发，需要关掉 proxy_buffering 或加 X-Accel-Buffering: no。"),
        ],
    ),
    "ai-rag": used(
        "agents/retrieval_agent.py", "3-24",
        "# 职责：BM25 + BGE-M3 混合检索 + BGE-Reranker 重排序\n# 融合策略：分数级 min-max 归一化 + 加权融合（alpha=0.6 语义，0.4 关键词）\n...\n流程：\n1. BGE-M3 向量检索（稠密语义匹配，Milvus + IP 内积）\n2. BM25 关键词检索（稀疏词频匹配，jieba 分词 + BM25Okapi）\n3. 分数归一化 + 加权融合（alpha 控制语义 vs 关键词权重）\n4. BGE-Reranker 语义重排序（BAAI/bge-reranker-v2-m3）\n5. 相似度阈值过滤",
        "整个 RAG 检索链路的五步：向量召回 + 关键词召回 → 归一化加权融合 → 重排序 → 阈值过滤。",
        "为什么要两路召回：向量擅长「意思相近但用词不同」（问「怎么办卡」能召回「充值流程」），"
        "BM25 擅长「精确关键词」（型号、专有名词，向量反而容易糊）。两路互补，缺一路就有一类问句答不准。"
        "融合前必须归一化，因为余弦相似度在 0~1、BM25 分数可能到几十，直接相加等于让 BM25 单方面决定结果。"
        "最后的重排是**精排**：召回阶段只求「别漏」，用便宜模型捞 50 条；重排用贵的 cross-encoder 只算这 50 条，把最相关的顶到前面。"
        "阈值过滤则是防幻觉的最后一道闸——最高分都不到阈值，就承认「不知道」，别硬答。",
        [
            choice("混合检索里，向量召回和 BM25 各自擅长什么？",
                   ["向量擅长精确关键词，BM25 擅长语义", "向量擅长语义相近，BM25 擅长精确关键词", "两者完全等价", "BM25 只支持英文"],
                   1, "稠密向量匹配语义，稀疏 BM25 匹配字面词频。互补才需要融合。"),
            judge("两路召回的分数量纲不同，可以直接相加后排序。", 0,
                  "错。余弦相似度和 BM25 分数范围差几个量级，直接相加等于让分数大的那一路独占权重，必须先归一化。"),
        ],
    ),
    "ai-memory": used(
        "core/chat_memory.py", "99-104",
        "history_lines = []\nfor r in user_msgs[-limit:]:\n    if r.get(\"role\") == \"user\":\n        history_lines.append(f\"用户：{r.get('content', '')}\")\n    else:\n        history_lines.append(f\"AI：{r.get('content', '')}\")",
        "取最近 limit 条消息，拼成「用户：… / AI：…」的文本，供下一轮改写和追问使用。",
        "`user_msgs[-limit:]` 是**滑动窗口**：只带最近 N 条，不是全量历史。"
        "原因很实在——上下文窗口有限，而且 token 是钱，把 200 轮历史全塞进去既贵又容易淹没重点。"
        "代价是「你上周说的那个」这类跨轮指代会失效，所以工程上还要配一层长期记忆（把关键事实摘要存下来）。"
        "另外这里把结构化消息拼成纯文本，是为了塞进 prompt 好读；如果要用原生多轮接口，应该保留 role 结构直接传 messages。",
        [
            choice("`user_msgs[-limit:]` 这种写法实现的是什么？",
                   ["全量历史", "只取最近 limit 条的滑动窗口", "随机采样", "按时间过滤到当天"],
                   1, "负索引切片取末尾 N 条，这就是最常用的多轮记忆窗口。"),
            judge("把全部历史对话都塞进 prompt 一定比只带最近几条效果好。", 0,
                  "错。会撞上下文上限、成本高，而且无关历史会稀释当前问题的重点。正确做法是窗口 + 关键信息摘要。"),
        ],
    ),
    "eng-test": used(
        "tests/test_core_units.py", "17",
        "class TestScoreFusion:",
        "用 pytest 的类把相关用例分组，覆盖分数融合、BM25、缓存 key、编排流程。",
        "pytest 用类组织用例只是**分组手段**，不是 xUnit 那种继承体系：类名要以 Test 开头、方法名以 test_ 开头，"
        "并且不需要继承任何基类。真正让测试能跑起来的是「不依赖真实外部服务」——"
        "这个文件里用 `FakeRetrievalAgent`、`FakeLLMClient` 替掉了真模型，"
        "否则一条用例要等十几秒、还要花 token，没人愿意跑。"
        "写测试的顺序建议：先测纯函数（分数融合、缓存 key 这种），再测流程（用 Fake），最后才碰集成。",
        [
            choice("pytest 里用 class 组织用例，需要继承某个基类吗？",
                   ["需要继承 unittest.TestCase", "不需要，类名 Test 开头即可", "需要继承 pytest.Test", "必须加 @pytest.fixture"],
                   1, "pytest 靠命名约定发现用例，不强制继承。继承 unittest.TestCase 是另一种兼容写法。"),
            judge("单元测试里调用真实大模型接口，能让测试更可信。", 0,
                  "错。会让测试变慢、不稳定、还烧钱。应该用 Fake/Stub 替掉外部依赖，真实调用放到单独的集成测试里。"),
        ],
    ),
    "eng-deps": used(
        "requirements.txt", "2-10",
        "fastapi==0.115.0\nuvicorn==0.30.6\n...\nlangchain==0.3.30\nlangchain-core==0.3.86",
        "依赖全部锁死到具体版本，并按用途分区块注释。",
        "`==` 精确锁版本，是为了「今天能跑，三个月后 clone 下来还能跑」。"
        "如果写 `fastapi>=0.100`，某天上游发个不兼容的小版本，你的构建就莫名其妙挂了，而且极难定位。"
        "分区块注释（Web 框架 / LangChain 生态 / 数据库…）在依赖上百个时特别有用，能一眼看出哪个包是干哪行的。"
        "真正规范的做法是把直接依赖和间接依赖分开管理（requirements.in + pip-compile 生成 requirements.txt），"
        "但这个项目规模用单文件锁版本已经够了。",
        [
            choice("requirements.txt 里写 `fastapi==0.115.0` 而不是 `fastapi>=0.115`，主要好处是？",
                   ["安装更快", "构建可复现，不会因为上游发新版突然挂掉", "体积更小", "自动升级"],
                   1, "锁版本保证任何时间、任何机器装出来的依赖树一致，这是可复现构建的基础。"),
            judge("虚拟环境（venv）和 requirements.txt 是一回事，有一个就够了。", 0,
                  "错。venv 隔离的是「装在哪儿」，requirements.txt 记录的是「装哪些、什么版本」，两者解决不同问题。"),
        ],
    ),
    "eng-quality": absent(
        "# 项目里没有 ruff / black / mypy 的配置文件\n# 全项目 0 处 pyproject.toml 的 [tool.ruff] 段、0 处 .ruff.toml、0 处 setup.cfg\n# 现状：靠统一的代码风格约定（类型注解 + 分区块注释）人工维持",
        "项目没有接入任何自动化代码质量工具：没有 ruff、没有 black、没有 mypy，也没有 CI 检查。",
        "这不代表这些工具没用，而是这个项目「靠人盯」还能撑住——单人开发、风格统一。"
        "一旦多人协作，没接工具就会立刻失控：缩进、引号、import 顺序每人一套，review 全花在格式上。"
        "最小可用组合是 ruff（格式 + lint 二合一，比 flake8 快一个数量级）+ mypy（类型检查）。"
        "对 pydantic 项目，mypy 配 `plugins = pydantic.mypy` 才能正确理解模型字段；"
        "真接的时候建议先只上 ruff 不阻塞提交（`--exit-zero`），跑一周看看噪音量再决定是否卡 CI。",
        [
            choice("项目里同时用 ruff 和 black 时，为什么通常建议只留 ruff？",
                   ["ruff 不支持格式化", "ruff 已内置 black 兼容的格式化，两套一起跑会互相改", "black 收费", "ruff 只能检查不能修"],
                   1, "ruff format 与 black 风格基本一致，同时装会出现两个工具反复改写同一段代码。"),
            judge("给一个已有项目接入 mypy，第一天就应该开 `--strict` 并把所有报错卡在 CI 上。", 0,
                  "错。存量代码报错量通常上千条，直接卡死没人能提交。应该先跑起来看基线，分批修，最后再收紧。"),
        ],
    ),
    "ai-eval": used(
        "bench_eval.py", "1-5",
        "# RAG 系统综合评测脚本\n# 指标：召回率 | 精确度 | 幻觉率 | 响应速度 | Token命中率",
        "离线评测脚本：从 chunks 的「常见问法」自动生成 QA 对，再跑一遍全链路算指标。",
        "评测是 Agent 项目最容易欠账的一环。这个脚本抓的五个指标其实覆盖了四类问题："
        "召回率/精确度看**检索准不准**，幻觉率看**生成可不可信**，响应速度看**体验**，Token 命中率看**成本**。"
        "评测集用的是 `eval/heldout_questions.json`——必须和调参时看到的样本分开，"
        "否则你只是在背答案，线上换一批问法立刻打回原形。"
        "工程上最重要的纪律：**改完 prompt 或检索参数，重跑评测再合并**，别凭几条 case 的手感上线。",
        [
            choice("评测集为什么要单独留一份 heldout（留出集）？",
                   ["节省内存", "防止调参时背答案，评估结果虚高", "加快运行速度", "方便多人共用"],
                   1, "用调参时看过的数据评估等于自欺欺人，必须留一份没见过的问句来测真实泛化。"),
            judge("召回率提高，精确度必然也提高。", 0,
                  "错。两者常常此消彼长：多召回一些文档（提高召回）往往带进噪音（拉低精确）；这中间的取舍要靠阈值和重排来平衡。"),
        ],
    ),
    "ai-multiagent": used(
        "agents/orchestrator.py", "55-63",
        "class SubTaskType(str, Enum):\n    \"\"\"子任务类型\"\"\"\n    QUERY_REWRITE = \"query_rewrite\"       # Query 改写\n    DOCUMENT_SEARCH = \"document_search\"   # 文档检索\n    RETRIEVAL = \"retrieval\"               # 混合检索\n    VERIFICATION = \"verification\"         # 校验与溯源\n    GENERATION = \"generation\"             # 答案生成\n    COMPLEX_SPLIT = \"complex_split\"       # 复杂问题拆分",
        "编排层把一个问题拆成有类型的子任务，再分派给对应的专职 Agent。",
        "多 Agent 的核心不是「Agent 越多越强」，而是**职责隔离**：检索的只管检索、校验的只管核对出处，"
        "每个 Agent 的 prompt 和工具都能调到最专一。代价是链路变长、延迟叠加、失败点变多。"
        "所以编排层必须做三件事：拆任务（`COMPLEX_SPLIT`）、定顺序（哪些能并行）、兜失败（某一步挂了要不要降级继续）。"
        "判断要不要拆多 Agent 的标准很土但很准：**单个 prompt 已经塞不下、或者不同步骤需要完全不同的工具集**时才拆，"
        "否则一个函数能解决的事别上编排。",
        [
            choice("把一个功能拆成多个 Agent，最主要的代价是什么？",
                   ["代码变短", "链路变长、延迟叠加、失败点增多", "模型能力下降", "无法使用工具"],
                   1, "每多一跳就多一次模型调用和网络往返，也多一个可能失败的地方，需要编排层兜底。"),
            judge("Agent 数量越多，系统能力一定越强。", 0,
                  "错。拆分只在「职责确实不同、单个 prompt 撑不住」时才有收益，否则只是把复杂度堆高。"),
        ],
    ),
}
