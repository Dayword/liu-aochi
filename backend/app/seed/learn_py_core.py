"""阶段二：Python 基础补强（会写之后，把最咬人的几个角落补上）。

这批课是「补充课」，`supplementary=True` 的含义是：**不参与引导式学习的主线解锁链条**。
主线课的顺序仍是 基础 → 进阶 → ……，而这些补充课各自成一条支线，
不会插队到别人的学习路径里，也不会把老学生已经解锁的课重新锁上。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank，恰好 4 道）

挑的都是新手「能跑通、但一定会踩」的点：
None 与真值判断、lambda 与排序 key、enumerate/zip/map/filter、作用域与深浅拷贝。
"""

STARTER = "# 在下面写出你的代码（删掉这行注释也没关系）\n"

NONE_CHECKER = """
try:
    assert safe_get({"a": 1}, "a", 0) == 1, "取到了就原样返回：safe_get({'a': 1}, 'a', 0) 应该得到 1"
    assert safe_get({"a": None}, "a", "空") == "空", "取到的值本身是 None，也算「没有值」，应该返回默认值 '空'"
    assert safe_get({}, "b", 0) == 0, "键取不到时要返回默认值 0 —— data.get(key, default) 正好能兜住这种情况"
    assert safe_get({"x": 0}, "x", 9) == 0, "0 是有效值，不该被默认值顶掉 —— 写 `value or default` 会踩这个坑（0、空串都会被吞掉），要写成显式判断 `value is None`"
    assert safe_get({"x": ""}, "x", "空") == "", "空字符串不是 None，要原样返回 —— 只有当取到的值「是 None」时才回退到默认值"
    assert flags == [False, False, False, True], "flags 应该是 [bool(0), bool(''), bool([]), bool([0])] 的结果，也就是 [False, False, False, True]（注意非空列表 [0] 是真值）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

LAMBDA_CHECKER = """
try:
    assert sort_by_length(["bbb", "a", "cc"]) == ["a", "cc", "bbb"], "按长度升序排列：'a' 长 1、'cc' 长 2、'bbb' 长 3，结果应该是 ['a', 'cc', 'bbb']"
    assert sort_by_length(["ba", "ab"]) == ["ab", "ba"], "长度相同时要按字典序升序 —— 只写 key=len 不够：那是稳定排序，会保留原来的 ['ba', 'ab']；要用元组 key，比如 key=lambda w: (len(w), w)"
    words = ["bbb", "a", "cc"]
    result = sort_by_length(words)
    assert result == ["a", "cc", "bbb"], "sort_by_length 的排序结果不对"
    assert words == ["bbb", "a", "cc"], "sort_by_length 不许改动传进来的列表 —— 用 sorted() 得到新列表，别用 words.sort()（它原地排序，还返回 None）"
    assert result is not words, "返回的应该是全新的列表，而不是把入参原样返回"
    assert top_scores([{"name": "amy", "score": 90}, {"name": "bob", "score": 90}, {"name": "cat", "score": 80}], 2) == ["amy", "bob"], "按 score 降序取前 2 个名字；两人都是 90 分，并列时按名字升序，所以是 ['amy', 'bob']"
    assert top_scores([{"name": "z", "score": 1}, {"name": "a", "score": 5}], 1) == ["a"], "取分数最高的 1 个名字，应该是 'a'"
    assert top_scores([], 3) == [], "空列表要返回空列表，不要报错"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

