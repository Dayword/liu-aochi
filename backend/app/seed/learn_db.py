"""MySQL：关系型数据库与 SQL 实战。

从建表到查询、从索引到事务，按"面试高频"的顺序编排。
"""

# 共用数据集：employees 表（mysql-02/03/04/06 共用，保证数据与题目一致）
EMPLOYEES_SQL = (
    "DROP TABLE IF EXISTS employees;\n"
    "CREATE TABLE employees (\n"
    "    id INTEGER PRIMARY KEY,\n"
    "    name TEXT,\n"
    "    dept TEXT,\n"
    "    salary INTEGER,\n"
    "    city TEXT\n"
    ");\n"
    "INSERT INTO employees (id, name, dept, salary, city) VALUES\n"
    "    (1, '张伟', '研发', 18000, '北京'),\n"
    "    (2, '李娜', '研发', 22000, '上海'),\n"
    "    (3, '刘洋', '研发', 25000, '上海'),\n"
    "    (4, '王强', '产品', 15000, '北京'),\n"
    "    (5, '陈静', '产品', 9000,  '北京'),\n"
    "    (6, '赵敏', '测试', 12000, '深圳'),\n"
    "    (7, '周涛', '测试', 11000, NULL),\n"
    "    (8, '孙磊', '运营', 8000,  '广州');\n"
)

