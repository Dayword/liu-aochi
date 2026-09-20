"""阶段二：Python 进阶（把代码写得更像样）。

这一阶段开始出现「暂时无法在沙箱里手写代码」的知识点（例如文件读写要用到
被沙箱屏蔽的 os/pathlib），这类知识点就以习题为主，照样能考到位。
"""

COMPREHENSION_CHECKER = """
try:
    assert squares == [1, 4, 9, 16, 25], "squares 应该是 1..5 的平方，用列表推导式一行写出来"
    assert evens == [2, 4, 6, 8], "evens 应该是 1..8 里的偶数，用推导式加 if 筛选"
    assert name_len == {"a": 1, "bb": 2}, "name_len 应该是字典推导式：名字 -> 长度"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

ARGS_CHECKER = """
try:
    assert add_all(1, 2, 3) == 6, "*args 版求和要能吃任意多个参数"
    assert add_all() == 0, "一个参数都不传时应该返回 0"
    assert make_config(model="a") == {"model": "a", "temperature": 0.7}, "默认 temperature 应该是 0.7"
    assert make_config(model="a", temperature=0.2)["temperature"] == 0.2, "传了 temperature 要能覆盖默认值"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

EXC_CHECKER = """
try:
    assert parse_tokens("128") == 128, "正常情况应该返回整数"
    assert parse_tokens("abc") == 0, "转换失败要返回 0，而不是让程序崩掉"
    assert parse_tokens(None) == 0, "传 None 也要返回 0"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

CLASS_CHECKER = """
try:
    m = Model("glm-5.3")
    assert m.name == "glm-5.3", "构造时要把 name 存下来"
    assert m.total_tokens == 0, "total_tokens 初始应该是 0"
    m.add_tokens(100)
    m.add_tokens(50)
    assert m.total_tokens == 150, "add_tokens 要累加"
    assert m.describe() == "glm-5.3: 150 tokens", "describe 要返回拼好的字符串"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except AttributeError as e:
    print("__FAIL__ 类里缺少属性或方法：" + str(e))
"""

GEN_CHECKER = """
try:
    assert list(fib(5)) == [0, 1, 1, 2, 3], "fib(5) 前 5 项应该是 0 1 1 2 3"
    assert list(fib(1)) == [0], "fib(1) 只有一项"
    assert list(fib(8)) == [0, 1, 1, 2, 3, 5, 8, 13], "fib(8) 要能连续产出 8 项，说明真的用了 yield"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

DECO_CHECKER = """
try:
    r = slow_add(1, 2)
    assert r == 3, "被装饰后函数结果不能变"
    assert calls == 1, "装饰器要记录调用次数"
    slow_add(3, 4)
    assert calls == 2, "再调用一次，计数应该变成 2"
    assert getattr(slow_add, "__name__") == "slow_add", "要用 functools.wraps 保留原函数名"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

MODULE_CHECKER = """
try:
    assert isinstance(theta, float), "theta 应该是小数（float）"
    assert abs(theta - 3.14159) < 0.001, "theta 应该约等于 pi / 1.0，用 math 里的常数算"
    assert isinstance(picked, str) and len(picked) == 1, "picked 应该是从选项里随机取的一个字符串"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