ITER_CHECKER = """
try:
    assert number_positions(["a", "b", "c"]) == [(1, "a"), (2, "b"), (3, "c")], "序号要从 1 开始、顺序不能乱：应该得到 [(1, 'a'), (2, 'b'), (3, 'c')] —— 提示用 enumerate(words, start=1)，外面再套一层 list(...)"
    assert number_positions([]) == [], "空列表要返回空列表"
    assert pair_up(["a", "b", "c"], [1, 2]) == {"a": 1, "b": 2}, "zip 以最短的为准：多余的 'c' 要忽略，用 dict(zip(names, scores)) 就能得到 {'a': 1, 'b': 2}"
    assert isinstance(evens([1, 2]), list), "evens 必须返回 list —— 直接 return filter(...) 得到的是迭代器，len() 会报错；记得用 list(...) 包一层，或者写列表推导式"
    assert evens([1, 2, 3, 4]) == [2, 4], "evens 要挑出偶数：[1, 2, 3, 4] 里的偶数是 2 和 4"
    assert isinstance(add_all([1], [2]), list), "add_all 也必须返回 list，不能返回 map 迭代器"
    assert add_all([1, 2], [10, 20]) == [11, 22], "add_all 要把两个等长列表逐项相加：[1, 2] 和 [10, 20] 相加应得 [11, 22]"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

SCOPE_CHECKER = """
try:
    first = append_safe("a")
    second = append_safe("b")
    assert first == ["a"] and second == ["b"], "两次调用结果串在一起了：应该分别得到 ['a'] 和 ['b']。八成把默认参数写成了 target=[] —— 默认值只在函数定义时创建一次，会被所有调用共享；要写 target=None，进函数后再新建列表"
    assert first is not second, "两次不传 target 的调用必须返回两个不同的列表对象"
    target = []
    got = append_safe("x", target)
    assert got is target, "传了 target 时，要在传入的那个列表上追加并返回它本身（用 is 判断是不是同一个对象），而不是复制一个新列表"
    assert target == ["x"], "追加之后，原来的 target 里应该能看到 'x'"
    outer = [[1], [2]]
    sh = shallow(outer)
    assert sh is not outer, "shallow 要返回一个新的外层列表"
    assert sh == [[1], [2]], "shallow 返回的内容应该和 outer 一样"
    sh[0].append(99)
    assert outer[0] == [1, 99], "浅拷贝只复制外层：改 sh 的内层会连带改到 outer —— shallow 用 list(outer) 或 copy.copy(outer) 就行"
    outer2 = [[1], [2]]
    dp = deep(outer2)
    dp[0].append(99)
    assert outer2[0] == [1], "深拷贝要完全独立：改 dp 的内层不该影响 outer2 —— 用 copy.deepcopy(outer2)"
    assert dp == [[1, 99], [2]], "deep 返回的内容应该是修改后的独立副本"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

