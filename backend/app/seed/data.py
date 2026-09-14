"""种子数据：关卡、成就、每日任务、知识库。"""
from datetime import date

from sqlalchemy.orm import Session

from ..models import (Achievement, DailyTask, KnowledgeEntry, Level,
                      UserDailyTask)

# ================= 关卡 =================
LEVELS = [
    # code, name, scene, desc, difficulty, order, unlock_prev, subject, tags, class, exp, coins, hp, icon
    ("nvillage-1", "新手训练营", "新手村", "掌握最基本的编程概念，迈出冒险第一步", 1, 1, "", "软件工程", ["编程基础", "入门"], "", 50, 20, 3, "🏕️"),
    ("ds-1", "数组与链表", "数据结构森林", "线性结构的存储与操作", 1, 2, "nvillage-1", "数据结构", ["数组", "链表"], "", 55, 20, 3, "🌲"),
    ("ds-2", "栈与队列", "数据结构森林", "先进后出与先进先出的智慧", 1, 3, "ds-1", "数据结构", ["栈", "队列"], "", 55, 20, 3, "🌲"),
    ("ds-3", "树与二叉树", "数据结构森林", "层级结构的核心，面试高频", 2, 4, "ds-2", "数据结构", ["二叉树", "树", "遍历"], "", 70, 25, 3, "🌳"),
    ("ds-4", "图与哈希", "数据结构森林", "图的遍历与哈希表的奥秘", 3, 5, "ds-3", "数据结构", ["图", "哈希表", "BFS", "DFS"], "", 85, 30, 3, "🌳"),
    ("algo-1", "排序算法", "算法峡谷", "冒泡到快排，复杂度思维启蒙", 1, 6, "ds-2", "算法", ["排序", "复杂度"], "algorithm", 60, 22, 3, "⛰️"),
    ("algo-2", "查找与递归", "算法峡谷", "二分查找与递归思想", 2, 7, "algo-1", "算法", ["查找", "递归", "二分"], "algorithm", 70, 25, 3, "⛰️"),
    ("algo-3", "动态规划入门", "算法峡谷", "把大问题拆成小问题的艺术", 3, 8, "algo-2", "算法", ["动态规划", "状态转移"], "algorithm", 90, 32, 3, "⛰️"),
    ("os-1", "进程与线程", "操作系统城堡", "并发的基础：进程、线程与调度", 2, 9, "algo-1", "操作系统", ["进程", "线程", "并发"], "backend", 70, 25, 3, "🏰"),
    ("os-2", "内存与文件系统", "操作系统城堡", "虚拟内存、页表与文件管理", 3, 10, "os-1", "操作系统", ["内存", "文件系统", "虚拟内存"], "backend", 85, 30, 3, "🏰"),
    ("net-1", "TCP/IP 基础", "计算机网络迷宫", "三次握手、四次挥手与 IP 寻址", 2, 11, "os-1", "计算机网络", ["TCP", "IP", "握手"], "devops", 70, 25, 3, "🕸️"),
    ("net-2", "HTTP 与网络协议", "计算机网络迷宫", "HTTP 报文、状态码与 HTTPS", 3, 12, "net-1", "计算机网络", ["HTTP", "HTTPS", "状态码"], "frontend", 85, 30, 3, "🕸️"),
    ("db-1", "SQL 基础", "数据库神庙", "增删改查与聚合查询", 2, 13, "net-1", "数据库", ["SQL", "查询"], "backend", 70, 25, 3, "🏛️"),
    ("db-2", "索引与事务", "数据库神庙", "索引原理与 ACID 事务", 3, 14, "db-1", "数据库", ["索引", "事务", "ACID"], "backend", 85, 30, 3, "🏛️"),
    ("db-3", "数据库设计", "数据库神庙", "范式、表设计与性能优化", 4, 15, "db-2", "数据库", ["范式", "设计", "优化"], "backend", 100, 35, 3, "🏛️"),
    ("tech-front", "前端工程", "技术栈之域", "JavaScript 核心与框架工程化", 3, 16, "db-1", "前端", ["JavaScript", "React", "工程化"], "frontend", 85, 30, 3, "🧙"),
    ("tech-back", "后端与微服务", "技术栈之域", "REST、Spring 与微服务架构", 3, 17, "db-2", "后端", ["REST", "Spring", "微服务"], "backend", 85, 30, 3, "⚔️"),
    ("tech-test", "测试与质量", "技术栈之域", "测试金字塔与自动化测试", 3, 18, "db-1", "测试", ["单元测试", "自动化", "用例设计"], "testing", 80, 28, 3, "🛡️"),
    ("tech-ops", "运维与云原生", "技术栈之域", "Linux、Docker 与 K8s 容器化", 3, 19, "db-1", "运维", ["Linux", "Docker", "K8s"], "devops", 80, 28, 3, "🐴"),
    ("interview-1", "技术面试冲刺", "面试试炼场", "大厂高频面试题综合演练", 4, 20, "tech-back", "面试专项", ["面试", "综合", "高频"], "", 110, 40, 3, "🎯"),
    ("arch-1", "系统设计与架构", "架构师王座", "高可用、高并发系统设计挑战", 5, 21, "interview-1", "系统设计", ["架构", "高可用", "高并发"], "backend", 130, 50, 3, "👑"),
]

