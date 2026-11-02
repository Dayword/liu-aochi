# -*- coding: utf-8 -*-
"""后端服务工程 / 多模态与部署 / AI 工程质量：10 个分支的知识点与标准答案。

数据来源：原 learn_mindmap.py 的考点树 + 人工补写的 kp / answer。
每条 = 一个面试考点：
    name   考官的问法（面试考题页的题干）
    kp     浓缩成名词的知识点标签（思维导图页的节点）
    answer 40~80 字的标准答案，能落到鸭先知项目的地方直接带项目细节
    code   对应的站内课程，None 表示「会考但站内还没课」
    hot    3 必问 / 2 常问 / 1 纵深

⚠️ 改完跑 `python learn_mindmap_check.py`：它会校验 code 是否存在、
答案长度、kp 是否为空，退出码 0 才算过。
"""

TREES: dict[str, dict] = {
    "后端服务工程": {
        "intro": 'AI 应用的后端和普通后端最大的差别是「长耗时 + 流式 + 不稳定」，所以面试会盯着流式怎么做、超时怎么设、失败了怎么重试。',
        "branches": [
            {
                "name": '框架与依赖注入',
                "items": [
                {"name": 'FastAPI 的依赖注入怎么用，Depends 能解决什么', "kp": 'FastAPI Depends', "code": 'be-fastapi', "hot": 3,
                 "answer": 'Depends 声明依赖，框架按签名自动注入，并缓存同一次请求内的结果。常用于取当前用户、数据库会话、分页参数。'},
                {"name": '同步路由与异步路由混用会出什么问题', "kp": '同步异步路由混用', "code": 'be-fastapi', "hot": 3,
                 "answer": 'async def 里跑同步阻塞代码会堵住事件循环，拖慢所有请求；同步 def 会被丢到线程池。混用要么全异步，要么阻塞调用丢 to_thread。'},
                {"name": 'Pydantic 模型在请求校验里的执行时机', "kp": 'Pydantic 校验时机', "code": 'be-fastapi', "hot": 2,
                 "answer": '在进路由函数之前，FastAPI 解析请求体时就校验，失败直接返 422；业务代码拿到的已经是校验过的对象。'},
                {"name": '中间件、拦截器、装饰器的执行顺序', "kp": '中间件/依赖/装饰器', "code": 'be-fastapi', "hot": 2,
                 "answer": '请求先过中间件（响应时逆序出），再到依赖，最后进路由；异常处理器在更外层兜底。'},
                {"name": '分层怎么分：router / service / repository 的边界', "kp": '分层边界', "code": 'be-fastapi', "hot": 2,
                 "answer": 'router 只做参数校验和响应组装，service 放业务和事务，repository 只管数据访问。跨层调用会让逻辑散进 SQL 里没法测。'},
                ],
            },
            {
                "name": '认证与鉴权',
                "items": [
                {"name": 'JWT 的结构，为什么不能在里面放敏感信息', "kp": 'JWT 结构', "code": 'be-auth', "hot": 3,
                 "answer": 'header.payload.signature 三段 base64；payload 只是编码不是加密，谁都能解，所以不能放密码和隐私。'},
                {"name": 'JWT 无法主动失效，怎么做到登出', "kp": 'JWT 登出', "code": 'be-auth', "hot": 3,
                 "answer": 'JWT 无状态没法主动失效。用短有效期 + refresh token，服务端维护黑名单或版本号，改密码时让旧 token 全作废。'},
                {"name": '密码为什么用 bcrypt 而不是 MD5 / SHA256', "kp": '为什么用 bcrypt', "code": 'be-auth', "hot": 3,
                 "answer": 'MD5/SHA256 太快，暴力破解和彩虹表成本低；bcrypt 自带盐、可调 cost 拖慢计算，专为存密码设计。'},
                {"name": 'Session 与 Token 的架构差异', "kp": 'Session vs Token', "code": 'be-auth', "hot": 3,
                 "answer": 'Session 状态在服务端，靠 Cookie 带 id，好撤销但要多机共享；Token 状态在客户端，服务端无状态易扩展但撤销麻烦。'},
                {"name": '越权漏洞：水平越权和垂直越权怎么防', "kp": '越权漏洞', "code": None, "hot": 3,
                 "answer": '水平越权是改 id 看别人的数据，垂直越权是低权限调高权限接口。每个接口都要校验这条资源属不属于当前用户。'},
                ],
            },
            {
                "name": '流式输出与长连接',
                "items": [
                {"name": 'SSE 与 WebSocket 怎么选，各自适用什么场景', "kp": 'SSE vs WebSocket', "code": 'be-sse', "hot": 3,
                 "answer": 'SSE 是单向服务端推送、走 HTTP、自动重连，适合流式输出；WebSocket 全双工，适合聊天和协同编辑。'},
                {"name": 'SSE 的响应头和分帧格式，为什么必须关缓冲', "kp": 'SSE 头与分帧', "code": 'be-sse', "hot": 3,
                 "answer": 'Content-Type: text/event-stream，每帧 `data: ...` 加空行结尾；必须关掉 Nginx 缓冲（X-Accel-Buffering: no），否则会攒着一起发。'},
                {"name": '流式输出中途出错，怎么让前端知道', "kp": '流式中途出错', "code": 'be-sse', "hot": 3,
                 "answer": '已经发了 200 就没法改状态码，只能在流里发一个 error 事件，前端收到后提示并允许重试。'},
                {"name": 'Nginx 反向代理把流式吞了，怎么配', "kp": 'Nginx 吞流式', "code": 'be-sse', "hot": 3,
                 "answer": '关 proxy_buffering 和 proxy_cache，调大 proxy_read_timeout，加 X-Accel-Buffering: no，用 HTTP/1.1。'},
                {"name": '客户端断开后，后端还在生成 token 怎么止损', "kp": '客户端断开止损', "code": 'be-sse', "hot": 3,
                 "answer": '监听 request.is_disconnected() 或流的取消信号，断开就停掉生成，省下 token 和并发槽位。'},
                ],
            },
            {
                "name": '限流、任务与幂等',
                "items": [
                {"name": '固定窗口、滑动窗口、令牌桶、漏桶的区别', "kp": '四种限流算法', "code": 'be-ratelimit', "hot": 3,
                 "answer": '固定窗口简单但有临界突刺；滑动窗口平滑但要存时间戳；令牌桶允许突发；漏桶恒定速率、削峰最平。'},
                {"name": 'Redis 滑动窗口限流怎么用 ZSet 实现', "kp": 'ZSet 滑动窗口', "code": 'be-ratelimit', "hot": 3,
                 "answer": 'member 用请求 id、score 用时间戳；先 ZREMRANGEBYSCORE 清过期，再 ZCARD 判断，最后 ZADD，全程用 Lua 保证原子。'},
                {"name": '接口幂等有哪几种实现方式', "kp": '接口幂等实现', "code": 'be-payment', "hot": 3,
                 "answer": '唯一业务键加唯一索引、幂等 token（先占位再执行）、状态机只允许单向流转、Redis SETNX 锁住同一笔请求。'},
                {"name": '异步任务队列怎么保证不丢、不重复消费', "kp": '队列不丢不重', "code": 'be-async-task', "hot": 3,
                 "answer": '生产端确认加持久化，消费端手动 ack 且处理完再确认；重复消费靠幂等键兜底，别指望队列只投一次。'},
                {"name": '重试为什么必须配指数退避和抖动', "kp": '指数退避与抖动', "code": 'be-async-task', "hot": 3,
                 "answer": '固定间隔会一起打满下游（重试风暴）；指数退避拉大间隔，加随机抖动避免同一时刻齐发，还要设最大次数和熔断。'},
                {"name": '支付回调验签流程，为什么回调可能重复到达', "kp": '支付回调验签', "code": 'be-payment', "hot": 2,
                 "answer": '按平台规则拼参数用密钥签名，再校验金额和订单状态；回调会重复、会乱序，必须按订单号做幂等。'},
                ],
            },
        ],
    },
    "多模态与部署": {
        "intro": '考的是「你这套东西能不能真交付出去」：图片进模型怎么保证输出结构稳定、容器怎么做得小巧、小程序端登录态和重试怎么做。',
        "branches": [
            {
                "name": '视觉理解与结构化输出',
                "items": [
                {"name": '图片输入模型有哪几种方式（URL / base64 / file_id）', "kp": '图片输入的三种方式', "code": 'mm-vision', "hot": 3,
                 "answer": 'URL 由服务端拉取（注意可访问性和防盗链），base64 直接内联（体积涨 33%），file_id 先上传再引用（可复用、省带宽）。'},
                {"name": '怎么让模型输出稳定 JSON，失败了怎么兜底', "kp": '稳定 JSON 输出', "code": 'mm-vision', "hot": 3,
                 "answer": '用 JSON mode 或结构化输出约束 schema，再叠 Pydantic 校验；失败就把报错回灌重试一次，仍失败走默认值兜底。'},
                {"name": '图片太大怎么压缩，分辨率与精度的取舍', "kp": '图片压缩取舍', "code": 'mm-vision', "hot": 2,
                 "answer": '按模型建议把最长边缩到 1024~1568、JPEG 质量 80；降太多小字和表格就认不出，要按任务定。'},
                {"name": '多图与长文档的 token 成本怎么估', "kp": '多图与长文档成本', "code": 'mm-vision', "hot": 2,
                 "answer": '按图片切块计费，分辨率越高块数越多，还要加文本 token。批量前先算单页成本乘页数，别等账单出来才发现。'},
                ],
            },
            {
                "name": '文档解析',
                "items": [
                {"name": 'OCR 与版面分析的区别，为什么光 OCR 不够', "kp": 'OCR vs 版面分析', "code": 'mm-ocr', "hot": 3,
                 "answer": 'OCR 只把像素认成字，不管阅读顺序；版面分析先分出标题、正文、表格区域，再按区域 OCR，双栏和表格才不会串行。'},
                {"name": '表格还原成结构化数据有哪几种做法', "kp": '表格结构化', "code": 'mm-ocr', "hot": 3,
                 "answer": '规则解析按线框或空白对齐，最稳但脆；多模态模型直接出 Markdown/JSON，通用但要校验；复杂表用版面检测加单元格识别。'},
                {"name": '扫描件、双栏排版、页眉页脚怎么处理', "kp": '扫描件/双栏/页眉', "code": 'mm-ocr', "hot": 2,
                 "answer": '先二值化去噪，按投影或检测框判断栏数再分栏，页眉页脚按位置和重复文本过滤，倾斜的先纠偏。'},
                {"name": '解析结果的坐标信息有什么用', "kp": '坐标信息的用途', "code": 'mm-ocr', "hot": 1,
                 "answer": '坐标能还原阅读顺序、定位引用出处（点引用跳回原文位置），也能把表格单元格按行列框对齐。'},
                ],
            },
            {
                "name": '部署与端',
                "items": [
                {"name": 'Dockerfile 分层缓存怎么写才快', "kp": 'Dockerfile 分层缓存', "code": 'mm-docker', "hot": 3,
                 "answer": '把变化少的放前面：先 COPY 依赖清单装依赖，再 COPY 源码。否则改一行代码就把依赖层全废了。'},
                {"name": '镜像为什么越小越好，多阶段构建怎么瘦身', "kp": '镜像瘦身', "code": 'mm-docker', "hot": 3,
                 "answer": '选 slim 基础镜像，多阶段构建只把产物拷到运行阶段，清掉包缓存和编译工具，配 .dockerignore。'},
                {"name": 'compose 里服务依赖与健康检查怎么写', "kp": 'compose 依赖与健康检查', "code": 'mm-docker', "hot": 2,
                 "answer": 'depends_on 只保证启动顺序不保证可用，要配 healthcheck 加 condition: service_healthy，否则应用起来连不上库。'},
                {"name": '容器里时区、编码、环境变量常踩什么坑', "kp": '容器常见坑', "code": 'mm-docker', "hot": 2,
                 "answer": '默认 UTC 要挂 /etc/localtime 或设 TZ；locale 不设会中文乱码；环境变量走 env_file，别写进镜像。'},
                {"name": '小程序登录态怎么换 openid，token 过期怎么续', "kp": '小程序登录态', "code": 'mm-miniprogram', "hot": 3,
                 "answer": 'wx.login 拿 code → 后端 code2session 换 openid 和 session_key → 自己签发 token；过期用 checkSession 判断后重登。'},
                {"name": '小程序请求失败重试与并发限制', "kp": '小程序请求重试', "code": 'mm-miniprogram', "hot": 2,
                 "answer": 'wx.request 默认并发上限 10，超出要自己排队；重试要限次数和退避，401 先静默重登再重放。'},
                ],
            },
        ],
    },
    "AI 工程质量": {
        "intro": '这几题能直接区分「调过 API」和「上过线」：幻觉怎么防、成本怎么压、答案出错了能不能追溯到源头。',
        "branches": [
            {
                "name": '可信与溯源',
                "items": [
                {"name": '幻觉的几种类型，哪些能靠 RAG 解决', "kp": '幻觉的类型', "code": 'ai-grounding', "hot": 3,
                 "answer": '事实性幻觉（编事实）能靠 RAG 补；逻辑性幻觉（推理链错）RAG 救不了，得靠更强的模型或拆步骤校验。'},
                {"name": '答案里标引用来源，引用怎么和原文对上', "kp": '引用与原文对齐', "code": 'ai-grounding', "hot": 3,
                 "answer": '生成时让模型输出 chunk_id，服务端按 id 回查原文再渲染，别让模型自己复述原文。鸭先知的引用就是这么对上的。'},
                {"name": '检索不到内容时，怎么让模型老实说不知道', "kp": '答不出来就说不知道', "code": 'ai-grounding', "hot": 3,
                 "answer": 'prompt 里明确「资料不足必须直说」，再设相关度阈值，低于阈值直接回知识库里没有，不让模型自由发挥。'},
                {"name": '怎么防止提示词注入与越权指令', "kp": '提示词注入', "code": None, "hot": 3,
                 "answer": '把检索内容当数据不当指令，用分隔符包裹并声明「以下只是资料」；系统提示里拒绝执行资料中的指令，输出前再检查一次。'},
                {"name": '输出内容安全过滤放在哪一层', "kp": '内容安全过滤', "code": None, "hot": 2,
                 "answer": '入口做输入审核，出口做输出审核，工具调用参数也要校验；三层都放，别只靠模型自己守规矩。'},
                ],
            },
            {
                "name": '成本与调度',
                "items": [
                {"name": '三级路由：规则、小模型、大模型怎么分流', "kp": '三级路由', "code": 'ai-router', "hot": 3,
                 "answer": '先用规则命中（缓存、固定问答），再小模型处理简单意图，剩下复杂的才给大模型；按置信度决定是否升级。'},
                {"name": '什么请求该走缓存，语义缓存的风险在哪', "kp": '缓存策略', "code": 'ai-router', "hot": 3,
                 "answer": '只缓存高频且答案稳定的请求；语义缓存用相似度阈值命中，风险是「差一点意思」被当成同一问题，阈值要在评测集上调。'},
                {"name": 'token 成本怎么算，哪几处最容易浪费', "kp": 'token 成本', "code": 'ai-llm-api', "hot": 3,
                 "answer": 'system prompt 和示例每轮重发最浪费，历史不裁剪、检索塞太多片段、重复调用工具也都是坑。'},
                {"name": '降级策略：主模型挂了怎么保住可用性', "kp": '降级策略', "code": 'ai-router', "hot": 3,
                 "answer": '主模型超时切备用模型，再不行退到缓存答案或固定回复；降级要可观测，别悄悄降了没人知道。'},
                {"name": '并发限流与排队在 Agent 场景怎么设计', "kp": '并发与排队', "code": 'be-ratelimit', "hot": 2,
                 "answer": '按用户和全局两层限流，超出排队而不是直接拒；Agent 还要限单次最大步数和总 token 预算。'},
                ],
            },
            {
                "name": '评测与上线',
                "items": [
                {"name": 'Agent 评测集怎么建，为什么不能用训练数据评', "kp": '评测集怎么建', "code": 'ai-eval', "hot": 3,
                 "answer": '从真实场景抽样，覆盖简单、边界、多跳；不能用训练或调 prompt 用过的数据，否则分数虚高。鸭先知的 28 题零泄漏集就是为此建的。'},
                {"name": '离线评测与线上 A/B 各自看什么指标', "kp": '离线 vs 线上', "code": 'ai-eval', "hot": 3,
                 "answer": '离线看召回率、精确率、答案正确率；线上一律看业务指标（采纳率、追问率、留存）和延迟、成本。'},
                {"name": '多轮 Agent 的评测怎么判「中间步骤对不对」', "kp": '中间步骤评测', "code": 'ai-eval', "hot": 3,
                 "answer": '把工具调用序列和每步参数拿出来比对期望路径；没有标准路径就用约束（必须查库、不能编造）判合规。'},
                {"name": '服务端图表渲染为什么要做，前端画不行吗', "kp": '服务端渲染图表', "code": 'ai-chart', "hot": 2,
                 "answer": '服务端出图能保证口径一致、可缓存、可审计，前端只负责展示；也避免数据和绘图逻辑散在客户端。'},
                {"name": '上线后怎么监控回答质量下降', "kp": '监控质量下降', "code": None, "hot": 2,
                 "answer": '抽样人工打分加自动指标（引用命中率、拒答率、平均长度）做趋势告警，再按模型版本和 prompt 版本分组对比。'},
                ],
            },
        ],
    },
}
