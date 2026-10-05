r"""Python 进阶补强：正则 / 标准库 / 上下文管理器 / 并发（4 节补充课）。

这批课补的是「会写基础 Python，但一遇到文本处理、现成轮子、资源清理、并发就卡壳」的缺口：
- 正则表达式：文本的查找、提取、替换、校验一次性解决
- 常用标准库：collections / itertools / functools，别自己造轮子
- 上下文管理器与 with：保证离开代码块时一定收尾
- 并发：线程 / 进程 / concurrent.futures 的取舍

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）

supplementary=True 表示这是「补充课」：不参与引导式学习的主线解锁链条
（见 app/seed/learn.py::next_code 与 routers/learn.py::_statuses）。
"""

STARTER = "# 在下面写出你的代码（删掉这行注释也没关系）\n"

REGEX_CHECKER = r"""
try:
    assert is_valid_id("A123") is True, "is_valid_id('A123') 应该是 True：大写 A 加 3 位数字，用 re.fullmatch 校验整串"
    assert is_valid_id("A12") is False, "is_valid_id('A12') 应该是 False：只有 2 位数字，位数不够"
    assert is_valid_id("a123") is False, "is_valid_id('a123') 应该是 False：题目要求大写 A，小写要判不通过"
    assert is_valid_id("A1234") is False, "is_valid_id('A1234') 应该是 False：多一位也不行，fullmatch 要求整串匹配"

    emails = extract_emails("联系 a@b.com 或 hello.world@test.org，谢谢")
    assert isinstance(emails, list), "extract_emails 要用 re.findall，返回一个列表"
    assert emails == ["a@b.com", "hello.world@test.org"], "extract_emails 要按出现顺序取出两个邮箱"

    assert mask_phone("13800000000") == "138****0000", "mask_phone 要把中间 4 位换成 ****，得到 138****0000"
    assert mask_phone("打给 13900000001 吧") == "打给 139****0001 吧", "手机号夹在文字中间时，也要只替换中间 4 位"

    s = "这里没有手机号"
    assert mask_phone(s) == s, "文本里没有手机号时应该原样返回，不要改动"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

STDLIB_CHECKER = r"""
try:
    top = top_words(["a", "b", "a", "c", "a", "b"], 2)
    assert top == [("a", 3), ("b", 2)], "top_words 应该返回出现最多的前 2 个 (词, 次数)：这里 a 出现 3 次、b 出现 2 次"

    assert top_words([], 3) == [], "空列表时 top_words 应该返回空列表"

    grouped = group_by_first_letter(["Apple", "banana", "avocado", "Cherry"])
    assert grouped == {"a": ["Apple", "avocado"], "b": ["banana"], "c": ["Cherry"]}, "group_by_first_letter 要按首字母小写分组，值保持原单词和出现顺序"
    assert isinstance(grouped, dict) and type(grouped) is dict, "要返回普通 dict：用 dict(...) 把 defaultdict 转回来"

    assert flat_all([[1, 2], [3], []]) == [1, 2, 3], "flat_all 要把嵌套列表拍平成一维，空子列表自动跳过"
    assert flat_all([]) == [], "空输入拍平后还是空列表"

    assert fib(30) == 832040, "fib(30) 应该等于 832040，注意用递归 + lru_cache"
    assert hasattr(fib, "cache_info"), "fib 必须用 @functools.lru_cache 装饰，否则没有 cache_info（缓存信息）"
    assert fib.cache_info().hits > 0, "缓存没生效：用 lru_cache 装饰后，重复子问题才会命中缓存"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

CONTEXT_CHECKER = r"""
try:
    with Timer() as t:
        pass
    assert isinstance(t, Timer), "Timer 的 __enter__ 应该返回 self，这样 as t 才能拿到计时器对象"
    assert isinstance(t.elapsed, float), "t.elapsed 应该是浮点秒数：用 time.perf_counter() 前后相减"
    assert t.elapsed >= 0, "t.elapsed 是耗时，不应该小于 0"

    raised = False
    try:
        with Timer() as t2:
            raise RuntimeError("boom")
    except RuntimeError:
        raised = True
    assert raised, "Timer 的 __exit__ 不能吞异常：块里抛出的异常要照常往上冒"

    swallowed = True
    try:
        with ignore_error():
            raise ValueError("要被吞掉")
    except ValueError:
        swallowed = False
    assert swallowed, "ignore_error 应该把块内的 ValueError 吞掉（不往外抛）"

    key_raised = False
    try:
        with ignore_error():
            raise KeyError("必须往外抛")
    except KeyError:
        key_raised = True
    assert key_raised, "ignore_error 只能吞 ValueError，其他异常（比如 KeyError）要照常抛出"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

CONCURRENCY_CHECKER = r"""
import threading
import time as _time

