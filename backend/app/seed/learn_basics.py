"""阶段一：Python 基础（会写代码）。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker / cases，二选一或同时用）
- 习题 quizzes（选择 choice / 判断 judge / 填空 blank / 简答 short / 应用 applied）

order_no 由 learn.py 统一按顺序编号，这里不用写。
"""

STARTER = "# 在下面写出你的代码（删掉这行注释也没关系）\n"

VAR_CHECKER = """
try:
    assert isinstance(city, str), "city 应该是字符串，记得加引号，比如 city = \\"北京\\""
    assert isinstance(year, int), "year 应该是整数，不要加引号"
    assert isinstance(MAX_SCORE, int), "MAX_SCORE 应该是整数"
    assert MAX_SCORE == 100, "MAX_SCORE 的值应该是 100"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

TYPE_CHECKER = """
try:
    assert isinstance(num, int), "num 应该是整数 —— 用 int(s) 转换，转换后不要带引号"
    assert num == 25, "num 的值应该来自 int(s)，也就是 25"
    assert isinstance(result, int), "result 应该是整数"
    assert result == 100, "result 应该等于 num * 4"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

OP_CHECKER = """
try:
    assert each == 3, "each 算错了：17 个苹果分给 5 个人，每人能拿几个？想一想 17 // 5"
    assert left == 2, "left 算错了：分完之后还剩几个？想一想 17 % 5"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

STR_CHECKER = """
try:
    assert isinstance(cleaned, str), "cleaned 应该是字符串"
    assert cleaned == "AI Agent", "cleaned 应该是去掉首尾空格后的 'AI Agent'，检查是不是用了 strip()"
    assert isinstance(parts, list) and parts == ["AI", "Agent"], "parts 应该是用空格切开后的列表"
    assert isinstance(msg, str) and "3" in msg and "claude" in msg, "msg 要用 f-string 把两个变量拼进去"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

SET_CHECKER = """
try:
    assert isinstance(unique, set), "unique 应该是集合（用 set(...) 得到）"
    assert unique == {3, 1, 2}, "unique 应该是不重复的三个数"
    assert isinstance(point, tuple), "point 应该是元组（用圆括号）"
    assert point == (3, 5), "point 应该是 (3, 5)"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DICT_CHECKER = """
try:
    # 用「键取不到就给默认值」的方式累加词频
    assert counts == {"a": 3, "b": 1, "c": 1}, "counts 词频算错了（a 在列表里出现了 3 次），用 counts.get(w, 0) + 1 试试"
    assert isinstance(info.get("model"), str), "info 应该是一个有 model 键的字典"
    assert info["model"] == "glm-5.3", "info['model'] 应该是字符串 'glm-5.3'（注意别写成布尔值 True）"
    assert info.get("tools") == 2, "info['tools'] 应该是数字 2，不是字符串 '2'"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