# ================= 成就 =================
ACHIEVEMENTS = [
    ("first_step", "初入江湖", "完成第一次知识闯关", "🎖️", "学习", "total_quests", 1, 30, 15),
    ("correct_10", "小试牛刀", "累计答对 10 道题", "⚡", "刷题", "total_correct", 10, 40, 20),
    ("correct_50", "刷题达人", "累计答对 50 道题", "🔥", "刷题", "total_correct", 50, 100, 50),
    ("correct_100", "百题斩", "累计答对 100 道题", "💯", "刷题", "total_correct", 100, 200, 100),
    ("streak_3", "三日之约", "连续签到 3 天", "📅", "学习", "streak_days", 3, 50, 25),
    ("streak_7", "七日坚持", "连续签到 7 天", "🗓️", "学习", "streak_days", 7, 150, 80),
    ("chat_5", "话痨养成", "与 AI 导师对话 5 次", "💬", "学习", "total_chats", 5, 60, 30),
    ("bug_1", "Bug 猎手", "完成 1 次 Bug 猎人挑战", "🐛", "刷题", "total_bugs", 1, 50, 25),
    ("bug_5", "Bug 终结者", "完成 5 次 Bug 猎人挑战", "🐞", "刷题", "total_bugs", 5, 150, 80),
    ("interview_1", "初面体验", "完成 1 次模拟面试", "🎤", "面试", "total_interviews", 1, 80, 40),
    ("interview_3", "面霸养成", "完成 3 次模拟面试", "🏆", "面试", "total_interviews", 3, 200, 100),
    ("level_10", "十级小将", "角色等级达到 10 级", "🚀", "学习", "level_reach", 10, 100, 50),
    ("level_30", "中级工程师", "角色等级达到 30 级", "💎", "学习", "level_reach", 30, 300, 150),
    ("class_5", "全栈挑战者", "通关 5 个不同关卡", "🌐", "学习", "class_quests", 5, 120, 60),
    ("coin_500", "财富积累", "代码币达到 500", "🪙", "学习", "coins", 500, 100, 0),
]

# ================= 每日任务 =================
DAILY_TASKS = [
    ("signin", "每日签到", "每日登录签到，领取签到奖励", "signin", 1, 15, 10, 1),
    ("quest_questions", "完成 3 道题", "在知识闯关中完成 3 道题", "quest_questions", 3, 20, 10, 2),
    ("chat", "与 AI 导师对话", "向 AI 导师提问 1 次", "chat", 1, 15, 8, 3),
    ("quest_pass", "闯过 1 关", "通关任意 1 个知识关卡", "quest_pass", 1, 30, 15, 4),
    ("share", "分享 1 次", "把学习成果分享出去（点击首页分享按钮）", "share", 1, 10, 5, 5),
]

