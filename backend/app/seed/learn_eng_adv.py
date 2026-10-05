"""阶段：工程进阶（补充课）。

在前面「工程基础」（JSON / 环境变量 / 日志 / 类型注解 / HTTP / 异步 / Pydantic）
之上，再往真正的工程实践走一步：写测试、管依赖、把代码质量交给工具链。

这三课都是 `supplementary=True` 的「补充课」：**不参与引导式学习的主线解锁链条**
（见 `routers/learn.py::_statuses`），永远可学，也不会把老学生已经解锁的课重新锁上。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）

注意：本文件里的 checker 只依赖标准库，且**不能 import 第三方库**
（另外，代码沙箱把 `inspect` 也列进了黑名单，所以用的都是 `__annotations__` 这类写法）。
"""

STARTER = "# 在下面写出你的代码（删掉这行注释也没关系）\n"


TEST_CHECKER = """
try:
    assert callable(apply_discount), "apply_discount 应该是一个函数"
    assert apply_discount(200, 0.5) == 100.0, "apply_discount(200, 0.5) 应该是 100.0 —— 折扣后金额 = 原价 × (1 - 折扣率)"
    assert apply_discount(100, 0) == 100.0, "rate=0 表示不打折，应该原价返回 100.0"
    assert apply_discount(100, 1) == 0.0, "rate=1 表示全免，应该返回 0.0"
    assert apply_discount(19.99, 0.33) == 13.39, "结果要四舍五入保留 2 位小数，别忘了 round(金额, 2)"

    assert isinstance(cases, list), "cases 应该是一个列表（测试用例列表）"
    assert len(cases) >= 4, f"cases 至少要有 4 条用例，现在只有 {len(cases)} 条"
    for i, c in enumerate(cases):
        assert isinstance(c, (tuple, list)) and len(c) == 3, f"第 {i + 1} 条用例应该是 (price, rate, expected) 三元组"
        p, r, exp = c
        got = apply_discount(p, r)
        assert got == exp, f"第 {i + 1} 条用例 ({p}, {r}, {exp}) 和你的 apply_discount 结果 {got} 对不上，检查一下期望值是不是写错了"

    rates = [c[1] for c in cases]
    assert 0 in rates, "cases 里要有一条 rate=0（不打折）的边界用例"
    assert 1 in rates, "cases 里要有一条 rate=1（免费）的边界用例"

    def broken_discount(price, rate):
        # 故意写错的实现：公式写成了「原价 × 折扣率」，还忘了 round。
        # 只用它来检验学生的用例能不能抓到 bug，绝不覆盖学生自己的 apply_discount。
        return price * rate

    caught = False
    for c in cases:
        p, r, exp = c
        if broken_discount(p, r) != exp:
            caught = True
            break
    assert caught, "你的用例抓不住 bug：拿一个故意写错的实现（算成 price * rate）去跑，居然全部通过了。说明期望值不够严格，或者覆盖面太窄 —— 重点检查 rate=0 / rate=1 这两条边界"

    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except TypeError as e:
    print("__FAIL__ 用例的写法不对：" + str(e) + "，每条应该是 (price, rate, expected) 三元组")
except ValueError as e:
    print("__FAIL__ 用例的写法不对：" + str(e) + "，一条用例要正好放三个值")
"""


