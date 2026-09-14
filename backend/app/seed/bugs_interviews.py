"""种子数据：Bug 猎人挑战 + 面试题库。"""
from sqlalchemy.orm import Session

from ..models import BugChallenge, InterviewQuestion

# ================= Bug 猎人 =================
# 每个挑战：buggy_code 含 Bug，fixed_code 为正确实现，test_cases 为 {input: stdin, expected: stdout}
BUGS = [
    # ----- 入门：语法 / 变量 -----
    ("bug-01", "语法错误·遗漏冒号", "修复代码中的语法错误，让函数能正常执行。",
     "语法", 1,
     "def greet(name)\n    return 'Hello, ' + name\n\nprint(greet('Code'))",
     "def greet(name):\n    return 'Hello, ' + name\n\nprint(greet('Code'))",
     [{"input": "", "expected": "Hello, Code"}],
     "def 语句末尾缺少冒号，函数体没有缩进对齐。",
     "观察 def 行结尾是否有冒号"),
    ("bug-02", "逻辑错误·平均值除零", "函数应返回列表平均值，但当列表为空时应返回 0 而不是报错。",
     "逻辑", 1,
     "def average(nums):\n    return sum(nums) / len(nums)\n\nprint(average([1, 2, 3]))\nprint(average([]))",
     "def average(nums):\n    if not nums:\n        return 0\n    return sum(nums) / len(nums)\n\nprint(average([1, 2, 3]))\nprint(average([]))",
     [{"input": "", "expected": "2.0\n0"}],
     "空列表时 len(nums)=0 导致除零错误，需先判空。",
     "空列表是边界条件"),
    ("bug-03", "逻辑错误·反转字符串", "reverse 函数应反转字符串，但当前实现输出错误。",
     "逻辑", 1,
     "def reverse(s):\n    result = ''\n    for ch in s:\n        result = result + ch\n    return result\n\nprint(reverse('abc'))",
     "def reverse(s):\n    result = ''\n    for ch in s:\n        result = ch + result\n    return result\n\nprint(reverse('abc'))",
     [{"input": "", "expected": "cba"}],
     "逐字符拼接时应把新字符放到前面才能实现反转。",
     "检查拼接顺序"),

    # ----- 进阶：逻辑错误 -----
    ("bug-04", "逻辑错误·找最大值", "find_max 应返回列表最大值，但结果总是第一个元素。",
     "逻辑", 2,
     "def find_max(nums):\n    mx = nums[0]\n    for n in nums:\n        if n < mx:\n            mx = n\n    return mx\n\nprint(find_max([3, 7, 2, 9, 1]))",
     "def find_max(nums):\n    mx = nums[0]\n    for n in nums:\n        if n > mx:\n            mx = n\n    return mx\n\nprint(find_max([3, 7, 2, 9, 1]))",
     [{"input": "", "expected": "9"}],
     "找最大值应使用 > 比较更新，当前用 < 找的是最小值且逻辑反了。",
     "比较方向反了"),
    ("bug-05", "逻辑错误·斐波那契", "fib(n) 应返回第 n 个斐波那契数，当前结果不正确。",
     "逻辑", 2,
     "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a = b\n        b = a + b\n    return a\n\nprint(fib(10))",
     "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n\nprint(fib(10))",
     [{"input": "", "expected": "55"}],
     "同时更新 a、b 需要元组解包；分两步更新会丢失旧 a 值导致错误。",
     "注意变量更新顺序"),
    ("bug-06", "逻辑错误·统计次数", "count_char 应统计字符出现次数，但结果把不同字符混在一起。",
     "逻辑", 2,
     "def count_char(s):\n    d = {}\n    for ch in s:\n        d[ch] += 1\n    return d\n\nprint(count_char('hello'))",
     "def count_char(s):\n    d = {}\n    for ch in s:\n        d[ch] = d.get(ch, 0) + 1\n    return d\n\nprint(count_char('hello'))",
     [{"input": "", "expected": "{'h': 1, 'e': 1, 'l': 2, 'o': 1}"}],
     "键不存在时 d[ch] += 1 会抛 KeyError，应使用 get 提供默认值。",
     "字典键不存在会报错"),

    # ----- 困难：性能 / 安全 -----
    ("bug-07", "性能问题·低效拼接", "该函数在输入较大时会非常慢，请优化其时间复杂度。",
     "性能", 3,
     "def build(n):\n    s = ''\n    for i in range(n):\n        s += str(i)\n    return s\n\nprint(build(1000) == ''.join(map(str, range(1000))))",
     "def build(n):\n    parts = []\n    for i in range(n):\n        parts.append(str(i))\n    return ''.join(parts)\n\nprint(build(1000) == ''.join(map(str, range(1000))))",
     [{"input": "", "expected": "True"}],
     "字符串是不可变对象，循环拼接是 O(n²)；改用列表收集再 join 为 O(n)。",
     "字符串不可变，拼接产生大量临时对象"),
    ("bug-08", "性能问题·嵌套循环", "find_dup 查找重复元素，请把 O(n²) 优化为 O(n)。",
     "性能", 3,
     "def find_dup(nums):\n    for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):\n            if nums[i] == nums[j]:\n                return nums[i]\n    return None\n\nprint(find_dup([3, 1, 4, 2, 4]))",
     "def find_dup(nums):\n    seen = set()\n    for n in nums:\n        if n in seen:\n            return n\n        seen.add(n)\n    return None\n\nprint(find_dup([3, 1, 4, 2, 4]))",
     [{"input": "", "expected": "4"}],
     "嵌套循环 O(n²)；用哈希集合记录已见元素，O(n) 完成。",
     "用 set 记录已出现的元素"),
    ("bug-09", "安全问题·校验缺失", "该登录函数在密码错误时仍可能返回成功，请修复鉴权逻辑。",
     "安全", 3,
     "def login(user, pwd):\n    users = {'admin': 'secret'}\n    if user in users:\n        return True\n    if pwd == users.get(user, ''):\n        return True\n    return False\n\nprint(login('admin', 'wrong'))",
     "def login(user, pwd):\n    users = {'admin': 'secret'}\n    if user in users and pwd == users[user]:\n        return True\n    return False\n\nprint(login('admin', 'wrong'))",
     [{"input": "", "expected": "False"}],
     "用户名存在时直接返回 True，绕过了密码校验；应同时校验用户名和密码。",
     "用户名与密码必须同时匹配"),
]