LESSONS: list[dict] = [
    {
        "code": "mysql-01",
        "subject": "MySQL",
        "stage": "SQL 基础",
        "runner": "sql",
        "title": "建表与数据类型",
        "summary": "列名和类型定错了，后面全在还债",
        "definition": (
            "建表就是**定义一张表有哪些列**：每列叫什么、存什么类型、允不允许为空。MySQL 常用类型：\n\n"
            "- `INT` / `BIGINT`：整数。主键推荐 `BIGINT`，`INT` 上限约 21 亿，业务涨起来会不够\n"
            "- `VARCHAR(n)`：变长字符串，`n` 是**字符**上限（utf8mb4 下 1 个汉字算 1 个）\n"
            "- `TEXT`：长文本，不能设默认值，也不适合直接建索引\n"
            "- `DECIMAL(m,d)`：**金额必须用它**，`FLOAT/DOUBLE` 存钱会出现精度误差\n"
            "- `DATETIME` / `TIMESTAMP`：时间。`TIMESTAMP` 只到 2038-01-19，且受时区影响\n\n"
            "主键 `PRIMARY KEY` 唯一且非空，`AUTO_INCREMENT` 让插入时不必手写 id。\n\n"
            "**它解决什么问题**：把「这一列能存什么」提前钉死，数据库才能按类型分配空间、做校验、"
            "建索引。类型选错，后面改表就是锁表 + 全量重写，代价极高。\n\n"
            "本课的沙箱用 SQLite，对应写法是 `INTEGER PRIMARY KEY AUTOINCREMENT`，规则一致。"
        ),
        "plain": (
            "建表像**设计一张 Excel 表格的表头**：先想清楚每一列放什么，再动手填数据。\n\n"
            "类型就是给每列**定「收纳盒的规格」**：`INT` 是只放整数的格子，`VARCHAR` 是放文字的格子，"
            "`DECIMAL` 是专门放钱的格子。规格定错了，后面很难改 —— 就像把水倒进了装文件的盒子。\n\n"
            "所以面试官问「这张表你会怎么设计」，真正想听的是：**字段类型选得对不对、金额有没有用 DECIMAL、"
            "主键够不够大、该 NOT NULL 的有没有 NOT NULL**。"
        ),
        "example": (
            "表结构：students(id 主键自增, name 非空, age, score)\n"
            "\n"
            "-- 建表\n"
            "CREATE TABLE students (\n"
            "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "    name TEXT NOT NULL,\n"
            "    age INTEGER,\n"
            "    score REAL\n"
            ");\n"
            "\n"
            "-- 插入数据\n"
            "INSERT INTO students (name, age, score) VALUES ('小明', 18, 88.5);\n"
            "INSERT INTO students (name, age, score) VALUES ('小红', 19, 92.5);\n"
            "\n"
            "-- 查看结果\n"
            "SELECT id, name, age, score FROM students ORDER BY id;"
        ),
        "example_output": "1 | 小明 | 18 | 88.5\n2 | 小红 | 19 | 92.5",
        "pitfalls": [
            "**金额别用 FLOAT/DOUBLE**：`0.1 + 0.2` 存进去可能变成 `0.30000000000000004`。金额一律 `DECIMAL(10,2)`。",
            "**`VARCHAR(n)` 里的 n 是字符数不是字节数**：`VARCHAR(10)` 能存 10 个汉字。别按 3 字节一个汉字去估算。",
            "**`= NULL` 查不到任何东西**：NULL 必须用 `IS NULL` 判断。所以建表时能 `NOT NULL DEFAULT ''` 就别留 NULL。",
            "**`TIMESTAMP` 有 2038 问题**：它只能存到 2038-01-19。要长期存时间用 `DATETIME`，或者直接存 `BIGINT` 时间戳。",
        ],
        "task": (
            "请写出建表 SQL 并插入数据。\n\n"
            "表名 `students`，列要求：\n"
            "1. `id`：`INTEGER`，主键（`PRIMARY KEY`），自增（`AUTOINCREMENT`）\n"
            "2. `name`：`TEXT`，不允许为空（`NOT NULL`）\n"
            "3. `age`：`INTEGER`\n"
            "4. `score`：`REAL`\n\n"
            "然后用 `INSERT INTO students (name, age, score) VALUES (...)` 依次插入三行：\n"
            "- ('小明', 18, 88.5)\n"
            "- ('小红', 19, 92.5)\n"
            "- ('小刚', 20, 75.5)\n\n"
            "系统最后会执行 `SELECT name, age, score FROM students ORDER BY id` 来检查。"
        ),
        "setup": "-- 本课的表由你自己创建，系统只做一次清理\nDROP TABLE IF EXISTS students;\n",
        "starter": (
            "-- 表名 students\n"
            "-- 列：id INTEGER PRIMARY KEY AUTOINCREMENT、name TEXT NOT NULL、age INTEGER、score REAL\n"
            "-- 补全建表语句，再用 INSERT INTO ... VALUES 插入题目要求的三行数据\n"
            "CREATE TABLE students (\n"
            "    -- 在这里写列定义\n"
            ");\n"
        ),
        "hint": (
            "建表：`CREATE TABLE students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER, score REAL);`\n"
            "插入：`INSERT INTO students (name, age, score) VALUES ('小明', 18, 88.5);`，三行就写三条 INSERT。"
        ),
        "sql_setup": "-- 本课的表由你自己创建，系统只做一次清理\nDROP TABLE IF EXISTS students;\n",
        "sql_verify": "SELECT name, age, score FROM students ORDER BY id;",
        "sql_expect": [["小明", 18, 88.5], ["小红", 19, 92.5], ["小刚", 20, 75.5]],
        "sql_ordered": True,
        "sql_hint_cols": ["name", "age", "score"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官让你设计一张订单表，`amount`（订单金额）列应该用什么类型？",
                "options": ["DECIMAL(10, 2)", "FLOAT", "DOUBLE", "VARCHAR(20)"],
                "answer_index": 0,
                "explanation": (
                    "金额必须用 `DECIMAL`，它是定点数，能精确表示小数。`FLOAT/DOUBLE` 是二进制浮点，"
                    "会有精度误差，对账时会出现一分钱对不上的经典事故；`VARCHAR` 存钱则没法直接求和。"
                ),
            },
            {
                "type": "choice",
                "stem": "下面哪条 `WHERE` 能正确查出 `city` 为空的记录？",
                "options": ["WHERE city IS NULL", "WHERE city = NULL", "WHERE city == NULL", "WHERE city = ''"],
                "answer_index": 0,
                "explanation": (
                    "NULL 表示「不知道」，`city = NULL` 的结果是 NULL 而不是 TRUE，所以一行都查不到。"
                    "判断空值只能用 `IS NULL` / `IS NOT NULL`；`city = ''` 查的是空字符串，不是空值。"
                ),
            },
            {
                "type": "judge",
                "stem": "在 utf8mb4 字符集下，`VARCHAR(10)` 最多只能存 10 个字节，也就是 3 个汉字。",
                "answer": False,
                "explanation": "`VARCHAR(n)` 的 n 是**字符数**上限，不是字节数。`VARCHAR(10)` 能存 10 个汉字。",
            },
            {
                "type": "blank",
                "stem": "补全这条 SQL，查出 `city` 为空的用户：\nSELECT name FROM employees WHERE city ___ NULL;",
                "answer": "IS",
                "accept": ["is"],
                "hint": "一个关键字，两个字母",
                "explanation": "NULL 不能用 `=` 比较，只能用 `IS NULL` / `IS NOT NULL`。",
            },
            {
                "type": "short",
                "stem": "面试官：让你设计一张用户表，你会怎么选字段类型？说说你的关键考虑。",
                "keywords": ["BIGINT 主键", "DECIMAL", "NOT NULL 默认值", "VARCHAR 长度", "DATETIME", "索引"],
                "reference": (
                    "主键用 `BIGINT UNSIGNED AUTO_INCREMENT`，别用 `INT`（21 亿会满），也别用 UUID（随机写入会页分裂）。"
                    "金额类字段用 `DECIMAL(m,2)`。字符串按实际长度定 `VARCHAR(n)`，别一上来就 `TEXT`。"
                    "时间用 `DATETIME`，避开 `TIMESTAMP` 的 2038 问题。"
                    "能 `NOT NULL DEFAULT ''` 的列就不要留 NULL，NULL 会让索引和统计都变复杂。"
                ),
                "explanation": "这类题考的是你踩过坑没有，答出 DECIMAL 和 NOT NULL 就已经超过一半人。",
            },
        ],
    },
    {
        "code": "mysql-02",
        "subject": "MySQL",
        "stage": "SQL 基础",
        "runner": "sql",
        "title": "基础查询与过滤 WHERE",
        "summary": "SELECT 选列，WHERE 选行",
        "definition": (
            "`SELECT` 决定**取哪些列**，`WHERE` 决定**留下哪些行**。骨架：\n\n"
            "```\nSELECT 列1, 列2\nFROM 表\nWHERE 条件\n```\n\n"
            "常用条件：\n\n"
            "- 比较：`=` `<>`（或 `!=`）`>` `<` `>=` `<=`\n"
            "- 区间：`BETWEEN 100 AND 200`，**含两端**\n"
            "- 集合：`IN ('北京', '上海')`\n"
            "- 模糊：`LIKE '小%'`（`%` 匹配任意多字符，`_` 匹配一个字符）\n"
            "- 空值：`IS NULL` / `IS NOT NULL`\n"
            "- 组合：`AND` / `OR` / `NOT`，注意 **`AND` 优先级高于 `OR`**\n\n"
            "**它解决什么问题**：一张表动辄千万行，业务要的永远只是其中一小部分。"
            "`WHERE` 让数据库只把符合条件的数据取出来，而不是全捞回来在应用层过滤 —— "
            "后者会浪费大量网络和内存。\n\n"
            "生产环境**不要写 `SELECT *`**：多取无关列会破坏覆盖索引、增加网络传输，"
            "而且表结构一变，代码就可能拿到意料之外的字段。"
        ),
        "plain": (
            "把表想成一摞**简历**：`SELECT` 是「我只看哪几栏」，`WHERE` 是「把不符合条件的简历丢掉」。\n\n"
            "`WHERE city = '北京' AND salary >= 15000` 读起来就是：**先看城市是不是北京，再看薪水够不够 15000，"
            "两个都满足才留下**。\n\n"
            "最容易踩的是 NULL。`city = NULL` 的答案不是「是」也不是「不是」，而是「**不知道**」，"
            "所以那一行永远不会被选中 —— 就像拿一张空白纸条去比对一个城市名，没法比。"
            "空值只能问 `IS NULL`。"
        ),
        "example": (
            "表结构：employees(id, name, dept, salary, city)，city 可能为 NULL\n"
            "\n"
            "SQL：\n"
            "SELECT name, salary\n"
            "FROM employees\n"
            "WHERE city = '北京' AND salary >= 15000;"
        ),
        "example_output": "张伟 | 18000\n王强 | 15000",
        "pitfalls": [
            "**`= NULL` 永远不成立**：必须写 `IS NULL` / `IS NOT NULL`。NULL 参与 `=`、`>`、`+` 的结果都是 NULL。",
            "**`AND` 和 `OR` 混用要加括号**：`WHERE a = 1 OR a = 2 AND b = 3` 会被解析成 `a = 1 OR (a = 2 AND b = 3)`，跟你想的不一样。",
            "**`BETWEEN` 对时间容易漏数据**：`BETWEEN '2026-01-01' AND '2026-01-31'` 会漏掉 31 号带时分秒的记录，正确写法是 `>= '2026-01-01' AND < '2026-02-01'`。",
            "**`LIKE '%x'` 用不上索引**：以 `%` 开头的模糊匹配只能全表扫；`LIKE 'x%'` 前缀匹配才能走索引。",
        ],
        "task": (
            "表 `employees` 有 5 列：`id`、`name`、`dept`、`salary`、`city`（城市可能为 NULL）。\n\n"
            "请写一条 SQL，查出**城市是北京、并且薪水大于等于 15000** 的员工，只输出 `name` 和 `salary` 两列。"
        ),
        "setup": EMPLOYEES_SQL,
        "starter": (
            "-- 表 employees(id, name, dept, salary, city)\n"
            "-- 请查出城市为北京、薪水 >= 15000 的员工姓名和薪水\n"
            "SELECT name, salary\n"
            "FROM employees\n"
            "WHERE "
        ),
        "hint": "两个条件用 `AND` 连接：`city = '北京'` 和 `salary >= 15000`。注意字符串要加引号。",
        "sql_setup": EMPLOYEES_SQL,
        "sql_expect": [["张伟", 18000], ["王强", 15000]],
        "sql_ordered": False,
        "sql_hint_cols": ["name", "salary"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`WHERE city = NULL` 会查出什么？",
                "options": ["什么都查不到", "city 为空的记录", "city 为空字符串的记录", "直接报语法错误"],
                "answer_index": 0,
                "explanation": (
                    "NULL 参与 `=` 比较的结果是 NULL（既不是真也不是假），所以没有任何行满足条件，结果集为空。"
                    "要查空值必须写 `IS NULL`。"
                ),
            },
            {
                "type": "choice",
                "stem": "`WHERE dept = '研发' OR dept = '测试' AND salary > 15000` 实际等价于下面哪个？",
                "options": [
                    "dept = '研发'，或者（dept = '测试' 且 salary > 15000）",
                    "（dept = '研发' 或 dept = '测试'）且 salary > 15000",
                    "与上面的写法完全等价，没有区别",
                    "语法错误",
                ],
                "answer_index": 0,
                "explanation": (
                    "`AND` 的优先级高于 `OR`，所以先算 `dept = '测试' AND salary > 15000`。"
                    "想表达第二种意思必须加括号：`(dept = '研发' OR dept = '测试') AND salary > 15000`。"
                ),
            },
            {
                "type": "judge",
                "stem": "`WHERE age BETWEEN 25 AND 30` 会把 age 正好等于 30 的行排除在外。",
                "answer": False,
                "explanation": "`BETWEEN` 是**闭区间**，包含 25 和 30 两端。但它对 DATETIME 容易漏掉带时分秒的记录。",
            },
            {
                "type": "blank",
                "stem": "补全这条 SQL，查出名字以「小」开头的员工：\nSELECT name FROM employees WHERE name ___ '小%';",
                "answer": "LIKE",
                "accept": ["like"],
                "hint": "一个关键字，四个字母",
                "explanation": "`LIKE '小%'` 是前缀匹配，可以走索引；写成 `LIKE '%小'` 就只能全表扫。",
            },
            {
                "type": "short",
                "stem": "面试官：产品要给用户列表加筛选条件 —— 城市、年龄区间、昵称模糊搜索、是否填了邮箱。你写这条 SQL 时要注意什么？",
                "keywords": ["AND OR 加括号", "BETWEEN 闭区间", "LIKE 前缀", "IS NULL", "索引", "SELECT 指定列"],
                "reference": (
                    "多个条件用 `AND` 拼接，一旦混入 `OR` 就必须加括号，否则优先级会和预期不一致。"
                    "年龄区间用 `BETWEEN`，但时间字段更推荐 `>= 起点 AND < 终点`，避免漏掉当天带时分秒的数据。"
                    "昵称模糊搜索只能写 `LIKE '关键词%'` 才会走索引，`LIKE '%关键词%'` 会全表扫。"
                    "「是否填了邮箱」用 `IS NULL` / `IS NOT NULL`，不能写 `= NULL`。最后 `SELECT` 要明确列出需要的列。"
                ),
                "explanation": "这就是「列表页筛选」的真实问法，考的是条件组合和索引意识。",
            },
        ],
    },
    {
        "code": "mysql-03",
        "subject": "MySQL",
        "stage": "SQL 基础",
        "runner": "sql",
        "title": "排序、分页与深分页问题",
        "summary": "ORDER BY 排序，LIMIT 分页，深分页必须改写",
        "definition": (
            "`ORDER BY 列 [ASC|DESC]` 决定结果的**行顺序**。多列排序写 `ORDER BY a DESC, b ASC`："
            "先按 a 排，a 相同时再按 b 排。**不写 ORDER BY，数据库不保证任何顺序。**\n\n"
            "分页用 `LIMIT 每页条数 OFFSET 偏移量`。第 `page` 页（从 1 开始）对应 "
            "`LIMIT size OFFSET (page-1) * size`。\n\n"
            "**深分页问题**：`LIMIT 10 OFFSET 1000000` 看起来只取 10 条，MySQL 却要"
            "**先扫描并丢弃前 100 万行**，偏移量越大越慢。两种优化思路：\n\n"
            "1. **游标（keyset）分页**：记住上一页最后一条的排序值，"
            "写 `WHERE id > 上一页最大 id ORDER BY id LIMIT 10`，直接走索引定位，代价不随页数增长\n"
            "2. **延迟关联**：先在索引上完成分页拿到主键，再回表取整行\n"
            "```\nSELECT t.* FROM t\nJOIN (SELECT id FROM t ORDER BY id LIMIT 10 OFFSET 1000000) x ON x.id = t.id;\n```\n\n"
            "**它解决什么问题**：让「排序 + 翻页」这件事有明确、可控的代价。"
        ),
        "plain": (
            "`ORDER BY` 像**把一摞牌按大小重新码好**。不特别说明就没人保证顺序 —— 数据库返回的"
            "「自然顺序」随时可能因为执行计划变化而改变，所以**要顺序就必须写 ORDER BY**。\n\n"
            "深分页的坑可以这样想：你要找一本书里「第 100 万零 1 到第 100 万零 10 个字」。"
            "如果只能从第一页开始数，前面 100 万字都得先翻一遍再丢掉。`OFFSET` 就是这么干的 —— "
            "它**不是跳过，而是数过去再扔掉**。\n\n"
            "游标分页相当于「上次读到哪儿夹了个书签」，下次从书签往后翻，所以飞快；"
            "代价是不能直接跳到第 N 页，只能一页页往后。"
        ),
        "example": (
            "表结构：employees(id, name, dept, salary, city)\n"
            "\n"
            "SQL（每页 2 条，取第 2 页，按薪水从高到低）：\n"
            "SELECT name, salary\n"
            "FROM employees\n"
            "ORDER BY salary DESC\n"
            "LIMIT 2 OFFSET 2;"
        ),
        "example_output": "张伟 | 18000\n王强 | 15000",
        "pitfalls": [
            "**排序值有重复时分页会乱**：`ORDER BY salary DESC` 如果有相同的 salary，同一行可能在第 1 页和第 2 页各出现一次，也可能两页都漏掉。排序字段要能唯一确定顺序，通常补一个 `, id`。",
            "**排序字段不在索引里会 filesort**：`ORDER BY` 的列没有索引、或者多列顺序和联合索引不一致，MySQL 只能把结果拉出来额外排序，数据量大时明显变慢。",
            "**`LIMIT 100 OFFSET 10` 和 `LIMIT 10 OFFSET 100` 不是一回事**：前者是「跳过 10 条取 100 条」。别写反。",
            "**深分页不能靠加内存硬扛**：`OFFSET` 的代价随偏移量线性增长，几百万偏移时怎么加配置都没用，必须改成游标分页或延迟关联。",
        ],
        "task": (
            "表 `employees(id, name, dept, salary, city)`。\n\n"
            "请查出**按薪水从高到低排序后的第 2 页**：每页 2 条，也就是跳过前 2 条、取接下来 2 条，"
            "输出 `name` 和 `salary` 两列。"
        ),
        "setup": EMPLOYEES_SQL,
        "starter": (
            "-- 表 employees(id, name, dept, salary, city)\n"
            "-- 分页：每页 2 条，取第 2 页（跳过前 2 条）\n"
            "SELECT name, salary\n"
            "FROM employees\n"
            "ORDER BY "
        ),
        "hint": "先 `ORDER BY salary DESC`，再加 `LIMIT 2 OFFSET 2`（也可以写成 `LIMIT 2, 2`）。",
        "sql_setup": EMPLOYEES_SQL,
        "sql_expect": [["张伟", 18000], ["王强", 15000]],
        "sql_ordered": True,
        "sql_hint_cols": ["name", "salary"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`LIMIT 10 OFFSET 20` 返回的是？",
                "options": ["跳过前 20 条，取接下来的 10 条", "取前 10 条，再跳过 20 条", "取第 10 到第 20 条", "一共取 30 条"],
                "answer_index": 0,
                "explanation": "`LIMIT` 是「取几条」，`OFFSET` 是「跳过几条」。第 p 页每页 n 条的偏移量是 `(p-1)*n`。",
            },
            {
                "type": "choice",
                "stem": "面试官：`LIMIT 10 OFFSET 1000000` 为什么慢？",
                "options": [
                    "要先扫描并丢弃前 100 万行，代价随偏移量线性增长",
                    "OFFSET 会锁住整张表",
                    "OFFSET 会强制创建临时表",
                    "网络要传输 100 万行数据",
                ],
                "answer_index": 0,
                "explanation": (
                    "`OFFSET` 不是「跳过」，而是「数过去再丢掉」。所以扫描量随偏移量线性增长，而实际只返回 10 行。"
                    "优化方向是游标分页（`WHERE id > 上次最大 id`）或延迟关联。"
                ),
            },
            {
                "type": "judge",
                "stem": "按 `salary DESC` 排序分页时，如果 salary 有重复值，同一行有可能在第 1 页和第 2 页都出现。",
                "answer": True,
                "explanation": "排序值相同时它们的相对顺序不确定，两次查询可能给出不同排列，导致行重复或遗漏。补一个唯一列（如 `, id`）排序即可解决。",
            },
            {
                "type": "blank",
                "stem": "分页查询第 3 页、每页 20 条，OFFSET 应该写 ___（填数字）：\nSELECT * FROM t LIMIT 20 OFFSET ___;",
                "answer": "40",
                "accept": ["40"],
                "hint": "填一个数字",
                "explanation": "偏移量 =（页码 - 1）× 每页条数 =（3 - 1）× 20 = 40。",
            },
            {
                "type": "short",
                "stem": "面试官：线上一个列表接口用 `LIMIT 20 OFFSET 500000` 翻到后面几页就超时，你怎么改？",
                "keywords": ["游标分页", "id >", "延迟关联", "走索引", "不能跳页", "排序唯一"],
                "reference": (
                    "先确认排序字段上有索引，没有就先补索引。然后把 `OFFSET` 分页改成游标分页："
                    "记住上一页最后一条的排序值，下一页查询写成 `WHERE id > 上次最大 id ORDER BY id LIMIT 20`，"
                    "这样能直接用索引定位，代价不随页数增长。"
                    "如果业务必须支持跳页，就用延迟关联：先在索引上分页取出主键，再 JOIN 回原表取整行。"
                    "同时排序字段要加上唯一列，保证顺序稳定。"
                ),
                "explanation": "这是最经典的慢查询场景之一，答出游标分页基本就到位了。",
            },
        ],
    },
    {
        "code": "mysql-04",
        "subject": "MySQL",
        "stage": "SQL 基础",
        "runner": "sql",
        "title": "聚合与分组 GROUP BY",
        "summary": "把行分成组，再对每组做统计",
        "definition": (
            "**聚合函数**把多行压成一个值：`COUNT()` 计数、`SUM()` 求和、`AVG()` 求平均、`MAX()/MIN()` 求最值。\n\n"
            "`GROUP BY 列` 先把行按该列的值**分组**，再对每组分别聚合。`SELECT` 里能出现的只有"
            "「分组列」和「聚合函数」。\n\n"
            "`WHERE` 与 `HAVING` 的分工是高频考点：\n\n"
            "- `WHERE` 在分组**之前**过滤**行**，不能用聚合函数\n"
            "- `HAVING` 在分组**之后**过滤**组**，可以用聚合函数\n\n"
            "完整执行顺序：`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`。\n\n"
            "几个细节：`COUNT(*)` 统计所有行，`COUNT(列)` 会**跳过 NULL**，`COUNT(DISTINCT 列)` 统计去重后的数量。\n\n"
            "**它解决什么问题**：报表类需求（每个部门多少人、每个商品卖了多少）本质都是「先分组再统计」，"
            "一条 SQL 就能算完，不用把数据全捞到应用层循环。"
        ),
        "plain": (
            "`GROUP BY` 像**把一筐水果按品种分堆**：先把苹果放一起、橘子放一起，然后数每堆几个、称每堆多重。\n\n"
            "`WHERE` 是**分堆之前**挑水果：「只要新鲜的」。这时候还没有堆，所以谈不上「这堆有几个」。"
            "`HAVING` 是**分堆之后**筛堆：「只留下超过 5 个的堆」—— 这时候说「这堆的数量」才有意义。\n\n"
            "所以 `WHERE COUNT(*) > 5` 必然报错，写成 `HAVING COUNT(*) > 5` 才对。这就是那句口诀："
            "**WHERE 筛行，HAVING 筛组**。"
        ),
        "example": (
            "表结构：employees(id, name, dept, salary, city)\n"
            "\n"
            "SQL：\n"
            "SELECT dept, COUNT(*) AS cnt, MAX(salary) AS max_salary\n"
            "FROM employees\n"
            "GROUP BY dept\n"
            "HAVING COUNT(*) >= 2\n"
            "ORDER BY max_salary DESC;"
        ),
        "example_output": "研发 | 3 | 25000\n产品 | 2 | 15000\n测试 | 2 | 12000",
        "pitfalls": [
            "**`WHERE` 里写聚合函数会直接报错**：`WHERE COUNT(*) > 5` 非法，必须改成 `HAVING COUNT(*) > 5`。",
            "**`SELECT` 里的非聚合列必须出现在 `GROUP BY` 里**：MySQL 5.7 起 `ONLY_FULL_GROUP_BY` 默认开启，`SELECT name, COUNT(*) FROM t GROUP BY dept` 会报错；就算关掉也只是随机取一行，结果不可靠。",
            "**`COUNT(列)` 会漏掉 NULL**：统计行数用 `COUNT(*)`；`COUNT(email)` 统计的是邮箱非空的行数，两者可能差很多。",
            "**`SUM/AVG` 对 NULL 是忽略而不是当 0**：`AVG(score)` 的分母是「score 非空的行数」。要按全部行算平均得自己写 `SUM(score) / COUNT(*)`。",
        ],
        "task": (
            "表 `employees(id, name, dept, salary, city)`。\n\n"
            "请统计每个部门的**人数**和**最高薪水**，只保留人数大于等于 2 的部门。\n"
            "输出三列：`dept`、人数（别名 `cnt`）、最高薪水（别名 `max_salary`），"
            "按 `max_salary` 从高到低排序。"
        ),
        "setup": EMPLOYEES_SQL,
        "starter": (
            "-- 表 employees(id, name, dept, salary, city)\n"
            "-- 统计每个部门的人数和最高薪水，只保留人数 >= 2 的部门\n"
            "SELECT dept, COUNT(*) AS cnt, MAX(salary) AS max_salary\n"
            "FROM employees\n"
        ),
        "hint": "`GROUP BY dept` 分组，`HAVING COUNT(*) >= 2` 过滤分组，最后 `ORDER BY max_salary DESC`。",
        "sql_setup": EMPLOYEES_SQL,
        "sql_expect": [["研发", 3, 25000], ["产品", 2, 15000], ["测试", 2, 12000]],
        "sql_ordered": True,
        "sql_hint_cols": ["dept", "cnt", "max_salary"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要筛选出「平均薪水大于 15000 的部门」，正确写法是？",
                "options": [
                    "GROUP BY dept HAVING AVG(salary) > 15000",
                    "WHERE AVG(salary) > 15000",
                    "GROUP BY dept WHERE AVG(salary) > 15000",
                    "ORDER BY AVG(salary) > 15000",
                ],
                "answer_index": 0,
                "explanation": (
                    "「平均薪水」是分组的统计结果，必须在分组之后用 `HAVING` 过滤。"
                    "`WHERE` 在分组前执行，此时还没有「平均薪水」这个东西，写聚合函数会报错。"
                ),
            },
            {
                "type": "choice",
                "stem": "面试官：`COUNT(*)`、`COUNT(1)` 和 `COUNT(email)` 有什么区别？",
                "options": [
                    "COUNT(*) 和 COUNT(1) 统计所有行数，COUNT(email) 会跳过 email 为 NULL 的行",
                    "COUNT(1) 比 COUNT(*) 快一倍",
                    "COUNT(email) 统计的也是所有行数",
                    "三者结果完全一样，只是写法不同",
                ],
                "answer_index": 0,
                "explanation": (
                    "`COUNT(*)` 和 `COUNT(1)` 都是统计行数，InnoDB 下执行方式基本一致，没有性能差异。"
                    "`COUNT(列)` 只统计该列**非 NULL** 的行数，所以有 NULL 时它会比 `COUNT(*)` 小。"
                ),
            },
            {
                "type": "judge",
                "stem": "`WHERE` 在 `GROUP BY` 之后执行，所以 `WHERE COUNT(*) > 5` 这种写法是合法的。",
                "answer": False,
                "explanation": "执行顺序是 `WHERE → GROUP BY → HAVING`，`WHERE` 在前且不能用聚合函数。过滤分组统计结果必须用 `HAVING`。",
            },
            {
                "type": "blank",
                "stem": "统计 employees 表一共有多少行，补全这条 SQL：\nSELECT ___(*) FROM employees;",
                "answer": "COUNT",
                "accept": ["count"],
                "hint": "一个聚合函数名",
                "explanation": "`COUNT(*)` 统计所有行数，包括含 NULL 的行。",
            },
            {
                "type": "short",
                "stem": "面试官：要统计「每个部门每个职级的平均薪水，只保留平均薪水超过 20000 的分组」，这条 SQL 怎么写？执行顺序是怎样的？",
                "keywords": ["GROUP BY 多列", "HAVING", "AVG", "WHERE 在前", "执行顺序", "ORDER BY"],
                "reference": (
                    "`SELECT dept, level, AVG(salary) FROM employees WHERE ... GROUP BY dept, level HAVING AVG(salary) > 20000;`。"
                    "要点是 `GROUP BY` 后面跟多列（先按部门再按职级），`HAVING` 里可以直接用聚合函数。"
                    "执行顺序是 `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`，"
                    "所以「按行过滤」的条件放 `WHERE`（能提前减少数据量，更快），「按组过滤」的条件只能放 `HAVING`。"
                ),
                "explanation": "考的是多列分组 + WHERE/HAVING 分工，顺带看你会不会把过滤条件尽量前移。",
            },
        ],
    },
    {
        "code": "mysql-05",
        "subject": "MySQL",
        "stage": "SQL 基础",
        "runner": "sql",
        "title": "多表连接 JOIN",
        "summary": "LEFT JOIN 保住左表，NULL 要用 COALESCE",
        "definition": (
            "`JOIN` 把两张表按条件拼成一张宽表，`ON` 后面写连接条件，最典型的是「外键 = 主键」。\n\n"
            "四种连接的区别（**面试必问**）：\n\n"
            "- `INNER JOIN`：只保留两边都匹配上的行\n"
            "- `LEFT JOIN`：保留**左表全部**，右表没匹配上的补 NULL\n"
            "- `RIGHT JOIN`：保留右表全部（实际很少用，调换两表顺序写成 LEFT JOIN 更清楚）\n"
            "- `FULL OUTER JOIN`：两边都保留（MySQL 不支持，要用 `UNION` 拼）\n\n"
            "判断方法很简单：**「没有订单的用户也要出现在结果里」就必须 LEFT JOIN。**\n\n"
            "`LEFT JOIN` 里 `ON` 和 `WHERE` 的区别是重灾区：\n\n"
            "- 条件写在 `ON` 里：只是「匹配条件」，不匹配就补 NULL，左表行照样保留\n"
            "- 条件写在 `WHERE` 里：是对**结果**过滤，会把右表补出来的 NULL 行直接干掉，效果等于 INNER JOIN\n\n"
            "**它解决什么问题**：数据按范式拆在多张表里避免冗余，查询时再用 JOIN 拼回来。"
        ),
        "plain": (
            "`INNER JOIN` 像**相亲配对**：只有两边都看上眼才留下，其余全刷掉。\n\n"
            "`LEFT JOIN` 像**点名**：以左表的花名册为准，每个人都要念到；右表能对上就把信息填上，"
            "对不上的就写着「无」—— 也就是 NULL。\n\n"
            "所以「查出所有用户的订单总额，没买过的显示 0」这种需求，用 `INNER JOIN` 会把"
            "没买过的用户整行丢掉，这是新手最容易犯的错。NULL 也不能直接参与计算，"
            "要用 `COALESCE(SUM(...), 0)` 把 NULL 兜成 0。"
        ),
        "example": (
            "表结构：users(id, name) / orders(id, user_id, amount)\n"
            "数据：小明和小红有订单，小美一单都没有\n"
            "\n"
            "SQL：\n"
            "SELECT u.name, COALESCE(SUM(o.amount), 0) AS total\n"
            "FROM users u\n"
            "LEFT JOIN orders o ON o.user_id = u.id\n"
            "GROUP BY u.id, u.name\n"
            "ORDER BY total DESC;"
        ),
        "example_output": "小明 | 350\n小刚 | 300\n小红 | 80\n小美 | 0",
        "pitfalls": [
            "**`LEFT JOIN` 把右表条件写到 `WHERE` 会退化成 `INNER JOIN`**：`LEFT JOIN orders ON ... WHERE o.amount > 100` 会把右表补 NULL 的行全部过滤掉。要保留左表就得把条件写进 `ON`。",
            "**不写连接条件会得到笛卡尔积**：`FROM a, b` 的结果行数是 `a 行数 × b 行数`，1000 × 1000 就是 100 万行，能把库直接拖死。",
            "**一对多 JOIN 后 `COUNT(*)` 会重复计数**：算的是「连接后的行数」，不是主表行数。要数用户数得写 `COUNT(DISTINCT u.id)`。",
            "**NULL 不参与连接匹配**：`ON a.x = b.x` 里 `b.x IS NULL` 的行永远匹配不上，别指望 NULL = NULL 能连上。",
        ],
        "task": (
            "表 `users(id, name)`、`orders(id, user_id, amount)`。\n\n"
            "请查出**每个用户**的名字和订单总金额（别名 `total`）：\n"
            "- **没有下过单的用户也要出现，金额显示 0**\n"
            "- 按 `total` 从高到低排序\n\n"
            "输出两列：`name` 和 `total`。"
        ),
        "setup": (
            "DROP TABLE IF EXISTS users;\n"
            "DROP TABLE IF EXISTS orders;\n"
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);\n"
            "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount INTEGER);\n"
            "INSERT INTO users (id, name) VALUES (1, '小明'), (2, '小红'), (3, '小刚'), (4, '小美');\n"
            "INSERT INTO orders (id, user_id, amount) VALUES\n"
            "    (1, 1, 100),\n"
            "    (2, 1, 250),\n"
            "    (3, 2, 80),\n"
            "    (4, 3, 300);\n"
        ),
        "starter": (
            "-- 表 users(id, name) 和 orders(id, user_id, amount)\n"
            "-- 查出每个用户的名字和订单总额，没有订单的用户显示 0\n"
            "SELECT u.name, COALESCE(SUM(o.amount), 0) AS total\n"
            "FROM users u "
        ),
        "hint": (
            "`LEFT JOIN orders o ON o.user_id = u.id`，然后 `GROUP BY u.id, u.name`；"
            "金额用 `COALESCE(SUM(o.amount), 0) AS total`，最后 `ORDER BY total DESC`。"
        ),
        "sql_setup": (
            "DROP TABLE IF EXISTS users;\n"
            "DROP TABLE IF EXISTS orders;\n"
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);\n"
            "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount INTEGER);\n"
            "INSERT INTO users (id, name) VALUES (1, '小明'), (2, '小红'), (3, '小刚'), (4, '小美');\n"
            "INSERT INTO orders (id, user_id, amount) VALUES\n"
            "    (1, 1, 100),\n"
            "    (2, 1, 250),\n"
            "    (3, 2, 80),\n"
            "    (4, 3, 300);\n"
        ),
        "sql_expect": [["小明", 350], ["小刚", 300], ["小红", 80], ["小美", 0]],
        "sql_ordered": True,
        "sql_hint_cols": ["name", "total"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要查出「所有用户及其订单数，没有订单的显示 0」，应该用哪种连接？",
                "options": ["LEFT JOIN（users 在左）", "INNER JOIN", "CROSS JOIN", "RIGHT JOIN（users 在右）"],
                "answer_index": 0,
                "explanation": (
                    "「所有用户」意味着左表必须完整保留，未匹配的订单侧补 NULL，再用 `COALESCE(..., 0)` 显示成 0。"
                    "`INNER JOIN` 会把没下单的用户丢掉。"
                ),
            },
            {
                "type": "choice",
                "stem": "`FROM a, b` 不写任何连接条件，结果会是？",
                "options": ["两表的笛卡尔积（a 行数 × b 行数）", "两表的交集", "直接报语法错误", "只返回 b 表的第一行"],
                "answer_index": 0,
                "explanation": "这就是笛卡尔积，行数会爆炸。两表各 1 万行就是 1 亿行结果，线上会直接把数据库打挂。",
            },
            {
                "type": "judge",
                "stem": "`LEFT JOIN` 时，把右表的过滤条件写在 `WHERE` 里和写在 `ON` 里，结果完全一样。",
                "answer": False,
                "explanation": "写在 `WHERE` 会把右表为 NULL 的行过滤掉，等价于 `INNER JOIN`；写在 `ON` 才是「匹配条件」，左表行依然全部保留。",
            },
            {
                "type": "blank",
                "stem": "补全 LEFT JOIN 的连接条件：\nSELECT u.name FROM users u LEFT JOIN orders o ___ o.user_id = u.id;",
                "answer": "ON",
                "accept": ["on"],
                "hint": "一个关键字，两个字母",
                "explanation": "`LEFT JOIN 表 ON 条件` 是固定写法，`ON` 后面写两张表的关联关系。",
            },
            {
                "type": "short",
                "stem": "面试官：一条查询变慢了，发现是两张千万级大表在 JOIN，你会从哪些角度排查和优化？",
                "keywords": ["驱动表", "小表驱动大表", "ON 列索引", "类型一致", "EXPLAIN", "先过滤再 JOIN"],
                "reference": (
                    "先用 `EXPLAIN` 看驱动顺序、`type`、`key`、`rows`。优化方向："
                    "一是保证 `ON` 里的关联列在两边都有索引，而且**类型和字符集一致**，否则会隐式转换导致索引失效；"
                    "二是让**小表驱动大表**（`EXPLAIN` 里第一行是驱动表，行数应当尽量小）；"
                    "三是尽量先用 `WHERE` 把数据量过滤小，再做 JOIN，避免连接超大中间结果；"
                    "四是只 `SELECT` 需要的列，让覆盖索引生效。"
                ),
                "explanation": "大表 JOIN 优化是面试常客，答出「小表驱动大表 + 关联列有索引且类型一致」就很稳。",
            },
        ],
    },
    {
        "code": "mysql-06",
        "subject": "MySQL",
        "stage": "SQL 基础",
        "runner": "sql",
        "title": "子查询与 UNION",
        "summary": "先算括号里的，再拿结果去筛",
        "definition": (
            "**子查询**就是嵌在另一条 SQL 里的 `SELECT`：\n\n"
            "- **标量子查询**：只返回一个值，可以当普通值用 —— "
            "`WHERE salary > (SELECT AVG(salary) FROM employees)`\n"
            "- **`IN` / `NOT IN` 子查询**：`WHERE dept IN (SELECT dept FROM ...)`\n"
            "- **`EXISTS`**：只判断「有没有匹配的行」，一旦找到就返回，通常比 `IN` 高效，也不会踩 NULL 的坑\n"
            "- **`FROM` 派生表**：`FROM (SELECT ...) AS t`，**必须给别名**\n\n"
            "**`UNION` 与 `UNION ALL`**：`UNION` 去重（内部要排序，慢），`UNION ALL` 直接拼接（不去重，快）。\n\n"
            "**`IN` 和 `EXISTS` 怎么选**：子查询结果集**小**的时候用 `IN` 更直观；"
            "结果集**大**、或者外层表小的时候用 `EXISTS`（能提前短路）。"
            "但 `NOT IN` 要特别当心 —— 子查询里只要有一行 NULL，整个结果就是空集，所以**否定场景一律用 `NOT EXISTS`**。\n\n"
            "**它解决什么问题**：把「先算一个中间结果、再拿它去筛选」这类两步逻辑用一条 SQL 表达出来，"
            "省掉应用层的往返。"
        ),
        "plain": (
            "子查询像**先算括号里的题**：`WHERE salary > (SELECT AVG(salary) FROM employees)`，"
            "先问「全公司平均薪水是多少」，拿到这个数，再回头逐行比较。\n\n"
            "`IN` 和 `EXISTS` 的区别可以想成**对名单**：`IN` 是先把子查询的结果**抄成一整张名单**，"
            "再拿每一行去名单里找；`EXISTS` 是拿每一行去问一句「存在吗」，一旦有人答应就立刻停手。"
            "名单很长时，后者明显划算。\n\n"
            "`UNION` 像把两份名单合并**并去重**（要额外整理一遍），`UNION ALL` 就是直接把两张纸粘在一起。"
            "除非真要去重，否则用 `UNION ALL`。"
        ),
        "example": (
            "表结构：employees(id, name, dept, salary, city)\n"
            "数据里 8 个人的薪水总和是 120000，平均薪水正好是 15000\n"
            "\n"
            "SQL：\n"
            "SELECT name, salary\n"
            "FROM employees\n"
            "WHERE salary > (SELECT AVG(salary) FROM employees)\n"
            "ORDER BY salary DESC;"
        ),
        "example_output": "刘洋 | 25000\n李娜 | 22000\n张伟 | 18000",
        "pitfalls": [
            "**`NOT IN` 的子查询里只要有一行 NULL，整个查询就返回空**：`x NOT IN (1, 2, NULL)` 既不为真也不为假。否定场景一律改用 `NOT EXISTS`。",
            "**`UNION` 会去重并排序，比 `UNION ALL` 慢**：确定没有重复数据就用 `UNION ALL`。另外 `UNION` 是按**所有列**一起去重的。",
            "**`FROM` 后面的子查询必须起别名**：`FROM (SELECT ...)` 不写 `AS t` 在 MySQL 里直接报语法错误。",
            "**关联子查询容易变成「逐行执行」**：`WHERE EXISTS (SELECT 1 FROM b WHERE b.uid = a.id)` 这类写法对 `a` 的每一行都要跑一次子查询，数据量大时要考虑改写成 JOIN，并保证关联列有索引。",
        ],
        "task": (
            "表 `employees(id, name, dept, salary, city)`。\n\n"
            "请查出**薪水高于全公司平均薪水**的员工，输出 `name` 和 `salary` 两列，按 `salary` 从高到低排序。\n\n"
            "（提示：平均薪水用子查询算出来。）"
        ),
        "setup": EMPLOYEES_SQL,
        "starter": (
            "-- 表 employees(id, name, dept, salary, city)\n"
            "-- 查出薪水高于全公司平均薪水的员工\n"
            "SELECT name, salary\n"
            "FROM employees\n"
            "WHERE "
        ),
        "hint": "用标量子查询：`WHERE salary > (SELECT AVG(salary) FROM employees)`，最后 `ORDER BY salary DESC`。",
        "sql_setup": EMPLOYEES_SQL,
        "sql_expect": [["刘洋", 25000], ["李娜", 22000], ["张伟", 18000]],
        "sql_ordered": True,
        "sql_hint_cols": ["name", "salary"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`x NOT IN (1, 2, NULL)` 的结果是？",
                "options": ["永远不成立，一行都查不到", "等价于 x NOT IN (1, 2)", "等价于 x IN (1, 2)", "会报语法错误"],
                "answer_index": 0,
                "explanation": (
                    "`x NOT IN (1, 2, NULL)` 展开后是 `x <> 1 AND x <> 2 AND x <> NULL`，"
                    "最后一项的结果是 NULL，整个 `AND` 也变成 NULL，永远不为真。要避免就用 `NOT EXISTS`。"
                ),
            },
            {
                "type": "choice",
                "stem": "只是想把两张结构相同的表的数据拼在一起，并且确定没有重复，应该用？",
                "options": ["UNION ALL", "UNION", "UNION DISTINCT", "FULL OUTER JOIN"],
                "answer_index": 0,
                "explanation": (
                    "`UNION ALL` 直接拼接，不排序不去重；`UNION` 会额外做去重排序，白白浪费性能。"
                    "MySQL 没有 `UNION DISTINCT` 这个写法（`UNION` 本身就是去重的）。"
                ),
            },
            {
                "type": "judge",
                "stem": "`EXISTS` 子查询一旦找到一行匹配的记录，就会停止继续扫描。",
                "answer": True,
                "explanation": "这就是 `EXISTS` 的「短路」特性，也是它在子查询结果集大时比 `IN` 更划算的原因。",
            },
            {
                "type": "blank",
                "stem": "补全这条 SQL，查出薪水高于全公司平均薪水的员工：\nSELECT name FROM employees WHERE salary > (SELECT ___ (salary) FROM employees);",
                "answer": "AVG",
                "accept": ["avg"],
                "hint": "一个聚合函数名",
                "explanation": "`AVG(salary)` 返回平均薪水，这是一个标量子查询，可以直接当数值参与比较。",
            },
            {
                "type": "short",
                "stem": "面试官：`IN` 和 `EXISTS`、`NOT IN` 和 `NOT EXISTS` 分别怎么选？说说理由。",
                "keywords": ["EXISTS 短路", "NOT IN 遇 NULL 返回空", "子查询结果集大小", "关联子查询", "索引", "改写 JOIN"],
                "reference": (
                    "`IN` 适合子查询结果集小、且列表是常量或小集合的场景；"
                    "`EXISTS` 是关联子查询，找到第一行就短路返回，子查询表大、外层表小时更划算。"
                    "`NOT IN` 有个致命坑：子查询结果里只要有一行 NULL，整个结果就是空集，所以否定场景应该统一用 `NOT EXISTS`。"
                    "两者的性能最终都取决于关联列上有没有索引，必要时可以改写成 JOIN 让优化器更自由地选择驱动表。"
                ),
                "explanation": "能答出「NOT IN 遇 NULL 返回空」这一条，就已经答到点上了。",
            },
        ],
    },
    {
        "code": "mysql-07",
        "subject": "MySQL",
        "stage": "索引与优化",
        "runner": "sql",
        "title": "B+ 树索引原理",
        "summary": "为什么 InnoDB 偏偏选 B+ 树",
        "definition": (
            "索引是**为某一列（或几列）额外维护的一份有序结构**，用来把「全表扫描」变成「快速定位」。"
            "InnoDB 的索引结构是 **B+ 树**。\n\n"
            "B+ 树的关键特征：\n\n"
            "- **只有叶子节点存数据**，非叶子节点只存键和指针 —— 同样的页大小能塞下更多键，树更矮，"
            "3~4 层就能撑住千万级数据，一次查询只需要几次磁盘 IO\n"
            "- **叶子节点按顺序排列，并用双向链表串起来** —— 天然支持范围查询和 `ORDER BY`，"
            "找到起点后顺着链表往后读就行\n"
            "- **所有查询都要走到叶子节点**，查询路径长度一致，性能可预测\n\n"
            "为什么不用别的结构（**面试必答**）：\n\n"
            "- **B 树**：非叶子节点也存数据，一个节点能放的键更少 → 树更高 → IO 更多；"
            "而且范围查询要做中序遍历，不如叶子链表\n"
            "- **哈希表**：等值查询 O(1)，但**不支持范围查询和排序**，也用不了联合索引的最左前缀\n"
            "- **红黑树 / 二叉树**：一个节点只有两个子节点，千万级数据树高几十层，每层一次磁盘 IO，扛不住\n\n"
            "**聚簇索引**：InnoDB 的主键索引，叶子节点直接存整行数据，所以按主键查最快。"
            "二级索引的叶子存的是**主键值**，查索引之外的列要**回表**再查一次聚簇索引。"
        ),
        "plain": (
            "索引像**书后面的索引页**：想找「B+ 树」在第几页，不用从第一页翻，翻到索引页按顺序定位就到了。"
            "没有索引，就只能一页页读完 —— 这就是「全表扫描」。\n\n"
            "B+ 树为什么适合数据库？可以想成**一本多级目录的书**：第一级目录只有几行（章），第二级是节，"
            "最底下的正文**按顺序连续排列**。所以「从第 100 页读到第 200 页」这种范围查询，"
            "只要找到起点，顺着往后读就行。\n\n"
            "哈希表则像字典的「按拼音精确查字」：一个字查得飞快，但你没法用它回答"
            "「拼音在 han 到 liu 之间的字有哪些」。等值查询它无敌，范围查询它直接不会。"
        ),
        "example": (
            "表结构：users(id 主键, name, age, city)，id 是主键（聚簇索引）\n"
            "\n"
            "SQL：\n"
            "SELECT name, age\n"
            "FROM users\n"
            "WHERE age BETWEEN 25 AND 30\n"
            "ORDER BY age;"
        ),
        "example_output": "小美 | 26\n阿明 | 27\n小红 | 28\n小刚 | 30",
        "pitfalls": [
            "**索引不是越多越好**：每个索引写入时都要维护，还占磁盘。单表索引一般控制在 5 个以内，写多读少的表更要克制。",
            "**范围条件后面的列用不上索引**：联合索引 `(a, b)` 里写 `WHERE a > 1 AND b = 2`，b 用不到索引。要尽量把等值条件的列排在前面。",
            "**二级索引要回表**：`SELECT *` 会让「先在二级索引定位、再回聚簇索引取整行」；如果只查索引里已有的列，MySQL 用**覆盖索引**就能直接在索引上返回结果，快很多。",
            "**自增 INT 主键比 UUID 好**：自增是顺序写入，页分裂少；UUID 随机插入会频繁页分裂，索引体积也更大。",
        ],
        "task": (
            "表 `users(id, name, age, city)`。\n\n"
            "请查出 **age 在 25 到 30 之间（含 25 和 30）** 的用户，输出 `name` 和 `age` 两列，"
            "按 `age` 从小到大排序。"
        ),
        "setup": (
            "DROP TABLE IF EXISTS users;\n"
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, city TEXT);\n"
            "INSERT INTO users (id, name, age, city) VALUES\n"
            "    (1, '小明', 24, '北京'),\n"
            "    (2, '小红', 28, '上海'),\n"
            "    (3, '小刚', 30, '北京'),\n"
            "    (4, '小美', 26, '深圳'),\n"
            "    (5, '阿强', 35, '杭州'),\n"
            "    (6, '小丽', 22, '上海'),\n"
            "    (7, '阿明', 27, '广州');\n"
        ),
        "starter": (
            "-- 表 users(id, name, age, city)\n"
            "-- 查出 age 在 25 到 30 之间（含两端）的用户，按年龄升序\n"
            "SELECT name, age\n"
            "FROM users\n"
            "WHERE "
        ),
        "hint": "范围条件用 `age BETWEEN 25 AND 30`（含两端），再 `ORDER BY age`。B+ 树的叶子是链表，天然适合这种范围查询。",
        "sql_setup": (
            "DROP TABLE IF EXISTS users;\n"
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, city TEXT);\n"
            "INSERT INTO users (id, name, age, city) VALUES\n"
            "    (1, '小明', 24, '北京'),\n"
            "    (2, '小红', 28, '上海'),\n"
            "    (3, '小刚', 30, '北京'),\n"
            "    (4, '小美', 26, '深圳'),\n"
            "    (5, '阿强', 35, '杭州'),\n"
            "    (6, '小丽', 22, '上海'),\n"
            "    (7, '阿明', 27, '广州');\n"
        ),
        "sql_expect": [["小美", 26], ["阿明", 27], ["小红", 28], ["小刚", 30]],
        "sql_ordered": True,
        "sql_hint_cols": ["name", "age"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官：InnoDB 为什么用 B+ 树，而不是哈希表？",
                "options": [
                    "B+ 树的叶子是有序链表，支持范围查询和排序；哈希表只支持等值查询",
                    "B+ 树的等值查询比哈希表更快",
                    "哈希表太占内存",
                    "哈希表不支持事务",
                ],
                "answer_index": 0,
                "explanation": (
                    "哈希索引等值查询确实是 O(1)，比 B+ 树还快，但它**不支持范围查询、排序和联合索引最左前缀**，"
                    "而真实业务里 `BETWEEN`、`ORDER BY`、`> <` 到处都是，所以 B+ 树才是默认选择。"
                ),
            },
            {
                "type": "choice",
                "stem": "关于 InnoDB 的二级索引（非聚簇索引），下面说法正确的是？",
                "options": [
                    "叶子节点存的是主键值，查其它列需要回表",
                    "叶子节点直接存整行数据",
                    "二级索引查询永远不需要回表",
                    "二级索引只支持等值查询",
                ],
                "answer_index": 0,
                "explanation": (
                    "二级索引的叶子存「索引列 + 主键值」。要取非索引列，得拿主键再查一次聚簇索引，这就是**回表**。"
                    "如果只查索引列和主键（覆盖索引），就不用回表。"
                ),
            },
            {
                "type": "judge",
                "stem": "B+ 树的非叶子节点也会存储完整的行数据。",
                "answer": False,
                "explanation": "B+ 树只有叶子节点存数据，非叶子节点只存键值和指针 —— 这正是它比 B 树矮、IO 更少的原因。存整行数据的是聚簇索引的叶子节点。",
            },
            {
                "type": "blank",
                "stem": "联合索引 `(a, b, c)`，查询条件 `WHERE a = 1 AND c = 3` 只能用到最左边的 ___ 个列（填数字）。",
                "answer": "1",
                "accept": ["一", "1"],
                "hint": "填一个数字",
                "explanation": "最左前缀原则：跳过了 `b`，`c` 就用不上索引，所以只能用 `a` 这一列来定位。",
            },
            {
                "type": "short",
                "stem": "面试官：为什么 InnoDB 用 B+ 树，而不是 B 树、红黑树或者哈希表？",
                "keywords": ["比 B 树矮", "非叶子不存数据", "叶子链表范围查询", "红黑树树高 IO", "哈希不支持范围", "IO 次数"],
                "reference": (
                    "核心目标是**减少磁盘 IO 次数**。B+ 树非叶子节点只存键和指针，一页能放更多键，"
                    "所以树更矮，千万级数据 3~4 层，一次查询只有几次 IO；B 树非叶子也存数据，节点能放的键少，树更高。"
                    "B+ 树的叶子按顺序链表相连，范围查询和排序只要顺着链表扫，B 树需要中序遍历。"
                    "红黑树是二叉的，数据量大时树高几十层，每层一次 IO。"
                    "哈希表等值查询 O(1)，但不支持范围查询、排序和最左前缀，所以只能做额外的索引类型，不能当默认结构。"
                ),
                "explanation": "这题的关键不是背结论，而是把「减少磁盘 IO」这条主线说清楚。",
            },
        ],
    },
    {
        "code": "mysql-08",
        "subject": "MySQL",
        "stage": "索引与优化",
        "runner": "sql",
        "title": "索引失效与 EXPLAIN",
        "summary": "建了索引也可能用不上，先看执行计划",
        "definition": (
            "索引建了不等于用得上。**会让索引失效的常见写法**（面试必背）：\n\n"
            "- **对索引列做函数或运算**：`WHERE YEAR(created_at) = 2026`、`WHERE id + 1 = 10` → "
            "改成 `created_at >= '2026-01-01' AND created_at < '2027-01-01'`\n"
            "- **隐式类型转换**：`phone` 是 `VARCHAR`，却写 `WHERE phone = 13800000000`（不加引号）→ 全表扫\n"
            "- **前导模糊匹配**：`LIKE '%abc'` 用不上索引，`LIKE 'abc%'` 可以\n"
            "- **`OR` 两边有一边没索引**：整个条件退化成全表扫\n"
            "- **否定条件**：`!=`、`NOT IN`、`IS NOT NULL` 等，优化器常判定「全表扫更划算」\n\n"
            "**联合索引的最左前缀原则**：`(a, b, c)` 能支撑 `a`、`a,b`、`a,b,c` 的查询；"
            "跳过 `a` 直接查 `b` 用不上；范围条件后面的列也用不上。\n\n"
            "**`EXPLAIN` 是排查入口**，重点看四列：\n\n"
            "- `type`：`const > eq_ref > ref > range > index > ALL`，出现 **`ALL` 就是全表扫描**\n"
            "- `key`：实际用了哪个索引，`NULL` 表示没用上\n"
            "- `rows`：预估要扫描多少行，越小越好\n"
            "- `Extra`：出现 `Using filesort`（额外排序）或 `Using temporary`（临时表）就要警惕\n\n"
            "**它解决什么问题**：把「这条 SQL 到底怎么执行的」变成可观察的事实，而不是靠猜。"
        ),
        "plain": (
            "索引像**书后面的索引页**，但有些查法会让索引页白建。\n\n"
            "你想查「2026 年出版的书」，索引却是按**出版日期**建的。你说「出版年份等于 2026」，"
            "数据库只好把每本书的日期都拿出来算一遍年份 —— 等于从头翻书。"
            "写成「日期在某个区间里」，它才能直接翻到索引对应的位置。这就是「**对列做函数，索引就失效**」。\n\n"
            "最左前缀则像**查电话簿**：电话簿按「姓 + 名」排。你说「姓张、名三」能找到；"
            "只报个「名叫三」就找不到 —— 顺序是固定的，跳过姓就用不上这个排序。"
        ),
        "example": (
            "表结构：orders(id, order_no, user_id, amount, created_at)，order_no 上有索引\n"
            "\n"
            "SQL：\n"
            "SELECT order_no, amount\n"
            "FROM orders\n"
            "WHERE order_no LIKE 'A%'\n"
            "ORDER BY order_no;"
        ),
        "example_output": "A1001 | 100\nA1002 | 200\nAB300 | 400",
        "pitfalls": [
            "**`EXPLAIN` 里 `type=ALL` 就是全表扫描**：排查时先看 `type` 和 `key`，再看 `rows`；`Extra` 里的 `Using filesort` / `Using temporary` 都是常见慢查询信号。",
            "**对列做函数或运算一定失效**：`WHERE DATE(created_at) = '2026-01-01'` 改成 `WHERE created_at >= '2026-01-01' AND created_at < '2026-01-02'`。",
            "**隐式类型转换是最隐蔽的坑**：字符串列 `phone` 写成 `WHERE phone = 13800000000`（不加引号），MySQL 会把列转成数字再比，索引直接失效。",
            "**`EXPLAIN` 的 `rows` 只是估算**：它基于统计信息，可能偏差很大。要准确判断得用 `EXPLAIN ANALYZE`（MySQL 8.0.18+）或慢查询日志里的实际扫描行数。",
        ],
        "task": (
            "表 `orders(id, order_no, user_id, amount, created_at)`，`order_no` 是订单号（TEXT）。\n\n"
            "请查出 **`order_no` 以字母 A 开头**的订单，输出 `order_no` 和 `amount` 两列，"
            "按 `order_no` 从小到大排序。"
        ),
        "setup": (
            "DROP TABLE IF EXISTS orders;\n"
            "CREATE TABLE orders (\n"
            "    id INTEGER PRIMARY KEY,\n"
            "    order_no TEXT,\n"
            "    user_id INTEGER,\n"
            "    amount INTEGER,\n"
            "    created_at TEXT\n"
            ");\n"
            "INSERT INTO orders (id, order_no, user_id, amount, created_at) VALUES\n"
            "    (1, 'A1001', 1, 100, '2026-01-05'),\n"
            "    (2, 'A1002', 2, 200, '2026-01-06'),\n"
            "    (3, 'B2001', 1, 300, '2026-02-01'),\n"
            "    (4, 'AB300', 3, 400, '2026-02-11'),\n"
            "    (5, 'C1234', 4, 500, '2026-03-01'),\n"
            "    (6, 'BA400', 2, 600, '2026-03-05');\n"
        ),
        "starter": (
            "-- 表 orders(id, order_no, user_id, amount, created_at)\n"
            "-- 查出 order_no 以 A 开头的订单，按 order_no 升序\n"
            "SELECT order_no, amount\n"
            "FROM orders\n"
            "WHERE "
        ),
        "hint": "用 `order_no LIKE 'A%'`（前缀匹配能走索引，别写 `LIKE '%A%'`），最后 `ORDER BY order_no`。",
        "sql_setup": (
            "DROP TABLE IF EXISTS orders;\n"
            "CREATE TABLE orders (\n"
            "    id INTEGER PRIMARY KEY,\n"
            "    order_no TEXT,\n"
            "    user_id INTEGER,\n"
            "    amount INTEGER,\n"
            "    created_at TEXT\n"
            ");\n"
            "INSERT INTO orders (id, order_no, user_id, amount, created_at) VALUES\n"
            "    (1, 'A1001', 1, 100, '2026-01-05'),\n"
            "    (2, 'A1002', 2, 200, '2026-01-06'),\n"
            "    (3, 'B2001', 1, 300, '2026-02-01'),\n"
            "    (4, 'AB300', 3, 400, '2026-02-11'),\n"
            "    (5, 'C1234', 4, 500, '2026-03-01'),\n"
            "    (6, 'BA400', 2, 600, '2026-03-05');\n"
        ),
        "sql_expect": [["A1001", 100], ["A1002", 200], ["AB300", 400]],
        "sql_ordered": True,
        "sql_hint_cols": ["order_no", "amount"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面的 `WHERE` 条件里，哪一条**用不上**索引？",
                "options": [
                    "WHERE YEAR(created_at) = 2026",
                    "WHERE created_at >= '2026-01-01'",
                    "WHERE order_no LIKE 'A%'",
                    "WHERE user_id = 5",
                ],
                "answer_index": 0,
                "explanation": (
                    "`YEAR(created_at)` 对索引列做了函数运算，索引里存的是原始值，没法用来定位，只能逐行计算。"
                    "改成范围条件 `created_at >= '2026-01-01' AND created_at < '2027-01-01'` 就能走索引。"
                ),
            },
            {
                "type": "choice",
                "stem": "联合索引 `(a, b, c)`，下面哪个查询用不上这个索引？",
                "options": ["WHERE b = 2", "WHERE a = 1 AND b = 2", "WHERE a = 1 AND b = 2 AND c = 3", "WHERE a = 1"],
                "answer_index": 0,
                "explanation": "最左前缀原则：必须从索引的第一列 `a` 开始用。跳过 `a` 直接查 `b`，索引完全用不上。",
            },
            {
                "type": "judge",
                "stem": "`EXPLAIN` 结果的 `type` 列出现 `ALL`，说明这条 SQL 走的是全表扫描。",
                "answer": True,
                "explanation": "`type=ALL` 就是全表扫描，是排查慢查询时第一个要消除的信号；`key` 列同时会显示 NULL。",
            },
            {
                "type": "blank",
                "stem": "`EXPLAIN` 结果里，`type` 列的值是 ___ 时表示全表扫描（填一个大写英文单词）。",
                "answer": "ALL",
                "accept": ["all"],
                "hint": "一个英文单词，三个字母",
                "explanation": "访问类型从好到坏是 `const > eq_ref > ref > range > index > ALL`，`ALL` 是最差的。",
            },
            {
                "type": "short",
                "stem": "面试官：线上一条查询突然变慢，你的排查步骤是什么？",
                "keywords": ["慢查询日志", "EXPLAIN", "type/key/rows", "索引失效", "数据量变化", "回表与排序"],
                "reference": (
                    "先定位：从慢查询日志或监控里找到具体是哪条 SQL、什么时候开始慢的。"
                    "然后 `EXPLAIN` 看执行计划，重点看 `type` 是不是 `ALL`、`key` 是不是 NULL、`rows` 预估多少。"
                    "常见原因有几类：索引失效（对列做函数、隐式类型转换、前导 %、OR）；"
                    "数据量涨了导致优化器换了执行计划；`Extra` 出现 `Using filesort` / `Using temporary`。"
                    "确定原因后再对症处理：改写 SQL 让条件能走索引、补合适的联合索引、或者把深分页改成游标分页。"
                ),
                "explanation": "这类题考的是排查路径是否成体系，答「先 EXPLAIN 再逐项排除」比直接甩结论更得分。",
            },
        ],
    },
    {
        "code": "mysql-09",
        "subject": "MySQL",
        "stage": "事务与设计",
        "runner": "sql",
        "title": "事务 ACID 与 MVCC",
        "summary": "要么全成功，要么全失败",
        "definition": (
            "**事务是一组「要么全成功、要么全失败」的 SQL**。转账就是标准例子：扣 A 的钱和加 B 的钱"
            "必须在同一个事务里。\n\n"
            "**ACID 分别靠什么实现**（面试必答）：\n\n"
            "- **A 原子性**（Atomicity）：事务内的操作不可分割 —— 靠 **undo log** 回滚\n"
            "- **C 一致性**（Consistency）：事务前后数据满足业务约束（总金额不变）—— 是 A、I、D 共同服务的**目的**\n"
            "- **I 隔离性**（Isolation）：并发事务互不干扰 —— 靠 **锁 + MVCC**\n"
            "- **D 持久性**（Durability）：提交后即使断电也不丢 —— 靠 **redo log**\n\n"
            "**MVCC（多版本并发控制）** 是 InnoDB 实现隔离性的核心：每行数据带隐藏的 `trx_id` 和回滚指针，"
            "修改时不覆盖原数据，而是写 undo log 形成**版本链**；读取时根据 **Read View** 判断哪个版本对自己可见。\n\n"
            "效果就是：**普通 `SELECT`（快照读）不加锁**，读写互不阻塞 —— 这是 MySQL 并发能力的关键。"
            "而 `SELECT ... FOR UPDATE`、`UPDATE`、`DELETE` 是**当前读**，会读最新版本并加锁。\n\n"
            "**它解决什么问题**：让并发操作下的数据保持一致，同时尽量不牺牲并发度。"
        ),
        "plain": (
            "事务像**转账的两步必须绑在一起**。如果只扣了钱没加钱，账就崩了，所以你希望它们**共生死** —— "
            "这就是原子性。\n\n"
            "MVCC 可以用**给数据拍快照**来理解：你开始读的时候，数据库给了你一个「时间点」；"
            "之后别人改了数据，你看到的仍是那个时间点的版本。于是他们改他们的、你读你的，谁也不等谁。"
            "旧版本也不丢，用 undo log 串成「版本链」，谁需要哪一版就取哪一版。\n\n"
            "代价是：你读到的可能不是最新值 —— 这叫**快照读**。要读最新值并且锁住它，就得写 "
            "`SELECT ... FOR UPDATE`，这叫当前读。"
        ),
        "example": (
            "表结构：accounts(id, owner, balance, init_balance)\n"
            "balance 是当前余额，init_balance 是初始余额；一次正常的转账不会改变两者之差的总和\n"
            "\n"
            "SQL（查出被改动过余额的账户，用于对账）：\n"
            "SELECT owner, balance, init_balance\n"
            "FROM accounts\n"
            "WHERE balance != init_balance\n"
            "ORDER BY id;"
        ),
        "example_output": "小明 | 1200 | 1000\n小红 | 2300 | 2500",
        "pitfalls": [
            "**`AUTOCOMMIT` 默认是开的**：每条 SQL 自己就是一个事务，执行完立刻提交。要手动控制必须先 `BEGIN` / `START TRANSACTION`，再 `COMMIT` 或 `ROLLBACK`。",
            "**事务要尽量短**：事务开着不提交会一直占着锁和 undo log，长事务是线上最常见的事故来源之一。",
            "**别在事务里做网络调用或等用户输入**：调 RPC、发消息这类耗时操作放进事务，会把锁持有时间拉长几个数量级。",
            "**`redo log` 和 `undo log` 别搞反**：redo log 保证**崩溃后能恢复已提交的数据**（持久性），undo log 保证**能回滚**并提供 MVCC 需要的旧版本。",
        ],
        "task": (
            "表 `accounts(id, owner, balance, init_balance)`：`balance` 是当前余额，`init_balance` 是初始余额。\n"
            "一次正确的转账应该让所有账户的 `balance` 之和仍然等于 `init_balance` 之和。\n\n"
            "请查出**余额和初始余额不一致（也就是被转账改动过）的账户**，输出 `owner`、`balance`、`init_balance` "
            "三列，按 `id` 从小到大排序。"
        ),
        "setup": (
            "DROP TABLE IF EXISTS accounts;\n"
            "CREATE TABLE accounts (\n"
            "    id INTEGER PRIMARY KEY,\n"
            "    owner TEXT,\n"
            "    balance INTEGER,\n"
            "    init_balance INTEGER\n"
            ");\n"
            "INSERT INTO accounts (id, owner, balance, init_balance) VALUES\n"
            "    (1, '小明', 1200, 1000),\n"
            "    (2, '小红', 2300, 2500),\n"
            "    (3, '小刚', 0,    0),\n"
            "    (4, '小美', 800,  800),\n"
            "    (5, '小强', 3200, 3200),\n"
            "    (6, '小丽', 1500, 1500);\n"
        ),
        "starter": (
            "-- 表 accounts(id, owner, balance, init_balance)\n"
            "-- 查出 balance 与 init_balance 不一致的账户（余额被改过）\n"
            "SELECT owner, balance, init_balance\n"
            "FROM accounts\n"
            "WHERE "
        ),
        "hint": "用 `WHERE balance != init_balance` 做对账筛选，最后 `ORDER BY id`。",
        "sql_setup": (
            "DROP TABLE IF EXISTS accounts;\n"
            "CREATE TABLE accounts (\n"
            "    id INTEGER PRIMARY KEY,\n"
            "    owner TEXT,\n"
            "    balance INTEGER,\n"
            "    init_balance INTEGER\n"
            ");\n"
            "INSERT INTO accounts (id, owner, balance, init_balance) VALUES\n"
            "    (1, '小明', 1200, 1000),\n"
            "    (2, '小红', 2300, 2500),\n"
            "    (3, '小刚', 0,    0),\n"
            "    (4, '小美', 800,  800),\n"
            "    (5, '小强', 3200, 3200),\n"
            "    (6, '小丽', 1500, 1500);\n"
        ),
        "sql_expect": [["小明", 1200, 1000], ["小红", 2300, 2500]],
        "sql_ordered": True,
        "sql_hint_cols": ["owner", "balance", "init_balance"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "事务的持久性（Durability）靠什么保证？",
                "options": ["redo log", "undo log", "MVCC", "binlog"],
                "answer_index": 0,
                "explanation": (
                    "redo log 是物理日志，事务提交时先写 redo log（WAL），崩溃重启后可以据此把已提交的修改重放回来。"
                    "undo log 管回滚和 MVCC，binlog 是 MySQL Server 层的归档日志，用于主从复制和恢复。"
                ),
            },
            {
                "type": "choice",
                "stem": "面试官：MVCC 主要解决了什么问题？",
                "options": [
                    "让读操作不加锁，读写不互相阻塞，提高并发度",
                    "防止 SQL 注入",
                    "加快索引查找速度",
                    "减少磁盘空间占用",
                ],
                "answer_index": 0,
                "explanation": (
                    "MVCC 让普通 `SELECT`（快照读）去读 undo log 里的历史版本，而不是去等写事务的锁，"
                    "所以读写并发不再互相阻塞。它带来的是隔离性，不是安全性或性能优化。"
                ),
            },
            {
                "type": "judge",
                "stem": "在默认隔离级别下，普通的 `SELECT` 属于快照读，不会给数据加锁。",
                "answer": True,
                "explanation": "普通 `SELECT` 是快照读，走 MVCC 读历史版本，不加锁。要加锁读最新值必须显式写 `SELECT ... FOR UPDATE` 或 `LOCK IN SHARE MODE`。",
            },
            {
                "type": "blank",
                "stem": "手动开启一个事务，除了 `START TRANSACTION` 还可以用简写 `___;`（填一个关键字，5 个字母）。",
                "answer": "BEGIN",
                "accept": ["begin"],
                "hint": "一个关键字，5 个字母",
                "explanation": "`BEGIN` 和 `START TRANSACTION` 等价，都表示开启一个显式事务。",
            },
            {
                "type": "short",
                "stem": "面试官：讲讲 ACID 分别靠什么实现的。",
                "keywords": ["原子性 undo log", "持久性 redo log", "隔离性 锁 + MVCC", "一致性 目的", "Read View", "WAL"],
                "reference": (
                    "原子性靠 undo log：修改前的旧值写进 undo log，回滚时反向执行即可。"
                    "持久性靠 redo log：提交时先写日志（WAL），宕机重启后按 redo log 重放已提交的修改。"
                    "隔离性靠锁 + MVCC：普通读走 MVCC 读 Read View 对应的历史版本，写和加锁读靠行锁、间隙锁来互斥。"
                    "一致性是 A、I、D 共同保障的结果，也是事务的最终目的 —— 它更多依赖业务约束（比如总金额不变）。"
                ),
                "explanation": "标准答案就是「undo log / redo log / 锁 + MVCC / 目的」这四句，能说清各自解决什么就够了。",
            },
        ],
    },
    {
        "code": "mysql-10",
        "subject": "MySQL",
        "stage": "事务与设计",
        "runner": "sql",
        "title": "锁、隔离级别与表设计",
        "summary": "没走索引的 UPDATE 会锁全表",
        "definition": (
            "**四种隔离级别**（从低到高，`tx_isolation` 可查）：\n\n"
            "- `READ UNCOMMITTED`：能读到别人**没提交**的数据 → 脏读\n"
            "- `READ COMMITTED`（RC）：只读已提交的，解决脏读；但同一事务内两次读同一行可能不一样 → "
            "**不可重复读**（Oracle、PostgreSQL 默认）\n"
            "- `REPEATABLE READ`（RR）：同一事务内多次读结果一致，解决不可重复读；范围查询可能多出几行 → "
            "**幻读**（**MySQL InnoDB 默认**）\n"
            "- `SERIALIZABLE`：串行执行，最安全也最慢\n\n"
            "InnoDB 在 RR 下用 **Next-Key Lock（记录锁 + 间隙锁）**，基本解决了幻读。\n\n"
            "**行锁的两条铁律**（面试高频）：\n\n"
            "- 只有**走索引**的 `UPDATE` / `DELETE` 才加行锁；**没走索引会锁住扫描过的所有行，等于锁全表**\n"
            "- 多个事务更新多行时要按**相同顺序**，否则容易死锁\n\n"
            "**表设计要点**：字段尽量 `NOT NULL` 并给默认值；一列只存一个值（别用逗号拼 id）；"
            "金额用 `DECIMAL`；枚举用 `TINYINT` 而不是字符串；**冗余字段要慎重**，能用 JOIN 换来的先别提前冗余。"
        ),
        "plain": (
            "隔离级别像**同一间办公室里隔板的高度**：\n\n"
            "- `READ UNCOMMITTED`：没隔板，别人屏幕上打到一半又删掉的内容你都看得见 —— 脏读\n"
            "- `READ COMMITTED`：只在别人**保存那一刻**起才看得见，但你自己前后看两次可能不一样\n"
            "- `REPEATABLE READ`：你一进门就给你拍了张快照，之后一直看这张 —— MySQL 默认这一档\n"
            "- `SERIALIZABLE`：干脆排队，一个人用完另一个再进\n\n"
            "行锁的道理也一样：你以为自己只锁了「那一行」，但如果 SQL 没走索引，MySQL 只能一行行去找，"
            "结果把**整张表**都锁住了 —— 线上那种「莫名其妙锁表」基本都是这么来的。"
        ),
        "example": (
            "表结构：products(id, name, stock) / order_items(id, product_id, qty)\n"
            "用途：把每个商品的下单总量和库存比一比，找出可能超卖的商品\n"
            "\n"
            "SQL：\n"
            "SELECT p.name, p.stock, SUM(o.qty) AS sold\n"
            "FROM products p\n"
            "JOIN order_items o ON o.product_id = p.id\n"
            "GROUP BY p.id, p.name, p.stock\n"
            "HAVING SUM(o.qty) > p.stock\n"
            "ORDER BY sold DESC;"
        ),
        "example_output": "薯片 | 30 | 35\n巧克力 | 20 | 25",
        "pitfalls": [
            "**`UPDATE` 的 `WHERE` 没走索引会锁全表**：InnoDB 会锁住扫描过程中碰到的所有行。线上执行 UPDATE 前一定确认 `WHERE` 能走索引。",
            "**多行更新顺序不一致会死锁**：事务 A 先锁 id=1 再锁 id=2，事务 B 反着来，就会互相等 → 死锁。**统一按 id 升序更新**。",
            "**RR 下 `SELECT ... FOR UPDATE` 是当前读**：它会读最新值并加锁，不是快照。要不要加锁必须明确写出来，别以为事务里读到的永远是快照。",
            "**「先 SELECT 查库存、再 UPDATE 扣减」防不住超卖**：两步之间有时间窗，并发下照样卖超。正确写法是 `UPDATE stock SET stock = stock - 1 WHERE id = ? AND stock >= 1`，然后看影响行数；或用版本号做乐观锁。",
        ],
        "task": (
            "表 `products(id, name, stock)` 和 `order_items(id, product_id, qty)`。\n\n"
            "请查出**下单总量已经超过库存**的商品（也就是可能超卖的商品）：\n"
            "- 只保留真正有下单记录的商品\n"
            "- 输出三列：`name`、`stock`、下单总量（别名 `sold`）\n"
            "- 按 `sold` 从高到低排序"
        ),
        "setup": (
            "DROP TABLE IF EXISTS products;\n"
            "DROP TABLE IF EXISTS order_items;\n"
            "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER);\n"
            "CREATE TABLE order_items (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER);\n"
            "INSERT INTO products (id, name, stock) VALUES\n"
            "    (1, '可乐', 100),\n"
            "    (2, '薯片', 30),\n"
            "    (3, '巧克力', 20),\n"
            "    (4, '矿泉水', 200);\n"
            "INSERT INTO order_items (id, product_id, qty) VALUES\n"
            "    (1, 1, 30),\n"
            "    (2, 1, 40),\n"
            "    (3, 2, 20),\n"
            "    (4, 3, 25),\n"
            "    (5, 2, 15);\n"
        ),
        "starter": (
            "-- 表 products(id, name, stock) 与 order_items(id, product_id, qty)\n"
            "-- 查出下单总量超过库存的商品（超卖排查）\n"
            "SELECT p.name, p.stock, SUM(o.qty) AS sold\n"
            "FROM products p JOIN order_items o ON o.product_id = p.id\n"
        ),
        "hint": "`GROUP BY p.id, p.name, p.stock` 分组，再用 `HAVING SUM(o.qty) > p.stock` 过滤分组，最后 `ORDER BY sold DESC`。",
        "sql_setup": (
            "DROP TABLE IF EXISTS products;\n"
            "DROP TABLE IF EXISTS order_items;\n"
            "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER);\n"
            "CREATE TABLE order_items (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER);\n"
            "INSERT INTO products (id, name, stock) VALUES\n"
            "    (1, '可乐', 100),\n"
            "    (2, '薯片', 30),\n"
            "    (3, '巧克力', 20),\n"
            "    (4, '矿泉水', 200);\n"
            "INSERT INTO order_items (id, product_id, qty) VALUES\n"
            "    (1, 1, 30),\n"
            "    (2, 1, 40),\n"
            "    (3, 2, 20),\n"
            "    (4, 3, 25),\n"
            "    (5, 2, 15);\n"
        ),
        "sql_expect": [["薯片", 30, 35], ["巧克力", 20, 25]],
        "sql_ordered": True,
        "sql_hint_cols": ["name", "stock", "sold"],
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官：MySQL InnoDB 的默认隔离级别是？",
                "options": ["REPEATABLE READ", "READ COMMITTED", "READ UNCOMMITTED", "SERIALIZABLE"],
                "answer_index": 0,
                "explanation": (
                    "InnoDB 默认是 `REPEATABLE READ`（RR），并通过 Next-Key Lock 基本解决了幻读。"
                    "Oracle、PostgreSQL 默认是 `READ COMMITTED`。"
                ),
            },
            {
                "type": "choice",
                "stem": "RR 级别下，InnoDB 靠什么机制基本解决了幻读？",
                "options": [
                    "Next-Key Lock（记录锁 + 间隙锁）",
                    "表级排他锁",
                    "redo log",
                    "只靠 MVCC 快照读",
                ],
                "answer_index": 0,
                "explanation": (
                    "MVCC 能解决快照读下的不一致，但当前读仍可能读到新插入的行。"
                    "Next-Key Lock 把记录本身和记录之间的间隙一起锁住，阻止了别的事务在范围内插入新行。"
                ),
            },
            {
                "type": "judge",
                "stem": "`UPDATE` 语句的 `WHERE` 条件没有走索引时，InnoDB 只会锁住真正命中的那几行。",
                "answer": False,
                "explanation": "没有索引时 InnoDB 只能全表扫描，扫描过程中碰到的行都会被加锁，效果接近锁全表。这是线上「莫名锁表」最常见的原因。",
            },
            {
                "type": "blank",
                "stem": "避免死锁的基本做法之一：多个事务更新多行时按相同顺序，比如统一按主键 ___ 序更新（填「升」或「降」）。",
                "answer": "升",
                "accept": ["升序", "升序更新"],
                "hint": "填一个字",
                "explanation": "所有事务按同一顺序（例如 id 升序）加锁，就不会出现「你等我、我等你」的环路，死锁自然不会有。",
            },
            {
                "type": "short",
                "stem": "面试官：秒杀场景下怎么防止库存超卖？说说你的方案。",
                "keywords": ["UPDATE stock = stock - 1", "WHERE stock >= 1", "影响行数", "乐观锁版本号", "事务", "不要先查再改"],
                "reference": (
                    "核心是不要「先 `SELECT` 查库存、判断够了再 `UPDATE`」，两步之间有并发窗口。"
                    "正确做法是把判断和扣减合并成一条原子更新："
                    "`UPDATE stock SET stock = stock - 1 WHERE id = ? AND stock >= 1`，然后看影响行数，"
                    "返回 0 就说明扣减失败（已售完）。"
                    "如果要支持更复杂的判断，可以用版本号做乐观锁，或者在事务里 `SELECT ... FOR UPDATE` 锁住这一行再改，"
                    "但要保证 `WHERE` 走主键索引，否则会锁表。"
                ),
                "explanation": "「判断和扣减放在同一条 UPDATE 里，再看影响行数」这一句就是标准答案的骨架。",
            },
        ],
    },
]