# ================= 知识库 =================
KNOWLEDGE = [
    ("数据结构", "数组与链表", ["数组", "链表", "线性表", "随机访问"],
     "数组是连续内存上的同类型元素集合，支持 O(1) 随机访问，但插入删除需要移动元素为 O(n)。"
     "链表通过指针串联节点，插入删除为 O(1)（已知位置），但随机访问为 O(n)。"
     "选择原则：读多写少用数组，写多读少用链表。"),
    ("数据结构", "栈与队列", ["栈", "队列", "先进后出", "先进先出"],
     "栈（Stack）是后进先出（LIFO）结构，典型应用：函数调用栈、括号匹配、浏览器后退。"
     "队列（Queue）是先进先出（FIFO）结构，典型应用：任务调度、消息队列、BFS 层序遍历。"),
    ("数据结构", "二叉树", ["二叉树", "遍历", "前序", "中序", "后序", "层序"],
     "二叉树每个节点最多两个子节点。遍历方式：前序（根左右）、中序（左根右）、后序（左右根）、层序（BFS）。"
     "二叉搜索树（BST）左小右大，中序遍历得到有序序列。面试高频：翻转二叉树、最近公共祖先、层序遍历。"),
    ("算法", "时间复杂度", ["复杂度", "大O", "时间复杂度"],
     "大 O 表示法描述算法运行时间随输入规模增长的趋势，忽略常数项与低阶项。"
     "常见复杂度：O(1)<O(log n)<O(n)<O(n log n)<O(n²)<O(2ⁿ)。"
     "例如冒泡排序 O(n²)，快速排序平均 O(n log n)，二分查找 O(log n)。"),
    ("算法", "动态规划", ["动态规划", "DP", "状态转移", "最优子结构"],
     "动态规划三要素：最优子结构、重叠子问题、状态转移方程。"
     "步骤：定义状态 → 确定转移方程 → 初始化边界 → 按序计算。"
     "经典题：斐波那契、爬楼梯、背包问题、最长公共子序列。注意空间优化可把二维数组压缩为一维。"),
    ("操作系统", "进程与线程", ["进程", "线程", "并发", "上下文切换"],
     "进程是资源分配的基本单位，拥有独立地址空间；线程是 CPU 调度的基本单位，共享进程资源。"
     "线程切换开销小于进程切换。并发 ≠ 并行：并发是交替执行，并行是同时执行。"
     "经典问题：死锁四条件（互斥、持有并等待、不可剥夺、循环等待）。"),
    ("操作系统", "虚拟内存", ["虚拟内存", "页表", "分页", "缺页"],
     "虚拟内存将进程地址空间映射到物理内存，通过页表管理，实现隔离与扩展。"
     "缺页中断时从磁盘换入页面，页面置换算法有 FIFO、LRU、LFU 等。"
     "分段 vs 分页：分页对程序员透明、无外部碎片；分段按逻辑划分、有外部碎片。"),
    ("计算机网络", "TCP 三次握手", ["TCP", "三次握手", "SYN", "可靠传输"],
     "TCP 三次握手建立连接：①客户端发 SYN；②服务端回 SYN+ACK；③客户端发 ACK。"
     "目的：确认双方收发能力，同步初始序列号，防止历史连接干扰。"
     "四次挥手断开连接：FIN → ACK → FIN → ACK，TIME_WAIT 等待 2MSL 确保最后一个 ACK 可达。"),
    ("计算机网络", "HTTP 与 HTTPS", ["HTTP", "HTTPS", "状态码", "TLS"],
     "HTTP 常见状态码：200 成功、301/302 重定向、400 请求错误、401 未认证、403 禁止、404 不存在、500 服务端错误、502 网关错误。"
     "HTTPS = HTTP + TLS，通过证书认证 + 对称加密传输 + 非对称交换密钥，解决窃听、篡改、伪装三大问题。"
     "HTTP/2 支持多路复用、头部压缩；HTTP/3 基于 QUIC（UDP）。"),
    ("数据库", "索引原理", ["索引", "B+树", "聚簇索引", "回表"],
     "MySQL InnoDB 默认使用 B+ 树索引：非叶子节点存键值，叶子节点存数据并双向链表串联，天然适合范围查询。"
     "聚簇索引（主键）叶子存整行数据；二级索引叶子存主键值，查询非索引列需回表。"
     "索引失效场景：左前缀原则被破坏、隐式类型转换、对列使用函数、OR 连接非索引条件。"),
    ("数据库", "事务 ACID", ["事务", "ACID", "隔离级别", "MVCC"],
     "事务四大特性：原子性（A）、一致性（C）、隔离性（I）、持久性（D）。"
     "隔离级别：读未提交→读已提交→可重复读→串行化，级别越高隔离越好但并发越低。"
     "MySQL 默认可重复读，通过 MVCC（多版本并发控制）+ 间隙锁解决幻读。"),
    ("软件工程", "敏捷开发", ["敏捷", "Scrum", "迭代", "DevOps"],
     "敏捷宣言强调：个体与互动高于流程与工具，可工作软件高于详尽文档，响应变化高于遵循计划。"
     "Scrum 框架：Sprint（迭代）、每日站会、评审会、回顾会。DevOps 强调开发与运维协作、CI/CD 持续交付。"),
    ("软件工程", "设计模式", ["设计模式", "单例", "工厂", "观察者", "SOLID"],
     "创建型：单例、工厂、建造者；结构型：适配器、代理、装饰器；行为型：观察者、策略、模板方法。"
     "SOLID 原则：单一职责、开闭、里氏替换、接口隔离、依赖倒置。"
     "设计模式的本质是应对变化：封装变化点、面向接口编程、组合优于继承。"),
    ("前端", "JavaScript 闭包", ["闭包", "作用域", "JavaScript", "事件循环"],
     "闭包 = 函数 + 其创建时的词法作用域。函数可以访问外部变量，即使外部函数已返回。"
     "用途：私有变量、柯里化、回调保持上下文。注意闭包容易造成内存泄漏。"
     "事件循环：同步代码 → 微任务（Promise）→ 宏任务（setTimeout），微任务优先于宏任务。"),
    ("前端", "React 核心", ["React", "虚拟DOM", "组件", "Hooks"],
     "React 通过虚拟 DOM 减少真实 DOM 操作：状态变化 → 生成新虚拟树 → diff 对比 → 最小化更新。"
     "组件通信：props 向下、回调向上、Context 跨层、状态管理库（Redux/Zustand）。"
     "Hooks 规则：只在顶层调用、只在函数组件调用；useEffect 管理副作用，依赖数组控制执行时机。"),
    ("后端", "REST 与 HTTP 语义", ["REST", "API", "幂等", "HTTP方法"],
     "RESTful API 用 HTTP 方法表达语义：GET 查询（幂等）、POST 创建（非幂等）、PUT 全量更新（幂等）、PATCH 局部更新、DELETE 删除。"
     "幂等：同一请求执行多次结果一致。设计建议：资源命名用名词复数，状态码表达结果。"),
    ("后端", "微服务", ["微服务", "服务拆分", "注册中心", "网关", "熔断"],
     "微服务将单体拆分为独立部署的小服务，通过 REST/RPC 通信。"
     "核心组件：注册中心（Nacos/Consul）、API 网关（路由/鉴权/限流）、配置中心、链路追踪。"
     "容错：熔断（Circuit Breaker）、降级、限流、重试。拆分依据：业务域边界、独立演进、团队自治。"),
    ("测试", "测试金字塔", ["测试", "单元测试", "集成测试", "E2E", "覆盖率"],
     "测试金字塔：底层大量单元测试（快、稳、定位准）→ 中层少量集成测试 → 顶层少量端到端测试。"
     "单元测试关注单一函数/模块，常用 Mock 隔离依赖；覆盖率指标：行覆盖、分支覆盖、语句覆盖。"
     "用例设计方法：等价类划分、边界值分析、场景法、错误推测法。"),
    ("运维", "Docker 与容器", ["Docker", "容器", "镜像", "K8s", "云原生"],
     "Docker 容器 = 镜像（只读模板）+ 可写层，通过命名空间隔离、Cgroups 限制资源。"
     "Dockerfile 常用指令：FROM、COPY、RUN、CMD/ENTRYPOINT、EXPOSE。"
     "K8s 核心对象：Pod（最小调度单元）、Deployment（无状态应用）、Service（负载均衡）、ConfigMap/Secret（配置）。"
     "云原生三要素：容器化、微服务、声明式编排（CI/CD 自动化）。"),
]