try:
    lock = threading.Lock()
    state = {"active": 0, "peak": 0, "names": set()}

    def fetch(url):
        with lock:
            state["active"] += 1
            if state["active"] > state["peak"]:
                state["peak"] = state["active"]
            state["names"].add(threading.current_thread().name)
        _time.sleep(0.05)
        with lock:
            state["active"] -= 1
        return "R:" + url

    result = fetch_all(["u1", "u2", "u3", "u4"], fetch)
    assert result == ["R:u1", "R:u2", "R:u3", "R:u4"], "fetch_all 的结果必须按输入顺序排列，即使各任务完成顺序不同"
    assert state["peak"] >= 2, "没检测到并发：同一时刻进入 fetch 的峰值线程数只有 1，说明是串行执行的，要用线程池"
    assert len(state["names"]) > 1, "看起来只用了 1 个线程：ThreadPoolExecutor 应该开多个工作线程"
    assert fetch_all([], fetch) == [], "空输入时 fetch_all 应该返回空列表"

    def slow_fetch(url):
        _time.sleep(0.2 if url == "slow" else 0.01)
        return url

    first = fetch_first_done(["slow", "fast"], slow_fetch)
    assert first == "fast", "fetch_first_done 应该返回最先完成的结果：slow 睡了更久，应返回 fast"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