DEPS_CHECKER = """
try:
    text = "# Web 框架\\nflask==2.0.1\\n\\nrequests>=2.28\\nuvicorn\\n  \\nDjango~=4.2\\n# 开发工具\\n"
    expected = {"flask": "==2.0.1", "requests": ">=2.28", "uvicorn": "", "django": "~=4.2"}
    got = parse_requirements(text)
    assert isinstance(got, dict), "parse_requirements 应该返回一个字典 {包名: 版本约束}"
    assert got == expected, f"解析结果不对：期望 {expected}，你得到 {got}。检查三点：空行/注释行有没有跳过、包名有没有转成小写、没有版本约束时值是不是空字符串 \\"\\""

    assert parse_requirements("") == {}, "空文本应该解析成空字典"
    assert parse_requirements("# 只有注释\\n\\n") == {}, "只有注释和空行的文本应该解析成空字典"
    assert parse_requirements("Flask==2.0.1")["flask"] == "==2.0.1", "包名要统一转成小写：Flask 应该变成 flask"

    lines = to_lines(expected)
    want_lines = ["django~=4.2", "flask==2.0.1", "requests>=2.28", "uvicorn"]
    assert lines == want_lines, f"to_lines 要按包名升序排列，且没有版本约束的只输出包名；期望 {want_lines}，你得到 {lines}"
    assert parse_requirements("\\n".join(lines)) == expected, "往返一致性：把 to_lines 生成的文本再解析回来，应该得到和原来等价的字典"
    assert to_lines({}) == [], "空字典应该生成空列表"

    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except AttributeError as e:
    print("__FAIL__ 用到了不存在的方法：" + str(e) + "，检查是不是把 dict / str 的方法名写错了")
except TypeError as e:
    print("__FAIL__ 参数或返回值类型不对：" + str(e) + "，parse_requirements 接收文本返回字典，to_lines 接收字典返回列表")
"""


QUALITY_CHECKER = """
try:
    assert callable(average), "average 应该是一个函数"
    ann = getattr(average, "__annotations__", {})
    assert "scores" in ann, "average 的参数缺少类型注解 —— 应该写成 def average(scores: list[float]) -> float"
    assert "return" in ann, "average 的返回值缺少类型注解 —— 在参数括号后面写 -> float"

    assert average([]) == 0.0, "空列表要返回 0.0，不能直接做除法（会除零报错）"
    assert isinstance(average([]), float), "空列表要返回 0.0 这个小数（float），不要返回整数 0"
    assert average([2, 4]) == 3.0, "average([2, 4]) 应该是 (2 + 4) / 2 = 3.0"
    assert average([1, 2, 4]) == 2.33, "average([1, 2, 4]) 是 7 / 3 = 2.333...，要用 round(总和 / 个数, 2) 保留两位小数"
    assert isinstance(average([2, 4]), float), "返回值要是 float（3.0 而不是 3）"
    assert average([5]) == 5.0, "只有一个元素时，平均值就是它自己"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except TypeError as e:
    print("__FAIL__ 调用方式或参数类型不对：" + str(e) + "，average 应该接收一个数字列表")
except ZeroDivisionError:
    print("__FAIL__ 空列表时发生了除零 —— 先判断 scores 为空就返回 0.0，再去算平均值")
"""