# ================= 初始化 =================
def seed_levels(db: Session) -> None:
    for code, name, scene, desc, diff, order, prev, subject, tags, cls, exp, coins, hp, icon in LEVELS:
        if db.query(Level).filter(Level.code == code).first():
            continue
        db.add(Level(code=code, name=name, scene=scene, description=desc,
                     difficulty=diff, order_no=order, unlock_prev=prev,
                     subject=subject, tags=tags, recommended_class=cls,
                     base_exp=exp, base_coins=coins, hp=hp, icon=icon))
    db.commit()


def seed_achievements(db: Session) -> None:
    for code, name, desc, icon, cat, ctype, cval, exp, coins in ACHIEVEMENTS:
        if db.query(Achievement).filter(Achievement.code == code).first():
            continue
        db.add(Achievement(code=code, name=name, description=desc, icon=icon,
                           category=cat, condition_type=ctype, condition_value=cval,
                           exp_reward=exp, coin_reward=coins))
    db.commit()


def seed_daily_tasks(db: Session) -> None:
    for code, name, desc, ttype, tval, exp, coins, sort in DAILY_TASKS:
        if db.query(DailyTask).filter(DailyTask.code == code).first():
            continue
        db.add(DailyTask(code=code, name=name, description=desc, target_type=ttype,
                         target_value=tval, exp_reward=exp, coin_reward=coins, sort=sort))
    db.commit()


def seed_knowledge(db: Session) -> None:
    for subject, topic, keywords, content in KNOWLEDGE:
        exists = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.topic == topic).first()
        if exists:
            continue
        db.add(KnowledgeEntry(subject=subject, topic=topic, keywords=keywords,
                              content=content))
    db.commit()
