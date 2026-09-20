"""数据结构：复杂度、线性结构、树与堆、查找排序与图。

按"面试笔试高频"的顺序编排，动手题用 Python 实现，由服务端断言判定。
"""

LESSONS: list[dict] = [
    # ------------------------------------------------------------------ ds-01
    {
        "code": "ds-01",
        "subject": "数据结构",
        "stage": "复杂度与线性结构",
        "runner": "none",
        "title": "复杂度分析",
        "summary": "先算清楚跑多快，再决定写什么代码",
        "definition": (
            "**大 O 表示的是「上界」，描述 n 趋向无穷时运算量的增长速度**，"
            "它忽略常数和低阶项：`3n + 100` 记作 `O(n)`，`n² + n log n` 记作 `O(n²)`。\n\n"
            "常见复杂度从快到慢：\n\n"
            "- `O(1)` 常数：哈希取值、数组随机访问 `nums[i]`\n"
            "- `O(log n)` 对数：二分查找、堆的插入与删除、平衡树的查找\n"
            "- `O(n)` 线性：一次遍历、哈希表的一次 rehash\n"
            "- `O(n log n)` 线性对数：快排/归并/堆排序、高效排序的下界\n"
            "- `O(n²)` 平方：双重循环、冒泡/插入/选择排序\n"
            "- `O(2ⁿ)`、`O(n!)`：递归穷举子集、全排列 —— 面试里出现基本就是让你优化\n\n"
            "**空间复杂度**同样的记法，但要**把递归的调用栈算进去**："
            "递归深度为 h 的遍历，额外空间是 `O(h)`，不是 `O(1)`。\n\n"
            "两个必须区分开的词：**平均复杂度**（期望值，哈希表 `O(1)`、快排 `O(n log n)`）"
            "和**最坏复杂度**（悲观保证，哈希表 `O(n)`、快排 `O(n²)`）。"
            "面试官问「这个操作多快」时，回答里必须自己点明是哪一个。"
        ),
        "plain": (
            "复杂度回答的是一个问题：**数据量翻倍，耗时会变成几倍？**\n\n"
            "- `O(1)`：n 从 1 万到 100 万，耗时纹丝不动\n"
            "- `O(n)`：耗时跟着涨 100 倍\n"
            "- `O(n²)`：耗时涨 10000 倍 —— 这就是「本地测试很快、线上直接超时」的根源\n\n"
            "工程上有个很好用的经验值：**Python 每秒大约能做 10⁷~10⁸ 次简单运算**。"
            "于是可以倒推能写什么：\n\n"
            "| n 量级 | 能承受的复杂度 |\n"
            "| --- | --- |\n"
            "| 20 以内 | `O(2ⁿ)` 穷举 |\n"
            "| 5000 以内 | `O(n²)` 可以赌一把 |\n"
            "| 10⁵ | 最多 `O(n log n)` |\n"
            "| 10⁶ 以上 | 必须 `O(n)` 或 `O(log n)` |\n\n"
            "**所以面试里的第一句话永远是先问数据量**。n 只有 100 的时候，`O(n²)` 就是最优解，"
            "强行上哈希表反而更难读、常数更大。"
        ),
        "example": (
            "def count_ops(n):\n"
            "    ops = 0\n"
            "    for i in range(n):        # 执行 n 次\n"
            "        ops += 1\n"
            "    for i in range(n):        # 执行 n * n 次\n"
            "        for j in range(n):\n"
            "            ops += 1\n"
            "    return ops\n"
            "\n"
            "print(count_ops(10))    # 10 + 100\n"
            "print(count_ops(20))    # 20 + 400\n"
            "\n"
            "# 同样的代码，把「输入翻倍」和「耗时翻倍」对上：\n"
            "print('n 翻倍后，平方项涨了', (count_ops(20) - 20) / (count_ops(10) - 10), '倍')"
        ),
        "example_output": "110\n420\nn 翻倍后，平方项涨了 4.0 倍",
        "pitfalls": [
            "**只算最显眼的那层循环**：`for i in range(n): if x in my_list:` 看起来是一层循环，但 `x in list` 本身是 `O(n)`，整体是 `O(n²)`。**循环体里调用的操作本身有复杂度**，这是最常见的翻车点。",
            "**忘了 `list.insert(0, x)` / `pop(0)` / 字符串 `+=` 都是 `O(n)`**：写在循环里就变成平方级。要频繁头部插入用 `deque`，要频繁拼接字符串用 `list.append` 最后 `join`。",
            "**空间复杂度漏算递归栈**：树遍历即使不建任何列表，递归版本的空间也是 `O(h)`（h 为树高）；深度过大还会直接 `RecursionError`。答「空间 `O(1)`」会被追问。",
            "**拿大 O 当耗时绝对值，又不区分平均和最坏**：`O(n log n)` 的函数在小数据上经常跑不过 `O(n²)`，因为常数差了几十倍，所以答之前先问数据量；同时哈希表、快排都是「平均好看、最坏难看」的例子，主动说明比等着被追问更好。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问你：这段代码的时间复杂度是多少？\n"
                    "```\nfor i in range(n):\n    j = 1\n    while j < n:\n        j *= 2\n```"
                ),
                "options": ["O(n log n)", "O(n²)", "O(n)", "O(log n)"],
                "answer_index": 0,
                "explanation": (
                    "外层执行 n 次，内层 `j` 每次翻倍，从 1 到 n 只需要 `log₂n` 次。相乘就是 `O(n log n)`。"
                    "看到 `j *= 2`、`j //= 2`、`mid = (lo+hi)//2` 这类「每次砍一半」的写法，就是 log 的信号。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "面试官问：哈希表查找平均是 O(1)，为什么最坏会退化成 O(n)？工程上怎么缓解？"
                ),
                "options": [
                    "所有 key 都冲突到同一个桶里时会逐个比较，退化成链表；靠扩容控制装填因子、桶内转红黑树来缓解",
                    "因为哈希函数本身要遍历整个 key，key 很长时就是 O(n)",
                    "因为哈希表要保持 key 有序，插入时需要移动元素",
                    "因为每次查找都可能触发一次扩容，扩容是 O(n)",
                ],
                "answer_index": 0,
                "explanation": (
                    "平均 O(1) 的前提是「key 均匀散列」。如果哈希函数设计得差或者被恶意构造，"
                    "所有 key 落到同一个桶，查找就退化成在链表里逐个扫描 O(n)。"
                    "工程手段有两个：一是控制装填因子（比如 0.75）及时翻倍扩容，二是桶内先链表、过长时转成红黑树（Java 8 的 HashMap）。"
                ),
            },
            {
                "type": "judge",
                "stem": "在 Python 里用 `x in my_list` 判断元素是否存在，平均时间复杂度是 O(1)。",
                "answer": False,
                "explanation": (
                    "列表没有索引结构，`in` 只能从头逐个比较，是 `O(n)`。要 `O(1)` 得用 `set` 或 `dict`。"
                    "这也是「把列表换成集合」能带来几十倍加速的原因。"
                ),
            },
            {
                "type": "blank",
                "stem": "在一个长度为 n 的列表中，从**头部**插入一个元素 `lst.insert(0, x)`，时间复杂度是 O(___)",
                "hint": "填一个字母",
                "answer": "n",
                "accept": ["n", "N"],
                "explanation": (
                    "头部插入要把后面 n 个元素整体后移一位，是 `O(n)`。"
                    "尾部 `append` 一般是 `O(1)`（偶发扩容时均摊下来仍然是 O(1)）。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：你写了个双重循环处理 10⁵ 条数据，本地用 200 条测都很快，上线后接口超时。"
                    "你会怎么判断问题、怎么改？"
                ),
                "keywords": ["10^8", "超时", "O(n²)", "哈希", "空间换时间", "降复杂度"],
                "reference": (
                    "先算量级：10⁵ 的平方是 10¹⁰ 次操作，远超 Python 每秒约 10⁷~10⁸ 次的能力，必然超时，"
                    "而 200 条只有 4×10⁴ 次，当然「很快」——所以本地小数据测不出问题，得按目标数据量估算。"
                    "接着定位内层循环在干什么：如果是「查找是否存在」「统计次数」「找配对」，就用 dict / set 把内层 O(n) 降到 O(1)，"
                    "整体从 O(n²) 降到 O(n)（典型的空间换时间）。"
                    "如果内层是排序或比较，考虑换成 O(n log n) 的排序或堆。"
                    "改完再按真实数据量压测一遍确认。"
                ),
                "explanation": (
                    "这道题考的是「用复杂度预估性能」的工程习惯：先估量级再动手，而不是本地跑一遍感觉挺快就上线。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-02
    {
        "code": "ds-02",
        "subject": "数据结构",
        "stage": "复杂度与线性结构",
        "runner": "python",
        "title": "数组与链表",
        "summary": "一个能按下标直接跳，一个只能顺着 next 走",
        "definition": (
            "**数组（Python 的 list 是动态数组）**：内存里一块连续空间，"
            "下标 i 的地址 = 起始地址 + i × 元素大小，所以随机访问是 `O(1)`。"
            "代价是插入/删除要挪动元素：尾部 `append` 均摊 `O(1)`，"
            "头部 `insert(0, x)` 是 `O(n)`。\n\n"
            "**链表**：由节点组成，每个节点存 `val` 和指向下一个节点的 `next` 指针。"
            "节点在内存里不连续，所以**必须从头顺着 `next` 找**，访问第 i 个是 `O(n)`；"
            "但已知前驱节点时插入/删除只要改两个指针，是 `O(1)`。\n\n"
            "| 操作 | 数组 | 链表 |\n"
            "| --- | --- | --- |\n"
            "| 按下标访问 | O(1) | O(n) |\n"
            "| 头部插入/删除 | O(n) | O(1) |\n"
            "| 尾部插入 | O(1) 均摊 | O(1)（维护 tail）|\n"
            "| 查找某个值 | O(n) | O(n) |\n"
            "| 额外空间 | 更省（无指针）| 每个节点多一个指针 |\n\n"
            "链表还分单向/双向、带头节点/不带头节点。**面试手写题里 90% 是单链表**。"
        ),
        "plain": (
            "**数组像一排连号的储物柜**：编号 0、1、2……你知道编号就能直接走到那个柜子，"
            "这就是 `O(1)` 随机访问。但要在最前面插一个柜子，后面所有柜子都得往后挪一格 —— `O(n)`。\n\n"
            "**链表像寻宝纸条**：第一张纸条上写着「下一个线索在 3 号箱」，你得一张一张顺着找，"
            "所以找第 100 个要走 100 步。但如果你想在「已知的某张纸条」后面插一张新的，"
            "只要把那张纸条的「下一个」改成新纸条、新纸条指向原来的下一个就行了 —— 改两个指针，与长度无关。\n\n"
            "还有一个实战差别：**数组遍历更快**，因为它内存连续，CPU 缓存命中率高。"
            "所以同样是 `O(n)` 遍历，数组实际能比链表快好几倍。"
            "这就是为什么工程里默认用 `list`，几乎不用手写链表 —— 只有当「头部频繁增删」且数据量大时，"
            "数组的 `O(n)` 挪动才会真的痛。"
        ),
        "example": (
            "nums = [10, 20, 30]\n"
            "nums.append(40)          # 尾部插入，均摊 O(1)\n"
            "print(nums)\n"
            "nums.insert(0, 5)        # 头部插入 O(n)：所有元素后移\n"
            "print(nums)\n"
            "print(nums[2])           # 随机访问 O(1)，直接跳到下标 2\n"
            "\n"
            "class ListNode:                  # 单链表节点\n"
            "    def __init__(self, val, next=None):\n"
            "        self.val = val\n"
            "        self.next = next\n"
            "\n"
            "head = ListNode(1, ListNode(2, ListNode(3)))\n"
            "while head:                      # 只能顺着 next 走\n"
            "    print(head.val)\n"
            "    head = head.next"
        ),
        "example_output": "[10, 20, 30, 40]\n[5, 10, 20, 30, 40]\n20\n1\n2\n3",
        "pitfalls": [
            "**把 list 当队列用**：`lst.pop(0)` 是 `O(n)`，写在循环里直接变 `O(n²)`。要先进先出就用 `collections.deque` 的 `popleft()`。",
            "**改指针前没先保存下一个节点**：`cur.next = prev` 一执行，原来的后继链就断了、再也找不回来。顺序必须是「先存 `nxt = cur.next`，再改 `cur.next`，最后往前走」。",
            "**忘了处理「头节点会变」**：反转、删除头节点的题如果没有哨兵节点，就得写一堆 `if head is None` 的特判。用一个 `dummy = ListNode(0); dummy.next = head` 能把这堆边界一次性消掉。",
            "**在链表上套用数组的思维**：不要写 `while head:` 的同时又想按下标跳到中间 —— 链表没法跳，要找中点只能用快慢指针（slow 走 1 步、fast 走 2 步），一次遍历搞定。",
        ],
        "task": (
            "题目已经给好了单链表节点类 `ListNode`，以及两个辅助函数：`build_list(values)` 把 Python 列表转成链表，"
            "`to_list(head)` 把链表转回列表（用于判定）。\n\n"
            "请实现 `reverse_list(head)`：**反转整条单链表，并返回新的头节点**。\n\n"
            "例：输入 `1 -> 2 -> 3 -> 4 -> 5`，返回 `5 -> 4 -> 3 -> 2 -> 1`。\n\n"
            "注意：`build_list`、`to_list` 是题目给的，不要改；空链表要能正确处理。"
        ),
        "setup": (
            "class ListNode:\n"
            "    def __init__(self, val=0, next=None):\n"
            "        self.val = val\n"
            "        self.next = next\n"
            "\n"
            "def build_list(values):\n"
            "    dummy = ListNode(0)\n"
            "    cur = dummy\n"
            "    for v in values:\n"
            "        cur.next = ListNode(v)\n"
            "        cur = cur.next\n"
            "    return dummy.next\n"
            "\n"
            "def to_list(head):\n"
            "    out = []\n"
            "    while head:\n"
            "        out.append(head.val)\n"
            "        head = head.next\n"
            "    return out\n"
        ),
        "starter": (
            "def reverse_list(head):\n"
            "    # 反转单链表，返回新的头节点\n"
            "    # 提示：需要三个指针 prev / cur / nxt\n"
            "    pass\n"
        ),
        "hint": (
            "三指针套路：`prev = None`，`cur = head`；\n"
            "每轮先 `nxt = cur.next` 把后面的链存住，再 `cur.next = prev` 断链回头，"
            "然后 `prev = cur`、`cur = nxt` 一起往前走。\n"
            "循环结束时 `cur` 是 None，**新的头节点是 `prev`**，返回它。"
        ),
        "checker": """
try:
    assert to_list(reverse_list(build_list([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1], "reverse_list 对 [1,2,3,4,5] 应该返回 5 4 3 2 1，检查循环里指针回头的顺序"
    assert to_list(reverse_list(build_list([1]))) == [1], "只有 1 个节点时应该原样返回那一个节点"
    assert to_list(reverse_list(build_list([]))) == [], "空链表（None）也要能处理，直接返回 None 即可，不要在 None 上取 .next"
    assert to_list(reverse_list(build_list([7, 8]))) == [8, 7], "换个输入验一遍：reverse_list 对任意链表都要成立，[7,8] 反转后是 8 7"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except AttributeError as e:
    print("__FAIL__ 在 None 上取了属性：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "在 Python 里对一个很长的列表执行 `lst.pop(0)`（弹出第一个元素），时间复杂度是？",
                "options": ["O(n)", "O(1)", "O(log n)", "O(n log n)"],
                "answer_index": 0,
                "explanation": (
                    "弹出第一个元素后，后面所有元素都要往前挪一格，是 `O(n)`。"
                    "同理 `lst.insert(0, x)` 也是 `O(n)`。需要频繁从两端增删就用 `collections.deque`。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "面试官问：给你一个单链表，怎么在**只遍历一次**的前提下找到中间节点？"
                ),
                "options": [
                    "快慢指针：slow 每次走 1 步，fast 每次走 2 步，fast 到末尾时 slow 正好在中点",
                    "先遍历一遍数出长度 n，再从头走 n/2 步",
                    "把链表存进列表后用 lst[len(lst)//2] 取出来",
                    "用哈希表记录每个节点的下标，然后查中间那个下标",
                ],
                "answer_index": 0,
                "explanation": (
                    "快慢指针（Floyd）是标准答案：一次遍历、`O(1)` 额外空间。"
                    "B 要遍历两遍；C 和 D 都要额外 `O(n)` 空间，而且把链表结构优势全丢了。"
                    "同一个套路还能判断链表有没有环。"
                ),
            },
            {
                "type": "judge",
                "stem": "数组随机访问是 O(1)，链表随机访问也是 O(1)，只是常数不同。",
                "answer": False,
                "explanation": (
                    "链表必须从头顺着 `next` 一个一个走，访问第 i 个是 `O(n)`，这是量级上的差别，不是常数差别。"
                    "链表的优势在于「已知前驱时的插入/删除」是 `O(1)`，不是访问。"
                ),
            },
            {
                "type": "blank",
                "stem": (
                    "反转链表、删除节点这类题里，为了避免反复处理「头节点会变」的边界，"
                    "通常先造一个不存数据的哨兵节点，习惯上把它命名为 ___"
                ),
                "hint": "一个英文单词",
                "answer": "dummy",
                "accept": ["dummy", "Dummy", "dummy node", "哑节点", "哨兵节点"],
                "explanation": (
                    "`dummy = ListNode(0); dummy.next = head`，最后返回 `dummy.next`。"
                    "有了它，「删除头节点」和「删除中间节点」就是同一套代码，边界讨论直接消失。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：数组和链表各自适合什么场景？你们项目里用列表（list）存数据，为什么不用链表？"
                ),
                "keywords": ["随机访问", "连续内存", "缓存", "O(n)", "头部插入", "deque"],
                "reference": (
                    "数组（list）适合「按下标随机访问多、遍历多、尾部增删」的场景，随机访问 `O(1)`；"
                    "链表适合「头部频繁增删、长度变化剧烈」的场景，已知前驱时增删是 `O(1)`。"
                    "项目里存数据几乎都用 list，因为绝大多数需求是遍历和按下标取，"
                    "而且数组内存连续、CPU 缓存友好，实际遍历比链表快好几倍，还不用为每个元素多存一个指针。"
                    "真有「两端频繁进出」的需求，用 `deque`（双端队列）比手写链表更省事。"
                ),
                "explanation": (
                    "面试官想听的是「你会按实际访问模式选结构」，而不是背表格。"
                    "主动提「缓存友好」和「deque 替代方案」是加分项。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-03
    {
        "code": "ds-03",
        "subject": "数据结构",
        "stage": "复杂度与线性结构",
        "runner": "python",
        "title": "栈与队列",
        "summary": "后进先出和先进先出，一个管回溯一个管排队",
        "definition": (
            "**栈 Stack**：只能在一端（栈顶）进出，**后进先出 LIFO**。"
            "操作 `push`（入栈）和 `pop`（出栈），都是 `O(1)`。\n\n"
            "**队列 Queue**：一端进（队尾）、另一端出（队首），**先进先出 FIFO**。"
            "操作 `enqueue` 和 `dequeue`，都是 `O(1)`。\n\n"
            "Python 里的对应实现：\n\n"
            "- 栈：直接用 `list`，`append()` 入栈、`pop()` 出栈（**只用尾部，两端都 O(1)**）\n"
            "- 队列：用 `collections.deque`，`append()` 入队、`popleft()` 出队\n\n"
            "**栈的经典应用**：括号匹配、表达式求值、函数调用栈、DFS 的迭代实现、"
            "单调栈（求「每个元素右边第一个比它大的数」、柱状图最大矩形）。\n\n"
            "**队列的经典应用**：BFS、任务调度、滑动窗口最大值（单调队列）、"
            "用两个栈实现队列（面试高频手写题）。"
        ),
        "plain": (
            "**栈像一叠盘子**：你只能从最上面拿，也只能往最上面放。所以最后放上去的，最先被拿走。"
            "「撤销操作」「浏览器后退」都是这个逻辑 —— 最近发生的先被撤回。\n\n"
            "**队列像排队买奶茶**：新来的排最后，做得最快的是队首那位。"
            "「打印任务队列」「消息队列」都是这个逻辑 —— 先来先服务。\n\n"
            "为什么要专门讲「用 list 当队列是个坑」？因为 `list` 只在**尾部**快：\n"
            "```\nq = []\nq.append(1)     # O(1)\nq.pop()         # O(1)  —— 从尾部拿，等价于「栈」\nq.pop(0)        # O(n)  —— 从头部拿，后面元素全要前移\n```\n"
            "写成 `q.pop(0)` 的循环就是 `O(n²)`。换 `deque().popleft()` 才是真 `O(1)`。\n\n"
            "反过来也要注意：**`deque` 只在两端快**，按 `d[i]` 取中间元素是 `O(n)`，"
            "它不能完全替代 `list`。"
        ),
        "example": (
            "from collections import deque\n"
            "\n"
            "stack = []\n"
            "stack.append(1)          # push\n"
            "stack.append(2)\n"
            "print(stack.pop())       # 2：后进先出\n"
            "print(stack)\n"
            "\n"
            "q = deque()\n"
            "q.append(1)              # 入队\n"
            "q.append(2)\n"
            "print(q.popleft())       # 1：先进先出\n"
            "print(list(q))\n"
            "\n"
            "# 括号匹配的骨架：左括号入栈，右括号找栈顶配对\n"
            "s = \"([{}])\"\n"
            "pairs = {\")\": \"(\", \"]\": \"[\", \"}\": \"{\"}\n"
            "stack = []\n"
            "ok = True\n"
            "for ch in s:\n"
            "    if ch in \"([{\":\n"
            "        stack.append(ch)\n"
            "    else:\n"
            "        if not stack or stack.pop() != pairs[ch]:\n"
            "            ok = False\n"
            "            break\n"
            "print(ok and not stack)   # True：配对成功且栈已清空"
        ),
        "example_output": "2\n[1]\n1\n[2]\nTrue",
        "pitfalls": [
            "**用 `list` 当队列**：`pop(0)` 是 `O(n)`，在循环里出队会变成 `O(n²)`。队列必须用 `collections.deque` 的 `popleft()`。",
            "**出栈/出队前不判空**：空 `list.pop()` 和空 `deque.popleft()` 都直接抛 `IndexError`，程序崩掉。循环条件里要保证非空，或先判 `if not stack`。",
            "**括号匹配忘了最后检查栈是否为空**：`\"(((\"` 全是很正常地入栈、一次都不报错，最后栈里还留着三个左括号。**结尾必须加 `not stack` 才算通过**。",
            "**以为 `deque` 是万能替代**：`deque` 只在两端是 `O(1)`，按下标访问中间元素是 `O(n)`。需要随机访问还得用 `list`。",
        ],
        "task": (
            "请实现 `is_valid(s)`：判断一个只含 `(` `)` `[` `]` `{` `}` 六种字符的字符串 `s` 是否是**合法的括号序列**。\n\n"
            "合法要求两条同时成立：\n"
            "1. 每个右括号都必须和栈顶的同类型左括号配对（`(]` 不算配对）\n"
            "2. 遍历结束后栈里不能剩下未闭合的左括号\n\n"
            "返回 `True` 或 `False`。空字符串视为合法。\n"
            "判定会换多组输入调用你的函数，所以不能用 `if s == ...` 之类的硬编码。"
        ),
        "setup": "",
        "starter": (
            "def is_valid(s):\n"
            "    # 返回 True / False\n"
            "    # 提示：遇到左括号入栈，遇到右括号检查栈顶\n"
            "    pass\n"
        ),
        "hint": (
            "用一个 `stack = []` 存左括号；字典把右括号映射到对应的左括号：`pairs = {\")\": \"(\", \"]\": \"[\", \"}\": \"{\"}`。\n"
            "遇到左括号 `append`；遇到右括号先判 `if not stack` 直接返回 `False`，"
            "再 `stack.pop()` 和后比较，不等也返回 `False`。\n"
            "循环结束后 `return not stack` —— 这一句最容易漏。"
        ),
        "checker": """
try:
    assert is_valid("()[]{}") == True, "「()[]{}」是合法序列，应该返回 True"
    assert is_valid("(]") == False, "「(]」两边类型不同，不配对，应该返回 False"
    assert is_valid("((") == False, "「((」结尾时栈里还剩一个未闭合的左括号，别忘了最后 return not stack"
    assert is_valid("([{}])") == True, "「([{}])」是正确嵌套，应该返回 True"
    assert is_valid("") == True, "空字符串按定义是合法序列，应该返回 True"
    assert is_valid("([)]") == False, "「([)]」是交叉嵌套而不是正确配对，应该返回 False —— 换个输入再验一遍"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：要在 O(n) 时间内求出「数组中每个元素右边第一个比它大的元素」，用什么结构？"
                ),
                "options": [
                    "单调栈（栈里存的是「还没找到答案的下标」，保持递减）",
                    "普通队列，按顺序出队比较",
                    "小顶堆，每次弹最小值",
                    "哈希表，把元素值当下标",
                ],
                "answer_index": 0,
                "explanation": (
                    "这是单调栈的标志题。遍历数组时维护一个**递减**的栈："
                    "当前元素比栈顶大，说明栈顶那个元素的答案就是当前元素，弹出并记录；"
                    "一直弹到栈顶比自己大为止，再把自己压进去。每个元素只进栈出栈各一次，所以是 `O(n)`。"
                    "堆做不到「右边第一个」这种位置关系。"
                ),
            },
            {
                "type": "choice",
                "stem": "在 Python 里实现一个频繁出队（先进先出）的队列，最合适的容器是？",
                "options": [
                    "collections.deque，用 append 入队、popleft 出队",
                    "list，用 append 入队、pop(0) 出队",
                    "list，用 insert(0, x) 入队、pop() 出队",
                    "set，用 add 入队、pop 出队",
                ],
                "answer_index": 0,
                "explanation": (
                    "`deque` 两端增删都是 `O(1)`。B 和 C 虽然语义正确，但都在头部操作 `O(n)`，"
                    "循环里就是 `O(n²)`；`set` 无序，根本不能当队列。"
                ),
            },
            {
                "type": "judge",
                "stem": "用栈实现 DFS 的迭代版本时，栈里既存节点也要标记「已访问」，否则无向图里会在两个相邻节点之间来回走，永不终止。",
                "answer": True,
                "explanation": (
                    "无向图的边是双向的：从 A 走到 B，处理 B 的邻居时又会看到 A。"
                    "所以必须在**入栈时（或出栈时）就标记 visited**，并在入栈前检查 `if nxt not in visited`。"
                ),
            },
            {
                "type": "blank",
                "stem": "栈的特点是后进先出（LIFO），队列的特点是先进先出，后者的英文缩写是 ___",
                "hint": "四个字母",
                "answer": "FIFO",
                "accept": ["FIFO", "fifo", "First In First Out"],
                "explanation": "FIFO = First In First Out；LIFO = Last In First Out。面试里说术语比说中文更简洁。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：怎么用两个栈实现一个队列？说说入队和出队的过程，以及每个操作的时间复杂度。"
                ),
                "keywords": ["入栈", "出栈", "倾倒", "摊还", "O(1)", "in/out"],
                "reference": (
                    "准备两个栈：`in_stack` 负责入队，`out_stack` 负责出队。"
                    "入队时直接 `in_stack.append(x)`，`O(1)`。"
                    "出队时如果 `out_stack` 非空就 `out_stack.pop()`；如果为空，就把 `in_stack` 里的元素**全部倒过来**压进 `out_stack`，再弹出。"
                    "关键在于每个元素一辈子最多被「倾倒」一次，所以均摊到每次操作是 `O(1)`，"
                    "单次最坏是 `O(n)`（恰好触发倾倒的那一次）。"
                ),
                "explanation": (
                    "面试官真正想听的是「均摊分析」这四个字，只说「出队是 O(n)」会被追问；"
                    "要主动说清「均摊 O(1)、单次最坏 O(n)」。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-04
    {
        "code": "ds-04",
        "subject": "数据结构",
        "stage": "复杂度与线性结构",
        "runner": "python",
        "title": "哈希表与冲突解决",
        "summary": "用哈希函数把 key 变成下标，平均 O(1) 找到它",
        "definition": (
            "哈希表的做法是：用一个**哈希函数** `hash(key)` 把 key 映射到数组下标（叫「桶」），"
            "取值时重算一遍哈希就能直接跳到那个位置，所以平均是 `O(1)`。\n\n"
            "**哈希冲突**是两个不同的 key 算出了同一个下标。这是必然的（key 空间远大于桶数量），"
            "只能解决，不能消除。两大流派：\n\n"
            "**1. 链地址法（拉链法，Separate Chaining）**\n"
            "每个桶挂一个链表，冲突的 key 依次挂在同一个桶里。\n"
            "Java 的 `HashMap`、Python 老版本 dict、Redis 的 dict 都用它。\n\n"
            "**2. 开放寻址法（Open Addressing）**\n"
            "不挂链表，冲突了就按规则找下一个空位：线性探测（+1 往后找）、"
            "二次探测（+1²、-1²、+2²……）、双重哈希（换个哈希函数再算步长）。\n"
            "Python 现在的 dict 就是开放寻址 + 伪随机探测。\n\n"
            "**装填因子 load factor = 元素数 / 桶数量。** 它越高冲突越频繁，"
            "所以要在超过阈值（Java HashMap 是 0.75）时**翻倍扩容并 rehash**。"
            "rehash 单次是 `O(n)`，但均摊到每次插入仍是 `O(1)`。\n\n"
            "**为什么 Java 8 之后 HashMap 要链表转红黑树？**\n"
            "链地址法在极端情况下（哈希函数差、或有人**恶意构造**大量同桶 key 做哈希碰撞攻击）"
            "会退化成一条长链表，查找从 `O(1)` 掉到 `O(n)`。"
            "Java 8 的规则是：**同一个桶里的链表长度达到 8，且桶数组长度达到 64 时，把链表转成红黑树**，"
            "把该桶的查找从 `O(n)` 降到 `O(log n)`；反过来元素减少到 6 时会退化回链表。"
            "为什么要「桶数组 ≥ 64」这个前提？因为桶太少时冲突多是因为表太小，"
            "**扩容比转树更划算**，所以优先扩容。"
        ),
        "plain": (
            "**哈希表像图书馆按索书号分区**：你不用从第一排翻到最后一排，"
            "算一下索书号就知道书在哪个区，直接走过去 —— 这就是 `O(1)`。\n\n"
            "**冲突是必然的**：索书号算法再好，也架不住书太多、区太少，总有几本算到同一个区。\n"
            "链地址法就是「同一个区里摆一排书架，顺着找」；开放寻址法是「这个格子被占了，"
            "那就按规则看下一个格子」。\n\n"
            "**装填因子可以理解成「区里的拥挤程度」**：60% 满的时候顺着找一两步就找到了；"
            "95% 满的时候，一个区里挤了几十本，`O(1)` 就名存实亡。"
            "所以哈希表宁可浪费点内存也要及时扩容 —— **用空间换时间**。\n\n"
            "再看两道「面试官真会问」的题：\n\n"
            "- **为什么桶内链表长了要转红黑树？** 链表只能顺着扫 `O(n)`，红黑树能二分着找 `O(log n)`。"
            "这是给「最坏情况」兜底，不是为了平均值好看。\n"
            "- **为什么 key 要尽量不可变？** 因为 key 一旦被改动，它的哈希值可能就变了，"
            "原来存的位置再也算不出来，那个 entry 就永远丢在表里成为垃圾。"
            "所以 Python 用 tuple/str 当 key，不用 list。"
        ),
        "example": (
            "# 只用 4 个桶的极简「链地址法」哈希表，故意让两个 key 撞在一起\n"
            "BUCKETS = 4\n"
            "\n"
            "def bucket_of(key):\n"
            "    return sum(ord(ch) for ch in key) % BUCKETS\n"
            "\n"
            "for key in [\"apple\", \"banana\", \"pear\", \"kiwi\"]:\n"
            "    print(key, \"-> 桶\", bucket_of(key))\n"
            "\n"
            "# Python 的 dict 就是哈希表：查 key 平均 O(1)，不是逐个比较\n"
            "counts = {}\n"
            "for w in [\"a\", \"b\", \"a\"]:\n"
            "    counts[w] = counts.get(w, 0) + 1\n"
            "print(counts)\n"
            "print(\"a\" in counts)          # O(1)：先算哈希再跳到对应位置\n"
            "print(counts[\"a\"])            # O(1)"
        ),
        "example_output": (
            "apple -> 桶 2\nbanana -> 桶 1\npear -> 桶 0\nkiwi -> 桶 0\n{'a': 2, 'b': 1}\nTrue\n2"
        ),
        "pitfalls": [
            "**用可变对象当 key**：`d[[1, 2]] = 3` 直接报 `TypeError: unhashable type: 'list'`。key 必须可哈希（str、int、tuple）。要拿一组值当 key，先转成 `tuple(...)`。",
            "**自定义对象当 key 时只实现 `__eq__` 没实现 `__hash__`**：Python 会直接把 `__hash__` 置为 None，对象变得不可哈希；反过来只实现 `__hash__` 不实现 `__eq__`，两个「看起来相同」的对象会被当成两个不同的 key，**字典里塞进重复的数据**。",
            "**遍历 dict 时增删键**：`for k in d: del d[k]` 会抛 `RuntimeError: dictionary changed size during iteration`，必须先 `for k in list(d)` 复制一份键。",
            "**以为 `in` 在哪都一样快**：`x in my_dict` / `x in my_set` 是哈希命中 `O(1)`；`x in my_list` 是逐个比较 `O(n)`。10 万个元素时差距是几万倍。",
        ],
        "task": (
            "请实现 `two_sum(nums, target)`：在整数列表 `nums` 中找出**两个数**，使它们相加等于 `target`，"
            "返回这两个数的**下标**（用列表返回，例如 `[0, 1]`）。\n\n"
            "约定：\n"
            "- 保证有且只有一组答案；同一个元素不能用两次\n"
            "- 下标顺序不限（返回 `[1, 0]` 也算对）\n"
            "- **必须用哈希表一次遍历完成，复杂度 O(n)**；写双重循环虽然答案对，但在大数据量下会超时\n\n"
            "例：`two_sum([2, 7, 11, 15], 9)` → `[0, 1]`"
        ),
        "setup": "",
        "starter": (
            "def two_sum(nums, target):\n"
            "    # 一次遍历 + 哈希表\n"
            "    # 提示：边走边记「已经见过的数 -> 它的下标」\n"
            "    pass\n"
        ),
        "hint": (
            "开一个字典 `seen = {}`，遍历 `for i, x in enumerate(nums):` ——\n"
            "先算 `need = target - x`，如果 `need in seen`，直接返回 `[seen[need], i]`；"
            "否则把当前的数记下来：`seen[x] = i`。\n"
            "注意**先查再存**，这样就不会把自己和自己配成一对（解决 `[3, 3]` 这种情况）。"
        ),
        "checker": """
try:
    r1 = two_sum([2, 7, 11, 15], 9)
    assert isinstance(r1, list), "two_sum 应该返回一个列表（两个下标），比如 [0, 1]"
    assert sorted(r1) == [0, 1], "two_sum([2, 7, 11, 15], 9) 应该返回 [0, 1]（因为 2 + 7 = 9）"
    r2 = two_sum([3, 2, 4], 6)
    assert sorted(r2) == [1, 2], "two_sum([3, 2, 4], 6) 应该返回 [1, 2]（因为 2 + 4 = 6），注意不是 [0, 0]"
    r3 = two_sum([3, 3], 6)
    assert sorted(r3) == [0, 1], "two_sum([3, 3], 6) 应该返回 [0, 1]：要先查 need 再存自己，否则同一个元素会被用两次"
    r4 = two_sum(list(range(20000)), 39997)
    assert sorted(r4) == [19998, 19999], "数据量大时也要能用：换成 20000 个数验一遍（答案是 19998 + 19999），说明必须是 O(n) 的哈希写法"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：哈希冲突有哪几种解决方式？Java 8 之后 HashMap 为什么要把链表转成红黑树？"
                ),
                "options": [
                    "链地址法（桶内挂链表）和开放寻址法（线性探测/二次探测/双重哈希）；转红黑树是为了在桶内元素过多时把最坏查找从 O(n) 降到 O(log n)，防哈希碰撞攻击",
                    "一种是扩容，一种是缩容；转红黑树是为了让遍历有序",
                    "只能用开放寻址法；转红黑树是为了减少内存占用",
                    "加锁和去锁两种；转红黑树是为了让并发更安全",
                ],
                "answer_index": 0,
                "explanation": (
                    "先答两类解法，再答 Java 8 的规则：**同一桶链表长度 ≥ 8 且桶数组长度 ≥ 64** 时转红黑树，"
                    "元素减少到 6 再退回链表。目的很明确 —— 平均 `O(1)` 不变，但把最坏情况的桶内查找从 `O(n)` 兜到 `O(log n)`。"
                    "「为什么要有桶数组 ≥ 64 的前提」也是常见追问：表太小时扩容比转树更划算。"
                ),
            },
            {
                "type": "choice",
                "stem": "哈希表在什么时机扩容？扩容时发生了什么？",
                "options": [
                    "装填因子超过阈值（如 0.75）时把桶数组翻倍，并把所有 key 重新哈希搬到新桶里（rehash）",
                    "每次插入都扩容一倍，保证永远不冲突",
                    "元素数量超过 100 万时固定扩容，与装填因子无关",
                    "查询变慢时扩容，扩容只搬新元素，旧元素留在原处",
                ],
                "answer_index": 0,
                "explanation": (
                    "扩容的触发条件是装填因子，扩容动作是「翻倍 + 全量 rehash」，单次 `O(n)`、均摊 `O(1)`。"
                    "C 忽略了装填因子这个关键指标；D 的半搬状态在哈希表里是不可能实现的（那样算不出准确位置）。"
                ),
            },
            {
                "type": "judge",
                "stem": "哈希表查找的最坏时间复杂度是 O(n)。",
                "answer": True,
                "explanation": (
                    "所有 key 都碰撞到同一个桶时，查找退化成在链表里逐个比较，是 `O(n)`。"
                    "所以答「哈希表是 O(1)」时必须补一句「平均 `O(1)`」。"
                    "Java 8 的链表转红黑树把这个最坏情况改善到 `O(log n)`。"
                ),
            },
            {
                "type": "blank",
                "stem": "解决哈希冲突的两大流派是链地址法和 ___ 法（冲突时按探测规则另找一个空桶）",
                "hint": "四个字，或填英文 open addressing",
                "answer": "开放寻址",
                "accept": ["开放寻址", "开放地址", "开放定址", "open addressing", "Open Addressing"],
                "explanation": (
                    "开放寻址不额外挂链表，而是在数组内部按规则找下一个空位："
                    "线性探测 `(h+1) % m`、二次探测 `(h ± i²) % m`、双重哈希 `(h1 + i·h2) % m`。"
                    "Python 的 dict 用的就是开放寻址。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "在 Agent 项目里你要用 dict 缓存「同一个 prompt 的模型返回结果」，避免重复调用模型。"
                    "说说哈希表为什么适合做这件事，以及 key 该怎么设计。"
                ),
                "keywords": ["O(1)", "缓存命中", "不可变", "tuple", "哈希", "命中率"],
                "reference": (
                    "缓存的本质是「用空间换时间」：每次调用前先用 key 在 dict 里查一次，"
                    "命中就跳过模型调用，平均 `O(1)` 的查询代价相对于几秒的模型请求可以忽略不计。"
                    "key 必须是**可哈希且不可变**的，所以不能直接用 list 装参数，"
                    "通常把 (prompt, model, temperature) 拼成一个元组或固定格式的字符串作为 key。"
                    "还要注意命中率问题：temperature 大于 0 时同一个 prompt 的结果本来就有随机性，"
                    "要不要缓存、按什么粒度缓存需要按业务定，通常只在 temperature=0 的场景做缓存。"
                ),
                "explanation": (
                    "这道题把哈希表落到项目里：面试官想听的是「为什么 O(1) 重要」和「key 的不可变性约束」。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-05
    {
        "code": "ds-05",
        "subject": "数据结构",
        "stage": "树与堆",
        "runner": "python",
        "title": "树与二叉树遍历",
        "summary": "四种遍历顺序，以及它们各自能解决什么问题",
        "definition": (
            "**树的术语**：根节点、叶子节点（没有孩子）、父/子节点、"
            "节点的高度（到最深叶子的边数）、树的深度、度（孩子个数）。\n\n"
            "**二叉树**每个节点最多两个子树：`left` 和 `right`。第 k 层最多 `2^(k-1)` 个节点，"
            "高度为 h 的二叉树最多 `2^h - 1` 个节点。\n\n"
            "**四种遍历**（差别只在「什么时候访问根」）：\n\n"
            "- **前序 Preorder**：根 → 左 → 右（用来复制/序列化一棵树）\n"
            "- **中序 Inorder**：左 → 根 → 右（**对 BST 得到有序序列**，最重要的性质）\n"
            "- **后序 Postorder**：左 → 右 → 根（用来先处理完孩子再处理父，如释放内存、算子树高度）\n"
            "- **层序 Level-order（BFS）**：一层一层从左到右，用**队列**实现\n\n"
            "前三种用递归写，每个节点恰好访问一次：时间 `O(n)`；空间是递归栈 `O(h)`，"
            "h 为树高（平衡树 `O(log n)`，最坏退化成链是 `O(n)`）。层序用队列，空间 `O(宽度)`。\n\n"
            "**已知遍历序列能还原树吗？**\n"
            "- 前序 + 中序 ✅ 可以唯一确定\n"
            "- 后序 + 中序 ✅ 可以唯一确定\n"
            "- 前序 + 后序 ❌ **不行**，因为分不清某个只有一个孩子的节点，那个孩子是左还是右"
        ),
        "plain": (
            "**树就是文件夹结构**：根目录下有若干子目录，子目录里还有子目录。"
            "「深度优先」就是一头扎到最深处再回头，「广度优先」就是先把同一层全看完再下一层。\n\n"
            "**递归遍历为什么只要三行？** 因为递归的精髓是："
            "**假设「遍历子树」这件事已经有人帮你做好了**，你只需要决定「先干什么、后干什么」。\n\n"
            "- 前序：先打印自己，再让人帮我遍历左子树，再遍历右子树\n"
            "- 中序：先让人帮我遍历左子树，再打印自己，再遍历右子树\n"
            "- 后序：先左、再右，最后才打印自己\n\n"
            "写递归时**只盯当前节点**：如果它是空就返回（base case），否则按顺序做三件事。"
            "千万别在脑子里展开整棵树 —— 那会绕晕。\n\n"
            "**层序为什么要用队列？** 因为「先来先服务」：先把根所在的一层排进队列，"
            "出队一个就把它两个孩子排到队尾，这样自然就是「从上到下、从左到右」。"
            "如果要求「每层输出一个列表」，只要在每轮循环开始时记下当前队列的长度，"
            "一次处理这么多元素，它们恰好就是同一层。"
        ),
        "example": (
            "from collections import deque\n"
            "\n"
            "class TreeNode:\n"
            "    def __init__(self, val, left=None, right=None):\n"
            "        self.val = val\n"
            "        self.left = left\n"
            "        self.right = right\n"
            "\n"
            "#        1\n"
            "#      /   \\\n"
            "#     2     3\n"
            "#    / \\\n"
            "#   4   5\n"
            "root = TreeNode(1, TreeNode(2, TreeNode(4), TreeNode(5)), TreeNode(3))\n"
            "\n"
            "def preorder(node, out):\n"
            "    if node is None:\n"
            "        return out\n"
            "    out.append(node.val)\n"
            "    preorder(node.left, out)\n"
            "    preorder(node.right, out)\n"
            "    return out\n"
            "\n"
            "def inorder(node, out):\n"
            "    if node is None:\n"
            "        return out\n"
            "    inorder(node.left, out)\n"
            "    out.append(node.val)\n"
            "    inorder(node.right, out)\n"
            "    return out\n"
            "\n"
            "def level_order(node):\n"
            "    if node is None:\n"
            "        return []\n"
            "    q = deque([node])\n"
            "    out = []\n"
            "    while q:\n"
            "        cur = q.popleft()\n"
            "        out.append(cur.val)\n"
            "        if cur.left:\n"
            "            q.append(cur.left)\n"
            "        if cur.right:\n"
            "            q.append(cur.right)\n"
            "    return out\n"
            "\n"
            "print(preorder(root, []))\n"
            "print(inorder(root, []))\n"
            "print(level_order(root))"
        ),
        "example_output": "[1, 2, 4, 5, 3]\n[4, 2, 5, 1, 3]\n[1, 2, 3, 4, 5]",
        "pitfalls": [
            "**递归忘了写 base case，或者忘了空树的返回值**：没写 `if node is None: return []` 就往下取 `node.val`，空节点上直接 `AttributeError`；"
            "而 `inorder(None)` 按约定要返回 `[]`（不是报错、也不是 `None`），判定用例里一定有这一组。",
            "**前中后序记混**：只记「根在第几个被访问」—— 前序根在最前、中序根在中间、后序根在最后。**左永远在右前面**，忘了这一点就会写出 `右→根→左` 这种不存在的遍历。",
            "**层序用 `list` 当队列**：写成 `q.pop(0)` 就是 `O(n)` 出队，整棵树变成 `O(n²)`。用 `collections.deque` 的 `popleft()`。",
            "**以为递归一定安全**：Python 默认递归深度约 1000，一条 10 万节点的链状树会直接 `RecursionError`。工程上深树要改成「显式栈 + while 循环」的迭代写法。",
        ],
        "task": (
            "题目已经给好了二叉树的节点类 `TreeNode`、辅助函数 `build_tree(values)`，以及队列 `deque`。\n\n"
            "`build_tree` 接收的是**层序数组**，`None` 表示空节点。例如 `[1, None, 2, 3]` 表示："
            "根 1，左孩子为空，右孩子是 2，2 的左孩子是 3。\n\n"
            "请实现两个函数：\n"
            "1. `inorder(root)` —— 返回**中序遍历**的值列表；空树返回 `[]`\n"
            "2. `level_order(root)` —— 返回**层序遍历**的值列表（从上到下、每层从左到右）；空树返回 `[]`\n\n"
            "返回值必须是列表（`list`），不要直接 `print`。"
        ),
        "setup": (
            "from collections import deque\n"
            "\n"
            "class TreeNode:\n"
            "    def __init__(self, val=0, left=None, right=None):\n"
            "        self.val = val\n"
            "        self.left = left\n"
            "        self.right = right\n"
            "\n"
            "def build_tree(values):\n"
            "    if not values:\n"
            "        return None\n"
            "    root = TreeNode(values[0])\n"
            "    q = deque([root])\n"
            "    i = 1\n"
            "    while q and i < len(values):\n"
            "        node = q.popleft()\n"
            "        if values[i] is not None:\n"
            "            node.left = TreeNode(values[i])\n"
            "            q.append(node.left)\n"
            "        i += 1\n"
            "        if i < len(values):\n"
            "            if values[i] is not None:\n"
            "                node.right = TreeNode(values[i])\n"
            "                q.append(node.right)\n"
            "            i += 1\n"
            "    return root\n"
        ),
        "starter": (
            "def inorder(root):\n"
            "    # 返回中序遍历的值列表；空树返回 []\n"
            "    pass\n"
            "\n"
            "\n"
            "def level_order(root):\n"
            "    # 返回层序遍历的值列表；空树返回 []\n"
            "    pass\n"
        ),
        "hint": (
            "`inorder` 递归写法：`if root is None: return []`，"
            "然后 `return inorder(root.left) + [root.val] + inorder(root.right)`（这样写最不容易错）。\n\n"
            "`level_order` 用 `deque`：`q = deque([root])`，循环里 `popleft()` 取值，"
            "左右孩子非空就 `append`。注意先判 `root is None` 再建队列。"
        ),
        "checker": """
try:
    assert inorder(build_tree([1, None, 2, 3])) == [1, 3, 2], "inorder 对「根 1、左空、右 2、2 的左孩子 3」应该得到 [1, 3, 2]，顺序是 左-根-右"
    assert inorder(None) == [], "inorder(None) 应该返回空列表 []，别忘了处理空树"
    assert level_order(build_tree([3, 9, 20, None, None, 15, 7])) == [3, 9, 20, 15, 7], "level_order 应该从上到下、每层从左到右，得到 [3, 9, 20, 15, 7]"
    assert level_order(None) == [], "level_order(None) 也要返回 []"
    assert level_order(build_tree([1, 2, 3, 4])) == [1, 2, 3, 4], "换个输入再验一遍：不管树的形状怎样，层序都是逐层从左到右 [1, 2, 3, 4]"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except AttributeError as e:
    print("__FAIL__ 在空节点上取了属性，先判 None：" + str(e))
except TypeError as e:
    print("__FAIL__ 返回的应该是一个列表（list），不是 None 或元组：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "已知一棵二叉树的前序遍历是 [1, 2, 4, 5, 3]，中序遍历是 [4, 2, 5, 1, 3]，它的后序遍历是？"
                ),
                "options": [
                    "[4, 5, 2, 3, 1]",
                    "[4, 2, 5, 3, 1]",
                    "[5, 4, 2, 3, 1]",
                    "[1, 2, 4, 5, 3]",
                ],
                "answer_index": 0,
                "explanation": (
                    "前序第一个 1 是根；在中序里 1 左边是 [4, 2, 5]（左子树）、右边是 [3]（右子树）。"
                    "左子树内前序是 [2, 4, 5]、中序是 [4, 2, 5]，所以 2 是左子树的根，4 是左孩子、5 是右孩子。"
                    "后序按「左 → 右 → 根」就是 4、5、2，再处理右子树 3，最后是根 1，得到 `[4, 5, 2, 3, 1]`。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "面试官问：为什么「前序遍历 + 后序遍历」不能唯一确定一棵二叉树？"
                ),
                "options": [
                    "当某个节点只有一个孩子时，前序和后序都无法判断这个孩子是左孩子还是右孩子",
                    "因为前序和后序里有重复的元素，无法区分",
                    "因为后序遍历会丢失叶子节点的信息",
                    "其实可以唯一确定，只是算法复杂度较高",
                ],
                "answer_index": 0,
                "explanation": (
                    "前序是「根 左 右」，后序是「左 右 根」，两种都只能看出「只有一个孩子」这一个事实，"
                    "但看不出它挂在左边还是右边 —— 于是能构造出两棵不同的树给出完全相同的前序和后序。"
                    "中序之所以关键，是因为它把「左子树」和「右子树」在序列上切开了。"
                ),
            },
            {
                "type": "judge",
                "stem": "对一棵二叉搜索树（BST）做中序遍历，得到的序列一定是升序的。",
                "answer": True,
                "explanation": (
                    "BST 的定义就是「左子树所有节点 < 根 < 右子树所有节点」，"
                    "中序按「左-根-右」访问，正好把这个大小关系展平成递增序列。"
                    "反过来，想验证一棵树是不是 BST，也可以用「中序是否严格递增」。"
                ),
            },
            {
                "type": "blank",
                "stem": "「先访问根，再遍历左子树，最后遍历右子树」这种遍历方式叫 ___ 遍历",
                "hint": "两个字",
                "answer": "前序",
                "accept": ["前序", "先序", "先根", "preorder", "pre-order"],
                "explanation": "前序（先序）= 根左右，中序 = 左根右，后序 = 左右根。记住「根的位置」就够了。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：层序遍历怎么写？如果要求「按层输出，每层一个列表」（比如输出 [[3], [9, 20], [15, 7]]），要怎么改？"
                ),
                "keywords": ["队列", "deque", "popleft", "当前层长度", "for 循环", "两层列表"],
                "reference": (
                    "基础版：用 `deque` 存节点，出队一个就把它非空的左右孩子入队，出队顺序就是层序。"
                    "按层输出要多做一步：**在每一轮 while 开始时先取 `n = len(q)`**，"
                    "这 n 个元素正好是当前这一层，用 `for _ in range(n)` 处理完就是一层，"
                    "把这批值收成一个列表再加进结果。"
                    "复杂度上每个节点进队出队各一次，时间是 `O(n)`，队列最大长度是树的最大宽度，空间是 `O(宽度)`。"
                ),
                "explanation": (
                    "「用当前队列长度切分层」是层序题的核心技巧，LeetCode 102、103、199 都是这个套路。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-06
    {
        "code": "ds-06",
        "subject": "数据结构",
        "stage": "树与堆",
        "runner": "python",
        "title": "二叉搜索树",
        "summary": "左边都比根小、右边都比根大，于是能二分着找",
        "definition": (
            "**二叉搜索树 BST** 的定义（注意是「子树里所有节点」，不是只比孩子）：\n\n"
            "- 左子树中**所有**节点的值 `<` 根的值\n"
            "- 右子树中**所有**节点的值 `>` 根的值\n"
            "- 左右子树本身也都是 BST\n\n"
            "**核心性质**：中序遍历得到严格递增序列。\n\n"
            "**三种操作的复杂度都是 O(h)，h 为树高**：\n\n"
            "- 查找：比根小往左走、比根大往右走，每步淘汰一半（前提是平衡）\n"
            "- 插入：沿着查找路径走到空位，把新节点挂上去\n"
            "- 删除：分三种情况 —— 叶子直接删；只有一个孩子用孩子顶替；"
            "有两个孩子则用**中序后继**（右子树里的最小值，即右子树最左节点）替换值，再递归删除那个后继\n\n"
            "**关键点在于 h**：理想情况下 h = `O(log n)`，但如果你按有序数据（1、2、3、4……）依次插入，"
            "树会退化成一个链表，h = `O(n)`，所有操作都变成 `O(n)`。\n"
            "所以工程上的有序字典（Java `TreeMap`、C++ `std::map`）用的不是裸 BST，"
            "而是**自平衡 BST：AVL 树或红黑树**，它们通过旋转把 h 稳定在 `O(log n)`。"
        ),
        "plain": (
            "**BST 就是「猜数字游戏」的数据结构版本**：我问「大于 50 吗」，你说「大了」，"
            "我就再也不看 50 以上的部分了 —— 这就是二分。BST 把二分查找变成了树形结构，"
            "所以能一边插一边查。\n\n"
            "**验证 BST 是全章最大的坑。** 很多人写：\n"
            "```\nif node.left and node.left.val >= node.val: return False\nif node.right and node.right.val <= node.val: return False\n```\n"
            "只比较**父子**，这是错的。反例：\n"
            "```\n      10\n     /  \\\n    5    15\n        /  \\\n       6    20\n```\n"
            "每个父子关系看起来都对（6 < 15、20 > 15），但 6 在 10 的**右子树**里，"
            "按定义右子树所有值必须大于 10，而 6 < 10，所以这棵树不是 BST。\n\n"
            "正确做法是**带着上下界往下走**：根的范围是 `(-∞, +∞)`；"
            "往左走时上界收紧为当前节点的值，往右走时下界收紧为当前节点的值。"
            "一旦某个节点的值跑到 `[low, high]` 外面，立刻判定不是 BST。"
        ),
        "example": (
            "class TreeNode:\n"
            "    def __init__(self, val, left=None, right=None):\n"
            "        self.val = val\n"
            "        self.left = left\n"
            "        self.right = right\n"
            "\n"
            "def insert(root, val):\n"
            "    if root is None:\n"
            "        return TreeNode(val)\n"
            "    if val < root.val:\n"
            "        root.left = insert(root.left, val)\n"
            "    else:\n"
            "        root.right = insert(root.right, val)\n"
            "    return root\n"
            "\n"
            "root = None\n"
            "for v in [5, 3, 8, 1, 4, 7, 9]:\n"
            "    root = insert(root, v)\n"
            "\n"
            "def search(root, target):\n"
            "    if root is None:\n"
            "        return False\n"
            "    if root.val == target:\n"
            "        return True\n"
            "    return search(root.left, target) if target < root.val else search(root.right, target)\n"
            "\n"
            "print(search(root, 7), search(root, 6))\n"
            "\n"
            "# 只比较父子会判错的那棵树\n"
            "bad = TreeNode(10, TreeNode(5), TreeNode(15, TreeNode(6), TreeNode(20)))\n"
            "\n"
            "def valid(node, low=float(\"-inf\"), high=float(\"inf\")):\n"
            "    if node is None:\n"
            "        return True\n"
            "    if not (low < node.val < high):\n"
            "        return False\n"
            "    return valid(node.left, low, node.val) and valid(node.right, node.val, high)\n"
            "\n"
            "print(bad.left.val < bad.val < bad.right.val)   # 只比父子：看起来是对的\n"
            "print(valid(bad))                               # 带上界：False，6 越过了 10 这条下界"
        ),
        "example_output": "True False\nTrue\nFalse",
        "pitfalls": [
            "**验证 BST 只比较父子节点**：必须传上下界（`low`/`high`）。判据是「每个节点都要落在它所属范围的 `(low, high)` 开区间内」，而不是「比左右孩子大/小」。",
            "**以为 BST 查找一定是 O(log n)**：只有**平衡**时才是。按有序序列插入会退化成链，`h = O(n)`，查找变 `O(n)`。工程上用红黑树/AVL，手写题里才用裸 BST。",
            "**删除有两个孩子的节点时接错子树**：不能用「把右子树整个搬上来顶替」—— 那样会破坏 BST 顺序。标准做法是找到**中序后继**（右子树的最小值，也就是右子树一路往左走到底的那个节点），把它的值复制到待删节点上，再递归删掉那个后继。",
            "**把中序后继当成「右孩子」**：中序后继是右子树里的最小值节点，不一定就是右孩子。写 `succ = node.right` 在右子树层级较深时会出错。",
        ],
        "task": (
            "题目已经给好了 `TreeNode` 和 `build_tree(values)`（层序数组建树，`None` 表示空节点）。\n\n"
            "请实现两个函数：\n"
            "1. `is_valid_bst(root)` —— 判断这棵树是不是合法 BST，返回 `True` / `False`；空树视为合法。"
            "注意要求**严格**：左子树所有值 `<` 根、右子树所有值 `>` 根。\n"
            "2. `search_bst(root, target)` —— 按 BST 的性质查找 `target`，找到返回 `True`，否则 `False`。\n\n"
            "判定里有一棵「每个父子关系看起来都对、但不是 BST」的树，只比较孩子值会判错。"
        ),
        "setup": (
            "from collections import deque\n"
            "\n"
            "class TreeNode:\n"
            "    def __init__(self, val=0, left=None, right=None):\n"
            "        self.val = val\n"
            "        self.left = left\n"
            "        self.right = right\n"
            "\n"
            "def build_tree(values):\n"
            "    if not values:\n"
            "        return None\n"
            "    root = TreeNode(values[0])\n"
            "    q = deque([root])\n"
            "    i = 1\n"
            "    while q and i < len(values):\n"
            "        node = q.popleft()\n"
            "        if values[i] is not None:\n"
            "            node.left = TreeNode(values[i])\n"
            "            q.append(node.left)\n"
            "        i += 1\n"
            "        if i < len(values):\n"
            "            if values[i] is not None:\n"
            "                node.right = TreeNode(values[i])\n"
            "                q.append(node.right)\n"
            "            i += 1\n"
            "    return root\n"
        ),
        "starter": (
            "def is_valid_bst(root):\n"
            "    # 返回 True / False；空树是合法的 BST\n"
            "    # 提示：往下走的时候把允许的上下界传下去\n"
            "    pass\n"
            "\n"
            "\n"
            "def search_bst(root, target):\n"
            "    # 找到返回 True，否则 False\n"
            "    pass\n"
        ),
        "hint": (
            "`is_valid_bst` 用一个带上下界的辅助函数：\n"
            "```\ndef check(node, low, high):\n    ...\n```\n"
            "初始 `low = float(\"-inf\")`、`high = float(\"inf\")`；"
            "往左走时把 `high` 收紧成 `node.val`，往右走时把 `low` 收紧成 `node.val`。\n"
            "注意浮点无穷可以用，也可以一开始传 `None` 表示「无界」再判断。\n\n"
            "`search_bst` 就是一路比大小：比根小往左、比根大往右，走到 `None` 说明没找到。"
        ),
        "checker": """
try:
    assert is_valid_bst(build_tree([2, 1, 3])) == True, "根 2、左 1、右 3 是合法 BST，应该返回 True"
    assert is_valid_bst(build_tree([5, 1, 4, None, None, 3, 6])) == False, "[5,1,4,None,None,3,6] 不是 BST：3 在 4 的左子树里、却比根还小，只比父子会判错，要用上下界"
    assert is_valid_bst(build_tree([10, 5, 15, None, None, 6, 20])) == False, "换个输入再验一遍：[10,5,15,None,None,6,20] 也不是 BST，因为 6 落在根 10 的右子树里却小于 10"
    assert is_valid_bst(None) == True, "空树按定义是合法 BST，应该返回 True"
    assert search_bst(build_tree([8, 3, 10, 1, 6, None, 14]), 6) == True, "6 在树里，search_bst 应该返回 True"
    assert search_bst(build_tree([8, 3, 10, 1, 6, None, 14]), 7) == False, "7 不在树里，search_bst 应该返回 False"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except TypeError as e:
    print("__FAIL__ 返回值应该是 True / False：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：怎么判断一棵二叉树是不是 BST？只比较每个节点和它左右孩子的大小，问题在哪？"
                ),
                "options": [
                    "必须带上下界递归：每个节点都要落在它所属的 (low, high) 区间内；只比父子会漏掉「右子树里有个比根小的节点」这种越界情况",
                    "只比父子就够了，只要每个节点都大于左孩子、小于右孩子就是 BST",
                    "必须先做一次中序遍历把树排好序，再逐层比较",
                    "只能用层序遍历逐层检查，因为 BST 是按层有序的",
                ],
                "answer_index": 0,
                "explanation": (
                    "BST 约束的是「整棵子树」，不是「相邻两个节点」。"
                    "典型反例是根 10、右孩子 15、15 的左孩子 6：父子关系全对，但 6 在 10 的右子树里，违反约束。"
                    "带上下界递归（或中序严格递增）才能判对。"
                ),
            },
            {
                "type": "choice",
                "stem": "往一棵二叉树搜索树里按 1、2、3、4、5、6 的顺序依次插入，插入完成后查找元素的时间复杂度是？",
                "options": [
                    "O(n)，树已经退化成一条链",
                    "O(log n)，BST 查找永远是 O(log n)",
                    "O(1)，因为数据有序",
                    "O(n log n)，因为每次插入都要重排",
                ],
                "answer_index": 0,
                "explanation": (
                    "升序插入时每个新节点都往右走，最终形成一条右斜链，树高 `h = n`，"
                    "查找退化成遍历链表 `O(n)`。这正是需要自平衡 BST（AVL/红黑树）的原因。"
                ),
            },
            {
                "type": "judge",
                "stem": "「中序遍历的结果严格递增」既可以用来验证 BST，也是 BST 最重要的性质之一。",
                "answer": True,
                "explanation": (
                    "中序是「左-根-右」，恰好把「左子树全小、右子树全大」的大小关系展平成递增序列。"
                    "不过要注意用的是**严格递增**（不允许相等），有重复值的树要先约定好放在哪边。"
                ),
            },
            {
                "type": "blank",
                "stem": "从 BST 中删除一个**有两个孩子**的节点时，标准做法是用它的中序 ___ 的值来替换它",
                "hint": "两个字",
                "answer": "后继",
                "accept": ["后继", "successor", "中序后继"],
                "explanation": (
                    "中序后继是「右子树里的最小节点」，也就是右子树一路往左走到底的那个节点。"
                    "用它替换能保证 BST 顺序不变。也可以对称地用「中序前驱」（左子树最大值）。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：既然有了哈希表，为什么还需要 BST？工程上为什么 Java 的 TreeMap、C++ 的 std::map "
                    "用红黑树而不是普通 BST？"
                ),
                "keywords": ["有序", "范围查询", "红黑树", "平衡", "O(log n)", "退化"],
                "reference": (
                    "哈希表能 `O(1)` 精确查找，但它**不维护顺序**，做不了「找所有在 [a, b] 之间的 key」"
                    "「找最小/最大的 key」「按顺序遍历」这类范围查询。BST 中序遍历天然有序，"
                    "这些操作都能做到 `O(log n)`，这是哈希表给不了的。"
                    "但普通 BST 按有序数据插入会退化成链，`O(log n)` 就不成立了，"
                    "所以要靠红黑树 / AVL 这类自平衡树在插入删除时旋转调整，把树高稳定在 `O(log n)`。"
                    "红黑树相对 AVL 的取舍是：平衡没那么严格（树略高一点），但插入删除需要的旋转次数更少，"
                    "综合性能更适合「读写都频繁」的场景。"
                ),
                "explanation": (
                    "能说出「有序性带来的范围查询能力」和「退化问题 → 自平衡」这两层，这道题就答满了。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-07
    {
        "code": "ds-07",
        "subject": "数据结构",
        "stage": "树与堆",
        "runner": "python",
        "title": "堆与优先队列",
        "summary": "只保证堆顶是最值，用它做 TopK 而不是全排序",
        "definition": (
            "**堆（Heap）是一棵完全二叉树**，用数组存：下标 `i` 的左右孩子是 `2i+1` 和 `2i+2`，"
            "父节点是 `(i-1)//2`。因为是完全二叉树，数组中间没有空洞，所以**不需要指针**。\n\n"
            "**堆序性质**：\n"
            "- 小顶堆：每个父节点都 `<=` 它的孩子 → **堆顶是全局最小值**\n"
            "- 大顶堆：每个父节点都 `>=` 它的孩子 → **堆顶是全局最大值**\n\n"
            "注意：堆**只保证堆顶是最值**，兄弟节点之间、不同分支之间没有任何顺序要求。\n\n"
            "**核心操作**：\n\n"
            "| 操作 | 做法 | 复杂度 |\n"
            "| --- | --- | --- |\n"
            "| 取堆顶 | 直接读 `h[0]` | O(1) |\n"
            "| 插入 | 放到数组末尾，然后**上浮** | O(log n) |\n"
            "| 弹出堆顶 | 把末尾元素换到堆顶，**下沉** | O(log n) |\n"
            "| 建堆 | 从最后一个非叶子节点往前下沉 | **O(n)** |\n\n"
            "「建堆是 `O(n)` 而不是 `O(n log n)`」是高频追问，因为大部分节点都在底层、下沉高度很浅，"
            "级数求和收敛到 `O(n)`。\n\n"
            "**堆的经典用途**：优先队列、TopK、第 K 大、合并 K 个有序链表、"
            "定时器/任务调度（按到期时间出队）、Dijkstra 最短路。"
        ),
        "plain": (
            "**堆不是排好序的数组**，这点必须刻在脑子里。"
            "`[1, 5, 3, 8, 9]` 是小顶堆，但 `[5, 9, 1, 8, 3]` 也是 —— 只要每个父节点不大于孩子就行。\n\n"
            "**打个比方**：堆像一个公司只考核「老板必须比所有下属干得少」。"
            "所以你永远能从堆顶知道「谁最闲」，但想知道「第二闲」必须先把老板挪走。"
            "而有序数组是「所有人按考核排好队」，代价是每次有人变动都要重新排队。\n\n"
            "**为什么求「第 K 大」用堆而不是全排序？**\n"
            "n 个数全排序是 `O(n log n)`，而且要把所有数据读进内存。"
            "改成**大小为 k 的小顶堆**：先放 k 个数建堆，之后每个新数只跟堆顶比 ——\n"
            "- 比堆顶小：它肯定进不了前 k 大，直接扔掉\n"
            "- 比堆顶大：替换掉堆顶并下沉\n"
            "每个元素最多花 `O(log k)`，总共 `O(n log k)`。k 远小于 n 时，"
            "它比全排序快得多，而且**内存只占 O(k)** —— 数据流场景（内存装不下全部数据）只能这么做。\n\n"
            "**Python 的坑**：`heapq` 只提供**小顶堆**。要当大顶堆用得存负数："
            "`heappush(h, -x)`，取出来再 `-heappop(h)`。"
        ),
        "example": (
            "import heapq\n"
            "\n"
            "nums = [5, 1, 8, 3]\n"
            "heapq.heapify(nums)          # 原地建堆 O(n)\n"
            "print(nums)                  # 只保证 nums[0] 是最小值\n"
            "print(heapq.heappop(nums))   # 弹出最小值\n"
            "print(heapq.heappushpop(nums, 0))   # 先 push 再 pop，比分开调用少一次下沉\n"
            "\n"
            "# 大顶堆：存负数\n"
            "max_heap = []\n"
            "for x in [5, 1, 8]:\n"
            "    heapq.heappush(max_heap, -x)\n"
            "print(-heapq.heappop(max_heap))     # 8\n"
            "\n"
            "# TopK 模板：大小为 k 的小顶堆\n"
            "def top_k(nums, k):\n"
            "    heap = nums[:k]\n"
            "    heapq.heapify(heap)\n"
            "    for x in nums[k:]:\n"
            "        if x > heap[0]:              # 比堆顶大才有资格进前 k\n"
            "            heapq.heapreplace(heap, x)\n"
            "    return sorted(heap, reverse=True)\n"
            "\n"
            "print(top_k([3, 2, 1, 5, 6, 4], 2))\n"
            "print(heapq.nlargest(2, [3, 2, 1, 5, 6, 4]))   # 标准库已经写好了"
        ),
        "example_output": "[1, 3, 8, 5]\n1\n0\n8\n[6, 5]\n[6, 5]",
        "pitfalls": [
            "**把普通 list 当堆用**：`h = [3, 1, 2]` 不是堆，直接 `h.pop()` 拿到的是最后一个元素而不是最小值。要么先 `heapq.heapify(h)`，要么用 `heappush` 一个个放进去，取最小值一律用 `heapq.heappop(h)`。",
            "**`heapify` 是原地操作、返回 None**：写 `h = heapq.heapify(nums)` 会让 `h` 变成 `None`。正确写法是先 `h = list(nums)` 再 `heapq.heapify(h)`。",
            "**以为 heapq 有大顶堆**：没有。要存负值，取出来再取负；存元组时可以存 `(-priority, item)`，但要注意第二项必须可比较（否则会 `TypeError`）。",
            "**TopK 用全排序**：数据是流式的、内存放不下时全排序根本做不到。用大小为 k 的堆，内存 `O(k)`、时间 `O(n log k)`；库函数 `heapq.nlargest(k, iterable)` 内部就是这么实现的。",
        ],
        "task": (
            "请实现 `kth_largest(nums, k)`：返回列表 `nums` 中**第 k 大的数**（重复元素按出现次数计数）。\n\n"
            "例：`kth_largest([3, 2, 1, 5, 6, 4], 2)` → 降序排列是 `[6, 5, 4, 3, 2, 1]`，第 2 个是 `5`。\n\n"
            "要求：用**堆**的思路完成。可以 `import heapq`，也可以用 `list` 手写堆，"
            "但不要写 `sorted(nums)[::-1][k-1]` 这种「全排序再取」的写法 —— 面试官要的是 `O(n log k)`。"
        ),
        "setup": "",
        "starter": (
            "def kth_largest(nums, k):\n"
            "    # 返回第 k 大的数（重复元素算多次）\n"
            "    # 提示：维护一个大小为 k 的小顶堆，堆顶就是第 k 大\n"
            "    pass\n"
        ),
        "hint": (
            "`import heapq`，然后维护一个**大小为 k 的小顶堆**：\n"
            "先把前 k 个数建堆，剩下的一路比较 —— `if x > heap[0]: heapq.heapreplace(heap, x)`；\n"
            "全部走完后 `heap[0]` 就是第 k 大。\n"
            "一行版：`heapq.nsmallest` / `heapq.nlargest` 也能解决，但把堆的逻辑写出来更保险。"
        ),
        "checker": """
try:
    assert kth_largest([3, 2, 1, 5, 6, 4], 2) == 5, "kth_largest([3,2,1,5,6,4], 2) 应该返回 5（降序第 2 个）"
    assert kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4, "重复元素要按出现次数计数：降序是 6,5,5,4,...，第 4 个是 4"
    assert kth_largest([1], 1) == 1, "只有 1 个数时取第 1 大就是它本身"
    assert kth_largest([-1, -2, -3], 2) == -2, "负数也要正确：降序是 -1,-2,-3，第 2 个是 -2（检查是不是把大顶堆写成了取绝对值）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except IndexError as e:
    print("__FAIL__ 堆是空的就取堆顶了，检查建堆和 heapq.heappop 的用法：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：求 n 个数的第 k 大，为什么用大小为 k 的**小顶堆**，而不是大顶堆？"
                ),
                "options": [
                    "小顶堆堆顶是这 k 个数里最小的，也就是「前 k 大里最弱的那个」，新元素只要比堆顶大就替换掉它；一次遍历即可，时间 O(n log k)、空间 O(k)",
                    "因为 Python 只有小顶堆，用大顶堆实现不了",
                    "因为小顶堆建堆是 O(n)，大顶堆建堆是 O(n log n)",
                    "因为大顶堆只能处理正数，负数会出错",
                ],
                "answer_index": 0,
                "explanation": (
                    "关键在于「谁最该被淘汰」。我们要留最大的 k 个，"
                    "所以需要一个能立刻告诉我们「当前留下的 k 个里面谁最小」的结构 —— 那就是小顶堆的堆顶。"
                    "用大顶堆的话，你没法快速判断新元素该不该进来（堆顶是最大值，淘汰谁看不出来）。"
                    "B 是错的，存负数就能模拟大顶堆；C 错在两者建堆都是 `O(n)`。"
                ),
            },
            {
                "type": "choice",
                "stem": "把 n 个无序元素直接建成一个堆，时间复杂度是？",
                "options": ["O(n)", "O(n log n)", "O(log n)", "O(n²)"],
                "answer_index": 0,
                "explanation": (
                    "从最后一个非叶子节点往前依次下沉，总共是 `O(n)`。"
                    "直觉是：绝大多数节点都在底层，它们下沉的高度只有 0 或 1，"
                    "把这些代价加起来的级数是收敛的。"
                    "如果改成「把 n 个元素一个个 heappush 进去」，那才是 `O(n log n)`。"
                ),
            },
            {
                "type": "judge",
                "stem": "`heapq.heapify` 处理后的数组整体是有序的。",
                "answer": False,
                "explanation": (
                    "堆只保证「父节点不大于子节点」，兄弟之间、不同分支之间没有顺序。"
                    "`[1, 3, 8, 5]` 是堆，但不是有序数组。想要整体有序还得再排序。"
                    "这也是堆排序要「反复弹出堆顶」才能拿到有序序列的原因。"
                ),
            },
            {
                "type": "blank",
                "stem": "Python 标准库 `heapq` 默认实现的是 ___ 堆（填「大顶」或「小顶」）",
                "hint": "两个字",
                "answer": "小顶",
                "accept": ["小顶", "小顶堆", "小根堆", "min"],
                "explanation": (
                    "`heapq` 只有小顶堆，`h[0]` 是最小值。要用大顶堆就往里 `heappush(h, -x)`，"
                    "取出时再 `-heappop(h)`。存元组时也可以 `(-priority, item)`。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：从 10 亿个数里找出最大的 10 个，内存装不下全部数据，只有一次遍历的机会。你怎么做？"
                ),
                "keywords": ["小顶堆", "O(k)", "流式", "堆顶比较", "O(n log k)", "TopK"],
                "reference": (
                    "维护一个**大小为 10 的小顶堆**，边读边比："
                    "先读入 10 个数建堆；之后每读一个数，只要它比堆顶大，就 `heapreplace` 替换堆顶；"
                    "比堆顶小就直接丢弃。"
                    "遍历结束后堆里的 10 个数就是最大的 10 个。"
                    "时间 `O(n log k)`（这里 k=10，几乎等于 `O(n)`），**额外内存只有 `O(k)`**，"
                    "所以数据流式读入、不用一次装进内存，正好满足「内存装不下」的约束。"
                    "如果内存放得下且只需要最终结果，也可以分块排序再归并，但堆方案更简单也更省内存。"
                ),
                "explanation": (
                    "这题考的是「大数据量 + 内存受限」的经典解法，答题时要主动提 `O(k)` 内存这个点。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-08
    {
        "code": "ds-08",
        "subject": "数据结构",
        "stage": "查找、排序与图",
        "runner": "python",
        "title": "排序算法",
        "summary": "各种排序的复杂度、稳定性，以及快排为什么会退化",
        "definition": (
            "**对比表（背下来）**：\n\n"
            "| 算法 | 平均 | 最坏 | 额外空间 | 稳定 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 冒泡 / 插入 | O(n²) | O(n²) | O(1) | 稳定 |\n"
            "| 选择 | O(n²) | O(n²) | O(1) | 不稳定 |\n"
            "| 快速排序 | O(n log n) | **O(n²)** | O(log n) 栈 | 不稳定 |\n"
            "| 归并排序 | O(n log n) | O(n log n) | O(n) | **稳定** |\n"
            "| 堆排序 | O(n log n) | O(n log n) | O(1) | 不稳定 |\n"
            "| 计数排序 | O(n + k) | O(n + k) | O(k) | 稳定 |\n\n"
            "**稳定性**的定义：值相等的元素，排序后**相对顺序不变**。"
            "「先按分数排序，再按班级排序」这种多关键字排序必须依赖稳定排序。\n\n"
            "**快速排序为什么最坏是 O(n²)？**\n"
            "快排先选一个 pivot 把数组分成「小于 pivot」和「大于 pivot」两堆，再对两堆递归。"
            "如果每次分区都刚好平分，递归深度是 `log n`，总共 `O(n log n)`。"
            "但如果**每次分区都极不均匀**（比如一半是空的），递归深度变成 `n`，总共 `O(n²)`。"
            "什么时候会发生？**数组已经有序（或逆序），而 pivot 又固定取第一个元素** —— "
            "第一个元素恰好是最小值，所有元素都被分到右边，每层只减少一个元素。"
            "这是最阴的地方：**已经排好序的输入反而最容易让快排退化**。\n\n"
            "**工程上怎么避免？**\n"
            "1. **随机选 pivot**（`random.choice` 或随机交换到首位），让「输入有序」不再是倒霉条件\n"
            "2. **三数取中**：取首、中、尾三个数的中位数当 pivot，比随机更稳定\n"
            "3. **小区间改用插入排序**（元素少于 10~16 个时插入排序更快）\n"
            "4. 递归太深时**改尾递归/显式栈**，避免栈溢出\n\n"
            "顺带一提：Python 的 `sorted()` 用的是 **Timsort**，"
            "它是归并 + 插入的混合算法，**稳定**、对部分有序的数据特别快，而且整体由 C 实现。"
            "所以日常业务代码里永远用 `sorted()`，只有面试要求手写时才手写。"
        ),
        "plain": (
            "**快排的思路一句话：选个基准，比它小的扔左边，比它大的扔右边，然后左右各自再来一遍。**\n\n"
            "**为什么「已经排好序」反而最慢？** 想象你整理一摞牌，规定「拿第一张当基准」。"
            "如果这摞牌本来就从小到大排好了，你拿起的第一张恰好是最小的那张，"
            "于是剩下所有牌都被扔到「比它大」那一边 —— **你只把问题缩小了 1 张牌**。"
            "重复下去就是 `n + (n-1) + ... = O(n²)`。\n\n"
            "**怎么破？随机拿一张当基准。** 随机的意思是「我不管你输入长什么样」，"
            "从概率上保证不会每次都抽到极端值。这就是**随机化快排**，也是工程上真正在用的做法。\n\n"
            "**稳定性为什么重要？** 假设你已经按下单时间排好了一万条订单，现在要「按金额从大到小」再排一次。"
            "如果排序是**稳定**的，金额相同的订单会保持原来的时间顺序 —— 一次排序就得到「金额降序、同金额按下单时间升序」。"
            "如果排序**不稳定**，同金额的顺序会被打乱，你还得写个复合比较函数重排一遍。\n\n"
            "**写代码时的实用建议**：用列表推导式把数组分成 `left / mid / right` 三段，"
            "比原地交换指针的写法容易对得多，而且天然处理重复元素（不会因为一堆相同元素而退化）。"
            "面试时先说清「我写的是容易读的版本」，再补一句「原地版用双指针分区」。"
        ),
        "example": (
            "def quick_sort(nums):\n"
            "    if len(nums) <= 1:\n"
            "        return nums\n"
            "    pivot = nums[len(nums) // 2]          # 取中间值当基准，避开「有序输入」这个坑\n"
            "    left = [x for x in nums if x < pivot]\n"
            "    mid = [x for x in nums if x == pivot]  # 相等的单独一组，重复元素不会退化\n"
            "    right = [x for x in nums if x > pivot]\n"
            "    return quick_sort(left) + mid + quick_sort(right)\n"
            "\n"
            "print(quick_sort([3, 1, 4, 1, 5, 9, 2, 6]))\n"
            "\n"
            "# 稳定性：sorted 是稳定的，同 key 保持原顺序\n"
            "pairs = [(\"b\", 1), (\"a\", 2), (\"b\", 3)]\n"
            "print(sorted(pairs, key=lambda p: p[0]))\n"
            "\n"
            "# 面试要求的原地分区（双指针）：返回 pivot 最终所在的下标\n"
            "def partition(nums, lo, hi):\n"
            "    pivot = nums[hi]\n"
            "    i = lo\n"
            "    for j in range(lo, hi):\n"
            "        if nums[j] < pivot:\n"
            "            nums[i], nums[j] = nums[j], nums[i]\n"
            "            i += 1\n"
            "    nums[i], nums[hi] = nums[hi], nums[i]\n"
            "    return i\n"
            "\n"
            "data = [3, 1, 4, 1, 5, 9, 2]\n"
            "p = partition(data, 0, len(data) - 1)\n"
            "print(p, data)          # pivot=2 归位后，左边全是 <2 的元素"
        ),
        "example_output": (
            "[1, 1, 2, 3, 4, 5, 6, 9]\n[('a', 2), ('b', 1), ('b', 3)]\n2 [1, 1, 2, 3, 5, 9, 4]"
        ),
        "pitfalls": [
            "**快排固定取首元素当 pivot + 已排序输入 → O(n²)**：这是最经典的退化路径，而且递归深度也会变成 `n`，可能直接 `RecursionError`。解法是随机 pivot 或三数取中，取中间下标 `nums[len(nums)//2]` 也能有效缓解。",
            "**以为快排是稳定的**：快排的分区会做远距离交换，相等元素相对顺序会被打乱。要稳定性就选**归并排序**（代价是 `O(n)` 额外空间）。",
            "**手写原地 partition 的边界写错**：`while` 条件里的 `<` 和 `<=` 差一个字符就会死循环或错位。不熟练时先用「三段列表推导式」版本，逻辑上不可能错。",
            "**在业务代码里手写排序**：Python 的 `sorted()` 是 C 实现的 Timsort，比手写 Python 快几十倍还稳定。只有面试要求时才手写，平时一律 `sorted()`。",
        ],
        "task": (
            "请实现 `quick_sort(nums)`：用快速排序的思路返回一个**升序排列的新列表**。\n\n"
            "要求：\n"
            "- 返回列表，不要求原地修改（原地也可以，只要返回值正确）\n"
            "- 空列表返回 `[]`，单元素返回它自己\n"
            "- 必须能处理**重复元素**（比如 `[5, 5, 5]`）\n"
            "- 会用一个 300 个元素的逆序数组再验一遍，所以别写死答案"
        ),
        "setup": "",
        "starter": (
            "def quick_sort(nums):\n"
            "    # 返回升序排列的新列表\n"
            "    # 提示：选 pivot，分成 left / mid / right 三段再递归拼接\n"
            "    pass\n"
        ),
        "hint": (
            "递归 + 列表推导式最不容易写错：\n"
            "```\nif len(nums) <= 1:\n    return nums\npivot = nums[len(nums) // 2]\n```\n"
            "然后 `left = [x for x in nums if x < pivot]`、`mid = [x for x in nums if x == pivot]`、"
            "`right = [x for x in nums if x > pivot]`，最后返回 `quick_sort(left) + mid + quick_sort(right)`。\n"
            "**一定要有 `mid` 这一组**，否则重复元素会让递归永远缩不下去。"
        ),
        "checker": """
try:
    assert quick_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9], "quick_sort([3,1,4,1,5,9,2,6]) 应该返回 [1,1,2,3,4,5,6,9]"
    assert quick_sort([]) == [], "空列表应该返回 []，别忘了 len(nums) <= 1 这个终止条件"
    assert quick_sort([2, 1]) == [1, 2], "只有两个元素时也要正确排序：[2,1] 应该变成 [1,2]"
    assert quick_sort([5, 5, 5]) == [5, 5, 5], "重复元素要单独归到 mid 一组，否则递归会缩不下去（或者死循环）"
    assert quick_sort(list(range(300, 0, -1))) == list(range(1, 301)), "换个输入再验一遍：逆序的 300 个数也要能排好，说明 pivot 不能固定取第一个"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except RecursionError as e:
    print("__FAIL__ 递归太深了 —— pivot 选得太极端，换成取中间下标的元素：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：为什么快速排序最坏是 O(n²)？工程上怎么避免？"
                ),
                "options": [
                    "每次分区极不均匀（例如固定取首元素当 pivot、而输入已经有序）时递归深度变成 n；用随机 pivot 或三数取中就能在概率上避免",
                    "因为快排要额外分配 O(n) 空间，空间不够时退化",
                    "因为快排不稳定，遇到大量重复元素必然变成 O(n²)",
                    "因为快排的 partition 里有两层循环，所以天生是 O(n²)",
                ],
                "answer_index": 0,
                "explanation": (
                    "快排的复杂度取决于**分区的均衡程度**：均衡就是 `O(n log n)`，"
                    "每次只切掉一个元素就是 `O(n²)`。避免手段有随机 pivot、三数取中、"
                    "三段分区（把等于 pivot 的单独归为一组，专门治大量重复元素）。"
                    "D 是错的：partition 本身是单层遍历，`O(n)`，两层循环的说法不成立。"
                ),
            },
            {
                "type": "choice",
                "stem": "下面哪种排序算法是**稳定**的？",
                "options": ["归并排序", "快速排序", "堆排序", "选择排序"],
                "answer_index": 0,
                "explanation": (
                    "归并排序在合并两个有序子数组时，遇到相等元素总是先取左边那个，所以相对顺序不变。"
                    "快排（远距离交换）、堆排（堆顶与末尾互换）、选择排序（把最小值换到前面）都会打乱相等元素的顺序。"
                ),
            },
            {
                "type": "judge",
                "stem": "Python 内置的 `sorted()` 是稳定排序。",
                "answer": True,
                "explanation": (
                    "`sorted()` 用的是 Timsort，归并 + 插入的混合算法，稳定、对部分有序数据特别快。"
                    "所以多关键字排序时，可以先按次要关键字排一次，再按主要关键字排一次，"
                    "就能得到「主降次升」这类复合顺序，不用写复杂比较函数。"
                ),
            },
            {
                "type": "blank",
                "stem": "在 n 个无序数中找第 k 大的数，用快速选择（Quick Select，只对一半递归）的平均时间复杂度是 O(___)",
                "hint": "填一个字母",
                "answer": "n",
                "accept": ["n", "N"],
                "explanation": (
                    "快速选择每次分区后只递归含有目标下标的那一半，"
                    "`n + n/2 + n/4 + ...` 收敛到 `O(n)`（最坏仍是 `O(n²)`）。"
                    "对比一下：堆的做法是 `O(n log k)`，全排序是 `O(n log n)`。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：给你 100 万条订单，要求「先按金额从大到小排，金额相同的再按下单时间从早到晚排」，你会怎么写？"
                ),
                "keywords": ["稳定排序", "两次排序", "key", "sorted", "反向", "Timsort"],
                "reference": (
                    "利用「稳定排序」这个性质，**分两次排**：先按次要关键字「下单时间」做一次升序排序，"
                    "再按主要关键字「金额」做一次降序排序。第二次排序（必须稳定）会保持第一次的顺序，"
                    "于是金额相同的那些订单仍按下单时间递增 —— 结果恰好符合要求。"
                    "用 Python 写就是 `sorted(orders, key=lambda o: o.time)` 之后 "
                    "`sorted(..., key=lambda o: o.amount, reverse=True)`。"
                    "也可以一次搞定但要注意 `reverse=True` 会把**所有**关键字一起反向，"
                    "此时得对时间取负或用 `sorted(orders, key=lambda o: (-o.amount, o.time))` 更直接，"
                    "不过面试里把「稳定排序 + 两次排」讲清楚更得分。"
                ),
                "explanation": (
                    "面试官想听到「稳定排序」这四个字，以及「先排次要、再排主要」的顺序。"
                    "注意陷阱：一次 `sorted` 加 `reverse=True` 会把次要关键字也反转。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-09
    {
        "code": "ds-09",
        "subject": "数据结构",
        "stage": "查找、排序与图",
        "runner": "python",
        "title": "二分查找与边界",
        "summary": "会写二分不难，难的是把边界写对",
        "definition": (
            "**二分查找的前提是数组有序**（或者更一般地：答案具有单调性）。"
            "每次取中间元素把查找区间砍一半，所以最多比较 `log₂n` 次，时间 `O(log n)`，空间 `O(1)`。\n\n"
            "**两套模板，选一套就不要再混：**\n\n"
            "**模板一：闭区间 `[lo, hi]`，`while lo <= hi`**\n"
            "适合「找一个确定存在的值」：\n"
            "```\nwhile lo <= hi:\n    mid = (lo + hi) // 2\n    if nums[mid] == target: return mid\n    if nums[mid] < target: lo = mid + 1\n    else: hi = mid - 1\nreturn -1\n```\n\n"
            "**模板二：左闭右开 `[lo, hi)`，`while lo < hi`**\n"
            "适合找**边界**（第一个满足条件的、最后一个满足条件的）：\n"
            "```\nwhile lo < hi:\n    mid = (lo + hi) // 2\n    if nums[mid] < target: lo = mid + 1\n    else: hi = mid\nreturn lo\n```\n\n"
            "**为什么会死循环？** 因为 `while lo < hi` 保证区间至少两个元素，"
            "如果里面写 `lo = mid`（少了 `+1`），当 `hi = lo + 1` 时 `mid == lo`，区间一点都不缩小，就永远转下去。"
            "**口诀：`while lo < hi` 配 `lo = mid + 1` / `hi = mid`；`while lo <= hi` 配 `lo = mid + 1` / `hi = mid - 1`。**\n\n"
            "**两个必会的边界函数**：\n"
            "- `lower_bound(target)`：第一个 `>= target` 的下标（也就是 target 的插入位置）\n"
            "- `upper_bound(target)`：第一个 `> target` 的下标\n\n"
            "这两个函数是 Python 标准库 `bisect.bisect_left` / `bisect_right` 的语义，"
            "面试里经常让你手写 `bisect_left`。\n\n"
            "**进阶：二分答案。** 只要问题满足「答案越小越难满足（单调性）」，"
            "即使数组本身无序，也能对**答案空间**二分 —— 例如「把数组切成 m 段使最大段和最小」、"
            "「k 天内运完包裹的最小载重」、「吃香蕉的最小速度」。"            "二分的对象从「数组下标」换成了「答案的值」，`lo`/`hi` 是答案的可能范围，"
            "`check(mid)` 判断「mid 这个答案够不够用」。"
        ),
        "plain": (
            "**二分查找就是你玩「猜数字」的策略**：范围 1~100，你猜 50，"
            "对方说「小了」，你立刻知道答案在 51~100，范围直接砍掉一半。"
            "最多猜 7 次（`log₂100 ≈ 6.6`）就能猜中 —— 暴力从 1 猜到 100 要 100 次。\n\n"
            "**为什么是 log₂n？** 因为每次砍一半，n 要砍多少次才到 1？"
            "`n / 2^k = 1` 解得 `k = log₂n`。41 亿个数也只要 32 次。\n\n"
            "**为什么边界这么难写？** 因为二分的循环条件是「区间还有几个元素」和「mid 要不要包含进去」"
            "两件事交织在一起，四个组合里只有两个是对的。\n"
            "最稳的办法是**背下一套模板用到底**，而不是每次现场推导。\n\n"
            "**一个极其实用的技巧**：手写完二分后，立刻用这四个输入在心里过一遍 ——\n"
            "1. `target` 比所有元素都小（答案 0）\n"
            "2. `target` 比所有元素都大（答案 = len(nums)）\n"
            "3. `target` 在中间但不存在（答案是插入位置）\n"
            "4. 空数组（答案 0）\n\n"
            "这四组恰好覆盖所有边界。判定的用例也是这么设计的。"
        ),
        "example": (
            "def lower_bound(nums, target):\n"
            "    \"\"\"第一个 >= target 的下标（也就是插入位置）\"\"\"\n"
            "    lo, hi = 0, len(nums)        # 左闭右开 [lo, hi)\n"
            "    while lo < hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if nums[mid] < target:\n"
            "            lo = mid + 1         # 区间右移，mid 已排除\n"
            "        else:\n"
            "            hi = mid             # mid 可能就是答案，保留\n"
            "    return lo\n"
            "\n"
            "def search(nums, target):\n"
            "    \"\"\"存在就返回下标，否则 -1（闭区间模板）\"\"\"\n"
            "    lo, hi = 0, len(nums) - 1\n"
            "    while lo <= hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if nums[mid] == target:\n"
            "            return mid\n"
            "        if nums[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
            "\n"
            "nums = [1, 3, 3, 5, 7]\n"
            "print(lower_bound(nums, 3))    # 1：第一个 >= 3 的位置\n"
            "print(lower_bound(nums, 4))    # 3：4 应该插在下标 3\n"
            "print(lower_bound(nums, 9))    # 5：比所有元素都大，插在末尾\n"
            "print(lower_bound([], 1))      # 0：空数组\n"
            "print(search(nums, 5), search(nums, 4))"
        ),
        "example_output": "1\n3\n5\n0\n3 -1",
        "pitfalls": [
            "**两个模板混用导致死循环**：`while lo < hi` 里面写了 `lo = mid`（漏掉 `+1`），当 `lo` 和 `hi` 相邻时区间不缩小，程序卡死。死记：`while lo < hi` 时 `lo` 那一路必须 `mid + 1`。",
            "**在无序数组上二分**：二分的前提是有序。对无序数组二分有时也能碰巧找到答案，所以**测试时不容易发现**，但实际上是错的。先确认有序，或者先排序（`O(n log n)`），或者改用 set/dict（`O(n)` 建、`O(1)` 查）。",
            "**用「找到 target 就返回下标」的模板去找边界**：那个模板只能告诉你「在不在」，找不到「第一个」或「最后一个」。要边界就必须用 `hi = mid` 的 lower_bound 写法。",
            "**`mid` 算错，以及不测极端输入**：写 `(lo + hi) / 2` 得到小数，`nums[2.5]` 直接 `TypeError`，整除要用 `//`（Java/C 里还要写 `lo + (hi - lo) // 2` 防溢出）。另外提交前必须过一遍「target 比所有元素都小、比所有元素都大、数组为空」这三组 —— 它们是二分 bug 的重灾区。",
        ],
        "task": (
            "请实现 `lower_bound(nums, target)`：\n\n"
            "`nums` 是一个**非递减**（已排好序，允许重复）的整数列表。"
            "返回**第一个 `>= target` 的元素下标**；如果所有元素都小于 `target`，返回 `len(nums)`。\n\n"
            "这个函数的语义等价于 Python 标准库的 `bisect.bisect_left`，就是一个「target 应该插入的位置」。\n\n"
            "例：\n"
            "- `lower_bound([1, 3, 5, 6], 5)` → `2`\n"
            "- `lower_bound([1, 3, 5, 6], 2)` → `1`\n"
            "- `lower_bound([1, 3, 5, 6], 7)` → `4`\n"
            "- `lower_bound([1, 3, 5, 6], 0)` → `0`\n\n"
            "要求用二分实现，不要写 `for` 循环逐个比较。"
        ),
        "setup": "",
        "starter": (
            "def lower_bound(nums, target):\n"
            "    # 返回第一个 >= target 的下标；都比 target 小则返回 len(nums)\n"
            "    # 提示：左闭右开区间 [lo, hi)，hi 初始为 len(nums)\n"
            "    pass\n"
        ),
        "hint": (
            "用左闭右开的模板：\n"
            "```\nlo, hi = 0, len(nums)\nwhile lo < hi:\n    mid = (lo + hi) // 2\n    if nums[mid] < target:\n        lo = mid + 1\n    else:\n        hi = mid\nreturn lo\n```\n"
            "关键在于「`nums[mid] >= target` 时 `hi = mid`」—— 因为 mid 自己可能就是那个「第一个」的位置，不能排除掉。"
        ),
        "checker": """
try:
    assert lower_bound([1, 3, 5, 6], 5) == 2, "lower_bound([1,3,5,6], 5) 应该返回 2（下标 2 的元素正好是 5）"
    assert lower_bound([1, 3, 5, 6], 2) == 1, "lower_bound([1,3,5,6], 2) 应该返回 1：2 不存在，应该是它该插入的位置"
    assert lower_bound([1, 3, 5, 6], 0) == 0, "target 比所有元素都小时要返回 0，检查 lo 的初始值和 mid+1 的边界"
    assert lower_bound([1, 3, 5, 6], 7) == 4, "target 比所有元素都大时要返回 len(nums)（也就是 4），说明 hi 初始必须是 len(nums) 而不是 len(nums)-1"
    assert lower_bound([], 1) == 0, "空列表要直接返回 0，循环一次都不执行才对"
    assert lower_bound([5, 5, 5], 5) == 0, "换个输入再验一遍：全是相同元素时，要返回**第一个** >= 的位置，也就是 0"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except IndexError as e:
    print("__FAIL__ 下标越界了，检查 hi 是 len(nums) 还是 len(nums)-1：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：一个「旋转有序数组」（比如 [4, 5, 6, 7, 0, 1, 2]）里找 target，还能二分吗？思路是什么？"
                ),
                "options": [
                    "可以。每次取 mid 后，[lo, mid] 和 [mid, hi] 这两段里必然有一段是完全有序的，判断 target 是否落在这段的范围内，就能决定往哪边收缩",
                    "不行，必须先用线性扫描找到最小值的位置，再在两边分别二分",
                    "不行，旋转之后数组不再单调，只能用哈希表",
                    "可以，直接对数组排序后再普通二分即可",
                ],
                "answer_index": 0,
                "explanation": (
                    "关键观察：把旋转数组从 mid 切开，**左右两段至少有一段是有序的**。"
                    "先判断 `nums[lo] <= nums[mid]`（左段有序）还是右段有序，"
                    "再看 target 是否落在有序那段的区间里，据此把 `lo` 或 `hi` 收掉一半。"
                    "依然是 `O(log n)`。B 的线性扫描会变成 `O(n)`，丢掉了二分的意义。"
                ),
            },
            {
                "type": "choice",
                "stem": "在长度为 1024 的有序数组里做二分查找，最多需要比较多少次？",
                "options": ["10", "32", "512", "1024"],
                "answer_index": 0,
                "explanation": (
                    "每次砍一半，`2¹⁰ = 1024`，所以最多 10 次。"
                    "这也是为什么 41 亿（2³²）个数也只需要 32 次比较 —— 这就是 `O(log n)` 的威力。"
                ),
            },
            {
                "type": "judge",
                "stem": "对一个无序数组做二分查找，有时也能「碰巧」找到目标值，但这种实现是不可靠的。",
                "answer": True,
                "explanation": (
                    "二分靠的是「能通过 mid 排除掉一半区间」这个前提，无序时这个排除逻辑不成立，"
                    "结果就是「有时对、有时错」—— 这种 bug 最难查，因为用几个手写用例测可能都是通过的。"
                    "所以面试里被要求「有序数组二分」时，别顺手写成「反正也能跑」。"
                ),
            },
            {
                "type": "blank",
                "stem": "在长度为 1024 的有序数组里二分查找，最多需要比较 ___ 次",
                "hint": "填一个数字",
                "answer": "10",
                "accept": ["10", "10次", "10 次"],
                "explanation": "`log₂1024 = 10`。二分每次砍一半，比较次数就是对数级别。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：「把 n 个数分成 m 段，使各段和的最大值最小」这类题为什么能二分？说说你怎么判断它能不能二分。"
                ),
                "keywords": ["单调性", "check", "答案空间", "二分答案", "最大段和", "贪心"],
                "reference": (
                    "判断标准是**单调性**：假设我们要求「最大段和不超过 X」，"
                    "X 越大越容易满足、X 越小越难满足 —— 存在一个临界值，比它小就不行、比它大就行。"
                    "有这种单调性就可以**对答案 X 二分**（答案空间是从 `max(nums)` 到 `sum(nums)`），"
                    "每次用 `check(X)` 贪心地从左往右能塞就塞、段数超过 m 就说明 X 太小。\n"
                    "所以套路是：确定答案的取值范围作为 `lo`/`hi`，"
                    "写一个 `O(n)` 的 `check(mid)` 判断「mid 是否可行」，"
                    "然后按「找第一个可行的 X」来二分，总复杂度 `O(n log(总和))`。"
                    "这个技巧叫「二分答案」，只要题目里出现「最小的最大值」「最大的最小值」就优先往这上面想。"
                ),
                "explanation": (
                    "面试官考的是你能不能从「查找一个下标」抽象到「二分答案空间」，这是二分题的分水岭。"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ ds-10
    {
        "code": "ds-10",
        "subject": "数据结构",
        "stage": "查找、排序与图",
        "runner": "python",
        "title": "图与 BFS/DFS",
        "summary": "两种遍历方式，一个求最短路一个找连通块",
        "definition": (
            "**图的表示**：\n\n"
            "- **邻接表**：`graph = {0: [1, 2], 1: [0, 3]}`，空间 `O(V + E)`，"
            "遍历某个点的邻居快。**绝大多数场景用它，尤其是稀疏图。**\n"
            "- **邻接矩阵**：`matrix[i][j]` 表示 i 到 j 有没有边，空间 `O(V²)`，"
            "判断两点是否相邻是 `O(1)`，适合**稠密图**或需要频繁查边的情况。\n\n"
            "**BFS（广度优先搜索）**\n"
            "用**队列**实现：起点入队 → 出队 → 把没访问过的邻居全部入队 → 重复。\n"
            "效果是「一层一层往外扩散」，所以**在无权图里，BFS 第一次到达某个点时走过的步数就是最短距离**。\n\n"
            "**DFS（深度优先搜索）**\n"
            "用**栈**（或递归）实现：一条路走到头再回头换路。\n"
            "适合判断连通性、数连通块个数、找所有路径、拓扑排序、检测环。\n\n"
            "| | BFS | DFS |\n"
            "| --- | --- | --- |\n"
            "| 实现 | 队列 deque | 栈 / 递归 |\n"
            "| 无权最短路 | ✅ 能 | ❌ 不能 |\n"
            "| 连通块/环检测 | 能 | 能（更常用）|\n"
            "| 空间 | O(宽度) | O(深度) |\n\n"
            "复杂度都是 `O(V + E)`（每个点访问一次、每条边检查一次）。\n\n"
            "**网格也是图**：二维数组的上下左右相邻关系天然构成一张图，"
            "「岛屿数量」「迷宫最短路」「腐烂的橘子」全是 BFS/DFS 的标准题。\n\n"
            "**拓扑排序**：对有向无环图（DAG），用 BFS 做「入度统计」——"
            "先把入度为 0 的点入队，出队时把它指向的点的入度减 1，减到 0 就入队。"
            "如果最后输出的点数少于总点数，说明图里有环。"
        ),
        "plain": (
            "**DFS 像走迷宫时贴着右手边走**：看到岔路就往里钻，撞墙了退回来换另一条。"
            "优点是省内存（只需要记住来时的路），能一口气把「连在一起的一整块」全部走完。\n\n"
            "**BFS 像往水里扔石头看涟漪**：一圈一圈往外扩，"
            "所以它天生知道「最短要几步」—— 第一圈是 1 步能到的，第二圈是 2 步能到的。\n\n"
            "**「无权图求最短路为什么不能用 DFS？」** 因为 DFS 一头扎到底，"
            "它第一次到达某个点时走的可能是绕远的那条路，之后再退回来「发现更近的路」也晚了。"
            "BFS 因为层层扩散，第一次到达必然是最短的。\n\n"
            "**`visited` 是命根子。** 无向图的边是双向的：从 A 走到 B，"
            "处理 B 的邻居时又会看见 A，如果不管就会 A→B→A→B…… 无限循环。"
            "所以**每次要访问一个节点前先检查 `if nxt not in visited`，"
            "并且入队/入栈的同时就标记 visited**（不要等出队才标记，那样同一个点会被重复入队很多次）。\n\n"
            "**网格题的四个方向**：`dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]`，"
            "用 `for dr, dc in dirs:` 遍历邻居。**访问前必须先判 `0 <= r < rows and 0 <= c < cols`**，"
            "否则会越界或者在对面墙上「穿墙」连成一片。"
        ),
        "example": (
            "from collections import deque\n"
            "\n"
            "graph = {0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2, 4], 4: [3]}\n"
            "\n"
            "def bfs(graph, start):\n"
            "    seen = {start}                # 起点也要标记，否则可能被重复入队\n"
            "    q = deque([start])\n"
            "    order = []\n"
            "    while q:\n"
            "        node = q.popleft()\n"
            "        order.append(node)\n"
            "        for nxt in graph[node]:\n"
            "            if nxt not in seen:\n"
            "                seen.add(nxt)     # 关键：入队时就标记\n"
            "                q.append(nxt)\n"
            "    return order\n"
            "\n"
            "def dfs(graph, node, seen=None, order=None):\n"
            "    if seen is None:\n"
            "        seen, order = set(), []\n"
            "    seen.add(node)\n"
            "    order.append(node)\n"
            "    for nxt in graph[node]:\n"
            "        if nxt not in seen:\n"
            "            dfs(graph, nxt, seen, order)\n"
            "    return order\n"
            "\n"
            "print(bfs(graph, 0))\n"
            "print(dfs(graph, 0))\n"
            "\n"
            "def shortest(graph, s, t):\n"
            "    \"\"\"无权图最短路：BFS 第一次到达 t 时的层数就是答案\"\"\"\n"
            "    q = deque([(s, 0)])\n"
            "    seen = {s}\n"
            "    while q:\n"
            "        node, d = q.popleft()\n"
            "        if node == t:\n"
            "            return d\n"
            "        for nxt in graph[node]:\n"
            "            if nxt not in seen:\n"
            "                seen.add(nxt)\n"
            "                q.append((nxt, d + 1))\n"
            "    return -1\n"
            "\n"
            "print(shortest(graph, 0, 4))     # 0 -> 1 -> 3 -> 4"
        ),
        "example_output": "[0, 1, 2, 3, 4]\n[0, 1, 3, 2, 4]\n3",
        "pitfalls": [
            "**忘了 `visited` 或者标记太晚**：无向图里会在相邻两点之间来回走导致死循环。而且**必须在入队时就标记**，"
            "如果等出队才标记，同一个点会被多次入队，队列爆掉、复杂度也退化。",
            "**用 `list` 当 BFS 的队列**：`q.pop(0)` 是 `O(n)`，整体变 `O(n²)`。BFS 一律用 `collections.deque` 的 `popleft()`。",
            "**网格 DFS 不判边界**：`grid[r][c]` 在 r 或 c 越界时直接 `IndexError`（Python 里负数下标还会「从右边绕回来」，"
            "造成更隐蔽的错误）。访问邻居前必须确认 `0 <= r < rows and 0 <= c < cols`。",
            "**用 DFS 求无权图最短路，或者让 DFS 递归得太深**：DFS 找到的第一条路径不一定最短 —— "
            "判断连通性、数连通块用 DFS，求最短步数、最少次数必须用 BFS。另外图上有 10 万个点、路径很深时递归会 `RecursionError`，要改成「显式栈 + while」的迭代写法。",
        ],
        "task": (
            "请实现 `num_islands(grid)`：数出二维网格里**岛屿的数量**。\n\n"
            "- `grid` 是列表的列表，元素是字符 `'1'`（陆地）或 `'0'`（水）\n"
            "- 岛屿由**上下左右**相邻的陆地连成；**对角线不算相连**\n"
            "- 可以假设网格四周都是水\n\n"
            "例：\n"
            "```\n[[\"1\",\"1\",\"0\"],\n [\"0\",\"1\",\"0\"],\n [\"0\",\"0\",\"1\"]]\n```\n"
            "这个网格里有 **2** 个岛（左上三块连成一个，右下单独一个）。\n\n"
            "要求：用 DFS 或 BFS 把每个岛「淹没」一遍来计数。"
            "可以直接修改传进来的 `grid`（判定每次都会传新的网格），也可以自己造副本。"
        ),
        "setup": "",
        "starter": (
            "def num_islands(grid):\n"
            "    # 返回岛屿数量\n"
            "    # 提示：遍历每个格子，遇到 '1' 就计数 +1，然后用 DFS/BFS 把整个岛标记成 '0'\n"
            "    pass\n"
        ),
        "hint": (
            "两层 `for` 扫每个格子：遇到 `'1'` 就 `count += 1`，然后从这个格子开始做一次 DFS 把相连的陆地全部改成 `'0'`。\n"
            "DFS 里先判边界和「是不是陆地」："
            "`if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1': return`，"
            "再把当前格子置 `'0'`，然后对四个方向各递归一次。\n"
            "注意 `grid[r][c] != '1'` 这一步同时兼顾了「是水」和「已经访问过」两种情况 —— "
            "把访问过的陆地改成 `'0'` 就天然起到了 `visited` 的作用。"
        ),
        "checker": """
try:
    assert num_islands([["1","1","0"],["0","1","0"],["0","0","1"]]) == 2, "这块网格应该有 2 个岛：左上三块连成一个、右下单独一个"
    assert num_islands([["0","0"],["0","0"]]) == 0, "全是水时要返回 0"
    assert num_islands([["1","1","1"],["1","1","1"]]) == 1, "全部是陆地、上下左右都连在一起，应该是 1 个岛"
    assert num_islands([["1","0","0"],["0","1","0"],["0","0","1"]]) == 3, "对角线不算相连，三个斜着排的陆地是 3 个"
    assert num_islands([["1"]]) == 1, "只有一个格子且是陆地时，应该返回 1"
    assert num_islands([["1","1","0","0","1"],["1","0","0","1","0"]]) == 3, "换个更大的输入再验一遍：左上三块连成 1 个岛，而 (0,4) 和 (1,3) 只是斜着相邻、不算相连，各算 1 个，共 3"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except IndexError as e:
    print("__FAIL__ 下标越界了：递归四个方向之前先判断 r、c 有没有超出范围：" + str(e))
except RecursionError as e:
    print("__FAIL__ 递归太深了 —— 网格里可能有大片相连的陆地，深搜要改成显式栈的迭代写法：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：无权图里求两点之间的最短路径，为什么必须用 BFS，DFS 不行？"
                ),
                "options": [
                    "BFS 层层向外扩散，第一次到达目标点时走过的层数就是最短距离；DFS 会一头扎到底，第一次到达时走的可能是绕远的路，不能保证最短",
                    "因为 DFS 会修改图的结构，导致路径信息丢失",
                    "因为 DFS 的时间复杂度比 BFS 高一个量级",
                    "其实 DFS 也可以，只要把每条路径都记下来最后取最短的一条就行",
                ],
                "answer_index": 0,
                "explanation": (
                    "BFS 的「层层扩散」性质保证了第一次访问一个节点时，用的边数最少 —— 这就是无权图最短路。"
                    "DFS 只保证「找到一条路」，不保证最短。D 说的「记录所有路径取最短」是指数级的暴力枚举，"
                    "和 BFS 的 `O(V+E)` 完全不是一个量级，不能算可行解法。"
                ),
            },
            {
                "type": "choice",
                "stem": "一个有向图能做拓扑排序的充分必要条件是什么？",
                "options": [
                    "它是有向无环图（DAG）",
                    "它是无向图且连通",
                    "它必须有环，否则排不出顺序",
                    "它必须用邻接矩阵存储",
                ],
                "answer_index": 0,
                "explanation": (
                    "拓扑排序是「把有依赖关系的任务排成线性顺序」，有环就说明存在循环依赖（A 依赖 B、B 又依赖 A），"
                    "排不出合法顺序。实现上通常用 BFS 统计入度：入度为 0 的点不断出队，"
                    "最后如果输出的点少于总点数，就说明存在环。"
                ),
            },
            {
                "type": "judge",
                "stem": "在 BFS 里，应该在节点**入队时**就把它标记为已访问，而不是等它出队时才标记。",
                "answer": True,
                "explanation": (
                    "如果等出队才标记，同一个节点可能被多个邻居重复入队，队列长度会膨胀、复杂度退化，"
                    "严重时还能把内存撑爆。入队即标记是标准写法。"
                ),
            },
            {
                "type": "blank",
                "stem": "BFS 用 ___ 来实现，DFS 用栈（或递归）来实现",
                "hint": "两个字",
                "answer": "队列",
                "accept": ["队列", "queue", "Queue", "deque", "双端队列"],
                "explanation": (
                    "BFS 要「按发现顺序依次处理」，正好是队列的先进先出；"
                    "DFS 要「后发现的先深入」，正好是栈的后进先出。"
                    "Python 里队列用 `collections.deque` 的 `popleft()`，不要用 `list.pop(0)`。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：图的邻接表和邻接矩阵怎么选？分别说说它们的空间复杂度和适用场景。"
                ),
                "keywords": ["O(V+E)", "O(V^2)", "稀疏", "稠密", "查边", "邻居"],
                "reference": (
                    "邻接表把每个点的邻居存成一个列表，空间 `O(V + E)`，"
                    "适合**稀疏图**（边远少于点的平方），几乎所有真实图都是这种，遍历某个点的邻居也很快。"
                    "邻接矩阵用一个 `V×V` 的二维数组存「两点之间有没有边」，空间固定 `O(V²)`，"
                    "适合**稠密图**，或者需要极频繁地 `O(1)` 判断「u 和 v 之间有没有边」的场景。\n"
                    "选择标准很简单：先看边的数量级 —— `E` 接近 `V²` 就用矩阵，否则用邻接表。"
                    "另外带权图里，邻接表要存成 `(邻居, 权重)` 的形式，"
                    "矩阵则把格子里的 0/1 换成权重（再加上 `∞` 表示不可达）。"
                ),
                "explanation": (
                    "答题要点是「先给空间复杂度，再给判断依据」，"
                    "最后补一句带权图的存储差异会更完整。"
                ),
            },
        ],
    },
]