LESSONS: list[dict] = [
    {
        "code": "py-none",
        "stage": "Python 基础补强",
        "title": "None 与真值判断",
        "summary": "分清 None 和假值，别再被 or 坑到",
        "supplementary": True,
        "definition": (
            "`None` 是 Python 里专门的**「没有值」**。它只此一个（单例），表示「这里本该有个值，但现在是空的」。\n\n"
            "判断「是不是 None」用 **`is None`**，而不是 `== None`。`is` 比较「是不是同一个对象」，"
            "`==` 比较「值相不相等」；对 None 来说结果常常一样，但 `is None` 是公认的规范写法。\n\n"
            '**「假值」和 `None` 是两回事**：`bool(0)`、`bool("")`、`bool([])`、`bool({})`、`bool(None)` 全是 `False`。'
            "但只有 `None` 才表示「没有值」——0 是一个值，空字符串也是一个值。"
            "所以「判断有没有拿到东西」要用 `is None`，不能图省事写 `not x`。\n\n"
            '**`and` / `or` 返回的是操作数本身，不是 `True` / `False`**：`or` 返回第一个「真值」操作数'
            "（都不真就返回最后一个），`and` 返回第一个「假值」操作数（都真就返回最后一个）。"
            '所以 `0 or "默认值"` 得到 `"默认值"`，而 `"" or []` 得到 `[]`。\n\n'
            "最后：函数**忘了写 `return`**（或只写了 `return` 没带值），调用结果就是 `None`。"
            "这是新手最常见的「函数返回 None」来源。"
        ),
        "plain": (
            "把 `None` 想成**一个空白的标签，上面写着「这里没有东西」**。"
            "它和「0 个」「空字符串」不一样——那些是「有东西，只不过内容是零或空」。\n\n"
            "所以：\n\n"
            "- `x is None` —— 问「这个抽屉里是不是压根没放东西」\n"
            "- `not x` —— 问「这个东西算不算假」——0、空串、空列表都会被算进来\n\n"
            "`or` 的经典坑：\n\n"
            "```python\n"
            "value = 0            # 0 是有效数值\n"
            "value = value or 10  # 结果变成 10 —— 数量 0 被当成「没有」丢掉了！\n"
            "```\n\n"
            "`or` 只认「假值」，不认「业务上算不算空」。想只兜住「没拿到」，就明确写 `if value is None:`。"
        ),
        "example": (
            "a = None\n"
            "print(a is None)            # True：判断「没有值」的规范写法\n"
            "print(a == None)            # True：能跑，但推荐用 is\n"
            "\n"
            'print(bool(0), bool(""), bool([]), bool(None))\n'
            "\n"
            'print(0 or "默认值")        # 0 是假值，or 返回后面那个\n'
            'print("abc" and "xyz")     # 都真，and 返回最后一个\n'
            "\n"
            "def no_return():\n"
            "    x = 1\n"
            "\n"
            "print(no_return())          # 忘了 return，得到 None"
        ),
        "example_output": (
            "True\nTrue\nFalse False False False\n默认值\nxyz\nNone"
        ),
        "pitfalls": [
            "**用 `not x` 代替 `is None`**：`not 0` 是 `True`，会把有效的 0 误判成「没有值」。只有 `None` 才该用 `is None` 判。",
            "**用 `value or default` 兜默认值**：value 是 0、`\"\"`、`[]` 时会被错误地替换成 default——它们是「有值但为假」，不是「没有值」。",
            "**误以为 `and` / `or` 只返回 True/False**：它们返回的是**操作数本身**，所以 `\"\" or []` 得到 `[]`（不是 False），`1 and 2` 得到 2。",
            "**函数忘了写 `return`**：函数会隐式返回 `None`，于是 `result = f()` 之后拿 `result + 1` 就报 `TypeError`。",
        ],
        "task": (
            "请完成两件事：\n\n"
            "1. 实现函数 `safe_get(data, key, default)`：从字典 `data` 里取 `key`。\n"
            "   - 键取不到 → 返回 `default`\n"
            "   - 取到了、但值本身是 `None` → 也返回 `default`\n"
            "   - 其他情况（包括值是 `0`、`\"\"` 这种「假值」）→ 原样返回值\n"
            "   提示：`data.get(key, ...)` 只能兜住「键不存在」，还要再判断一下取到的值是不是 None。\n\n"
            "2. 定义变量 `flags`，它是由这四个表达式的结果按顺序组成的列表：\n"
            '   `bool(0)`、`bool("")`、`bool([])`、`bool([0])`\n'
            "   用来直观感受「什么算假值」。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "`value = data.get(key, default)` 先把「键取不到」兜住；"
            "再 `if value is None:` 就把 value 换成 default。\n"
            "注意是 `value is None`，别写成 `value or default`（0 和空串会被误伤）。\n"
            '`flags = [bool(0), bool(""), bool([]), bool([0])]`。'
        ),
        "checker": NONE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "想判断变量 `x` 是不是 None，下面哪种写法最规范？",
                "options": ["x is None", "x == None", "x = None", "not x"],
                "answer_index": 0,
                "explanation": (
                    "`is` 比较的是「是不是同一个对象」，None 是单例，写 `is None` 最规范也最安全；"
                    "`x == None` 能跑但不推荐；`x = None` 是赋值不是判断；"
                    "`not x` 会把 0、空串、空列表一起当成「空」，它们和 None 不是一回事。"
                ),
            },
            {
                "type": "choice",
                "stem": "已知 `value = 0`，那么表达式 `value or 10` 的结果是？",
                "options": ["10", "0", "True", "None"],
                "answer_index": 0,
                "explanation": (
                    "`or` 返回第一个「真值」操作数。0 是假值，所以继续往后看，返回 10。"
                    "这也正是 `value or default` 的坑：value 是 0 时会被错误地替换成默认值。"
                ),
            },
            {
                "type": "judge",
                "stem": "在 Python 里，`0`、空字符串、空列表这些「假值」，本质上和 `None` 一样都表示「没有值」。",
                "answer": False,
                "explanation": (
                    "假值只是 `bool(x)` 为 False；它们本身是「有值」的（一个内容为 0 的数、一个空字符串对象）。"
                    "只有 `None` 才表示「没有值」，所以判断「没拿到东西」要用 `is None` 而不是 `not x`。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全下面这一行，让它「键取不到时返回默认值」：\nvalue = data.___(\"name\", \"匿名\")",
                "answer": "get",
                "hint": "填一个字典方法名",
                "explanation": (
                    "`dict.get(key, default)` 在键不存在时返回 default，这是字典取值的标准写法；"
                    "直接写 `data[\"name\"]` 在键不存在时会抛 KeyError。"
                ),
            },
        ],
    },
    {
        "code": "py-lambda",
        "stage": "Python 基础补强",
        "title": "lambda 与排序 key",
        "summary": "用 lambda 和 key 写出稳定的多级排序",
        "supplementary": True,
        "definition": (
            "**lambda 是「用完就扔的匿名函数」**：`lambda x: x + 1` 等价于一个只做一件事、没有名字的小函数。"
            "它**只能写一个表达式**，不能有语句（不能写 `if` 语句块、循环、赋值），返回值就是这个表达式的结果。\n\n"
            "`sorted(列表, key=...)` 里的 **`key` 是「排序依据」，不是「比较函数」**："
            "key 收到一个元素，返回一个「用来比大小的值」，Python 拿这个值去排序。"
            "所以 `key=len` 表示「按长度排」，`key=lambda s: s[-1]` 表示「按最后一个字符排」。\n\n"
            "**`sorted()` 是稳定排序**：key 相等的元素会保持原来的先后顺序。"
            "利用这一点可以做多级排序，但更直接的写法是**元组 key**——比较元组时会先比第一项，第一项相等再比第二项：\n\n"
            "```python\n"
            "sorted(records, key=lambda r: (-r['score'], r['name']))\n"
            "# 先按 score 从大到小；分数相同时按 name 从小到大\n"
            "```\n\n"
            "（`-r['score']` 取负，是为了把「默认的升序」变成「降序」。）\n\n"
            "**`list.sort()` 原地排序、且返回 `None`；`sorted(list)` 返回一个新列表、原列表不动**。"
            "不想改动原数据就用 `sorted()`。\n\n"
            "`max()` / `min()` 也能带 key：`max(records, key=lambda r: r['score'])` 取出分数最高的那条记录。"
        ),
        "plain": (
            "**key 就是「比什么」**。想象给一排学生排队，key 是「按身高排」还是「按名字排」——"
            "你提供的是**测量的尺子**（把一条数据变成一把可以比较的量），不是「谁比谁高的裁判」。"
            "这是最容易搞混的地方。\n\n"
            "**多级排序 = 先看主字段，再看次字段**：就像先比较总分，总分一样再看姓名。"
            "元组 `(分数, 姓名)` 天然支持这种「先看第一项、再看第二项」的比较；"
            "第一项写成 `-分数` 就能实现「分数高的排前面」。\n\n"
            "**`.sort()` vs `sorted()`**：`.sort()` 是「把这一摞牌在原地理好」（牌还是那一摞，理完返回空）；"
            "`sorted()` 是「照着这摞牌另抄一份理好的」（原来那摞没动）。"
        ),
        "example": (
            "nums = [4, 1, 3]\n"
            "print(sorted(nums))              # 返回新列表\n"
            "print(nums)                      # 原列表没动\n"
            "\n"
            'words = ["bbb", "a", "cc"]\n'
            "print(sorted(words, key=len))    # 按长度排\n"
            "\n"
            "# 多级排序：先按 score 降序，分数相同再按 name 升序\n"
            'records = [("amy", 90), ("bob", 90), ("cat", 80)]\n'
            "print(sorted(records, key=lambda r: (-r[1], r[0])))"
        ),
        "example_output": (
            "[1, 3, 4]\n[4, 1, 3]\n['a', 'cc', 'bbb']\n"
            "[('amy', 90), ('bob', 90), ('cat', 80)]"
        ),
        "pitfalls": [
            "**把 key 当成比较函数**：key 只要「返回排序依据」就行，不需要返回 True/False 或谁大谁小；要反转用 `reverse=True`。",
            "**lambda 里写语句**：`lambda` 只能写一个表达式，写 `lambda x: if x: ...` 会直接语法报错，这种情况改用 `def`。",
            "**以为 `key=len` 就够做多级排序**：key 相等时靠稳定排序保留原顺序，不是按第二关键字排；要按第二关键字就写元组 key。",
            "**`nums = nums.sort()`**：`.sort()` 原地排序并返回 `None`，这样写会把 nums 变成 None；要新列表用 `sorted(nums)`。",
        ],
        "task": (
            "请实现两个函数：\n\n"
            "1. `sort_by_length(words)` —— 返回一个**新列表**：按**长度升序**排列；"
            "长度相同时按**字典序（字母顺序）升序**。不允许改动传进来的 `words`。\n"
            "   提示：用 `sorted(...)`，key 用元组 `(len(w), w)` 一次搞定两级排序。\n\n"
            "2. `top_scores(records, n)` —— `records` 形如 `[{\"name\": \"...\", \"score\": 数字}, ...]`。"
            "返回**按 score 降序**的前 n 个 `name` 组成的列表；分数相同时按名字升序。\n"
            "   提示：`sorted(records, key=lambda r: (-r['score'], r['name']))`，再切片取前 n 个。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "`sort_by_length`：`return sorted(words, key=lambda w: (len(w), w))`\n"
            "`top_scores`：先 `ordered = sorted(records, key=lambda r: (-r['score'], r['name']))`，"
            "再 `return [r['name'] for r in ordered[:n]]`"
        ),
        "checker": LAMBDA_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "在 `sorted(records, key=lambda r: r['score'])` 里，`key` 参数的作用是？",
                "options": [
                    "指定「按什么算排序依据」，函数返回的值用来比大小",
                    "指定一个比较函数，返回两个元素谁大谁小",
                    "指定要不要反转顺序",
                    "指定用哪种排序算法",
                ],
                "answer_index": 0,
                "explanation": (
                    "key 接收一个「把元素映射成排序依据」的函数，Python 拿这个依据去比大小。"
                    "它不像 C 的 qsort 那样传「比较两个元素的函数」；要反转用 `reverse=True`；"
                    "排序算法由 Python 内部决定，这个参数管不着。"
                ),
            },
            {
                "type": "choice",
                "stem": "`nums = [3, 1, 2]`，执行 `nums.sort()` 之后，`nums` 和它的返回值分别是什么？",
                "options": [
                    "nums 变成 [1, 2, 3]，返回值是 None",
                    "nums 不变，返回值是新列表 [1, 2, 3]",
                    "nums 变成 [1, 2, 3]，返回值也是 [1, 2, 3]",
                    "会报错，list 没有 sort 方法",
                ],
                "answer_index": 0,
                "explanation": (
                    "`list.sort()` 原地排序、返回 None（所以写 `nums = nums.sort()` 会把 nums 变成 None）。"
                    "要拿到新列表又不改原数据，用 `sorted(nums)`。"
                ),
            },
            {
                "type": "judge",
                "stem": "`sorted()` 是稳定排序，所以 `sorted(records, key=lambda r: -r['score'])` 里分数相同的元素会保持它们原来的先后顺序。",
                "answer": True,
                "explanation": (
                    "这就是稳定排序：key 相等的元素保留原顺序。所以多级排序可以先按次要字段排一次、"
                    "再按主要字段排一次；不过更直接的写法是一次给一个元组 key。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全这一行，让 `words` 按字符串长度升序排列（返回新列表）：\nresult = sorted(words, key=___)",
                "answer": "len",
                "hint": "填一个内置函数名",
                "explanation": "`key=len` 表示用每个元素的长度作为排序依据。",
            },
        ],
    },
    {
        "code": "py-iterate",
        "stage": "Python 基础补强",
        "title": "enumerate / zip / map / filter",
        "summary": "别再手写下标，用好这几个遍历工具",
        "supplementary": True,
        "definition": (
            "**`enumerate(xs)` 同时给你「序号 + 元素」**：`for i, x in enumerate(xs)`。"
            "写 `for i in range(len(xs))` 再 `xs[i]` 是新手写法——多一层下标、还容易越界。"
            "序号要从 1 开始就加 `start=1`：`enumerate(xs, start=1)`。\n\n"
            "**`zip(a, b)` 把多个序列按位置配对**：`list(zip([1, 2, 3], ['a', 'b']))` 得到 `[(1, 'a'), (2, 'b')]`"
            "——**以最短的那个为准**，多出来的直接丢掉（不报错、也不补 `None`）。"
            "注意 `zip` 返回的是**迭代器**，要看内容得用 `list()` 转出来。\n\n"
            "**`map(f, xs)` 对每个元素应用 f，`filter(f, xs)` 保留让 f 为真的元素**。"
            "它们返回的都是**迭代器**，不是列表：\n\n"
            "- 迭代器**只能消费一次**——遍历过一遍就空了，再遍历得到空\n"
            "- 迭代器**没有 `len()`**，要看长度得先 `list()` 转成列表\n\n"
            "这就是 `len(filter(...))` 报错的原因。\n\n"
            "**列表推导式通常比 `map`/`filter` 更可读**：`[x * 2 for x in xs if x > 0]` "
            "比 `map` + `filter` 套在一起清楚。需要惰性、省内存时才优先选 `map`/`filter` 这类迭代器。"
        ),
        "plain": (
            "**`enumerate` 像给队伍里每个人发号码牌**：你既知道「第几个」，也知道「是谁」，不用自己去数。\n\n"
            "**`zip` 像把两条拉链咬合**：两条长度不一样时，短的那条到头了，咬合就停——长出来的部分没人配，自动忽略。\n\n"
            "**迭代器像一次性传送带**：东西从你面前过一遍，过了就没了。想再看一遍，得重新造一条"
            "（重新调用一次 `map`/`filter`）。所以 `list(...)` 就是「把传送带上的东西全收进一个箱子」，"
            "之后随便看、还能数个数。\n\n"
            "写 `for i in range(len(xs)): x = xs[i]`，等于「先数总人数、再按号码挨个叫人」，"
            "而 `for i, x in enumerate(xs)` 是「一边点名一边报号」——后者少一次出错的机会。"
        ),
        "example": (
            'names = ["amy", "bob"]\n'
            "\n"
            "for i, name in enumerate(names, start=1):\n"
            "    print(i, name)\n"
            "\n"
            "pairs = list(zip(names, [90, 85, 70]))   # 以最短的为准\n"
            "print(pairs)\n"
            "\n"
            "nums = [1, 2, 3, 4]\n"
            "print(list(map(lambda x: x * 10, nums)))\n"
            "print(list(filter(lambda x: x % 2 == 0, nums)))\n"
            "\n"
            "# 迭代器只能消费一次\n"
            "it = map(lambda x: x + 1, nums)\n"
            "print(list(it))\n"
            "print(list(it))"
        ),
        "example_output": (
            "1 amy\n2 bob\n[('amy', 90), ('bob', 85)]\n"
            "[10, 20, 30, 40]\n[2, 4]\n[2, 3, 4, 5]\n[]"
        ),
        "pitfalls": [
            "**`zip` 结果忘了转 list**：在 Python 3 里 `zip(...)` 是迭代器，直接 `print(zip(a, b))` 打印出来是一串对象地址，要 `list(zip(a, b))`。",
            "**以为 `zip` 会补全**：长度不同时以最短的为准，长出来的部分被静默丢弃，不会补 None 也不报错——对不齐的锅要自己查。",
            "**把迭代器当列表用**：`map` / `filter` 返回迭代器，`len()` 会报 TypeError，而且遍历一次就空了，第二次拿到的是空。",
            "**`for i in range(len(xs))` 硬凑下标**：写法啰嗦又容易越界，同时要下标和值就用 `enumerate(xs)`。",
        ],
        "task": (
            "请实现四个函数（返回值必须是 **list / dict**，不要返回迭代器）：\n\n"
            "1. `number_positions(words)` —— 返回形如 `[(1, 第一个词), (2, 第二个词), ...]` 的列表，**下标从 1 开始**。\n"
            "   提示：`enumerate(words, start=1)`。\n\n"
            "2. `pair_up(names, scores)` —— 用 `zip` 把两个列表拼成 `{名字: 分数}` 的字典；"
            "长度不一样时以**短的**为准，多余的忽略。\n\n"
            "3. `evens(nums)` —— 返回 `nums` 里所有偶数组成的 **list**。\n"
            "   提示：可以用 `filter`，但记得 `list(...)` 包一层；也可以写列表推导式。\n\n"
            "4. `add_all(a, b)` —— 把两个**等长**列表逐项相加，返回 **list**"
            "（如 `[1, 2]` 和 `[10, 20]` → `[11, 22]`）。\n"
            "   提示：`map` 可以同时吃多个列表，但同样要 `list(...)` 包一层。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "`number_positions`：`return list(enumerate(words, start=1))`\n"
            "`pair_up`：`return dict(zip(names, scores))`\n"
            "`evens`：`return [x for x in nums if x % 2 == 0]`（或 `list(filter(...))`）\n"
            "`add_all`：`return [x + y for x, y in zip(a, b)]`（或 `list(map(lambda x, y: x + y, a, b))`）"
        ),
        "checker": ITER_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "想把列表 `words` 里的词按「从 1 开始」的编号打印出来，最清楚的写法是？",
                "options": [
                    "for i, w in enumerate(words, start=1): print(i, w)",
                    "for i in range(len(words)): print(i, words[i])",
                    "for w in words: print(words.index(w), w)",
                    "for i, w in zip(words, range(len(words))): print(i, w)",
                ],
                "answer_index": 0,
                "explanation": (
                    "`enumerate(words, start=1)` 直接同时给你序号和元素，序号从 1 开始。"
                    "B 能跑但下标从 0 起、还要手动取元素；C 在元素重复时会取到错误的第一个下标；"
                    "D 把序号和元素的位置传反了。"
                ),
            },
            {
                "type": "choice",
                "stem": "`list(zip([1, 2, 3], [\"a\", \"b\"]))` 的结果是？",
                "options": [
                    "[(1, 'a'), (2, 'b')]",
                    "[(1, 'a'), (2, 'b'), (3, None)]",
                    "[(1, 'a'), (2, 'b'), (3, 'c')]",
                    "报错，两个列表长度不一样",
                ],
                "answer_index": 0,
                "explanation": "`zip` 以最短的序列为准，多余的 3 会被直接丢弃，既不补 None 也不报错。",
            },
            {
                "type": "judge",
                "stem": "`map` 和 `filter` 返回的是列表，可以直接用 `len()` 取长度。",
                "answer": False,
                "explanation": (
                    "它们返回的是**迭代器**，没有 `len()`，而且只能消费一次——遍历过一遍就空了，"
                    "第二次拿到的是空。要列表得用 `list(...)` 包一层。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全这一行，让 `for` 循环同时拿到序号（从 1 开始）和元素：\nfor i, w in ___(words, start=1):",
                "answer": "enumerate",
                "hint": "填一个内置函数名",
                "explanation": "`enumerate(words, start=1)` 依次产出 `(1, w1)、(2, w2)……`，比 `range(len(...))` 清楚得多。",
            },
        ],
    },
    {
        "code": "py-scope",
        "stage": "Python 基础补强",
        "title": "作用域、可变性与深浅拷贝",
        "summary": "搞清作用域、可变对象和深浅拷贝的坑",
        "supplementary": True,
        "definition": (
            "**函数里赋值 = 新建一个局部变量**：`def f(): x = 1` 里的 `x` 和外面的 `x` 没关系，函数一结束就没了。"
            "想让函数改外面的名字，得声明 `global` / `nonlocal`——但**先问自己该不该改**，"
            "绝大多数时候「函数偷偷改外面的变量」是设计没理顺的信号。\n\n"
            "**可变对象传进函数后原地修改，外面会跟着变**：列表、字典、集合都是可变的。"
            "`def f(lst): lst.append(1)`，调用后传进去的那个列表真的多了一个 1"
            "——因为传进去的是**同一个对象**，不是它的副本。\n\n"
            "**`=` 赋值不是复制**：`b = a` 只是让 `b` 这个名字也**指向 a 指向的那个对象**。改 `b` 会连 `a` 一起改。\n\n"
            "**拷贝分两层**：\n\n"
            "- 浅拷贝 `list(x)` / `copy.copy(x)`：只复制外面一层。外层是新对象，"
            "**内层元素还是和原来共享的**——改内层会互相影响\n"
            "- 深拷贝 `copy.deepcopy(x)`：里里外外全部复制，改哪一层都不影响原对象\n\n"
            "**经典陷阱——可变默认参数**：\n\n"
            "```python\n"
            "def add(x, acc=[]):   # 危险！\n"
            "    acc.append(x)\n"
            "    return acc\n"
            "```\n\n"
            "默认值 `[]` **只在函数定义时创建一次**，被所有「不传 acc」的调用共享，于是结果会越攒越多。"
            "正确写法是 `acc=None`，进函数后再判断、再新建。"
        ),
        "plain": (
            "**名字是标签，对象是箱子**。`b = a` 不是「把箱子复制一份」，而是「再拿一张写着 b 的标签，"
            "贴到同一个箱子上」。所以从 b 这条线去改箱子，从 a 这条线看当然也变了。\n\n"
            "**函数收参数 = 收到一张写着对象位置的纸条**，不是收到一个复制品。纸条指向的箱子还是原来那个，"
            "所以函数里「原地改箱子」（`append` / `remove` / `sort`）外面看得见；"
            "但如果函数里只是「把纸条撕了重新写一张」——即 `lst = [...]` 重新赋值——"
            "那只是换了局部名字的指向，外面不受影响。\n\n"
            "**浅拷贝 vs 深拷贝**：浅拷贝像「换了个新文件夹，但里面装的文件还是原来那些文件」——"
            "往里加一个新文件不影响原文件夹，可你改某个文件的内容，原文件夹里那个也跟着改；"
            "深拷贝则是「连文件也全都复印一遍」。"
        ),
        "example": (
            "# = 不是复制，只是又起了个名字\n"
            "a = [1, 2]\n"
            "b = a\n"
            "b.append(3)\n"
            "print(a)                     # a 也变了\n"
            "\n"
            "import copy\n"
            "\n"
            "# 浅拷贝：只有外层是新的\n"
            "outer = [[1], [2]]\n"
            "sh = copy.copy(outer)\n"
            "sh[0].append(99)\n"
            "print(outer)                 # 内层被连带改了\n"
            "\n"
            "# 深拷贝：完全独立\n"
            "outer2 = [[1], [2]]\n"
            "dp = copy.deepcopy(outer2)\n"
            "dp[0].append(99)\n"
            "print(outer2)                # 原样不动\n"
            "\n"
            "# 可变默认参数陷阱\n"
            "def add(x, acc=[]):\n"
            "    acc.append(x)\n"
            "    return acc\n"
            "\n"
            'print(add("a"))\n'
            'print(add("b"))              # 不是 ["b"]！'
        ),
        "example_output": (
            "[1, 2, 3]\n[[1, 99], [2]]\n[[1], [2]]\n['a']\n['a', 'b']"
        ),
        "pitfalls": [
            "**可变默认参数 `def f(x, acc=[])`**：默认值只在定义时创建一次，被所有调用共享，结果会跨调用累积；要写 `acc=None` 再在函数里新建。",
            "**以为 `b = a` 是复制**：那只是又起了一个名字，两者指向同一个对象，改 b 会连 a 一起改；要副本用 `a[:]` / `list(a)` / `copy.copy(a)`。",
            "**浅拷贝当深拷贝用**：`list(outer)` 只复制外层，内层元素还是共享的，改内层照样影响原对象；要彻底独立用 `copy.deepcopy`。",
            "**在函数里给外层变量赋值却忘了 `global` / `nonlocal`**：那只会新建一个局部变量，外面那个纹丝不动；该改的话先想清楚是不是设计问题。",
        ],
        "task": (
            "请实现三个函数：\n\n"
            "1. `append_safe(item, target=None)`\n"
            "   - **不传** `target` 时：每次调用都返回一个**新的**单元素列表 `[item]`，上一次调用的结果不能受影响。\n"
            "   - **传了** `target` 时：在传入的那个列表上 `append(item)`，并返回它本身（同一个对象）。\n"
            "   ⚠️ 参数签名照抄 `target=None`，不要写成 `target=[]`。\n\n"
            "2. `shallow(outer)` —— 返回 `outer` 的**浅拷贝**：外层是一个新列表，内层元素仍是原来的对象。\n"
            "   提示：`list(outer)` 或 `copy.copy(outer)`。\n\n"
            "3. `deep(outer)` —— 返回 `outer` 的**深拷贝**：内外层都完全独立。\n"
            "   提示：`copy.deepcopy(outer)`。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "`append_safe`：先 `if target is None: target = []`，再 `target.append(item)`，最后 `return target`。\n"
            "`shallow`：`import copy` 后 `return copy.copy(outer)`（也可以 `return list(outer)`）。\n"
            "`deep`：`return copy.deepcopy(outer)`。"
        ),
        "checker": SCOPE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面这个函数每次调用都会把结果累积起来（第二次调用拿到 ['a', 'b']），原因是？\n```\ndef add(x, acc=[]):\n    acc.append(x)\n    return acc\n```",
                "options": [
                    "默认值 `[]` 只在函数定义时创建一次，被所有调用共享",
                    "`append` 会修改全局变量",
                    "Python 的列表是引用类型，所以每次都要重新创建",
                    "因为函数最后没写 `return acc`",
                ],
                "answer_index": 0,
                "explanation": (
                    "默认参数在**定义时**求值一次，那个列表对象被所有「不传 acc」的调用共享。"
                    "要避免就写 `acc=None`，进函数后再 `acc = [] if acc is None else acc`。"
                ),
            },
            {
                "type": "choice",
                "stem": "`outer = [[1], [2]]`，`sh = list(outer)`。执行 `sh[0].append(9)` 之后，`outer` 是？",
                "options": ["[[1, 9], [2]]", "[[1], [2]]", "[[1, 9], [2, 9]]", "会报错"],
                "answer_index": 0,
                "explanation": (
                    "`list(outer)` 是浅拷贝：外层是新列表，但内层 [1]、[2] 还是和 outer 共享的同一批对象，"
                    "改内层会连带改到 outer。要彻底独立用 `copy.deepcopy`。"
                ),
            },
            {
                "type": "judge",
                "stem": "在函数里对一个可变参数（比如列表）执行 `append`，函数外面那个列表也会变。",
                "answer": True,
                "explanation": (
                    "Python 传的是「对象的引用」。函数里对同一个列表做原地修改（append/remove/sort），"
                    "外面的列表跟着变。想不影响外面，就传一个副本进去，或者干脆返回一个新对象。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全这一行，得到一份和外层完全独立的拷贝：\nimport copy\ndp = copy.___(outer)",
                "answer": "deepcopy",
                "hint": "填一个函数名",
                "explanation": "`copy.deepcopy(outer)` 会把对象里里外外都复制一份；`copy.copy` 只复制一层（浅拷贝）。",
            },
        ],
    },
]