LESSONS: list[dict] = [
    # ----------------------------------------------------------------- eng-test
    {
        "code": "eng-test",
        "stage": "工程进阶",
        "title": "单元测试与 pytest",
        "summary": "测试是给未来的自己留的安全网，改代码不慌",
        "supplementary": True,
        "definition": (
            "**单元测试**就是写一段代码去调用你做好的函数，检查它返回的结果对不对。"
            "「单元」指被单独拿出来测的一小块功能，通常就是一个函数。\n\n"
            "**pytest** 是目前 Python 最常用的测试框架，它的约定少得惊人：\n\n"
            "- 文件名形如 `test_*.py`，`pytest` 会自动找到它们\n"
            "- 文件里 **`test_` 开头的函数**就是一条用例，一个函数只测一件事\n"
            "- 断言直接写普通的 `assert`；失败时 pytest 会把**实际值**和期望值一起打印出来，一眼能看出差在哪\n"
            "```python\n# test_discount.py\ndef test_half():\n    assert apply_discount(200, 0.5) == 100.0\n```\n"
            "在项目根目录敲一行 `pytest`，它就会自动发现并运行所有用例，输出 `3 passed` 或 `1 failed`。\n\n"
            "**断言异常**：要检查「这段代码应该抛异常」时用 `pytest.raises`：\n"
            "```python\nimport pytest\n\ndef test_bad_rate():\n    with pytest.raises(ValueError):\n        apply_discount(100, 2)\n```\n\n"
            "**参数化**：同一段断言要跑很多组数据时，用 `@pytest.mark.parametrize`，"
            "省掉把测试函数复制好几遍：\n"
            "```python\n@pytest.mark.parametrize(\"price, rate, expected\", [\n"
            "    (100, 0, 100.0),\n"
            "    (100, 1, 0.0),\n"
            "])\ndef test_discount(price, rate, expected):\n"
            "    assert apply_discount(price, rate) == expected\n```\n\n"
            "**fixture**：好几个用例都要用的东西（临时数据库、样例文件、登录好的客户端），"
            "用 `@pytest.fixture` 定义成夹具，测试函数只要把它写成参数，pytest 负责注入和清理。"
        ),
        "plain": (
            "**为什么说测试是「给未来的自己留的安全网」？**\n\n"
            "今天你写的函数，三个月后要加个新功能。改完之后你怎么知道没把别的功能改坏？"
            "如果有一堆测试，敲一行 `pytest`：绿色就是没改坏，红色就指出哪一条挂了 —— "
            "**几秒钟拿到答案，不用把每个场景再手工点一遍**。\n\n"
            "刚入门最容易忽略的一点：**一条永远会通过的测试，等于没有测试**。\n\n"
            "`assert True` 永远通过，它不检查任何东西；"
            "`assert apply_discount(100, 0) == 100.0` 才有意义 —— 一旦你把公式写错，它就会变红。"
            "**测试的价值恰恰来自它能失败**。\n\n"
            "所以写完一条测试，要反过来问自己："
            "「我把现在的实现故意改坏，这条测试能抓住吗？」抓不住，就说明它太弱了。"
        ),
        "example": (
            "# pytest 的三条约定：test_ 开头的函数是一条用例、\n"
            "# 普通 assert 就是断言、pytest 会自动发现并运行它们。\n"
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "def test_add():\n"
            "    assert add(2, 3) == 5\n"
            "\n"
            "def test_add_zero():\n"
            "    assert add(0, 0) == 0\n"
            "\n"
            "# 这里用最朴素的循环，模拟 pytest 的「自动发现」\n"
            "for _name, _fn in list(globals().items()):\n"
            "    if _name.startswith(\"test_\"):\n"
            "        _fn()\n"
            "        print(\"通过:\", _name)"
        ),
        "example_output": "通过: test_add\n通过: test_add_zero",
        "pitfalls": [
            "**只写 `assert True` 这类恒真断言**：永远通过 = 什么都没测；测试必须能在实现改错时变红。",
            "**期望值直接调用被测函数算出来**：`assert f(x) == f(x)` 两边永远相等，实现错了它照样通过；期望值要按业务规则独立写出来。",
            "**只测正常值、不测边界**：空输入、0、满值、异常路径往往是 bug 的藏身处，漏掉边界等于漏掉最该测的地方。",
            "**浮点数直接用 `==` 比**：金额先 `round(..., 2)` 再比，否则 `0.1 + 0.2 == 0.3` 这种精度问题会让测试乱红乱绿。",
        ],
        "task": (
            "1. 实现函数 `apply_discount(price, rate)`：`rate` 是折扣率（0~1），"
            "返回打完折后的金额，**四舍五入保留 2 位小数**（用 `round(..., 2)`）。\n"
            "2. 再定义一个变量 `cases`，它是**测试用例列表**：每个元素是 "
            "`(price, rate, expected)` 三元组，至少要 **4 条**。\n"
            "3. 用例必须覆盖 `rate=0`（不打折）和 `rate=1`（免费）两个**边界**。\n\n"
            "系统会拿一个**故意写错的实现**去跑你给的每一条用例，"
            "要求至少有 1 条会失败 —— 也就是说你的用例必须真的能抓 bug，而不是一堆恒真断言。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "折扣后金额 = 原价 × (1 - 折扣率)，最后 `round(..., 2)`：\n"
            "```\n"
            "def apply_discount(price, rate):\n"
            "    return round(price * (1 - rate), 2)\n"
            "\n"
            "cases = [\n"
            "    (100, 0, 100.0),      # 不打折\n"
            "    (100, 1, 0.0),        # 免费\n"
            "    (200, 0.5, 100.0),\n"
            "    (19.99, 0.33, 13.39),\n"
            "]\n"
            "```"
        ),
        "checker": TEST_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "一条「永远都会通过」的测试，最大的问题是什么？",
                "options": [
                    "它没有真正检查任何东西，等于没写测试",
                    "它会让测试运行变慢",
                    "它说明代码覆盖率已经达到 100%",
                    "它只是风格问题，保留着也无所谓",
                ],
                "answer_index": 0,
                "explanation": (
                    "测试的价值来自它能失败：实现一改错，它就应该变红。"
                    "`assert True` 在任何情况下都通过，所以它保护不了你。速度、覆盖率都不是重点。"
                ),
            },
            {
                "type": "choice",
                "stem": "关于 pytest 怎么找测试、怎么断言，下面说法正确的是？",
                "options": [
                    "自动运行 `test_*.py` 里 `test_` 开头的函数，普通 `assert` 就是断言",
                    "必须手动把所有用例注册进一个列表才会执行",
                    "测试函数必须以 `check` 开头，断言必须写 `self.assertEqual(...)`",
                    "只能测类里的方法，普通函数测不了",
                ],
                "answer_index": 0,
                "explanation": (
                    "这正是 pytest 最省事的地方：命名约定 + 普通 assert。"
                    "需要手动注册、或者必须用 `self.assertEqual` 的是 unittest 的风格。"
                ),
            },
            {
                "type": "judge",
                "stem": "测试里的期望值可以直接调用被测函数算出来，例如 `assert apply_discount(p, r) == apply_discount(p, r)`。",
                "answer": False,
                "explanation": (
                    "这样写左右两边永远相等，是一条恒真断言，实现改错了它也照样通过。"
                    "期望值必须按业务规则独立写出来（手算或查表），比如 `(100, 0.5, 50.0)`。"
                ),
            },
            {
                "type": "blank",
                "stem": "下面这段代码断言「调用会抛出 ValueError」，补全函数名（用 `___` 表示要填的部分）：\nwith pytest.___(ValueError):\n    apply_discount(100, 2)",
                "answer": "raises",
                "hint": "填一个单词，意思是「应该抛出……」",
                "explanation": "`pytest.raises(异常类型)` 用来断言「这段代码应该抛异常」，是测异常路径的标准写法。",
            },
        ],
    },
    # ----------------------------------------------------------------- eng-deps
    {
        "code": "eng-deps",
        "stage": "工程进阶",
        "title": "依赖管理与项目结构",
        "summary": "一个项目一套依赖，换台电脑也能跑起来",
        "supplementary": True,
        "definition": (
            "**虚拟环境**给每个项目一套独立的依赖，互不干扰：\n"
            "```bash\n"
            "python -m venv .venv            # 建一个叫 .venv 的虚拟环境\n"
            "source .venv/bin/activate       # macOS / Linux 激活\n"
            ".venv\\Scripts\\activate          # Windows 激活\n"
            "pip install flask requests      # 装进这个环境，不影响全局\n"
            "```\n"
            "激活后命令行提示符前面会出现 `(.venv)`，此时 `python` 和 `pip` 都指向这个环境。\n\n"
            "**依赖清单**有两种主流形式：\n\n"
            "- `requirements.txt`：扁平的「一行一个依赖」，简单直接\n"
            "- `pyproject.toml`：除了依赖，还能声明项目名称/版本、构建后端、`dev` 依赖分组等，**现代项目首选**\n"
            "```toml\n[project]\nname = \"myapp\"\ndependencies = [\"flask==2.0.1\", \"requests>=2.28\"]\n```\n\n"
            "**版本约束符号**：\n\n"
            "- `==2.0.1` 精确锁定，装的就是这个版本\n"
            "- `>=2.28` 至少这个版本，更高也行\n"
            "- `~=2.28` 兼容升级：允许 `2.x` 里大于等于 2.28，但不跨到 `3.0`\n"
            "- 不写：装最新版（最不可控）\n\n"
            "`pip freeze` 会把当前环境里**所有**包（包括第三方库带进来的间接依赖）连同精确版本一次性列出来，"
            "它是「锁定文件」的原料，**不适合直接当依赖清单手写维护** —— 清单只该写你**直接**用到的那几个包。"
        ),
        "plain": (
            "**「在我电脑上是好的」这句话，几乎都出在依赖上**："
            "A 项目要 `requests 2.28`，B 项目要 `requests 2.31`，两个都装进全局 Python，"
            "必然有一个项目装不上、或者行为悄悄变了。\n\n"
            "虚拟环境（venv）就是**给每个项目单独开一个抽屉**："
            "`python -m venv .venv` 建抽屉，激活之后 `pip install` 装的东西只进这个抽屉，"
            "彼此不打架。换台电脑，照着依赖清单重装一遍，环境就能复现。\n\n"
            "**为什么依赖清单要提交进 git，`.venv/` 必须忽略？**\n\n"
            "- 清单体积小、是纯文本，记录了「项目需要什么」，别人和 CI 靠它复现环境 —— **要提交**\n"
            "- `.venv/` 有几百 MB、路径还和机器/平台绑定，是「在这台机器上装出来的结果」—— "
            "提交进去既臃肿又没用，必须写进 `.gitignore`\n\n"
            "这也正是这个项目自己的做法：`.gitignore` 里忽略了 `.venv/`，而依赖清单是要入库的。"
        ),
        "example": (
            "# requirements.txt 长什么样：一行一个依赖，有三种版本约束写法\n"
            "req = [\n"
            "    \"# Web 框架\",\n"
            "    \"flask==2.0.1\",     # == 精确锁定版本\n"
            "    \"requests>=2.28\",   # >= 至少这个版本\n"
            "    \"uvicorn~=0.23.0\",  # ~= 兼容升级（同一个大版本内）\n"
            "    \"rich\",             # 不写版本 = 装最新\n"
            "]\n"
            "\n"
            "# 注释行和空行不是依赖，要跳过\n"
            "for raw in req:\n"
            "    text = raw.split(\"#\")[0].strip()\n"
            "    if text:\n"
            "        print(\"依赖:\", text)\n"
            "\n"
            "# 谁该进 git：清单要提交，虚拟环境目录必须忽略\n"
            "print(\"提交 requirements.txt / pyproject.toml\")\n"
            "print(\"忽略 .venv/\")"
        ),
        "example_output": (
            "依赖: flask==2.0.1\n"
            "依赖: requests>=2.28\n"
            "依赖: uvicorn~=0.23.0\n"
            "依赖: rich\n"
            "提交 requirements.txt / pyproject.toml\n"
            "忽略 .venv/"
        ),
        "pitfalls": [
            "**不用虚拟环境、直接往全局 Python 里装**：不同项目的依赖版本互相覆盖，就会出现「在我电脑上是好的」。",
            "**把 `.venv/` 提交进 git**：几百 MB 且和机器、平台绑定，等于往仓库里塞一堆没用的文件，还拖慢 clone。",
            "**拿 `pip freeze` 的输出当依赖清单**：它把所有间接依赖都写了进去，动辄几十行难以维护；清单只写你直接用到的包。",
            "**依赖清单不提交**：别人和 CI 无法复现你的环境，只能靠猜——这也是「在我电脑上是好的」的另一半原因。",
        ],
        "task": (
            "1. 实现函数 `parse_requirements(text)`：把 requirements.txt 的文本解析成 "
            "`{包名: 版本约束}` 字典。要求：\n"
            "   - 忽略空行和以 `#` 开头的注释行\n"
            "   - 支持 `flask==2.0.1`、`requests>=2.28`、`uvicorn`（没有版本约束时值用空字符串 `\"\"`）\n"
            "   - 包名统一转成**小写**\n"
            "2. 实现函数 `to_lines(mapping)`：反向生成依赖清单的文本行，"
            "按**包名升序**排列，每行是 `f\"{name}{constraint}\"`；没有版本约束的只输出包名。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "逐行读：先 `strip()`，空行或 `#` 开头就 `continue`。\n"
            "找版本约束的位置可以用一个循环，遇到 `<>=!~` 里任意一个字符就切开：\n"
            "```\n"
            "name, constraint = line, \"\"\n"
            "for i, ch in enumerate(line):\n"
            "    if ch in \"<>=!~\":\n"
            "        name, constraint = line[:i].strip(), line[i:].strip()\n"
            "        break\n"
            "result[name.lower()] = constraint\n"
            "```\n"
            "生成文本行：`[f\"{name}{mapping[name]}\" for name in sorted(mapping)]`。"
        ),
        "checker": DEPS_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "为什么每个项目都建议用一个独立的虚拟环境？",
                "options": [
                    "让每个项目有自己的一套依赖，避免版本互相覆盖、出现「在我电脑上是好的」",
                    "能让 Python 代码跑得更快",
                    "虚拟环境会自动帮项目生成 requirements.txt",
                    "只有部署到服务器时才需要，本地开发直接装到全局就行",
                ],
                "answer_index": 0,
                "explanation": (
                    "两个项目依赖同一个包的不同版本时，都装进全局 Python 必然有一个出问题。"
                    "虚拟环境给每个项目单独一套依赖，还能照着清单在别的机器上复现。"
                ),
            },
            {
                "type": "choice",
                "stem": "关于 `requirements.txt` 和 `pyproject.toml` 的区别，下面说法正确的是？",
                "options": [
                    "前者是扁平的依赖清单；后者还能声明项目元信息、构建后端和依赖分组，现代项目首选",
                    "两者完全一样，用哪个都行",
                    "`pyproject.toml` 只能写依赖，不能写项目名和版本",
                    "`requirements.txt` 是 Python 官方唯一标准，`pyproject.toml` 已经废弃",
                ],
                "answer_index": 0,
                "explanation": (
                    "`requirements.txt` 就是一行一个依赖；`pyproject.toml` 用 `[project]` 表同时声明名称、"
                    "版本、依赖、可选依赖分组和构建后端，是现在的主流做法。"
                ),
            },
            {
                "type": "judge",
                "stem": "`pip freeze` 的输出包含所有间接依赖，适合不整理就直接当作项目的依赖清单提交。",
                "answer": False,
                "explanation": (
                    "`pip freeze` 会把你装过的每个包（连同第三方库带进来的间接依赖）按精确版本全列出来，"
                    "动辄几十行、难以维护。依赖清单只该写你**直接**用到的包。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全版本约束，表示「至少 2.28，更高版本也可以」（用 `___` 表示要填的部分）：\nrequests___2.28",
                "answer": ">=",
                "hint": "填一个版本约束符号",
                "explanation": "`>=` 表示最低版本；`==` 是精确锁定；`~=` 是兼容升级（允许补丁/次版本，不跨大版本）。",
            },
        ],
    },
    # -------------------------------------------------------------- eng-quality
    {
        "code": "eng-quality",
        "stage": "工程进阶",
        "title": "代码质量工具链：ruff / black / mypy",
        "summary": "让工具管格式和类型，评审只谈逻辑",
        "supplementary": True,
        "definition": (
            "三件工具各管一件事，不要混：\n\n"
            "- **black** —— 只管**格式**：缩进、引号、换行、空行。它故意「几乎没有配置项」，"
            "目的就是让团队不再争论风格，**存盘即格式化**。\n"
            "- **ruff** —— 管**静态检查**：未使用的变量 / import、可疑写法、命名问题等。"
            "它非常快，可以一次替代 flake8 + isort + 一部分 pylint 的工作。\n"
            "- **mypy** —— 管**类型检查**：读你写的类型注解，在**不运行代码**的情况下"
            "找出「传错类型」「返回值类型不符」这类问题。\n\n"
            "它们通常不靠人记得手动跑，而是挂在 **CI** 和 **pre-commit** 上："
            "提交时自动跑，有问题当场拦下来；代码评审也就不用再纠结空格和引号，只需讨论逻辑。\n\n"
            "一个现实是：**类型注解是可执行的文档**。IDE 靠它做补全和跳转，"
            "重构工具靠它安全地改名，mypy 靠它提前发现错误 —— 这也是为什么"
            "「类型注解」那一课和这一课要连起来看。"
        ),
        "plain": (
            "把三件工具想成**三道自动检查，各查各的**：\n\n"
            "- black = **排版机器人**：把你写的东西按同一套版式重排，不评价好坏\n"
            "- ruff = **挑错的老同事**：指出「这个变量没人用」「这个 import 没用上」「这里写法可疑」\n"
            "- mypy = **合同审查员**：只看你声明了什么类型、有没有违约，**根本不用把程序跑起来**\n\n"
            "**为什么三者要一起用？**因为它们管的层次不同："
            "格式乱不影响运行，但会让 diff 变脏、评论变多；静态检查能抓到「运行前就注定错」的问题；"
            "类型检查能在重构时兜住跨文件的调用。合起来，"
            "「空格要不要换行」交给 black，「这里有 bug」交给 ruff / mypy，"
            "人就只负责**业务逻辑对不对**。\n\n"
            "顺带一句：写了注解却从来不跑 mypy，就像买了保险不看条款 —— 让工具真的跑起来才有用。"
        ),
        "example": (
            "# 类型注解是「可执行的文档」：IDE 补全、重构、mypy 都靠它\n"
            "def distance(km: float, hours: float) -> float:\n"
            "    if hours == 0:\n"
            "        return 0.0\n"
            "    return round(km / hours, 2)\n"
            "\n"
            "print(distance.__annotations__)\n"
            "print(distance(120, 2.5))\n"
            "print(distance(10, 0))\n"
            "print(type(distance(10, 0)).__name__)"
        ),
        "example_output": (
            "{'km': <class 'float'>, 'hours': <class 'float'>, 'return': <class 'float'>}\n"
            "48.0\n"
            "0.0\n"
            "float"
        ),
        "pitfalls": [
            "**指望 black 帮你改逻辑**：它只动格式，看不懂你的意图，业务 bug 一个也抓不到。",
            "**写了类型注解却从不跑 mypy**：注解在运行时不会被检查，不跑 mypy 它就只是一行好看的注释。",
            "**只在本地手动跑这些工具**：人一定会忘；挂到 pre-commit / CI 上，才会每次提交都真的跑。",
            "**以为 ruff 能顶替所有检查**：它做静态检查又快又好，但不做类型推断（那需要 mypy），两者是互补关系。",
        ],
        "task": (
            "把一段「能跑但很烂」的代码重写好：实现函数 `average(scores)`，要求：\n"
            "1. **写全类型注解**：参数是 `list[float]`，返回值是 `float`\n"
            "2. 传进来**空列表**时返回 `0.0`（不能除零报错）\n"
            "3. 返回 `round(总和 / 个数, 2)` —— 保留两位小数"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "先判空再算，最后 round：\n"
            "```\n"
            "def average(scores: list[float]) -> float:\n"
            "    if not scores:\n"
            "        return 0.0\n"
            "    return round(sum(scores) / len(scores), 2)\n"
            "```"
        ),
        "checker": QUALITY_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "black / ruff / mypy 这三件工具分别管什么？",
                "options": [
                    "black 管格式，ruff 管静态检查（未用变量、可疑写法），mypy 管类型检查",
                    "black 管类型检查，ruff 管格式，mypy 管测试",
                    "三者都是格式化工具，只是速度不一样",
                    "ruff 会真正运行代码，用运行结果来发现错误",
                ],
                "answer_index": 0,
                "explanation": (
                    "black 只动格式、不管逻辑；ruff 是静态检查器，不运行代码也能指出未使用变量 / import 等问题；"
                    "mypy 读类型注解做类型检查。"
                ),
            },
            {
                "type": "choice",
                "stem": "关于类型注解，下面说法正确的是？",
                "options": [
                    "它是「可执行的文档」，IDE 补全和重构靠它，mypy 不运行代码就能据此检查",
                    "加了注解之后，Python 运行时会在类型不匹配时抛异常",
                    "加了注解程序会跑得更快",
                    "只有标准库需要写注解，业务代码不用写",
                ],
                "answer_index": 0,
                "explanation": (
                    "注解运行时不会被强制检查。要在**运行时**校验外部数据（比如接口传来的 JSON）得用 Pydantic；"
                    "注解本身主要服务于 IDE、mypy 和读代码的人。"
                ),
            },
            {
                "type": "judge",
                "stem": "black 几乎没有可配置项，它的设计目的就是终止团队里关于代码风格的争论。",
                "answer": True,
                "explanation": "black 的哲学是「没有选择就没有争论」，统一按一套版式重排，格式问题从此不用在评审里讨论。",
            },
            {
                "type": "blank",
                "stem": "补全给返回值加类型注解的符号（用 `___` 表示要填的部分）：\ndef average(scores: list[float]) ___ float:",
                "answer": "->",
                "hint": "填两个字符的箭头",
                "explanation": "`->` 后面跟返回类型，写在参数括号和冒号之间，例如 `def average(scores: list[float]) -> float:`。",
            },
        ],
    },
]