FUNC_CHECKER = """
try:
    assert area(2, 3) == 6, "area(2, 3) 应该返回 6，检查一下函数里的计算"
    assert area(4, 5) == 20, "area(4, 5) 应该返回 20"
    assert area(7, 2) == 14, "area(7, 2) 应该返回 14 —— 函数要对任意长宽都成立"
    assert result == 20, "result 应该等于 area(4, 5) 的返回值"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

LESSONS: list[dict] = [
    {
        "code": "py-var",
        "stage": "Python 基础",
        "title": "变量与常量",
        "summary": "给数据起个名字，后面就能反复用",
        "definition": (
            "变量是一个「名字」，用来指向内存里存着的某个值。用 `=` 把值绑定到名字上，"
            "写 `age = 18` 就是「让 age 这个名字指向 18」。之后写 `age`，Python 就取出 18。\n\n"
            "Python 里**没有真正的常量**，只有约定俗成的常量：把名字全部写成大写（如 `PI`），"
            "表示这个值不应该被修改。这只是一个约定，改了不会报错。"
        ),
        "plain": (
            "把变量想成**贴了标签的收纳盒**。`age = 18`：拿一个盒子，贴上 `age` 标签，把 18 放进去；"
            "以后喊 `age`，Python 就去盒子里把 18 拿出来。\n\n"
            "再写 `age = 20` 不是又拿了新盒子，而是**把原来盒子里的东西换掉**——所以叫「变量」。\n\n"
            "⚠️ 这里的 `=` 不是数学里的「等于」，而是**「把右边的值放进左边的名字」**。"
            "判断相等要写两个等号 `==`。"
        ),
        "example": (
            'name = "小明"        # 字符串：用引号包起来\n'
            "age = 18             # 整数：不用引号\n"
            "PI = 3.14159         # 全大写：约定俗成的常量\n"
            "\n"
            "print(name, age, PI)\n"
            "\n"
            "age = age + 1        # 先取出 age 的值加 1，再放回去\n"
            "print(age)"
        ),
        "example_output": "小明 18 3.14159\n19",
        "pitfalls": [
            "**`=` 和 `==` 写混**：`age = 18` 是赋值；判断相等要用 `age == 18`。写 `18 = age` 直接语法报错。",
            "**变量必须先赋值再使用**：没定义就用会报 `NameError: name 'x' is not defined`。",
            "**名字不能乱起**：不能以数字开头（`2name` 非法）、不能有空格、不能用关键字（`if`/`class`/`for`）。中文名合法但不推荐。",
            "**常量只是约定**：`PI = 3.14` 之后再写 `PI = 5` 完全合法，不会报错。",
        ],
        "task": (
            "请定义三个变量：\n"
            "1. `city` —— 你所在的城市，字符串\n"
            "2. `year` —— 今年年份，整数\n"
            "3. `MAX_SCORE` —— 满分 100，用**全大写**表示这是约定不变的量\n\n"
            "最后用 `print` 把这三个值输出出来。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            '字符串要加引号：`city = "上海"`；整数不加引号：`year = 2026`；\n'
            "常量按约定全大写：`MAX_SCORE = 100`；\n"
            "输出：`print(city, year, MAX_SCORE)`。"
        ),
        "checker": VAR_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面哪一行是合法的变量赋值，并且最符合「常量」的命名约定？",
                "options": [
                    "MAX_TOKENS = 4096",
                    "max_tokens = 4096",
                    "4096 = MAX_TOKENS",
                    "max tokens = 4096",
                ],
                "answer_index": 0,
                "explanation": (
                    "全大写 `MAX_TOKENS` 是约定表示「这个值不该改」。B 语法合法但看不出是常量；"
                    "C 把值写在左边，语法直接报错；D 变量名里有空格，非法。"
                ),
            },
            {
                "type": "judge",
                "stem": "在 Python 里写了 `PI = 3.14` 之后，如果再写 `PI = 5`，程序会报错阻止你修改常量。",
                "answer": False,
                "explanation": "Python 没有真正的常量机制，全大写只是给人看的约定，改了不会报错。",
            },
            {
                "type": "blank",
                "stem": "补全下面这一行，让它输出 20（用 `___` 表示要填的部分）：\nage = 19\nage = age + ___",
                "answer": "1",
                "hint": "填一个数字",
                "explanation": "`age = age + 1` 会先取出 19 加 1 得到 20，再放回 age。",
            },
        ],
    },
    {
        "code": "py-type",
        "stage": "Python 基础",
        "title": "数据类型与类型转换",
        "summary": "数字和文字是两种东西，混用会报错",
        "definition": (
            "最常用的四种基础类型：\n\n"
            "- `int` 整数：`7`\n"
            "- `float` 小数：`9.9`\n"
            "- `str` 字符串（文字）：`\"7\"`，**引号是类型的一部分**\n"
            "- `bool` 布尔值：`True` / `False`（首字母大写）\n\n"
            "用 `type(x)` 查看类型，用 `int()`、`float()`、`str()` 在类型之间转换。"
        ),
        "plain": (
            "`7` 和 `\"7\"` 看起来差不多，其实是**两种完全不同的东西**：\n\n"
            "- `7` 是数字，能算：`7 + 1` 得到 `8`\n"
            "- `\"7\"` 是文字，只能拼：`\"7\" + \"1\"` 得到 `\"71\"`\n\n"
            "就像「3 个苹果」和「写着 3 的纸条」——前者能吃掉、能称重，后者只能读或者拼起来。\n\n"
            "所以 `\"7\" + 1` 会报 `TypeError`：Python 不知道该按加法还是拼接算，它不猜，直接报错。"
        ),
        "example": (
            "n = 7            # int\n"
            "price = 9.9      # float\n"
            'label = "7"      # str\n'
            "ok = True        # bool\n"
            "\n"
            "print(type(n), type(label))\n"
            'print(n + 1)              # 8     数字相加\n'
            'print(label + "1")        # 71    字符串拼接，不是加法\n'
            'print(n + int(label))     # 14    先转换再相加'
        ),
        "example_output": "<class 'int'> <class 'str'>\n8\n71\n14",
        "pitfalls": [
            '**`"7" + 1` 报 `TypeError`**：字符串和数字不能相加，先 `int("7")` 转换。',
            '**`input()` 拿到的永远是字符串**：哪怕输入 25 也得到 `"25"`，要算数必须先转换。',
            '**`int("3.5")` 会报错**：字符串里有小数点，得先 `float("3.5")` 再 `int()`。',
            "**`int()` 是截断不是四舍五入**：`int(3.9)` 得到 3。要四舍五入用 `round()`。",
            "**除法 `/` 结果一定是小数**：`6 / 3` 得到 `2.0`；只要整数部分用 `//`。",
        ],
        "task": (
            "题目已经给好了 `s = \"25\"`（注意它是**字符串**）。\n\n"
            "1. 把 `s` 转成整数存到 `num`\n"
            "2. 计算 `num * 4` 存到 `result`，并 `print` 出来"
        ),
        "setup": 's = "25"\n',
        "starter": "# s 已经给好了，直接用\n\n",
        "hint": "用 `int(...)` 把字符串变整数：`num = int(s)`；再 `result = num * 4`。",
        "checker": TYPE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "从接口拿到一个字符串 `\"3\"`，要把它当数字参与计算，正确做法是？",
                "options": ['int("3")', '"3" + 0', 'str("3")', 'float("3") + "1"'],
                "answer_index": 0,
                "explanation": (
                    "`int()` 把字符串转成整数。B 会报 TypeError；C 本来就已是字符串，转了没意义；"
                    "D 里 `float(\"3\")` 得到 3.0，但再和字符串相加又出错了。"
                ),
            },
            {
                "type": "judge",
                "stem": '执行 `print("7" + "1")` 会输出 8。',
                "answer": False,
                "explanation": '两个字符串相加是拼接，输出的是 "71"。',
            },
            {
                "type": "blank",
                "stem": "下面这段代码的结果是 `___`（填数字）：\nprint(10 / 4)",
                "answer": "2.5",
                "accept": ["2.5"],
                "hint": "注意 `/` 和 `//` 的区别",
                "explanation": "`/` 是普通除法，结果是小数 2.5；要整数部分得用 `//`。",
            },
        ],
    },
    {
        "code": "py-op",
        "stage": "Python 基础",
        "title": "运算符",
        "summary": "算数、比较，以及取余和整除",
        "definition": (
            "**算术**：`+` `-` `*` `/`（除）、`//`（整除）、`%`（取余）、`**`（乘方）。\n\n"
            "**比较**：`==` `!=` `>` `<` `>=` `<=`，结果是 `True` / `False`。\n\n"
            "**逻辑**：`and`（都真才真）、`or`（有一个真就真）、`not`（取反）。"
        ),
        "plain": (
            "`//` 和 `%` 用**分苹果**理解最清楚：17 个苹果分给 5 个人——\n"
            "- `17 // 5` = **3**，每人能拿几个（只要整数部分）\n"
            "- `17 % 5` = **2**，分完还剩几个（余数）\n\n"
            "比较运算的结果是 `True`/`False`，所以它常被当「开关」用——下一课的 `if` 就靠它决定走哪条路。"
        ),
        "example": (
            "print(7 + 2, 7 - 2, 7 * 2)\n"
            "print(7 / 2)      # 3.5  除法结果一定是小数\n"
            "print(7 // 2)     # 3    整除\n"
            "print(7 % 2)      # 1    余数\n"
            "print(2 ** 3)     # 8    2 的 3 次方\n"
            "print(7 > 2, 7 == 2, not (7 > 2))"
        ),
        "example_output": "9 5 14\n3.5\n3\n1\n8\nTrue False False",
        "pitfalls": [
            "**`=` 是赋值、`==` 是判断**：`if x = 1` 会语法报错。",
            "**优先级**：`2 + 3 * 4` 是 14 不是 20。拿不准就加括号。",
            "**浮点有精度问题**：`0.1 + 0.2 == 0.3` 是 `False`。要精确比较用 `round()` 或改用整数计算。",
            "**`and`/`or` 会短路**：`False and (1/0)` 不报错，因为右边根本不执行。",
            "**`//` 对负数是向下取整**：`-7 // 2` 得到 `-4`。",
        ],
        "task": (
            "题目已经给好了 `total = 17`（17 个苹果）、`people = 5`（5 个人）。\n\n"
            "1. 每人分到几个 → 存到 `each`\n"
            "2. 分完还剩几个 → 存到 `left`"
        ),
        "setup": "total = 17\npeople = 5\n",
        "starter": "# total 和 people 已经给好了\n\n",
        "hint": "每人分几个 → 整除 `each = total // people`；还剩几个 → 取余 `left = total % people`。",
        "checker": OP_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要判断一个整数 `n` 是不是偶数，最直接的写法是？",
                "options": ["n % 2 == 0", "n / 2 == 0", "n // 2 == 0", "n * 2 == 0"],
                "answer_index": 0,
                "explanation": "`%` 取余数，偶数除以 2 余 0。`/` 是普通除法得不到 0；`//` 是整除，也不能判断奇偶。",
            },
            {
                "type": "blank",
                "stem": "补全这一行，让它取出 `text` 字符串的最后一个字符：\nlast = text[___]",
                "answer": "-1",
                "hint": "也可以用 len(text)-1，但这里填更简洁的写法",
                "explanation": "负数下标从末尾数，`-1` 就是最后一个字符。",
            },
            {
                "type": "judge",
                "stem": "在 Python 里，`2 + 3 * 4` 的结果是 20。",
                "answer": False,
                "explanation": "乘除优先级高于加减，先算 `3 * 4 = 12`，再加 2，结果是 14。",
            },
        ],
    },
    {
        "code": "py-str",
        "stage": "Python 基础",
        "title": "字符串",
        "summary": "拼接、切片、常用方法，以及 f-string",
        "definition": (
            "字符串是**不可变**的字符序列：`s = \"Hello\"`。\n\n"
            "- 下标与切片：`s[0]` 是 `H`，`s[-1]` 是 `o`，`s[0:2]` 是 `He`（含头不含尾）\n"
            "- 常用方法：`.strip()` 去首尾空白、`.split()` 切分、`.replace()` 替换、"
            "`.upper()/.lower()` 大小写、`.startswith()/.endswith()`\n"
            "- **f-string**（最推荐）：`f\"你好，{name}\"`，花括号里可以直接写变量或表达式\n"
            "- `len(s)` 取长度；`\"a\" + \"b\"` 拼接；`\"-\" * 3` 得到 `\"---\"`"
        ),
        "plain": (
            "字符串像**一串珠子**，每颗珠子是一个字符，按编号（从 0 开始）取。\n\n"
            "「不可变」的意思是：你不能改其中某一颗珠子。`s[0] = \"h\"` 会报错，"
            "只能**生成一个新字符串**，例如 `s = \"h\" + s[1:]`。这一点在处理大模型返回的文本时很重要 —— "
            "每次拼接都在产生新对象。\n\n"
            "**f-string 是日常用得最多的**：\n"
            "```\nname = \"小明\"\nscore = 95\nprint(f\"{name} 考了 {score} 分\")\n```\n"
            "直接 `+` 拼接要小心：`\"分数：\" + 95` 会报 TypeError，因为数字不能和字符串相加，"
            "f-string 会自动帮你转成文字。"
        ),
        "example": (
            's = "  Hello AI Agent  "\n'
            "\n"
            "print(s.strip())            # 去掉首尾空格\n"
            "print(s.strip().split())    # 按空白切成列表\n"
            'print("-".join(["a", "b"]))  # a-b\n'
            "\n"
            'model = "glm-5.3"\n'
            "tokens = 128\n"
            'print(f"模型 {model} 生成了 {tokens} 个 token")   # f-string\n'
            "\n"
            "print(len(s), s[2:7])       # 长度、切片"
        ),
        "example_output": (
            "Hello AI Agent\n['Hello', 'AI', 'Agent']\na-b\n"
            "模型 glm-5.3 生成了 128 个 token\n16 Hello"
        ),
        "pitfalls": [
            "**字符串不可变**：`s[0] = \"x\"` 会报 TypeError，要改只能重新拼一个新字符串。",
            "**`split()` 和 `split(\",\")` 不一样**：不传参数按任意空白切（还会自动去掉连续空格）；传了参数就按那个字符切。",
            "**`replace()` 返回新字符串，不改原串**：`s.replace(\"a\", \"b\")` 必须赋值回去才有效。",
            "**切片含头不含尾**：`s[0:2]` 只有两个字符。**`s[:2]` 从头取 2 个，`s[-2:]` 取最后 2 个**，这两个写法很常用。",
            "**中文长度**：`len(\"你好\")` 是 2（按字符数），但 `\"你好\".encode()` 有 6 字节。算 token 预算时别搞混。",
        ],
        "task": (
            "题目已经给好了 `raw = \"  AI Agent  \"`（前后有空格）、`model = \"claude\"`、`version = 3`。\n\n"
            "1. 去掉 `raw` 首尾空格存到 `cleaned`\n"
            "2. 用空格把 `cleaned` 切开，结果存到 `parts`（应该是列表 `[\"AI\", \"Agent\"]`）\n"
            "3. 用 **f-string** 拼一句话存到 `msg`，要求里面同时出现 `model` 的值和 `version` 的值"
        ),
        "setup": 'raw = "  AI Agent  "\nmodel = "claude"\nversion = 3\n',
        "starter": "# raw / model / version 已经给好了\n\n",
        "hint": (
            "`cleaned = raw.strip()`\n"
            "`parts = cleaned.split()`\n"
            '`msg = f"模型 {model} 版本 {version}"` —— f-string 里用花括号放变量。'
        ),
        "checker": STR_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": '字符串 `s = "agent"`，那么 `s[-3:]` 的结果是？',
                "options": ["ent", "age", "gen", "nt"],
                "answer_index": 0,
                "explanation": "`s[-3:]` 表示「从倒数第 3 个取到最后」，即 `ent`。取最后 N 个字符就用这个写法。",
            },
            {
                "type": "judge",
                "stem": '执行 `s = "hello"` 之后再执行 `s.upper()`，`s` 的值会变成 `"HELLO"`。',
                "answer": False,
                "explanation": "字符串不可变，`upper()` 返回的是**新字符串**，原变量 `s` 没变，要赋值才生效。",
            },
            {
                "type": "blank",
                "stem": "补全这一行，把 `name` 和 `score` 拼成 `小明: 95`：\nprint(f\"{name}___ {score}\")",
                "answer": ":",
                "hint": "填一个标点符号",
                "explanation": "f-string 里花括号外的内容会原样输出，所以直接写冒号即可。",
            },
            {
                "type": "short",
                "stem": "调用大模型 API 拿到一段回复后，你发现开头和结尾有多余的空格和换行，想去掉并检查里面有没有关键词。你会用哪些字符串方法？说说思路。",
                "keywords": ["strip", "in", "lower", "去"],
                "reference": (
                    "先用 `text.strip()` 去掉首尾空白（包括换行）；再判断关键词可以用 `\"关键词\" in text`；"
                    "如果想忽略大小写，两边都先 `.lower()` 再比较。注意这些方法都返回新字符串，要赋值回去。"
                ),
                "explanation": "这类清理在处理模型输出时几乎每次都要做。",
            },
        ],
    },
    {
        "code": "py-if",
        "stage": "Python 基础",
        "title": "选择结构",
        "summary": "让程序学会分岔：if / elif / else",
        "definition": (
            "```python\nif 条件:\n    # 条件为 True 时执行\nelif 另一个条件:\n    # 上面不成立、且这个条件成立时执行\nelse:\n    # 上面都不成立时执行\n```\n\n"
            "`if` 后面是一个能得出 `True`/`False` 的表达式。Python 靠**缩进**区分「哪些代码属于这个分支」。"
        ),
        "plain": (
            "`if` 就是**分岔路口**。`elif` 是「否则如果」，`else` 是兜底。\n\n"
            "**缩进是语法，不是排版！** Python 不用花括号，靠行首空格决定「这几行属于同一个门」。约定 4 个空格。\n\n"
            "**判断顺序很重要**：从上往下挨个检查，**一旦命中就不再往下看**。"
            "所以判断分数要先写 `>= 90` 再写 `>= 60`——反过来的话，95 分会在 `>= 60` 那步就被拦下。"
        ),
        "example": (
            "score = 78\n"
            "\n"
            "if score >= 90:\n"
            '    print("优秀")\n'
            "elif score >= 60:\n"
            '    print("及格")\n'
            "else:\n"
            '    print("不及格")'
        ),
        "example_output": "及格",
        "pitfalls": [
            "**忘了冒号 `:`**：`if score >= 60` 后面必须跟 `:`。",
            "**缩进不统一**：一会儿 4 空格一会儿 Tab，会报 `IndentationError`。",
            "**判断顺序写反**：`if score >= 60` 写在前面，90 分也进不了「优秀」。",
            "**分支里暂时不写逻辑**：不能空着，用 `pass` 占位。",
        ],
        "task": (
            "题目已经给好了变量 `score`（0~100）。\n\n"
            "请写判断：90 分及以上输出 `优秀`；60 分及以上输出 `及格`；其余输出 `不及格`。\n\n"
            "输出用 `print`，**只要这三个词之一**。"
        ),
        "setup": "score = 73\n",
        "starter": "# score 已经给好了，写你的 if / elif / else\n\n",
        "hint": "从高往低判断：先 `if score >= 90`，再 `elif score >= 60`，最后 `else`。",
        "checker": None,
        "cases": [
            {"setup": "score = 73\n", "expect_stdout": "及格"},
            {"setup": "score = 95\n", "expect_stdout": "优秀"},
            {"setup": "score = 41\n", "expect_stdout": "不及格"},
            {"setup": "score = 90\n", "expect_stdout": "优秀"},
        ],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面这段代码会输出什么？\n```\nscore = 95\nif score >= 60:\n    print(\"及格\")\nelif score >= 90:\n    print(\"优秀\")\n```",
                "options": ["及格", "优秀", "及格 优秀", "什么都不输出"],
                "answer_index": 0,
                "explanation": "从上往下判断，95 >= 60 先成立，打印「及格」后就不再往下看了。所以高门槛的条件必须写在前面。",
            },
            {
                "type": "judge",
                "stem": "在 Python 里，`if x = 1:` 是合法的写法，表示「如果 x 等于 1」。",
                "answer": False,
                "explanation": "`=` 是赋值，判断相等要用 `==`。写成 `if x = 1:` 会直接语法报错。",
            },
            {
                "type": "applied",
                "stem": "写一段逻辑：判断一个 API 调用结果该走哪条路 —— 状态码是 200 就正常处理；401 提示「密钥无效」；"
                        "429 提示「触发限流，稍后重试」；其他情况提示「未知错误」。用文字描述你的 if/elif/else 结构。",
                "keywords": ["200", "401", "429", "elif", "else"],
                "reference": (
                    "```\nif status == 200:\n    正常处理\nelif status == 401:\n    print(\"密钥无效\")\n"
                    "elif status == 429:\n    print(\"触发限流，稍后重试\")\nelse:\n    print(\"未知错误\")\n```\n"
                    "要点：用 `==` 比较状态码；403/500 之类没单独列出的都落到 `else`。"
                ),
                "explanation": "这是 Agent 调用外部工具时最常见的分支判断。",
            },
        ],
    },
    {
        "code": "py-while",
        "stage": "Python 基础",
        "title": "while 循环",
        "summary": "只要条件成立，就反复做",
        "definition": (
            "```python\nwhile 条件:\n    # 条件为 True 就重复执行这里\n```\n\n"
            "**`break`** 立刻跳出整个循环；**`continue`** 跳过本轮剩下的语句，直接回到条件判断。"
        ),
        "plain": (
            "`while` 读作「只要……就一直做」。\n\n"
            "最常见的新手事故是**死循环**：条件一直为真，程序转个不停。"
            "关键是在循环体里做点事，让条件**逐渐趋近于假**：\n"
            "```\nn = 3\nwhile n > 0:\n    print(n)\n    n = n - 1     # 少了这行，n 永远是 3\n```\n\n"
            "在 Agent 里 `while` 的典型用法是「反复调用模型直到任务完成或达到最大步数」——"
            "**最大步数那个条件就是防止它无限转下去的保险**。"
        ),
        "example": (
            "n = 3\n"
            "while n > 0:\n"
            "    print(n)\n"
            "    n = n - 1\n"
            'print("发射！")\n'
            "\n"
            "# 用 break 提前退出（Agent 循环的常见写法）\n"
            "step = 0\n"
            "while True:\n"
            "    step = step + 1\n"
            "    if step >= 3:\n"
            "        break        # 达到最大步数就停\n"
            "print(step)"
        ),
        "example_output": "3\n2\n1\n发射！\n3",
        "pitfalls": [
            "**死循环**：忘了更新条件里的变量。沙箱有 5 秒超时保护，超时会强制停掉。",
            "**循环变量没初始化**：进 `while` 之前要先给初始值，否则 `NameError`。",
            "**`while True:` 里没有能执行的 break**：写了但被别的条件挡住，等于没有。",
            "**累加前要先准备 0**：想算总和得先 `total = 0`，否则 `NameError`。",
        ],
        "task": (
            "题目已经给好了变量 `n`。\n\n"
            "请用 **while 循环**计算 `1 + 2 + ... + n`，存到 `total` 并 `print(total)`。\n\n"
            "（会换一个 `n` 再测一次，别把答案写死。）"
        ),
        "setup": "n = 13\n",
        "starter": "# n 已经给好了\ntotal = 0\n# 用 while 把 1..n 累加到 total\n\n",
        "hint": "需要 `total` 存和、`i` 存当前加到几；别忘了每轮 `i = i + 1`，否则死循环。",
        "checker": None,
        "cases": [
            {"setup": "n = 13\n", "expect_stdout": "91"},
            {"setup": "n = 6\n", "expect_stdout": "21"},
        ],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面这段代码的问题是什么？\n```\ni = 0\nwhile i < 5:\n    print(i)\n```",
                "options": [
                    "死循环，因为 i 永远不会变",
                    "语法错误，while 后面少了 else",
                    "只会打印一次",
                    "没有任何问题",
                ],
                "answer_index": 0,
                "explanation": "循环体里没有改变 `i`，条件 `i < 5` 永远成立，会一直打印 0。必须补一行 `i = i + 1`。",
            },
            {
                "type": "judge",
                "stem": "`while True:` 配合 `break` 是一种常见写法，但必须保证有能真正执行到的 break 条件。",
                "answer": True,
                "explanation": "Agent 循环就是「while True 调用模型 → 判断是否该停 → break」，最大步数就是那个保险。",
            },
            {
                "type": "blank",
                "stem": "补全循环体，让循环能正常结束：\nn = 5\nwhile n > 0:\n    print(n)\n    n = n - ___",
                "answer": "1",
                "hint": "填一个数字",
                "explanation": "每轮让 n 减 1，最终会变成 0 使条件不成立，循环结束。",
            },
        ],
    },
    {
        "code": "py-for",
        "stage": "Python 基础",
        "title": "for 循环与 range",
        "summary": "把一串东西挨个过一遍",
        "definition": (
            "```python\nfor 变量 in 一串东西:\n    # 每取一个元素执行一次\n```\n\n"
            "`range(n)` 生成 `0, 1, ..., n-1`；`range(a, b)` 生成 `a ... b-1`；"
            "`range(a, b, step)` 按步长生成。\n\n"
            "`for` 可以直接遍历列表、字符串、字典：`for ch in \"abc\"`、`for k in d`、`for k, v in d.items()`。"
        ),
        "plain": (
            "`while` 是「只要……」，`for` 是「把这一串**挨个**过一遍」。"
            "需要「重复 N 次」或「遍历一批数据」时用 `for`，更安全（不容易写出死循环）。\n\n"
            "`range` 最容易踩的是**差一**：`range(5)` 给的是 `0 1 2 3 4`，**不含 5**。"
            "口诀：**含头不含尾**。想要 1 到 5 得写 `range(1, 6)`。\n\n"
            "在 Agent 里，`for` 最常用来「遍历一批文档做检索」或「逐个调用工具」。"
        ),
        "example": (
            "for i in range(3):\n"
            '    print("第", i + 1, "次")\n'
            "\n"
            "total = 0\n"
            "for x in range(1, 5):     # 1,2,3,4\n"
            "    total = total + x\n"
            "print(total)              # 10\n"
            "\n"
            "for y in range(0, 10, 2):  # 0,2,4,6,8\n"
            "    print(y)"
        ),
        "example_output": "第 1 次\n第 2 次\n第 3 次\n10\n0\n2\n4\n6\n8",
        "pitfalls": [
            "**差一错误**：`range(5)` 只到 4。要 1 到 5 得写 `range(1, 6)`。",
            "**累加变量要初始化在循环外面**：写在循环里每轮都会被清零。",
            "**不要在 for 里增删正在遍历的列表**：会漏掉元素，要改就先复制一份。",
            "**`for i in range(len(lst))` 不是好写法**：直接 `for x in lst` 更清晰；同时要下标时才用 `enumerate(lst)`。",
        ],
        "task": (
            "题目已经给好了变量 `n`。\n\n"
            "请用 **for + range** 计算 `1` 到 `n` 之间所有**偶数**的和，存到 `total` 并 `print(total)`。\n\n"
            "（会换一个 `n` 再测一次。）"
        ),
        "setup": "n = 20\n",
        "starter": "# n 已经给好了\ntotal = 0\n# 用 for 把 1..n 里的偶数累加到 total\n\n",
        "hint": "方法一：遍历 1..n，用 `if i % 2 == 0` 挑偶数。方法二：`for i in range(2, n + 1, 2)` 直接用步长 2。",
        "checker": None,
        "cases": [
            {"setup": "n = 20\n", "expect_stdout": "110"},
            {"setup": "n = 10\n", "expect_stdout": "30"},
        ],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`list(range(2, 11, 3))` 的结果是？",
                "options": ["[2, 5, 8]", "[2, 5, 8, 11]", "[3, 6, 9]", "[2, 4, 6, 8, 10]"],
                "answer_index": 0,
                "explanation": "从 2 开始、每次加 3、到 11 之前停：2、5、8（9+3=11 不包含）。含头不含尾。",
            },
            {
                "type": "judge",
                "stem": "要遍历一个列表里的每个元素，`for x in my_list:` 比 `for i in range(len(my_list)):` 更好。",
                "answer": True,
                "explanation": "直接遍历元素更清晰、不易出下标错误。需要下标时用 `enumerate(my_list)` 拿到索引和值。",
            },
            {
                "type": "blank",
                "stem": "补全这一行，让它循环 10 次（i 取 0 到 9）：\nfor i in range(___):",
                "answer": "10",
                "hint": "填一个数字",
                "explanation": "`range(10)` 生成 0~9 共 10 个数。",
            },
        ],
    },
    {
        "code": "py-list",
        "stage": "Python 基础",
        "title": "列表",
        "summary": "一排编了号的储物柜",
        "definition": (
            "列表用中括号：`scores = [88, 92, 79]`。\n\n"
            "- 下标**从 0 开始**：`scores[0]` 是 88；`scores[-1]` 是最后一个\n"
            "- `len(scores)` 取长度；`scores.append(x)` 末尾追加\n"
            "- 切片 `scores[0:2]` 取下标 0、1（**含头不含尾**）\n"
            "- 排序 `sorted(scores)` 返回新列表（原列表不变）；`scores.sort()` 原地排序\n"
            "- `x in scores` 判断是否存在；`sum()/max()/min()` 求和与最值"
        ),
        "plain": (
            "列表像**一排编了号的储物柜**，编号**从 0 开始**：\n"
            "```\nscores = [88, 92, 79]\n编号:      0   1   2\n```\n"
            "所以第一个柜子是 `scores[0]`，不是 `scores[1]`。\n\n"
            "负数编号从右边数，`scores[-1]` 是最右边那个——不用先算长度就能拿到最后一个。\n\n"
            "**列表是「可变」的**，这点和字符串不同：`scores.append(100)` 会真的改变这个列表。"
            "而 `b = a` 不会复制，只是给同一个列表又起了个名字，改 `b` 会连 `a` 一起改。"
        ),
        "example": (
            'fruits = ["苹果", "香蕉", "橘子"]\n'
            "\n"
            "print(fruits[0], fruits[-1], len(fruits))\n"
            'fruits.append("葡萄")\n'
            "print(fruits)\n"
            "print(fruits[1:3])         # ['香蕉', '橘子']\n"
            "\n"
            "nums = [3, 1, 4, 1, 5]\n"
            "print(sorted(nums))        # 排序后是新列表\n"
            "print(max(nums), sum(nums))"
        ),
        "example_output": (
            "苹果 橘子 3\n['苹果', '香蕉', '橘子', '葡萄']\n['香蕉', '橘子']\n"
            "[1, 1, 3, 4, 5]\n5 14"
        ),
        "pitfalls": [
            "**下标从 0 开始**：长度 3 的列表合法下标只有 0、1、2，写 `[3]` 报 `IndexError`。",
            "**切片含头不含尾**：`[0:2]` 只有两个元素。",
            "**`append()` 原地修改、返回 None**：写 `a = a.append(x)` 会让 `a` 变成 `None`。",
            "**`len()` 是函数不是方法**：写 `len(lst)`，不是 `lst.len()`。",
            "**`sorted()` 和 `.sort()` 不一样**：前者返回新列表（原列表不变），后者原地改并返回 `None`。",
            "**`b = a` 不是复制**：改 `b` 会连 `a` 一起变。要复制用 `b = a[:]` 或 `b = list(a)`。",
        ],
        "task": (
            "题目已经给好了列表 `scores`。\n\n"
            "请找出其中的**最高分**存到 `best`，然后 `print(best)`。\n\n"
            "（可以用 `max(scores)`，也可以自己用循环比较。会换一组数据再测。）"
        ),
        "setup": "scores = [88, 92, 79, 95, 67]\n",
        "starter": "# scores 已经给好了\n\n",
        "hint": "最简单：`best = max(scores)`。想练循环：先假设 `best = scores[0]`，再遍历比较更新。",
        "checker": None,
        "cases": [
            {"setup": "scores = [88, 92, 79, 95, 67]\n", "expect_stdout": "95"},
            {"setup": "scores = [10, 3, 44, 7]\n", "expect_stdout": "44"},
        ],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`nums = [10, 20, 30, 40]`，`nums[1:3]` 的结果是？",
                "options": ["[20, 30]", "[10, 20, 30]", "[20, 30, 40]", "[30, 40]"],
                "answer_index": 0,
                "explanation": "含头不含尾，取下标 1 和 2，也就是 20 和 30。",
            },
            {
                "type": "judge",
                "stem": "`a = [1, 2, 3]` 之后执行 `b = a`，再执行 `b.append(4)`，此时 `a` 也会变成 `[1, 2, 3, 4]`。",
                "answer": True,
                "explanation": "`b = a` 只是又起了一个名字，两者指向同一个列表。要独立副本得用 `b = a[:]` 或 `b = list(a)`。",
            },
            {
                "type": "blank",
                "stem": "补全这一行，把 `\"新元素\"` 追加到列表 `items` 末尾：\nitems.___(\"新元素\")",
                "answer": "append",
                "hint": "填一个方法名",
                "explanation": "`append()` 在末尾追加元素。注意它原地修改、返回 None。",
            },
            {
                "type": "short",
                "stem": "你要把一批文档片段（列表）按长度从长到短排序，然后取前 3 条做检索结果。用列表的哪些能力实现？说说思路。",
                "keywords": ["sorted", "key", "len", "reverse", "切片", "[:3]"],
                "reference": (
                    "`sorted(docs, key=len, reverse=True)[:3]`。要点：`key=len` 表示按长度排序，"
                    "`reverse=True` 是降序，切片 `[:3]` 取前三条。`sorted()` 不改原列表，比较安全。"
                ),
                "explanation": "这就是 RAG 里「按相关度/长度筛候选」的最小写法。",
            },
        ],
    },
    {
        "code": "py-tuple-set",
        "stage": "Python 基础",
        "title": "元组与集合",
        "summary": "一组不能改的数据，和一个自动去重的袋子",
        "definition": (
            "**元组 tuple**：用圆括号 `point = (3, 5)`，**创建后不能修改**。"
            "常用来表示「一条固定记录」，例如模型配置 `(\"glm-5.3\", 4096)`。\n\n"
            "**集合 set**：用花括号 `s = {1, 2, 3}`，特点是**自动去重**、**无序**。\n"
            "- 去重：`set([1, 2, 2, 3])` → `{1, 2, 3}`\n"
            "- 交并差：`a & b`、`a | b`、`a - b`\n"
            "- 判断是否包含极快：`x in s`\n\n"
            "两者都支持 `len()`、`in`、遍历。"
        ),
        "plain": (
            "**元组 = 写死的便利贴**：贴上就不能改。为什么用它？因为「不会被我意外改掉」本身就是一种安全，"
            "而且元组可以做字典的键（列表不行）。\n\n"
            "**集合 = 一个自动去重的袋子**：往里扔东西，重复的自动消失，但**里面没有顺序**，"
            "所以不能按下标取，`s[0]` 会报错。\n\n"
            "集合最实用的两个场景：\n"
            "1. **去重**：`set(list_of_tags)` 一步搞定\n"
            "2. **快速判断「在不在里面」**：数据量大时，`x in set` 比 `x in list` 快得多"
            "（列表要一个个找，集合是哈希直接命中）"
        ),
        "example": (
            "point = (3, 5)\n"
            "print(point[0], len(point))\n"
            "model_cfg = (\"glm-5.3\", 4096)     # 不可改的配置\n"
            "\n"
            "tags = [\"rag\", \"agent\", \"rag\", \"llm\"]\n"
            "unique = set(tags)\n"
            "print(unique)                 # 去重，顺序不保证\n"
            "print(len(unique))\n"
            "\n"
            "a = {1, 2, 3}\n"
            "b = {2, 3, 4}\n"
            "print(a & b, a | b, a - b)     # 交、并、差"
        ),
        "example_output": "3 2\n{'rag', 'agent', 'llm'}\n3\n{2, 3} {1, 2, 3, 4} {1}",
        "pitfalls": [
            "**元组不可改**：`point[0] = 9` 会报 `TypeError`。需要能改就用列表。",
            "**单元素元组要加逗号**：`(5)` 是数字 5，`(5,)` 才是元组。这个坑很隐蔽。",
            "**集合无序**：`s[0]` 报错，集合不能按下标取。要顺序就先 `sorted(s)` 或 `list(s)`。",
            "**`{}` 是空字典不是空集合**：空集合要写 `set()`。",
            "**集合里的元素必须可哈希**：列表不能放进集合，元组可以。",
        ],
        "task": (
            "题目已经给好了 `nums = [3, 1, 2, 3, 1]`。\n\n"
            "1. 用 `set(...)` 去掉重复，结果存到 `unique`\n"
            "2. 定义一个元组 `point`，值为 `(3, 5)`"
        ),
        "setup": "nums = [3, 1, 2, 3, 1]\n",
        "starter": "# nums 已经给好了\n\n",
        "hint": "`unique = set(nums)`；元组用圆括号：`point = (3, 5)`。",
        "checker": SET_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要把一个「用户标签」列表里的重复项去掉，最简单的写法是？",
                "options": ["set(tags)", "tags.unique()", "tags[::-1]", "sorted(tags)"],
                "answer_index": 0,
                "explanation": "`set(tags)` 一步去重。排序不会去重；列表也没有 `unique()` 方法。",
            },
            {
                "type": "judge",
                "stem": "`s = {1, 2, 3}` 之后可以用 `s[0]` 取出第一个元素。",
                "answer": False,
                "explanation": "集合是无序的，不支持按下标取值，会报 TypeError。需要顺序就先 `sorted(s)`。",
            },
            {
                "type": "blank",
                "stem": "补全这一行，得到一个「只含一个元素 5」的元组：\nt = (5___)",
                "answer": ",",
                "hint": "填一个标点",
                "explanation": "`(5)` 只是加了括号的数字 5；必须写成 `(5,)` 才是元组。",
            },
            {
                "type": "short",
                "stem": "在 Agent 里你有一批「已处理过的文档 id」，需要频繁判断某个 id 是否处理过。用列表还是集合存更合适？为什么？",
                "keywords": ["集合", "set", "快", "哈希", "去重"],
                "reference": (
                    "用**集合**。判断「在不在里面」时集合基于哈希，平均是 O(1)，列表要逐个扫描是 O(n)。"
                    "另外集合天然去重，不用担心重复加入。如果还需要保持顺序，可以集合判断 + 列表存顺序。"
                ),
                "explanation": "这是很实在的性能选择：数据量一大，list 的 in 会明显变慢。",
            },
        ],
    },
    {
        "code": "py-dict",
        "stage": "Python 基础",
        "title": "字典",
        "summary": "用名字取值，Agent 里到处都在用",
        "definition": (
            "字典用花括号存**键值对**：`info = {\"model\": \"glm-5.3\", \"tokens\": 128}`。\n\n"
            "- 取值：`info[\"model\"]`；取不到会报 `KeyError`\n"
            "- **安全取值**：`info.get(\"temp\", 0.7)` —— 键不存在时返回默认值\n"
            "- 赋值/新增：`info[\"top_p\"] = 0.9`\n"
            "- 遍历：`for k in info`（键）、`for k, v in info.items()`（键值对）\n"
            "- `in` 判断键是否存在；`len()` 取数量"
        ),
        "plain": (
            "列表靠**位置**找东西（第 0 个），字典靠**名字**找东西（叫 model 的那个）。"
            "名字比位置好记也好维护，所以配置、接口返回的 JSON，在 Python 里都是字典。\n\n"
            "**大模型返回的结构化数据就是字典**，例如：\n"
            "```\n{\"name\": \"get_weather\", \"arguments\": {\"city\": \"北京\"}}\n```\n"
            "你要取城市名就得写 `data[\"arguments\"][\"city\"]`。\n\n"
            "**`get()` 是最该养成的习惯**：直接用 `d[\"key\"]` 一旦键不存在就整个程序崩掉；"
            "`d.get(\"key\")` 拿到 `None`，`d.get(\"key\", 默认值)` 拿到默认值，程序能继续跑。"
            "在处理「模型可能少给字段」的返回时，这一点尤其重要。"
        ),
        "example": (
            "info = {\"model\": \"glm-5.3\", \"tokens\": 128}\n"
            "\n"
            "print(info[\"model\"])\n"
            'print(info.get("temperature", 0.7))    # 键不存在，用默认值\n'
            'info["tools"] = 2                      # 新增键\n'
            "print(info)\n"
            "\n"
            "for k, v in info.items():\n"
            "    print(k, \"=\", v)\n"
            "\n"
            'print("model" in info)'
        ),
        "example_output": (
            "glm-5.3\n0.7\n{'model': 'glm-5.3', 'tokens': 128, 'tools': 2}\n"
            "model = glm-5.3\ntokens = 128\ntools = 2\nTrue"
        ),
        "pitfalls": [
            "**`d[\"不存在的键\"]` 会直接崩**：不确定键在不在就用 `.get()`。",
            "**`.get()` 的默认值只在键不存在时生效**：如果键存在但值是 `None`，返回的还是 `None`。",
            "**字典的键必须可哈希**：字符串、数字、元组可以；列表不行。",
            "**遍历时不能增删键**：会报 `RuntimeError`，要改就先 `list(d.items())` 复制一份。",
            "**键是唯一的**：重复赋值会覆盖旧值，不会报错——写错键名时很难发现。",
        ],
        "task": (
            "题目已经给好了 `words = [\"a\", \"b\", \"a\", \"c\", \"a\"]`（注意 a 出现了 3 次）。\n\n"
            "1. 统计每个单词出现次数，存到字典 `counts`\n"
            "2. 定义一个字典 `info`，包含：`\"model\"` 是字符串 `\"glm-5.3\"`、`\"tools\"` 是数字 `2`"
        ),
        "setup": 'words = ["a", "b", "a", "c", "a"]\n',
        "starter": "counts = {}\n# 遍历 words，统计每个词出现几次\n\n",
        "hint": (
            "统计词频的固定套路：\n"
            "```\nfor w in words:\n    counts[w] = counts.get(w, 0) + 1\n```\n"
            "`get(w, 0)` 表示「没有这个键就当 0」，再 +1 存回去。"
        ),
        "checker": DICT_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "大模型返回的 JSON 解析后是字典 `data`，但 `temperature` 字段**可能不存在**。要安全地取它（不存在就用 0.7），应该写？",
                "options": [
                    'data.get("temperature", 0.7)',
                    'data["temperature"]',
                    'data.find("temperature")',
                    'data.get("temperature") or 0.7',
                ],
                "answer_index": 0,
                "explanation": (
                    "`get(键, 默认值)` 是标准做法。B 在缺字段时直接抛 KeyError；"
                    "C 字典没有 find；D 用 `or` 有个坑——如果取到的值是 0（合法值）也会被替换成 0.7。"
                ),
            },
            {
                "type": "judge",
                "stem": "字典的键可以重复，后写的会覆盖前面的，且不会报错。",
                "answer": True,
                "explanation": "键唯一，重复赋值是覆盖而非报错——也正因为不报错，写错键名时不容易察觉。",
            },
            {
                "type": "blank",
                "stem": "补全这一行，遍历字典 `cfg` 并同时拿到键和值：\nfor k, v in cfg.___():",
                "answer": "items",
                "hint": "填一个方法名",
                "explanation": "`items()` 返回 (键, 值) 对，配合 `for k, v in ...` 解包最常用。",
            },
            {
                "type": "applied",
                "stem": "工具调用返回的是 `{\"name\": \"search\", \"arguments\": {\"query\": \"RAG\", \"top_k\": 3}}`。"
                        "请写出取出 query 和 top_k 的代码，并要求 top_k 缺失时默认用 5。",
                "keywords": ["arguments", "get", "query", "top_k"],
                "reference": (
                    "```\nargs = data[\"arguments\"]\nquery = args[\"query\"]\ntop_k = args.get(\"top_k\", 5)\n```\n"
                    "要点：先定位到 `arguments` 这层；`query` 是必需参数可以直接取；"
                    "`top_k` 是可选参数要用 `.get(..., 5)` 兜默认值。"
                ),
                "explanation": "这就是解析 Function Calling 参数的日常写法。",
            },
        ],
    },
    {
        "code": "py-func",
        "stage": "Python 基础",
        "title": "函数",
        "summary": "把一段逻辑装进盒子，起个名字反复用",
        "definition": (
            "```python\ndef 函数名(参数1, 参数2):\n    # 逻辑\n    return 结果\n```\n\n"
            "用 `def` 定义，用 `函数名(值)` 调用。**`return` 把结果交回给调用者**；"
            "没写 `return` 的函数返回 `None`。\n\n"
            "参数可以有默认值：`def chat(prompt, temperature=0.7)`，调用时 `temperature` 可省。"
        ),
        "plain": (
            "函数就是**给一段逻辑起个名字**，以后用名字就能使唤它。\n\n"
            "- **参数**是入口：`def add(a, b)` 里的 `a`、`b` 是占位符，调用时 `add(3, 5)` 才把真实值传进去\n"
            "- **返回值**是出口：`return a + b` 把结果交给外面\n\n"
            "⚠️ **`print` 和 `return` 完全是两回事**：\n"
            "- `print` 只是显示在屏幕上，外面**拿不到**这个值\n"
            "- `return` 才是把结果交给调用者，可以被赋值、被继续计算\n\n"
            "判断标准很简单：**这个函数的结果别人还要用吗？**要用就 `return`。"
            "在 Agent 开发里，工具函数必须 `return`（比如返回查询结果字符串），"
            "因为要把结果再喂回给模型。"
        ),
        "example": (
            "def add(a, b):\n"
            "    return a + b          # 把结果交给外面\n"
            "\n"
            "def greet(name):\n"
            '    print("你好，" + name)  # 只显示，没有返回值\n'
            "\n"
            "print(add(3, 5))      # 8\n"
            "total = add(1, 2)     # 返回值可以存起来\n"
            "print(total * 10)     # 30\n"
            "\n"
            'def chat(prompt, temperature=0.7):   # 默认参数\n'
            '    return f"{prompt} @ {temperature}"\n'
            "\n"
            'print(chat("你好"))            # 用默认值\n'
            'print(chat("你好", 0.2))       # 覆盖默认值'
        ),
        "example_output": "8\n30\n你好，小明\nNone\n你好 @ 0.7\n你好 @ 0.2",
        "pitfalls": [
            "**`print` 当 `return` 用**：函数里只 `print` 不 `return`，外面拿到的是 `None`。",
            "**定义了却没调用**：只写 `def area(...)` 不会执行任何东西。",
            "**`return` 后面的代码不会执行**：`return` 会立刻结束函数。",
            "**默认参数别用可变对象**：`def f(x=[])` 是经典坑，多次调用会共用同一个列表；要写 `def f(x=None)` 再在函数里处理。",
            "**函数必须先定义后调用**：调用写在 `def` 之前会报 `NameError`。",
        ],
        "task": (
            "请写一个函数 `area(width, height)`，**返回**矩形面积。\n\n"
            "然后用它计算长 4、宽 5 的面积，存到 `result` 并 `print(result)`。\n\n"
            "（判定会换别的长宽再调用一次你的函数，所以要真的在函数里算。）"
        ),
        "setup": "",
        "starter": "def area(width, height):\n    # 这里要 return 面积\n    pass\n\nresult = 0  # 用 area(4, 5) 的结果替换掉\n",
        "hint": "```\ndef area(width, height):\n    return width * height\n\nresult = area(4, 5)\n```",
        "checker": FUNC_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面这个函数被调用后，`x` 的值是？\n```\ndef f(n):\n    print(n * 2)\n\nx = f(5)\n```",
                "options": ["None", "10", "5", "报错"],
                "answer_index": 0,
                "explanation": "函数里只有 `print` 没有 `return`，所以返回值是 `None`。屏幕上会打印 10，但 `x` 拿到的是 `None`。",
            },
            {
                "type": "judge",
                "stem": "工具函数（会被 Agent 调用的函数）应该用 `print` 输出结果，这样模型才能拿到。",
                "answer": False,
                "explanation": "必须用 `return`。Agent 拿到的是函数返回值，`print` 只是打到屏幕上，程序拿不到。",
            },
            {
                "type": "blank",
                "stem": "补全函数，让它返回两数之和：\ndef add(a, b):\n    ___ a + b",
                "answer": "return",
                "hint": "填一个关键字",
                "explanation": "`return` 把计算结果交给调用者。",
            },
            {
                "type": "short",
                "stem": "为什么说 Agent 的工具函数必须用 `return` 而不是 `print`？说说你的理解。",
                "keywords": ["返回值", "return", "模型", "拿不到", "print"],
                "reference": (
                    "Agent 的流程是「模型决定调工具 → 程序执行 → 把**结果**回传给模型 → 模型继续推理」。"
                    "这个回传靠的是函数返回值。`print` 只把内容打到控制台，程序里拿不到，"
                    "模型自然也就看不到工具的执行结果，整个循环就断了。"
                ),
                "explanation": "这是 Agent 开发里最基础也最容易搞错的一点。",
            },
        ],
    },
]
