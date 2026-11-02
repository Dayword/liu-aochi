"""面试知识树：每个科目一棵，按「面试考察维度」组织，而不是照抄课程阶段。

为什么不从课程结构自动生成：课程的 stage 是教学顺序（Python 基础 → 进阶 → 工程 → Agent），
面试官脑子里的结构是另一套（可变性 → 容器 → 并发 → 工程）。两套结构对不上，
自动生成出来的图只是目录换了画法，学生看不出「这题会怎么问」。

数据结构：
    MINDMAPS[科目名] = {
        "intro": 一句话说清这科在 AI Agent 面试里的定位（会怎么考），
        "branches": [
            {"name": 一级分支（考察维度）, "items": [
                {"name": 面试知识点的具体表述, "code": 对应课程 code 或 None, "hot": 1|2|3},
            ]},
        ],
    }

hot 的口径：
    3 = 几乎每轮面试都会问，答不上来直接减分
    2 = 常问，答得好是加分项
    1 = 知道就行，属于纵深问题

code 的口径：
    指向 `seed/learn_*.py` 里的课程 code，前端点一下能跳过去学；
    写 None 表示「面试会问、但站内还没对应课程」，图上标成待补，不假装有。
    这个字段不是装饰：它让这张图能反过来暴露课程空缺，补课时按图补。
"""