LESSONS: list[dict] = [
    {
        "code": "py-regex",
        "stage": "Python 进阶补强",
        "title": "正则表达式",
        "summary": "用一套模式串，一次搞定查找、提取与替换",
        "supplementary": True,
        "definition": r"""正则表达式（regex）是一套用**字符串描述文本模式**的语法，Python 用 `re` 模块来使用它。

四个主力函数，分工一定要分清：

- `re.search(pat, s)` —— 在 `s` 里找**第一个**匹配，返回 `Match` 对象；找不到返回 `None`。
- `re.findall(pat, s)` —— 找出**所有**匹配，直接返回**字符串列表**（模式里带分组时返回分组内容的列表）。
- `re.sub(pat, repl, s)` —— 把所有匹配替换成 `repl`，返回替换后的新字符串。
- `re.fullmatch(pat, s)` —— **整串**必须从头到尾匹配，返回 `Match` 或 `None`；**做格式校验就用它**。

**原始字符串** `r"\d"`：写正则一定要加 `r` 前缀。因为 `"\d"` 里的 `\d` 会先被 Python 当成普通字符串转义处理一遍
（`\` 可能被吞掉或变成别的字符），加上 `r` 之后 Python 不再转义，正则引擎拿到的才是原样的 `\d`。

常用元字符：

- `\d` 数字、`\w` 单词字符（字母/数字/下划线）、`\s` 空白、`.` 任意一个字符（默认不含换行）
- 量词：`*` 0 次或多次、`+` 1 次或多次、`?` 0 次或 1 次、`{n}` 恰好 n 次、`{n,m}` n 到 m 次
- `^` 字符串开头、`$` 字符串结尾
- 字符集：`[abc]` 里面任意一个字符、`[^abc]` 取反、`[3-9]` 范围
- 分组 `(...)`：既能把一部分括起来量词，也能在 `sub` 的替换串里用 `\1` `\2` 反向引用

量词默认是**贪婪**的（能多匹配就多匹配），在量词后面加 `?` 就变成**非贪婪**：`<.+?>` 只吃到第一个 `>`。

**高频混淆点**：`re.match` **只从字符串开头**尝试匹配，`re.search` 会**在整串里找**。
要让「整串都符合」应该用 `re.fullmatch`，而不是 `re.match`。""",
        "plain": r"""正则就是**搜索框「通配符」的加强版**。

普通查找只能找固定文字，正则能找「**形状**」：

- `\d{3}` = 「连着的 3 个数字」，不管具体是哪三个
- `A\d{3}` = 「大写 A 开头，后面跟 3 个数字」，所以能一网打尽 A123、A999

四个函数像四件不同的工具：

- `search` 是**找第一个**（像 Ctrl+F 找下一个）
- `findall` 是**全部找出来装进列表**（像“全部高亮并复制”）
- `sub` 是**批量替换**（像“全部替换”）
- `fullmatch` 是**门卫**：整张通行证必须从头到尾都对才放行，所以最适合做校验

⚠️ 为什么必须写 `r"\d"`？因为 Python 会先把字符串里的反斜杠处理一遍，才交给正则。
`r` 前缀就是告诉 Python：“这串里的反斜杠别动，原样交给正则”。""",
        "example": r"""import re

text = "订单 A123 已发货，联系 zhang@shop.com"

# search：只找第一个匹配，返回 Match 或 None
m = re.search(r"A\d{3}", text)
print(m.group())

# findall：找出全部，直接返回字符串列表
print(re.findall(r"\d+", text))

# sub：把匹配到的部分批量替换
print(re.sub(r"\d+", "#", text))

# fullmatch：整串必须匹配，专门用来做校验
print(re.fullmatch(r"A\d{3}", "A123") is not None)
print(re.fullmatch(r"A\d{3}", "A123x") is not None)

# 原始字符串：r"\d" 输出的就是反斜杠加 d
print(r"\d")""",
        "example_output": "A123\n['123']\n订单 A# 已发货，联系 zhang@shop.com\nTrue\nFalse\n\\d",
        "pitfalls": [
            r'**忘了写 `r` 前缀**：`"\d"` 里的反斜杠会先被 Python 处理一遍，正则拿到的可能不是 `\d`，匹配结果莫名其妙。',
            "**把 `re.match` 当整串校验**：`re.match` 只从开头匹配，`A123x` 也会通过；要整串校验得用 `re.fullmatch`。",
            "**`findall` 里带分组就变样**：模式里有 `(...)` 时，`findall` 返回的是分组内容，不再是一整个匹配串。",
            r"**忘了量词默认贪婪**：`<.+>` 会一路吃到最后一个 `>`；只想吃一个要写非贪婪 `<.+?>`。",
        ],
        "task": r"""定义三个函数：

1. `is_valid_id(text)` —— 用 `re.fullmatch` 校验字符串形如「大写 `A` 后面跟 3 位数字」（如 `A123`），返回 `bool`。
   注意大小写敏感，`a123` 不合法。
2. `extract_emails(text)` —— 用 `re.findall` 返回文本里**所有邮箱**组成的列表，保持出现顺序。
3. `mask_phone(text)` —— 用 `re.sub` 把文本里 11 位手机号（`1` 开头、第二位是 3~9）的**中间 4 位**替换成 `****`。
   例如 `13800000000` 变成 `138****0000`；文本里没有手机号时要**原样返回**。""",
        "setup": "",
        "starter": STARTER,
        "hint": r"""- 校验整串：`return bool(re.fullmatch(r"A\d{3}", text))`
- 邮箱：`return re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text)`
- 手机号：先用分组把「前 3 位」和「后 4 位」括起来，替换时用 `\1` `\2` 引用：
  `re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", text)`""",
        "checker": REGEX_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "关于 `re.match` 和 `re.search`，下面说法正确的是？",
                "options": [
                    "`re.match` 只从字符串开头匹配，`re.search` 会在整串里找第一个匹配",
                    "两者完全一样，只是名字不同",
                    "`re.search` 只从开头匹配，`re.match` 会找全文",
                    "`re.match` 返回所有匹配的列表，`re.search` 返回第一个",
                ],
                "answer_index": 0,
                "explanation": "`re.match` 只在开头尝试，`re.search` 会一直往后找；要整串校验则该用 `re.fullmatch`。B、C 把两者说成一样或说反了，D 混淆了 `findall`。",
            },
            {
                "type": "choice",
                "stem": r'写正则时为什么推荐用 `r"\d"` 而不是 `"\d"`？',
                "options": [
                    r"`r` 前缀让反斜杠不被字符串转义，正则引擎拿到的才是 `\d`",
                    "`r` 前缀能让正则匹配得更快",
                    "`r` 前缀能让正则区分大小写",
                    r'没有区别，`"\d"` 也一样能匹配数字',
                ],
                "answer_index": 0,
                "explanation": r"`r` 表示原始字符串，反斜杠原样保留；不加 `r`，Python 会先对 `\d` 做一次转义处理，正则拿到的可能不是想要的内容。",
            },
            {
                "type": "judge",
                "stem": r'在 Python 中，`re.fullmatch(r"A\d{3}", "A1234")` 会匹配成功，因为开头是大写 A 后面跟着数字。',
                "answer": False,
                "explanation": "`fullmatch` 要求**整串**匹配，`A1234` 有 4 位数字，多出来一位，所以返回 `None`。",
            },
            {
                "type": "blank",
                "stem": (
                    "补全这一步，把文本里匹配到的所有数字都替换成 #（用 ___ 表示要填的部分）：\n"
                    r're.___(r"\d+", "#", text)'
                ),
                "answer": "sub",
                "hint": "填一个三字母的方法名",
                "explanation": "`re.sub` 用来做替换，返回替换后的新字符串。",
            },
        ],
    },
    {
        "code": "py-stdlib",
        "stage": "Python 进阶补强",
        "title": "常用标准库：collections / itertools / functools",
        "summary": "别自己造轮子，标准库早就写好了",
        "supplementary": True,
        "definition": r"""标准库是 Python 自带、**不用安装**就能 `import` 的模块。很多「看起来要自己写」的功能，标准库早就写好了。

- `collections.Counter` —— 一句话统计词频。`Counter(可迭代对象)` 直接得到「元素 → 次数」；
  `.most_common(n)` 返回按次数从高到低的**前 n 个 `(元素, 次数)` 元组**。
- `collections.defaultdict` —— 让「键不存在时自动给个默认值」。用 `defaultdict(list)` 之后，
  `d[k].append(v)` 不用先判断键在不在，省掉 `if k not in d: d[k] = []` 这类绕法。
  对比普通字典要写 `counts[w] = counts.get(w, 0) + 1`，`defaultdict` 直接 `counts[w] += 1`。
- `itertools.chain` —— 把多个序列**接成一条**。`chain.from_iterable(嵌套列表)` 常用于把二维拍平成一维。
- `functools.lru_cache` —— 给函数加「最近使用」缓存，一行搞定。递归函数加上它，重复子问题直接取缓存，
  复杂度从指数级降到线性。**限制：参数必须可哈希**（数字/字符串/元组可以，列表/字典不行）。
- `functools.wraps` —— 写装饰器时保留原函数的 `__name__` 和文档串；不写会让被装饰函数的名字全变成 `wrapper`
  （对比「装饰器」那一课）。

原则：**先查标准库，别自己造轮子**。自己写的版本往往更慢、更容易有 bug。""",
        "plain": r"""这些工具就是编程界的「常用工具包」，随 Python 一起发货：

- `Counter` = **计数器**：把一堆东西丢进去，它告诉你每个出现了几次，数词频一句话结束。
- `defaultdict` = **自带默认值的字典**：普通字典查不存在的键会 `KeyError`，它不会，会当场给你一个新值
  （比如一个空列表），省掉每次都写 `d.get(k, 0)` 的麻烦。
- `chain` = **传送带**：把好几条队伍首尾接起来，当成一条长队来遍历。
- `lru_cache` = **便签本**：算过一次的结果记在便签上，下次同样的输入直接翻便签，不再算一遍。
  递归斐波那契不加缓存要算几百万次，加上缓存几乎瞬间出结果。
- `wraps` = **保身份**：给函数套装饰器外壳时，别让它把原函数的名字弄丢，否则报错日志里全是 `wrapper`。""",
        "example": r"""from collections import Counter, defaultdict
from itertools import chain
import functools

# Counter：一行统计词频并取最多的前 2 个
print(Counter(["a", "a", "a", "b", "b", "c"]).most_common(2))

# defaultdict(list)：键不存在时自动建一个空列表
groups = defaultdict(list)
for k, v in [("a", 1), ("b", 2), ("a", 3)]:
    groups[k].append(v)
print(dict(groups))

# chain.from_iterable：把嵌套列表拍平
print(list(chain.from_iterable([[1, 2], [3], [4, 5]])))

# lru_cache：给递归自动加缓存
@functools.lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(10))
print(fib.cache_info().hits > 0)

# functools.wraps：保留被装饰函数的名字
def deco(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@deco
def hello():
    return "hi"

print(hello.__name__)""",
        "example_output": "[('a', 3), ('b', 2)]\n{'a': [1, 3], 'b': [2]}\n[1, 2, 3, 4, 5]\n55\nTrue\nhello",
        "pitfalls": [
            "**自己写循环数词频**：`Counter` 一行就够，`for` 循环加 `dict.get` 又长又慢。",
            "**`defaultdict` 忘了转回 `dict`**：直接返回 `defaultdict`，别人拿去用时查不存在的键会自动创建，容易埋 bug。",
            "**`lru_cache` 用在不可哈希的参数上**：参数是列表/字典会 `TypeError`，缓存键必须是可哈希的（数字/字符串/元组）。",
            "**装饰器忘了 `functools.wraps`**：被装饰函数的名字全变成 `wrapper`，日志和报错里分不清是谁。",
        ],
        "task": r"""定义以下四个函数：

1. `top_words(words, n)` —— 用 `collections.Counter` 返回出现次数最多的前 `n` 个 `(词, 次数)` 元组列表，
   按次数从高到低排列。
2. `group_by_first_letter(words)` —— 用 `collections.defaultdict(list)` 按每个单词**首字母小写**分组，
   返回一个**普通 `dict`**（分组内的值保留原单词和出现顺序）。
3. `flat_all(nested)` —— 用 `itertools.chain.from_iterable` 把嵌套列表拍平成一维列表。
4. `fib(n)` —— 用 `functools.lru_cache` 装饰的递归斐波那契（`fib(0)=0`、`fib(1)=1`）。
   要求缓存真的生效（`fib.cache_info()` 能查到命中次数）。""",
        "setup": "",
        "starter": STARTER,
        "hint": r"""- `return Counter(words).most_common(n)`
- `d = defaultdict(list)` → `for w in words: d[w[0].lower()].append(w)` → `return dict(d)`
- `return list(chain.from_iterable(nested))`
- 在 `def fib(n)` 上一行写 `@functools.lru_cache(maxsize=None)`，函数体里写递归即可""",
        "checker": STDLIB_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要统计一段文本里每个词出现的次数，并取出出现最多的前 3 个，最省事的做法是？",
                "options": [
                    "用 `collections.Counter(...).most_common(3)`",
                    "用 `for` 循环加 `list.index()` 手动数",
                    "先 `sorted` 排序，再用 `len` 数长度",
                    "转成 `set` 之后数集合的大小",
                ],
                "answer_index": 0,
                "explanation": "`Counter` 直接统计并给出 `most_common(n)`。B 又慢又容易写错；C、D 都得不到每个词各自出现的次数。",
            },
            {
                "type": "choice",
                "stem": "想给一个递归函数自动加缓存、避免重复计算，最直接的做法是？",
                "options": [
                    "用 `functools.lru_cache` 装饰这个函数",
                    "把递归改写成 `while` 循环",
                    "用一个 `global` 变量手动存结果",
                    "每次调用前先把缓存清空",
                ],
                "answer_index": 0,
                "explanation": "`@functools.lru_cache` 一行给函数加缓存。B 要手动改逻辑；C 自己维护容易出错；D 清缓存等于不缓存。",
            },
            {
                "type": "judge",
                "stem": "`functools.lru_cache` 可以装饰参数是列表的函数，因为列表也能当作缓存的键。",
                "answer": False,
                "explanation": "缓存键必须可哈希，列表和字典不可哈希，装饰后被调用会抛 `TypeError`。",
            },
            {
                "type": "blank",
                "stem": (
                    "用 `chain` 把嵌套列表拍平成一维（用 ___ 表示要填的部分）：\n"
                    "list(chain.___([[1, 2], [3]]))"
                ),
                "answer": "from_iterable",
                "hint": "填 chain 上的那个类方法名",
                "explanation": "`chain.from_iterable` 会把每个子序列依次接起来，正好用于拍平嵌套序列。",
            },
        ],
    },
    {
        "code": "py-context",
        "stage": "Python 进阶补强",
        "title": "上下文管理器与 with",
        "summary": "离开代码块时，保证把该收尾的都收尾",
        "supplementary": True,
        "definition": r"""上下文管理器是一个「进入时做准备、离开时一定会收尾」的对象。`with` 语句就是它的用法：

```python
with 管理器() as 变量:
    代码块
```

执行顺序：先调用管理器的 `__enter__`，把它的返回值绑定给 `变量`；然后执行代码块；
**无论代码块正常结束还是中途抛异常**，都会调用 `__exit__` 收尾。这正是 `with` 存在的全部理由 ——
**保证清理一定发生**（哪怕中间抛异常）。

`__exit__(self, exc_type, exc, tb)` 的三个参数：

- 没有异常时三者都是 `None`
- 有异常时分别是异常类型、异常对象、回溯信息

`__exit__` 的返回值决定异常是否继续往外抛：

- 返回 `None` 或 `False` —— **不吞**，异常继续往上冒（默认行为，多数情况要这个）
- 返回 `True` —— **吞掉**异常，代码块后面继续正常执行（只在明确想忽略某种错误时用）

`with` 和 `try/finally` 是等价的：`try: 干活 finally: 收尾` 能保证收尾，`with` 是它更短的写法。

用 `contextlib.contextmanager` 可以把一个**生成器函数**变成上下文管理器：`yield` 之前的代码相当于 `__enter__`，
`yield` 之后的代码相当于 `__exit__`。**清理代码必须放进 `try/finally`**，否则代码块里抛异常时，
`yield` 之后的代码根本不会执行。""",
        "plain": r"""把 `with` 想成**进门换鞋、出门收鞋**：

`__enter__` 是进门要做的事（拿钥匙、开文件、开始计时），`__exit__` 是出门必做的事（锁门、关文件、停止计时）。
关键是**不管你在屋里发生了什么**（哪怕摔了一跤 = 抛异常），出门时该做的收尾一样不会漏 ——
这就是它比「记得手动关」可靠的地方。

`__exit__` 返回 `True`，相当于**跟 Python 说“这个错我处理了，别往外报了”**；返回 `False`/`None` 就是
“我收个尾，但错还是照常往上报”。

`@contextmanager` 是「短写版」：把 `yield` 当分界线，上半段是进门、下半段是出门。
但出门那段一定要包 `try/finally`，否则屋里一出事，它就溜了。

⚠️ 常见坑：只写了 `yield` 却忘了 `finally` 里的清理；或者明明该让异常冒出来，却随手 `return True` 把它吞了。""",
        "example": r"""from contextlib import contextmanager

class Tag:
    def __init__(self, name):
        self.name = name
    def __enter__(self):
        print(f"<{self.name}>")
        return self
    def __exit__(self, exc_type, exc, tb):
        print(f"</{self.name}>")
        return False          # 不吞异常

with Tag("b") as t:
    print("内容")

@contextmanager
def opening(name):
    print("open", name)
    try:
        yield name
    finally:
        print("close", name)

with opening("file") as f:
    print("use", f)""",
        "example_output": "<b>\n内容\n</b>\nopen file\nuse file\nclose file",
        "pitfalls": [
            "**`__exit__` 少写参数**：必须是 `__exit__(self, exc_type, exc, tb)` 四个参数，少写会报错。",
            "**随手 `return True` 吞异常**：除非明确要忽略这种错误，否则异常应照常外抛（`return False`/`None`）。",
            "**`@contextmanager` 里清理没放 `finally`**：块内抛异常时，`yield` 后面的清理代码不会执行，资源就泄漏了。",
            "**该收尾的没放进 `with`**：把 `open`、锁、连接用 `with` 管起来，别指望自己每次都记得手动关。",
        ],
        "task": r"""1. 用**类**实现上下文管理器 `Timer`：
   - `__enter__` 返回 `self`，并开始计时（用 `time.perf_counter()`）
   - `__exit__` 把耗时存到 `self.elapsed`（浮点秒）
   - `__exit__` 要返回 `None` 或 `False`，**不能吞异常**
2. 用 `@contextlib.contextmanager` 实现上下文管理器函数 `ignore_error()`：
   - 块内抛出 `ValueError` 时**把它吞掉**（不往外抛）
   - 其他异常（如 `KeyError`）**照常抛出**""",
        "setup": "",
        "starter": STARTER,
        "hint": r"""- `Timer.__enter__`：`self.start = time.perf_counter()`，然后 `return self`
- `Timer.__exit__(self, exc_type, exc, tb)`：`self.elapsed = time.perf_counter() - self.start`，然后 `return False`
- `ignore_error`：
  `@contextmanager` 装饰 `def ignore_error():`
  函数体写 `try:` → `yield` → `except ValueError:` → `pass`""",
        "checker": CONTEXT_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`with` 语句要能「离开代码块时一定执行清理」，依赖对象上的哪两个方法？",
                "options": [
                    "`__enter__` 和 `__exit__`",
                    "`__init__` 和 `__del__`",
                    "`__open__` 和 `__close__`",
                    "`__start__` 和 `__stop__`",
                ],
                "answer_index": 0,
                "explanation": "`with` 先调用 `__enter__`、离开时调用 `__exit__`。其他几个名字都不是上下文管理器协议的一部分。",
            },
            {
                "type": "choice",
                "stem": "`__exit__(self, exc_type, exc, tb)` 返回什么时，会「吞掉」代码块里抛出的异常？",
                "options": [
                    "返回 `True`",
                    "返回 `False`",
                    "返回 `None`",
                    "只要不写 `return` 就会吞掉",
                ],
                "answer_index": 0,
                "explanation": "返回 `True` 表示异常已处理、不再外抛；返回 `False` 或 `None` 时异常继续往上冒。",
            },
            {
                "type": "judge",
                "stem": "用 `@contextmanager` 写上下文管理器时，`yield` 之前的代码相当于 `__enter__`，之后的代码相当于 `__exit__`，而清理代码必须放进 `try/finally` 才能在异常时也执行。",
                "answer": True,
                "explanation": "生成器上下文管理器以 `yield` 为分界；只有把清理放进 `finally`，块内抛异常时它才会执行。",
            },
            {
                "type": "blank",
                "stem": (
                    "补全这个上下文管理器，让它在块结束时打印 close（用 ___ 表示要填的部分）：\n"
                    "from contextlib import contextmanager\n\n"
                    "@contextmanager\n"
                    "def open_it():\n"
                    '    print("open")\n'
                    "    try:\n"
                    "        ___\n"
                    "    finally:\n"
                    '        print("close")'
                ),
                "answer": "yield",
                "hint": "填一个关键字",
                "explanation": "生成器上下文管理器用 `yield` 把控制权交给 `with` 代码块，块结束再回到 `yield` 之后继续执行。",
            },
        ],
    },
    {
        "code": "py-concurrency",
        "stage": "Python 进阶补强",
        "title": "并发：线程、进程与 concurrent.futures",
        "summary": "等 I/O 时别干等，让多个任务一起跑",
        "supplementary": True,
        "definition": r"""并发是指「让多个任务在一段时间内一起推进」。选哪种方式，先看任务是**等 I/O** 还是**烧 CPU**：

- **I/O 密集**（网络请求、读写文件/数据库，大量时间在「等对方」）→ 用**线程**（`ThreadPoolExecutor`）。
- **CPU 密集**（大量计算）→ 用**进程**（`ProcessPoolExecutor`）。

原因：CPython 有 **GIL（全局解释器锁）**，同一时刻只有一个线程能执行 Python 字节码，
所以多线程**跑不出并行计算**；但线程在**等待 I/O 时会主动释放 GIL**，这时别的线程就能跑，
所以 I/O 密集用线程是有效的。CPU 密集要真正并行，只能开多个进程，各自有独立的解释器和 GIL。

`concurrent.futures` 提供统一接口：

- `ThreadPoolExecutor(...)` / `ProcessPoolExecutor(...)` —— 线程池 / 进程池
- `executor.submit(fn, 参数)` —— 提交一个任务，立刻返回一个 `Future`；用 `future.result()` 取结果（**会阻塞**到该任务完成）
- `executor.map(fn, 一堆参数)` —— 更省事，返回结果的迭代器，**顺序与输入一致**（内部按输入顺序产出，
  所以即使第 2 个任务先完成，也会等第 1 个）
- `as_completed(futures)` —— 反过来，**谁先完成就先给我谁**

**一定要用 `with` 管理线程池**：代码块结束时 `with` 会调用 `executor.shutdown()` 关闭池子、回收线程。
不用 `with` 又忘了手动 `shutdown()`，线程会一直挂着，越积越多。

`asyncio` 是另一条路：**单线程事件循环**，靠 `await` 在等 I/O 时切换任务，不开新线程；
线程池则是真的开了多个线程去跑。""",
        "plain": r"""判断用线程还是进程，记住一句话：**「等」用线程，「算」用进程。**

- 线程池像**一个客服带多个窗口**：客服大部分时间在等客户回应（等 I/O），
  一个客服可以同时盯好几个窗口，等的时候就去处理别的窗口 —— 所以 I/O 密集用线程很划算。
- 进程池像**多开几个工厂**：因为 Python 有个「一次只让一个线程动脑算」的规矩（GIL），
  想真正同时做**大量计算**，就得开多个进程，每个进程各有一套脑子。

`executor.map` 像**按号取餐**：它按你提交的顺序叫号，第 1 号没好就等第 1 号，
所以结果顺序和输入**永远对得上**。想要「谁先好先拿谁」，就用 `as_completed`。

⚠️ 为什么一定要 `with`？因为线程池是**借来的资源**，`with` 保证离开时自动还回去（关池子）；
不用 `with` 又不手动关，线程会一直挂在那儿泄漏。

⚠️ `asyncio` 和线程池不是一回事：`asyncio` 只有**一个线程**在跑，靠事件循环不停切换任务；
线程池是**实打实开了好几个线程**。""",
        "example": r"""import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fake_fetch(url):
    time.sleep(0.05)          # 假装在等网络
    return "内容:" + url

urls = ["a", "b", "c"]

# map：结果顺序和输入一致
with ThreadPoolExecutor(max_workers=3) as ex:
    print(list(ex.map(fake_fetch, urls)))

# as_completed：谁先完成先拿谁
with ThreadPoolExecutor(max_workers=3) as ex:
    futures = [ex.submit(fake_fetch, u) for u in urls]
    done = [f.result() for f in as_completed(futures)]
print(sorted(done))""",
        "example_output": "['内容:a', '内容:b', '内容:c']\n['内容:a', '内容:b', '内容:c']",
        "pitfalls": [
            "**CPU 密集却用线程池**：GIL 让多线程算不快，白开线程还有开销；这种场景要用进程池。",
            "**不用 `with` 管线程池**：忘了 `shutdown()` 会泄漏线程，程序退出前线程一直挂着。",
            "**以为 `map` 按完成顺序返回**：`map` 返回的顺序和输入一致；要按完成先后取，得用 `as_completed`。",
            "**乱用 `future.result()` 阻塞**：对提交的 future 依次 `.result()` 会按顺序干等，等于串行；要并发得先都 `submit` 再取结果。",
        ],
        "task": r"""定义两个函数（`fetch` 是**同步**函数：接收一个 url 返回字符串）：

1. `fetch_all(urls, fetch)` —— 用 `ThreadPoolExecutor` 并发调用 `fetch`，
   返回**按输入顺序排列**的结果列表。
2. `fetch_first_done(urls, fetch)` —— 用 `as_completed` 返回**最先完成**的那个结果。""",
        "setup": "",
        "starter": STARTER,
        "hint": r"""- `fetch_all`：`with ThreadPoolExecutor() as ex:` 然后 `return list(ex.map(fetch, urls))`
- `fetch_first_done`：先 `futures = [ex.submit(fetch, u) for u in urls]`，
  再 `for f in as_completed(futures): return f.result()`""",
        "checker": CONCURRENCY_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要抓取一批网页，主要时间都花在等网络上（I/O 密集），通常选哪种并发方式最合适？",
                "options": [
                    "`ThreadPoolExecutor`（线程池）",
                    "`ProcessPoolExecutor`（进程池）",
                    "完全串行，不开并发",
                    "先 `sleep` 一会儿再串行跑",
                ],
                "answer_index": 0,
                "explanation": "I/O 密集时线程足够：等 I/O 会释放 GIL，多个线程能重叠等待。进程池开销更大，一般留给 CPU 密集任务。",
            },
            {
                "type": "choice",
                "stem": "`executor.map(fn, items)` 返回的结果迭代器有什么特点？",
                "options": [
                    "结果的顺序和输入顺序一致",
                    "按任务完成的先后顺序返回",
                    "返回顺序随机、不可预测",
                    "只返回第一个任务的结果",
                ],
                "answer_index": 0,
                "explanation": "`map` 会按输入顺序产出结果；想按完成先后取，用 `as_completed`。",
            },
            {
                "type": "judge",
                "stem": "用 `with ThreadPoolExecutor() as ex:` 管理线程池，是为了在代码块结束时自动关闭线程池、回收线程。",
                "answer": True,
                "explanation": "`with` 退出时会调用 `executor.shutdown()`，把线程回收掉；不用 `with` 又忘了关会泄漏线程。",
            },
            {
                "type": "blank",
                "stem": (
                    "要从一批 future 里按完成先后取结果，先从 `concurrent.futures` 导入两个名字（用 ___ 表示要填的部分）：\n"
                    "from concurrent.futures import ___, as_completed"
                ),
                "answer": "ThreadPoolExecutor",
                "hint": "填线程池类的名字",
                "explanation": "`from concurrent.futures import ThreadPoolExecutor, as_completed`，前者建池子，后者按完成顺序遍历。",
            },
        ],
    },
]
