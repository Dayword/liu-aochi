"""MySQL 10 课 + Redis 8 课在鸭先知项目里的真实落点。

库表结构：database/schema_mysql.sql（23 张表、43 个索引/唯一键）
数据访问：database/db_mysql.py（约 3900 行，全部手写 SQL，没有 ORM）
缓存：core/cache.py（Redis String + TTL）
"""

from .learn_project_base import absent, choice, judge, used

REFS: dict[str, dict] = {
    # ---------------- MySQL ----------------
    "mysql-01": used(
        "database/schema_mysql.sql", "18-31",
        "CREATE TABLE IF NOT EXISTS users (\n    id            INT UNSIGNED NOT NULL AUTO_INCREMENT,\n    username      VARCHAR(64)  NOT NULL,\n    password_hash VARCHAR(255) NOT NULL,\n    nickname      VARCHAR(64)  DEFAULT '',\n    role          VARCHAR(20)  DEFAULT 'user',\n    wx_openid     VARCHAR(64)  DEFAULT NULL COMMENT '微信小程序openid',\n    pwd_set       TINYINT      DEFAULT 0 COMMENT '1=用户自设过登录密码 / 0=密码为系统占位随机串',\n    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,\n    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\n    PRIMARY KEY (id),\n    UNIQUE KEY uk_username (username)，\n    UNIQUE KEY uk_wx_openid (wx_openid)",
        "项目的用户表：主键自增 + 唯一键约束 + 时间戳自动维护。",
        "每个类型选择都有理由：主键用 `INT UNSIGNED`（无符号够用且范围翻倍）；`VARCHAR(64)` 而不是 TEXT，"
        "因为用户名短、放进行内能走覆盖索引；布尔语义用 `TINYINT`（MySQL 没有真正的 bool）；"
        "时间用 `DATETIME DEFAULT CURRENT_TIMESTAMP` 让数据库兜住，应用忘了赋值也不会插进空时间。"
        "最值得学的是 `updated_at ... ON UPDATE CURRENT_TIMESTAMP`——更新时间交给数据库，"
        "避免每个 UPDATE 语句都手动写一遍、还容易漏。",
        [
            choice("项目里用 TINYINT 存「是否自设过密码」，主要原因是什么？",
                   ["MySQL 没有布尔类型，TINYINT 是最省的替代", "TINYINT 能存中文", "为了兼容 Redis", "TINYINT 可以自动自增"],
                   0, "MySQL 的 BOOL 只是 TINYINT(1) 的别名，实际存储就是整数。用 TINYINT 明确表达这是 0/1 标志位。"),
            judge("`ON UPDATE CURRENT_TIMESTAMP` 能让数据库在每次 UPDATE 时自动刷新更新时间。", 1,
                  "对。这样应用层不用手动维护 updated_at，也不会因为漏写而拿到过期时间。"),
        ],
    ),
    "mysql-02": used(
        "database/db_mysql.py", "1106-1108",
        'cur.execute(\n    "SELECT * FROM chat_sessions WHERE user_id = %s ORDER BY last_message_at DESC LIMIT %s",\n    (user_id, limit)\n)',
        "按用户查会话列表，按最后消息时间倒序取前几条。",
        "`%s` 是**参数占位符**，不是字符串拼接——pymysql 会把参数单独发给服务端做转义，"
        "这是防 SQL 注入的根本手段。千万别写 `f\"... WHERE user_id = {user_id}\"`，那是把用户输入直接拼进 SQL。"
        "执行顺序上，WHERE 先筛行、ORDER BY 再排序、LIMIT 最后截断，所以能走 `idx_user_id` 索引把候选集缩小后才有排序成本。"
        "`SELECT *` 在这个项目里用得很多，方便但会多传无用字段；列多、行多时应该显式列出需要的列。",
        [
            choice("SQL 里用 `WHERE user_id = %s` 传参，相比 f-string 拼接，核心好处是？",
                   ["执行更快", "参数不参与 SQL 解析，从根本上防注入", "能自动建索引", "支持中文"],
                   1, "参数化查询让数据永远只是数据，不会被当成 SQL 语法解析，注入无从下手。"),
            judge("`SELECT *` 在只需要两三个字段时也没有任何代价。", 0,
                  "错。会多传数据、破坏覆盖索引（无法只读索引就返回）、表结构变动时也容易出隐性 bug。"),
        ],
    ),
    "mysql-03": used(
        "database/db_mysql.py", "1029-1032",
        '"SELECT id, username, nickname, phone, role, created_at, "\n"(wx_openid IS NOT NULL AND wx_openid <> \'\') AS has_wx "\nf"FROM users{sql_where} ORDER BY id LIMIT %s OFFSET %s",\nargs + [limit, (page - 1) * limit]',
        "后台用户列表的分页查询：每页 limit 条，跳过前 (page-1)*limit 条。",
        "`LIMIT n OFFSET m` 的语义是「跳过 m 行，取 n 行」。问题在于 **m 越大越慢**："
        "数据库必须先把前 m 行读出来再扔掉，翻到第 1000 页时等于白扫 2 万行。这就是「深分页」。"
        "改法有两种：① 游标分页 `WHERE id > 上一页最后一个 id ORDER BY id LIMIT 20`，走索引直接定位，恒定快；"
        "② 延迟关联 `JOIN (SELECT id FROM users ORDER BY id LIMIT 20 OFFSET 20000) t USING(id)`，先在索引上翻页再回表。"
        "注意这里 `ORDER BY id` 刚好是主键，还算能走索引；如果按非索引字段排序，深分页会更糟。",
        [
            choice("`LIMIT 20 OFFSET 20000` 慢的根本原因是什么？",
                   ["返回的数据太多", "数据库要先扫过并丢弃前 20000 行", "OFFSET 不能超过一万", "排序算法退化成冒泡"],
                   1, "OFFSET 不是「直接跳到第 20001 行」，而是逐行计数丢弃，跳过的行数越多越慢。"),
            judge("把深分页改造成 `WHERE id > 上一页最后一个 id` 的游标分页，可以让翻页耗时基本恒定。", 1,
                  "对。它靠索引直接定位起点，不依赖 OFFSET 计数；代价是不能随机跳到第 N 页。"),
        ],
    ),
    "mysql-04": used(
        "database/db_mysql.py", "1667",
        '"SELECT intent, COUNT(*) as cnt FROM chat_messages WHERE role=\'user\' GROUP BY intent"',
        "统计每种意图各被问了多少次，用于运营看板。",
        "`GROUP BY` 把行按 intent 分桶，`COUNT(*)` 数每个桶的行数——这就是「分组聚合」的全部。"
        "SQL 的执行顺序是 FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY，"
        "所以 WHERE 里不能写聚合函数（那时还没分组），过滤聚合结果要用 HAVING。"
        "性能上，如果 intent 上有索引，可以走索引扫描避免临时表排序；没有索引就会看到 `Using temporary; Using filesort`。",
        [
            choice("想筛选「出现次数大于 100 的意图」，条件应该写在哪里？",
                   ["WHERE cnt > 100", "HAVING cnt > 100", "ORDER BY cnt > 100", "GROUP BY cnt > 100"],
                   1, "WHERE 在分组前执行，拿不到聚合结果；HAVING 在分组后过滤，才能用 COUNT(*) 这类聚合值。"),
            judge("`SELECT intent, COUNT(*) FROM chat_messages GROUP BY intent` 里，SELECT 的 intent 必须在 GROUP BY 中出现。", 1,
                  "对（严格模式下）。否则数据库不知道该取这一组里哪一行的值，ONLY_FULL_GROUP_BY 会直接报错。"),
        ],
    ),
    "mysql-05": used(
        "database/db_mysql.py", "1937-1939",
        "FROM card_orders o\nLEFT JOIN users u ON u.id = o.user_id\nLEFT JOIN user_cards uc ON uc.order_no = o.order_no",
        "查卡订单时顺带带出用户信息和卡信息，避免应用层再发两次查询。",
        "`LEFT JOIN` 保留左表所有行，右表匹配不上就用 NULL 填充——这正好对应「订单一定有，用户可能已注销」。"
        "换成 `INNER JOIN` 就会把「用户已删除」的订单整条丢掉，报表数字会比实际少，这是最典型的 JOIN 事故。"
        "连接条件写在 ON 里，过滤条件写在 WHERE 里，两者对 LEFT JOIN 不等价："
        "把 `u.status = 1` 写进 WHERE，会让 NULL 行被过滤掉，LEFT JOIN 退化成 INNER JOIN。"
        "另外 JOIN 的列必须有索引（这里是主键和唯一键），否则每行都要全表扫，行数一多就是灾难。",
        [
            choice("`LEFT JOIN` 和 `INNER JOIN` 的关键区别是？",
                   ["LEFT JOIN 更快", "LEFT JOIN 保留左表全部行，匹配不上补 NULL", "INNER JOIN 不支持多表", "两者等价"],
                   1, "LEFT 保留左表全集，INNER 只保留两边都匹配上的行。统计类查询里选错会少算数据。"),
            judge("对 LEFT JOIN 的右表加 WHERE 条件（如 WHERE u.status=1），不会影响左表行的保留。", 0,
                  "错。WHERE 在连接之后过滤，会把右表为 NULL 的行一并筛掉，效果等同于 INNER JOIN。要保留就用 ON 里加条件。"),
        ],
    ),
    "mysql-06": absent(
        "FROM consumption_orders o\nLEFT JOIN users u ON u.id = o.user_id\nLEFT JOIN user_cards uc ON uc.order_no = o.order_no",
        "项目里 0 处 `UNION`、0 处 `IN (SELECT ...)` 形式的子查询：需要「拼数据」的地方一律用 JOIN。",
        "子查询和 UNION 不是不能用，而是**能用 JOIN 表达的就不该用子查询**——"
        "相关子查询会对每一行执行一次内层查询（N+1 的 SQL 版），而优化器对 JOIN 的处理成熟得多。"
        "`IN (SELECT ...)` 在 MySQL 8 里通常会被改写成半连接，但老版本可能退化成逐行判断。"
        "UNION 的真实价值在「两个来源结构不同、必须纵向摞起来」：比如「游客报失」和「商家登记」两张表要合成一个列表。"
        "这个项目选择了统一建一张 `lost_found_items` 表用字段区分来源，从表设计上避免 UNION，也算一种解法。",
        [
            choice("用 `IN (SELECT ...)` 做子查询，最需要警惕的性能问题是？",
                   ["语法不合法", "可能对每一行都执行一次内层查询，行数一多就爆炸", "不能返回多条结果", "无法使用索引"],
                   1, "相关子查询是逐行求值；能改写成 JOIN 的尽量改写，优化器才有发挥空间。"),
            judge("UNION 会自动去重，UNION ALL 不会，所以 UNION ALL 通常更快。", 1,
                  "对。去重要排序/哈希，有额外开销；确定没有重复（或不在乎）就用 UNION ALL。"),
        ],
    ),
    "mysql-07": used(
        "database/schema_mysql.sql", "31-32",
        "UNIQUE KEY uk_username (username),\nUNIQUE KEY uk_wx_openid (wx_openid)",
        "用户名和微信 openid 都建了唯一索引：既保证不重复，也让登录查询走索引。",
        "InnoDB 的索引是 B+ 树：非叶子节点只存键、叶子节点存数据并用双向链表相连。"
        "所以它既能做等值查询（O(log n)），也能高效做范围查询和排序（叶子有序，顺着链表扫就行）——"
        "这也是为什么 `ORDER BY id` 很快，而 `ORDER BY 非索引字段` 会 `Using filesort`。"
        "唯一索引还有语义作用：插入重复用户名时数据库直接报错，比「先查再插」可靠（后者在并发下仍会插进两条）。"
        "全项目 23 张表一共建了 43 个索引/唯一键，说明索引是按查询路径设计的，不是随手加。",
        [
            choice("B+ 树索引能高效支持范围查询（BETWEEN / > / ORDER BY），根本原因是？",
                   ["非叶子节点存了数据", "叶子节点按键有序且用链表相连", "它把数据放在了内存", "它会自动建哈希表"],
                   1, "叶子层是有序链表，范围扫描可以顺着链表走，不必回到根节点重新查找。"),
            judge("「先 SELECT 判断用户名是否存在，再 INSERT」能完全避免重复用户名。", 0,
                  "错。两个并发请求可能都查到不存在，然后都插入。只有唯一索引/唯一键约束才能在数据库层真正拦住。"),
        ],
    ),
    "mysql-08": used(
        "database/db_mysql.py", "2238",
        '"SELECT COUNT(*) AS cnt FROM question_logs WHERE DATE(created_at) = CURDATE()"',
        "统计今天的提问量。这条 SQL 就是教科书级的「索引失效」写法。",
        "`created_at` 上如果建了索引，写成 `WHERE DATE(created_at) = CURDATE()` 也用不上——"
        "因为索引里存的是原始的 datetime 值，而 `DATE(created_at)` 是**对列做了函数运算**，"
        "优化器无法把函数结果和索引里的键对应起来，只能整表扫（type=ALL）。"
        "改成范围查询就能命中索引：`WHERE created_at >= CURDATE() AND created_at < CURDATE() + INTERVAL 1 DAY`。"
        "同样的坑还有：`WHERE name LIKE '%张三'`（前导 % 无法走索引）、`WHERE phone = 13800000000`（字符串列传数字会隐式转换）、"
        "以及 `OR` 连接的条件里有一侧没索引。项目里这类写法还有两条（2275、3253），数据量小时不痛，量大了要先优化它们。",
        [
            choice("`WHERE DATE(created_at) = CURDATE()` 用不上 created_at 索引，原因是？",
                   ["DATE() 函数不支持索引", "对列做了函数运算，索引键和表达式结果对不上", "CURDATE() 每次结果不同", "COUNT(*) 不能走索引"],
                   1, "索引是对「列的原值」排序的，一旦列被函数包住，就无法用有序性定位，只能逐行算。"),
            judge("把 `WHERE DATE(created_at) = CURDATE()` 改写成 `created_at >= CURDATE() AND created_at < CURDATE() + INTERVAL 1 DAY`，通常能命中索引。", 1,
                  "对。这叫「把函数移到常量侧」，让列保持裸值，是索引优化的第一步。"),
        ],
    ),
    "mysql-09": used(
        "database/db_mysql.py", "983-988",
        "conn.commit()\nreturn deleted\nexcept Exception:\n    conn.rollback()\n    raise",
        "删用户：先把这个人名下的十几张关联表数据删干净，最后删主表，全程一个事务。",
        "这十几条 DELETE 必须**同生共死**：删到第 8 张表时失败，如果前面 7 张已经提交，数据库就留下一个「用户还在、数据没了」的残局。"
        "`commit()` 之前所有改动只在当前连接可见，出错 `rollback()` 就全部撤销，这就是原子性（A）。"
        "一致性（C）靠外键和约束保证；隔离性（I）靠 MVCC 和锁；持久性（D）靠 redo log——"
        "注意 `commit` 返回时数据已经写进 redo log，即使此刻断电也能恢复，不是「等刷盘才算成功」。"
        "还有一个实践点：`finally: conn.close()` 必须写，否则连接池很快被耗光。",
        [
            choice("事务的原子性（A）具体保证什么？",
                   ["数据一定不重复", "事务里多条语句要么全部生效，要么全部撤销", "并发事务互不干扰", "提交后一定不丢"],
                   1, "原子性就是「不可分割」：中途失败会回滚到事务开始前的状态，不会留下半截数据。"),
            judge("InnoDB 里 `commit` 返回成功就代表数据已经写进磁盘的数据文件了。", 0,
                  "错。commit 保证的是 redo log 落盘（配置为 1 时），脏页可以之后慢慢刷。靠 redo log 就能恢复，不需要立刻写数据文件。"),
        ],
    ),
    "mysql-10": used(
        "database/db_mysql.py", "3529-3533",
        'cur.execute(\n    f"SELECT * FROM consumption_items WHERE item_code IN ({ph}) FOR UPDATE",\n    tuple(norm)\n)',
        "退款前先用 `FOR UPDATE` 把要退的券码行锁住，再判断状态、再改状态。",
        "这是「读-判断-写」并发问题的标准解法。如果只是普通 SELECT，两个请求会同时读到「未退款」，"
        "然后各自执行退款，同一个券码退两次——这就是超卖/重复退款的经典场景。"
        "`SELECT ... FOR UPDATE` 是**排他锁**：谁先拿到谁执行，另一个阻塞等待，等它提交后再读到最新状态，自然就跳过了。"
        "两个必要前提：① 必须在事务里，autocommit 下语句一结束锁就放，等于没锁；"
        "② 锁的是索引命中的行，如果 WHERE 条件没走索引，InnoDB 会锁住扫描到的所有行，退化成近似表锁。"
        "另外要注意加锁顺序一致（都按 item_code 升序），否则两个事务反向加锁会死锁。",
        [
            choice("`SELECT ... FOR UPDATE` 必须在事务里使用，原因是？",
                   ["事务里语法才合法", "非事务环境下语句结束就释放锁，起不到互斥作用", "事务能让查询更快", "否则不返回数据"],
                   1, "锁的持有时长跟事务绑定，autocommit 下每条语句自成一个事务，锁瞬间就没了。"),
            judge("`WHERE` 条件没走索引时，`FOR UPDATE` 可能锁住大量不相关的行。", 1,
                  "对。没有索引就只能全表扫描，扫到的行都会被加锁，并发度骤降，严重时接近表锁。"),
        ],
    ),
    # ---------------- Redis ----------------
    "redis-01": used(
        "core/cache.py", "178",
        "self._client.setex(key, ttl or CACHE_TTL, json.dumps(payload, ensure_ascii=False))",
        "问答结果缓存：一个 key 对应一段 JSON 字符串，带过期时间。",
        "Redis 有五种基础类型，这个项目**只用了 String**（`setex`/`get`/`incr`/`expire`），"
        "因为它的场景就是「一个问句 → 一段答案」，天然的键值对。"
        "这也是选型时最该先问的问题：你的数据是「整体读写」还是「只改其中一部分」？"
        "整体读写用 String 最省；要单独改对象里某个字段才考虑 Hash；要做队列才考虑 List；"
        "要去重/排行榜才用 Set/ZSet。**先想清楚访问模式，再选类型**，反过来做就是给自己挖坑。",
        [
            choice("这个项目的缓存只用 String 类型，最根本的原因是？",
                   ["String 性能最好", "访问模式是「整段答案整体读写」，没有单字段更新需求", "其它类型 Redis 不支持", "为了省内存"],
                   1, "选类型看访问模式。整体读写用 String 最简单；要单字段更新才需要 Hash。"),
            judge("Redis 的 String 类型只能存字符串，不能存数字。", 0,
                  "错。String 可以存数字并支持 incr/decr 原子自增，项目里的计数器就是这么做的。"),
        ],
    ),
    "redis-02": used(
        "core/cache.py", "270-272",
        "current = self._client.incr(key)\nif current == 1:\n    self._client.expire(key, window)",
        "固定窗口限流：每次请求把计数 +1，第一次计数时设置窗口过期时间。",
        "`INCR` 是**原子操作**，多个进程同时自增不会丢计数——这是它比自己 `get` 再 `set` 强的地方，"
        "后者在并发下必然少算。`if current == 1: expire(...)` 只在窗口的第一个请求上设过期，"
        "否则每次都刷新 TTL，计数永远不清零，限流就失效了。"
        "这个实现有个已知缺陷：**固定窗口临界问题**——第 59 秒来 100 次、第 61 秒再来 100 次，"
        "两秒内实际放过了 200 次。要更准就用滑动窗口（ZSet 存时间戳）或令牌桶。"
        "生产上也可以直接用 `SET key 1 EX 60 NX` 一条命令完成「不存在则设值并带过期」。",
        [
            choice("为什么只在 `current == 1` 时设置过期时间？",
                   ["省一次网络往返", "每次都设会导致 TTL 不断被刷新，计数永远不清零", "Redis 不允许重复 expire", "为了让计数更准"],
                   1, "窗口的过期时间只在窗口开始时设一次。每次都续期等于永不过期，限流彻底失效。"),
            judge("Redis 的 INCR 在多个客户端并发时可能丢失计数。", 0,
                  "错。Redis 单线程执行命令，INCR 是原子的；丢计数的是「先 get 再 set」这种非原子组合。"),
        ],
    ),
    "redis-03": absent(
        "cls._instance._queue = queue.Queue()\nself._worker = threading.Thread(target=self._process_queue, daemon=True)",
        "项目里没有用 Redis 的 List/Hash：任务队列用的是**进程内** `queue.Queue`，对象字段也没用 Hash 存。",
        "为什么不用 Redis List 做队列：它是单机部署，进程内队列够用且没有网络开销；"
        "但代价很明确——**服务重启队列里的任务就丢了**，也没法多实例消费。"
        "真要做可靠队列，Redis List 的 `LPUSH + BRPOP`（或 `BLPOP`）能实现，"
        "但更稳的是用 Stream（支持消费组、ACK、重投）或专门的消息队列。"
        "Hash 的适用场景是「只改对象里某个字段」：比如用户画像有 10 个字段，只更新其中一个，"
        "用 Hash 就 `HSET` 一个字段，不用把整个 JSON 反序列化再写回。这个项目的画像数据量小，直接用 JSON 存了。",
        [
            choice("用进程内 `queue.Queue` 而不是 Redis List 做任务队列，最主要的代价是？",
                   ["性能更差", "进程重启后队列里的任务丢失，且无法多实例消费", "不能存字典", "线程不安全"],
                   1, "内存队列不持久、不跨进程。单机小任务够用，一旦要求可靠或多实例就必须外置。"),
            judge("只想更新对象里的一个字段时，用 Redis Hash 比存整个 JSON 字符串更省。", 1,
                  "对。Hash 可以单字段 HSET，不必读出整个 JSON、改完再整体写回。"),
        ],
    ),
    "redis-04": absent(
        "cur.execute(\n    \"SELECT intent, COUNT(*) as cnt FROM chat_messages WHERE role='user' GROUP BY intent\"\n)",
        "项目里没有用 Set/ZSet：没有排行榜，也没有用集合做去重，统计类需求全部交给 MySQL 的 GROUP BY。",
        "Set 适合「去重 + 交并差」（比如「昨天来过且今天没来」的用户），ZSet 适合「按分数排序的榜单」"
        "（热度榜、积分榜，`ZINCRBY` + `ZREVRANGE` 一条龙）。"
        "这个项目的数据量小、统计口径又需要和订单表关联，直接在 MySQL 里 GROUP BY 更简单，"
        "引入 ZSet 反而要维护两份数据的一致性。"
        "选型的分界线大概是：**需要实时刷新、读多写多、且能容忍最终一致** 的榜单用 ZSet；"
        "需要精确、要跟其它表 JOIN 的统计留在 MySQL。",
        [
            choice("要做「实时积分排行榜，取前 10 名」，最适合的 Redis 类型是？",
                   ["String", "List", "Hash", "ZSet"], 3,
                   "ZSet 按 score 有序，ZINCRBY 加分、ZREVRANGE 取前 N 名，天然就是排行榜结构。"),
            judge("统计需求只要用了 Redis 就一定要比 MySQL 快。", 0,
                  "错。要看数据量和一致性要求。需要 JOIN、要精确对账的统计放 MySQL 更合适，多维护一份 Redis 数据反而增加不一致风险。"),
        ],
    ),
    "redis-05": used(
        "core/cache.py", "193-195",
        "data = self._client.get(key)\nif data:\n    self._client.expire(key, CACHE_TTL)  # 刷新过期时长",
        "缓存命中后把 TTL 重新续上，实现「热数据一直留着、冷数据自然淘汰」。",
        "Redis 的过期策略是**惰性删除 + 定期删除**的组合：访问到才检查是否过期（惰性），"
        "同时后台每秒抽样一批 key 清理（定期）。所以「过期了但没被访问」的 key 可能还占着内存——"
        "这也是为什么不能把 Redis 当数据库用。"
        "这里命中后 `expire` 续期，是**滑动过期**：只要还在被访问就一直活着，长期没人问就自己消失。"
        "好处是热点数据不用反复回源；风险是极热的 key 永不淘汰，内存只增不减。"
        "内存满了之后走淘汰策略（`maxmemory-policy`），缓存场景一般配 `allkeys-lru`。",
        [
            choice("Redis 的 key 到了过期时间，会立刻从内存里消失吗？",
                   ["会，精确到毫秒删除", "不一定，惰性删除 + 定期抽样，可能短暂残留", "永远不会删", "只能手动 DEL"],
                   1, "过期是「逻辑上失效」，物理回收靠访问时检查和后台抽样，所以内存占用会滞后。"),
            judge("缓存命中后刷新 TTL（滑动过期），可能导致某些极热的 key 永不淘汰。", 1,
                  "对。只要持续被访问就持续续期，这类 key 需要额外手段控制（比如加最大存活时间或分级 TTL）。"),
        ],
    ),
    "redis-06": absent(
        "# 项目没有配置 Redis 持久化（未设置 appendonly / save 策略）\n# 定位：纯缓存层，丢了可以从 MySQL 重建",
        "项目没有开启 Redis 持久化：既没配 RDB 的 save 规则，也没开 AOF。",
        "这是**刻意的选择**，前提是这层缓存里没有不可再生的数据——问答结果、检索结果丢了都能重新算出来，"
        "最坏结果是短暂变慢，不会丢业务数据。反过来，如果 Redis 里存的是「唯一一份」数据（比如订单号生成器的计数、"
        "分布式锁的状态），那就必须开持久化，而且要认真选："
        "RDB 是定时快照，恢复快但会丢最后一段时间的数据；AOF 记每条写命令，丢得少但文件大、恢复慢；"
        "生产常用 `appendfsync everysec` 折中。判断标准只有一句：**这份数据丢了，能不能从别处重建？**",
        [
            choice("纯缓存层不配 Redis 持久化，可接受的原因是？",
                   ["缓存不需要速度", "数据能从数据库重建，最坏只是短暂变慢", "Redis 不支持持久化", "持久化会导致内存泄漏"],
                   1, "缓存是可再生的派生数据。只要源头还在，丢了重建即可。"),
            judge("RDB 和 AOF 相比，RDB 恢复更快但可能丢失最后一次快照之后的数据。", 1,
                  "对。RDB 是快照，文件紧凑、加载快；AOF 记录更细但回放慢、体积大。"),
        ],
    ),
    "redis-07": absent(
        "if time.time() < self._unavailable_until:\n    return None\n...\nself._unavailable_until = time.time() + self._FAIL_COOLDOWN",
        "项目没有做缓存穿透/击穿/雪崩的专项防护，只做了「Redis 挂了就冷却 30 秒直接当未命中」的熔断降级。",
        "三者的区别值得记牢：**穿透**是查一个根本不存在的 key，每次都打到数据库（解法：缓存空值或布隆过滤器）；"
        "**击穿**是某个热点 key 刚好过期，大量请求同时回源（解法：互斥锁只放一个请求去重建）；"
        "**雪崩**是大量 key 同时过期或 Redis 整体挂掉（解法：TTL 加随机抖动、多级缓存、限流降级）。"
        "这个项目规模小、key 分散，前两种风险低，所以只做了熔断：Redis 不可用后 30 秒内直接跳过缓存，"
        "避免每个请求都等一次连接超时——这条其实很关键，否则 Redis 一挂，整个服务会被超时拖死。"
        "要补穿透防护，最小改动是「查不到也写一个短 TTL 的空值缓存」。",
        [
            choice("「缓存穿透」指的是哪种情况？",
                   ["热点 key 突然过期，大量请求回源", "查一个不存在的 key，每次都打到数据库", "大量 key 同时过期", "Redis 内存满了"],
                   1, "穿透是「查的东西根本不存在」，缓存永远不命中，请求全部穿透到数据库。解法是缓存空值或布隆过滤器。"),
            judge("Redis 不可用后设置一段冷却期、期间直接当未命中，能避免每个请求都等连接超时。", 1,
                  "对。这是熔断降级的基本做法，防止下游故障把上游线程全部拖死。"),
        ],
    ),
    "redis-08": absent(
        "_lock = threading.Lock()",
        "项目里没有分布式锁：用的是 `threading.Lock`（**进程内**锁），只在一个进程内有效。",
        "这个区别非常关键：`threading.Lock` 只能拦住同一进程里的线程，"
        "一旦用 uvicorn 起多个 worker 或者部署两台机器，两个进程各自拿到自己的锁，互不感知，锁就形同虚设。"
        "分布式锁要满足三件事：**互斥**（`SET key val NX PX 30000` 一条命令原子地抢锁+设过期）、"
        "**防误删**（value 存请求唯一 ID，删除前用 Lua 比对，避免删掉别人续期后的锁）、"
        "**防死锁**（必须带过期时间，否则持锁进程崩了锁永远不释放）。"
        "这套实现细节很容易写错，生产上更推荐直接用 Redisson 这类成熟客户端。",
        [
            choice("用 `threading.Lock` 做「分布式锁」的问题是什么？",
                   ["性能太差", "只在单进程内有效，多 worker / 多机部署时互不感知", "不能加超时", "会阻塞事件循环"],
                   1, "进程内锁的作用域是本进程，跨进程完全无效，这是最常见的误用。"),
            judge("用 `SET key val NX PX 30000` 抢锁，比「先 SETNX 再 EXPIRE」两条命令更安全。", 1,
                  "对。两条命令之间如果进程崩溃，就会留下一个永不过期的锁；单条命令把抢锁和设过期做成原子操作。"),
        ],
    ),
}