MINDMAPS: dict[str, dict] = {
    # ==================================================================
    # Python —— 50 课，全站最大的一科，10 个考察维度
    # ==================================================================
    "Python": {
        "intro": "面试基本不考语法，考的是「底层到底懂不懂」：可变性、容器复杂度、并发模型、"
        "以及能不能用装饰器/上下文管理器写出干净的工程代码。",
        "branches": [
            {
                "name": "可变性与内存模型",
                "items": [
                    {"name": "可变对象与不可变对象差在哪，改 str 为什么等于新建", "code": "py-type", "hot": 3},
                    {"name": "深拷贝与浅拷贝：嵌套列表拷贝后改内层会怎样", "code": "py-scope", "hot": 3},
                    {"name": "函数默认参数写成 [] 或 {} 会踩什么坑", "code": "py-scope", "hot": 3},
                    {"name": "is 与 == 的区别，小整数缓存和字符串驻留", "code": "py-none", "hot": 3},
                    {"name": "Python 传参是值传递还是引用传递", "code": "py-scope", "hot": 2},
                    {"name": "可变对象为什么不能当 dict 的 key", "code": "py-dict", "hot": 2},
                    {"name": "循环引用与垃圾回收的分代策略", "code": None, "hot": 1},
                ],
            },
            {
                "name": "容器选型与底层实现",
                "items": [
                    {"name": "list 的 in 为什么是 O(n)，该换成什么结构", "code": "py-list", "hot": 3},
                    {"name": "dict 的哈希表实现，查找为什么平均 O(1)", "code": "py-dict", "hot": 3},
                    {"name": "list 与 tuple 的差别，tuple 凭什么能当 key", "code": "py-tuple-set", "hot": 3},
                    {"name": "dict 从 3.7 起保证插入有序，底层怎么做到的", "code": "py-dict", "hot": 2},
                    {"name": "set 去重与交并差的典型用法", "code": "py-tuple-set", "hot": 2},
                    {"name": "列表推导式与生成器表达式什么时候该用哪个", "code": "py-comprehension", "hot": 3},
                    {"name": "Counter / defaultdict / deque 各解决什么问题", "code": "py-stdlib", "hot": 2},
                ],
            },
            {
                "name": "迭代器与生成器",
                "items": [
                    {"name": "可迭代对象和迭代器的区别，__iter__ 与 __next__", "code": "py-generator", "hot": 3},
                    {"name": "yield 到底暂停了什么，为什么适合流式处理", "code": "py-generator", "hot": 3},
                    {"name": "生成器只能遍历一次，线上踩过什么坑", "code": "py-generator", "hot": 3},
                    {"name": "用生成器读大文件不爆内存怎么写", "code": "py-file", "hot": 2},
                    {"name": "边遍历边删列表会发生什么", "code": "py-list", "hot": 2},
                    {"name": "enumerate / zip / map / filter 的返回值差异", "code": "py-iterate", "hot": 2},
                ],
            },
            {
                "name": "函数、闭包与装饰器",
                "items": [
                    {"name": "闭包怎么捕获变量，循环里的 lambda 为什么全是最后一个值", "code": "py-scope", "hot": 3},
                    {"name": "装饰器怎么写，带参数的装饰器为什么多两层函数", "code": "py-decorator", "hot": 3},
                    {"name": "functools.wraps 不加会丢掉什么", "code": "py-decorator", "hot": 2},
                    {"name": "*args 与 **kwargs 的打包和解包过程", "code": "py-func-adv", "hot": 2},
                    {"name": "sorted 的 key 用 lambda 怎么写多字段排序", "code": "py-lambda", "hot": 2},
                    {"name": "partial 偏函数解决什么问题", "code": "py-stdlib", "hot": 1},
                    {"name": "描述符协议 __get__ / __set__ 是哪些框架的底座", "code": None, "hot": 1},
                    {"name": "元类 metaclass 到底能干什么", "code": None, "hot": 1},
                ],
            },
            {
                "name": "面向对象与接口契约",
                "items": [
                    {"name": "继承的 MRO 查找顺序，super() 在多继承里怎么走", "code": "py-oop", "hot": 3},
                    {"name": "Python 的多态靠什么实现，什么是鸭子类型", "code": "py-oop", "hot": 3},
                    {"name": "抽象基类 ABC 与 Protocol 的差别，什么时候用哪个", "code": "py-abc", "hot": 3},
                    {"name": "dataclass 与普通类、NamedTuple 怎么选", "code": "eng-typing", "hot": 3},
                    {"name": "__init__ 与 __new__ 的区别", "code": "py-magic", "hot": 2},
                    {"name": "@property 与直接暴露属性比好在哪", "code": "py-magic", "hot": 2},
                    {"name": "__slots__ 省内存的原理和副作用", "code": "py-magic", "hot": 1},
                ],
            },
            {
                "name": "并发模型与异步",
                "items": [
                    {"name": "GIL 到底是什么，为什么多线程跑不满多核", "code": "py-concurrency", "hot": 3},
                    {"name": "IO 密集、CPU 密集分别该用线程、进程还是协程", "code": "py-concurrency", "hot": 3},
                    {"name": "asyncio 事件循环怎么跑起来，await 为什么不会阻塞", "code": "eng-async", "hot": 3},
                    {"name": "用 asyncio.gather 并发调多个模型接口怎么写", "code": "eng-async", "hot": 3},
                    {"name": "同步库在 async 函数里把事件循环堵死了怎么救", "code": "eng-async", "hot": 2},
                    {"name": "有 GIL 是不是就不用加锁了", "code": "py-concurrency", "hot": 2},
                    {"name": "进程间通信有哪些方式，进程池开销在哪", "code": "py-concurrency", "hot": 2},
                    {"name": "Python 3.13 free-threading 移除 GIL 的进展", "code": None, "hot": 1},
                ],
            },
            {
                "name": "异常、上下文与资源管理",
                "items": [
                    {"name": "try / except / else / finally 的执行顺序", "code": "py-exception", "hot": 3},
                    {"name": "该捕获 Exception 还是裸 except，为什么", "code": "py-exception", "hot": 3},
                    {"name": "with 背后是 __enter__ 和 __exit__，异常怎么传进去", "code": "py-context", "hot": 3},
                    {"name": "自定义异常体系怎么设计，raise from 有什么用", "code": "py-exception", "hot": 2},
                    {"name": "用 @contextmanager 写上下文管理器", "code": "py-context", "hot": 2},
                    {"name": "文件读写的编码问题，newline 影响什么", "code": "py-file", "hot": 2},
                    {"name": "路径处理为什么用 pathlib 而不是字符串拼接", "code": "py-file", "hot": 1},
                ],
            },
            {
                "name": "类型注解与数据校验",
                "items": [
                    {"name": "类型注解运行时会被检查吗，mypy 在哪个阶段生效", "code": "eng-typing", "hot": 3},
                    {"name": "Pydantic 怎么做校验、类型转换和默认值", "code": "eng-pydantic", "hot": 3},
                    {"name": "接 LLM 结构化输出时 Pydantic 模型怎么落", "code": "ai-structured", "hot": 3},
                    {"name": "Optional / Union / | 的写法演变", "code": "eng-typing", "hot": 2},
                    {"name": "dataclass 的 field 与 default_factory 怎么用", "code": "eng-typing", "hot": 2},
                    {"name": "Pydantic v1 与 v2 的 validator 写法差异", "code": "eng-pydantic", "hot": 2},
                ],
            },
            {
                "name": "工程化与可观测",
                "items": [
                    {"name": "logging 的级别、handler、formatter 怎么组织", "code": "eng-log", "hot": 3},
                    {"name": "密钥为什么不能进代码，怎么用环境变量管", "code": "eng-env", "hot": 3},
                    {"name": "pytest 的 fixture 与参数化怎么写", "code": "eng-test", "hot": 3},
                    {"name": "怎么 mock 掉外部模型调用做单测", "code": "eng-test", "hot": 2},
                    {"name": "requirements 锁版本与依赖冲突怎么处理", "code": "eng-deps", "hot": 2},
                    {"name": "ruff / black / mypy 各管什么，能替代 code review 吗", "code": "eng-quality", "hot": 2},
                    {"name": "项目目录怎么分层，为什么不能所有代码堆根目录", "code": "eng-deps", "hot": 1},
                ],
            },
            {
                "name": "文本处理与外部调用",
                "items": [
                    {"name": "正则贪婪与非贪婪，分组和命名分组怎么写", "code": "py-regex", "hot": 3},
                    {"name": "requests 的超时、重试、连接池怎么配", "code": "eng-http", "hot": 3},
                    {"name": "SSE 流式响应怎么逐行解析", "code": "ai-stream", "hot": 3},
                    {"name": "JSON 序列化中文字符、datetime、Decimal 怎么处理", "code": "eng-json", "hot": 2},
                    {"name": "re.sub 做文本清洗的典型模式", "code": "py-regex", "hot": 2},
                ],
            },
            {
                "name": "Agent 应用开发",
                "items": [
                    {"name": "messages 里 system / user / assistant / tool 各自的作用", "code": "ai-llm-api", "hot": 3},
                    {"name": "temperature、top_p、max_tokens 怎么配才稳定", "code": "ai-llm-api", "hot": 3},
                    {"name": "Prompt 的结构化写法：角色、任务、约束、示例怎么排", "code": "ai-prompt", "hot": 3},
                    {"name": "Few-shot 什么时候有效，什么时候反而是负担", "code": "ai-prompt", "hot": 2},
                    {"name": "怎么保证模型输出一定是可解析的 JSON", "code": "ai-structured", "hot": 3},
                    {"name": "Function Calling 的完整流程，结果怎么回传给模型", "code": "ai-tools", "hot": 3},
                    {"name": "工具描述怎么写才不会被误调用或漏调用", "code": "ai-tools", "hot": 3},
                    {"name": "ReAct 循环：Thought / Action / Observation 怎么串", "code": "ai-agent-loop", "hot": 3},
                    {"name": "Agent 循环靠什么终止，死循环怎么防和兜底", "code": "ai-agent-loop", "hot": 3},
                    {"name": "流式输出与工具调用能同时做吗，冲突在哪", "code": "ai-stream", "hot": 3},
                    {"name": "多轮记忆的四种策略：全量、滑窗、摘要、向量召回", "code": "ai-memory", "hot": 3},
                    {"name": "上下文超长怎么裁剪，裁掉什么会直接答错", "code": "ai-memory", "hot": 3},
                    {"name": "RAG 的基本链路：索引 → 检索 → 拼上下文 → 生成", "code": "ai-rag", "hot": 3},
                    {"name": "MCP 协议解决什么问题，和直接写函数调用差在哪", "code": None, "hot": 3},
                    {"name": "多 Agent 编排：串行、并行、主管-工人怎么选", "code": "ai-multiagent", "hot": 3},
                    {"name": "什么时候不该上多 Agent（成本和可控性代价）", "code": "ai-multiagent", "hot": 3},
                    {"name": "Agent 之间怎么传状态，某一步失败怎么回滚", "code": "ai-multiagent", "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # MySQL —— 10 课，面试集中在索引、事务、优化三块
    # ==================================================================
    "MySQL": {
        "intro": "AI Agent 岗问 MySQL 不会考建表语法，几乎只问三件事："
        "索引为什么这么建、这条 SQL 为什么慢、事务和锁在并发下会怎样。",
        "branches": [
            {
                "name": "索引原理",
                "items": [
                    {"name": "为什么用 B+ 树而不是 B 树、红黑树、哈希表", "code": "mysql-07", "hot": 3},
                    {"name": "聚簇索引与二级索引，回表是什么", "code": "mysql-07", "hot": 3},
                    {"name": "最左前缀原则，联合索引 (a,b,c) 能命中哪些查询", "code": "mysql-08", "hot": 3},
                    {"name": "覆盖索引为什么能避免回表", "code": "mysql-07", "hot": 3},
                    {"name": "索引下推 ICP 解决什么问题", "code": "mysql-08", "hot": 2},
                    {"name": "一张表建多少个索引合适，索引的代价在哪", "code": "mysql-08", "hot": 2},
                ],
            },
            {
                "name": "索引失效与执行计划",
                "items": [
                    {"name": "EXPLAIN 的 type 字段从好到坏怎么排", "code": "mysql-08", "hot": 3},
                    {"name": "对索引列做函数、运算、隐式转换为什么失效", "code": "mysql-08", "hot": 3},
                    {"name": "like '%xx' 为什么用不上索引，怎么优化", "code": "mysql-08", "hot": 3},
                    {"name": "or 条件里有一个没索引会怎样", "code": "mysql-08", "hot": 2},
                    {"name": "Extra 里的 Using filesort、Using temporary 意味着什么", "code": "mysql-08", "hot": 2},
                ],
            },
            {
                "name": "事务、锁与并发",
                "items": [
                    {"name": "ACID 分别靠什么机制保证", "code": "mysql-09", "hot": 3},
                    {"name": "MVCC 怎么实现，undo log 和 Read View 各干什么", "code": "mysql-09", "hot": 3},
                    {"name": "四种隔离级别，幻读在 RR 下怎么被解决", "code": "mysql-10", "hot": 3},
                    {"name": "间隙锁和临键锁什么时候加，为什么容易死锁", "code": "mysql-10", "hot": 3},
                    {"name": "快照读与当前读的区别，for update 加什么锁", "code": "mysql-09", "hot": 2},
                    {"name": "redo log / binlog / undo log 各管什么，两阶段提交", "code": "mysql-10", "hot": 3},
                ],
            },
            {
                "name": "SQL 写法与优化实战",
                "items": [
                    {"name": "NULL 的比较陷阱：为什么 = NULL 查不出东西", "code": "mysql-02", "hot": 3},
                    {"name": "深分页 limit 100000,20 为什么慢，怎么改", "code": "mysql-03", "hot": 3},
                    {"name": "count(*)、count(1)、count(字段) 谁快", "code": "mysql-04", "hot": 3},
                    {"name": "group by 与 having 的执行顺序", "code": "mysql-04", "hot": 2},
                    {"name": "inner join 与 left join 的驱动表怎么选", "code": "mysql-05", "hot": 3},
                    {"name": "子查询什么时候会被改写成 join", "code": "mysql-06", "hot": 2},
                    {"name": "大表加字段、改字段类型怎么做到不锁表", "code": None, "hot": 2},
                ],
            },
            {
                "name": "表设计与数据类型",
                "items": [
                    {"name": "主键用自增 ID 还是 UUID，各有什么代价", "code": "mysql-01", "hot": 3},
                    {"name": "varchar 与 char、text 怎么选", "code": "mysql-01", "hot": 2},
                    {"name": "金额为什么不用 float，该用什么类型", "code": "mysql-01", "hot": 3},
                    {"name": "为什么建议每张表都有 create_time / update_time", "code": "mysql-10", "hot": 2},
                    {"name": "范式与反范式，什么时候故意冗余", "code": "mysql-10", "hot": 2},
                    {"name": "分库分表什么时候才该做，先做什么", "code": None, "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # Redis —— 8 课，缓存 + 锁 + 高可用三块
    # ==================================================================
    "Redis": {
        "intro": "问 Redis 的真实意图是「你会不会用缓存扛流量」："
        "三大缓存问题怎么防、分布式锁怎么保证不误删、主从切换会不会丢数据。",
        "branches": [
            {
                "name": "数据类型与底层结构",
                "items": [
                    {"name": "Redis 单线程为什么还这么快", "code": "redis-01", "hot": 3},
                    {"name": "五种基本类型分别对应什么业务场景", "code": "redis-01", "hot": 3},
                    {"name": "String 的 SDS 相比 C 字符串改了什么", "code": "redis-02", "hot": 2},
                    {"name": "ZSet 的底层跳表 + 哈希表，为什么不用红黑树", "code": "redis-04", "hot": 3},
                    {"name": "用 String 做计数器与分布式 ID 的写法", "code": "redis-02", "hot": 2},
                    {"name": "List 做队列与 Hash 存对象，各自的问题", "code": "redis-03", "hot": 2},
                    {"name": "ZSet 实现排行榜：分数相同怎么稳定排序", "code": "redis-04", "hot": 2},
                    {"name": "Redis 6 的多线程 IO 到底多线程在哪", "code": None, "hot": 2},
                ],
            },
            {
                "name": "持久化与内存管理",
                "items": [
                    {"name": "RDB 与 AOF 各自的写入时机与丢失窗口", "code": "redis-06", "hot": 3},
                    {"name": "AOF 重写解决什么问题，fsync 三种策略怎么选", "code": "redis-06", "hot": 3},
                    {"name": "混合持久化为什么成了默认推荐", "code": "redis-06", "hot": 2},
                    {"name": "过期删除策略：惰性删除 + 定期删除怎么配合", "code": "redis-05", "hot": 3},
                    {"name": "八种内存淘汰策略，allkeys-lru 与 volatile-lru 差在哪", "code": "redis-05", "hot": 3},
                    {"name": "内存碎片和大 key 怎么排查处理", "code": "redis-05", "hot": 2},
                ],
            },
            {
                "name": "缓存三大问题",
                "items": [
                    {"name": "缓存穿透：布隆过滤器与空值缓存怎么选", "code": "redis-07", "hot": 3},
                    {"name": "缓存击穿：互斥重建与逻辑过期两种方案", "code": "redis-07", "hot": 3},
                    {"name": "缓存雪崩：过期时间打散与多级缓存", "code": "redis-07", "hot": 3},
                    {"name": "先删缓存还是先更新库，为什么都会不一致", "code": "redis-07", "hot": 3},
                    {"name": "延迟双删、订阅 binlog 各自能解决到什么程度", "code": "redis-07", "hot": 2},
                    {"name": "热 key 怎么发现、怎么拆", "code": None, "hot": 2},
                ],
            },
            {
                "name": "分布式锁",
                "items": [
                    {"name": "SET NX EX 加锁为什么必须带过期时间", "code": "redis-08", "hot": 3},
                    {"name": "锁的 value 为什么要用唯一标识，删锁为什么要原子", "code": "redis-08", "hot": 3},
                    {"name": "业务没跑完锁过期了怎么办，看门狗续期", "code": "redis-08", "hot": 3},
                    {"name": "主从切换导致锁丢失，Redlock 能不能救", "code": "redis-08", "hot": 2},
                    {"name": "Redisson 的可重入锁怎么实现", "code": None, "hot": 2},
                ],
            },
            {
                "name": "高可用与集群",
                "items": [
                    {"name": "主从复制全量同步与增量同步的过程", "code": "redis-08", "hot": 3},
                    {"name": "哨兵怎么判断主观下线与客观下线，选举流程", "code": "redis-08", "hot": 3},
                    {"name": "Cluster 的 16384 个槽与 MOVED / ASK 重定向", "code": "redis-08", "hot": 2},
                    {"name": "缓存与数据库双写时如何兜底重建", "code": "redis-07", "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # 计算机网络 —— 10 课，握手挥手 + HTTP + HTTPS 是三大必考
    # ==================================================================
    "计算机网络": {
        "intro": "最高频的一道题是「输入 URL 到页面展示发生了什么」，它能把 DNS、TCP、HTTP、"
        "TLS 全串起来。答得出细节就说明网络不是背的。",
        "branches": [
            {
                "name": "TCP 连接管理",
                "items": [
                    {"name": "三次握手每一步交换了什么，为什么不能是两次", "code": "net-02", "hot": 3},
                    {"name": "SYN Flood 攻击原理，半连接队列怎么被打满", "code": "net-02", "hot": 3},
                    {"name": "四次挥手为什么比握手多一次，CLOSE_WAIT 是谁的问题", "code": "net-03", "hot": 3},
                    {"name": "TIME_WAIT 为什么要等 2MSL，太多怎么优化", "code": "net-03", "hot": 3},
                    {"name": "服务端出现大量 TIME_WAIT / CLOSE_WAIT 分别怎么查", "code": "net-03", "hot": 2},
                ],
            },
            {
                "name": "TCP 可靠性与拥塞控制",
                "items": [
                    {"name": "序号、确认号、超时重传怎么保证不丢", "code": "net-04", "hot": 3},
                    {"name": "滑动窗口与流量控制的区别", "code": "net-04", "hot": 3},
                    {"name": "慢启动、拥塞避免、快重传、快恢复四个阶段", "code": "net-05", "hot": 3},
                    {"name": "Nagle 算法与延迟确认为什么会凑出 40ms 延迟", "code": "net-05", "hot": 2},
                    {"name": "UDP 与 TCP 怎么选，为什么音视频用 UDP", "code": "net-06", "hot": 3},
                    {"name": "QUIC 在 UDP 上补了 TCP 的哪些短板", "code": "net-08", "hot": 2},
                ],
            },
            {
                "name": "HTTP 协议与演进",
                "items": [
                    {"name": "常见状态码：301 / 302 / 304 / 401 / 403 / 502 / 504", "code": "net-07", "hot": 3},
                    {"name": "GET 与 POST 的本质区别（不是长度）", "code": "net-07", "hot": 3},
                    {"name": "HTTP/1.1 的队头阻塞与 keep-alive", "code": "net-08", "hot": 3},
                    {"name": "HTTP/2 多路复用、二进制分帧、头部压缩", "code": "net-08", "hot": 3},
                    {"name": "HTTP/3 为什么基于 QUIC，解决了什么问题", "code": "net-08", "hot": 2},
                    {"name": "Cookie、Session、Token 三者的关系", "code": "net-07", "hot": 3},
                    {"name": "跨域是什么，CORS 预检请求什么时候触发", "code": "net-07", "hot": 3},
                ],
            },
            {
                "name": "HTTPS 与 TLS",
                "items": [
                    {"name": "对称加密与非对称加密为什么要混合使用", "code": "net-09", "hot": 3},
                    {"name": "TLS 1.2 握手完整流程，几个 RTT", "code": "net-09", "hot": 3},
                    {"name": "证书链怎么校验，中间人为什么伪造不了", "code": "net-09", "hot": 3},
                    {"name": "TLS 1.3 把握手压缩到 1-RTT 做了什么", "code": "net-09", "hot": 2},
                    {"name": "会话复用 Session ID 与 Session Ticket", "code": "net-09", "hot": 1},
                ],
            },
            {
                "name": "DNS 与请求全链路",
                "items": [
                    {"name": "从输入 URL 到页面展示，完整按顺序讲一遍", "code": "net-10", "hot": 3},
                    {"name": "DNS 递归查询与迭代查询的过程", "code": "net-10", "hot": 3},
                    {"name": "DNS 缓存层级，改了解析为什么没立刻生效", "code": "net-10", "hot": 2},
                    {"name": "CDN 是怎么靠 DNS 调度到最近节点的", "code": "net-10", "hot": 2},
                    {"name": "OSI 七层与 TCP/IP 四层的对应关系", "code": "net-01", "hot": 2},
                    {"name": "一次请求慢，从哪几层开始排查", "code": None, "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # 数据结构 —— 10 课，复杂度 + 手写 + 选型三块
    # ==================================================================
    "数据结构": {
        "intro": "校招会考手写和复杂度推导，社招更考「这个场景你选什么结构、为什么」。"
        "AI Agent 岗特别容易被问：向量检索为什么用 HNSW 而不是暴力扫。",
        "branches": [
            {
                "name": "复杂度分析",
                "items": [
                    {"name": "大 O 怎么推：只看最高阶、忽略常数", "code": "ds-01", "hot": 3},
                    {"name": "最好、最坏、平均、均摊复杂度的区别", "code": "ds-01", "hot": 3},
                    {"name": "空间复杂度怎么算，递归的栈深度算不算", "code": "ds-01", "hot": 2},
                    {"name": "为什么 O(n log n) 是 comparison sort 的下界", "code": "ds-08", "hot": 2},
                ],
            },
            {
                "name": "线性结构",
                "items": [
                    {"name": "数组与链表：随机访问、插入删除、缓存友好性", "code": "ds-02", "hot": 3},
                    {"name": "用两个栈实现队列，用两个队列实现栈", "code": "ds-03", "hot": 3},
                    {"name": "哈希表冲突解决：链地址法与开放寻址", "code": "ds-04", "hot": 3},
                    {"name": "哈希表扩容为什么触发 rehash，负载因子取多少", "code": "ds-04", "hot": 2},
                    {"name": "单调栈能解决哪类问题（下一个更大元素）", "code": "ds-03", "hot": 2},
                    {"name": "LRU 缓存怎么用哈希表 + 双向链表实现", "code": "ds-04", "hot": 3},
                ],
            },
            {
                "name": "树与堆",
                "items": [
                    {"name": "二叉树前中后序与层序遍历，递归和迭代都要会", "code": "ds-05", "hot": 3},
                    {"name": "二叉搜索树的查找、插入、删除，退化情况", "code": "ds-06", "hot": 3},
                    {"name": "AVL 与红黑树怎么选，为什么工程里多用红黑树", "code": "ds-06", "hot": 2},
                    {"name": "堆的建堆为什么是 O(n) 而不是 O(n log n)", "code": "ds-07", "hot": 3},
                    {"name": "求 Top K 用堆还是快排，各自复杂度", "code": "ds-07", "hot": 3},
                    {"name": "B 树与 B+ 树为磁盘做的优化是什么", "code": None, "hot": 3},
                    {"name": "Trie 树在前缀匹配与分词里的用法", "code": None, "hot": 2},
                ],
            },
            {
                "name": "排序与查找",
                "items": [
                    {"name": "快排的分区怎么写，最坏 O(n²) 怎么避免", "code": "ds-08", "hot": 3},
                    {"name": "归并排序的稳定性从哪来，用在什么场景", "code": "ds-08", "hot": 3},
                    {"name": "各排序的稳定性、复杂度、适用场景对比表", "code": "ds-08", "hot": 3},
                    {"name": "二分查找的边界：找第一个、找最后一个、找插入位置", "code": "ds-09", "hot": 3},
                    {"name": "二分答案类题目怎么建模", "code": "ds-09", "hot": 2},
                    {"name": "海量数据求中位数怎么用两个堆", "code": None, "hot": 2},
                ],
            },
            {
                "name": "图与检索结构",
                "items": [
                    {"name": "邻接矩阵与邻接表怎么选", "code": "ds-10", "hot": 3},
                    {"name": "BFS 求最短路、DFS 求连通分量", "code": "ds-10", "hot": 3},
                    {"name": "拓扑排序判环，和课程表问题", "code": "ds-10", "hot": 3},
                    {"name": "Dijkstra 与 A* 的区别，A* 的启发函数要求", "code": "ds-10", "hot": 2},
                    {"name": "向量检索为什么用 HNSW，暴力扫描差在哪", "code": "rag-vector-db", "hot": 3},
                    {"name": "倒排索引的结构，BM25 为什么比 TF-IDF 好", "code": "rag-bm25", "hot": 3},
                ],
            },
        ],
    },

    # ==================================================================
    # 操作系统 —— 9 课，进程线程 + 内存 + IO 是三大块
    # ==================================================================
    "操作系统": {
        "intro": "后端岗的底层筛查：进程线程协程的区别、IO 多路复用、虚拟内存。"
        "答得清 epoll 和 select 的差别，基本就过线了。",
        "branches": [
            {
                "name": "进程与线程",
                "items": [
                    {"name": "进程和线程的本质区别，切换开销差在哪", "code": "os-01", "hot": 3},
                    {"name": "协程与线程的区别，为什么协程是用户态调度", "code": "os-01", "hot": 3},
                    {"name": "进程状态转换：就绪、运行、阻塞怎么流转", "code": "os-02", "hot": 3},
                    {"name": "常见调度算法：时间片轮转、优先级、多级反馈队列", "code": "os-02", "hot": 2},
                    {"name": "进程间通信有哪些方式，各自适合什么数据量", "code": "os-03", "hot": 3},
                    {"name": "管道、消息队列、共享内存、信号量怎么选", "code": "os-03", "hot": 2},
                    {"name": "线程之间共享什么、独享什么", "code": "os-01", "hot": 3},
                ],
            },
            {
                "name": "死锁与同步",
                "items": [
                    {"name": "死锁的四个必要条件，打破任意一个就行吗", "code": "os-04", "hot": 3},
                    {"name": "互斥锁、读写锁、自旋锁、信号量的使用场景", "code": "os-04", "hot": 3},
                    {"name": "银行家算法与死锁检测的实际价值", "code": "os-04", "hot": 1},
                    {"name": "线上服务卡死怎么判断是不是死锁", "code": None, "hot": 2},
                ],
            },
            {
                "name": "内存管理",
                "items": [
                    {"name": "分页与分段的区别，段页式怎么组合", "code": "os-05", "hot": 3},
                    {"name": "虚拟内存解决什么问题，页表怎么映射", "code": "os-06", "hot": 3},
                    {"name": "多级页表与 TLB 为什么必须有", "code": "os-06", "hot": 3},
                    {"name": "页面置换算法：FIFO、LRU、Clock、LFU", "code": "os-06", "hot": 3},
                    {"name": "缺页中断的完整处理流程", "code": "os-06", "hot": 2},
                    {"name": "内存泄漏与 OOM 在 Linux 上怎么定位", "code": None, "hot": 2},
                ],
            },
            {
                "name": "文件系统与 IO",
                "items": [
                    {"name": "inode 里存了什么，文件名为什么不放在 inode 里", "code": "os-07", "hot": 3},
                    {"name": "硬链接与软链接的区别", "code": "os-07", "hot": 3},
                    {"name": "五种 IO 模型：阻塞、非阻塞、多路复用、信号驱动、异步", "code": "os-08", "hot": 3},
                    {"name": "select、poll、epoll 的区别，epoll 为什么高效", "code": "os-08", "hot": 3},
                    {"name": "水平触发与边缘触发的差别，写错会怎样", "code": "os-08", "hot": 3},
                    {"name": "零拷贝 sendfile 省掉了哪几次拷贝", "code": "os-08", "hot": 2},
                    {"name": "页缓存与直接 IO，数据库为什么要绕过页缓存", "code": "os-07", "hot": 2},
                ],
            },
            {
                "name": "Linux 排障实操",
                "items": [
                    {"name": "top / ps 看 CPU 和内存，load average 高说明什么", "code": "os-09", "hot": 3},
                    {"name": "df 与 du 的区别，磁盘满了怎么快速定位", "code": "os-09", "hot": 3},
                    {"name": "netstat / ss 查端口占用与连接状态", "code": "os-09", "hot": 3},
                    {"name": "lsof 与 strace 分别用来查什么", "code": "os-09", "hot": 2},
                    {"name": "服务起不来，按什么顺序排查", "code": "os-09", "hot": 3},
                ],
            },
        ],
    },

    # ==================================================================
    # 数据分析与处理 —— 8 课，NumPy/Pandas 的坑 + 分析结论
    # ==================================================================
    "数据分析与处理": {
        "intro": "AI 岗考这块不是考你会不会画图，是考「脏数据交给你能不能收敛成结论」，"
        "以及 Pandas 里那几个经典的坑（链式赋值、SettingWithCopy、groupby 的索引）。",
        "branches": [
            {
                "name": "NumPy 与向量化",
                "items": [
                    {"name": "ndarray 与 list 的性能差从哪来", "code": "da-01", "hot": 3},
                    {"name": "广播机制的规则，形状不匹配怎么补", "code": "da-01", "hot": 3},
                    {"name": "视图与副本：切片赋值会不会改原数组", "code": "da-01", "hot": 3},
                    {"name": "花式索引、布尔索引、np.where 的用法", "code": "da-01", "hot": 2},
                    {"name": "为什么循环里逐元素算比向量化慢两个数量级", "code": "da-01", "hot": 2},
                ],
            },
            {
                "name": "Pandas 核心操作",
                "items": [
                    {"name": "Series 与 DataFrame 的索引对齐机制", "code": "da-02", "hot": 3},
                    {"name": "loc、iloc、at、iat 的区别，什么时候用哪个", "code": "da-02", "hot": 3},
                    {"name": "SettingWithCopyWarning 到底在警告什么", "code": "da-02", "hot": 3},
                    {"name": "apply 与 map 与 vectorized 操作怎么选", "code": "da-05", "hot": 2},
                    {"name": "merge 的四种连接方式与索引重置", "code": "da-06", "hot": 3},
                    {"name": "pivot_table、melt、stack/unstack 的转换关系", "code": "da-06", "hot": 2},
                ],
            },
            {
                "name": "脏数据处理",
                "items": [
                    {"name": "读 CSV 时编码、分隔符、列类型错乱怎么处理", "code": "da-03", "hot": 3},
                    {"name": "缺失值该删、该填还是该标记，判断依据是什么", "code": "da-04", "hot": 3},
                    {"name": "重复值判定为什么不能只按主键", "code": "da-04", "hot": 2},
                    {"name": "异常值用 3σ 还是 IQR，业务上要不要保留", "code": "da-04", "hot": 3},
                    {"name": "时间字段解析、时区与重采样", "code": "da-07", "hot": 2},
                    {"name": "groupby 之后索引变成多层怎么拍平", "code": "da-05", "hot": 2},
                ],
            },
            {
                "name": "分析与结论产出",
                "items": [
                    {"name": "拿到一份陌生数据，先看哪几个指标", "code": "da-03", "hot": 3},
                    {"name": "相关性不等于因果，怎么避免下错结论", "code": "da-08", "hot": 3},
                    {"name": "图表选型：趋势、对比、分布、占比各用什么图", "code": "da-08", "hot": 2},
                    {"name": "分析报告怎么组织才让人看得懂结论", "code": "da-08", "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # Transformer —— 8 课，AI 岗的技术底座，几乎必考
    # ==================================================================
    "Transformer": {
        "intro": "AI Agent 岗必考，但深度有差别：应用岗要能讲清注意力怎么算、"
        "为什么除 √d、KV Cache 省了什么；算法岗还会问位置编码外推和 FlashAttention。",
        "branches": [
            {
                "name": "注意力机制",
                "items": [
                    {"name": "RNN 的序列依赖问题，Attention 怎么解决", "code": "tf-01", "hot": 3},
                    {"name": "Q/K/V 分别是什么，为什么叫 Query 和 Key", "code": "tf-02", "hot": 3},
                    {"name": "Self-Attention 的计算公式，矩阵维度怎么变", "code": "tf-02", "hot": 3},
                    {"name": "为什么除以 √d_k，不除会怎样", "code": "tf-03", "hot": 3},
                    {"name": "Softmax 的数值稳定性，为什么要减最大值", "code": "tf-03", "hot": 2},
                    {"name": "注意力的复杂度 O(n²d)，长文本怎么缓解", "code": "tf-03", "hot": 3},
                ],
            },
            {
                "name": "模型结构",
                "items": [
                    {"name": "多头注意力为什么要拆成多个头", "code": "tf-04", "hot": 3},
                    {"name": "多头之间怎么拼接，参数量和单头比差多少", "code": "tf-04", "hot": 2},
                    {"name": "位置编码为什么必需，正弦编码与可学习编码的区别", "code": "tf-05", "hot": 3},
                    {"name": "RoPE 相对位置编码的原理，为什么成了主流", "code": "tf-05", "hot": 3},
                    {"name": "残差连接与 LayerNorm 各解决什么问题", "code": "tf-06", "hot": 3},
                    {"name": "Pre-LN 与 Post-LN 的差别，训练稳定性", "code": "tf-06", "hot": 2},
                    {"name": "Encoder-Decoder、Decoder-only、Encoder-only 怎么选", "code": "tf-06", "hot": 3},
                ],
            },
            {
                "name": "预训练与模型选型",
                "items": [
                    {"name": "BERT 与 GPT 的架构和训练目标差异", "code": "tf-07", "hot": 3},
                    {"name": "MLM、CLM、Seq2Seq 三种预训练目标", "code": "tf-07", "hot": 3},
                    {"name": "为什么现在大模型几乎都是 Decoder-only", "code": "tf-07", "hot": 3},
                    {"name": "参数量、上下文长度、词表大小怎么权衡", "code": "tf-07", "hot": 2},
                    {"name": "Embedding 模型和生成模型能混用吗", "code": "rag-embedding", "hot": 2},
                ],
            },
            {
                "name": "推理与加速",
                "items": [
                    {"name": "KV Cache 缓存了什么，为什么能省算力", "code": "tf-08", "hot": 3},
                    {"name": "KV Cache 显存怎么估算，长上下文为什么爆显存", "code": "tf-08", "hot": 3},
                    {"name": "prefill 与 decode 两阶段的瓶颈差异", "code": "tf-08", "hot": 3},
                    {"name": "量化 INT8 / INT4 损失在哪，什么场景能用", "code": None, "hot": 2},
                    {"name": "投机采样、PagedAttention 各自优化什么", "code": None, "hot": 2},
                    {"name": "温度、top_p、top_k 采样参数怎么影响输出", "code": "ai-llm-api", "hot": 3},
                ],
            },
        ],
    },

    # ==================================================================
    # RAG 检索工程 —— 9 课，AI Agent 岗最核心的一科，问得最细
    # ==================================================================
    "RAG 检索工程": {
        "intro": "这是 AI Agent 岗区分度最高的一科。面试官会从一个具体故障切入："
        "「检索结果不对，你怎么定位是分块、召回还是精排的问题」，答得出链路就赢了。",
        "branches": [
            {
                "name": "分块与预处理",
                "items": [
                    {"name": "固定长度切分为什么不能直接用，标题层级切分好在哪", "code": "rag-chunk", "hot": 3},
                    {"name": "chunk size 和 overlap 怎么定，多大会丢语义", "code": "rag-chunk", "hot": 3},
                    {"name": "表格、代码块、公式怎么单独处理", "code": "rag-chunk", "hot": 2},
                    {"name": "中文分词为什么不能只用空格，jieba 自定义词典解决什么", "code": "rag-tokenize", "hot": 3},
                    {"name": "分块粒度与召回粒度的矛盾，parent-child 检索", "code": None, "hot": 3},
                    {"name": "PDF 解析出来的文本乱序怎么修", "code": "mm-ocr", "hot": 2},
                ],
            },
            {
                "name": "检索算法",
                "items": [
                    {"name": "BM25 的打分公式，k1 和 b 各控制什么", "code": "rag-bm25", "hot": 3},
                    {"name": "稀疏检索与稠密检索各自的强项和盲区", "code": "rag-hybrid", "hot": 3},
                    {"name": "为什么必须做混合检索，什么 query 只有 BM25 能救", "code": "rag-hybrid", "hot": 3},
                    {"name": "Embedding 模型的选型依据，维度越高越好吗", "code": "rag-embedding", "hot": 3},
                    {"name": "向量归一化与余弦相似度、内积的关系", "code": "rag-embedding", "hot": 3},
                    {"name": "Recall@K、MRR、NDCG 分别衡量什么", "code": None, "hot": 3},
                ],
            },
            {
                "name": "融合与精排",
                "items": [
                    {"name": "RRF 倒数排名融合为什么比加权分数稳", "code": "rag-hybrid", "hot": 3},
                    {"name": "交叉编码器 Reranker 为什么比双塔准，代价在哪", "code": "rag-rerank", "hot": 3},
                    {"name": "召回 top50 再精排到 top4，参数怎么调", "code": "rag-rerank", "hot": 3},
                    {"name": "精排模型和 LLM 直接打分怎么选", "code": "rag-rerank", "hot": 2},
                    {"name": "多路召回结果怎么去重合并", "code": "rag-hybrid", "hot": 2},
                ],
            },
            {
                "name": "向量库与索引",
                "items": [
                    {"name": "HNSW 的分层图结构，ef 和 M 参数影响什么", "code": "rag-vector-db", "hot": 3},
                    {"name": "IVF、PQ 量化牺牲了什么换来了内存", "code": "rag-vector-db", "hot": 2},
                    {"name": "Milvus 的 collection、partition、segment 概念", "code": "rag-vector-db", "hot": 2},
                    {"name": "暴力检索在什么数据量下反而更合适", "code": "rag-vector-db", "hot": 2},
                    {"name": "元数据过滤和向量检索怎么组合才不丢召回", "code": "rag-vector-db", "hot": 3},
                ],
            },
            {
                "name": "数据治理与入库",
                "items": [
                    {"name": "文档入库流水线有哪几步，哪步最容易出问题", "code": "rag-ingest", "hot": 3},
                    {"name": "增量更新怎么保证不重不漏，幂等键怎么设计", "code": "rag-ingest", "hot": 3},
                    {"name": "去重的三层：哈希、归一化、语义阈值", "code": "rag-dedup", "hot": 3},
                    {"name": "文档删除了，向量库怎么同步删除", "code": "rag-ingest", "hot": 2},
                    {"name": "知识库更新后旧答案还在，是缓存还是索引问题", "code": "rag-ingest", "hot": 2},
                ],
            },
            {
                "name": "效果归因与调优",
                "items": [
                    {"name": "答案不对，怎么判断是检索问题还是生成问题", "code": "ai-eval", "hot": 3},
                    {"name": "怎么构造一套不泄漏的评测集", "code": "ai-eval", "hot": 3},
                    {"name": "召回率上不去，按什么顺序排查", "code": None, "hot": 3},
                    {"name": "query 改写与 HyDE 什么时候有用", "code": None, "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # 后端服务工程 —— 6 课，AI 应用后端的高频工程题
    # ==================================================================
    "后端服务工程": {
        "intro": "AI 应用的后端和普通后端最大的差别是「长耗时 + 流式 + 不稳定」，"
        "所以面试会盯着流式怎么做、超时怎么设、失败了怎么重试。",
        "branches": [
            {
                "name": "框架与依赖注入",
                "items": [
                    {"name": "FastAPI 的依赖注入怎么用，Depends 能解决什么", "code": "be-fastapi", "hot": 3},
                    {"name": "同步路由与异步路由混用会出什么问题", "code": "be-fastapi", "hot": 3},
                    {"name": "Pydantic 模型在请求校验里的执行时机", "code": "be-fastapi", "hot": 2},
                    {"name": "中间件、拦截器、装饰器的执行顺序", "code": "be-fastapi", "hot": 2},
                    {"name": "分层怎么分：router / service / repository 的边界", "code": "be-fastapi", "hot": 2},
                ],
            },
            {
                "name": "认证与鉴权",
                "items": [
                    {"name": "JWT 的结构，为什么不能在里面放敏感信息", "code": "be-auth", "hot": 3},
                    {"name": "JWT 无法主动失效，怎么做到登出", "code": "be-auth", "hot": 3},
                    {"name": "密码为什么用 bcrypt 而不是 MD5 / SHA256", "code": "be-auth", "hot": 3},
                    {"name": "Session 与 Token 的架构差异", "code": "be-auth", "hot": 3},
                    {"name": "越权漏洞：水平越权和垂直越权怎么防", "code": None, "hot": 3},
                ],
            },
            {
                "name": "流式输出与长连接",
                "items": [
                    {"name": "SSE 与 WebSocket 怎么选，各自适用什么场景", "code": "be-sse", "hot": 3},
                    {"name": "SSE 的响应头和分帧格式，为什么必须关缓冲", "code": "be-sse", "hot": 3},
                    {"name": "流式输出中途出错，怎么让前端知道", "code": "be-sse", "hot": 3},
                    {"name": "Nginx 反向代理把流式吞了，怎么配", "code": "be-sse", "hot": 3},
                    {"name": "客户端断开后，后端还在生成 token 怎么止损", "code": "be-sse", "hot": 3},
                ],
            },
            {
                "name": "限流、任务与幂等",
                "items": [
                    {"name": "固定窗口、滑动窗口、令牌桶、漏桶的区别", "code": "be-ratelimit", "hot": 3},
                    {"name": "Redis 滑动窗口限流怎么用 ZSet 实现", "code": "be-ratelimit", "hot": 3},
                    {"name": "接口幂等有哪几种实现方式", "code": "be-payment", "hot": 3},
                    {"name": "异步任务队列怎么保证不丢、不重复消费", "code": "be-async-task", "hot": 3},
                    {"name": "重试为什么必须配指数退避和抖动", "code": "be-async-task", "hot": 3},
                    {"name": "支付回调验签流程，为什么回调可能重复到达", "code": "be-payment", "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # 多模态与部署 —— 4 课，偏落地交付
    # ==================================================================
    "多模态与部署": {
        "intro": "考的是「你这套东西能不能真交付出去」：图片进模型怎么保证输出结构稳定、"
        "容器怎么做得小巧、小程序端登录态和重试怎么做。",
        "branches": [
            {
                "name": "视觉理解与结构化输出",
                "items": [
                    {"name": "图片输入模型有哪几种方式（URL / base64 / file_id）", "code": "mm-vision", "hot": 3},
                    {"name": "怎么让模型输出稳定 JSON，失败了怎么兜底", "code": "mm-vision", "hot": 3},
                    {"name": "图片太大怎么压缩，分辨率与精度的取舍", "code": "mm-vision", "hot": 2},
                    {"name": "多图与长文档的 token 成本怎么估", "code": "mm-vision", "hot": 2},
                ],
            },
            {
                "name": "文档解析",
                "items": [
                    {"name": "OCR 与版面分析的区别，为什么光 OCR 不够", "code": "mm-ocr", "hot": 3},
                    {"name": "表格还原成结构化数据有哪几种做法", "code": "mm-ocr", "hot": 3},
                    {"name": "扫描件、双栏排版、页眉页脚怎么处理", "code": "mm-ocr", "hot": 2},
                    {"name": "解析结果的坐标信息有什么用", "code": "mm-ocr", "hot": 1},
                ],
            },
            {
                "name": "部署与端",
                "items": [
                    {"name": "Dockerfile 分层缓存怎么写才快", "code": "mm-docker", "hot": 3},
                    {"name": "镜像为什么越小越好，多阶段构建怎么瘦身", "code": "mm-docker", "hot": 3},
                    {"name": "compose 里服务依赖与健康检查怎么写", "code": "mm-docker", "hot": 2},
                    {"name": "容器里时区、编码、环境变量常踩什么坑", "code": "mm-docker", "hot": 2},
                    {"name": "小程序登录态怎么换 openid，token 过期怎么续", "code": "mm-miniprogram", "hot": 3},
                    {"name": "小程序请求失败重试与并发限制", "code": "mm-miniprogram", "hot": 2},
                ],
            },
        ],
    },

    # ==================================================================
    # AI 工程质量 —— 3 课，但都是面试加分项
    # ==================================================================
    "AI 工程质量": {
        "intro": "这几题能直接区分「调过 API」和「上过线」："
        "幻觉怎么防、成本怎么压、答案出错了能不能追溯到源头。",
        "branches": [
            {
                "name": "可信与溯源",
                "items": [
                    {"name": "幻觉的几种类型，哪些能靠 RAG 解决", "code": "ai-grounding", "hot": 3},
                    {"name": "答案里标引用来源，引用怎么和原文对上", "code": "ai-grounding", "hot": 3},
                    {"name": "检索不到内容时，怎么让模型老实说不知道", "code": "ai-grounding", "hot": 3},
                    {"name": "怎么防止提示词注入与越权指令", "code": None, "hot": 3},
                    {"name": "输出内容安全过滤放在哪一层", "code": None, "hot": 2},
                ],
            },
            {
                "name": "成本与调度",
                "items": [
                    {"name": "三级路由：规则、小模型、大模型怎么分流", "code": "ai-router", "hot": 3},
                    {"name": "什么请求该走缓存，语义缓存的风险在哪", "code": "ai-router", "hot": 3},
                    {"name": "token 成本怎么算，哪几处最容易浪费", "code": "ai-llm-api", "hot": 3},
                    {"name": "降级策略：主模型挂了怎么保住可用性", "code": "ai-router", "hot": 3},
                    {"name": "并发限流与排队在 Agent 场景怎么设计", "code": "be-ratelimit", "hot": 2},
                ],
            },
            {
                "name": "评测与上线",
                "items": [
                    {"name": "Agent 评测集怎么建，为什么不能用训练数据评", "code": "ai-eval", "hot": 3},
                    {"name": "离线评测与线上 A/B 各自看什么指标", "code": "ai-eval", "hot": 3},
                    {"name": "多轮 Agent 的评测怎么判「中间步骤对不对」", "code": "ai-eval", "hot": 3},
                    {"name": "服务端图表渲染为什么要做，前端画不行吗", "code": "ai-chart", "hot": 2},
                    {"name": "上线后怎么监控回答质量下降", "code": None, "hot": 2},
                ],
            },
        ],
    },
}