LESSONS: list[dict] = [
    {
        "code": "py-comprehension",
        "stage": "Python 进阶",
        "title": "推导式",
        "summary": "一行生成列表/字典，Agent 里到处在用",
        "definition": (
            "**列表推导式**：`[表达式 for 变量 in 可迭代对象 if 条件]`\n"
            "例：`[x * x for x in range(1, 6)]` → `[1, 4, 9, 16, 25]`\n\n"
            "**字典推导式**：`{键表达式: 值表达式 for ...}`\n"
            "例：`{name: len(name) for name in names}`\n\n"
            "**集合推导式**：`{x for x in ...}`（自动去重）\n\n"
            "还有**生成器表达式**：把方括号换成圆括号 `(x for x in ...)`，它不一次性建列表，更省内存。"
        ),
        "plain": (
            "推导式是「**把循环和追加合并成一行**」。\n\n"
            "老写法要三行：\n"
            "```\nsquares = []\nfor x in range(1, 6):\n    squares.append(x * x)\n```\n"
            "推导式一行：`squares = [x * x for x in range(1, 6)]`\n\n"
            "读的时候倒过来读更顺：**「对于 range(1,6) 里的每个 x，取 x*x，组成一个列表」**。\n\n"
            "在 Agent 里最常见的用法是**从一堆结构化结果里抽出某个字段**：\n"
            "```\ntitles = [doc[\"title\"] for doc in results]\n"
            "texts = [item[\"text\"] for item in chunks if len(item[\"text\"]) > 50]\n```\n"
            "注意：**推导式适合简单逻辑**。如果里面要塞 if-else 又要调好几个函数，"
            "还是老老实实写循环更易读——可读性比「一行搞定」重要。"
        ),
        "example": (
            "squares = [x * x for x in range(1, 6)]\n"
            "print(squares)\n"
            "\n"
            "evens = [x for x in range(1, 9) if x % 2 == 0]   # 带筛选\n"
            "print(evens)\n"
            "\n"
            "names = [\"a\", \"bb\", \"ccc\"]\n"
            "name_len = {n: len(n) for n in names}            # 字典推导式\n"
            "print(name_len)\n"
            "\n"
            "docs = [{\"title\": \"RAG 入门\"}, {\"title\": \"Agent 实战\"}]\n"
            "titles = [d[\"title\"] for d in docs]             # 抽字段\n"
            "print(titles)"
        ),
        "example_output": (
            "[1, 4, 9, 16, 25]\n[2, 4, 6, 8]\n{'a': 1, 'bb': 2, 'ccc': 3}\n['RAG 入门', 'Agent 实战']"
        ),
        "pitfalls": [
            "**别把复杂逻辑塞进推导式**：两层以上嵌套就该拆成普通循环，不然没人读得懂。",
            "**圆括号是生成器不是元组**：`(x for x in ...)` 不会马上算，要 `list()` 才看得到内容。",
            "**推导式里的变量会泄漏到外层**（Python 3 里其实不会，但普通 for 循环会），别依赖这个行为。",
            "**字典推导式要写冒号**：`{k: v for ...}`，只写 `{k for ...}` 得到的是集合。",
        ],
        "task": (
            "题目已经给好了 `nums = [1, 2, 3, 4, 5, 6, 7, 8]`、`names = [\"a\", \"bb\"]`。\n\n"
            "用**推导式**完成：\n"
            "1. `squares` —— 1 到 5 的平方（`[1, 4, 9, 16, 25]`）\n"
            "2. `evens` —— `nums` 里的偶数\n"
            "3. `name_len` —— 字典：名字 → 长度"
        ),
        "setup": 'nums = [1, 2, 3, 4, 5, 6, 7, 8]\nnames = ["a", "bb"]\n',
        "starter": "# 用推导式写，不要用 for 循环三行展开\n\n",
        "hint": (
            "`squares = [x * x for x in range(1, 6)]`\n"
            "`evens = [x for x in nums if x % 2 == 0]`\n"
            "`name_len = {n: len(n) for n in names}`"
        ),
        "checker": COMPREHENSION_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要从 `results = [{\"title\": \"A\"}, {\"title\": \"B\"}]` 里取出所有 title 组成列表，最简洁的写法是？",
                "options": [
                    '[r["title"] for r in results]',
                    'results["title"]',
                    '[r.title for r in results]',
                    'for r in results: r["title"]',
                ],
                "answer_index": 0,
                "explanation": "列表推导式。B 对列表用字符串键会报错；C 字典要用 `[\"title\"]` 取值，`.title` 是属性访问；D 只是循环，没有收集结果。",
            },
            {
                "type": "judge",
                "stem": "生成器表达式 `(x * 2 for x in range(3))` 会立刻生成一个列表 `[0, 2, 4]`。",
                "answer": False,
                "explanation": "圆括号是生成器表达式，惰性求值，不会立刻建列表；要看到内容得 `list(...)`，好处是省内存。",
            },
            {
                "type": "blank",
                "stem": "补全字典推导式，生成「单词 → 长度」：\nword_len = {w: ___(w) for w in words}",
                "answer": "len",
                "hint": "填一个内置函数名",
                "explanation": "`len(w)` 取字符串长度。",
            },
        ],
    },
    {
        "code": "py-func-adv",
        "stage": "Python 进阶",
        "title": "函数进阶：*args、**kwargs 与默认值",
        "summary": "写出能被灵活调用的函数，也是工具函数的基础",
        "definition": (
            "**默认参数**：`def chat(prompt, temperature=0.7)` —— 调用时可省略。\n\n"
            "**`*args`**：把多出来的位置参数收成一个元组。`def add_all(*args)` 可以 `add_all(1, 2, 3)`。\n\n"
            "**`**kwargs`**：把多出来的关键字参数收成一个字典。`def f(**kwargs)` 可以 `f(a=1, b=2)`。\n\n"
            "调用时反过来用也可以：`add_all(*my_list)`、`f(**my_dict)` 是**解包**。"
        ),
        "plain": (
            "`*args` / `**kwargs` 解决的是「**参数个数不确定**」的问题。\n\n"
            "在 Agent 开发里它们特别常见，因为**工具的参数是模型动态给的**：\n"
            "```\ndef call_tool(name, **kwargs):\n    print(name, kwargs)\n\ncall_tool(\"search\", query=\"RAG\", top_k=3)\n# kwargs = {'query': 'RAG', 'top_k': 3}\n```\n"
            "封装大模型客户端时也经常写成 `def chat(messages, **options)`，"
            "这样 temperature、max_tokens 这些都能透传，而不用每加一个参数就改函数签名。\n\n"
            "⚠️ **一个必须记住的坑**：默认值**只在函数定义时算一次**，所以**永远不要用可变对象做默认值**：\n"
            "```\ndef bad(x, items=[]):     # 错！所有调用共用同一个列表\n    items.append(x)\n    return items\n\ndef good(x, items=None):  # 对\n    if items is None:\n        items = []\n    items.append(x)\n    return items\n```"
        ),
        "example": (
            "def add_all(*args):\n"
            "    return sum(args)\n"
            "\n"
            "print(add_all(1, 2, 3))        # 6\n"
            "print(add_all())               # 0\n"
            "\n"
            "def make_config(**kwargs):\n"
            "    cfg = {\"model\": \"glm-5.3\", \"temperature\": 0.7}\n"
            "    cfg.update(kwargs)\n"
            "    return cfg\n"
            "\n"
            "print(make_config(temperature=0.2))\n"
            "print(make_config(model=\"x\", top_p=0.9))"
        ),
        "example_output": "6\n0\n{'model': 'glm-5.3', 'temperature': 0.2}\n{'model': 'x', 'temperature': 0.7, 'top_p': 0.9}",
        "pitfalls": [
            "**默认值不能用可变对象**：`def f(x=[])` 会让所有调用共用同一个列表，这是最经典的坑。",
            "**参数顺序**：位置参数 → 默认参数 → `*args` → `**kwargs`，写反了语法报错。",
            "**`*args` 拿到的是元组，`**kwargs` 拿到的是字典**。",
            "**`*` 和 `**` 在定义和调用时含义不同**：定义时是「收集」，调用时是「解包」。",
        ],
        "task": (
            "请实现两个函数：\n"
            "1. `add_all(*args)` —— 返回所有参数的和（不传参数时返回 0）\n"
            "2. `make_config(**kwargs)` —— 返回一个字典，默认包含 `model` 和 `temperature`，"
            "并把传入的关键字参数合并进去"
        ),
        "setup": "",
        "starter": "def add_all(*args):\n    pass\n\ndef make_config(**kwargs):\n    pass\n",
        "hint": (
            "`add_all` 里可以直接 `return sum(args)`。\n"
            "`make_config` 里先写默认字典，再 `cfg.update(kwargs)`，最后 `return cfg`。"
        ),
        "checker": ARGS_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面这个函数连续调用两次，`f()` 和 `f()` 的结果分别是？\n```\ndef f(x=[]):\n    x.append(1)\n    return x\n```",
                "options": ["[1] 和 [1]", "[1] 和 [1, 1]", "[1] 和 []", "都会报错"],
                "answer_index": 1,
                "explanation": "默认值在定义时只算一次，两次调用共用同一个列表，所以第二次变成 [1, 1]。正确写法是用 `x=None` 再在函数内新建列表。",
            },
            {
                "type": "judge",
                "stem": "封装大模型客户端时写 `def chat(messages, **options)`，可以把 temperature、max_tokens 等参数透传下去，以后加参数不用改函数签名。",
                "answer": True,
                "explanation": "这是 `**kwargs` 最实用的场景之一：让上层调用保持稳定，底层选项灵活扩展。",
            },
            {
                "type": "blank",
                "stem": "补全函数定义，让它能接收任意多个关键字参数：\ndef build(___):",
                "answer": "**kwargs",
                "accept": ["**kwargs", " **kwargs"],
                "hint": "填参数写法",
                "explanation": "`**kwargs` 把所有关键字参数收成一个字典。",
            },
        ],
    },
    {
        "code": "py-exception",
        "stage": "Python 进阶",
        "title": "异常处理",
        "summary": "出错时别让整个程序崩掉，Agent 里必须做",
        "definition": (
            "```python\ntry:\n    # 可能出错的代码\nexcept ValueError as e:\n    # 出错时怎么办\nelse:\n    # 没出错时执行（可选）\nfinally:\n    # 无论如何都执行（可选）\n```\n\n"
            "`raise` 主动抛出异常；`raise ValueError(\"说明\")` 可以带上原因。"
        ),
        "plain": (
            "异常处理就是**提前想好「万一失败怎么办」**。\n\n"
            "在 Agent 应用里这不是可选项，而是**必须项**，因为外部依赖到处都可能失败：\n"
            "- 模型 API 超时、限流、返回 500\n"
            "- 模型返回的 JSON 格式不对，`json.loads` 直接抛异常\n"
            "- 工具函数里访问不到数据源\n\n"
            "如果没有 try，**一处失败整个请求就 500 了**。稳妥的写法是这样：\n"
            "```python\ntry:\n    data = json.loads(text)\nexcept json.JSONDecodeError:\n    data = {}      # 兜底，流程继续\n```\n\n"
            "⚠️ **别写 `except: pass`**。它会把所有错误（包括你自己拼错变量名这种 bug）一起吞掉，"
            "出了问题完全无从查起。至少要 `except Exception as e: ` 并**记录日志**。"
        ),
        "example": (
            "def to_int(text):\n"
            "    try:\n"
            "        return int(text)\n"
            "    except (ValueError, TypeError) as e:\n"
            "        print(f\"转换失败：{e}\")\n"
            "        return 0\n"
            "\n"
            'print(to_int("128"))\n'
            'print(to_int("abc"))\n'
            "print(to_int(None))\n"
            "\n"
            "# finally 无论成败都会执行，适合收尾\n"
            "try:\n"
            "    print(\"调用接口\")\n"
            "finally:\n"
            "    print(\"记录日志\")"
        ),
        "example_output": "128\n转换失败：invalid literal for int() with base 10: 'abc'\n0\n转换失败：int() argument must be a string...\n0\n调用接口\n记录日志",
        "pitfalls": [
            "**`except: pass` 是大坑**：连自己的拼写错误一起吞掉，问题极难定位。至少要记录日志。",
            "**`except` 要写具体类型**：`ValueError` 比裸 `except` 精确，能避免误捕。",
            "**`finally` 一定会执行**，哪怕 `try` 里 `return` 了。适合关连接、写日志。",
            "**别用异常做正常流程控制**：能用 `if` 判断的就别指望 try。",
            "**捕获了要处理**：捕获后什么都不做（或只 print）在生产环境等于埋雷。",
        ],
        "task": (
            "请实现 `parse_tokens(text)`：\n"
            "- 正常情况（如 `\"128\"`）返回整数 128\n"
            "- 转换失败（如 `\"abc\"`、`None`）返回 0，**不能让程序崩掉**"
        ),
        "setup": "",
        "starter": "def parse_tokens(text):\n    # 用 try/except 包住转换\n    pass\n",
        "hint": (
            "```\ndef parse_tokens(text):\n    try:\n        return int(text)\n"
            "    except (ValueError, TypeError):\n        return 0\n```\n"
            "注意要同时接住 `TypeError`（传 None 时是它），而不是只接 ValueError。"
        ),
        "checker": EXC_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "模型返回的文本要 json 解析，但格式可能不对。下面哪种写法最稳妥？",
                "options": [
                    "try 里 json.loads，except 里返回空字典并记日志",
                    "直接 json.loads，出错就让程序崩",
                    "except: pass",
                    "用 if 判断文本长度再解析",
                ],
                "answer_index": 0,
                "explanation": "捕获具体异常并给出兜底值 + 日志。B 会让整个请求挂掉；C 会连其他 bug 一起吞掉；D 判断长度和 JSON 是否合法没关系。",
            },
            {
                "type": "judge",
                "stem": "`try` 块里写了 `return`，`finally` 块就不会执行了。",
                "answer": False,
                "explanation": "`finally` 一定会执行，即使 try 里 return 或抛异常。这正是它适合做收尾（关连接、写日志）的原因。",
            },
            {
                "type": "applied",
                "stem": "你的 Agent 要调用一个外部工具，可能遇到：网络超时、返回 429 限流、返回的 JSON 解析失败。"
                        "请描述你会怎么组织异常处理，让整个流程不崩、还能给模型一个可用的错误信息。",
                "keywords": ["try", "except", "超时", "429", "重试", "日志", "返回"],
                "reference": (
                    "分层处理：\n"
                    "1. 网络层：`try ... except httpx.TimeoutException` → 记录后重试（带退避），超过次数返回「超时」文案\n"
                    "2. 状态码：`if resp.status_code == 429` → 等待后重试\n"
                    "3. 解析层：`try: data = resp.json() except json.JSONDecodeError: data = {}`\n"
                    "4. 统一收口：所有异常都转成**字符串结果返回给模型**（而不是抛出中断循环），"
                    "因为模型看到「工具执行失败：超时」还能换个方式继续；同时写日志便于排查。"
                ),
                "explanation": "关键点是：**异常要变成模型能读懂的文本返回**，而不是让循环崩掉。",
            },
        ],
    },
    {
        "code": "py-class",
        "stage": "Python 进阶",
        "title": "类与对象",
        "summary": "把数据和行为打包在一起",
        "definition": (
            "```python\nclass Model:\n    def __init__(self, name):      # 构造方法\n        self.name = name           # 实例属性\n\n    def describe(self):            # 实例方法，第一个参数固定是 self\n        return self.name\n\nm = Model(\"glm-5.3\")   # 创建实例\nprint(m.describe())\n```\n\n"
            "`self` 代表「这个实例本身」，用来读写自己的属性、调用自己的方法。"
            "`__init__` 在创建对象时自动执行。"
        ),
        "plain": (
            "类是**模板**，对象是按模板做出来的**具体东西**。"
            "`class Model` 是模板，`Model(\"glm-5.3\")` 才是具体的一个实例。\n\n"
            "为什么需要类？因为**「数据」和「操作这些数据的函数」应该放在一起**。\n"
            "不用类的话，你就得这样：\n"
            "```python\nsession = {\"history\": [], \"tokens\": 0}\nsession_tokens_add(session, 100)\n```\n"
            "用类变成：\n"
            "```python\nsession = Session()\nsession.add(100)\n```\n"
            "后者不容易搞错，也更好扩展——所以在 Agent 里，"
            "「会话」「工具」「模型客户端」通常都写成类。"
        ),
        "example": (
            "class Session:\n"
            "    def __init__(self, user):\n"
            "        self.user = user\n"
            "        self.history = []          # 每个实例各自一份\n"
            "\n"
            "    def add(self, message):\n"
            "        self.history.append(message)\n"
            "\n"
            "    def describe(self):\n"
            "        return f\"{self.user}: {len(self.history)} 条消息\"\n"
            "\n"
            "s1 = Session(\"小明\")\n"
            "s2 = Session(\"小红\")\n"
            "s1.add(\"你好\")\n"
            "print(s1.describe())     # 小明: 1 条消息\n"
            "print(s2.describe())     # 小红: 0 条消息  —— 互相不影响"
        ),
        "example_output": "小明: 1 条消息\n小红: 0 条消息",
        "pitfalls": [
            "**`__init__` 前后都是两个下划线**：写成 `_init_` 不会报错，但永远不会被自动调用。",
            "**方法第一个参数必须是 `self`**：漏了会报「takes 0 positional arguments but 1 was given」。",
            "**实例属性要在 `__init__` 里初始化**：否则不同实例可能行为不一致。",
            "**类属性 vs 实例属性**：写在 `class` 里（不在 `__init__`）的是类属性，所有实例共享，容易被误改。",
            "**可变类属性是坑**：`history = []` 写在类里，所有实例会共用同一个列表。要放 `__init__` 里。",
        ],
        "task": (
            "请写一个类 `Model`：\n"
            "- `__init__(self, name)` 存下名字，并把 `total_tokens` 初始化为 0\n"
            "- `add_tokens(self, n)` 把 n 累加到 `total_tokens`\n"
            "- `describe(self)` 返回字符串，格式为 `名字: N tokens`（如 `glm-5.3: 150 tokens`）"
        ),
        "setup": "",
        "starter": "class Model:\n    def __init__(self, name):\n        # 初始化 name 和 total_tokens\n        pass\n\n    def add_tokens(self, n):\n        pass\n\n    def describe(self):\n        pass\n",
        "hint": (
            "`self.name = name`、`self.total_tokens = 0`；\n"
            "`self.total_tokens = self.total_tokens + n`；\n"
            "`return f\"{self.name}: {self.total_tokens} tokens\"`"
        ),
        "checker": CLASS_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面哪种写法定义的实例属性，能让每个对象各自独立、互不影响？",
                "options": [
                    "在 __init__ 里写 self.history = []",
                    "在 class 下面直接写 history = []",
                    "在方法外面写 history = []",
                    "在 describe 方法里写 self.history = []",
                ],
                "answer_index": 0,
                "explanation": "放 `__init__` 里才能每个实例一份。写在 class 下是类属性，所有实例共享——这是很隐蔽的 bug 来源。",
            },
            {
                "type": "judge",
                "stem": "类的方法第一个参数必须是 `self`（名字可以改，但约定叫 self）。",
                "answer": True,
                "explanation": "`self` 指向调用该方法的实例，Python 会自动传进去，你不需要手动传。",
            },
            {
                "type": "blank",
                "stem": "补全构造方法的参数：\nclass A:\n    def __init_____:\n        self.x = x",
                "answer": "(self, x)",
                "accept": ["(self, x)", "(self,x)"],
                "hint": "把 self 和 x 都写上",
                "explanation": "实例方法第一个参数是 self，后面才是真正的参数。",
            },
        ],
    },
    {
        "code": "py-generator",
        "stage": "Python 进阶",
        "title": "生成器与迭代器",
        "summary": "边算边给，不占内存——处理大模型流式输出就靠它",
        "definition": (
            "函数里出现 **`yield`** 就变成**生成器函数**：调用它不会立刻执行，"
            "而是返回一个生成器对象，**每次 `next()` 才往下走到下一个 yield**。\n\n"
            "生成器是**惰性**的：数据是用的时候才算、拿到就扔，所以处理大数据时极省内存。"
            "配合 `for` 遍历：`for item in gen(): ...`\n\n"
            "`yield` 和 `return` 的区别：`return` 一次给完并结束函数；`yield` 可以给很多次，"
            "每次都会「暂停」在那里，下次从这里继续。"
        ),
        "plain": (
            "**普通函数像打包好一整箱水再给你**：`def get_all(): return [1,2,3,...]` 数据全都占了内存。\n\n"
            "**生成器像接了根水管**：要多少流多少，`yield` 就是「吐出当前这个，先暂停」。\n\n"
            "这对大模型应用特别重要，因为**流式输出本来就是「边生成边给」**：\n"
            "```\nfor chunk in stream_response():\n    print(chunk, end=\"\", flush=True)   # 逐字/逐块吐出来\n```\n"
            "后端把这个 `for` 里的内容一段段推给前端（SSE），用户就能看到字在往外冒，"
            "而不用等整段答案生成完。\n\n"
            "另一个用途是**读大文件**：一行行 yield，而不是一次 `read()` 全部读进内存。"
        ),
        "example": (
            "def countdown(n):\n"
            "    while n > 0:\n"
            "        yield n          # 吐出当前值，暂停在这里\n"
            "        n = n - 1\n"
            "\n"
            "for x in countdown(3):\n"
            "    print(x)\n"
            "\n"
            "g = countdown(2)\n"
            "print(type(g))\n"
            "print(next(g))           # 2\n"
            "print(next(g))           # 1\n"
            "\n"
            "# 斐波那契：无限序列，但生成器不会撑爆内存\n"
            "def fib():\n"
            "    a, b = 0, 1\n"
            "    while True:\n"
            "        yield a\n"
            "        a, b = b, a + b\n"
            "\n"
            "f = fib()\n"
            "print([next(f) for _ in range(6)])"
        ),
        "example_output": "3\n2\n1\n<class 'generator'>\n2\n1\n[0, 1, 1, 2, 3, 5]",
        "pitfalls": [
            "**生成器只能遍历一次**：走完就空了，要重来必须重新调用生成器函数。",
            "**调用生成器函数不会执行任何代码**：只有开始取值（for / next）才真正跑。",
            "**`list(gen)` 会把它耗尽**，之后再用就是空的。",
            "**生成器里不能 `return 值`**（只能 `return` 表示结束），要返回值用普通函数。",
            "**`yield` 写在函数里，整个函数性质就变了**：哪怕还有 `return` 也一样，调用它拿到的是生成器不是结果。",
        ],
        "task": (
            "请用生成器实现 `fib(n)`：依次产出斐波那契数列的前 n 项（从 0 开始）。\n\n"
            "要求：`list(fib(5))` 得到 `[0, 1, 1, 2, 3]`；`fib(0)` 或 `fib(1)` 也能正常工作。"
        ),
        "setup": "",
        "starter": "def fib(n):\n    # 用 yield 产出前 n 项\n    pass\n",
        "hint": (
            "```\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b\n```"
        ),
        "checker": GEN_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "为什么流式输出（模型边生成边返回）特别适合用生成器实现？",
                "options": [
                    "因为生成器可以边产生边交付，不必等全部生成完，也不用把结果全存内存",
                    "因为生成器比普通函数运行更快",
                    "因为生成器可以并发执行",
                    "因为生成器能自动重试",
                ],
                "answer_index": 0,
                "explanation": "生成器是惰性的：每 yield 一块就能立刻推给前端，用户马上看到内容；同时不必把整段答案堆在内存里。",
            },
            {
                "type": "judge",
                "stem": "一个生成器对象可以被完整遍历两次，第二次还会拿到同样的数据。",
                "answer": False,
                "explanation": "生成器是「一次性」的，遍历完就耗尽了。要再遍历一次必须重新调用生成器函数得到新对象。",
            },
            {
                "type": "blank",
                "stem": "补全这个函数，让它变成生成器：\ndef nums():\n    for i in range(3):\n        ___ i",
                "answer": "yield",
                "hint": "填一个关键字",
                "explanation": "`yield` 让函数变成生成器，每产出一次就暂停。",
            },
        ],
    },
    {
        "code": "py-decorator",
        "stage": "Python 进阶",
        "title": "装饰器",
        "summary": "在不改原函数的前提下，给它加点额外能力",
        "definition": (
            "装饰器是一个**接收函数、返回新函数**的函数，用 `@名字` 放在函数定义上方。\n\n"
            "```python\nimport functools\n\ndef log_calls(func):\n    @functools.wraps(func)          # 保留原函数的名字和文档\n    def wrapper(*args, **kwargs):\n        print(f\"调用 {func.__name__}\")\n        return func(*args, **kwargs)  # 别忘了返回原函数的结果\n    return wrapper\n\n@log_calls\ndef add(a, b):\n    return a + b\n```\n\n"
            "`@log_calls` 等价于 `add = log_calls(add)`。"
        ),
        "plain": (
            "装饰器就是**给函数套一层外壳**，让它多干点事（记日志、计时、重试、鉴权），"
            "而**函数本身的代码一行都不用改**。\n\n"
            "为什么要用？想想 Agent 里这个需求：「每个工具被调用时都要记录参数和耗时」。"
            "不用装饰器就得在每个工具函数里复制粘贴一遍日志代码；"
            "用装饰器只在上面加一行 `@log_calls`。\n\n"
            "理解它的关键是**函数也是普通对象**，可以当参数传、可以当返回值。"
            "`log_calls(add)` 接收 add 这个函数，返回一个新的 wrapper 函数，"
            "以后调用 `add(1,2)` 其实调用的是 wrapper。\n\n"
            "⚠️ 记住 `functools.wraps`：不加它，被装饰后函数的名字会变成 `wrapper`，"
            "调试和文档都会很难看。"
        ),
        "example": (
            "import functools\n"
            "\n"
            "calls = 0\n"
            "\n"
            "def count_calls(func):\n"
            "    @functools.wraps(func)\n"
            "    def wrapper(*args, **kwargs):\n"
            "        global calls\n"
            "        calls = calls + 1\n"
            "        return func(*args, **kwargs)\n"
            "    return wrapper\n"
            "\n"
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "add = count_calls(add)     # 等价于在函数上写 @count_calls\n"
            "print(add(1, 2))\n"
            "print(add(3, 4))\n"
            "print(calls)"
        ),
        "example_output": "3\n7\n2",
        "pitfalls": [
            "**忘了 `return func(...)`**：wrapper 里不返回原函数结果，调用方拿到的是 `None`。",
            "**忘了 `*args, **kwargs`**：wrapper 只写 `()` 的话，被装饰的函数就不能带参数了。",
            "**忘了 `functools.wraps`**：函数名会变成 `wrapper`，排错时很痛苦。",
            "**顺序有讲究**：多个装饰器从下往上套，`@a` 在 `@b` 上面时实际是 `a(b(func))`。",
        ],
        "task": (
            "题目已经给好了 `calls = 0`。\n\n"
            "请写一个装饰器 `count_calls`，要求：\n"
            "- 每次调用被装饰的函数，就把全局变量 `calls` 加 1\n"
            "- 保留原函数的返回值\n"
            "- 用 `@functools.wraps` 保留原函数名\n\n"
            "然后用它装饰给定的 `slow_add`。"
        ),
        "setup": "calls = 0\n\ndef slow_add(a, b):\n    return a + b\n",
        "starter": "import functools\n\n# 写装饰器，然后用 @count_calls 装饰 slow_add\n",
        "hint": (
            "```\ndef count_calls(func):\n    @functools.wraps(func)\n    def wrapper(*args, **kwargs):\n"
            "        global calls\n        calls = calls + 1\n        return func(*args, **kwargs)\n"
            "    return wrapper\n\n@count_calls\ndef slow_add(a, b):\n    return a + b\n```"
        ),
        "checker": DECO_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`@log_calls` 写在 `def add(a, b)` 上方，等价于下面哪一句？",
                "options": ["add = log_calls(add)", "log_calls(add)", "add = add(log_calls)", "log_calls = add"],
                "answer_index": 0,
                "explanation": "装饰器语法糖就是「把函数传进去，用返回值替换原名字」。",
            },
            {
                "type": "judge",
                "stem": "装饰器里如果不写 `functools.wraps`，被装饰函数的名字会变成 wrapper，排查问题时容易困惑。",
                "answer": True,
                "explanation": "`@functools.wraps(func)` 会把原函数的 `__name__`、文档等复制到 wrapper 上。",
            },
            {
                "type": "applied",
                "stem": "你要给 Agent 的每个工具函数加「自动重试 3 次、并记录每次调用耗时」的能力。"
                        "说说用装饰器怎么设计，以及为什么不把这段代码写进每个工具函数里。",
                "keywords": ["装饰器", "重试", "functools.wraps", "复用", "统一"],
                "reference": (
                    "写一个装饰器 `@retry(times=3)`（可以再叠一个 `@timed` 计耗时）：内部用 `for` 循环包住"
                    "原函数调用、捕获异常后重试，用 `time.perf_counter()` 计算耗时并写日志，"
                    "最后 `return func(*args, **kwargs)`，并加 `functools.wraps` 保留原函数名。\n\n"
                    "不把这段代码写进每个工具函数里的原因：① 重试和计时的逻辑是**统一**的，"
                    "复制到十几个工具里就是重复代码，改一处要改十几处；② 容易漏；"
                    "③ 业务逻辑和可靠性逻辑混在一起可读性差。装饰器让这段能力**复用**，"
                    "加一个新工具只要多写一行注解。"
                ),
                "explanation": "这是工程上「横切关注点」的典型处理方式。",
            },
        ],
    },
    {
        "code": "py-module",
        "stage": "Python 进阶",
        "title": "模块、包与虚拟环境",
        "summary": "用别人写好的库，也管好自己项目的依赖",
        "definition": (
            "**模块**：一个 `.py` 文件就是一个模块，用 `import 模块名` 引入。\n"
            "```python\nimport math\nprint(math.pi)\n\nfrom math import sqrt     # 只引入某个名字\nprint(sqrt(16))\n```\n\n"
            "**包**：一个含 `__init__.py` 的文件夹，里面可以有多个模块。\n\n"
            "**虚拟环境**：给每个项目独立的依赖目录，避免版本互相打架。\n"
            "```bash\npython -m venv .venv          # 创建\nsource .venv/bin/activate     # 激活（Windows 是 .venv\\Scripts\\activate）\npip install httpx             # 装依赖\npip freeze > requirements.txt # 记录依赖\n```"
        ),
        "plain": (
            "**模块 = 别人写好的工具箱**。你不必自己实现开方和随机数，`import math` / `import random` 就行。"
            "Python 自带一大堆标准库（`json`、`math`、`random`、`datetime`、`asyncio`…），"
            "这些都是「不用装就能用」的。\n\n"
            "**虚拟环境为什么必须有**？因为 A 项目要 `httpx==0.27`、B 项目要 `0.28`，"
            "装在全局就会互相覆盖。虚拟环境相当于**给每个项目一个独立的抽屉**。\n\n"
            "在 Agent 开发里，你装的第三方库通常有：`httpx`（调 API）、`pydantic`（数据校验）、"
            "`fastapi`（做服务）、`numpy`（向量计算）。**`requirements.txt` 一定要提交到 git**，"
            "别人（和服务器）才能复现你的环境。"
        ),
        "example": (
            "import math\n"
            "import random\n"
            "\n"
            "print(math.pi)\n"
            "print(math.sqrt(16))\n"
            "print(math.floor(3.7))\n"
            "\n"
            "random.seed(42)                     # 固定随机种子，结果可复现\n"
            "print(random.choice([\"a\", \"b\", \"c\"]))\n"
            "print(random.randint(1, 6))\n"
            "\n"
            "from datetime import datetime\n"
            "print(datetime.now().year)"
        ),
        "example_output": "3.141592653589793\n4.0\n3\nc\n2\n2026",
        "pitfalls": [
            "**`import` 要放在文件顶部**（约定），不要写在函数中间。",
            "**别用 `from math import *`**：会污染命名空间，还可能覆盖你已有的变量名。",
            "**模块名不要和标准库重名**：自己的文件叫 `json.py` 会导致 `import json` 引入你自己的文件，报错很难懂。",
            "**忘记录依赖**：本地跑得好好的，部署就 ImportError。养成 `pip freeze > requirements.txt` 的习惯。",
            "**`random` 默认每次都不一样**，要可复现就先 `random.seed(42)`。",
        ],
        "task": (
            "题目已经给好了 `options = [\"a\", \"b\", \"c\"]`。\n\n"
            "1. 用 `math` 模块算出 `pi / 1.0`（也就是 π），存到 `theta`\n"
            "2. 用 `random` 从 `options` 里随机挑一个，存到 `picked`"
        ),
        "setup": 'options = ["a", "b", "c"]\n',
        "starter": "# 记得先 import\n\n",
        "hint": "`import math` 后用 `math.pi`；`import random` 后用 `random.choice(options)`。",
        "checker": MODULE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "为什么建议每个项目都用独立的虚拟环境？",
                "options": [
                    "避免不同项目的依赖版本互相冲突，并让依赖可复现",
                    "让 Python 运行得更快",
                    "虚拟环境能自动修复 bug",
                    "不建虚拟环境就无法 import 任何库",
                ],
                "answer_index": 0,
                "explanation": "虚拟环境隔离依赖版本，配合 requirements.txt 让别人/服务器能装出和你一样的环境。",
            },
            {
                "type": "judge",
                "stem": "把项目的 `requirements.txt` 提交到 git 仓库是推荐做法。",
                "answer": True,
                "explanation": "它记录了确切的依赖清单，是部署和协作的基础。注意别把 `.env`（含密钥）提交上去。",
            },
            {
                "type": "blank",
                "stem": "补全命令，把当前环境装的依赖导出到文件：\npip freeze > ___",
                "answer": "requirements.txt",
                "hint": "填文件名",
                "explanation": "`requirements.txt` 是 Python 项目记录依赖的约定文件名。",
            },
        ],
    },
    {
        "code": "py-file",
        "stage": "Python 进阶",
        "title": "文件读写与路径",
        "summary": "把数据存到磁盘、从磁盘读回来（本节以习题为主）",
        "definition": (
            "```python\n# 写\nwith open(\"data.txt\", \"w\", encoding=\"utf-8\") as f:\n    f.write(\"hello\")\n\n# 读\nwith open(\"data.txt\", \"r\", encoding=\"utf-8\") as f:\n    text = f.read()\n```\n\n"
            "`with` 会自动关闭文件（即使中途出错）。模式：`r` 读、`w` 覆盖写、`a` 追加、`rb/wb` 二进制。\n\n"
            "路径推荐用 `pathlib`：`from pathlib import Path` → `p = Path(\"data\") / \"a.txt\"`，"
            "`p.exists()`、`p.read_text(encoding=\"utf-8\")`。"
        ),
        "plain": (
            "**`encoding=\"utf-8\"` 一定要写**。Windows 上默认编码不是 UTF-8，"
            "不写的话中文很容易变成乱码或者直接 `UnicodeDecodeError`——"
            "这是新手最难查的 bug 之一。\n\n"
            "**为什么用 `with`**？因为手写 `f = open(...)` 后忘了 `f.close()`，"
            "文件会一直被占用、内容可能没真正写进磁盘。`with` 无论正常结束还是抛异常都会帮你关掉。\n\n"
            "**路径拼接不要用字符串相加**（`\"data\" + \"/\" + \"a.txt\"`），"
            "因为 Windows 和 Linux 的分隔符不一样。用 `pathlib` 的 `/` 运算，跨平台都对。\n\n"
            "在 Agent 项目里，文件读写的常见用途是：加载 prompt 模板、"
            "读知识库原文、把对话日志落盘。"
        ),
        "example": (
            "from pathlib import Path\n"
            "\n"
            "p = Path(\"prompt.txt\")\n"
            "p.write_text(\"你是一个助手\", encoding=\"utf-8\")\n"
            "print(p.read_text(encoding=\"utf-8\"))\n"
            "print(p.exists())\n"
            "\n"
            "# 按行读：适合大文件，一行行处理不占内存\n"
            "Path(\"lines.txt\").write_text(\"第一行\\n第二行\\n\", encoding=\"utf-8\")\n"
            "for line in Path(\"lines.txt\").read_text(encoding=\"utf-8\").splitlines():\n"
            "    print(line)"
        ),
        "example_output": "你是一个助手\nTrue\n第一行\n第二行",
        "pitfalls": [
            "**忘记 `encoding=\"utf-8\"`**：中文在 Windows 上会乱码或报 `UnicodeDecodeError`。",
            "**忘记 `with`**：文件句柄不释放，写入可能没落盘。",
            "**`\"w\"` 会清空原文件**：想追加要用 `\"a\"`，否则数据直接没了。",
            "**路径字符串拼接不跨平台**：用 `pathlib.Path` 而不是 `\"a\" + \"/\" + \"b\"`。",
            "**读大文件别 `read()` 一把梭**：会全部读进内存，应该逐行迭代。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "checker": None,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "读取一个含中文的文本文件，下面哪种写法最不容易出问题？",
                "options": [
                    'with open("a.txt", encoding="utf-8") as f: text = f.read()',
                    'with open("a.txt") as f: text = f.read()',
                    'f = open("a.txt"); text = f.read()',
                    'text = open("a.txt").readlines()',
                ],
                "answer_index": 0,
                "explanation": "显式指定 UTF-8 + 用 with 自动关闭。B 在 Windows 上可能因默认编码不同而乱码；C 不会自动关闭文件；D 没指定编码，问题和 B 一样。",
            },
            {
                "type": "choice",
                "stem": "向已有文件追加内容（保留原内容），应该用哪种模式打开？",
                "options": ['"a"', '"w"', '"r"', '"x"'],
                "answer_index": 0,
                "explanation": "`\"a\"` 是追加；`\"w\"` 会清空原文件——这是很危险的操作，务必确认。",
            },
            {
                "type": "judge",
                "stem": "`with open(...) as f:` 即使代码块里抛出了异常，文件也会被正确关闭。",
                "answer": True,
                "explanation": "这正是 with 的价值：无论正常结束还是异常退出都会释放资源。",
            },
            {
                "type": "blank",
                "stem": "补全路径拼接（用 pathlib 的跨平台写法）：\nfrom pathlib import Path\np = Path(\"data\") ___ \"a.txt\"",
                "answer": "/",
                "hint": "填一个运算符",
                "explanation": "`Path / \"名字\"` 是 pathlib 重载的运算符，跨平台自动用正确的分隔符。",
            },
        ],
    },
]
