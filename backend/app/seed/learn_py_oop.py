"""补充课：Python 面向对象（进阶）。

`py-class`（类与对象）讲了类、属性、`__init__` 这些基础；这一批课接着往深里讲
继承与多态、魔术方法与 @property、抽象基类与接口契约 —— 都是「把对象设计得像样」
时绕不开的东西，也是读懂别人代码里那些 `super()` / `__repr__` / `ABC` 的前提。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）

supplementary=True 表示这是「补充课」：不参与引导式学习的主线解锁链条。
"""

STARTER = "# 在下面写出你的代码（删掉这行注释也没关系）\n"

OOP_CHECKER = """
try:
    assert Animal("x").speak() == "...", "Animal.speak() 应该返回 '...'（这是父类的默认行为）"
    assert Dog("旺财").speak() == "汪汪", "Dog 要重写 speak() 让它返回 '汪汪'"
    assert Cat("咪").speak() == "喵", "Cat 要重写 speak() 让它返回 '喵'"
    assert Dog("旺财").name == "旺财", "Dog 里要用 super().__init__(name) 把名字交给父类存下来，否则 .name 会报错或取不到值"
    assert chorus([Dog("a"), Cat("b")]) == "汪汪 喵", "chorus 要把列表里每只动物的 speak() 用空格拼起来，别漏了空格或顺序"
    assert chorus([]) == "", "空列表时 chorus 应该返回空字符串 ''"
    assert kinds == [True, False], "kinds 应该是 [isinstance(Dog('a'), Animal), isinstance(Cat('a'), Dog)]，也就是 [True, False]"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except AttributeError as e:
    print("__FAIL__ 类里缺少属性或方法：" + str(e))
"""

MAGIC_CHECKER = """
try:
    assert repr(Money(100, "CNY")) == "Money(100, 'CNY')", "Money 的 __repr__ 要返回形如 Money(100, 'CNY') 的字符串（货币用单引号）"
    assert repr(Money(5, "USD")) == "Money(5, 'USD')", "__repr__ 要根据实际参数变化，不能把值写死"
    assert Money(100, "CNY") == Money(100, "CNY"), "金额和币种都相同的两个 Money 应该相等，需要自己写 __eq__ 按值比较"
    assert (Money(100, "CNY") == Money(100, "USD")) is False, "金额相同但币种不同不能算相等，__eq__ 里要把 currency 也比进去"
    assert Money(0, "CNY").label == "0 CNY", "label 要返回 '金额 币种' 的字符串，金额为 0 时也要正常显示"
    try:
        Money(100, "CNY").label = "改了"
        ro = False
    except AttributeError:
        ro = True
    assert ro, "label 只写了 getter，是只读属性；给它赋值应该抛 AttributeError"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except AttributeError as e:
    print("__FAIL__ 类里缺少属性或方法：" + str(e))
"""

ABC_CHECKER = """
try:
    assert Square(3).area() == 9, "Square(3).area() 应该返回 9（边长乘边长）"
    assert total_area([Square(2), Square(3)]) == 13, "total_area 要把所有形状的面积加起来，别漏算或重复算"
    assert total_area([]) == 0, "空列表时 total_area 应该返回 0"
    try:
        Shape()
        inst = False
    except TypeError:
        inst = True
    assert inst, "Shape 是抽象基类，直接 Shape() 必须抛 TypeError —— 检查 area 有没有用 @abstractmethod 装饰"
    assert hasattr(Square(1), "area"), "Square 必须提供 area()，才能兑现 Shape 定下的接口契约"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except TypeError as e:
    print("__FAIL__ 类的定义或实例化有问题：" + str(e))
except AttributeError as e:
    print("__FAIL__ 类里缺少属性或方法：" + str(e))
"""