# ================= 面试题库 =================
# (class_key, round_no, category, question, sample_answer, keywords, difficulty)
INTERVIEWS = [
    # ---- 一面·基础面（所有职业通用）----
    ("common", 1, "自我介绍", "请做 1 分钟自我介绍，突出你的技术栈与项目亮点。",
     "结构：姓名学校 → 技术栈（对应岗位）→ 1 个代表性项目（用 STAR 简述）→ 为什么适合这个岗位。控制在 60-90 秒。",
     ["技术栈", "项目", "负责", "结果", "岗位"], 2),
    ("common", 1, "项目介绍", "挑一个你最满意的项目，讲讲它的架构和你的贡献。",
     "用 STAR：背景（解决什么问题）→ 任务（你的职责）→ 行动（技术方案）→ 结果（量化数据）。强调你负责的模块而非整个团队。",
     ["背景", "负责", "架构", "实现", "结果", "量化"], 2),
    ("common", 1, "基础知识", "谈谈你对面向对象三大特性的理解。",
     "封装（隐藏实现细节）、继承（代码复用与扩展）、多态（同一接口不同实现），各举一个实际例子。",
     ["封装", "继承", "多态", "例子"], 2),
    ("common", 1, "学习能力", "最近在学什么新技术？怎么学的？",
     "说一个与岗位相关的新技术，讲清：为什么学 → 学了什么 → 做了什么小实践 → 接下来计划。体现持续学习能力。",
     ["学习", "实践", "计划", "新技术"], 1),

    # ---- 二面·深度面（分职业）----
    ("frontend", 2, "前端深度", "讲讲浏览器从输入 URL 到页面渲染的完整过程。",
     "DNS 解析 → TCP 连接 → HTTP 请求 → 服务器响应 → HTML 解析构建 DOM/CSSOM → 渲染树 → 布局 → 绘制。可补充浏览器缓存、HTTP/2、关键渲染路径优化。",
     ["DNS", "TCP", "DOM", "CSSOM", "渲染", "缓存"], 3),
    ("frontend", 2, "前端深度", "React 中 useState 和 useEffect 的执行时机有什么不同？",
     "useState 在渲染时返回状态与更新函数；useEffect 在渲染提交后执行副作用（异步），依赖数组控制执行。注意闭包陷阱与清理函数。",
     ["useState", "useEffect", "渲染", "依赖", "副作用"], 3),
    ("frontend", 2, "前端深度", "一个页面首屏很慢，你会从哪些方面定位和优化？",
     "定位：Lighthouse / Performance 面板看指标（FCP、LCP、TBT）与请求瀑布图。优化：资源压缩与 CDN、路由懒加载与代码分割、图片懒加载与 WebP、接口合并与缓存、SSR/预渲染、减少主线程长任务。",
     ["首屏", "LCP", "懒加载", "CDN", "缓存"], 3),
    ("backend", 2, "后端深度", "讲讲 TCP 三次握手的过程，以及为什么不是两次？",
     "SYN → SYN+ACK → ACK；两次无法确认双方收发能力，也无法防止历史连接干扰（序列号同步）。",
     ["SYN", "ACK", "序列号", "收发能力", "防重"], 3),
    ("backend", 2, "后端深度", "MySQL 中索引为什么会失效？请列举常见场景。",
     "左前缀破坏、隐式类型转换、对列使用函数/运算、前模糊匹配、OR 连接非索引条件、优化器选择全表扫描等。",
     ["左前缀", "类型转换", "函数", "模糊", "OR"], 3),
    ("backend", 2, "后端深度", "缓存和数据库的一致性怎么保证？",
     "常用 Cache Aside：读时未命中回源并回填，写时先更新数据库再删除缓存（而不是更新缓存）。配合延迟双删、消息队列重试、设置过期时间兜底。对强一致要求高的场景可订阅 binlog 异步刷新。",
     ["缓存", "更新", "失效", "双删", "一致性"], 3),
    ("algorithm", 2, "算法深度", "讲讲动态规划的解题套路，并举例。",
     "定义状态 → 状态转移方程 → 初始化边界 → 遍历顺序；举例爬楼梯/最长公共子序列。强调最优子结构与重叠子问题。",
     ["状态", "转移方程", "边界", "最优子结构", "重叠子问题"], 3),
    ("algorithm", 2, "算法深度", "如何判断一个链表是否有环？时间空间复杂度？",
     "快慢指针：快指针每次走两步，慢指针走一步，相遇则有环。O(n) 时间 O(1) 空间。",
     ["快慢指针", "相遇", "O(n)", "O(1)"], 3),
    ("algorithm", 2, "算法深度", "海量数据中求 Top K，有哪些解法？各自复杂度如何？",
     "① 小顶堆维护 K 个元素：O(n log K)，空间 O(K)，适合流式数据；② 快排 partition 选择：平均 O(n)；③ 分治 + 归并：适合数据量超过内存的场景。",
     ["堆", "partition", "分治", "复杂度"], 3),
    ("testing", 2, "测试深度", "如何为一个登录功能设计测试用例？",
     "功能：正常登录、错误密码、用户不存在、锁定；边界：空输入、超长输入、特殊字符；安全：SQL 注入、暴力破解；兼容：不同浏览器。",
     ["边界", "空值", "安全", "注入", "兼容"], 3),
    ("testing", 2, "测试深度", "单元测试中 Mock 与 Stub 的区别是什么？",
     "Stub 提供预设返回值（状态验证）；Mock 可验证调用行为（行为验证，如是否被调用、调用参数）。",
     ["返回值", "行为验证", "调用"], 3),
    ("testing", 2, "测试深度", "如何设计一个接口自动化测试框架？",
     "分层设计：用例层（YAML/Excel 数据驱动）→ 业务封装层 → 请求层（统一鉴权、重试、日志）。要点：多环境配置隔离、断言与数据库校验、测试数据清理、生成报告并接入 CI 定时执行。",
     ["数据驱动", "断言", "报告", "CI", "分层"], 3),
    ("devops", 2, "运维深度", "Docker 与虚拟机的主要区别是什么？",
     "Docker 共享宿主机内核，通过命名空间+Cgroups 隔离，启动秒级、体积小；虚拟机有独立内核，隔离强、开销大。",
     ["内核", "命名空间", "隔离", "启动", "开销"], 3),
    ("devops", 2, "运维深度", "K8s 中 Deployment 和 StatefulSet 分别适用于什么场景？",
     "Deployment 无状态应用（可任意伸缩替换）；StatefulSet 有状态应用（数据库等），提供稳定网络标识与有序部署。",
     ["无状态", "有状态", "稳定标识", "有序"], 3),
    ("devops", 2, "运维深度", "线上服务 CPU 飙高，你会怎么排查？",
     "先用 top/uptime 确认整体负载与目标进程，再用 top -H 定位高耗 CPU 线程，把线程号转十六进制后到 jstack / perf 里找对应堆栈，必要时用火焰图看热点方法。常见根因：死循环、正则回溯、频繁 GC、锁竞争、流量突增。",
     ["top", "线程", "堆栈", "火焰图", "定位"], 3),

    # ---- 三面·主管面（通用 + 设计）----
    ("common", 3, "系统设计", "如果让你设计一个短链接服务，你会考虑哪些方面？",
     "核心链路：发码（自增/哈希/布隆）→ 存储 → 重定向（302）→ 统计。考虑：全局唯一、并发发码、缓存热点、过期清理、安全（防滥用）。",
     ["唯一", "并发", "缓存", "重定向", "过期", "防滥用"], 3),
    ("common", 3, "团队协作", "当你的方案和资深同事冲突时，你会怎么做？",
     "先数据说话（对比方案利弊）→ 私下沟通 → 必要时小范围灰度验证 → 以团队目标为准，达成一致后坚决执行。",
     ["数据", "沟通", "验证", "团队目标"], 2),
    ("common", 3, "压力场景", "项目上线前发现一个严重 Bug，你会怎么处理？",
     "评估影响面 → 快速定位（看日志/回滚）→ 先止血（回滚/降级）→ 修复并补回归测试 → 复盘总结，避免再次发生。",
     ["评估", "定位", "回滚", "修复", "复盘"], 2),

    # ---- HR 面 ----
    ("common", 4, "职业规划", "你未来 3 年的职业规划是什么？",
     "分阶段：1 年深耕技术基础成为独立开发者 → 2-3 年成长为团队骨干/技术负责人方向，持续学习并沉淀方法论。与岗位发展路径匹配。",
     ["阶段", "技术", "骨干", "规划", "匹配"], 2),
    ("common", 4, "优缺点", "你的优点和缺点分别是什么？",
     "优点：学习能力强、责任心重（配事例）；缺点：有时追求完美导致节奏慢，正在通过优先级管理改进（注意：缺点要真实但可控，并说明改进）。",
     ["优点", "缺点", "改进", "例子"], 2),
    ("common", 4, "薪资期望", "你对薪资的期望是多少？",
     "先反问岗位薪资范围 → 结合自身能力给合理区间 → 强调更看重成长空间，可谈。参考校招价并留出谈判空间。",
     ["范围", "能力", "区间", "成长"], 2),
    ("common", 4, "离职原因", "（社招）你从上家离职的原因是什么？",
     "客观陈述（职业发展空间/方向调整），不贬低前公司，强调积极求变。",
     ["发展", "客观", "积极"], 1),
]


def seed_bugs(db: Session) -> None:
    for code, title, desc, btype, diff, buggy, fixed, tests, expl, hint in BUGS:
        if db.query(BugChallenge).filter(BugChallenge.code == code).first():
            continue
        db.add(BugChallenge(code=code, title=title, description=desc, bug_type=btype,
                            difficulty=diff, buggy_code=buggy, fixed_code=fixed,
                            test_cases=tests, explanation=expl, hint=hint,
                            base_exp=30 + diff * 20, base_coins=10 + diff * 5))
    db.commit()


def seed_interviews(db: Session) -> None:
    for cls, rnd, cat, q, ans, kws, diff in INTERVIEWS:
        exists = db.query(InterviewQuestion).filter(
            InterviewQuestion.question == q).first()
        if exists:
            continue
        db.add(InterviewQuestion(class_key=cls, round_no=rnd, category=cat,
                                 question=q, sample_answer=ans, keywords=kws,
                                 difficulty=diff))
    db.commit()
