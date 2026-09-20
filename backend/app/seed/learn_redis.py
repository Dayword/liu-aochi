"""Redis：缓存与高性能数据结构实战。

从五种数据结构讲到持久化、高可用与缓存三大问题，按"面试高频"顺序编排。
"""

LESSONS: list[dict] = [
    # ---------------- 阶段：数据类型 ----------------
    {
        "code": "redis-01",
        "subject": "Redis",
        "stage": "数据类型",
        "runner": "none",
        "title": "Redis 为什么快与五大数据类型",
        "summary": "内存 + 单线程 + IO 多路复用",
        "definition": (
            "Redis 是一个**基于内存**的 key-value 数据库，最常被当作缓存用。它快的原因有四条，面试要能一条条说出来：\n\n"
            "- **数据全在内存里**：读内存是纳秒级，读磁盘是毫秒级，差了好几万倍\n"
            "- **命令单线程执行**：没有锁竞争、没有线程上下文切换的开销，顺手还保证了每条命令都是原子的\n"
            "- **IO 多路复用**：一个线程用 epoll 同时盯住上万个连接，谁有数据就处理谁，不空等\n"
            "- **数据结构是为场景定制的**：ZSet 取 TOP N 是 O(log N)，不用自己排序\n\n"
            "五种基础数据类型（面试让你「讲讲 Redis 的数据结构」，先说这五种）：\n\n"
            "- `String` 字符串：`SET` / `GET`。能存文本、数字，也能存序列化后的二进制\n"
            "- `List` 列表：`LPUSH` / `RPOP`。有序、可重复，两端进出都是 O(1)，能当队列也能当栈\n"
            "- `Hash` 哈希：`HSET` / `HGET`。一个 key 下面挂一张 field→value 的小表，适合存对象\n"
            "- `Set` 集合：`SADD` / `SISMEMBER`。无序、不重复，天生做去重和交集\n"
            "- `ZSet` 有序集合：`ZADD` / `ZRANGE`。每个成员绑一个 score，按分数自动排序\n\n"
            "另外还有几种特殊结构，面试用来加分：`Bitmap`（签到打卡）、`HyperLogLog`（UV 估算，误差 0.81%）、"
            "`GEO`（附近的人）、`Stream`（Redis 5.0 的消息队列）。\n\n"
            "⚠️ 一个必考细节：Redis 6.0 之后**网络 IO 变成了多线程**，但**执行命令仍然是单线程**。"
            "面试官问「Redis 是单线程吗」，标准答案是「命令执行是单线程的」。"
        ),
        "plain": (
            "把数据库想成**仓库**：东西全、能长期存，但取一次要跑一趟，慢。Redis 就是贴在你手边的**便利贴墙**："
            "常用的东西抄一份贴上来，抬手就能看到，几乎不用等。\n\n"
            "单线程为什么反而快？像一个**只有一名店员的小店**：店员不用和别人抢货架，也不用停下来交接工作，"
            "动作是连贯的。真正拖慢服务器的是「等网络、等磁盘」这类发呆时间，而 Redis 用 IO 多路复用把发呆时间利用起来了"
            "——一个店员同时照看几十桌客人，谁举手就去谁那，而不是站在一桌旁边干等。所以它快不是因为「能并行」，"
            "而是因为**几乎没有浪费**。"
        ),
        "example": (
            "# 五种类型各来一遍，感受一下命令风格\n"
            'SET user:1:name "小明"\n'
            "GET user:1:name\n"
            '→ "小明"\n'
            "\n"
            "RPUSH queue task1 task2 task3\n"
            "LRANGE queue 0 -1\n"
            '→ 1) "task1"  2) "task2"  3) "task3"\n'
            "\n"
            'HSET user:1 age 18 city "杭州"\n'
            "HGET user:1 age\n"
            '→ "18"\n'
            "\n"
            "SADD tags python redis python\n"
            "SCARD tags\n"
            "→ (integer) 2\n"
            "\n"
            'ZADD rank 88 "小明" 95 "小红" 70 "小刚"\n'
            "ZREVRANGE rank 0 -1 WITHSCORES\n"
            '→ 1) "小红"  2) "95"  3) "小明"  4) "88"  5) "小刚"  6) "70"'
        ),
        "example_output": (
            '"小明"\n'
            '1) "task1"\n'
            '2) "task2"\n'
            '3) "task3"\n'
            '"18"\n'
            "(integer) 2\n"
            '1) "小红"\n'
            '2) "95"\n'
            '3) "小明"\n'
            '4) "88"\n'
            '5) "小刚"\n'
            '6) "70"'
        ),
        "pitfalls": [
            "**别把 Redis 当数据库用**：即使开了 RDB/AOF 也可能丢最后几秒的数据，而且内存比磁盘贵一个数量级。能落库的业务数据，Redis 只负责加速，不能当唯一数据源。",
            "**「单线程」指的是命令执行**：一条慢命令会卡住所有人的请求。生产环境**禁用 `KEYS *`**，用 `SCAN` 游标分批遍历；`SMEMBERS`、`HGETALL`、`LRANGE k 0 -1` 在大 key 上同样危险。",
            "**key 不会自动过期**：不写 `EXPIRE` / `EX` 就一直占着内存。所有缓存 key 必须带 TTL，这是缓存实例能长期稳定运行的底线。",
            "**`INCR` 的数值有上限**：它按 64 位有符号整数处理，加到 `9223372036854775807` 会直接报 `ERR increment or decrement would overflow`，别拿它做无上限的累计。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官：Redis 的命令是单线程执行的，为什么还比 MySQL 快这么多？",
                "options": [
                    "数据全在内存里省掉了磁盘 IO，再加上单线程免去了锁竞争和上下文切换",
                    "因为 Redis 是 C 语言写的，编译后的机器码执行更快",
                    "因为 Redis 只是缓存，不需要保证数据一致性和事务",
                    "因为 Redis 多线程并行执行命令，吞吐自然更高",
                ],
                "answer_index": 0,
                "explanation": (
                    "核心就两条：**内存 + 单线程免锁**。B 站不住脚，MySQL 也是 C/C++ 写的；"
                    "C 说反了，Redis 有事务（MULTI/EXEC）和原子命令；D 说错了执行模型——多线程只在网络 IO 层。"
                    "把「epoll 多路复用」和「专用数据结构」补上，这个回答就满了。"
                ),
            },
            {
                "type": "choice",
                "stem": "要统计一个页面的独立访客（UV），同一个用户刷 100 次只算 1 次，用哪种类型最合适？",
                "options": ["String", "List", "Set", "Hash"],
                "answer_index": 2,
                "explanation": (
                    "`SADD uv:20260919 u1001` 会自动去重，`SCARD` 就是 UV。List 能重复、Hash 要自己维护 field，都不合适。"
                    "数据量上亿时再换 `HyperLogLog`（`PFADD` / `PFCOUNT`），固定约 12KB 内存、误差 0.81%。"
                ),
            },
            {
                "type": "judge",
                "stem": "用 `RPUSH` 从右边插入、`LPOP` 从左边弹出，实现的就是一个先进先出的队列。",
                "answer": True,
                "explanation": (
                    "先进去的元素先被取出，正是 FIFO。反过来 `RPUSH` + `RPOP`（或者 `LPUSH` + `LPOP`）就是栈（LIFO）。"
                    "中间的任何不一致，队形就乱了——这也是 List 做队列最容易被忽略的细节。"
                ),
            },
            {
                "type": "blank",
                "stem": ("补全命令，把 `rank` 这个有序集合里分数最高的 3 个成员按从高到低取出来：\nZ___ rank 0 2 WITHSCORES"),
                "answer": "REVRANGE",
                "accept": ["revrange", "ZRANGE"],
                "hint": "一个命令名，8 个字母，表示「反向区间」",
                "explanation": (
                    "`ZREVRANGE` 按 score 从大到小取，做排行榜就用它；`ZRANGE` 是从小到大。"
                    "Redis 6.2 之后官方推荐统一写 `ZRANGE rank 0 2 REV WITHSCORES`，两者等价。"
                ),
            },
            {
                "type": "short",
                "stem": "面试官：你说 Redis 快，除了「数据在内存里」，还有什么原因？",
                "keywords": [
                    "单线程免锁",
                    "IO 多路复用 epoll",
                    "无上下文切换",
                    "高效数据结构",
                    "RESP 协议",
                    "命令原子性",
                ],
                "reference": (
                    "第一是**单线程执行命令**，没有锁竞争也没有线程上下文切换的开销，"
                    "而且每条命令天然原子，`INCR`、`SETNX` 这类操作不用额外加锁。"
                    "第二是**IO 多路复用**，用 epoll 一个线程管理上万个连接，不阻塞在单个连接上。"
                    "第三是**数据结构为场景定制**，ZSet 用跳表做到 O(log N) 的范围查询和排名。"
                    "第四是协议简单（RESP）和连接复用（pipeline），省掉了大量网络往返。"
                    "最后补一句：Redis 6.0 之后网络 IO 是多线程的，但命令执行仍然是单线程。"
                ),
                "explanation": "把「单线程 + 多路复用」讲清楚，再点名 Redis 6.0 的 IO 多线程，就是标准满分答案。",
            },
        ],
    },
    {
        "code": "redis-02",
        "subject": "Redis",
        "stage": "数据类型",
        "runner": "none",
        "title": "String 计数器与分布式 ID",
        "summary": "SET NX 加锁，INCR 发号",
        "definition": (
            "`String` 是 Redis 最基础也最常用的类型。核心命令：\n\n"
            "- `SET k v` / `GET k`：写入和读取\n"
            "- `SET k v EX 60`：写入并设过期时间（秒），`PX` 是毫秒\n"
            "- `SET k v NX`：key 不存在才写；`XX` 是只在已存在时写\n"
            "- `SET k v KEEPTTL`：覆盖 value 但**保留原有 TTL**（Redis 6.0+）\n"
            "- `SETEX k 60 v`：等价于 `SET k v EX 60`；`GETSET` 是「取旧值再写新值」\n"
            "- `INCR k` / `INCRBY k 10` / `DECRBY k 5`：原子自增自减\n"
            "- `MSET` / `MGET`：一次读写多个 key，省往返\n\n"
            "**它解决什么问题**：计数器和分布式 ID 都依赖 `INCR` 的原子性。Redis 单线程执行命令，"
            "`INCR` 的「读—加—写」不会被别的请求插队，所以不需要加锁。相比之下，"
            "MySQL 里 `UPDATE counter SET v = v + 1` 要顶着行锁，热点行会严重串行化。\n\n"
            "**分布式 ID 的两种常用做法**：\n\n"
            "- `INCR order:id`：拿到全局唯一的递增号。好处是**有序**——有序主键在 MySQL 里是顺序写，不会页分裂\n"
            "- `INCR` + 业务标识/日期拼接：`ORDER_20260919_000123`，既唯一又方便排查\n\n"
            "**分布式锁的起点**也在这：`SET lock:order:1001 <uuid> NX PX 30000` 一条命令同时做到"
            "「互斥 + 防死锁 + 可识别持有者」，是官方推荐的加锁写法。"
        ),
        "plain": (
            "`INCR` 就像停车场入口的**自动计数牌**：车开过去它自己 +1，不需要两个人配合——"
            "一个人看数字、另一个人加，中间必然出岔子。Redis 单线程把这一步做成了不可分割的动作，"
            "所以再多的人同时点「点赞」，数字也一定是准的。\n\n"
            "分布式 ID 就像**银行叫号机**：窗口再多，叫号机只有一个，谁拿到票谁就知道自己是第几号。"
            "用 `INCR order:id` 拿一个全局递增的号，比 UUID 短、有顺序、还能直接当 MySQL 主键。"
            "而 `SET ... NX` 像会议室门口的**房卡槽**：卡槽里已经有卡了，后来的就插不进去——这就是锁的全部原理。"
        ),
        "example": (
            "# 最简单的原子计数器\n"
            "SET article:9:likes 0\n"
            "→ OK\n"
            "INCR article:9:likes\n"
            "→ (integer) 1\n"
            "INCRBY article:9:likes 10\n"
            "→ (integer) 11\n"
            "\n"
            "# 带 TTL 的缓存：5 分钟后自动消失\n"
            'SET user:1:name "小明" EX 300\n'
            "→ OK\n"
            "GET user:1:name\n"
            '→ "小明"\n'
            "TTL user:1:name\n"
            "→ (integer) 300\n"
            "\n"
            "# 不存在才写：幂等控制 / 加锁的基础\n"
            "SET id:order 1000 NX\n"
            "→ OK\n"
            "SET id:order 1000 NX\n"
            "→ (nil)          # 已存在，不会覆盖\n"
            "INCR id:order\n"
            "→ (integer) 1001\n"
            "\n"
            "# 批量读写，省网络往返\n"
            "MSET a 1 b 2 c 3\n"
            "→ OK\n"
            "MGET a b c\n"
            '→ 1) "1"  2) "2"  3) "3"'
        ),
        "example_output": (
            "OK\n"
            "(integer) 1\n"
            "(integer) 11\n"
            "OK\n"
            '"小明"\n'
            "(integer) 300\n"
            "OK\n"
            "(nil)\n"
            "(integer) 1001\n"
            "OK\n"
            '1) "1"\n'
            '2) "2"\n'
            '3) "3"'
        ),
        "pitfalls": [
            "**`INCR` 只能作用在数字字符串上**：对 `SET k \"abc\"` 执行 `INCR` 会报 `ERR value is not an integer or out of range`。反过来，key 不存在时 `INCR` 会当成 0 再加 1，正好可以用来「第一次访问就初始化」，省掉一次 `SETNX`。",
            "**`SET k v` 会把原来的 TTL 一起清掉**：这是「缓存越跑越大、内存缓慢泄漏」最常见的根因。更新缓存必须写成 `SET k v EX 3600`，或者用 `SET k v KEEPTTL` 保留原过期时间。",
            "**`INCR` 出来的 ID 不是绝对可靠的**：如果只开 RDB 没开 AOF，Redis 崩溃重启后会从上一个快照恢复，`id:order` 回退到一个更小的值，可能发出**重复 ID**。要求严格唯一时用「时间戳 + 自增」拼接，或者用雪花算法/数据库序列。",
            "**不要用 `MGET` 一次捞几百个 key**：单线程执行，一次几百上千个 key 会明显抬高这次请求的耗时，进而拖慢所有客户端。大 key（value 超 10KB，或集合类元素超 5000）也是同理，该拆就拆。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "用 `SET lock:order:1001 <uuid> NX PX 30000` 加锁，为什么 `NX` 和 `PX` 缺一不可？",
                "options": [
                    "`NX` 保证同一时刻只有一个客户端能拿到锁，`PX` 保证客户端崩溃后锁会自动释放",
                    "`NX` 用来设置 value，`PX` 用来设置 key 的类型",
                    "`NX` 表示「不覆盖已有值」，`PX` 表示「只读」",
                    "两个都是可选项，只写 `SET` 效果一样",
                ],
                "answer_index": 0,
                "explanation": (
                    "只有 `NX` 会变成死锁——进程崩了锁永远不释放；只有 `PX` 就没有互斥，谁都能覆盖。"
                    "而且这两者必须在**同一条命令**里：如果写成 `SETNX` 再 `EXPIRE`，中间那一刻进程挂掉，就留下了一把永不过期的锁。"
                ),
            },
            {
                "type": "choice",
                "stem": "下面哪条命令能拿到一个全局递增的分布式 ID？",
                "options": ["`INCR order:id`", "`SET order:id 0`", "`GET order:id`", "`HSET order id 0`"],
                "answer_index": 0,
                "explanation": (
                    "`INCR` 是原子的「读—加—写」，并发下每个客户端拿到的号都不同。"
                    "`SET` 是写死一个值，`GET` 只读，`HSET` 建的是 Hash 字段而且不递增。"
                ),
            },
            {
                "type": "judge",
                "stem": "执行 `SET user:1:name \"小明\" EX 300` 之后，再执行一次不带 `EX` 的 `SET user:1:name \"小红\"`，这个 key 的过期时间仍然是 300 秒。",
                "answer": False,
                "explanation": (
                    "不带 `EX`/`KEEPTTL` 的 `SET` 会**清除原有 TTL**，key 变成永不过期。"
                    "要保留过期时间得显式写 `SET user:1:name \"小红\" KEEPTTL`。"
                ),
            },
            {
                "type": "blank",
                "stem": "只允许在 key 不存在时写入（用来做加锁或幂等控制），需要给 `SET` 加上哪个选项？\nSET lock:order:1001 uuid-abc ___ PX 30000",
                "answer": "NX",
                "accept": ["nx"],
                "hint": "两个字母的选项",
                "explanation": "`NX` = Not eXists，不存在才写。与之相对的是 `XX`（只在已存在时写），常用来更新缓存而不误建 key。",
            },
            {
                "type": "short",
                "stem": "面试官：为什么用 Redis 的 `INCR` 生成分布式 ID，比 UUID 好？它有什么风险？",
                "keywords": [
                    "全局递增",
                    "有序主键不页分裂",
                    "无锁原子操作",
                    "长度短省空间",
                    "重启回退可能重复",
                    "时间戳加自增拼接",
                ],
                "reference": (
                    "好处有三点：`INCR` 是**原子的无锁自增**，并发安全且性能高；生成的是**递增且有序**的数字，"
                    "作为 MySQL 主键是顺序写，不会像 UUID 那样随机写导致页分裂；长度只有十几个字节，"
                    "比 36 字符的 UUID 省索引空间、也更好排查问题。\n"
                    "风险在于**持久化**：如果只开 RDB，Redis 崩溃重启后计数会回退到快照时刻的值，可能发出重复 ID。"
                    "生产上通常用「日期 + `INCR` 补零」拼成 `ORDER_20260919_000123`，或者干脆用雪花算法，"
                    "把唯一性建立在时间戳和机器位上而不是单点计数上。"
                ),
                "explanation": "这类题的得分点是「有序」和「无锁原子」，能主动说出重启回退风险就算答到位了。",
            },
        ],
    },
    {
        "code": "redis-03",
        "subject": "Redis",
        "stage": "数据类型",
        "runner": "none",
        "title": "List 与 Hash 的典型用法",
        "summary": "List 排队，Hash 存对象",
        "definition": (
            "`List` 是有序、可重复的列表，两端插入和弹出都是 O(1)：\n\n"
            "- `LPUSH` / `RPUSH`：从左 / 右压入\n"
            "- `LPOP` / `RPOP`：从左 / 右弹出\n"
            "- `BRPOP k 30` / `BLPOP k 30`：**阻塞版**弹出，队列空时挂起等待，超时才返回——做队列的关键\n"
            "- `LRANGE k 0 -1`：取区间，`-1` 表示最后一个\n"
            "- `LLEN`：长度；`LTRIM k 0 99`：只保留前 100 个，做「最近 N 条」的标准手法\n"
            "- `LMOVE` / `RPOPLPUSH`：从一个 list 弹出并压到另一个 list，一条命令完成「搬运」\n\n"
            "做队列：`RPUSH` 入队 + `LPOP` / `BRPOP` 出队，就是 FIFO。\n\n"
            "`Hash` 是一个 key 下面挂一张 field→value 的小表：\n\n"
            "- `HSET k f v` / `HGET k f` / `HMGET` / `HGETALL`\n"
            "- `HINCRBY k f 1`：对某个 field 原子自增\n"
            "- `HDEL k f` / `HLEN k` / `HKEYS` / `HVALS`\n\n"
            "**它解决什么问题**：存一个对象时，用 `user:1` 这样的 Hash 只占 1 个 key，"
            "而把每个字段拆成 `user:1:name`、`user:1:age` 会产生一堆 key，既费内存，也没法一次取全。\n\n"
            "**选型口诀**：要「顺序 + 两端进出」用 List（队列、消息流、最近 N 条）；"
            "要「按字段读写一个对象」用 Hash（购物车、用户资料、配置）；"
            "只是存一个整串用 String。"
        ),
        "plain": (
            "`List` 就是**排队买奶茶的队伍**：新人从队尾加入（`RPUSH`），店员从队首叫人（`LPOP`），"
            "先来先服务；如果从同一头进出，它就变成了「后进先出」的栈。所以 List 既能当队列也能当栈，"
            "关键看你在哪一头取。`BRPOP` 是**队空了也不下班，站在门口等**的店员，一来人立刻开工。\n\n"
            "`Hash` 像**一张贴了名字的资料卡**：卡片本身叫 `user:1`，上面有「姓名」「年龄」「城市」几个格子。"
            "改哪个格子只改那一格，不用整张卡重写。要是把每个格子单独贴到墙上，想凑齐一个人的信息就得跑好几个地方"
            "——这既慢，又占地方。"
        ),
        "example": (
            "# List：先进先出的任务队列\n"
            "RPUSH queue:mail m1 m2 m3\n"
            "LLEN queue:mail\n"
            "→ (integer) 3\n"
            "LPOP queue:mail\n"
            '→ "m1"\n'
            "LRANGE queue:mail 0 -1\n"
            '→ 1) "m2"  2) "m3"\n'
            "\n"
            "# List：只保留最近 3 条（典型的 feed 流做法）\n"
            'RPUSH feed:1 "a" "b" "c" "d"\n'
            "LTRIM feed:1 0 2\n"
            "LRANGE feed:1 0 -1\n"
            '→ 1) "a"  2) "b"  3) "c"\n'
            "\n"
            "# Hash：存一个对象，只改其中一个字段\n"
            'HSET user:1 name "小明" age 18 city "杭州"\n'
            "→ (integer) 3\n"
            "HGET user:1 name\n"
            '→ "小明"\n'
            "HINCRBY user:1 age 1\n"
            "→ (integer) 19\n"
            "HGETALL user:1\n"
            '→ 1) "name"  2) "小明"  3) "age"  4) "19"  5) "city"  6) "杭州"'
        ),
        "example_output": (
            "(integer) 3\n"
            '"m1"\n'
            '1) "m2"\n'
            '2) "m3"\n'
            "OK\n"
            '1) "a"\n'
            '2) "b"\n'
            '3) "c"\n'
            "(integer) 3\n"
            '"小明"\n'
            "(integer) 19\n"
            '1) "name"\n'
            '2) "小明"\n'
            '3) "age"\n'
            '4) "19"\n'
            '5) "city"\n'
            '6) "杭州"'
        ),
        "pitfalls": [
            "**Hash 的单个 field 不能设 TTL**：`EXPIRE` 作用在整个 key 上。Redis 7.4 起才有 `HEXPIRE` / `HTTL` 支持字段级过期；在那之前要给单个字段单独过期，只能拆成独立的 String key。",
            "**小 Hash 很省内存，但不代表 Hash 永远更省**：field 少时用紧凑的 listpack/ziplist 编码；field 超过 `hash-max-listpack-entries`（默认 128 个）就转成 hashtable，内存开销会明显上来。存大对象时反而拆成 String 更划算。",
            "**`LRANGE k 0 -1` 在大 List 上会卡住整个 Redis**：list 里有十万条就够让所有请求一起等。遍历用分段取，或者用 `LTRIM` 把长度控制在几千以内。",
            "**List 做消息队列默认不保证不丢**：`LPOP` 弹出来之后进程崩溃，这条消息就永远消失了。要可靠消费必须两步走——用 `LMOVE` / `BRPOPLPUSH` 把消息搬到「处理中」队列，处理成功再删除；或者直接用 Redis 5.0+ 的 `Stream`（`XADD` / `XREADGROUP` / `XACK`）。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "用 List 实现「先进先出」的队列，下面哪种写法是对的？",
                "options": [
                    "`RPUSH` 入队、`LPOP` 出队",
                    "`LPUSH` 入队、`LPOP` 出队",
                    "`LPUSH` 入队、`LRANGE` 出队",
                    "`RPUSH` 入队、`RPOP` 出队",
                ],
                "answer_index": 0,
                "explanation": (
                    "右边进、左边出才是 FIFO。B 和 D 是同一头进出，得到的是**栈**（LIFO）；"
                    "C 的 `LRANGE` 只读不删，队列永远不会变短，是典型的错误写法。"
                ),
            },
            {
                "type": "choice",
                "stem": "要存一个用户对象的 name / age / city 三个字段，而且经常只改其中一个字段，用哪种结构更合适？",
                "options": [
                    "一个 Hash，key 为 `user:1`",
                    "三个独立的 String：`user:1:name`、`user:1:age`、`user:1:city`",
                    "一个 List，依次放三个值",
                    "一个 Set，放三个字符串",
                ],
                "answer_index": 0,
                "explanation": (
                    "Hash 只占 1 个 key、改单字段用 `HSET`、取全部用 `HGETALL`，语义也最清楚。"
                    "B 的写法会产生大量 key 且没法一次取全；List 要靠下标猜字段，Set 无序还去重，都不合适。"
                ),
            },
            {
                "type": "judge",
                "stem": "在 Hash 上执行 `EXPIRE user:1 60`，只会让 age 这个字段 60 秒后过期，其他字段不受影响。",
                "answer": False,
                "explanation": (
                    "`EXPIRE` 作用在**整个 key** 上，到点后 `user:1` 这张 Hash 整体消失。"
                    "在 Redis 7.4 之前 Hash 字段没有独立的 TTL，需要字段级过期就只能拆成多个 String key。"
                ),
            },
            {
                "type": "blank",
                "stem": "要阻塞等待 `queue:mail` 里有新任务再弹出（30 秒超时），应该用哪个命令？\n___ queue:mail 30",
                "answer": "BRPOP",
                "accept": ["brpop", "BLPOP", "blpop"],
                "hint": "阻塞版弹出命令，5 个字母",
                "explanation": (
                    "`BRPOP` 从右边弹出，必须和入队的 `LPUSH` 配对才是 FIFO；`BLPOP` 从左边弹出，配 `RPUSH`。"
                    "**取的方向必须和存的方向相反**，否则队列会退化成栈。"
                ),
            },
            {
                "type": "short",
                "stem": "面试官：让你用 Redis 做一个简单的任务队列，你会怎么做？和 Kafka 比差在哪？",
                "keywords": [
                    "RPUSH + BRPOP 阻塞消费",
                    "先进先出",
                    "消息可能丢",
                    "LMOVE 到处理中队列",
                    "无消费组无回溯",
                    "Stream 或换 Kafka",
                ],
                "reference": (
                    "最简版是**生产者 `LPUSH`、消费者 `BRPOP` 阻塞等待**：一条命令完成入队，一条完成出队，"
                    "队列空时消费者挂起不消耗 CPU。\n"
                    "但它有几个硬伤：`LPOP` 之后进程崩溃**消息就丢了**，没有 ACK 机制；"
                    "多个消费者抢同一个 list，无法按组消费；消息出队即删除，**不支持回溯和重放**；"
                    "也没有分区、堆积监控这些能力。\n"
                    "所以生产上要么升级到 `Stream`（有消费组和 `XACK`，能查未确认消息），"
                    "要么直接把这种场景交给 Kafka / RocketMQ。**Redis 适合做轻量、允许少量丢失的队列**，"
                    "不要拿它扛订单、支付这类不能丢的链路。"
                ),
                "explanation": "能主动说出「会丢消息」和「不支持消费组」，说明你分得清玩具和基础设施。",
            },
        ],
    },
    {
        "code": "redis-04",
        "subject": "Redis",
        "stage": "数据类型",
        "runner": "none",
        "title": "Set 与 ZSet 排行榜实战",
        "summary": "Set 去重，ZSet 实时排序",
        "definition": (
            "`Set` 是无序、不重复的集合，底层就是哈希表，所以判重是 O(1)：\n\n"
            "- `SADD k a b c` / `SREM k a` / `SCARD k`\n"
            "- `SISMEMBER k a`：判断成员在不在，返回 1 / 0\n"
            "- `SMEMBERS k`：取全部（大 Set 慎用）\n"
            "- `SINTER` 交集 / `SUNION` 并集 / `SDIFF` 差集\n"
            "- `SPOP` 随机弹出并删除 / `SRANDMEMBER` 随机取不删除\n\n"
            "典型场景：点赞去重、用户标签、**共同好友**（`SINTER`）、抽奖不重复（`SPOP`）、UV 统计（`SCARD`）。\n\n"
            "`ZSet`（sorted set）在 Set 的基础上给每个成员绑一个 `score`，按 score 排序，"
            "底层是**跳表 + 哈希表**：跳表负责范围查询和排名，哈希表负责 O(1) 查分数。\n\n"
            "- `ZADD rank 95 \"小红\"`：加成员并给分\n"
            "- `ZINCRBY rank 1 \"小红\"`：在原分数上累加，不存在就新建\n"
            "- `ZSCORE rank \"小红\"`：查分数\n"
            "- `ZRANGE rank 0 9 WITHSCORES`：从低到高取前 10\n"
            "- `ZREVRANGE rank 0 9 WITHSCORES`：从高到低取前 10（排行榜就用这个）\n"
            "- `ZRANK` / `ZREVRANK`：查排名，**返回值从 0 开始**\n"
            "- `ZRANGEBYSCORE rank 90 100`：按分数区间取\n\n"
            "**它解决什么问题**：排行榜要求「实时更新分数 + 随时取 TOP N + 查某人排名」。"
            "MySQL 得 `ORDER BY score DESC LIMIT 10` 全表排序，数据一多就撑不住；"
            "ZSet 的插入和范围查询都是 O(log N)，而且 `ZINCRBY` 天生原子。\n\n"
            "这题几乎必考，**标准答案是：排行榜用 ZSet，底层跳表，`ZINCRBY` 累加分数、"
            "`ZREVRANGE` 取 TOP N、`ZREVRANK` 查个人排名**。"
        ),
        "plain": (
            "`Set` 像**门口的签到表**：来一个人签名，签过的人再签一次也只算一个，所以人数一眼能数出来。"
            "「我们俩有几个共同好友？」把两张签到表叠起来对一对——对上的就是交集，这就是 `SINTER`。\n\n"
            "`ZSet` 像**游戏里的排行榜**：每个玩家有分数，分数一变名次自动重排，你不需要每次有人加分"
            "就把整张榜重新排一遍。面试官最想听的就是这一点：ZSet **不是靠「每次查询时排序」，"
            "而是在插入的那一刻就把顺序维护好了**。所以取前十名几乎是白送的，跟榜上有 100 人还是 100 万人关系不大。"
        ),
        "example": (
            "# Set：去重、判重、交集\n"
            "SADD uv:20260919 u1 u2 u3 u1\n"
            "→ (integer) 3\n"
            "SCARD uv:20260919\n"
            "→ (integer) 3\n"
            "SISMEMBER uv:20260919 u2\n"
            "→ (integer) 1\n"
            "SADD uv:20260918 u2 u3 u4\n"
            "→ (integer) 3\n"
            "SINTER uv:20260918 uv:20260919\n"
            '→ 1) "u2"  2) "u3"\n'
            "\n"
            "# ZSet：实时排行榜\n"
            'ZADD rank 88 "小明"\n'
            "→ (integer) 1\n"
            'ZADD rank 95 "小红" 70 "小刚"\n'
            "→ (integer) 2\n"
            'ZINCRBY rank 10 "小刚"\n'
            '→ "80"\n'
            "ZREVRANGE rank 0 2 WITHSCORES\n"
            '→ 1) "小红"  2) "95"  3) "小明"  4) "88"  5) "小刚"  6) "80"\n'
            'ZREVRANK rank "小刚"\n'
            "→ (integer) 2"
        ),
        "example_output": (
            "(integer) 3\n"
            "(integer) 3\n"
            "(integer) 1\n"
            "(integer) 3\n"
            '1) "u2"\n'
            '2) "u3"\n'
            "(integer) 1\n"
            "(integer) 2\n"
            '"80"\n'
            '1) "小红"\n'
            '2) "95"\n'
            '3) "小明"\n'
            '4) "88"\n'
            '5) "小刚"\n'
            '6) "80"\n'
            "(integer) 2"
        ),
        "pitfalls": [
            "**`SMEMBERS` / `ZRANGE k 0 -1` 在大集合上会阻塞主线程**：Set 有几百万成员时取全量是灾难。判重优先 `SISMEMBER`，遍历用 `SSCAN` / `ZSCAN`，只要前 N 名就老实写 `ZREVRANGE k 0 9`。",
            "**ZSet 的 score 是双精度浮点数**：反复 `ZINCRBY` 加 0.1 会出现 `0.30000000000000004` 这类精度误差。涉及金额的分数一律用整数——**存「分」而不是「元」**。",
            "**并列名次 ZSet 不会帮你处理**：score 相同时按成员字典序排列。业务要「同分并列第几」得在应用层算，或者用「`score * 10^10 + 反向时间戳`」拼一个复合分数，让「分数高、先到先排」自动成立。",
            "**`ZRANK` 返回的是从 0 开始的下标**：第一名返回 `(integer) 0`，直接展示给用户会变成「第 0 名」，记得 +1。Redis 7.2 起可用 `ZRANK k member WITHSCORE` 同时拿分数。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "抽奖要把中奖用户从名单里移除，保证同一个人不会被重复抽到，用哪个命令？",
                "options": [
                    "`SPOP prize`",
                    "`SMEMBERS prize`",
                    "`SISMEMBER prize u1`",
                    "`SCARD prize`",
                ],
                "answer_index": 0,
                "explanation": (
                    "`SPOP` 随机弹出**并删除**，弹出来的人自动从集合消失，天然不重复。"
                    "如果业务允许重复中奖，就用 `SRANDMEMBER`（只取不删）。"
                    "`SMEMBERS` 只是读全部，`SCARD` 只数个数，都不改变集合。"
                ),
            },
            {
                "type": "choice",
                "stem": "排行榜里每个成员的分数会频繁被 +1，下面哪条命令最合适？",
                "options": [
                    "`ZINCRBY rank 1 \"小明\"`",
                    "`ZADD rank 1 \"小明\"`",
                    "`ZSCORE rank \"小明\"`",
                    "`SADD rank \"小明\"`",
                ],
                "answer_index": 0,
                "explanation": (
                    "`ZINCRBY` 在**原有分数上累加**，而且是一条原子命令，并发加分不会丢。"
                    "`ZADD` 是直接覆盖分数，会把之前攒的分全冲掉——这是最常写错的一行。"
                    "`ZSCORE` 只读，`SADD` 是 Set 的命令，ZSet 上用不了。"
                ),
            },
            {
                "type": "judge",
                "stem": "ZSet 的 `ZRANGE` 复杂度是 O(1)，所以取前 10 名和取前 100 万名的耗时差不多。",
                "answer": False,
                "explanation": (
                    "定位到区间的起点是 O(log N)，但**返回 N 个元素的开销是 O(N)**，整体是 O(log N + N)。"
                    "取前 10 名很快，取前 100 万条照样会把网络和内存打满，还可能阻塞单线程。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全命令，查出 `uv:20260918` 与 `uv:20260919` 两个集合的**共同元素**：\n___ uv:20260918 uv:20260919",
                "answer": "SINTER",
                "accept": ["sinter"],
                "hint": "一个命令名，6 个字母，intersection 的意思",
                "explanation": "`SINTER` 求交集，「共同好友」「共同关注」都是它。并集是 `SUNION`，差集是 `SDIFF`。",
            },
            {
                "type": "short",
                "stem": "面试官：直播间的实时礼物榜，要支持分数实时累加、查 TOP 10、查「我的排名」，你怎么设计？数据量上千万怎么办？",
                "keywords": [
                    "ZSet",
                    "ZINCRBY 原子累加",
                    "ZREVRANGE 取 TOP N",
                    "ZREVRANK 查排名",
                    "O(log N)",
                    "按天或按房间分片",
                ],
                "reference": (
                    "用 ZSet：`ZINCRBY rank:room1001 1 \"user:88\"` 做原子累加分数，"
                    "`ZREVRANGE rank:room1001 0 9 WITHSCORES` 取 TOP 10，"
                    "`ZREVRANK rank:room1001 \"user:88\"` 查排名——三者都是 O(log N)，千万级成员也能扛。\n"
                    "要注意三点：一是**榜单必须按房间、按天拆 key**（`rank:room1001:20260919`），"
                    "否则单 key 会无限膨胀；二是名次展示用 `ZREVRANK` 的返回值 +1，"
                    "「距上一名还差多少分」用 `ZREVRANGEBYSCORE` 按分数区间查；"
                    "三是历史榜单直接给 key 设 TTL，过期即归档到数据库，不要让热数据一直占内存。"
                ),
                "explanation": "这题考的是「ZSet + `ZINCRBY`/`ZREVRANGE`/`ZREVRANK`」这套组合拳，外加分片意识。",
            },
        ],
    },
    # ---------------- 阶段：持久化与高可用 ----------------
    {
        "code": "redis-05",
        "subject": "Redis",
        "stage": "持久化与高可用",
        "runner": "none",
        "title": "过期策略与内存淘汰",
        "summary": "TTL 到期不等于马上被删",
        "definition": (
            "给 key 设过期：`EXPIRE k 60`（秒）、`PEXPIRE k 60000`（毫秒）、`EXPIREAT k <时间戳>`；"
            "`TTL k` 查剩余秒数，`PERSIST k` 取消过期。返回值要记牢：\n\n"
            "- `(integer) -1`：key 存在，但**没有设置**过期时间\n"
            "- `(integer) -2`：key **已经不存在**\n\n"
            "**Redis 怎么删除过期 key**（面试必问，答案就是下面这两条）：\n\n"
            "- **惰性删除**：key 被访问时才检查是否过期，过期就删掉并返回 nil。缺点是不访问就永远占着内存\n"
            "- **定期删除**：默认每秒 10 次，每次**随机抽 20 个**设了 TTL 的 key，删掉其中过期的；"
            "如果过期比例超过 25%，就再抽一轮。用随机采样把 CPU 占用控制在可接受范围\n\n"
            "关键结论：**Redis 不会给每个 key 挂定时器**——几十万个 key 配几十万个定时任务，CPU 直接崩。"
            "所以「TTL 归零」和「内存被释放」是两件事，过期 key 会在一段时间内继续占内存。\n\n"
            "**内存淘汰**：当 `maxmemory` 用满时，按 `maxmemory-policy` 决定淘汰谁。策略共 8 种，"
            "分三大类：\n\n"
            "- `noeviction`（**默认值**）：不淘汰，写入直接报错 `OOM command not allowed when used memory > 'maxmemory'`\n"
            "- `allkeys-*`：在所有 key 里挑\n"
            "  - `allkeys-lru`：淘汰最久未使用的 —— **纯缓存场景首选**\n"
            "  - `allkeys-lfu`：淘汰访问频率最低的（Redis 4.0+）—— 比 LRU 更抗「偶发全量扫描冲掉热 key」\n"
            "  - `allkeys-random`：随机删\n"
            "- `volatile-*`：只在**设了 TTL 的 key** 里挑，有 `volatile-lru` / `volatile-lfu` / `volatile-ttl` / `volatile-random`\n\n"
            "**生产结论**：纯做缓存就配 `allkeys-lru` 或 `allkeys-lfu`；"
            "同一个实例既存缓存又存不能丢的数据，就配 `volatile-lru` 并保证缓存 key 都带 TTL，"
            "但**更推荐拆成两个实例**，用架构解决问题比用策略调参可靠。\n\n"
            "另外要记住：**Redis 的 LRU 是近似的**，它只采样若干个 key 比较（`maxmemory-samples` 默认 5），"
            "并不精确，这是为了省内存和 CPU 做的取舍。"
        ),
        "plain": (
            "把 Redis 想成一间**出租的储物柜**：每个格子都有租期。管理员不会一直盯着时钟——他**随机抽查几个柜子**"
            "（定期删除），有人来开柜子时**顺手看一眼有没有过期**（惰性删除）。所以一个柜子租期到了但没人碰，"
            "东西还可能待在里面。\n\n"
            "内存淘汰则是**柜子全满了还要装新东西**：管理员得决定扔谁的。`allkeys-lru` 就是「谁最久没来用过就扔谁的」"
            "——像衣柜塞不下时先扔掉一年没穿的衣服。`volatile-*` 系列是「只扔那些写了租期的柜子」，"
            "凡是不设 TTL 的数据（比如排行榜）一律不动。所以：**给缓存 key 设 TTL，等于给淘汰策略划了一块安全区**。"
        ),
        "example": (
            "# 设 TTL 与查看\n"
            'SET session:abc "token123"\n'
            "EXPIRE session:abc 60\n"
            "TTL session:abc\n"
            "→ (integer) 60\n"
            "PERSIST session:abc\n"
            "→ (integer) 1\n"
            "TTL session:abc\n"
            "→ (integer) -1          # -1 表示永不过期\n"
            "\n"
            "# 一条命令搞定「写入 + TTL」，推荐写法\n"
            'SET code:13800000000 "9527" EX 300\n'
            "TTL code:13800000000\n"
            "→ (integer) 300\n"
            "\n"
            "# 看当前的淘汰策略和内存占用\n"
            "CONFIG GET maxmemory-policy\n"
            '→ 1) "maxmemory-policy"  2) "noeviction"\n'
            "CONFIG SET maxmemory-policy allkeys-lru\n"
            "→ OK\n"
            "INFO memory\n"
            "→ used_memory_human:1.02G"
        ),
        "example_output": (
            "(integer) 60\n"
            "(integer) 1\n"
            "(integer) -1\n"
            "OK\n"
            "(integer) 300\n"
            '1) "maxmemory-policy"\n'
            '2) "noeviction"\n'
            "OK\n"
            "used_memory_human:1.02G"
        ),
        "pitfalls": [
            "**TTL 到点内存不一定马上释放**：惰性 + 定期删除意味着过期 key 会滞留一段时间。排查内存异常时不要只看 key 数量，先用 `INFO memory` 看 `used_memory` 与 `mem_fragmentation_ratio`，再用 `redis-cli --bigkeys` 和 `MEMORY USAGE k` 找大 key，大 key 往往才是真凶。",
            "**`EXPIRE` 会被 `SET` 冲掉**：不带 `EX` 也不带 `KEEPTTL` 的 `SET` 会把过期时间清零，key 变成永久。这就是「缓存实例内存缓慢上涨」最常见的原因，代码审查时重点看这一行。",
            "**`volatile-*` 在「所有 key 都没 TTL」的实例上等于不淘汰**：找不到候选，行为退化成 `noeviction`，写满直接报错。用 `volatile-lru` 就必须在代码层面保证缓存 key 全都带 TTL，两边是不成文契约。",
            "**默认的 `noeviction` 在生产缓存里是个坑**：一旦内存打满，所有写请求（包括新缓存的写入）全部失败，故障会直接从 Redis 传导到业务。上线缓存实例第一件事就是显式把它改成 `allkeys-lru` 或 `allkeys-lfu`。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "一个**纯缓存**实例（所有数据丢了都能从数据库重建），`maxmemory-policy` 应该配成什么？",
                "options": [
                    "`allkeys-lru` 或 `allkeys-lfu`",
                    "`noeviction`",
                    "`volatile-ttl`",
                    "`allkeys-random`",
                ],
                "answer_index": 0,
                "explanation": (
                    "纯缓存意味着**任何 key 丢了都能重建**，所以要在全集里挑淘汰对象，用 `allkeys-lru`；"
                    "热点集中、想抗住偶发的全量扫描，就用 `allkeys-lfu`。"
                    "`noeviction` 一写满就报错；`volatile-ttl` 只从带 TTL 的 key 里挑，候选集不全；"
                    "`allkeys-random` 可能把最热的 key 随机删掉，命中率会崩。"
                ),
            },
            {
                "type": "choice",
                "stem": "关于 Redis 删除过期 key 的方式，下面哪个说法是对的？",
                "options": [
                    "惰性删除 + 定期随机采样删除，所以过期 key 可能还占着内存",
                    "Redis 给每个 key 都注册了定时器，时间一到立刻删除",
                    "只有惰性删除，只要没人访问就永远不删",
                    "只有定期删除，每次都会扫描全部设了 TTL 的 key",
                ],
                "answer_index": 0,
                "explanation": (
                    "惰性删除负责「被访问时顺手清理」，定期删除每秒 10 次、每次随机抽 20 个 key 清理，"
                    "用采样控制 CPU 开销。**不会给每个 key 挂定时器**，也**不会扫描全部 key**——"
                    "那样 CPU 直接被打满。这正解释了「TTL 到了内存还占着」的现象。"
                ),
            },
            {
                "type": "judge",
                "stem": "如果 `maxmemory-policy` 设为 `volatile-lru`，而实例里所有 key 都没有设置过期时间，那么内存打满后新写入会直接报错。",
                "answer": True,
                "explanation": (
                    "`volatile-*` 系列只在**带 TTL 的 key** 里找淘汰候选。一个候选都没有时它无从下手，"
                    "行为退化成 `noeviction`，于是返回 `OOM command not allowed`。"
                    "所以用 `volatile-lru` 的前提是：缓存 key 必须全部带 TTL。"
                ),
            },
            {
                "type": "blank",
                "stem": "`TTL k` 返回 `(integer) -1` 表示 key 存在但没有过期时间；那么返回 `___` 表示这个 key 已经不存在了。",
                "answer": "-2",
                "accept": ["-2"],
                "hint": "填一个负数",
                "explanation": "`-1` 是「存在但永不过期」，`-2` 是「key 不存在」。排查线上问题时靠这两个值区分「没设 TTL」和「key 被删了」。",
            },
            {
                "type": "short",
                "stem": "面试官：线上 Redis 内存快满了，你从哪几件事开始排查和治理？",
                "keywords": [
                    "INFO memory 看 used_memory",
                    "bigkeys 与 MEMORY USAGE",
                    "内存碎片率",
                    "maxmemory-policy 淘汰策略",
                    "给缓存 key 补 TTL",
                    "拆分实例或扩容",
                ],
                "reference": (
                    "第一步先看指标：`INFO memory` 里 `used_memory` 和 `maxmemory` 的差距、"
                    "`mem_fragmentation_ratio`（超过 1.5 说明碎片严重，可考虑重启或 `activedefrag`）。\n"
                    "第二步找大 key：`redis-cli --bigkeys` 扫类型分布，再对可疑 key 用 `MEMORY USAGE k` 看确切占用。\n"
                    "第三步看策略：确认 `maxmemory-policy` 不是默认的 `noeviction`，否则内存满就是写在报错而不是淘汰。\n"
                    "治理上，优先**给所有缓存 key 补上 TTL**、把大 key 拆小，其次是按业务拆分实例、最后才是扩容。"
                    "要记住：扩容只是延后问题，不设 TTL 的缓存迟早还会写满。"
                ),
                "explanation": "「大 key + 没设 TTL + 默认 noeviction」这三条能覆盖绝大多数线上内存事故。",
            },
        ],
    },
    {
        "code": "redis-06",
        "subject": "Redis",
        "stage": "持久化与高可用",
        "runner": "none",
        "title": "持久化 RDB 与 AOF 怎么选",
        "summary": "RDB 拍快照，AOF 记流水账",
        "definition": (
            "Redis 是内存数据库，重启后要把数据找回来，靠的就是 RDB 和 AOF 两套机制。\n\n"
            "**RDB（快照）**：把某一时刻的整个数据集写成二进制文件 `dump.rdb`。\n\n"
            "- `SAVE`：在主线程执行，**会阻塞整个 Redis**，生产禁用\n"
            "- `BGSAVE`：`fork` 出子进程写文件，主线程继续服务请求\n"
            "- 配置 `save 900 1 300 10 60 10000`：900 秒内至少 1 次修改、300 秒内 10 次、60 秒内 10000 次，任一满足就触发\n"
            "- 优点：文件紧凑、**恢复极快**，也适合做冷备和主从全量同步\n"
            "- 缺点：两次快照之间的写入会丢；`fork` 和数据量大时可能有秒级停顿\n\n"
            "**AOF（追加日志）**：把每条写命令追加到 `appendonly.aof`，重启时重放一遍命令。\n\n"
            "- `appendfsync always`：每条命令都 fsync，几乎不丢，但**吞吐明显下降**\n"
            "- `appendfsync everysec`：每秒 fsync 一次，**最多丢 1 秒数据，性能与安全兼顾，生产首选**\n"
            "- `appendfsync no`：交给操作系统刷盘，性能最好，丢多少完全不可控\n"
            "- **AOF 重写**：文件会越写越大，`BGREWRITEAOF` 把「100 次 INCR」压成一条 `SET k 100`\n\n"
            "**混合持久化**（Redis 4.0+，`aof-use-rdb-preamble`）：AOF 重写时前半段写 RDB 二进制快照、"
            "后半段追加增量命令。重启先加载快照再重放增量，**恢复快又丢得少**，是现在的默认推荐。\n\n"
            "**面试必须给出结论**：\n\n"
            "- 只当缓存、数据能从数据库重建 → 两个都可以关，性能最好\n"
            "- 既要持久化又要少丢 → **开 AOF + `everysec` + 混合持久化**，再用 RDB 定期做冷备\n"
            "- 只能二选一 → **选 AOF**，因为 RDB 丢的是「最后一次快照之后的全部数据」，窗口可能长达几分钟"
        ),
        "plain": (
            "RDB 像**下班前给整个办公室拍一张全景照**：拍的那一秒什么都在，照片小、一眼就能看全；"
            "但拍照之后发生的事照片里没有，而且拍照瞬间所有人都得站着不动一下（`fork` 的停顿）。\n\n"
            "AOF 像**把每个人的每个动作都记在流水账上**：改一个字就记一笔，恢复时照着账本重演一遍。"
            "账本一定比照片完整，但会越记越厚（所以需要 AOF 重写），重演一遍也比看照片慢。\n\n"
            "**混合持久化就是「先拍一张照片，再从拍照那一刻开始记流水账」**——恢复时先看照片把场景还原，"
            "再补上照片之后发生的动作，又快又全。所以生产上的标准配置是：AOF 打开、"
            "`everysec` 刷盘、开混合持久化，再让 RDB 定期产出快照去做异地备份。"
        ),
        "example": (
            "# 查看当前的持久化配置\n"
            "CONFIG GET save\n"
            '→ 1) "save"  2) "900 1 300 10 60 10000"\n'
            "CONFIG GET appendonly\n"
            '→ 1) "appendonly"  2) "no"\n'
            "CONFIG GET appendfsync\n"
            '→ 1) "appendfsync"  2) "everysec"\n'
            "CONFIG GET aof-use-rdb-preamble\n"
            '→ 1) "aof-use-rdb-preamble"  2) "yes"\n'
            "\n"
            "# 手动触发一次 RDB 快照（后台执行，不阻塞主线程）\n"
            "BGSAVE\n"
            "→ Background saving started\n"
            "\n"
            "# 手动触发 AOF 重写（把臃肿的命令压缩）\n"
            "BGREWRITEAOF\n"
            "→ Background append only file rewriting started\n"
            "\n"
            "# 看最近一次 RDB 是否成功\n"
            "INFO persistence\n"
            "→ rdb_last_bgsave_status:ok\n"
            "→ rdb_last_save_time:1758200000\n"
            "→ aof_enabled:0"
        ),
        "example_output": (
            '1) "save"\n'
            '2) "900 1 300 10 60 10000"\n'
            '1) "appendonly"\n'
            '2) "no"\n'
            '1) "appendfsync"\n'
            '2) "everysec"\n'
            '1) "aof-use-rdb-preamble"\n'
            '2) "yes"\n'
            "Background saving started\n"
            "Background append only file rewriting started\n"
            "rdb_last_bgsave_status:ok\n"
            "rdb_last_save_time:1758200000\n"
            "aof_enabled:0"
        ),
        "pitfalls": [
            "**`SAVE` 会阻塞整个 Redis**：它跑在主线程上，数据量大时几秒到几十秒完全不可用，所有请求一起超时。生产只允许用 `BGSAVE`，或者交给配置里的 `save` 规则自动触发。",
            "**`fork` 有内存和停顿代价**：`BGSAVE` 靠写时复制（COW），数据被大量修改时额外占用会接近翻倍。物理内存吃紧时 `BGSAVE` 可能失败甚至被 OOM Killer 杀掉，所以 `maxmemory` 一般不超过物理内存的 50%~60%，要留出余量。",
            "**开了 AOF 不等于不丢数据**：`appendfsync everysec` 在进程崩溃时最多丢 1 秒；只有 `always` 才接近不丢，代价是吞吐下降。面试别说成「开了 AOF 就绝对不丢」。",
            "**AOF 文件损坏会导致启动失败**：进程被 kill、磁盘写满都可能让最后一条命令写坏。可用 `redis-check-aof --fix appendonly.aof` 修复；平时必须监控磁盘剩余空间和 `rdb_last_bgsave_status` / `aof_last_bgrewrite_status` 这两个指标。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "生产环境既要「尽量少丢数据」又要「性能可接受」，AOF 的 `appendfsync` 应该配成什么？",
                "options": ["`everysec`", "`always`", "`no`", "关闭 AOF，只留 RDB"],
                "answer_index": 0,
                "explanation": (
                    "`everysec` 每秒 fsync 一次，**最多丢 1 秒**，是性能和安全的标准平衡点，也是生产首选。"
                    "`always` 每条命令都落盘，吞吐掉得厉害；`no` 由操作系统决定，可能丢几十秒；"
                    "关掉 AOF 只留 RDB，丢失窗口能到几分钟，和题目要求相反。"
                ),
            },
            {
                "type": "choice",
                "stem": "关于 RDB 和 AOF 的区别，下面哪个说法是对的？",
                "options": [
                    "RDB 是某一时刻的全量快照，恢复快但会丢快照之后的数据；AOF 是写命令日志，丢得少但恢复慢、文件会变大",
                    "RDB 记录的是每条写命令，AOF 记录的是全量快照",
                    "两者都是实时同步的，宕机时都不会丢任何数据",
                    "AOF 的文件一定比 RDB 文件更小",
                ],
                "answer_index": 0,
                "explanation": (
                    "B 把两者说反了。C 错在「实时」——RDB 是周期性快照，AOF 的 `everysec` 也有最多 1 秒的窗口。"
                    "D 错在文件大小：AOF 记录的是命令流，相同数据量下通常比紧凑的二进制 RDB 大，"
                    "所以 AOF 需要重写、也需要混合持久化来压缩体积。"
                ),
            },
            {
                "type": "judge",
                "stem": "`SAVE` 和 `BGSAVE` 都是 `fork` 子进程在后台做快照，不会影响主线程处理请求。",
                "answer": False,
                "explanation": (
                    "`SAVE` 是在**主线程**里同步执行的，整个 Redis 会被卡住直到快照写完；"
                    "只有 `BGSAVE` 才 `fork` 子进程在后台干。这也是生产环境禁用 `SAVE` 的原因。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全命令：在后台重写 AOF 文件，把 100 条 `INCR k` 压缩成一条 `SET k 100`：\n___",
                "answer": "BGREWRITEAOF",
                "accept": ["bgrewriteaof"],
                "hint": "一个命令名，12 个字母，以 BG 开头",
                "explanation": (
                    "`BGREWRITEAOF` 后台重写，把冗余命令压缩成最小集合，同时释放文件体积。"
                    "Redis 4.0+ 重写出来的就是「RDB 头部 + 增量 AOF」的混合格式。"
                ),
            },
            {
                "type": "short",
                "stem": "面试官：Redis 的 RDB 和 AOF 你怎么选？生产环境具体怎么配？",
                "keywords": [
                    "RDB 全量快照恢复快",
                    "AOF everysec 最多丢 1 秒",
                    "混合持久化",
                    "丢失窗口",
                    "纯缓存可以都关",
                    "fork 与磁盘成本",
                ],
                "reference": (
                    "先分清两者的代价：RDB 是**周期性全量快照**，文件紧凑、恢复快，"
                    "但丢的是「最后一次快照之后的全部写入」，窗口可能几分钟；"
                    "AOF 是**写命令日志**，`everysec` 刷盘最多丢 1 秒，代价是恢复要重放、文件需要重写。\n"
                    "生产上的标准答案是：**开 AOF + `appendfsync everysec` + 开 `aof-use-rdb-preamble` 混合持久化**，"
                    "同时保留 RDB 定期快照做冷备和主从全量同步用的基础。"
                    "如果这个实例纯粹做缓存、数据丢了能从数据库重建，那两个都可以关掉，性能最好。\n"
                    "另外要主动提一句：`fork` 做快照需要额外内存，日志写的是磁盘，所以要给 Redis 留足物理内存余量、"
                    "并监控磁盘剩余空间，否则快照会直接失败。"
                ),
                "explanation": "这题的关键是**给出结论**：everysec + 混合持久化，而不是两边都描述一遍就结束。",
            },
        ],
    },
    # ---------------- 阶段：缓存实战 ----------------
    {
        "code": "redis-07",
        "subject": "Redis",
        "stage": "缓存实战",
        "runner": "none",
        "title": "缓存穿透、击穿、雪崩",
        "summary": "三个坑，三套解法都不一样",
        "definition": (
            "这三个词经常被混着说，**第一句话就要把区别摆清楚**：\n\n"
            "**缓存穿透**：请求的 key **在缓存和数据库里都不存在**（比如拿不存在的 id 一直刷）。\n"
            "缓存挡不住，每次请求都打到数据库。\n\n"
            "- 解法一：**布隆过滤器**（Bloom Filter）。把所有存在的 key 预加载进去，请求先过过滤器："
            "说「不存在」就直接返回，说「可能存在」才去查缓存和 DB。注意它有**假阳性**"
            "（可能误判为存在），但没有假阴性——只要它说不存在，就一定不存在\n"
            "- 解法二：**缓存空值**。查不到就写 `SET k \"\" EX 60`，把空结果也缓存起来，用短 TTL 兜底。"
            "实现最简单，代价是攻击者用随机 key 会撑大内存\n"
            "- 兜底：接口层做参数校验（id 必须是正整数、长度限制）+ 限流，从源头减少无效请求\n\n"
            "**缓存击穿**：**某个热点 key 刚好过期**，这一瞬间大量并发请求同时落到数据库。\n"
            "注意 key 是存在的，只是缓存里过期了。\n\n"
            "- 解法一：**互斥锁**。只放一个请求去查 DB 重建缓存，其他请求稍等再读缓存\n"
            "（`SET lock:xx NX PX 3000` 加锁，Lua 脚本释放）\n"
            "- 解法二：**逻辑过期**。value 里带一个 `expire_at` 字段，物理上永不过期；"
            "读到发现逻辑过期时，先返回旧值，同时异步起任务更新。**用一致性换可用性**，适合超热点数据\n\n"
            "**缓存雪崩**：**大批 key 在同一时间过期**（比如凌晨统一预热、TTL 都设 1 小时），"
            "或者 **Redis 整个实例挂了**，请求全砸到数据库。\n\n"
            "- 解法一：**随机化过期时间**。`EX = 基础时间 + 随机(0, 300)`，把过期点打散\n"
            "- 解法二：**多级缓存**（本地 Caffeine + Redis），Redis 挂掉时本地还能挡一阵\n"
            "- 解法三：**熔断降级 + 限流**，保证数据库至少不被打死；热点数据再加互斥重建\n\n"
            "面试可以照着这张表答：\n\n"
            "| 问题 | 数据在不在 | 触发条件 | 主解法 |\n"
            "| --- | --- | --- | --- |\n"
            "| 穿透 | 缓存和 DB 都没有 | 恶意刷不存在的 key | 布隆过滤器 / 缓存空值 |\n"
            "| 击穿 | 有，但缓存里过期了 | 单个热点 key 过期 | 互斥锁 / 逻辑过期 |\n"
            "| 雪崩 | 有，但一大批同时失效 | 大量 key 同时过期或 Redis 宕机 | 随机 TTL / 多级缓存 / 熔断 |"
        ),
        "plain": (
            "把缓存想成**便利店门口的保温箱**，数据库是想吃现做的后厨。\n\n"
            "**穿透**：来的人点了一个**根本不存在的菜**，保温箱里没有、后厨也没有，可他还每分钟来问一次，"
            "服务员每次白跑一趟后厨。→ 那就直接在门口贴张纸条「这个菜没有」（缓存空值），"
            "或者雇个门卫一眼认出生面孔（布隆过滤器）。\n\n"
            "**击穿**：招牌菜**刚卖完的那一秒**，十几个客人同时要，全都冲进后厨。→ 门口挂个牌子"
            "「后厨正在做，一个人进去催就够了」（互斥锁），其他人稍等；或者干脆先把昨天剩的端出来"
            "（逻辑过期，返回旧值）。\n\n"
            "**雪崩**：**整个保温箱突然断电**，或者所有菜约定好同一分钟一起下架，瞬间所有需求挤进后厨。"
            "→ 别让菜同时下架（随机 TTL），再准备一个备用小冰箱（多级缓存），实在不行先关门限流"
            "（熔断降级）。三件事的**触发条件完全不同，所以解法也不能互相套用**。"
        ),
        "example": (
            "# 1. 缓存穿透：查不到就缓存空值，用短 TTL 防止垃圾 key 撑满内存\n"
            "GET product:999999\n"
            "→ (nil)\n"
            'SET product:999999 "" EX 60\n'
            "→ OK\n"
            "GET product:999999\n"
            '→ ""          # 第二次就被空值挡住，不再打到数据库\n'
            "\n"
            "# 2. 缓存击穿：互斥锁，只放一个请求去重建缓存\n"
            'SET lock:product:1 "uuid-abc" NX PX 3000\n'
            "→ OK\n"
            '# 拿到锁的请求去查 DB 并回写缓存，TTL 再加一点随机值\n'
            'SET product:1 "hot-product-json" EX 3600\n'
            "→ OK\n"
            "# 释放锁要保证「只删自己的锁」，用 Lua 原子执行\n"
            'EVAL "if redis.call(\'get\',KEYS[1])==ARGV[1] then return redis.call(\'del\',KEYS[1]) else return 0 end" 1 lock:product:1 uuid-abc\n'
            "→ (integer) 1\n"
            "\n"
            "# 3. 缓存雪崩：TTL 加随机值，把过期时间点打散\n"
            'SET product:1 "..." EX 3600\n'
            "→ OK\n"
            'SET product:2 "..." EX 3617\n'
            "→ OK\n"
            'SET product:3 "..." EX 3583\n'
            "→ OK"
        ),
        "example_output": (
            "(nil)\n"
            "OK\n"
            '""\n'
            "OK\n"
            "OK\n"
            "(integer) 1\n"
            "OK\n"
            "OK\n"
            "OK"
        ),
        "pitfalls": [
            "**别把三个词说反**：穿透是「数据压根不存在」，击穿是「单个热点 key 过期」，雪崩是「一大批 key 同时过期或 Redis 挂了」。面试第一句就把区别摆出来，比后面答得再细都加分。",
            "**缓存空值必须给短 TTL**：写 `SET k \"\" EX 60`，绝不能缓存成永久空值。否则攻击者换一批随机 key，Redis 内存很快被这些空值撑满，穿透没治住反而先爆了内存。",
            "**互斥锁必须带 `PX`，而且只能用 Lua 释放**：不带过期时间的锁在进程崩溃后永远不释放；而 `GET` 之后再 `DEL` 是两步操作，中间锁可能已经超时被别人抢走，你的 `DEL` 就误删了别人的锁。",
            "**「先删缓存再更新数据库」会把旧值回填成脏数据**：删除缓存后、更新 DB 前的这个窗口里，读请求会把旧值重新写进缓存，而且长期不失效。业界主流是 `Cache Aside`——**先更新数据库，再删除缓存**，删除失败用消息队列或订阅 binlog 重试补偿，延迟双删只是缓解不是根治。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面哪种情况属于「缓存击穿」？",
                "options": [
                    "某个热点 key 过期的瞬间，大量并发请求同时打到数据库",
                    "请求的 key 在缓存和数据库里都不存在",
                    "大量 key 在同一时刻集中过期，请求全部落到数据库",
                    "Redis 实例宕机导致所有请求直接落到数据库",
                ],
                "answer_index": 0,
                "explanation": (
                    "击穿的关键词是「**单个热点 key 过期**」，解法是互斥锁或逻辑过期。"
                    "B 是穿透（解法是布隆过滤器 / 缓存空值）；"
                    "C 和 D 都是雪崩（解法是随机 TTL、多级缓存、熔断降级）。四个选项正好把三个概念摆在一起，别选错。"
                ),
            },
            {
                "type": "choice",
                "stem": "面试官：缓存和数据库怎么保证一致性？先删缓存还是先更新数据库？",
                "options": [
                    "先更新数据库，再删除缓存（Cache Aside），失败用消息队列或 binlog 补偿",
                    "先删除缓存，再更新数据库，这是业界标准做法",
                    "先更新缓存，再靠异步任务慢慢刷回数据库",
                    "加分布式锁让所有读请求排队，就可以不用考虑删缓存",
                ],
                "answer_index": 0,
                "explanation": (
                    "**先更新 DB、再删缓存**（Cache Aside）是主流：删缓存失败的概率远低于「删完缓存到更新完 DB」"
                    "这段时间里被读请求回填旧值，所以它的不一致窗口更小。"
                    "B 的顺序正好会踩那个回填窗口，脏数据可能长期存在；"
                    "C 让缓存和 DB 双写，冲突更多；D 理论上能强一致，但把读也串行化了，性能和可用性代价太大，"
                    "一般业务接受**最终一致**就够了。要补强就上延迟双删或订阅 binlog 重试。"
                ),
            },
            {
                "type": "judge",
                "stem": "布隆过滤器判断某个 key「不存在」，这个结论是可靠的；判断「存在」则可能是误判。",
                "answer": True,
                "explanation": (
                    "布隆过滤器基于多个哈希位，**没有假阴性、只有假阳性**："
                    "说不存在就一定不存在，说存在有可能是哈希碰撞造成的误判。"
                    "所以它的用法是「先挡掉肯定不存在的请求」，剩下的一小部分误判交给缓存空值兜底。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全命令，缓存一个空值来防止缓存穿透（要求 60 秒后自动失效）：\nSET product:999999 \"\" ___ 60",
                "answer": "EX",
                "accept": ["ex"],
                "hint": "两个字母的过期参数（大写）",
                "explanation": (
                    "`EX 60` 表示 60 秒后过期（`PX` 是毫秒）。空值也必须带过期时间，"
                    "否则随机 key 会不断堆积、把内存吃满——那是把穿透问题换成了内存问题。"
                ),
            },
            {
                "type": "short",
                "stem": "面试官：缓存穿透、缓存击穿、缓存雪崩分别是什么？各自怎么治？",
                "keywords": [
                    "穿透=数据不存在",
                    "布隆过滤器或缓存空值",
                    "击穿=热点 key 过期",
                    "互斥锁或逻辑过期",
                    "雪崩=大量 key 同时失效或宕机",
                    "随机 TTL 加多级缓存加熔断",
                ],
                "reference": (
                    "**穿透**是请求的数据在缓存和数据库里都不存在，缓存形同虚设，"
                    "解法是布隆过滤器先把肯定不存在的请求挡掉，再用短 TTL 缓存空值兜底，配合接口参数校验和限流。\n"
                    "**击穿**是单个热点 key 过期的瞬间，大量并发同时查库重建，"
                    "解法是用互斥锁只放一个请求去重建，或者用逻辑过期返回旧值、异步更新。\n"
                    "**雪崩**是大批 key 同时过期，或者 Redis 整个挂掉导致请求全部涌向数据库，"
                    "解法是给 TTL 加随机值打散过期点、加本地缓存做多级兜底、再上熔断降级和限流保住数据库。\n"
                    "一句话总结区别：**穿透是数据不存在，击穿是一个热点 key 过期，雪崩是一大批 key 同时失效**。"
                ),
                "explanation": "这题考的就是「分得清」——先把三者定义说准，再各给一套解法，顺序别串。",
            },
        ],
    },
    {
        "code": "redis-08",
        "subject": "Redis",
        "stage": "缓存实战",
        "runner": "none",
        "title": "分布式锁与主从哨兵集群",
        "summary": "锁要原子，集群要分片",
        "definition": (
            "**分布式锁**用一条命令实现：`SET lock:order:1001 <uuid> NX PX 30000`。三个要点缺一不可：\n\n"
            "- `NX`：保证互斥，只有一个客户端能写进去\n"
            "- `PX 30000`：过期时间兜底，防止客户端崩溃后锁永远不释放\n"
            "- `value` 必须放**自己的唯一标识**（UUID / 请求 id），释放时先判断「是不是我的锁」再删\n\n"
            "释放锁必须用 **Lua** 保证原子：\n\n"
            "```\n"
            "if redis.call('get', KEYS[1]) == ARGV[1] then\n"
            "    return redis.call('del', KEYS[1])\n"
            "else\n"
            "    return 0\n"
            "end\n"
            "```\n\n"
            "为什么不能 `GET` 之后再 `DEL`：两条命令之间锁可能刚好超时被别人拿走，你的 `DEL` 就删了别人的锁。"
            "Lua 脚本在 Redis 里是**整体原子执行**的，中间不会插入其他命令。\n\n"
            "生产上直接用 **Redisson**：封装了 `tryLock`、Lua 释放，还有**看门狗**（watchdog）——"
            "业务没跑完就自动续期（默认 30 秒一次），避免「业务还在跑、锁已经过期」的尴尬。\n\n"
            "关于 **Redlock**：它向多个独立的 Redis 实例申请锁，多数成功才算拿到。"
            "这套算法有争议（Martin Kleppmann 质疑它依赖时钟和 GC 停顿），**面试提到即可，别当银弹**。"
            "真要强一致，用 ZooKeeper 的临时顺序节点，或者数据库唯一索引。\n\n"
            "**主从 / 哨兵 / 集群**：\n\n"
            "- **主从复制**：从节点 `REPLICAOF` 连上主节点。首次同步走**全量**——主节点 `BGSAVE` 出 RDB 传给从节点；"
            "之后走**增量**——主节点把写命令写进 repl backlog 发给从节点重放。复制是**异步**的，"
            "所以从节点读到旧数据是常态（这就是 CAP 里偏向 AP 的原因）。主节点挂了需要人工介入。\n"
            "- **哨兵（Sentinel）**：一组独立进程监控主从，主节点宕机后**自动选主并切换**，"
            "同时把新主节点地址通知客户端。解决「不能自动故障转移」，但**不解决容量问题**，单机内存上限还在。\n"
            "- **集群（Cluster）**：数据分片，一共 **16384 个 slot**，`slot = CRC16(key) % 16384`，每个主节点负责一段，"
            "节点之间用 gossip 通信，支持多主多从。解决容量和吞吐，代价是**跨 key 命令**"
            "（`MSET` / `MGET` / `SINTER`）要求所有 key 在同一个 slot，得用 hash tag `{user1}:name` 把它们绑在一起。\n\n"
            "**一句话总结**：主从解决**读扩展和数据冗余**，哨兵解决**自动故障转移**，Cluster 解决**容量和写扩展**。"
        ),
        "plain": (
            "分布式锁就像**宿舍洗漱间门上挂的牌子**：谁进去谁把牌子挂上（`NX`），出来摘掉。牌子必须写名字"
            "——不然别人等太久以为你走了，把自己的牌子挂上去，你出来时顺手一摘，摘的是**别人的牌子**。"
            "还要给牌子设一个自动脱落的时间（`PX`），万一你晕在里面，牌子也不会永远挂着。\n\n"
            "**主从复制**像**师傅带徒弟**：徒弟先抄一遍师傅的全部笔记（RDB 全量同步），之后师傅每写一笔就喊一声，"
            "徒弟跟着记（增量同步）。喊话有延迟，所以徒弟的本子总是略旧一点。\n\n"
            "**哨兵**是**门口的宿管**：发现师傅不在，马上把徒弟扶正，并通知所有人「以后找新师傅」——"
            "但它不增加人手，一个人还是只有一双手。\n\n"
            "**Cluster** 是**直接把活儿分给多个人**：一共 16384 个抽屉，按 key 分配，每人管一段。"
            "好处是总容量和吞吐都上去了；代价是「一个请求要同时翻好几个人的抽屉」变得很麻烦——"
            "所以同一类的 key 得想办法分给同一个人。"
        ),
        "example": (
            "# 加锁：NX 保证互斥，PX 保证不会死锁，value 必须是自己的唯一标识\n"
            'SET lock:order:1001 "uuid-abc-123" NX PX 30000\n'
            "→ OK\n"
            "# 另一个客户端来抢，抢不到\n"
            'SET lock:order:1001 "uuid-def-456" NX PX 30000\n'
            "→ (nil)\n"
            "TTL lock:order:1001\n"
            "→ (integer) 30\n"
            "\n"
            "# 释放锁：先判断「是不是我的」，再删，用 Lua 保证两步原子\n"
            'EVAL "if redis.call(\'get\',KEYS[1])==ARGV[1] then return redis.call(\'del\',KEYS[1]) else return 0 end" 1 lock:order:1001 uuid-abc-123\n'
            "→ (integer) 1\n"
            "\n"
            "# Cluster：16384 个 slot，key 落在哪个槽由 CRC16(key) % 16384 决定\n"
            "CLUSTER INFO\n"
            "→ cluster_enabled:1\n"
            "CLUSTER KEYSLOT order:1001\n"
            "→ (integer) 866\n"
            "CLUSTER KEYSLOT order:1002\n"
            "→ (integer) 12345\n"
            "# 用 hash tag 把两个 key 绑到同一个 slot，才能一起用 MGET\n"
            'CLUSTER KEYSLOT "{order}:1001"\n'
            "→ (integer) 866\n"
            'CLUSTER KEYSLOT "{order}:1002"\n'
            "→ (integer) 866"
        ),
        "example_output": (
            "OK\n"
            "(nil)\n"
            "(integer) 30\n"
            "(integer) 1\n"
            "cluster_enabled:1\n"
            "(integer) 866\n"
            "(integer) 12345\n"
            "(integer) 866\n"
            "(integer) 866"
        ),
        "pitfalls": [
            "**释放锁必须是「判断 + 删除」的原子操作**：`GET` 再 `DEL` 两步之间有窗口期，锁可能已经超时易主，你的 `DEL` 就删掉了别人的锁，互斥直接失效。用 Lua 或 Redisson，别自己手写两步。",
            "**锁的过期时间要大于业务执行时间**：TTL 设小了，业务还没跑完锁就自动释放，两个线程会同时进临界区。解决办法是加长 TTL，或者用 Redisson 看门狗自动续期；**不要靠「业务里手动判断锁还在不在」来兜底**，那本身就有竞态。",
            "**主从架构下的分布式锁天然不安全**：加锁写在主节点，还没异步同步到从节点时主节点就宕机，从节点升主后锁没了，别的客户端能重复加锁。要求严格的场景用 Redlock（仍有争议，别当银弹）、ZooKeeper 或数据库唯一约束。",
            "**Cluster 不支持跨 slot 的多 key 命令**：`MGET`、`MSET`、`SINTER` 只要 key 不在同一槽就报 `CROSSSLOT Keys in request don't hash to the same slot`。用 hash tag（`{user1}:name`、`{user1}:age`）把它们绑到同一槽，或者在应用层拆成多次单 key 请求。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": "用 Redis 实现分布式锁，下面哪个写法是正确的？",
                "options": [
                    "`SET lock:o1 <uuid> NX PX 30000`",
                    "`SETNX lock:o1 1` 之后再 `EXPIRE lock:o1 30`",
                    "`SET lock:o1 1`",
                    "先 `GET lock:o1` 判断为空，再 `SET lock:o1 1`",
                ],
                "answer_index": 0,
                "explanation": (
                    "`SET NX PX` 一条命令同时做到互斥和防死锁，是官方推荐写法。"
                    "B 是两步操作，中间进程崩溃就留下一把**永不过期的锁**；"
                    "C 既没有互斥也会永久持有；D 的「判断」和「设置」之间存在竞态，两个客户端可能同时通过判断。"
                ),
            },
            {
                "type": "choice",
                "stem": "Redis 的主从复制默认是异步的，这对业务意味着什么？",
                "options": [
                    "主节点写成功后从节点可能还没同步到，读到旧数据是正常现象",
                    "从节点的数据和主节点永远完全一致，可以放心做读写分离",
                    "主节点宕机后从节点会自动升主，不需要哨兵介入",
                    "从节点可以接受写请求，用来分担写压力",
                ],
                "answer_index": 0,
                "explanation": (
                    "异步复制意味着主从之间存在一段**延迟窗口**，所以 Redis 在 CAP 里偏向 AP，"
                    "对一致性敏感的场景（比如「写入后立刻读」）要强制读主节点。"
                    "故障转移需要哨兵；从节点默认只读，写请求会返回 `READONLY You can't write against a read only replica`。"
                ),
            },
            {
                "type": "judge",
                "stem": "Redis Cluster 一共有 16384 个 slot，`{user1}:name` 和 `{user1}:age` 这两个 key 一定落在同一个 slot，所以可以放在一条 `MGET` 里执行。",
                "answer": True,
                "explanation": (
                    "带 `{}` 时只用花括号里的内容计算哈希，所以这两个 key 的 `CRC16` 结果相同、必然同槽，"
                    "跨 key 命令就不会报 `CROSSSLOT`。这就是 hash tag 的用途——"
                    "把「必须一起操作」的 key 人为绑到同一个节点上。"
                ),
            },
            {
                "type": "blank",
                "stem": "释放分布式锁时，为了保证「判断是不是自己的锁」和「删除」两步原子执行，要使用哪种脚本？\nEVAL \"...\" 1 lock:order:1001 uuid-abc",
                "answer": "Lua",
                "accept": ["lua", "LUA"],
                "hint": "三个字母的脚本语言",
                "explanation": (
                    "Lua 脚本在 Redis 里是**整体原子执行**的，中间不会插入其他命令，"
                    "所以 `get` 判断和 `del` 删除之间不存在窗口期。生产上直接用 Redisson 已经封装好了。"
                ),
            },
            {
                "type": "short",
                "stem": "面试官：主从、哨兵、Cluster 有什么区别？各自解决什么问题？什么时候你会从主从换到 Cluster？",
                "keywords": [
                    "主从=读写分离与数据冗余",
                    "异步复制有延迟",
                    "哨兵=自动故障转移",
                    "哨兵不解决容量",
                    "Cluster=16384 slot 分片",
                    "跨 slot 命令受限",
                ],
                "reference": (
                    "**主从复制**解决读扩展和数据冗余：从节点 `REPLICAOF` 主节点，全量走 RDB、增量走命令流，"
                    "复制是异步的所以从节点有延迟，主节点宕机需要人工介入。\n"
                    "**哨兵**在主从之上加了自动故障转移：多个哨兵进程监控集群，主节点挂了自动选主、"
                    "通知客户端新地址，但它**不解决容量和写吞吐**——单机内存上限依旧。\n"
                    "**Cluster** 是分片方案：16384 个 slot 分散到多个主节点，每个主节点再挂从节点，"
                    "同时解决了容量和写扩展，代价是跨 slot 的 `MGET`/`MSET` 会报 `CROSSSLOT`，需要 hash tag。\n"
                    "判断标准很直接：**单机内存装得下、QPS 也够，就主从 + 哨兵；"
                    "一旦数据量超出单机内存上限、或写入 QPS 顶不住，就该上 Cluster**。"
                ),
                "explanation": "这题的关键是给出「什么时候升级」的判断标准，光背三个定义拿不到高分。",
            },
        ],
    },
]