LESSONS: list[dict] = [
    {
        "code": "py-oop",
        "stage": "Python 面向对象",
        "title": "继承与多态",
        "summary": "子类复用父类、改写行为，调用方只认父类接口",
        "supplementary": True,
        "definition": (
            "**继承**表达的是 **is-a（是一个）** 关系：`Dog` is an `Animal`，"
            "所以 `class Dog(Animal)` 是合理的。\n\n"
            "```python\n"
            "class Animal:\n"
            "    def __init__(self, name):\n"
            "        self.name = name\n\n"
            "    def speak(self):\n"
            "        return \"...\"\n\n"
            "class Dog(Animal):\n"
            "    def __init__(self, name):\n"
            "        super().__init__(name)   # 先把父类那部分初始化好\n\n"
            "    def speak(self):             # 重写（override）：在子类里定义同名方法\n"
            "        return \"汪汪\"\n"
            "```\n\n"
            "**为什么要 `super().__init__(name)`**：子类只要写了自己的 `__init__`，就把父类的构造"
            "**盖掉**了。父类 `Animal.__init__` 里的 `self.name = name` 没人执行，"
            "`dog.name` 就会 `AttributeError`。所以子类构造的**第一件事**是把父类该存的东西存好。\n\n"
            "**方法重写（override）**：子类里定义一个和父类**同名**的方法，就把它替换掉了；"
            "调用 `dog.speak()` 走子类的版本，`animal.speak()` 还是父类的版本。\n\n"
            "**多态**的价值：调用方**只认父类的方法名**（`speak()`），"
            "具体返回什么由对象的**实际类型**决定。所以 `chorus(animals)` 只管挨个调 `a.speak()`，"
            "以后新增 `Bird` 子类，这个函数**一行都不用改**。\n\n"
            "`isinstance(obj, Cls)` 判断对象是不是某个类的实例；子类的实例对它父类也为 `True`。"
        ),
        "plain": (
            "继承就是「**子类自动拥有父类的一切，再补上或改掉一部分**」。\n\n"
            "它表达的是 **is-a**：狗「是一种」动物，所以 `Dog(Animal)` 成立。"
            "但车和引擎是 **has-a**（车「有一个」引擎），这就**不该用继承**，"
            "而应该在 `Car.__init__` 里写 `self.engine = Engine()` —— 这就是常说的「**组合优于继承**」。\n\n"
            "⚠️ **最容易忘的一步**：子类只要写了 `__init__`，它就把父类的 `__init__` 顶掉了，"
            "必须自己**第一行**调 `super().__init__(...)`，先把父类要存的东西存好。"
            "就像盖房子先打地基，再装修自己那一层——地基没打，上面全塌。\n\n"
            "**多态的好处打个比方**：你开了一家「宠物店播音系统」，只要每只动物都会 `speak()`，"
            "喇叭就照着放，它根本不用知道笼子里是猫还是狗。下次进一批鹦鹉，"
            "只要鹦鹉也会 `speak()`，系统照用不误——**加新东西不用动老代码**，这就是多态。"
        ),
        "example": (
            "class Employee:\n"
            "    def __init__(self, name):\n"
            "        self.name = name\n"
            "\n"
            "    def work(self):\n"
            "        return f\"{self.name} 在做通用任务\"\n"
            "\n"
            "class Engineer(Employee):\n"
            "    def work(self):                 # 重写父类的 work\n"
            "        return f\"{self.name} 在写代码\"\n"
            "\n"
            "class Designer(Employee):\n"
            "    def work(self):\n"
            "        return f\"{self.name} 在画图\"\n"
            "\n"
            "def report_all(members):\n"
            "    # 只认父类的 work()，不关心具体是哪种员工 —— 这就是多态\n"
            "    return \" | \".join(m.work() for m in members)\n"
            "\n"
            "team = [Engineer(\"小明\"), Designer(\"小红\")]\n"
            "print(report_all(team))\n"
            "print(Engineer(\"小明\").work())\n"
            "print(isinstance(Engineer(\"小明\"), Employee), isinstance(Engineer(\"小明\"), Designer))"
        ),
        "example_output": "小明 在写代码 | 小红 在画图\n小明 在写代码\nTrue False",
        "pitfalls": [
            "**子类写了 `__init__` 却忘了 `super().__init__(...)`**：父类里赋值的属性不会存在，访问时突然 `AttributeError`。",
            "**把 has-a 关系写成继承**：车和引擎不是 is-a，硬继承会让类层次越来越乱；这种该用组合（把对象当属性持有）。",
            "**重写时把方法名拼错**：写成 `Speak` 就不是重写而是新增方法，父类的旧方法照旧生效，行为和你以为的不一样。",
            "**到处用 `isinstance` 判断类型**：一旦满屏 `if isinstance(x, Dog)`，就等于把多态又写回了 if-else；能让子类重写解决的，别用 isinstance。",
        ],
        "task": (
            "请按下面几步写：\n"
            "1. 定义基类 `Animal`：`__init__(self, name)` 把名字存到 `self.name`；`speak(self)` 返回字符串 `\"...\"`。\n"
            "2. 定义子类 `Dog(Animal)` 和 `Cat(Animal)`，**各自的 `__init__` 里第一行调用 `super().__init__(name)`**；"
            "分别**重写** `speak`，`Dog` 返回 `\"汪汪\"`，`Cat` 返回 `\"喵\"`。\n"
            "3. 实现函数 `chorus(animals)`：接收一个动物列表，把每只动物的 `speak()` 用 `\" \".join(...)` 拼成一个字符串返回。"
            "**这个函数不需要知道具体是什么动物**（这就是多态）；空列表时返回空字符串。\n"
            "4. 定义变量 `kinds = [isinstance(Dog(\"a\"), Animal), isinstance(Cat(\"a\"), Dog)]`。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "```\n"
            "class Animal:\n"
            "    def __init__(self, name):\n"
            "        self.name = name\n\n"
            "    def speak(self):\n"
            "        return \"...\"\n\n"
            "class Dog(Animal):\n"
            "    def __init__(self, name):\n"
            "        super().__init__(name)\n\n"
            "    def speak(self):\n"
            "        return \"汪汪\"\n\n"
            "def chorus(animals):\n"
            "    return \" \".join(a.speak() for a in animals)\n"
            "```\n"
            "`Cat` 照着 `Dog` 写即可；`kinds` 那一行直接用列表字面量写出两个 `isinstance` 的结果。"
        ),
        "checker": OOP_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "关于子类里的 `super().__init__(name)`，下面说法正确的是？",
                "options": [
                    "子类定义了自己的 __init__ 就必须调用它，否则父类里赋值的属性会缺失",
                    "可调可不调，效果完全一样",
                    "它是用来调用子类自己的 __init__",
                    "只有多重继承才需要调用它",
                ],
                "answer_index": 0,
                "explanation": "子类的 `__init__` 会覆盖父类的构造，不调 `super().__init__(...)` 父类那段初始化就不执行，属性会缺失。它调用的是父类的构造方法，而不是自己的。",
            },
            {
                "type": "choice",
                "stem": "使用多态最大的好处是什么？",
                "options": [
                    "调用方只依赖父类的方法名，新增子类时不用改调用方代码",
                    "让程序运行得更快",
                    "让子类可以少写几个属性",
                    "可以绕过类型检查",
                ],
                "answer_index": 0,
                "explanation": "多态让调用方只认父类接口，行为由实际类型决定；新增子类时老代码一行不用改。它和性能、属性数量、类型检查都无关。",
            },
            {
                "type": "judge",
                "stem": "如果 `Car` 需要持有一个 `Engine`，就应该让 `Car` 继承 `Engine`。",
                "answer": False,
                "explanation": "这是 has-a 关系而不是 is-a，应该用组合：在 `Car.__init__` 里 `self.engine = Engine()`。硬继承会把不相关的类绑在一起。",
            },
            {
                "type": "blank",
                "stem": "补全让子类调用父类构造方法的那一行：\nclass Dog(Animal):\n    def __init__(self, name):\n        ______.__init__(name)",
                "answer": "super()",
                "hint": "填调用父类的写法（注意带括号）",
                "explanation": "`super().__init__(name)` 会去调用父类的 `__init__`，把父类那部分初始化好。",
            },
        ],
    },
    {
        "code": "py-magic",
        "stage": "Python 面向对象",
        "title": "魔术方法与 @property",
        "summary": "让对象支持 print、== 等内置操作，还能只读派生",
        "supplementary": True,
        "definition": (
            "**魔术方法（dunder）**指前后各有两个下划线的方法，比如 `__init__`、`__repr__`、"
            "`__eq__`、`__len__`。它们不是你手动去调的，而是**当对象参与内置操作时，Python 自动去找它们**："
            "`print(obj)` 找 `__str__`，`repr(obj)` 找 `__repr__`，`a == b` 找 `__eq__`，`len(obj)` 找 `__len__`。\n\n"
            "- `__repr__`：给**开发者**看的，要求能**看出怎么重建这个对象**，例如 `Money(100, 'CNY')`。\n"
            "- `__str__`：给**用户**看的，可以写得好看，例如 `100 CNY`。\n"
            "- `print` **优先用 `__str__`，没有 `__str__` 就退回 `__repr__`**。\n\n"
            "默认的 `==` 比的是「**是不是同一个对象**」（内存地址），"
            "所以两个内容相同的 `Money(100, \"CNY\")` 默认并不相等。想按值比较，就得自己写 `__eq__`。\n\n"
            "**`@property`** 把一个方法变成「**像属性一样读**」：读的时候不加括号，写 `m.label` 就行。"
            "常用来做**只读派生值**（由已有属性算出来的值）或**加校验**。"
            "只写 getter、不写 setter 时，给它赋值会抛 `AttributeError`。\n\n"
            "**`@classmethod`** 第一个参数是**类** `cls`，常用来做「替代构造器」；"
            "**`@staticmethod`** 就是写在类里的一个普通函数，不接收 `self` / `cls`。"
        ),
        "plain": (
            "魔术方法就是**让你的对象「会用」Python 的内置语法**。\n\n"
            "不写 `__repr__` 时，`print(对象)` 会打出一串 `<__main__.Money object at 0x7f...>`，"
            "完全看不出里面是什么，调试时很痛苦；写了 `__repr__`，日志里一眼就能看懂。\n\n"
            "区分 `__repr__` 和 `__str__` 的一句话：**`__repr__` 是给同事看的，`__str__` 是给用户看的**。"
            "`repr()` 和交互式命令行用前者，`print` / `f\"{obj}\"` 优先用后者（没有就退回前者）。\n\n"
            "为什么默认的 `==` 不按值比较？因为 Python 不知道「对你这个类来说什么算相等」——"
            "两个 `Money` 是金额一样就算相等，还是连币种也必须一样？这得你自己用 `__eq__` 说清楚。\n\n"
            "`@property` 的价值是**造一个「假属性」**：调用方写 `m.label` 就像读普通字段一样自然，"
            "但它其实是每次现算出来的；而且因为它只有 getter、是只读的，谁也别想乱改。"
            "适合「由其他属性推导出来的值」，比如金额 + 币种拼出来的展示文本。"
        ),
        "example": (
            "class Point:\n"
            "    def __init__(self, x, y):\n"
            "        self.x = x\n"
            "        self.y = y\n"
            "\n"
            "    def __repr__(self):              # 给开发者看：能看出怎么重建这个对象\n"
            "        return f\"Point({self.x}, {self.y})\"\n"
            "\n"
            "    def __eq__(self, other):         # 默认 == 比的是\"是不是同一个对象\"\n"
            "        return self.x == other.x and self.y == other.y\n"
            "\n"
            "    @property\n"
            "    def quadrant(self):              # 像属性一样读，不用加括号\n"
            "        return 1 if self.x > 0 and self.y > 0 else 4\n"
            "\n"
            "    @classmethod\n"
            "    def origin(cls):                 # 第一个参数是类，常做替代构造器\n"
            "        return cls(0, 0)\n"
            "\n"
            "p = Point(3, 4)\n"
            "print(p)                             # 没写 __str__，print 退回 __repr__\n"
            "print(repr(p))\n"
            "print(p == Point(3, 4))\n"
            "print(p == Point(1, 1))\n"
            "print(p.quadrant)\n"
            "print(Point.origin())"
        ),
        "example_output": "Point(3, 4)\nPoint(3, 4)\nTrue\nFalse\n1\nPoint(0, 0)",
        "pitfalls": [
            "**`__repr__` 必须返回字符串**：返回了别的类型（比如直接 `return self.amount`）会 `TypeError`。",
            "**`__eq__` 少比了字段**：只比金额不比币种，`Money(100, 'CNY') == Money(100, 'USD')` 会错误地变成 True。",
            "**`@property` 当成普通方法用**：读的时候多写了括号 `m.label()`，或把函数对象拿去比较，都说明属性化没生效。",
            "**重写 `__eq__` 后对象变得不可哈希**：这样一来 `Money(...)` 不能再放进 set、也不能当字典的键；需要时还要补一个 `__hash__`。",
        ],
        "task": (
            "请写一个类 `Money`：\n"
            "1. `__init__(self, amount, currency)` 把金额和币种存成属性。\n"
            "2. 写 `__repr__`，返回形如 `Money(100, 'CNY')` 的字符串（**注意货币要用单引号包起来**）。\n"
            "3. 写 `__eq__`：**金额和币种都相等**才算相等。\n"
            "4. 写一个 `@property` 名为 `label`，返回形如 `\"100 CNY\"` 的字符串（金额、一个空格、币种）；"
            "它只有 getter，是**只读**的。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "```\n"
            "class Money:\n"
            "    def __init__(self, amount, currency):\n"
            "        self.amount = amount\n"
            "        self.currency = currency\n\n"
            "    def __repr__(self):\n"
            "        return f\"Money({self.amount}, '{self.currency}')\"\n\n"
            "    def __eq__(self, other):\n"
            "        return self.amount == other.amount and self.currency == other.currency\n\n"
            "    @property\n"
            "    def label(self):\n"
            "        return f\"{self.amount} {self.currency}\"\n"
            "```"
        ),
        "checker": MAGIC_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`print(obj)` 会优先调用对象的哪个方法？",
                "options": [
                    "先找 __str__，没有才退回 __repr__",
                    "先找 __repr__，没有才退回 __str__",
                    "__init__",
                    "__eq__",
                ],
                "answer_index": 0,
                "explanation": "`print` / `f\"{obj}\"` 优先用 `__str__`（面向用户），没有定义时退回 `__repr__`（面向开发者）。",
            },
            {
                "type": "choice",
                "stem": "两个内容相同的对象 `Money(100, 'CNY')`，在一行 `__eq__` 都没写时用 `==` 比较，结果是？",
                "options": [
                    "False，因为默认比的是是不是同一个对象",
                    "True，Python 会自动按属性值比较",
                    "报错 TypeError",
                    "取决于金额是不是 0",
                ],
                "answer_index": 0,
                "explanation": "默认 `==` 比较的是身份（内存地址），两个不同的对象默认不相等。要按值比较必须自己写 `__eq__`。",
            },
            {
                "type": "judge",
                "stem": "用 `@property` 装饰的方法，读取时要加括号，例如 `m.label()`。",
                "answer": False,
                "explanation": "`@property` 的目的就是让方法「像属性一样读」，直接用 `m.label`，不加括号；加括号是把返回的字符串又当函数调用了。",
            },
            {
                "type": "blank",
                "stem": "补全装饰器，让 `label` 能像属性一样被读取：\nclass M:\n    @______\n    def label(self):\n        return \"ok\"",
                "answer": "property",
                "hint": "填一个内置装饰器的名字",
                "explanation": "`@property` 把方法变成只读属性，读取时不用加括号。",
            },
        ],
    },
    {
        "code": "py-abc",
        "stage": "Python 面向对象",
        "title": "抽象基类与接口契约",
        "summary": "用 ABC 定接口契约，让缺方法的子类直接建不出来",
        "supplementary": True,
        "definition": (
            "**抽象基类（ABC）**的作用是**定契约**，不是为了复用代码。"
            "它规定「所有形状都必须会算面积」，但自己**不写**怎么算。\n\n"
            "```python\n"
            "from abc import ABC, abstractmethod\n\n"
            "class Shape(ABC):\n"
            "    @abstractmethod\n"
            "    def area(self):\n"
            "        ...          # 只声明接口，不写实现\n"
            "```\n\n"
            "规则：**只要还有抽象方法没被实现，这个类就不能被实例化** —— "
            "`Shape()` 会直接抛 `TypeError`；子类 `Square(Shape)` 如果忘了实现 `area`，"
            "`Square(...)` 也一样抛 `TypeError`。\n\n"
            "这比「写个普通基类、方法体里 `raise NotImplementedError`」好在**把错误提前到了最早的时刻**："
            "一半的问题在**创建对象**时就暴露了，而不是等到某次调用才炸。"
            "错误发现得越早，代价越小。\n\n"
            "还有个思路叫**鸭子类型（duck typing）**：「如果它走路像鸭子、叫起来像鸭子，那就是鸭子」——"
            "接口靠「**有没有这个方法**」来判断，而不是靠「继承自谁」。"
            "`typing.Protocol` 就是把这种结构化子类型写成可以检查的形式（了解即可）。"
        ),
        "plain": (
            "抽象基类就像**一份必须签的合同**：上面写着「每个形状都必须提供 `area()`」，"
            "谁签了（继承了 `Shape`）就必须把这条补齐，**写不全就别想上岗（实例化）**。\n\n"
            "为什么这样更好？举个例子：你写了普通基类，方法体是 `raise NotImplementedError(\"没实现\")`，"
            "结果子类忘了实现，程序能一路跑过去，直到某个深夜才在线上被调用时崩掉。"
            "换成 `@abstractmethod`，**在 `Square(...)` 那一刻就直接 `TypeError`**，"
            "根本不给它混进去的机会。\n\n"
            "⚠️ 注意抽象基类**不是为了省代码**。它几乎没有能复用的实现，"
            "它的价值是**约束**：保证「所有形状」这个集合里每个成员都真的会 `area()`，"
            "于是 `total_area(shapes)` 才能放心地挨个调 `s.area()`。\n\n"
            "`Protocol` / 鸭子类型是更松的一版：不需要真的继承谁，"
            "只要**凑巧有同名方法**就算符合这个接口——「不看血缘，只看会不会」。"
        ),
        "example": (
            "from abc import ABC, abstractmethod\n"
            "\n"
            "class Notifier(ABC):\n"
            "    @abstractmethod\n"
            "    def send(self, text):\n"
            "        ...                          # 只定契约，不写实现\n"
            "\n"
            "class ConsoleNotifier(Notifier):\n"
            "    def send(self, text):\n"
            "        return f\"打印到控制台: {text}\"\n"
            "\n"
            "class FileNotifier(Notifier):\n"
            "    def send(self, text):\n"
            "        return f\"写入文件: {text}\"\n"
            "\n"
            "def notify_all(notifiers, text):\n"
            "    # 只依赖 Notifier 定下的 send()，不关心具体是哪种通知器\n"
            "    return [n.send(text) for n in notifiers]\n"
            "\n"
            "print(notify_all([ConsoleNotifier(), FileNotifier()], \"构建完成\"))\n"
            "try:\n"
            "    Notifier()\n"
            "except TypeError:\n"
            "    print(\"抽象类不能被实例化\")"
        ),
        "example_output": "['打印到控制台: 构建完成', '写入文件: 构建完成']\n抽象类不能被实例化",
        "pitfalls": [
            "**忘了 `from abc import ABC, abstractmethod`**：`ABC` 或 `abstractmethod` 直接 `NameError`。",
            "**子类没有实现全部抽象方法**：实例化时抛 `TypeError`（不是等调用才报），这正是 ABC 想要的「提前拦截」。",
            "**抽象方法忘了加 `@abstractmethod`**：那它只是普通方法，基类照样能被实例化，契约形同虚设。",
            "**把抽象基类当成工具类**：它主要用来定接口；想复用实现应该用普通父类或组合，别硬塞进 ABC。",
        ],
        "task": (
            "请用 `abc` 模块完成：\n"
            "1. `from abc import ABC, abstractmethod`，定义抽象基类 `Shape(ABC)`，"
            "里面有一个装饰了 `@abstractmethod` 的方法 `area(self)`（方法体可以不写实现）。\n"
            "2. 定义 `Square(Shape)`：`__init__(self, side)` 存边长，`area(self)` 返回 `side * side`。\n"
            "3. 实现函数 `total_area(shapes)`：返回所有形状面积之和，"
            "用 `round(总和, 2)` 四舍五入到两位小数；空列表返回 0。"
        ),
        "setup": "",
        "starter": STARTER,
        "hint": (
            "```\n"
            "from abc import ABC, abstractmethod\n\n"
            "class Shape(ABC):\n"
            "    @abstractmethod\n"
            "    def area(self):\n"
            "        ...\n\n"
            "class Square(Shape):\n"
            "    def __init__(self, side):\n"
            "        self.side = side\n\n"
            "    def area(self):\n"
            "        return self.side * self.side\n\n"
            "def total_area(shapes):\n"
            "    return round(sum(s.area() for s in shapes), 2)\n"
            "```"
        ),
        "checker": ABC_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "关于抽象基类（ABC），下面说法正确的是？",
                "options": [
                    "它规定子类必须实现哪些方法，没实现的子类不能被实例化",
                    "它的主要目的是帮子类省下重复代码",
                    "只要继承了抽象基类，就自动实现了所有抽象方法",
                    "抽象方法必须用 raise NotImplementedError 来写",
                ],
                "answer_index": 0,
                "explanation": "ABC 是「定契约」，保证子类实现指定方法；没实现就实例化会抛 TypeError。它的价值是约束而非复用，`@abstractmethod` 也不需要手写 `raise NotImplementedError`。",
            },
            {
                "type": "choice",
                "stem": "子类继承了 `Shape(ABC)`，但没实现抽象方法 `area`，此时执行 `Square()` 会怎样？",
                "options": [
                    "抛 TypeError，提示不能实例化抽象类",
                    "正常创建，只是 area() 返回 None",
                    "抛 AttributeError",
                    "什么都不发生，照常创建",
                ],
                "answer_index": 0,
                "explanation": "只要还有抽象方法没实现，实例化就抛 `TypeError`。这正是 ABC 提前拦截错误的方式——不等到调用才炸。",
            },
            {
                "type": "judge",
                "stem": "鸭子类型认为，一个对象只要提供了需要的方法，就可以当作该接口使用，不一定非要继承某个基类。",
                "answer": True,
                "explanation": "「看会不会，不看血缘」。接口由「有没有这个方法」决定，`Protocol` 就是把这种结构化子类型写出来便于检查。",
            },
            {
                "type": "blank",
                "stem": "补全装饰器，让 `area` 成为必须由子类实现的抽象方法：\nclass Shape(ABC):\n    @______\n    def area(self):\n        ...",
                "answer": "abstractmethod",
                "hint": "填 abc 模块提供的那个装饰器名",
                "explanation": "`@abstractmethod` 标记抽象方法，子类不实现就无法实例化。",
            },
        ],
    },
]
