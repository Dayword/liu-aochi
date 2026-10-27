"""每课开头的「一句话」+ 手绘知识图数据。

为什么要单独放一个文件：
- 21 个 `learn_*.py` 里塞的是题目、判定器、例子，改动它们风险高（判定器一改就得重跑自检）；
- 这里是**纯展示层内容**，课程代码（code）当 key，和题库解耦，加一课不加这里也不会报错。

数据结构
--------
```python
"py-var": {
    "oneliner": "一句话：讲什么 + 学完能做什么",
    "center": "变量",                      # 图中心那个圈里的字，2~6 字最佳
    "nodes": [
        {"id": "assign", "label": "赋值 =", "kind": "core", "zone": "t"},
        {"id": "next-type", "label": "数据类型", "kind": "next",
         "zone": "r", "code": "py-type"},
    ],
    "edges": [
        {"a": "center", "b": "assign", "label": "第一步"},
    ],
}
```

- `kind`：`core` 本课内部知识点 / `prev` 前置课 / `next` 后续课 / `side` 跨科目或工程旁支。
- `zone`：节点挂在中心的哪个方向，八个方位 `t tr r br b bl l tl`。
  手写定位而不是自动布局，是为了让每张图的重心可控、不会两个球撞在一起。
- `code`：填了就能点，跳到那一课（`learn.py` 会校验它真的存在）。
- `edges.a` / `edges.b` 除了节点 id，还可以写 `"center"` 指中心节点。

排版约定（渲染器 `KnowledgeSketch.tsx` 按这个来）：
- `core` 画在内圈、实线圈 + 靛蓝色；`prev/next` 画在外圈、虚线圈；`side` 用琥珀色。
- 一句「话」不要超过 60 个汉字，图上节点标签不超过 8 个字。
- 每课固定 3 个内圈 `core`（占 `t` / `bl` / `br`）+ 外圈 1~3 个 `prev/next/side`
  （占 `l` / `r` / `b`）。**同一个圈里不能有两个节点抢同一个 zone**，否则必然叠在一起，
  `learn_sketch_check.py` 会直接判失败。

覆盖进度：**135 / 135 课全部铺满**（2026-10-27 先做 Python 前 10 课试点，确认口径后按同一
标准铺完 12 科）。新增课程时：
1. 在这个文件里补一条，`code` 必须和 `learn*.py` 里的完全一致；
2. 跑 `python learn_sketch_check.py`，退出码 0 才算过；
3. 没写也不会报错 —— `sketch_of()` 返回 None，前端自动退回只显示 `summary`。
"""

SKETCHES: dict[str, dict] = {
    # ---------- Python 基础 ----------
    "py-var": {
        "oneliner": (
            "变量就是给数据起个名字，用「名字 = 值」把结果存下来反复使用；"
            "学完你能正确地定义变量、按规则命名，并分清常量和普通变量。"
        ),
        "center": "变量",
        "nodes": [
            {"id": "assign", "label": "赋值 =", "kind": "core", "zone": "t"},
            {"id": "naming", "label": "命名规则", "kind": "core", "zone": "bl"},
            {"id": "const", "label": "常量约定", "kind": "core", "zone": "br"},
            {"id": "t-type", "label": "数据类型", "kind": "next", "zone": "r", "code": "py-type"},
            {"id": "s-print", "label": "print 输出", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "assign", "label": "第一步"},
            {"a": "center", "b": "naming", "label": "不合规就报错"},
            {"a": "center", "b": "const", "label": "全大写"},
            {"a": "center", "b": "t-type", "label": "值都有类型"},
            {"a": "center", "b": "s-print", "label": "看结果"},
        ],
    },
    "py-type": {
        "oneliner": (
            "Python 的每个值都有类型，常见的是整数、小数、字符串和布尔；"
            "学完你能判断一个值是什么类型、用 int()/str() 互相转换，并在拼接前先统一类型。"
        ),
        "center": "数据类型",
        "nodes": [
            {"id": "basic", "label": "四种基本类型", "kind": "core", "zone": "t"},
            {"id": "cast", "label": "类型转换", "kind": "core", "zone": "bl"},
            {"id": "error", "label": "混用会报错", "kind": "core", "zone": "br"},
            {"id": "p-var", "label": "变量", "kind": "prev", "zone": "l", "code": "py-var"},
            {"id": "n-op", "label": "运算符", "kind": "next", "zone": "r", "code": "py-op"},
        ],
        "edges": [
            {"a": "center", "b": "basic", "label": "四种常见类型"},
            {"a": "center", "b": "cast", "label": "int() str()"},
            {"a": "center", "b": "error", "label": "不转换就算不动"},
            {"a": "center", "b": "p-var", "label": "变量里装的就是它"},
            {"a": "center", "b": "n-op", "label": "同类型才能运算"},
        ],
    },
    "py-op": {
        "oneliner": (
            "运算符决定两个值怎么算：加减乘除、比较大小、判断真假，其中整除和取余最容易写错；"
            "学完你能写出算平均分、判奇偶、拆出个位十位的表达式。"
        ),
        "center": "运算符",
        "nodes": [
            {"id": "math", "label": "算术 + - * /", "kind": "core", "zone": "t"},
            {"id": "mod", "label": "整除与取余", "kind": "core", "zone": "bl"},
            {"id": "cmp", "label": "比较与逻辑", "kind": "core", "zone": "br"},
            {"id": "p-type", "label": "数据类型", "kind": "prev", "zone": "l", "code": "py-type"},
            {"id": "n-if", "label": "选择结构", "kind": "next", "zone": "r", "code": "py-if"},
        ],
        "edges": [
            {"a": "center", "b": "math", "label": "算数"},
            {"a": "center", "b": "mod", "label": "// 和 %"},
            {"a": "center", "b": "cmp", "label": "得到 True/False"},
            {"a": "center", "b": "p-type", "label": "作用于同类型"},
            {"a": "center", "b": "n-if", "label": "比较结果是条件"},
        ],
    },
    "py-str": {
        "oneliner": (
            "字符串是最常用的数据类型，核心是三件事：拼接、切片、格式化；"
            "学完你能从一段文本里取出想要的那一段，并拼出一句带变量的完整话。"
        ),
        "center": "字符串",
        "nodes": [
            {"id": "concat", "label": "拼接与重复", "kind": "core", "zone": "t"},
            {"id": "slice", "label": "切片 [a:b]", "kind": "core", "zone": "bl"},
            {"id": "fstr", "label": "f-string", "kind": "core", "zone": "br"},
            {"id": "p-type", "label": "数据类型", "kind": "prev", "zone": "l", "code": "py-type"},
            {"id": "n-list", "label": "列表", "kind": "next", "zone": "r", "code": "py-list"},
        ],
        "edges": [
            {"a": "center", "b": "concat", "label": "串起来"},
            {"a": "center", "b": "slice", "label": "取一段"},
            {"a": "center", "b": "fstr", "label": "填变量"},
            {"a": "center", "b": "p-type", "label": "str 类型"},
            {"a": "center", "b": "n-list", "label": "切片思想通用"},
        ],
    },
    "py-if": {
        "oneliner": (
            "if / elif / else 让程序按条件走不同分支，从上往下第一个成立的分支赢；"
            "学完你能把「如果……否则……」写成代码，并避开条件写反、顺序写错的坑。"
        ),
        "center": "选择结构",
        "nodes": [
            {"id": "if", "label": "if 条件", "kind": "core", "zone": "t"},
            {"id": "elif", "label": "elif 多分支", "kind": "core", "zone": "bl"},
            {"id": "else", "label": "else 兜底", "kind": "core", "zone": "br"},
            {"id": "p-op", "label": "运算符", "kind": "prev", "zone": "l", "code": "py-op"},
            {"id": "n-while", "label": "while 循环", "kind": "next", "zone": "r", "code": "py-while"},
        ],
        "edges": [
            {"a": "center", "b": "if", "label": "条件为真才进"},
            {"a": "center", "b": "elif", "label": "依次判断"},
            {"a": "center", "b": "else", "label": "都不成立"},
            {"a": "center", "b": "p-op", "label": "比较得出真假"},
            {"a": "center", "b": "n-while", "label": "循环也要判断"},
        ],
    },
    "py-while": {
        "oneliner": (
            "while 在条件成立时反复执行同一段代码，条件一旦变假就退出；"
            "学完你能写出倒计时、重试这类循环，并知道死循环是怎么来的、怎么避开。"
        ),
        "center": "while 循环",
        "nodes": [
            {"id": "cond", "label": "循环条件", "kind": "core", "zone": "t"},
            {"id": "body", "label": "循环体", "kind": "core", "zone": "bl"},
            {"id": "stuck", "label": "死循环", "kind": "core", "zone": "br"},
            {"id": "p-if", "label": "选择结构", "kind": "prev", "zone": "l", "code": "py-if"},
            {"id": "n-for", "label": "for 循环", "kind": "next", "zone": "r", "code": "py-for"},
        ],
        "edges": [
            {"a": "center", "b": "cond", "label": "每轮先判断"},
            {"a": "center", "b": "body", "label": "缩进的这几行"},
            {"a": "center", "b": "stuck", "label": "条件永不为假"},
            {"a": "center", "b": "p-if", "label": "条件靠 if 那套"},
            {"a": "center", "b": "n-for", "label": "次数已知就用它"},
        ],
    },
    "py-for": {
        "oneliner": (
            "for 把一串东西挨个取出来处理一遍，range 负责生成一串数字；"
            "学完你能遍历列表、按固定次数重复，并分清什么时候该用 for、什么时候该用 while。"
        ),
        "center": "for 循环",
        "nodes": [
            {"id": "iter", "label": "遍历元素", "kind": "core", "zone": "t"},
            {"id": "range", "label": "range 数字序列", "kind": "core", "zone": "bl"},
            {"id": "jump", "label": "break / continue", "kind": "core", "zone": "br"},
            {"id": "p-while", "label": "while 循环", "kind": "prev", "zone": "l", "code": "py-while"},
            {"id": "n-list", "label": "列表", "kind": "next", "zone": "r", "code": "py-list"},
        ],
        "edges": [
            {"a": "center", "b": "iter", "label": "一次一个"},
            {"a": "center", "b": "range", "label": "只管次数"},
            {"a": "center", "b": "jump", "label": "中途跳走"},
            {"a": "center", "b": "p-while", "label": "次数已知用它"},
            {"a": "center", "b": "n-list", "label": "最常遍历的东西"},
        ],
    },
    "py-list": {
        "oneliner": (
            "列表是一排有顺序、能改动的数据，用下标取值、用方法增删改、用循环挨个处理；"
            "学完你能把一批同类数据存进列表，并完成取子集、排序、统计这几件常做的事。"
        ),
        "center": "列表",
        "nodes": [
            {"id": "index", "label": "下标与切片", "kind": "core", "zone": "t"},
            {"id": "edit", "label": "增删改", "kind": "core", "zone": "bl"},
            {"id": "sort", "label": "排序与遍历", "kind": "core", "zone": "br"},
            {"id": "p-for", "label": "for 循环", "kind": "prev", "zone": "l", "code": "py-for"},
            {"id": "n-tuple", "label": "元组与集合", "kind": "next", "zone": "r", "code": "py-tuple-set"},
            {"id": "s-numpy", "label": "NumPy 数组", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "index", "label": "从 0 开始"},
            {"a": "center", "b": "edit", "label": "append / pop"},
            {"a": "center", "b": "sort", "label": "sort / sorted"},
            {"a": "center", "b": "p-for", "label": "用来遍历"},
            {"a": "center", "b": "n-tuple", "label": "想要不可改就用元组"},
            {"a": "center", "b": "s-numpy", "label": "数据分析里的升级版"},
        ],
    },
    "py-tuple-set": {
        "oneliner": (
            "元组是不可变的有序序列，集合是自动去重、能算交并差的无序容器；"
            "学完你能在多返回值、固定配置、去重统计这几种场景里一眼选对结构。"
        ),
        "center": "元组与集合",
        "nodes": [
            {"id": "tuple", "label": "元组不可变", "kind": "core", "zone": "t"},
            {"id": "set", "label": "集合去重", "kind": "core", "zone": "bl"},
            {"id": "ops", "label": "交并差运算", "kind": "core", "zone": "br"},
            {"id": "p-list", "label": "列表", "kind": "prev", "zone": "l", "code": "py-list"},
            {"id": "n-dict", "label": "字典", "kind": "next", "zone": "r", "code": "py-dict"},
        ],
        "edges": [
            {"a": "center", "b": "tuple", "label": "建好就不能改"},
            {"a": "center", "b": "set", "label": "重复自动消失"},
            {"a": "center", "b": "ops", "label": "& | -"},
            {"a": "center", "b": "p-list", "label": "列表能改，它不能"},
            {"a": "center", "b": "n-dict", "label": "都要可哈希的键"},
        ],
    },
    "py-dict": {
        "oneliner": (
            "字典用 key 直接找到 value，是 Python 里描述一个对象最自然的结构；"
            "学完你能用字典存结构化数据，并在 JSON 和接口参数里读写它。"
        ),
        "center": "字典",
        "nodes": [
            {"id": "kv", "label": "键值对", "kind": "core", "zone": "t"},
            {"id": "crud", "label": "取值与增删改", "kind": "core", "zone": "bl"},
            {"id": "nest", "label": "嵌套与遍历", "kind": "core", "zone": "br"},
            {"id": "p-list", "label": "列表", "kind": "prev", "zone": "l", "code": "py-list"},
            {"id": "n-func", "label": "函数", "kind": "next", "zone": "r", "code": "py-func"},
            {"id": "s-json", "label": "JSON / 接口参数", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "kv", "label": "key → value"},
            {"a": "center", "b": "crud", "label": "get / pop"},
            {"a": "center", "b": "nest", "label": "字典套字典"},
            {"a": "center", "b": "p-list", "label": "列表装字典"},
            {"a": "center", "b": "n-func", "label": "**kwargs 就是字典"},
            {"a": "center", "b": "s-json", "label": "几乎一一对应"},
        ],
    },
    # ---------- Python 基础：函数与容器 ----------
    "py-func": {
        "oneliner": (
            "函数把一段逻辑装进盒子：用参数喂数据、用 return 拿结果；"
            "学完你能把长脚本拆成能复用的零件，改一处不影响别处。"
        ),
        "center": "函数",
        "nodes": [
            {"id": "define", "label": "def 定义", "kind": "core", "zone": "t"},
            {"id": "io", "label": "参数与 return", "kind": "core", "zone": "bl"},
            {"id": "call", "label": "调用", "kind": "core", "zone": "br"},
            {"id": "p-dict", "label": "字典", "kind": "prev", "zone": "l", "code": "py-dict"},
            {"id": "n-none", "label": "None 与真值", "kind": "next", "zone": "r", "code": "py-none"},
        ],
        "edges": [
            {"a": "center", "b": "define", "label": "先定义再使用"},
            {"a": "center", "b": "io", "label": "进和出"},
            {"a": "center", "b": "call", "label": "名字加括号"},
            {"a": "center", "b": "p-dict", "label": "数据装进函数"},
            {"a": "center", "b": "n-none", "label": "不 return 就是 None"},
        ],
    },
    "py-none": {
        "oneliner": (
            "None 表示「什么都没有」，和 0、空字符串一样被当成假值，但两者完全不是一回事；"
            "学完你能用 is None 正确判断缺失，不再被 or 坑。"
        ),
        "center": "None 与真值",
        "nodes": [
            {"id": "falsy", "label": "假值清单", "kind": "core", "zone": "t"},
            {"id": "isnone", "label": "is None", "kind": "core", "zone": "bl"},
            {"id": "ortrap", "label": "or 的陷阱", "kind": "core", "zone": "br"},
            {"id": "p-func", "label": "函数", "kind": "prev", "zone": "l", "code": "py-func"},
            {"id": "n-lambda", "label": "lambda 与排序", "kind": "next", "zone": "r", "code": "py-lambda"},
            {"id": "s-null", "label": "接口返回 null", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "falsy", "label": "0 / '' / []"},
            {"a": "center", "b": "isnone", "label": "判空用它"},
            {"a": "center", "b": "ortrap", "label": "0 也被当成空"},
            {"a": "center", "b": "p-func", "label": "没 return 就返回它"},
            {"a": "center", "b": "n-lambda", "label": "key 里要先排除"},
            {"a": "center", "b": "s-null", "label": "JSON 里叫 null"},
        ],
    },
    "py-lambda": {
        "oneliner": (
            "lambda 是只有一行的匿名函数，配上 sorted 的 key 就能写出多级排序；"
            "学完你能按任意字段给列表排序，不用为排序专门写一个 def。"
        ),
        "center": "lambda 与排序",
        "nodes": [
            {"id": "anon", "label": "匿名函数", "kind": "core", "zone": "t"},
            {"id": "key", "label": "sorted key", "kind": "core", "zone": "bl"},
            {"id": "multi", "label": "多级排序", "kind": "core", "zone": "br"},
            {"id": "p-func", "label": "函数", "kind": "prev", "zone": "l", "code": "py-func"},
            {"id": "n-iter", "label": "遍历工具", "kind": "next", "zone": "r", "code": "py-iterate"},
            {"id": "s-data", "label": "给数据排序", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "anon", "label": "一句话一个函数"},
            {"a": "center", "b": "key", "label": "按什么比大小"},
            {"a": "center", "b": "multi", "label": "元组越靠前越优先"},
            {"a": "center", "b": "p-func", "label": "它的简写"},
            {"a": "center", "b": "n-iter", "label": "常一起用"},
            {"a": "center", "b": "s-data", "label": "排行榜就靠它"},
        ],
    },
    "py-iterate": {
        "oneliner": (
            "enumerate 同时给下标、zip 把两个列表并排走、map 和 filter 一行批量处理；"
            "学完你能彻底告别 range(len()) 那套笨写法。"
        ),
        "center": "遍历工具",
        "nodes": [
            {"id": "enum", "label": "enumerate", "kind": "core", "zone": "t"},
            {"id": "zip", "label": "zip 并排", "kind": "core", "zone": "bl"},
            {"id": "mf", "label": "map / filter", "kind": "core", "zone": "br"},
            {"id": "p-for", "label": "for 循环", "kind": "prev", "zone": "l", "code": "py-for"},
            {"id": "n-comp", "label": "推导式", "kind": "next", "zone": "r", "code": "py-comprehension"},
            {"id": "s-align", "label": "两个列表对齐", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "enum", "label": "下标和值一起拿"},
            {"a": "center", "b": "zip", "label": "按位置配对"},
            {"a": "center", "b": "mf", "label": "函数批量套"},
            {"a": "center", "b": "p-for", "label": "都在 for 里用"},
            {"a": "center", "b": "n-comp", "label": "推导式更长用"},
            {"a": "center", "b": "s-align", "label": "长度不等会截断"},
        ],
    },
    "py-scope": {
        "oneliner": (
            "变量在哪一层生效、列表传进函数会不会被改、深浅拷贝差在哪——这三个坑一次讲清；"
            "学完你能预判函数调用完，原数据到底变没变。"
        ),
        "center": "作用域与拷贝",
        "nodes": [
            {"id": "scope", "label": "局部 / 全局", "kind": "core", "zone": "t"},
            {"id": "mut", "label": "可变对象传参", "kind": "core", "zone": "bl"},
            {"id": "copy", "label": "深浅拷贝", "kind": "core", "zone": "br"},
            {"id": "p-func", "label": "函数", "kind": "prev", "zone": "l", "code": "py-func"},
            {"id": "n-comp", "label": "推导式", "kind": "next", "zone": "r", "code": "py-comprehension"},
            {"id": "s-default", "label": "默认参数别用列表", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "scope", "label": "函数内部是另一层"},
            {"a": "center", "b": "mut", "label": "传的是引用"},
            {"a": "center", "b": "copy", "label": "copy 与 deepcopy"},
            {"a": "center", "b": "p-func", "label": "调用时才生效"},
            {"a": "center", "b": "n-comp", "label": "推导式有独立作用域"},
            {"a": "center", "b": "s-default", "label": "会被共享"},
        ],
    },
    "py-comprehension": {
        "oneliner": (
            "推导式把「遍历 + 筛选 + 变形」压成一行，列表、字典、集合都能用；"
            "学完你能用一行写出过滤后的新列表，读起来比循环更清楚。"
        ),
        "center": "推导式",
        "nodes": [
            {"id": "list", "label": "列表推导", "kind": "core", "zone": "t"},
            {"id": "cond", "label": "条件筛选", "kind": "core", "zone": "bl"},
            {"id": "dictset", "label": "字典 / 集合推导", "kind": "core", "zone": "br"},
            {"id": "p-for", "label": "for 循环", "kind": "prev", "zone": "l", "code": "py-for"},
            {"id": "n-kwargs", "label": "*args 与 **kwargs", "kind": "next", "zone": "r", "code": "py-func-adv"},
            {"id": "s-clean", "label": "数据清洗", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "list", "label": "[x for x in ...]"},
            {"a": "center", "b": "cond", "label": "if 放后面"},
            {"a": "center", "b": "dictset", "label": "{k: v ...}"},
            {"a": "center", "b": "p-for", "label": "循环的紧凑写法"},
            {"a": "center", "b": "n-kwargs", "label": "常一起出现在函数里"},
            {"a": "center", "b": "s-clean", "label": "过滤脏数据"},
        ],
    },
    "py-func-adv": {
        "oneliner": (
            "*args 收任意多个位置参数、**kwargs 收任意多个关键字参数，默认值别用可变对象；"
            "学完你能写出适配各种调用方式的工具函数。"
        ),
        "center": "灵活的函数",
        "nodes": [
            {"id": "args", "label": "*args", "kind": "core", "zone": "t"},
            {"id": "kwargs", "label": "**kwargs", "kind": "core", "zone": "bl"},
            {"id": "default", "label": "默认值陷阱", "kind": "core", "zone": "br"},
            {"id": "p-func", "label": "函数", "kind": "prev", "zone": "l", "code": "py-func"},
            {"id": "n-exc", "label": "异常处理", "kind": "next", "zone": "r", "code": "py-exception"},
            {"id": "s-tool", "label": "工具函数入参", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "args", "label": "打包成元组"},
            {"a": "center", "b": "kwargs", "label": "打包成字典"},
            {"a": "center", "b": "default", "label": "写 None 再判空"},
            {"a": "center", "b": "p-func", "label": "函数的进阶形态"},
            {"a": "center", "b": "n-exc", "label": "参数不对就抛异常"},
            {"a": "center", "b": "s-tool", "label": "Agent 工具就靠它"},
        ],
    },
    "py-exception": {
        "oneliner": (
            "try / except / else / finally 让程序出错时还能优雅收场；"
            "学完你能捕获指定异常、带上有用信息，而不是让整个服务直接崩掉。"
        ),
        "center": "异常处理",
        "nodes": [
            {"id": "try", "label": "try / except", "kind": "core", "zone": "t"},
            {"id": "types", "label": "认清异常类型", "kind": "core", "zone": "bl"},
            {"id": "finally", "label": "finally 收尾", "kind": "core", "zone": "br"},
            {"id": "p-kwargs", "label": "灵活的函数", "kind": "prev", "zone": "l", "code": "py-func-adv"},
            {"id": "n-class", "label": "类与对象", "kind": "next", "zone": "r", "code": "py-class"},
            {"id": "s-agent", "label": "Agent 必须兜底", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "try", "label": "出错就跳这里"},
            {"a": "center", "b": "types", "label": "别一把抓 Exception"},
            {"a": "center", "b": "finally", "label": "关文件关连接"},
            {"a": "center", "b": "p-kwargs", "label": "参数不合法先抛"},
            {"a": "center", "b": "n-class", "label": "自定义异常类"},
            {"a": "center", "b": "s-agent", "label": "模型调用随时会挂"},
        ],
    },
    "py-class": {
        "oneliner": (
            "类是把数据和行为打包在一起的模板，__init__ 决定对象怎么被创建；"
            "学完你能定义类、创建对象，每个对象的属性互不干扰。"
        ),
        "center": "类与对象",
        "nodes": [
            {"id": "inst", "label": "class 与实例", "kind": "core", "zone": "t"},
            {"id": "init", "label": "__init__", "kind": "core", "zone": "bl"},
            {"id": "self", "label": "self 与属性", "kind": "core", "zone": "br"},
            {"id": "p-func", "label": "函数", "kind": "prev", "zone": "l", "code": "py-func"},
            {"id": "n-gen", "label": "生成器", "kind": "next", "zone": "r", "code": "py-generator"},
            {"id": "s-model", "label": "给数据建模", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "inst", "label": "模板与成品"},
            {"a": "center", "b": "init", "label": "创建时执行一次"},
            {"a": "center", "b": "self", "label": "指对象自己"},
            {"a": "center", "b": "p-func", "label": "方法就是函数"},
            {"a": "center", "b": "n-gen", "label": "容器也能自定义"},
            {"a": "center", "b": "s-model", "label": "一个对象一组字段"},
        ],
    },
    "py-generator": {
        "oneliner": (
            "yield 让函数变成「边算边给」的生产者，不把结果一次性塞进内存；"
            "学完你能写出省内存的遍历，也看得懂大模型的流式输出。"
        ),
        "center": "生成器",
        "nodes": [
            {"id": "yield", "label": "yield", "kind": "core", "zone": "t"},
            {"id": "lazy", "label": "惰性求值", "kind": "core", "zone": "bl"},
            {"id": "proto", "label": "迭代器协议", "kind": "core", "zone": "br"},
            {"id": "p-for", "label": "for 循环", "kind": "prev", "zone": "l", "code": "py-for"},
            {"id": "n-deco", "label": "装饰器", "kind": "next", "zone": "r", "code": "py-decorator"},
            {"id": "s-stream", "label": "大模型流式输出", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "yield", "label": "给一个停一下"},
            {"a": "center", "b": "lazy", "label": "要了才算"},
            {"a": "center", "b": "proto", "label": "__iter__ / __next__"},
            {"a": "center", "b": "p-for", "label": "只能遍历一次"},
            {"a": "center", "b": "n-deco", "label": "自己写 __next__"},
            {"a": "center", "b": "s-stream", "label": "一段一段吐字"},
        ],
    },
    # ---------- Python 进阶：面向对象与标准库 ----------
    "py-decorator": {
        "oneliner": (
            "装饰器是「接收函数、返回新函数」的函数，@ 只是语法糖；"
            "学完你能给函数加上计时、重试、日志，而不改动原函数一行代码。"
        ),
        "center": "装饰器",
        "nodes": [
            {"id": "fcf", "label": "函数是一等公民", "kind": "core", "zone": "t"},
            {"id": "closure", "label": "闭包", "kind": "core", "zone": "bl"},
            {"id": "sugar", "label": "@ 语法糖", "kind": "core", "zone": "br"},
            {"id": "p-gen", "label": "生成器", "kind": "prev", "zone": "l", "code": "py-generator"},
            {"id": "n-module", "label": "模块与包", "kind": "next", "zone": "r", "code": "py-module"},
            {"id": "s-retry", "label": "重试与限流", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "fcf", "label": "能当参数传"},
            {"a": "center", "b": "closure", "label": "记住外层变量"},
            {"a": "center", "b": "sugar", "label": "等价于手动包装"},
            {"a": "center", "b": "p-gen", "label": "都能包一层"},
            {"a": "center", "b": "n-module", "label": "跨文件复用"},
            {"a": "center", "b": "s-retry", "label": "失败自动重来"},
        ],
    },
    "py-module": {
        "oneliner": (
            "用 import 引入别人写好的库，用 venv 给每个项目一套独立依赖；"
            "学完你能组织多文件项目，也不会再「换台电脑就跑不起来」。"
        ),
        "center": "模块与包",
        "nodes": [
            {"id": "import", "label": "import 机制", "kind": "core", "zone": "t"},
            {"id": "pkg", "label": "包与 __init__", "kind": "core", "zone": "bl"},
            {"id": "venv", "label": "venv 与 pip", "kind": "core", "zone": "br"},
            {"id": "p-deco", "label": "装饰器", "kind": "prev", "zone": "l", "code": "py-decorator"},
            {"id": "n-file", "label": "文件读写", "kind": "next", "zone": "r", "code": "py-file"},
            {"id": "s-req", "label": "requirements.txt", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "import", "label": "按路径找文件"},
            {"a": "center", "b": "pkg", "label": "一层层文件夹"},
            {"a": "center", "b": "venv", "label": "项目之间互不污染"},
            {"a": "center", "b": "p-deco", "label": "拆到单独文件"},
            {"a": "center", "b": "n-file", "label": "标准库也要 import"},
            {"a": "center", "b": "s-req", "label": "把版本钉住"},
        ],
    },
    "py-file": {
        "oneliner": (
            "open 配合 with 读写文本，pathlib 统一处理跨平台路径；"
            "学完你能把程序结果存成文件、再从文件读回来，中文也不会乱码。"
        ),
        "center": "文件读写",
        "nodes": [
            {"id": "open", "label": "with open", "kind": "core", "zone": "t"},
            {"id": "mode", "label": "读写模式", "kind": "core", "zone": "bl"},
            {"id": "path", "label": "pathlib 路径", "kind": "core", "zone": "br"},
            {"id": "p-module", "label": "模块与包", "kind": "prev", "zone": "l", "code": "py-module"},
            {"id": "n-oop", "label": "继承与多态", "kind": "next", "zone": "r", "code": "py-oop"},
            {"id": "s-utf8", "label": "encoding='utf-8'", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "open", "label": "自动关文件"},
            {"a": "center", "b": "mode", "label": "r / w / a"},
            {"a": "center", "b": "path", "label": "Windows 和 Linux 都能用"},
            {"a": "center", "b": "p-module", "label": "写日志先会写文件"},
            {"a": "center", "b": "n-oop", "label": "文件对象就是类"},
            {"a": "center", "b": "s-utf8", "label": "不写就容易乱码"},
        ],
    },
    "py-oop": {
        "oneliner": (
            "子类继承父类的属性和方法，也能重写其中一部分；调用方只认父类接口，"
            "运行时自动走子类实现，这就是多态。学完你能用继承消掉重复代码。"
        ),
        "center": "继承与多态",
        "nodes": [
            {"id": "sub", "label": "class 子类", "kind": "core", "zone": "t"},
            {"id": "super", "label": "super()", "kind": "core", "zone": "bl"},
            {"id": "override", "label": "方法重写", "kind": "core", "zone": "br"},
            {"id": "p-class", "label": "类与对象", "kind": "prev", "zone": "l", "code": "py-class"},
            {"id": "n-magic", "label": "魔术方法", "kind": "next", "zone": "r", "code": "py-magic"},
            {"id": "s-strategy", "label": "换实现不改调用", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "sub", "label": "class Dog(Animal)"},
            {"a": "center", "b": "super", "label": "先跑父类的初始化"},
            {"a": "center", "b": "override", "label": "同名就覆盖"},
            {"a": "center", "b": "p-class", "label": "单个类的升级版"},
            {"a": "center", "b": "n-magic", "label": "父类也能定协议"},
            {"a": "center", "b": "s-strategy", "label": "同一接口多种实现"},
        ],
    },
    "py-magic": {
        "oneliner": (
            "`__str__`、`__eq__`、`__len__` 决定对象在 print、== 下的表现，"
            "@property 让方法能当属性用；学完你能写出用起来像内置类型的对象。"
        ),
        "center": "魔术方法",
        "nodes": [
            {"id": "str", "label": "__str__ / __repr__", "kind": "core", "zone": "t"},
            {"id": "eq", "label": "__eq__ 与 __len__", "kind": "core", "zone": "bl"},
            {"id": "prop", "label": "@property", "kind": "core", "zone": "br"},
            {"id": "p-oop", "label": "继承与多态", "kind": "prev", "zone": "l", "code": "py-oop"},
            {"id": "n-abc", "label": "抽象基类", "kind": "next", "zone": "r", "code": "py-abc"},
            {"id": "s-debug", "label": "调试时看清对象", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "str", "label": "print 时调它"},
            {"a": "center", "b": "eq", "label": "内置操作也能接管"},
            {"a": "center", "b": "prop", "label": "只读派生属性"},
            {"a": "center", "b": "p-oop", "label": "父类定义子类实现"},
            {"a": "center", "b": "n-abc", "label": "协议的一种"},
            {"a": "center", "b": "s-debug", "label": "别再打印一串内存地址"},
        ],
    },
    "py-abc": {
        "oneliner": (
            "ABC 加 @abstractmethod 定义「必须实现哪些方法」，漏一个就当场报错；"
            "学完你能给一组实现类定下统一接口，插件式扩展不怕写漏。"
        ),
        "center": "接口契约",
        "nodes": [
            {"id": "abc", "label": "ABC 基类", "kind": "core", "zone": "t"},
            {"id": "abstract", "label": "@abstractmethod", "kind": "core", "zone": "bl"},
            {"id": "contract", "label": "统一接口", "kind": "core", "zone": "br"},
            {"id": "p-magic", "label": "魔术方法", "kind": "prev", "zone": "l", "code": "py-magic"},
            {"id": "n-regex", "label": "正则表达式", "kind": "next", "zone": "r", "code": "py-regex"},
            {"id": "s-tool", "label": "Agent 工具接口", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "abc", "label": "继承它才算实现类"},
            {"a": "center", "b": "abstract", "label": "漏了就建不出来"},
            {"a": "center", "b": "contract", "label": "调用方只认这套"},
            {"a": "center", "b": "p-magic", "label": "比空方法更早报错"},
            {"a": "center", "b": "n-regex", "label": "工具各有各的参数"},
            {"a": "center", "b": "s-tool", "label": "每个工具都实现 run()"},
        ],
    },
    "py-regex": {
        "oneliner": (
            "正则用一套模式串描述「长什么样的文本」，一次搞定查找、提取、替换；"
            "学完你能从日志或模型输出里精准抠出想要的那几个字段。"
        ),
        "center": "正则表达式",
        "nodes": [
            {"id": "meta", "label": "字符与量词", "kind": "core", "zone": "t"},
            {"id": "group", "label": "分组捕获", "kind": "core", "zone": "bl"},
            {"id": "sub", "label": "search / sub", "kind": "core", "zone": "br"},
            {"id": "p-str", "label": "字符串", "kind": "prev", "zone": "l", "code": "py-str"},
            {"id": "n-stdlib", "label": "标准库", "kind": "next", "zone": "r", "code": "py-stdlib"},
            {"id": "s-log", "label": "从日志提取字段", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "meta", "label": "\\d \\w . * + ?"},
            {"a": "center", "b": "group", "label": "( ) 只取想要的"},
            {"a": "center", "b": "sub", "label": "找和换"},
            {"a": "center", "b": "p-str", "label": "本质是在字符串里找"},
            {"a": "center", "b": "n-stdlib", "label": "re 就是标准库"},
            {"a": "center", "b": "s-log", "label": "定位报错行号"},
        ],
    },
    "py-stdlib": {
        "oneliner": (
            "Counter 数频次、defaultdict 免判空、chain 串多个列表、lru_cache 做缓存；"
            "学完你能少写一半循环，标准库早就替你写好了。"
        ),
        "center": "标准库",
        "nodes": [
            {"id": "collections", "label": "计数与默认值", "kind": "core", "zone": "t"},
            {"id": "itertools", "label": "itertools", "kind": "core", "zone": "bl"},
            {"id": "functools", "label": "functools", "kind": "core", "zone": "br"},
            {"id": "p-dict", "label": "字典", "kind": "prev", "zone": "l", "code": "py-dict"},
            {"id": "n-context", "label": "上下文管理器", "kind": "next", "zone": "r", "code": "py-context"},
            {"id": "s-cache", "label": "给函数加缓存", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "collections", "label": "Counter / defaultdict"},
            {"a": "center", "b": "itertools", "label": "排列组合拼接"},
            {"a": "center", "b": "functools", "label": "lru_cache / partial"},
            {"a": "center", "b": "p-dict", "label": "都建在字典上"},
            {"a": "center", "b": "n-context", "label": "少写 try/finally"},
            {"a": "center", "b": "s-cache", "label": "重复调用只算一次"},
        ],
    },
    "py-context": {
        "oneliner": (
            "with 保证代码块结束时一定执行收尾动作，中间有没有报错都不例外；"
            "学完你能自己写 __enter__ / __exit__，管好文件、连接和锁。"
        ),
        "center": "上下文管理器",
        "nodes": [
            {"id": "with", "label": "with 语句", "kind": "core", "zone": "t"},
            {"id": "enter", "label": "__enter__/__exit__", "kind": "core", "zone": "bl"},
            {"id": "cm", "label": "@contextmanager", "kind": "core", "zone": "br"},
            {"id": "p-exc", "label": "异常处理", "kind": "prev", "zone": "l", "code": "py-exception"},
            {"id": "n-conc", "label": "并发", "kind": "next", "zone": "r", "code": "py-concurrency"},
            {"id": "s-conn", "label": "数据库连接", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "with", "label": "进来一次出去一次"},
            {"a": "center", "b": "enter", "label": "两个方法管两头"},
            {"a": "center", "b": "cm", "label": "用 yield 写更省事"},
            {"a": "center", "b": "p-exc", "label": "报错也照样收尾"},
            {"a": "center", "b": "n-conc", "label": "锁要用 with"},
            {"a": "center", "b": "s-conn", "label": "用完一定关掉"},
        ],
    },
    "py-concurrency": {
        "oneliner": (
            "线程适合等 I/O、进程适合吃 CPU，concurrent.futures 用一套接口提交任务；"
            "学完你能把 10 次网络请求从 10 秒压到 1 秒。"
        ),
        "center": "并发",
        "nodes": [
            {"id": "thread", "label": "线程池", "kind": "core", "zone": "t"},
            {"id": "process", "label": "进程池", "kind": "core", "zone": "bl"},
            {"id": "gil", "label": "GIL 与选型", "kind": "core", "zone": "br"},
            {"id": "p-context", "label": "上下文管理器", "kind": "prev", "zone": "l", "code": "py-context"},
            {"id": "n-json", "label": "JSON 处理", "kind": "next", "zone": "r", "code": "eng-json"},
            {"id": "s-llm", "label": "并发调模型", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "thread", "label": "等网络时切走"},
            {"a": "center", "b": "process", "label": "真并行吃满 CPU"},
            {"a": "center", "b": "gil", "label": "一把锁限制多线程"},
            {"a": "center", "b": "p-context", "label": "锁和池都要收尾"},
            {"a": "center", "b": "n-json", "label": "并发解析结果"},
            {"a": "center", "b": "s-llm", "label": "10 个请求一起发"},
        ],
    },
    # ---------- 工程基础 + AI Agent 开发 ----------
    "eng-json": {
        "oneliner": (
            "json.loads 把字符串变字典、json.dumps 把字典变回字符串；"
            "学完你能读写接口报文，也能处理中文转义和嵌套结构。"
        ),
        "center": "JSON 处理",
        "nodes": [
            {"id": "sd", "label": "loads / dumps", "kind": "core", "zone": "t"},
            {"id": "cn", "label": "中文与转义", "kind": "core", "zone": "bl"},
            {"id": "nest", "label": "嵌套读写", "kind": "core", "zone": "br"},
            {"id": "p-dict", "label": "字典", "kind": "prev", "zone": "l", "code": "py-dict"},
            {"id": "n-env", "label": "环境变量", "kind": "next", "zone": "r", "code": "eng-env"},
            {"id": "s-llm", "label": "大模型报文", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "sd", "label": "字符串与对象互转"},
            {"a": "center", "b": "cn", "label": "ensure_ascii=False"},
            {"a": "center", "b": "nest", "label": "一层层往下取"},
            {"a": "center", "b": "p-dict", "label": "转完就是字典"},
            {"a": "center", "b": "n-env", "label": "配置也常写成 JSON"},
            {"a": "center", "b": "s-llm", "label": "请求体全是它"},
        ],
    },
    "eng-env": {
        "oneliner": (
            "API Key 只放环境变量或 .env，绝不写进代码和仓库；"
            "学完你能用 os.getenv 读配置，并在启动时检查密钥有没有漏配。"
        ),
        "center": "密钥管理",
        "nodes": [
            {"id": "getenv", "label": "os.getenv", "kind": "core", "zone": "t"},
            {"id": "dotenv", "label": ".env 与 gitignore", "kind": "core", "zone": "bl"},
            {"id": "check", "label": "启动自检", "kind": "core", "zone": "br"},
            {"id": "p-json", "label": "JSON 处理", "kind": "prev", "zone": "l", "code": "eng-json"},
            {"id": "n-log", "label": "日志与调试", "kind": "next", "zone": "r", "code": "eng-log"},
            {"id": "s-server", "label": "服务器上配环境", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "getenv", "label": "带默认值更稳"},
            {"a": "center", "b": "dotenv", "label": "本地开发用"},
            {"a": "center", "b": "check", "label": "缺了就早报错"},
            {"a": "center", "b": "p-json", "label": "配置常是 JSON"},
            {"a": "center", "b": "n-log", "label": "别把密钥打进日志"},
            {"a": "center", "b": "s-server", "label": "改完要重启服务"},
        ],
    },
    "eng-log": {
        "oneliner": (
            "print 只能救急，logging 才能上线：分级别、带时间、能落盘；"
            "学完你能给项目加上结构化日志，出问题时顺着日志找到根因。"
        ),
        "center": "日志",
        "nodes": [
            {"id": "level", "label": "五个级别", "kind": "core", "zone": "t"},
            {"id": "format", "label": "格式与落盘", "kind": "core", "zone": "bl"},
            {"id": "trace", "label": "异常堆栈", "kind": "core", "zone": "br"},
            {"id": "p-env", "label": "环境变量", "kind": "prev", "zone": "l", "code": "eng-env"},
            {"id": "n-typing", "label": "类型注解", "kind": "next", "zone": "r", "code": "eng-typing"},
            {"id": "s-online", "label": "线上排查", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "level", "label": "DEBUG 到 ERROR"},
            {"a": "center", "b": "format", "label": "时间 / 模块 / 行号"},
            {"a": "center", "b": "trace", "label": "exc_info=True"},
            {"a": "center", "b": "p-env", "label": "级别从配置读"},
            {"a": "center", "b": "n-typing", "label": "别用 print 调试"},
            {"a": "center", "b": "s-online", "label": "日志是唯一线索"},
        ],
    },
    "eng-typing": {
        "oneliner": (
            "用类型注解写清函数吃什么、吐什么，dataclass 自动生成初始化和打印；"
            "学完你能让编辑器提前发现类型错误，代码也更好读。"
        ),
        "center": "类型注解",
        "nodes": [
            {"id": "anno", "label": "注解写法", "kind": "core", "zone": "t"},
            {"id": "opt", "label": "Optional 与泛型", "kind": "core", "zone": "bl"},
            {"id": "dc", "label": "@dataclass", "kind": "core", "zone": "br"},
            {"id": "p-log", "label": "日志与调试", "kind": "prev", "zone": "l", "code": "eng-log"},
            {"id": "n-http", "label": "HTTP 请求", "kind": "next", "zone": "r", "code": "eng-http"},
            {"id": "s-pydantic", "label": "和 Pydantic 分工", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "anno", "label": "name: str -> int"},
            {"a": "center", "b": "opt", "label": "可能是 None"},
            {"a": "center", "b": "dc", "label": "少写一堆样板代码"},
            {"a": "center", "b": "p-log", "label": "报错时看得懂类型"},
            {"a": "center", "b": "n-http", "label": "响应结构先定义"},
            {"a": "center", "b": "s-pydantic", "label": "注解不校验，它才校验"},
        ],
    },
    "eng-http": {
        "oneliner": (
            "请求方法、状态码、请求头、JSON body 是 HTTP 的四件套，requests 把它们封装好；"
            "学完你能调通第三方接口，并处理超时和错误码。"
        ),
        "center": "HTTP 请求",
        "nodes": [
            {"id": "method", "label": "方法与 URL", "kind": "core", "zone": "t"},
            {"id": "header", "label": "headers 与 body", "kind": "core", "zone": "bl"},
            {"id": "status", "label": "状态码与超时", "kind": "core", "zone": "br"},
            {"id": "p-typing", "label": "类型注解", "kind": "prev", "zone": "l", "code": "eng-typing"},
            {"id": "n-async", "label": "异步编程", "kind": "next", "zone": "r", "code": "eng-async"},
            {"id": "s-llm", "label": "调大模型 API", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "method", "label": "GET 取 POST 交"},
            {"a": "center", "b": "header", "label": "身份和格式"},
            {"a": "center", "b": "status", "label": "200 / 401 / 500"},
            {"a": "center", "b": "p-typing", "label": "返回值先定结构"},
            {"a": "center", "b": "n-async", "label": "同步版换成异步版"},
            {"a": "center", "b": "s-llm", "label": "本质就是一次 POST"},
        ],
    },
    "eng-async": {
        "oneliner": (
            "async / await 让单线程也能同时等多个网络请求，遇到 await 就切去干别的；"
            "学完你能把串行调用改成并发，耗时砍到最慢那一个。"
        ),
        "center": "asyncio",
        "nodes": [
            {"id": "await", "label": "async / await", "kind": "core", "zone": "t"},
            {"id": "loop", "label": "事件循环", "kind": "core", "zone": "bl"},
            {"id": "gather", "label": "gather 并发", "kind": "core", "zone": "br"},
            {"id": "p-http", "label": "HTTP 请求", "kind": "prev", "zone": "l", "code": "eng-http"},
            {"id": "n-pydantic", "label": "Pydantic 校验", "kind": "next", "zone": "r", "code": "eng-pydantic"},
            {"id": "s-fastapi", "label": "FastAPI 就是异步", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "await", "label": "等的时候让出线程"},
            {"a": "center", "b": "loop", "label": "一个线程调度所有任务"},
            {"a": "center", "b": "gather", "label": "一起等结果"},
            {"a": "center", "b": "p-http", "label": "把请求换成 aiohttp"},
            {"a": "center", "b": "n-pydantic", "label": "并发返回统一校验"},
            {"a": "center", "b": "s-fastapi", "label": "一个接口一个协程"},
        ],
    },
    "eng-pydantic": {
        "oneliner": (
            "外部进来的数据一律先过 Pydantic：类型不对、字段缺了都当场拦下；"
            "学完你能给接口定义请求模型，还能写校验器管住格式。"
        ),
        "center": "数据校验",
        "nodes": [
            {"id": "model", "label": "BaseModel", "kind": "core", "zone": "t"},
            {"id": "validator", "label": "字段校验器", "kind": "core", "zone": "bl"},
            {"id": "error", "label": "错误信息", "kind": "core", "zone": "br"},
            {"id": "p-typing", "label": "类型注解", "kind": "prev", "zone": "l", "code": "eng-typing"},
            {"id": "n-llm", "label": "调用大模型", "kind": "next", "zone": "r", "code": "ai-llm-api"},
            {"id": "s-request", "label": "FastAPI 请求体", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "model", "label": "一个类就是一份 schema"},
            {"a": "center", "b": "validator", "label": "自己写规则"},
            {"a": "center", "b": "error", "label": "422 带字段名"},
            {"a": "center", "b": "p-typing", "label": "注解的运行时加强版"},
            {"a": "center", "b": "n-llm", "label": "模型输出也能校验"},
            {"a": "center", "b": "s-request", "label": "进接口第一道闸"},
        ],
    },
    "ai-llm-api": {
        "oneliner": (
            "一次调用就是往 messages 里塞 system 和 user，再把回复取出来；"
            "学完你能用代码问模型问题、控制温度和长度，并算清 token 成本。"
        ),
        "center": "调大模型",
        "nodes": [
            {"id": "messages", "label": "messages 结构", "kind": "core", "zone": "t"},
            {"id": "role", "label": "system 与 user", "kind": "core", "zone": "bl"},
            {"id": "params", "label": "参数与成本", "kind": "core", "zone": "br"},
            {"id": "p-http", "label": "HTTP 请求", "kind": "prev", "zone": "l", "code": "eng-http"},
            {"id": "n-prompt", "label": "Prompt 工程", "kind": "next", "zone": "r", "code": "ai-prompt"},
            {"id": "s-stream", "label": "流式开关", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "messages", "label": "一问一答都是对象"},
            {"a": "center", "b": "role", "label": "人设和问题分开"},
            {"a": "center", "b": "params", "label": "温度与长度上限"},
            {"a": "center", "b": "p-http", "label": "POST 一个接口"},
            {"a": "center", "b": "n-prompt", "label": "内容怎么写才开始"} ,
            {"a": "center", "b": "s-stream", "label": "stream=True"},
        ],
    },
    "ai-prompt": {
        "oneliner": (
            "把角色、任务、规则、输出格式写清楚，模型才会稳定给出对的结果；"
            "学完你能写出可复用的 prompt 模板，也知道哪句话该放 system。"
        ),
        "center": "Prompt 工程",
        "nodes": [
            {"id": "role", "label": "角色与任务", "kind": "core", "zone": "t"},
            {"id": "rule", "label": "规则与约束", "kind": "core", "zone": "bl"},
            {"id": "format", "label": "输出格式", "kind": "core", "zone": "br"},
            {"id": "p-llm", "label": "调用大模型", "kind": "prev", "zone": "l", "code": "ai-llm-api"},
            {"id": "n-struct", "label": "结构化输出", "kind": "next", "zone": "r", "code": "ai-structured"},
            {"id": "s-fewshot", "label": "few-shot 示例", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "role", "label": "你是谁、做什么"},
            {"a": "center", "b": "rule", "label": "不许做什么"},
            {"a": "center", "b": "format", "label": "几条、什么结构"},
            {"a": "center", "b": "p-llm", "label": "写进 system"},
            {"a": "center", "b": "n-struct", "label": "格式约束是它的前置"},
            {"a": "center", "b": "s-fewshot", "label": "给两个样例最省事"},
        ],
    },
    "ai-structured": {
        "oneliner": (
            "让模型稳定返回 JSON 需要两道保险：prompt 里写清 schema，代码里再做容错解析；"
            "学完你能把模型输出变成程序可以直接用的字典。"
        ),
        "center": "结构化输出",
        "nodes": [
            {"id": "schema", "label": "schema 约束", "kind": "core", "zone": "t"},
            {"id": "parse", "label": "容错解析", "kind": "core", "zone": "bl"},
            {"id": "retry", "label": "失败重试", "kind": "core", "zone": "br"},
            {"id": "p-prompt", "label": "Prompt 工程", "kind": "prev", "zone": "l", "code": "ai-prompt"},
            {"id": "n-tools", "label": "工具调用", "kind": "next", "zone": "r", "code": "ai-tools"},
            {"id": "s-pydantic", "label": "用 Pydantic 校验", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "schema", "label": "把字段和类型写死"},
            {"a": "center", "b": "parse", "label": "去掉 ```json 包裹"},
            {"a": "center", "b": "retry", "label": "解析失败再问一次"},
            {"a": "center", "b": "p-prompt", "label": "格式要求写在 prompt 里"},
            {"a": "center", "b": "n-tools", "label": "工具参数就是 schema"},
            {"a": "center", "b": "s-pydantic", "label": "解析完再校验一遍"},
        ],
    },
    "ai-tools": {
        "oneliner": (
            "把函数的名字、说明、参数 schema 交给模型，模型会告诉你该调哪个、传什么参数；"
            "学完你能让模型真正「动手」查数据、算东西。"
        ),
        "center": "工具调用",
        "nodes": [
            {"id": "schema", "label": "工具 schema", "kind": "core", "zone": "t"},
            {"id": "calls", "label": "返回 tool_calls", "kind": "core", "zone": "bl"},
            {"id": "exec", "label": "执行与回填", "kind": "core", "zone": "br"},
            {"id": "p-struct", "label": "结构化输出", "kind": "prev", "zone": "l", "code": "ai-structured"},
            {"id": "n-loop", "label": "Agent 循环", "kind": "next", "zone": "r", "code": "ai-agent-loop"},
            {"id": "s-mcp", "label": "MCP 协议", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "schema", "label": "名字 + 说明 + 参数"},
            {"a": "center", "b": "calls", "label": "模型只说要调什么"},
            {"a": "center", "b": "exec", "label": "真正执行的是你"},
            {"a": "center", "b": "p-struct", "label": "参数就是一段 JSON"},
            {"a": "center", "b": "n-loop", "label": "调完还要接着想"},
            {"a": "center", "b": "s-mcp", "label": "工具的统一插座"},
        ],
    },
    "ai-agent-loop": {
        "oneliner": (
            "思考、调工具、看结果，这个循环跑到模型不再要工具为止；"
            "学完你能写出一个会自己查资料、多步推理的 Agent。"
        ),
        "center": "Agent 循环",
        "nodes": [
            {"id": "stop", "label": "终止条件", "kind": "core", "zone": "t"},
            {"id": "feed", "label": "结果回填", "kind": "core", "zone": "bl"},
            {"id": "max", "label": "最大轮数兜底", "kind": "core", "zone": "br"},
            {"id": "p-tools", "label": "工具调用", "kind": "prev", "zone": "l", "code": "ai-tools"},
            {"id": "n-stream", "label": "流式输出", "kind": "next", "zone": "r", "code": "ai-stream"},
            {"id": "s-multi", "label": "多 Agent 编排", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "stop", "label": "不再要工具就结束"},
            {"a": "center", "b": "feed", "label": "把结果塞回 messages"},
            {"a": "center", "b": "max", "label": "防止无限转圈"},
            {"a": "center", "b": "p-tools", "label": "一轮用一次工具"},
            {"a": "center", "b": "n-stream", "label": "每步都能推给前端"},
            {"a": "center", "b": "s-multi", "label": "循环套循环"},
        ],
    },
    "ai-stream": {
        "oneliner": (
            "流式返回是一串增量片段，拼起来才是完整回复；"
            "学完你能边收边推给前端，让用户看到字在往外冒，而不是转圈等十秒。"
        ),
        "center": "流式输出",
        "nodes": [
            {"id": "flag", "label": "stream=True", "kind": "core", "zone": "t"},
            {"id": "concat", "label": "增量拼接", "kind": "core", "zone": "bl"},
            {"id": "sse", "label": "SSE 推送", "kind": "core", "zone": "br"},
            {"id": "p-loop", "label": "Agent 循环", "kind": "prev", "zone": "l", "code": "ai-agent-loop"},
            {"id": "n-rag", "label": "RAG 检索", "kind": "next", "zone": "r", "code": "ai-rag"},
            {"id": "s-typewriter", "label": "前端打字机", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "flag", "label": "开开关"},
            {"a": "center", "b": "concat", "label": "delta 一片片接"},
            {"a": "center", "b": "sse", "label": "边生成边下发"},
            {"a": "center", "b": "p-loop", "label": "循环里也能流"},
            {"a": "center", "b": "n-rag", "label": "先检索再吐字"},
            {"a": "center", "b": "s-typewriter", "label": "一个字一个字显示"},
        ],
    },
    "ai-rag": {
        "oneliner": (
            "先把资料切片存成向量，提问时检索最相关的几段塞进 prompt；"
            "学完你能让模型回答它从没训练过的私有知识。"
        ),
        "center": "RAG",
        "nodes": [
            {"id": "chunk", "label": "切片与向量化", "kind": "core", "zone": "t"},
            {"id": "search", "label": "相似度检索", "kind": "core", "zone": "bl"},
            {"id": "inject", "label": "拼进 prompt", "kind": "core", "zone": "br"},
            {"id": "p-prompt", "label": "Prompt 工程", "kind": "prev", "zone": "l", "code": "ai-prompt"},
            {"id": "n-memory", "label": "多轮与记忆", "kind": "next", "zone": "r", "code": "ai-memory"},
            {"id": "s-vector", "label": "向量数据库", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "chunk", "label": "太长要切开"},
            {"a": "center", "b": "search", "label": "余弦相似度取 top-k"},
            {"a": "center", "b": "inject", "label": "带资料再问"},
            {"a": "center", "b": "p-prompt", "label": "检索结果也要排版"},
            {"a": "center", "b": "n-memory", "label": "都得管上下文长度"},
            {"a": "center", "b": "s-vector", "label": "存和查都靠它"},
        ],
    },
    "ai-memory": {
        "oneliner": (
            "对话越长上下文越贵，得按策略裁剪：留最近几轮、摘要早期内容、把事实外置存储；"
            "学完你能让长对话既记得住又不爆 token。"
        ),
        "center": "对话记忆",
        "nodes": [
            {"id": "trim", "label": "历史裁剪", "kind": "core", "zone": "t"},
            {"id": "summary", "label": "摘要压缩", "kind": "core", "zone": "bl"},
            {"id": "external", "label": "外置记忆", "kind": "core", "zone": "br"},
            {"id": "p-rag", "label": "RAG 检索", "kind": "prev", "zone": "l", "code": "ai-rag"},
            {"id": "n-test", "label": "单元测试", "kind": "next", "zone": "r", "code": "eng-test"},
            {"id": "s-session", "label": "会话存储", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "trim", "label": "只留最近几轮"},
            {"a": "center", "b": "summary", "label": "老的压成一段话"},
            {"a": "center", "b": "external", "label": "事实存数据库"},
            {"a": "center", "b": "p-rag", "label": "记忆也能当检索源"},
            {"a": "center", "b": "n-test", "label": "裁剪逻辑最该测"},
            {"a": "center", "b": "s-session", "label": "刷新页面还在"},
        ],
    },
    "eng-test": {
        "oneliner": (
            "用 pytest 给关键函数写断言，改完代码一条命令就知道有没有弄坏东西；"
            "学完你能给核心逻辑补上测试，重构时不用心慌。"
        ),
        "center": "单元测试",
        "nodes": [
            {"id": "assert", "label": "断言 assert", "kind": "core", "zone": "t"},
            {"id": "fixture", "label": "fixture", "kind": "core", "zone": "bl"},
            {"id": "param", "label": "参数化", "kind": "core", "zone": "br"},
            {"id": "p-module", "label": "模块与包", "kind": "prev", "zone": "l", "code": "py-module"},
            {"id": "n-deps", "label": "依赖管理", "kind": "next", "zone": "r", "code": "eng-deps"},
            {"id": "s-cov", "label": "覆盖率", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "assert", "label": "期望等于实际"},
            {"a": "center", "b": "fixture", "label": "复用准备数据"},
            {"a": "center", "b": "param", "label": "一组输入一起跑"},
            {"a": "center", "b": "p-module", "label": "按模块建测试文件"},
            {"a": "center", "b": "n-deps", "label": "pytest 也是依赖"},
            {"a": "center", "b": "s-cov", "label": "看哪行没跑到"},
        ],
    },
    "eng-deps": {
        "oneliner": (
            "一个项目一份依赖清单，代码按模块分好文件夹；"
            "学完你能用 requirements 或 pyproject 钉住版本，换台机器一条命令装齐。"
        ),
        "center": "项目依赖",
        "nodes": [
            {"id": "req", "label": "requirements.txt", "kind": "core", "zone": "t"},
            {"id": "layout", "label": "目录结构", "kind": "core", "zone": "bl"},
            {"id": "pin", "label": "版本锁定", "kind": "core", "zone": "br"},
            {"id": "p-module", "label": "模块与包", "kind": "prev", "zone": "l", "code": "py-module"},
            {"id": "n-quality", "label": "代码质量", "kind": "next", "zone": "r", "code": "eng-quality"},
            {"id": "s-docker", "label": "打成镜像", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "req", "label": "清单写在这里"},
            {"a": "center", "b": "layout", "label": "代码和配置分开"},
            {"a": "center", "b": "pin", "label": "写 == 不写 >="},
            {"a": "center", "b": "p-module", "label": "包结构决定可维护性"},
            {"a": "center", "b": "n-quality", "label": "工具也要装进来"},
            {"a": "center", "b": "s-docker", "label": "镜像里再装一遍"},
        ],
    },
    "eng-quality": {
        "oneliner": (
            "ruff 查问题、black 管格式、mypy 查类型，三件套跑一遍再提交；"
            "学完你能把风格争议交给工具，代码评审只谈逻辑。"
        ),
        "center": "质量工具链",
        "nodes": [
            {"id": "ruff", "label": "ruff 查问题", "kind": "core", "zone": "t"},
            {"id": "black", "label": "black 格式化", "kind": "core", "zone": "bl"},
            {"id": "mypy", "label": "mypy 查类型", "kind": "core", "zone": "br"},
            {"id": "p-deps", "label": "依赖管理", "kind": "prev", "zone": "l", "code": "eng-deps"},
            {"id": "n-eval", "label": "Agent 评测", "kind": "next", "zone": "r", "code": "ai-eval"},
            {"id": "s-hook", "label": "pre-commit 钩子", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "ruff", "label": "未用变量、坏味道"},
            {"a": "center", "b": "black", "label": "不争风格"},
            {"a": "center", "b": "mypy", "label": "按注解查"},
            {"a": "center", "b": "p-deps", "label": "工具版本也要钉住"},
            {"a": "center", "b": "n-eval", "label": "两种质量都要量"},
            {"a": "center", "b": "s-hook", "label": "提交前自动跑"},
        ],
    },
    "ai-eval": {
        "oneliner": (
            "固定一批问题加标准答案，每次改 prompt 都跑一遍看分数；"
            "学完你能用数据判断改动是变好还是变坏，而不是凭感觉。"
        ),
        "center": "Agent 评测",
        "nodes": [
            {"id": "set", "label": "评测集", "kind": "core", "zone": "t"},
            {"id": "judge", "label": "判定标准", "kind": "core", "zone": "bl"},
            {"id": "regress", "label": "回归对比", "kind": "core", "zone": "br"},
            {"id": "p-prompt", "label": "Prompt 工程", "kind": "prev", "zone": "l", "code": "ai-prompt"},
            {"id": "n-multi", "label": "多 Agent", "kind": "next", "zone": "r", "code": "ai-multiagent"},
            {"id": "s-judge", "label": "用模型打分", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "set", "label": "问题和答案都固定"},
            {"a": "center", "b": "judge", "label": "关键词还是人工"},
            {"a": "center", "b": "regress", "label": "改一次跑一次"},
            {"a": "center", "b": "p-prompt", "label": "改完就得测"},
            {"a": "center", "b": "n-multi", "label": "多角色更难评"},
            {"a": "center", "b": "s-judge", "label": "LLM as judge"},
        ],
    },
    "ai-multiagent": {
        "oneliner": (
            "把任务拆给不同角色的 Agent，由调度者分配和汇总；"
            "学完你能设计分工清晰的协作流程，避免互相甩锅和死循环。"
        ),
        "center": "多 Agent",
        "nodes": [
            {"id": "roles", "label": "角色分工", "kind": "core", "zone": "t"},
            {"id": "route", "label": "调度与交接", "kind": "core", "zone": "bl"},
            {"id": "state", "label": "状态与终止", "kind": "core", "zone": "br"},
            {"id": "p-loop", "label": "Agent 循环", "kind": "prev", "zone": "l", "code": "ai-agent-loop"},
            {"id": "s-framework", "label": "编排框架", "kind": "side", "zone": "r"},
            {"id": "s-context", "label": "共享上下文", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "roles", "label": "每个只管一段"},
            {"a": "center", "b": "route", "label": "谁来干、干完给谁"},
            {"a": "center", "b": "state", "label": "别无限来回踢"},
            {"a": "center", "b": "p-loop", "label": "自身也是一轮循环"},
            {"a": "center", "b": "s-framework", "label": "不必从零写"},
            {"a": "center", "b": "s-context", "label": "交接时传什么最关键"},
        ],
    },
    # ---------- MySQL ----------
    "mysql-01": {
        "oneliner": (
            "建表要先想清楚每列存什么、用哪种类型、能不能为空，定错了后面都在还债；"
            "学完你能写出带主键、约束和合适类型的建表语句。"
        ),
        "center": "建表",
        "nodes": [
            {"id": "type", "label": "字段类型", "kind": "core", "zone": "t"},
            {"id": "pk", "label": "主键与约束", "kind": "core", "zone": "bl"},
            {"id": "charset", "label": "字符集与默认值", "kind": "core", "zone": "br"},
            {"id": "n-query", "label": "基础查询", "kind": "next", "zone": "r", "code": "mysql-02"},
            {"id": "s-debt", "label": "类型选错都在还债", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "type", "label": "INT 还是 VARCHAR"},
            {"a": "center", "b": "pk", "label": "一行怎么唯一标识"},
            {"a": "center", "b": "charset", "label": "utf8mb4 才存得下表情"},
            {"a": "center", "b": "n-query", "label": "建完才轮到查"},
            {"a": "center", "b": "s-debt", "label": "后面改表很痛"},
        ],
    },
    "mysql-02": {
        "oneliner": (
            "SELECT 选列、WHERE 选行，配合比较、IN、LIKE 把想要的数据挑出来；"
            "学完你能写出一条带条件的查询，而不是把整张表拉回内存再过滤。"
        ),
        "center": "查询与过滤",
        "nodes": [
            {"id": "select", "label": "SELECT 选列", "kind": "core", "zone": "t"},
            {"id": "where", "label": "WHERE 条件", "kind": "core", "zone": "bl"},
            {"id": "null", "label": "NULL 判断", "kind": "core", "zone": "br"},
            {"id": "p-create", "label": "建表", "kind": "prev", "zone": "l", "code": "mysql-01"},
            {"id": "n-order", "label": "排序与分页", "kind": "next", "zone": "r", "code": "mysql-03"},
            {"id": "s-index", "label": "条件写法影响索引", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "select", "label": "要哪几列"},
            {"a": "center", "b": "where", "label": "要哪几行"},
            {"a": "center", "b": "null", "label": "= NULL 永远不成立"},
            {"a": "center", "b": "p-create", "label": "先有表"},
            {"a": "center", "b": "n-order", "label": "筛完再排"},
            {"a": "center", "b": "s-index", "label": "函数包住列就用不上"},
        ],
    },
    "mysql-03": {
        "oneliner": (
            "ORDER BY 排序、LIMIT 分页，但 LIMIT 100000,20 会越翻越慢；"
            "学完你能写出走索引的分页，也讲得清深分页为什么要改写。"
        ),
        "center": "排序与分页",
        "nodes": [
            {"id": "order", "label": "ORDER BY", "kind": "core", "zone": "t"},
            {"id": "limit", "label": "LIMIT offset", "kind": "core", "zone": "bl"},
            {"id": "deep", "label": "深分页改写", "kind": "core", "zone": "br"},
            {"id": "p-where", "label": "查询与过滤", "kind": "prev", "zone": "l", "code": "mysql-02"},
            {"id": "n-group", "label": "聚合与分组", "kind": "next", "zone": "r", "code": "mysql-04"},
            {"id": "s-cursor", "label": "游标分页", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "order", "label": "按哪列排"},
            {"a": "center", "b": "limit", "label": "跳过多少取多少"},
            {"a": "center", "b": "deep", "label": "先查主键再回表"},
            {"a": "center", "b": "p-where", "label": "先筛后排"},
            {"a": "center", "b": "n-group", "label": "统计前常要排序"},
            {"a": "center", "b": "s-cursor", "label": "记住上一页最后一条"},
        ],
    },
    "mysql-04": {
        "oneliner": (
            "GROUP BY 把行分组、聚合函数对每组算一个数，HAVING 再筛组；"
            "学完你能写出「每个班平均分」这类统计，并分清 WHERE 和 HAVING。"
        ),
        "center": "聚合分组",
        "nodes": [
            {"id": "agg", "label": "聚合函数", "kind": "core", "zone": "t"},
            {"id": "group", "label": "GROUP BY", "kind": "core", "zone": "bl"},
            {"id": "having", "label": "WHERE 与 HAVING", "kind": "core", "zone": "br"},
            {"id": "p-order", "label": "排序与分页", "kind": "prev", "zone": "l", "code": "mysql-03"},
            {"id": "n-join", "label": "多表连接", "kind": "next", "zone": "r", "code": "mysql-05"},
            {"id": "s-rank", "label": "排行榜统计", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "agg", "label": "COUNT / SUM / AVG"},
            {"a": "center", "b": "group", "label": "按谁分组"},
            {"a": "center", "b": "having", "label": "组前筛行、组后筛组"},
            {"a": "center", "b": "p-order", "label": "先有结果集"},
            {"a": "center", "b": "n-join", "label": "分组前先拼表"},
            {"a": "center", "b": "s-rank", "label": "按分数段数人"},
        ],
    },
    "mysql-05": {
        "oneliner": (
            "INNER JOIN 只留匹配上的、LEFT JOIN 保住左表，右表没匹配就补 NULL；"
            "学完你能把拆开的表拼回完整记录，并用 COALESCE 兜住空值。"
        ),
        "center": "多表连接",
        "nodes": [
            {"id": "kind", "label": "INNER / LEFT", "kind": "core", "zone": "t"},
            {"id": "on", "label": "ON 与笛卡尔积", "kind": "core", "zone": "bl"},
            {"id": "null", "label": "NULL 与 COALESCE", "kind": "core", "zone": "br"},
            {"id": "p-group", "label": "聚合与分组", "kind": "prev", "zone": "l", "code": "mysql-04"},
            {"id": "n-sub", "label": "子查询与 UNION", "kind": "next", "zone": "r", "code": "mysql-06"},
            {"id": "s-dup", "label": "一对多会重复计数", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "kind", "label": "要不要保住没匹配的"},
            {"a": "center", "b": "on", "label": "漏写就全乘全"},
            {"a": "center", "b": "null", "label": "空值参与计算要小心"},
            {"a": "center", "b": "p-group", "label": "拼完再统计"},
            {"a": "center", "b": "n-sub", "label": "嵌套的另一种写法"},
            {"a": "center", "b": "s-dup", "label": "求和会偏大"},
        ],
    },
    "mysql-06": {
        "oneliner": (
            "子查询先算括号里的结果、再拿它去筛，UNION 把多条查询竖着接起来；"
            "学完你能拆解复杂 SQL，也知道什么时候该改成 JOIN 更快。"
        ),
        "center": "子查询",
        "nodes": [
            {"id": "in", "label": "标量 / IN 子查询", "kind": "core", "zone": "t"},
            {"id": "exists", "label": "EXISTS", "kind": "core", "zone": "bl"},
            {"id": "union", "label": "UNION 与 UNION ALL", "kind": "core", "zone": "br"},
            {"id": "p-join", "label": "多表连接", "kind": "prev", "zone": "l", "code": "mysql-05"},
            {"id": "n-btree", "label": "B+ 树索引", "kind": "next", "zone": "r", "code": "mysql-07"},
            {"id": "s-rewrite", "label": "慢查询改写", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "in", "label": "结果当成一张临时表"},
            {"a": "center", "b": "exists", "label": "只关心有没有"},
            {"a": "center", "b": "union", "label": "竖着拼结果"},
            {"a": "center", "b": "p-join", "label": "多数能改写成 JOIN"},
            {"a": "center", "b": "n-btree", "label": "嵌套太深就慢"},
            {"a": "center", "b": "s-rewrite", "label": "改成 JOIN 往往更快"},
        ],
    },
    "mysql-07": {
        "oneliner": (
            "InnoDB 选 B+ 树，是因为它矮、有序、叶子节点还串成链表；"
            "学完你能讲清一次查询查几层、为什么范围查询也快。"
        ),
        "center": "B+ 树索引",
        "nodes": [
            {"id": "why", "label": "为什么是 B+ 树", "kind": "core", "zone": "t"},
            {"id": "cluster", "label": "聚簇与二级索引", "kind": "core", "zone": "bl"},
            {"id": "back", "label": "回表", "kind": "core", "zone": "br"},
            {"id": "p-sub", "label": "子查询", "kind": "prev", "zone": "l", "code": "mysql-06"},
            {"id": "n-explain", "label": "索引失效", "kind": "next", "zone": "r", "code": "mysql-08"},
            {"id": "s-io", "label": "少读几次磁盘", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "why", "label": "层数少、范围快"},
            {"a": "center", "b": "cluster", "label": "主键索引存整行"},
            {"a": "center", "b": "back", "label": "二级索引要再查一次"},
            {"a": "center", "b": "p-sub", "label": "慢在没索引"},
            {"a": "center", "b": "n-explain", "label": "用不用得上另说"},
            {"a": "center", "b": "s-io", "label": "三层能放两千万行"},
        ],
    },
    "mysql-08": {
        "oneliner": (
            "建了索引不一定用得上：函数包列、隐式转换、前导模糊都会让它失效；"
            "学完你能用 EXPLAIN 看执行计划，判断这条 SQL 到底走没走索引。"
        ),
        "center": "索引失效",
        "nodes": [
            {"id": "left", "label": "最左前缀", "kind": "core", "zone": "t"},
            {"id": "cases", "label": "常见失效场景", "kind": "core", "zone": "bl"},
            {"id": "explain", "label": "EXPLAIN 看什么", "kind": "core", "zone": "br"},
            {"id": "p-btree", "label": "B+ 树索引", "kind": "prev", "zone": "l", "code": "mysql-07"},
            {"id": "n-acid", "label": "事务 ACID", "kind": "next", "zone": "r", "code": "mysql-09"},
            {"id": "s-slow", "label": "慢查询日志", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "left", "label": "联合索引从左往右"},
            {"a": "center", "b": "cases", "label": "函数 / 转换 / like '%x'"},
            {"a": "center", "b": "explain", "label": "看 type 和 key"},
            {"a": "center", "b": "p-btree", "label": "先懂结构再谈失效"},
            {"a": "center", "b": "n-acid", "label": "锁的范围也看索引"},
            {"a": "center", "b": "s-slow", "label": "先找出慢的那条"},
        ],
    },
    "mysql-09": {
        "oneliner": (
            "事务要么全成功要么全失败，靠 undo log、redo log 和锁一起保证；"
            "学完你能讲清 ACID 各自靠什么实现，以及 MVCC 怎么让读写不互相阻塞。"
        ),
        "center": "事务",
        "nodes": [
            {"id": "acid", "label": "ACID", "kind": "core", "zone": "t"},
            {"id": "log", "label": "undo / redo log", "kind": "core", "zone": "bl"},
            {"id": "mvcc", "label": "MVCC 快照", "kind": "core", "zone": "br"},
            {"id": "p-explain", "label": "索引失效", "kind": "prev", "zone": "l", "code": "mysql-08"},
            {"id": "n-lock", "label": "锁与隔离级别", "kind": "next", "zone": "r", "code": "mysql-10"},
            {"id": "s-transfer", "label": "转账不能转一半", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "acid", "label": "四个字母对应四件事"},
            {"a": "center", "b": "log", "label": "undo 与 redo"},
            {"a": "center", "b": "mvcc", "label": "读不加锁靠版本链"},
            {"a": "center", "b": "p-explain", "label": "长事务会拖住索引清理"},
            {"a": "center", "b": "n-lock", "label": "隔离级别决定加什么锁"},
            {"a": "center", "b": "s-transfer", "label": "扣钱和加钱一个事务"},
        ],
    },
    "mysql-10": {
        "oneliner": (
            "隔离级别决定你能看到别人未提交的哪些改动，锁决定谁能改；没走索引的 UPDATE 会锁全表。"
            "学完你能选对隔离级别，也能避开锁表。"
        ),
        "center": "锁与隔离",
        "nodes": [
            {"id": "iso", "label": "四种隔离级别", "kind": "core", "zone": "t"},
            {"id": "lock", "label": "行锁与表锁", "kind": "core", "zone": "bl"},
            {"id": "design", "label": "范式与反范式", "kind": "core", "zone": "br"},
            {"id": "p-acid", "label": "事务 ACID", "kind": "prev", "zone": "l", "code": "mysql-09"},
            {"id": "s-deadlock", "label": "死锁排查", "kind": "side", "zone": "r"},
            {"id": "s-split", "label": "大字段拆表", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "iso", "label": "RR 是默认值"},
            {"a": "center", "b": "lock", "label": "没索引就从行锁升表锁"},
            {"a": "center", "b": "design", "label": "该拆就拆、该冗余就冗余"},
            {"a": "center", "b": "p-acid", "label": "隔离级别是 ACID 的 I"},
            {"a": "center", "b": "s-deadlock", "label": "两边互相等"},
            {"a": "center", "b": "s-split", "label": "TEXT 单独放一张表"},
        ],
    },
    # ---------- Redis ----------
    "redis-01": {
        "oneliner": (
            "Redis 快，是因为数据都在内存、单线程免锁、还用了 IO 多路复用；"
            "学完你能说清五种数据类型各自存什么，以及为什么单线程反而快。"
        ),
        "center": "Redis 基础",
        "nodes": [
            {"id": "fast", "label": "单线程与多路复用", "kind": "core", "zone": "t"},
            {"id": "types", "label": "五种数据类型", "kind": "core", "zone": "bl"},
            {"id": "mem", "label": "纯内存存储", "kind": "core", "zone": "br"},
            {"id": "n-string", "label": "String 计数器", "kind": "next", "zone": "r", "code": "redis-02"},
            {"id": "s-split", "label": "和 MySQL 分工", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "fast", "label": "不用来回加锁"},
            {"a": "center", "b": "types", "label": "String 到 ZSet"},
            {"a": "center", "b": "mem", "label": "少一次磁盘 IO"},
            {"a": "center", "b": "n-string", "label": "最常用的那个"},
            {"a": "center", "b": "s-split", "label": "热数据放它、全量放库"},
        ],
    },
    "redis-02": {
        "oneliner": (
            "String 不只能存字符串：INCR 做计数、SET NX 做锁、自增还能发号；"
            "学完你能用一条命令实现原子计数，并发下也不会数错。"
        ),
        "center": "String",
        "nodes": [
            {"id": "incr", "label": "INCR 原子自增", "kind": "core", "zone": "t"},
            {"id": "nx", "label": "SET NX", "kind": "core", "zone": "bl"},
            {"id": "id", "label": "分布式 ID", "kind": "core", "zone": "br"},
            {"id": "p-types", "label": "五大数据类型", "kind": "prev", "zone": "l", "code": "redis-01"},
            {"id": "n-list", "label": "List 与 Hash", "kind": "next", "zone": "r", "code": "redis-03"},
            {"id": "s-limit", "label": "限流计数器", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "incr", "label": "读改写一条命令完成"},
            {"a": "center", "b": "nx", "label": "不存在才写"},
            {"a": "center", "b": "id", "label": "INCR 就是发号器"},
            {"a": "center", "b": "p-types", "label": "最简单的那一种"},
            {"a": "center", "b": "n-list", "label": "要存多个值就换类型"},
            {"a": "center", "b": "s-limit", "label": "一分钟内超过 N 次就拒"},
        ],
    },
    "redis-03": {
        "oneliner": (
            "List 适合排队和取最新几条，Hash 适合存一个对象的多个字段；"
            "学完你能用 List 做队列、用 Hash 存用户资料，还能省下内存。"
        ),
        "center": "List 与 Hash",
        "nodes": [
            {"id": "queue", "label": "List 排队", "kind": "core", "zone": "t"},
            {"id": "hash", "label": "Hash 存对象", "kind": "core", "zone": "bl"},
            {"id": "mem", "label": "小对象省内存", "kind": "core", "zone": "br"},
            {"id": "p-string", "label": "String", "kind": "prev", "zone": "l", "code": "redis-02"},
            {"id": "n-zset", "label": "Set 与 ZSet", "kind": "next", "zone": "r", "code": "redis-04"},
            {"id": "s-mq", "label": "队列也有边界", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "queue", "label": "LPUSH + BRPOP"},
            {"a": "center", "b": "hash", "label": "一个 key 装一组字段"},
            {"a": "center", "b": "mem", "label": "字段少时更省"},
            {"a": "center", "b": "p-string", "label": "都是 value 的组织方式"},
            {"a": "center", "b": "n-zset", "label": "要排序就得再加分数"},
            {"a": "center", "b": "s-mq", "label": "没有确认和重试"},
        ],
    },
    "redis-04": {
        "oneliner": (
            "Set 天然去重、还能做交集并集，ZSet 带分数、天然按分数排序；"
            "学完你能一条命令做出实时排行榜，也能算出共同好友。"
        ),
        "center": "Set 与 ZSet",
        "nodes": [
            {"id": "set", "label": "Set 去重与交并集", "kind": "core", "zone": "t"},
            {"id": "zset", "label": "ZSet 分数排序", "kind": "core", "zone": "bl"},
            {"id": "rank", "label": "排行榜写法", "kind": "core", "zone": "br"},
            {"id": "p-list", "label": "List 与 Hash", "kind": "prev", "zone": "l", "code": "redis-03"},
            {"id": "n-ttl", "label": "过期与淘汰", "kind": "next", "zone": "r", "code": "redis-05"},
            {"id": "s-friend", "label": "共同好友", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "set", "label": "SINTER / SUNION"},
            {"a": "center", "b": "zset", "label": "ZINCRBY 加分"},
            {"a": "center", "b": "rank", "label": "ZREVRANGE 取前 N"},
            {"a": "center", "b": "p-list", "label": "都要保住顺序"},
            {"a": "center", "b": "n-ttl", "label": "榜单也要过期"},
            {"a": "center", "b": "s-friend", "label": "两个 Set 求交集"},
        ],
    },
    "redis-05": {
        "oneliner": (
            "TTL 到期不等于马上被删，Redis 用惰性删除加定期抽检；内存满了还有八种淘汰策略。"
            "学完你能给缓存设对过期时间，也不怕内存打满。"
        ),
        "center": "过期与淘汰",
        "nodes": [
            {"id": "lazy", "label": "惰性删除", "kind": "core", "zone": "t"},
            {"id": "scan", "label": "定期抽检", "kind": "core", "zone": "bl"},
            {"id": "policy", "label": "八种淘汰策略", "kind": "core", "zone": "br"},
            {"id": "p-zset", "label": "Set 与 ZSet", "kind": "prev", "zone": "l", "code": "redis-04"},
            {"id": "n-persist", "label": "持久化", "kind": "next", "zone": "r", "code": "redis-06"},
            {"id": "s-ttl", "label": "别设同一时刻过期", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "lazy", "label": "访问时才判过期"},
            {"a": "center", "b": "scan", "label": "每秒抽一批"},
            {"a": "center", "b": "policy", "label": "LRU / LFU / random"},
            {"a": "center", "b": "p-zset", "label": "热数据也要设 TTL"},
            {"a": "center", "b": "n-persist", "label": "过期数据不会被存下来"},
            {"a": "center", "b": "s-ttl", "label": "加个随机偏移"},
        ],
    },
    "redis-06": {
        "oneliner": (
            "RDB 定时拍快照、恢复快但会丢一段，AOF 记每条写命令、更安全但文件大；"
            "学完你能按业务选对持久化方式，也能配上混合持久化。"
        ),
        "center": "持久化",
        "nodes": [
            {"id": "rdb", "label": "RDB 快照", "kind": "core", "zone": "t"},
            {"id": "aof", "label": "AOF 日志", "kind": "core", "zone": "bl"},
            {"id": "mix", "label": "混合持久化", "kind": "core", "zone": "br"},
            {"id": "p-ttl", "label": "过期与淘汰", "kind": "prev", "zone": "l", "code": "redis-05"},
            {"id": "n-cache", "label": "缓存三大问题", "kind": "next", "zone": "r", "code": "redis-07"},
            {"id": "s-restart", "label": "重启要多久", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "rdb", "label": "fork 子进程写盘"},
            {"a": "center", "b": "aof", "label": "everysec 最多丢一秒"},
            {"a": "center", "b": "mix", "label": "RDB 打底 + AOF 补增量"},
            {"a": "center", "b": "p-ttl", "label": "淘汰的是内存不是磁盘"},
            {"a": "center", "b": "n-cache", "label": "只解决重启不丢"},
            {"a": "center", "b": "s-restart", "label": "AOF 大就恢复慢"},
        ],
    },
    "redis-07": {
        "oneliner": (
            "穿透是查不存在的数据、击穿是一个热点 key 过期、雪崩是一大批同时过期；"
            "学完你能分别用布隆过滤器、互斥锁、随机过期时间挡住。"
        ),
        "center": "缓存三大问题",
        "nodes": [
            {"id": "through", "label": "穿透与布隆过滤器", "kind": "core", "zone": "t"},
            {"id": "break", "label": "击穿与互斥锁", "kind": "core", "zone": "bl"},
            {"id": "avalanche", "label": "雪崩与随机 TTL", "kind": "core", "zone": "br"},
            {"id": "p-persist", "label": "持久化", "kind": "prev", "zone": "l", "code": "redis-06"},
            {"id": "n-lock", "label": "分布式锁", "kind": "next", "zone": "r", "code": "redis-08"},
            {"id": "s-null", "label": "空值也缓存一下", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "through", "label": "查了库里也没有"},
            {"a": "center", "b": "break", "label": "只让一个请求去回源"},
            {"a": "center", "b": "avalanche", "label": "别让一批 key 同时死"},
            {"a": "center", "b": "p-persist", "label": "重启后缓存全空也算雪崩"},
            {"a": "center", "b": "n-lock", "label": "互斥锁就是它的实现"},
            {"a": "center", "b": "s-null", "label": "短 TTL 存个空对象"},
        ],
    },
    "redis-08": {
        "oneliner": (
            "分布式锁要 SET NX 带过期时间、释放时校验持有者，集群要主从加哨兵做故障转移；"
            "学完你能写出不会误删别人锁的实现。"
        ),
        "center": "锁与集群",
        "nodes": [
            {"id": "setnx", "label": "SET NX 加锁", "kind": "core", "zone": "t"},
            {"id": "release", "label": "释放校验持有者", "kind": "core", "zone": "bl"},
            {"id": "cluster", "label": "主从与哨兵", "kind": "core", "zone": "br"},
            {"id": "p-cache", "label": "缓存三大问题", "kind": "prev", "zone": "l", "code": "redis-07"},
            {"id": "s-redlock", "label": "Redlock 的争议", "kind": "side", "zone": "r"},
            {"id": "s-shard", "label": "分片 cluster", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "setnx", "label": "一条命令搞定加锁和超时"},
            {"a": "center", "b": "release", "label": "Lua 比对 value 再删"},
            {"a": "center", "b": "cluster", "label": "主挂了哨兵顶上"},
            {"a": "center", "b": "p-cache", "label": "击穿那层锁就是它"},
            {"a": "center", "b": "s-redlock", "label": "多节点加锁更难保证"},
            {"a": "center", "b": "s-shard", "label": "数据多了一台放不下"},
        ],
    },
    # ---------- 计算机网络 ----------
    "net-01": {
        "oneliner": (
            "网络要一层套一层，是因为每层只解决一件事，换实现不影响别人；"
            "学完你能说清 OSI 七层与 TCP/IP 四层的对应，也知道每层有哪些协议。"
        ),
        "center": "分层模型",
        "nodes": [
            {"id": "osi", "label": "OSI 七层", "kind": "core", "zone": "t"},
            {"id": "tcpip", "label": "TCP/IP 四层", "kind": "core", "zone": "bl"},
            {"id": "encap", "label": "封装与解封装", "kind": "core", "zone": "br"},
            {"id": "n-hand", "label": "三次握手", "kind": "next", "zone": "r", "code": "net-02"},
            {"id": "s-tool", "label": "每层都有排错工具", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "osi", "label": "教学用的七层"},
            {"a": "center", "b": "tcpip", "label": "工程用的四层"},
            {"a": "center", "b": "encap", "label": "每层加一个头"},
            {"a": "center", "b": "n-hand", "label": "传输层的事"},
            {"a": "center", "b": "s-tool", "label": "ping 与 curl"},
        ],
    },
    "net-02": {
        "oneliner": (
            "三次握手是为了双方都确认「我能发、你能收」，顺便同步初始序号；"
            "学完你能画出 SYN、SYN+ACK、ACK，并说清为什么两次不够。"
        ),
        "center": "三次握手",
        "nodes": [
            {"id": "flow", "label": "SYN / ACK 过程", "kind": "core", "zone": "t"},
            {"id": "isn", "label": "初始序号 ISN", "kind": "core", "zone": "bl"},
            {"id": "why", "label": "为什么不是两次", "kind": "core", "zone": "br"},
            {"id": "p-layer", "label": "分层模型", "kind": "prev", "zone": "l", "code": "net-01"},
            {"id": "n-wave", "label": "四次挥手", "kind": "next", "zone": "r", "code": "net-03"},
            {"id": "s-flood", "label": "SYN Flood 攻击", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "flow", "label": "一来一回再确认"},
            {"a": "center", "b": "isn", "label": "双方各报一个起点"},
            {"a": "center", "b": "why", "label": "防止旧连接串进来"},
            {"a": "center", "b": "p-layer", "label": "发生在传输层"},
            {"a": "center", "b": "n-wave", "label": "关的时候要四次"},
            {"a": "center", "b": "s-flood", "label": "半连接占满队列"},
        ],
    },
    "net-03": {
        "oneliner": (
            "TCP 是全双工，两个方向各关一次，所以挥手是四次；TIME_WAIT 等 2MSL 是给最后的"
            " ACK 留重发机会。学完你能解释服务器上那堆 TIME_WAIT 是怎么回事。"
        ),
        "center": "四次挥手",
        "nodes": [
            {"id": "flow", "label": "FIN / ACK 过程", "kind": "core", "zone": "t"},
            {"id": "timewait", "label": "TIME_WAIT 与 2MSL", "kind": "core", "zone": "bl"},
            {"id": "closewait", "label": "CLOSE_WAIT 过多", "kind": "core", "zone": "br"},
            {"id": "p-hand", "label": "三次握手", "kind": "prev", "zone": "l", "code": "net-02"},
            {"id": "n-reliable", "label": "可靠传输", "kind": "next", "zone": "r", "code": "net-04"},
            {"id": "s-port", "label": "端口被占满", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "flow", "label": "各关各的方向"},
            {"a": "center", "b": "timewait", "label": "主动关闭方才有"},
            {"a": "center", "b": "closewait", "label": "多半是代码没 close"},
            {"a": "center", "b": "p-hand", "label": "建连三步、断连四步"},
            {"a": "center", "b": "n-reliable", "label": "都靠序号和确认"},
            {"a": "center", "b": "s-port", "label": "调大可用端口范围"},
        ],
    },
    "net-04": {
        "oneliner": (
            "序号让接收方能排好序、确认告诉发送方收到了哪、超时和快重传负责补发；"
            "学完你能讲清 TCP 怎么在一个会丢包的网络上装作不丢包。"
        ),
        "center": "可靠传输",
        "nodes": [
            {"id": "seq", "label": "序号与确认", "kind": "core", "zone": "t"},
            {"id": "rto", "label": "超时重传", "kind": "core", "zone": "bl"},
            {"id": "fast", "label": "快速重传", "kind": "core", "zone": "br"},
            {"id": "p-wave", "label": "四次挥手", "kind": "prev", "zone": "l", "code": "net-03"},
            {"id": "n-cong", "label": "流量与拥塞控制", "kind": "next", "zone": "r", "code": "net-05"},
            {"id": "s-ack", "label": "累计确认", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "seq", "label": "每个字节都有编号"},
            {"a": "center", "b": "rto", "label": "等不到就重发"},
            {"a": "center", "b": "fast", "label": "三个重复 ACK 立刻补"},
            {"a": "center", "b": "p-wave", "label": "断开也靠它保证"},
            {"a": "center", "b": "n-cong", "label": "重传太猛会加剧拥塞"},
            {"a": "center", "b": "s-ack", "label": "确认号之前的都收到了"},
        ],
    },
    "net-05": {
        "oneliner": (
            "滑动窗口管接收方收不收得下，拥塞控制管网络扛不扛得住；"
            "学完你能讲清慢启动、拥塞避免、快恢复分别在什么时候用。"
        ),
        "center": "两个控制",
        "nodes": [
            {"id": "window", "label": "滑动窗口", "kind": "core", "zone": "t"},
            {"id": "slow", "label": "慢启动与拥塞避免", "kind": "core", "zone": "bl"},
            {"id": "recover", "label": "快重传与快恢复", "kind": "core", "zone": "br"},
            {"id": "p-reliable", "label": "可靠传输", "kind": "prev", "zone": "l", "code": "net-04"},
            {"id": "n-udp", "label": "UDP 与 TCP", "kind": "next", "zone": "r", "code": "net-06"},
            {"id": "s-bbr", "label": "BBR 不看丢包", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "window", "label": "接收方说还能收多少"},
            {"a": "center", "b": "slow", "label": "从 1 个 MSS 开始翻倍"},
            {"a": "center", "b": "recover", "label": "丢包后别从头再来"},
            {"a": "center", "b": "p-reliable", "label": "确认和重传是前提"},
            {"a": "center", "b": "n-udp", "label": "正因为有它，TCP 才稳而慢"},
            {"a": "center", "b": "s-bbr", "label": "测带宽和延迟"},
        ],
    },
    "net-06": {
        "oneliner": (
            "TCP 什么都替你做，代价是慢；UDP 什么都不管，快但得自己兜底。"
            "学完你能按场景选：文件传输用 TCP，直播和游戏用 UDP。"
        ),
        "center": "UDP 与 TCP",
        "nodes": [
            {"id": "conn", "label": "无连接与不可靠", "kind": "core", "zone": "t"},
            {"id": "header", "label": "头部开销小", "kind": "core", "zone": "bl"},
            {"id": "choose", "label": "场景选型", "kind": "core", "zone": "br"},
            {"id": "p-cong", "label": "流量与拥塞控制", "kind": "prev", "zone": "l", "code": "net-05"},
            {"id": "n-http", "label": "HTTP 报文", "kind": "next", "zone": "r", "code": "net-07"},
            {"id": "s-quic", "label": "QUIC 建在 UDP 上", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "conn", "label": "不用握手直接发"},
            {"a": "center", "b": "header", "label": "8 字节 vs 20 字节"},
            {"a": "center", "b": "choose", "label": "要不要自己保证可靠"},
            {"a": "center", "b": "p-cong", "label": "TCP 的重活"},
            {"a": "center", "b": "n-http", "label": "HTTP 默认跑在 TCP 上"},
            {"a": "center", "b": "s-quic", "label": "可靠和拥塞自己做"},
        ],
    },
    "net-07": {
        "oneliner": (
            "请求行、请求头、空行、请求体四段构成一条 HTTP 报文，状态码第一位就说明大类；"
            "学完你能看懂抓包内容，也能凭 4xx / 5xx 判断问题出在哪边。"
        ),
        "center": "HTTP 报文",
        "nodes": [
            {"id": "struct", "label": "请求与响应结构", "kind": "core", "zone": "t"},
            {"id": "code", "label": "常见状态码", "kind": "core", "zone": "bl"},
            {"id": "field", "label": "头部字段", "kind": "core", "zone": "br"},
            {"id": "p-udp", "label": "UDP 与 TCP", "kind": "prev", "zone": "l", "code": "net-06"},
            {"id": "n-version", "label": "HTTP 版本演进", "kind": "next", "zone": "r", "code": "net-08"},
            {"id": "s-capture", "label": "抓包看报文", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "struct", "label": "起始行 + 头 + 体"},
            {"a": "center", "b": "code", "label": "首位数字看大类"},
            {"a": "center", "b": "field", "label": "Content-Type / Cookie"},
            {"a": "center", "b": "p-udp", "label": "跑在 TCP 之上"},
            {"a": "center", "b": "n-version", "label": "报文格式基本没变"},
            {"a": "center", "b": "s-capture", "label": "浏览器 F12 就能看"},
        ],
    },
    "net-08": {
        "oneliner": (
            "1.1 有队头阻塞、2 用多路复用但还是受 TCP 拖累、3 干脆换到 UDP 上；"
            "学完你能讲清三次升级各自解决了什么问题。"
        ),
        "center": "HTTP 版本",
        "nodes": [
            {"id": "hol", "label": "1.1 与队头阻塞", "kind": "core", "zone": "t"},
            {"id": "mux", "label": "2 多路复用", "kind": "core", "zone": "bl"},
            {"id": "quic", "label": "3 与 QUIC", "kind": "core", "zone": "br"},
            {"id": "p-http", "label": "HTTP 报文", "kind": "prev", "zone": "l", "code": "net-07"},
            {"id": "n-tls", "label": "HTTPS 与 TLS", "kind": "next", "zone": "r", "code": "net-09"},
            {"id": "s-hpack", "label": "头部压缩 HPACK", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "hol", "label": "一个慢请求堵住后面"},
            {"a": "center", "b": "mux", "label": "一条连接跑多个流"},
            {"a": "center", "b": "quic", "label": "丢包只影响一个流"},
            {"a": "center", "b": "p-http", "label": "语义没变、传法变了"},
            {"a": "center", "b": "n-tls", "label": "2 强制加密、3 内置 TLS"},
            {"a": "center", "b": "s-hpack", "label": "重复的头只发一次"},
        ],
    },
    "net-09": {
        "oneliner": (
            "HTTPS 先用证书验明服务器身份，再协商出一把只有双方知道的对称密钥；"
            "学完你能说清非对称加密为什么只用来换钥匙，以及证书链怎么验。"
        ),
        "center": "HTTPS",
        "nodes": [
            {"id": "cert", "label": "证书与 CA", "kind": "core", "zone": "t"},
            {"id": "exchange", "label": "密钥交换", "kind": "core", "zone": "bl"},
            {"id": "sym", "label": "对称加密传数据", "kind": "core", "zone": "br"},
            {"id": "p-version", "label": "HTTP 版本", "kind": "prev", "zone": "l", "code": "net-08"},
            {"id": "n-dns", "label": "DNS 与全流程", "kind": "next", "zone": "r", "code": "net-10"},
            {"id": "s-mitm", "label": "中间人攻击", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "cert", "label": "浏览器顺着链验到根"},
            {"a": "center", "b": "exchange", "label": "ECDHE 各出一半"},
            {"a": "center", "b": "sym", "label": "非对称太慢，只用来协商"},
            {"a": "center", "b": "p-version", "label": "HTTP over TLS"},
            {"a": "center", "b": "n-dns", "label": "全流程里的一步"},
            {"a": "center", "b": "s-mitm", "label": "证书不对就报警"},
        ],
    },
    "net-10": {
        "oneliner": (
            "从输入网址到页面出现，要经过 DNS 解析、TCP 握手、TLS 协商、发请求、渲染；"
            "学完你能把这一串串成一条完整链路，面试时每一步都讲得清。"
        ),
        "center": "URL 全流程",
        "nodes": [
            {"id": "dns", "label": "DNS 解析", "kind": "core", "zone": "t"},
            {"id": "conn", "label": "建连与请求", "kind": "core", "zone": "bl"},
            {"id": "render", "label": "浏览器渲染", "kind": "core", "zone": "br"},
            {"id": "p-tls", "label": "HTTPS 与 TLS", "kind": "prev", "zone": "l", "code": "net-09"},
            {"id": "s-cache", "label": "DNS 缓存层级", "kind": "side", "zone": "r"},
            {"id": "s-cdn", "label": "CDN 就近接入", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "dns", "label": "域名换成 IP"},
            {"a": "center", "b": "conn", "label": "握手完才发请求"},
            {"a": "center", "b": "render", "label": "HTML 到像素"},
            {"a": "center", "b": "p-tls", "label": "中间还夹一次加密协商"},
            {"a": "center", "b": "s-cache", "label": "三层缓存依次查"},
            {"a": "center", "b": "s-cdn", "label": "解析到最近的节点"},
        ],
    },
    # ---------- 数据结构 ----------
    "ds-01": {
        "oneliner": (
            "大 O 只看增长趋势，忽略常数和低阶项；"
            "学完你能估算一段代码的时间与空间复杂度，也说清 O(1)、O(n)、O(n log n) 差多少。"
        ),
        "center": "复杂度",
        "nodes": [
            {"id": "time", "label": "时间复杂度", "kind": "core", "zone": "t"},
            {"id": "space", "label": "空间复杂度", "kind": "core", "zone": "bl"},
            {"id": "order", "label": "常见量级排序", "kind": "core", "zone": "br"},
            {"id": "n-array", "label": "数组与链表", "kind": "next", "zone": "r", "code": "ds-02"},
            {"id": "s-interview", "label": "面试先问这个", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "time", "label": "循环嵌套看层数"},
            {"a": "center", "b": "space", "label": "额外开了多少"},
            {"a": "center", "b": "order", "label": "从常数到平方"},
            {"a": "center", "b": "n-array", "label": "先有尺子再比结构"},
            {"a": "center", "b": "s-interview", "label": "写完先说复杂度"},
        ],
    },
    "ds-02": {
        "oneliner": (
            "数组按下标能直接跳、但插入要挪一片；链表插入只改指针、但要顺着 next 一个个走。"
            "学完你能按读写比例选对结构。"
        ),
        "center": "数组与链表",
        "nodes": [
            {"id": "random", "label": "随机访问", "kind": "core", "zone": "t"},
            {"id": "insert", "label": "插入删除代价", "kind": "core", "zone": "bl"},
            {"id": "cache", "label": "缓存友好性", "kind": "core", "zone": "br"},
            {"id": "p-complex", "label": "复杂度", "kind": "prev", "zone": "l", "code": "ds-01"},
            {"id": "n-stack", "label": "栈与队列", "kind": "next", "zone": "r", "code": "ds-03"},
            {"id": "s-pylist", "label": "Python list 是数组", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "random", "label": "地址能算出来"},
            {"a": "center", "b": "insert", "label": "一个 O(n) 一个 O(1)"},
            {"a": "center", "b": "cache", "label": "连续内存更快"},
            {"a": "center", "b": "p-complex", "label": "对比要用同一把尺"},
            {"a": "center", "b": "n-stack", "label": "都建在这两种之上"},
            {"a": "center", "b": "s-pylist", "label": "所以头部插入很慢"},
        ],
    },
    "ds-03": {
        "oneliner": (
            "栈后进先出管回溯，队列先进先出管排队；"
            "学完你能用栈做括号匹配和撤销，用队列做 BFS 和任务排队。"
        ),
        "center": "栈与队列",
        "nodes": [
            {"id": "stack", "label": "栈 LIFO", "kind": "core", "zone": "t"},
            {"id": "queue", "label": "队列 FIFO", "kind": "core", "zone": "bl"},
            {"id": "apps", "label": "典型应用", "kind": "core", "zone": "br"},
            {"id": "p-array", "label": "数组与链表", "kind": "prev", "zone": "l", "code": "ds-02"},
            {"id": "n-hash", "label": "哈希表", "kind": "next", "zone": "r", "code": "ds-04"},
            {"id": "s-monotone", "label": "单调栈", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "stack", "label": "后进先出"},
            {"a": "center", "b": "queue", "label": "先进先出"},
            {"a": "center", "b": "apps", "label": "括号匹配 / BFS"},
            {"a": "center", "b": "p-array", "label": "用数组或链表实现"},
            {"a": "center", "b": "n-hash", "label": "都是容器，用途不同"},
            {"a": "center", "b": "s-monotone", "label": "找左右第一个更大值"},
        ],
    },
    "ds-04": {
        "oneliner": (
            "哈希函数把 key 变成下标，冲突了就用链地址或开放寻址处理；"
            "学完你能讲清平均 O(1) 是怎么来的，以及什么时候会退化成 O(n)。"
        ),
        "center": "哈希表",
        "nodes": [
            {"id": "hash", "label": "哈希函数", "kind": "core", "zone": "t"},
            {"id": "collision", "label": "冲突解决", "kind": "core", "zone": "bl"},
            {"id": "resize", "label": "扩容与负载因子", "kind": "core", "zone": "br"},
            {"id": "p-stack", "label": "栈与队列", "kind": "prev", "zone": "l", "code": "ds-03"},
            {"id": "n-tree", "label": "树与遍历", "kind": "next", "zone": "r", "code": "ds-05"},
            {"id": "s-pydict", "label": "Python dict 的实现", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "hash", "label": "同样的 key 同样的下标"},
            {"a": "center", "b": "collision", "label": "拉链或往后找空位"},
            {"a": "center", "b": "resize", "label": "装太满就要扩"},
            {"a": "center", "b": "p-stack", "label": "用途完全不同"},
            {"a": "center", "b": "n-tree", "label": "要有序就换结构"},
            {"a": "center", "b": "s-pydict", "label": "开放寻址 + 紧凑数组"},
        ],
    },
    "ds-05": {
        "oneliner": (
            "前序适合复制、中序能出有序序列、后序算子树结果、层序按层处理；"
            "学完你能写出四种遍历，并知道每道题该用哪一种。"
        ),
        "center": "二叉树遍历",
        "nodes": [
            {"id": "order", "label": "前中后序", "kind": "core", "zone": "t"},
            {"id": "recursive", "label": "递归与迭代", "kind": "core", "zone": "bl"},
            {"id": "level", "label": "层序遍历", "kind": "core", "zone": "br"},
            {"id": "p-hash", "label": "哈希表", "kind": "prev", "zone": "l", "code": "ds-04"},
            {"id": "n-bst", "label": "二叉搜索树", "kind": "next", "zone": "r", "code": "ds-06"},
            {"id": "s-expr", "label": "表达式树", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "order", "label": "根在哪就是哪种序"},
            {"a": "center", "b": "recursive", "label": "递归简单、迭代省栈"},
            {"a": "center", "b": "level", "label": "用队列一层层来"},
            {"a": "center", "b": "p-hash", "label": "树是另一种组织方式"},
            {"a": "center", "b": "n-bst", "label": "中序能出有序"},
            {"a": "center", "b": "s-expr", "label": "后序求值最方便"},
        ],
    },
    "ds-06": {
        "oneliner": (
            "左小右大让查找能一路排除一半，但树歪了就退化成链表；"
            "学完你能写出查找与插入，也知道为什么还需要平衡树。"
        ),
        "center": "二叉搜索树",
        "nodes": [
            {"id": "prop", "label": "有序性质", "kind": "core", "zone": "t"},
            {"id": "crud", "label": "查找与插入", "kind": "core", "zone": "bl"},
            {"id": "degenerate", "label": "退化与平衡", "kind": "core", "zone": "br"},
            {"id": "p-tree", "label": "树与遍历", "kind": "prev", "zone": "l", "code": "ds-05"},
            {"id": "n-heap", "label": "堆与优先队列", "kind": "next", "zone": "r", "code": "ds-07"},
            {"id": "s-inorder", "label": "中序就是排序", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "prop", "label": "左边全小、右边全大"},
            {"a": "center", "b": "crud", "label": "每层砍掉一半"},
            {"a": "center", "b": "degenerate", "label": "有序插入会变成链表"},
            {"a": "center", "b": "p-tree", "label": "遍历是它的基础"},
            {"a": "center", "b": "n-heap", "label": "只关心最值就用堆"},
            {"a": "center", "b": "s-inorder", "label": "中序输出天然递增"},
        ],
    },
    "ds-07": {
        "oneliner": (
            "堆只保证堆顶是最值，插入和弹出都是 O(log n)；"
            "学完你能用最小堆做 TopK 和任务调度，而不必整体排序。"
        ),
        "center": "堆",
        "nodes": [
            {"id": "prop", "label": "堆的性质", "kind": "core", "zone": "t"},
            {"id": "sift", "label": "上浮与下沉", "kind": "core", "zone": "bl"},
            {"id": "topk", "label": "TopK 应用", "kind": "core", "zone": "br"},
            {"id": "p-bst", "label": "二叉搜索树", "kind": "prev", "zone": "l", "code": "ds-06"},
            {"id": "n-sort", "label": "排序算法", "kind": "next", "zone": "r", "code": "ds-08"},
            {"id": "s-heapq", "label": "Python heapq", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "prop", "label": "父节点总比子节点小"},
            {"a": "center", "b": "sift", "label": "调整只需一条路径"},
            {"a": "center", "b": "topk", "label": "留 k 个就够"},
            {"a": "center", "b": "p-bst", "label": "弱化版但更快"},
            {"a": "center", "b": "n-sort", "label": "堆排就是反复取顶"},
            {"a": "center", "b": "s-heapq", "label": "是最小堆，取最大要取负"},
        ],
    },
    "ds-08": {
        "oneliner": (
            "快排平均最快但会退化、归并稳定但要额外空间、堆排原地但不稳定；"
            "学完你能按数据特点选排序，也能说清「稳定」到底影响什么。"
        ),
        "center": "排序算法",
        "nodes": [
            {"id": "quick", "label": "快排与分区", "kind": "core", "zone": "t"},
            {"id": "merge", "label": "归并与稳定性", "kind": "core", "zone": "bl"},
            {"id": "compare", "label": "复杂度对比", "kind": "core", "zone": "br"},
            {"id": "p-heap", "label": "堆", "kind": "prev", "zone": "l", "code": "ds-07"},
            {"id": "n-binary", "label": "二分查找", "kind": "next", "zone": "r", "code": "ds-09"},
            {"id": "s-timsort", "label": "sort 是 Timsort", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "quick", "label": "选错基准就退化成 O(n²)"},
            {"a": "center", "b": "merge", "label": "相等元素顺序不变"},
            {"a": "center", "b": "compare", "label": "时间 / 空间 / 稳定"},
            {"a": "center", "b": "p-heap", "label": "堆排也是 O(n log n)"},
            {"a": "center", "b": "n-binary", "label": "排好才能二分"},
            {"a": "center", "b": "s-timsort", "label": "归并加插入的混合"},
        ],
    },
    "ds-09": {
        "oneliner": (
            "二分的难点不在思路而在边界：left 加不加一、循环用小于还是小于等于；"
            "学完你能一次写对左闭右开区间和找左右边界的模板。"
        ),
        "center": "二分查找",
        "nodes": [
            {"id": "invariant", "label": "循环不变量", "kind": "core", "zone": "t"},
            {"id": "bound", "label": "左右边界", "kind": "core", "zone": "bl"},
            {"id": "bug", "label": "溢出与死循环", "kind": "core", "zone": "br"},
            {"id": "p-sort", "label": "排序算法", "kind": "prev", "zone": "l", "code": "ds-08"},
            {"id": "n-graph", "label": "图与 BFS/DFS", "kind": "next", "zone": "r", "code": "ds-10"},
            {"id": "s-answer", "label": "二分答案", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "invariant", "label": "答案永远在区间里"},
            {"a": "center", "b": "bound", "label": "找第一个 / 最后一个"},
            {"a": "center", "b": "bug", "label": "mid 防溢出"},
            {"a": "center", "b": "p-sort", "label": "有序是前提"},
            {"a": "center", "b": "n-graph", "label": "都是 O(log n) 的直觉"},
            {"a": "center", "b": "s-answer", "label": "对答案本身二分"},
        ],
    },
    "ds-10": {
        "oneliner": (
            "BFS 一层层扩散能求无权最短路，DFS 一路走到底能找连通块；"
            "学完你能写出两种遍历，并知道什么时候该用哪一个。"
        ),
        "center": "图遍历",
        "nodes": [
            {"id": "store", "label": "邻接表与矩阵", "kind": "core", "zone": "t"},
            {"id": "bfs", "label": "BFS 与最短路", "kind": "core", "zone": "bl"},
            {"id": "dfs", "label": "DFS 与回溯", "kind": "core", "zone": "br"},
            {"id": "p-binary", "label": "二分查找", "kind": "prev", "zone": "l", "code": "ds-09"},
            {"id": "s-topo", "label": "拓扑排序", "kind": "side", "zone": "r"},
            {"id": "s-union", "label": "并查集", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "store", "label": "先想怎么存边"},
            {"a": "center", "b": "bfs", "label": "队列 + 标记已访问"},
            {"a": "center", "b": "dfs", "label": "递归 + 撤销选择"},
            {"a": "center", "b": "p-binary", "label": "都是遍历思想"},
            {"a": "center", "b": "s-topo", "label": "有向无环图排任务"},
            {"a": "center", "b": "s-union", "label": "只问连通不问路径"},
        ],
    },
    # ---------- 操作系统 ----------
    "os-01": {
        "oneliner": (
            "进程是资源分配的单位、线程是 CPU 调度的单位，同一进程的线程共享内存；"
            "学完你能说清切换开销差在哪，以及什么时候该用多进程。"
        ),
        "center": "进程与线程",
        "nodes": [
            {"id": "unit", "label": "资源与调度单位", "kind": "core", "zone": "t"},
            {"id": "share", "label": "共享与隔离", "kind": "core", "zone": "bl"},
            {"id": "switch", "label": "切换开销", "kind": "core", "zone": "br"},
            {"id": "n-state", "label": "进程状态与调度", "kind": "next", "zone": "r", "code": "os-02"},
            {"id": "s-gil", "label": "多进程绕开 GIL", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "unit", "label": "一个分资源一个分 CPU"},
            {"a": "center", "b": "share", "label": "线程共享堆、各有栈"},
            {"a": "center", "b": "switch", "label": "线程切换更便宜"},
            {"a": "center", "b": "n-state", "label": "都要被调度"},
            {"a": "center", "b": "s-gil", "label": "CPU 密集就用进程"},
        ],
    },
    "os-02": {
        "oneliner": (
            "进程在就绪、运行、阻塞之间来回迁移，调度算法决定下一个谁上 CPU；"
            "学完你能画出状态图，也能说清时间片轮转和优先级调度的取舍。"
        ),
        "center": "状态与调度",
        "nodes": [
            {"id": "states", "label": "三态与迁移", "kind": "core", "zone": "t"},
            {"id": "algo", "label": "调度算法", "kind": "core", "zone": "bl"},
            {"id": "ctx", "label": "上下文切换", "kind": "core", "zone": "br"},
            {"id": "p-pc", "label": "进程与线程", "kind": "prev", "zone": "l", "code": "os-01"},
            {"id": "n-ipc", "label": "进程间通信", "kind": "next", "zone": "r", "code": "os-03"},
            {"id": "s-zombie", "label": "僵尸进程", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "states", "label": "就绪 / 运行 / 阻塞"},
            {"a": "center", "b": "algo", "label": "FCFS / 时间片 / 优先级"},
            {"a": "center", "b": "ctx", "label": "保存再恢复现场"},
            {"a": "center", "b": "p-pc", "label": "调度对象是线程"},
            {"a": "center", "b": "n-ipc", "label": "切换后要能协作"},
            {"a": "center", "b": "s-zombie", "label": "退出了但父进程没回收"},
        ],
    },
    "os-03": {
        "oneliner": (
            "管道只能单向传字节、消息队列有边界、共享内存最快但要自己加锁；"
            "学完你能按数据量和同步需求选对 IPC 方式。"
        ),
        "center": "进程间通信",
        "nodes": [
            {"id": "pipe", "label": "管道与 FIFO", "kind": "core", "zone": "t"},
            {"id": "mq", "label": "消息队列", "kind": "core", "zone": "bl"},
            {"id": "shm", "label": "共享内存与信号量", "kind": "core", "zone": "br"},
            {"id": "p-state", "label": "状态与调度", "kind": "prev", "zone": "l", "code": "os-02"},
            {"id": "n-deadlock", "label": "死锁", "kind": "next", "zone": "r", "code": "os-04"},
            {"id": "s-socket", "label": "socket 能跨机器", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "pipe", "label": "只能亲缘进程用"},
            {"a": "center", "b": "mq", "label": "有类型有优先级"},
            {"a": "center", "b": "shm", "label": "零拷贝但要同步"},
            {"a": "center", "b": "p-state", "label": "阻塞和唤醒靠它"},
            {"a": "center", "b": "n-deadlock", "label": "等锁等出环"},
            {"a": "center", "b": "s-socket", "label": "本机也走这套"},
        ],
    },
    "os-04": {
        "oneliner": (
            "互斥、占有并等待、不可抢占、循环等待，四个条件同时成立才会死锁；"
            "学完你能说出打破其中任意一个的具体做法。"
        ),
        "center": "死锁",
        "nodes": [
            {"id": "four", "label": "四个必要条件", "kind": "core", "zone": "t"},
            {"id": "prevent", "label": "预防与避免", "kind": "core", "zone": "bl"},
            {"id": "detect", "label": "检测与恢复", "kind": "core", "zone": "br"},
            {"id": "p-ipc", "label": "进程间通信", "kind": "prev", "zone": "l", "code": "os-03"},
            {"id": "n-page", "label": "分页与分段", "kind": "next", "zone": "r", "code": "os-05"},
            {"id": "s-db", "label": "数据库死锁", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "four", "label": "少一个就不会死"},
            {"a": "center", "b": "prevent", "label": "按顺序申请锁"},
            {"a": "center", "b": "detect", "label": "银行家算法 / 超时回滚"},
            {"a": "center", "b": "p-ipc", "label": "共享资源才有争抢"},
            {"a": "center", "b": "n-page", "label": "内存也会被占住"},
            {"a": "center", "b": "s-db", "label": "两边顺序反了就互等"},
        ],
    },
    "os-05": {
        "oneliner": (
            "分页把内存切成固定大小的块、分段按逻辑划分，段页式先分段再分页；"
            "学完你能讲清虚拟地址怎么翻译成物理地址、碎片到底从哪来。"
        ),
        "center": "内存管理",
        "nodes": [
            {"id": "page", "label": "分页与页表", "kind": "core", "zone": "t"},
            {"id": "seg", "label": "分段", "kind": "core", "zone": "bl"},
            {"id": "segpage", "label": "段页式与 TLB", "kind": "core", "zone": "br"},
            {"id": "p-deadlock", "label": "死锁", "kind": "prev", "zone": "l", "code": "os-04"},
            {"id": "n-virtual", "label": "虚拟内存", "kind": "next", "zone": "r", "code": "os-06"},
            {"id": "s-frag", "label": "内部与外部碎片", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "page", "label": "地址 = 页号 + 偏移"},
            {"a": "center", "b": "seg", "label": "按代码段数据段切"},
            {"a": "center", "b": "segpage", "label": "两级翻译 + 快表"},
            {"a": "center", "b": "p-deadlock", "label": "资源分配的另一面"},
            {"a": "center", "b": "n-virtual", "label": "页表撑起虚拟空间"},
            {"a": "center", "b": "s-frag", "label": "分页只有内部碎片"},
        ],
    },
    "os-06": {
        "oneliner": (
            "虚拟内存让每个进程都以为自己独占内存，缺页了再从磁盘换进来；"
            "学完你能说清 FIFO、LRU、Clock 的差别，以及「抖动」是怎么发生的。"
        ),
        "center": "虚拟内存",
        "nodes": [
            {"id": "fault", "label": "缺页中断", "kind": "core", "zone": "t"},
            {"id": "algo", "label": "置换算法", "kind": "core", "zone": "bl"},
            {"id": "thrash", "label": "抖动", "kind": "core", "zone": "br"},
            {"id": "p-page", "label": "分页与分段", "kind": "prev", "zone": "l", "code": "os-05"},
            {"id": "n-fs", "label": "文件系统", "kind": "next", "zone": "r", "code": "os-07"},
            {"id": "s-locality", "label": "局部性原理", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "fault", "label": "不在内存就去取"},
            {"a": "center", "b": "algo", "label": "LRU 最常用"},
            {"a": "center", "b": "thrash", "label": "内存太小就一直换"},
            {"a": "center", "b": "p-page", "label": "建立在页表之上"},
            {"a": "center", "b": "n-fs", "label": "换页也走磁盘"},
            {"a": "center", "b": "s-locality", "label": "所以才值得缓存"},
        ],
    },
    "os-07": {
        "oneliner": (
            "inode 存文件的元信息和数据块指针，文件名只是目录里的一条映射；"
            "学完你能讲清软链接和硬链接的区别，也知道删文件到底删了什么。"
        ),
        "center": "文件系统",
        "nodes": [
            {"id": "inode", "label": "inode 存什么", "kind": "core", "zone": "t"},
            {"id": "dir", "label": "目录与路径", "kind": "core", "zone": "bl"},
            {"id": "link", "label": "软硬链接", "kind": "core", "zone": "br"},
            {"id": "p-virtual", "label": "虚拟内存", "kind": "prev", "zone": "l", "code": "os-06"},
            {"id": "n-io", "label": "五种 IO 模型", "kind": "next", "zone": "r", "code": "os-08"},
            {"id": "s-df", "label": "df 和 du 对不上", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "inode", "label": "除名字外的都在这"},
            {"a": "center", "b": "dir", "label": "目录就是一张名字表"},
            {"a": "center", "b": "link", "label": "硬链接同一个 inode"},
            {"a": "center", "b": "p-virtual", "label": "都要和磁盘打交道"},
            {"a": "center", "b": "n-io", "label": "读写文件就是 IO"},
            {"a": "center", "b": "s-df", "label": "删了但进程还占着"},
        ],
    },
    "os-08": {
        "oneliner": (
            "从阻塞到非阻塞、多路复用、信号驱动、异步，差别在于「谁来等」；"
            "学完你能说清 select、poll、epoll 的区别，以及 epoll 为什么快。"
        ),
        "center": "IO 模型",
        "nodes": [
            {"id": "block", "label": "阻塞与非阻塞", "kind": "core", "zone": "t"},
            {"id": "mux", "label": "IO 多路复用", "kind": "core", "zone": "bl"},
            {"id": "epoll", "label": "epoll 的本质", "kind": "core", "zone": "br"},
            {"id": "p-fs", "label": "文件系统", "kind": "prev", "zone": "l", "code": "os-07"},
            {"id": "n-cmd", "label": "排查命令", "kind": "next", "zone": "r", "code": "os-09"},
            {"id": "s-redis", "label": "Redis 为什么快", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "block", "label": "等的时候能不能干别的"},
            {"a": "center", "b": "mux", "label": "一个线程看多个 fd"},
            {"a": "center", "b": "epoll", "label": "事件回调不用轮询"},
            {"a": "center", "b": "p-fs", "label": "读文件就是一次 IO"},
            {"a": "center", "b": "n-cmd", "label": "IO 高要能看出来"},
            {"a": "center", "b": "s-redis", "label": "单线程 + epoll"},
        ],
    },
    "os-09": {
        "oneliner": (
            "top 看 CPU、free 看内存、iostat 看磁盘、ss 看连接，再配合 grep 定位；"
            "学完你能按「先看整体再揪进程」的顺序排查线上问题。"
        ),
        "center": "排查命令",
        "nodes": [
            {"id": "cpu", "label": "CPU 与负载", "kind": "core", "zone": "t"},
            {"id": "mem", "label": "内存与 swap", "kind": "core", "zone": "bl"},
            {"id": "disk", "label": "磁盘与网络", "kind": "core", "zone": "br"},
            {"id": "p-io", "label": "五种 IO 模型", "kind": "prev", "zone": "l", "code": "os-08"},
            {"id": "s-flame", "label": "火焰图", "kind": "side", "zone": "r"},
            {"id": "s-log", "label": "先看日志再猜", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "cpu", "label": "load 高未必是算力"},
            {"a": "center", "b": "mem", "label": "swap 用了就慢"},
            {"a": "center", "b": "disk", "label": "iostat / ss / lsof"},
            {"a": "center", "b": "p-io", "label": "IO 高先分清是哪类"},
            {"a": "center", "b": "s-flame", "label": "看热点在哪个函数"},
            {"a": "center", "b": "s-log", "label": "命令只告诉你现象"},
        ],
    },
    # ---------- 数据分析与处理 ----------
    "da-01": {
        "oneliner": (
            "NumPy 用整块数组做运算，底层是 C 循环，比 Python 的 for 快几十倍；"
            "学完你能把逐元素循环改写成向量化操作，代码还更短。"
        ),
        "center": "NumPy",
        "nodes": [
            {"id": "ndarray", "label": "ndarray 与形状", "kind": "core", "zone": "t"},
            {"id": "vector", "label": "向量化运算", "kind": "core", "zone": "bl"},
            {"id": "broadcast", "label": "广播机制", "kind": "core", "zone": "br"},
            {"id": "n-pandas", "label": "Pandas", "kind": "next", "zone": "r", "code": "da-02"},
            {"id": "s-list", "label": "和 list 的区别", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "ndarray", "label": "同类型、定长、连续内存"},
            {"a": "center", "b": "vector", "label": "不用写 for"},
            {"a": "center", "b": "broadcast", "label": "形状不同也能算"},
            {"a": "center", "b": "n-pandas", "label": "DataFrame 底层就是它"},
            {"a": "center", "b": "s-list", "label": "list 什么都能装但慢"},
        ],
    },
    "da-02": {
        "oneliner": (
            "Series 是一列带索引的数据，DataFrame 是多列共享同一个索引；"
            "学完你能按下标、按标签、按条件三种方式把想要的数据取出来。"
        ),
        "center": "DataFrame",
        "nodes": [
            {"id": "series", "label": "Series 与索引", "kind": "core", "zone": "t"},
            {"id": "pick", "label": "选行选列", "kind": "core", "zone": "bl"},
            {"id": "loc", "label": "loc 与 iloc", "kind": "core", "zone": "br"},
            {"id": "p-numpy", "label": "NumPy", "kind": "prev", "zone": "l", "code": "da-01"},
            {"id": "n-read", "label": "数据读取", "kind": "next", "zone": "r", "code": "da-03"},
            {"id": "s-excel", "label": "就是一张 Excel", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "series", "label": "一列就是一个 Series"},
            {"a": "center", "b": "pick", "label": "df[col] / 布尔条件"},
            {"a": "center", "b": "loc", "label": "按标签还是按位置"},
            {"a": "center", "b": "p-numpy", "label": "运算还是数组那套"},
            {"a": "center", "b": "n-read", "label": "先读进来才有它"},
            {"a": "center", "b": "s-excel", "label": "行列结构一一对应"},
        ],
    },
    "da-03": {
        "oneliner": (
            "读进来第一件事是看 dtypes、head、describe，先确认类型对不对；"
            "学完你能一眼看出「数字被读成字符串」这类最常见的坑。"
        ),
        "center": "读取与体检",
        "nodes": [
            {"id": "read", "label": "read_csv 参数", "kind": "core", "zone": "t"},
            {"id": "dtype", "label": "dtypes 与 info", "kind": "core", "zone": "bl"},
            {"id": "describe", "label": "head / describe", "kind": "core", "zone": "br"},
            {"id": "p-frame", "label": "DataFrame", "kind": "prev", "zone": "l", "code": "da-02"},
            {"id": "n-clean", "label": "清洗三板斧", "kind": "next", "zone": "r", "code": "da-04"},
            {"id": "s-encoding", "label": "编码与分隔符", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "read", "label": "sep / encoding / dtype"},
            {"a": "center", "b": "dtype", "label": "类型错后面全错"},
            {"a": "center", "b": "describe", "label": "先看分布有没有离谱值"},
            {"a": "center", "b": "p-frame", "label": "读进来就是 DataFrame"},
            {"a": "center", "b": "n-clean", "label": "体检完才知道洗什么"},
            {"a": "center", "b": "s-encoding", "label": "中文乱码多半是这里"},
        ],
    },
    "da-04": {
        "oneliner": (
            "缺失值可以删、可以填、也可以先标记；重复值先查再删；异常值要分清是错误还是真实极端。"
            "学完你能写出一套可复用的清洗流程。"
        ),
        "center": "数据清洗",
        "nodes": [
            {"id": "na", "label": "缺失值处理", "kind": "core", "zone": "t"},
            {"id": "dup", "label": "重复值", "kind": "core", "zone": "bl"},
            {"id": "outlier", "label": "异常值识别", "kind": "core", "zone": "br"},
            {"id": "p-read", "label": "读取与体检", "kind": "prev", "zone": "l", "code": "da-03"},
            {"id": "n-group", "label": "分组聚合", "kind": "next", "zone": "r", "code": "da-05"},
            {"id": "s-fill", "label": "填充要有依据", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "na", "label": "dropna / fillna"},
            {"a": "center", "b": "dup", "label": "duplicated 看、drop 删"},
            {"a": "center", "b": "outlier", "label": "3σ 还是箱线图"},
            {"a": "center", "b": "p-read", "label": "先体检再动手"},
            {"a": "center", "b": "n-group", "label": "洗不干净统计就偏"},
            {"a": "center", "b": "s-fill", "label": "别用 0 填所有空"},
        ],
    },
    "da-05": {
        "oneliner": (
            "groupby 按某些列分组、再对每组算指标，是分析里最常用的工具；"
            "学完你能写出「每个城市每月的均值」这类多层分组统计。"
        ),
        "center": "分组聚合",
        "nodes": [
            {"id": "group", "label": "groupby 分组", "kind": "core", "zone": "t"},
            {"id": "agg", "label": "agg 多指标", "kind": "core", "zone": "bl"},
            {"id": "index", "label": "多层索引", "kind": "core", "zone": "br"},
            {"id": "p-clean", "label": "数据清洗", "kind": "prev", "zone": "l", "code": "da-04"},
            {"id": "n-pivot", "label": "连接与透视", "kind": "next", "zone": "r", "code": "da-06"},
            {"id": "s-sql", "label": "和 SQL 一一对应", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "group", "label": "先按谁分组"},
            {"a": "center", "b": "agg", "label": "一次算多个统计量"},
            {"a": "center", "b": "index", "label": "reset_index 拍平"},
            {"a": "center", "b": "p-clean", "label": "空值会被跳过"},
            {"a": "center", "b": "n-pivot", "label": "统计完常要换方向"},
            {"a": "center", "b": "s-sql", "label": "GROUP BY 的孪生兄弟"},
        ],
    },
    "da-06": {
        "oneliner": (
            "merge 按 key 对齐两张表、pivot 把行变成列、melt 再变回来；"
            "学完你能在宽表和长表之间自由转换，也能合并多份数据源。"
        ),
        "center": "表连接与重塑",
        "nodes": [
            {"id": "merge", "label": "merge 与连接方式", "kind": "core", "zone": "t"},
            {"id": "pivot", "label": "pivot 与 melt", "kind": "core", "zone": "bl"},
            {"id": "shape", "label": "长表与宽表", "kind": "core", "zone": "br"},
            {"id": "p-group", "label": "分组聚合", "kind": "prev", "zone": "l", "code": "da-05"},
            {"id": "n-time", "label": "时间序列", "kind": "next", "zone": "r", "code": "da-07"},
            {"id": "s-join", "label": "对照 SQL JOIN", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "merge", "label": "how 决定保哪边"},
            {"a": "center", "b": "pivot", "label": "行转列、列转行"},
            {"a": "center", "b": "shape", "label": "画图要长表、报表要宽表"},
            {"a": "center", "b": "p-group", "label": "透视前先聚合"},
            {"a": "center", "b": "n-time", "label": "多源数据先对齐"},
            {"a": "center", "b": "s-join", "label": "left / inner 一个意思"},
        ],
    },
    "da-07": {
        "oneliner": (
            "时间列要先转成 datetime，才能取年月日、做重采样和滑动窗口；"
            "学完你能把原始时间戳整理成按天或按月的趋势数据。"
        ),
        "center": "时间序列",
        "nodes": [
            {"id": "parse", "label": "to_datetime", "kind": "core", "zone": "t"},
            {"id": "fields", "label": "dt 取字段", "kind": "core", "zone": "bl"},
            {"id": "resample", "label": "重采样与滚动", "kind": "core", "zone": "br"},
            {"id": "p-pivot", "label": "连接与透视", "kind": "prev", "zone": "l", "code": "da-06"},
            {"id": "n-viz", "label": "可视化与结论", "kind": "next", "zone": "r", "code": "da-08"},
            {"id": "s-tz", "label": "时区别忽略", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "parse", "label": "字符串变时间类型"},
            {"a": "center", "b": "fields", "label": "dt.year / dt.month"},
            {"a": "center", "b": "resample", "label": "按周按月聚合"},
            {"a": "center", "b": "p-pivot", "label": "先对齐再算"},
            {"a": "center", "b": "n-viz", "label": "趋势图最常画时间"},
            {"a": "center", "b": "s-tz", "label": "跨时区会差一天"},
        ],
    },
    "da-08": {
        "oneliner": (
            "图的作用是给结论做证据，不是好看；"
            "学完你能选对图型、标出关键数字，并用一段带数据的结论收尾。"
        ),
        "center": "可视化结论",
        "nodes": [
            {"id": "chart", "label": "图型选择", "kind": "core", "zone": "t"},
            {"id": "mark", "label": "关键标注", "kind": "core", "zone": "bl"},
            {"id": "conclusion", "label": "结论带数字", "kind": "core", "zone": "br"},
            {"id": "p-time", "label": "时间序列", "kind": "prev", "zone": "l", "code": "da-07"},
            {"id": "s-mislead", "label": "别让坐标轴说谎", "kind": "side", "zone": "r"},
            {"id": "s-report", "label": "一页纸结构", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "chart", "label": "趋势折线、对比柱状"},
            {"a": "center", "b": "mark", "label": "把峰值和拐点标出来"},
            {"a": "center", "b": "conclusion", "label": "涨了多少、占比多少"},
            {"a": "center", "b": "p-time", "label": "时序数据最适合画图"},
            {"a": "center", "b": "s-mislead", "label": "截断 Y 轴会放大差异"},
            {"a": "center", "b": "s-report", "label": "结论在前、证据在后"},
        ],
    },
    # ---------- Transformer ----------
    "tf-01": {
        "oneliner": (
            "RNN 必须一步步算、长距离信息会一路衰减，Attention 让任意两个位置直接相连；"
            "学完你能说清 Transformer 为什么能并行训练。"
        ),
        "center": "为什么用 Attention",
        "nodes": [
            {"id": "rnn", "label": "RNN 的两个瓶颈", "kind": "core", "zone": "t"},
            {"id": "direct", "label": "注意力直连", "kind": "core", "zone": "bl"},
            {"id": "parallel", "label": "并行化", "kind": "core", "zone": "br"},
            {"id": "n-selfattn", "label": "Self-Attention", "kind": "next", "zone": "r", "code": "tf-02"},
            {"id": "s-long", "label": "长距离依赖", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "rnn", "label": "不能并行 + 信息衰减"},
            {"a": "center", "b": "direct", "label": "任意两步距离都是 1"},
            {"a": "center", "b": "parallel", "label": "整句一起算"},
            {"a": "center", "b": "n-selfattn", "label": "具体怎么算"},
            {"a": "center", "b": "s-long", "label": "再远也能直接看"},
        ],
    },
    "tf-02": {
        "oneliner": (
            "每个词生成 Q、K、V，用 Q 和所有 K 点积算相关性，再拿权重加权 V；"
            "学完你能手动推一遍注意力矩阵的形状变化。"
        ),
        "center": "Self-Attention",
        "nodes": [
            {"id": "qkv", "label": "Q / K / V 是什么", "kind": "core", "zone": "t"},
            {"id": "score", "label": "点积算权重", "kind": "core", "zone": "bl"},
            {"id": "weighted", "label": "加权求和", "kind": "core", "zone": "br"},
            {"id": "p-why", "label": "为什么用 Attention", "kind": "prev", "zone": "l", "code": "tf-01"},
            {"id": "n-scale", "label": "缩放点积", "kind": "next", "zone": "r", "code": "tf-03"},
            {"id": "s-attn", "label": "注意力可视化", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "qkv", "label": "查询、键、值三个投影"},
            {"a": "center", "b": "score", "label": "QKᵀ 得到 n×n"},
            {"a": "center", "b": "weighted", "label": "softmax 后乘 V"},
            {"a": "center", "b": "p-why", "label": "它是那套思路的实现"},
            {"a": "center", "b": "n-scale", "label": "下一步是数值稳定"},
            {"a": "center", "b": "s-attn", "label": "看词和词怎么对上"},
        ],
    },
    "tf-03": {
        "oneliner": (
            "点积会随维度变大而变大、把 softmax 推到饱和，所以要除以根号 d_k；"
            "学完你能说清温度、mask 和数值稳定性各自在解决什么。"
        ),
        "center": "缩放点积",
        "nodes": [
            {"id": "scale", "label": "为什么除以 √d_k", "kind": "core", "zone": "t"},
            {"id": "softmax", "label": "Softmax 与温度", "kind": "core", "zone": "bl"},
            {"id": "mask", "label": "mask 机制", "kind": "core", "zone": "br"},
            {"id": "p-self", "label": "Self-Attention", "kind": "prev", "zone": "l", "code": "tf-02"},
            {"id": "n-multi", "label": "多头注意力", "kind": "next", "zone": "r", "code": "tf-04"},
            {"id": "s-overflow", "label": "上溢与下溢", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "scale", "label": "方差拉回 1"},
            {"a": "center", "b": "softmax", "label": "温度越高越平"},
            {"a": "center", "b": "mask", "label": "填充位和未来位要遮"},
            {"a": "center", "b": "p-self", "label": "它是注意力的最后一步"},
            {"a": "center", "b": "n-multi", "label": "多个头各算一遍"},
            {"a": "center", "b": "s-overflow", "label": "exp 太大就 inf"},
        ],
    },
    "tf-04": {
        "oneliner": (
            "把 Q、K、V 各投影到多组子空间并行算注意力，最后拼接再线性变换；"
            "学完你能说清多头到底「多」在哪，以及为什么不是简单重复。"
        ),
        "center": "多头注意力",
        "nodes": [
            {"id": "split", "label": "拆头与投影", "kind": "core", "zone": "t"},
            {"id": "parallel", "label": "并行与拼接", "kind": "core", "zone": "bl"},
            {"id": "heads", "label": "每个头学到什么", "kind": "core", "zone": "br"},
            {"id": "p-scale", "label": "缩放点积", "kind": "prev", "zone": "l", "code": "tf-03"},
            {"id": "n-pos", "label": "位置编码", "kind": "next", "zone": "r", "code": "tf-05"},
            {"id": "s-num", "label": "头数怎么选", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "split", "label": "d_model 切成 h 份"},
            {"a": "center", "b": "parallel", "label": "h 个注意力同时算"},
            {"a": "center", "b": "heads", "label": "有的看语法有的看指代"},
            {"a": "center", "b": "p-scale", "label": "每个头内部都用它"},
            {"a": "center", "b": "n-pos", "label": "多头的输出还要加位置"},
            {"a": "center", "b": "s-num", "label": "总维度不变、头数可调"},
        ],
    },
    "tf-05": {
        "oneliner": (
            "自注意力本身不区分顺序，位置信息要靠位置编码补进去；"
            "学完你能对比正弦编码和可学习编码，也说得清 RoPE 的思路。"
        ),
        "center": "位置编码",
        "nodes": [
            {"id": "why", "label": "为什么需要", "kind": "core", "zone": "t"},
            {"id": "sincos", "label": "正弦编码", "kind": "core", "zone": "bl"},
            {"id": "rope", "label": "RoPE 与相对位置", "kind": "core", "zone": "br"},
            {"id": "p-multi", "label": "多头注意力", "kind": "prev", "zone": "l", "code": "tf-04"},
            {"id": "n-arch", "label": "整体架构", "kind": "next", "zone": "r", "code": "tf-06"},
            {"id": "s-extrapolate", "label": "长度外推", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "why", "label": "词袋模型分不出先后"},
            {"a": "center", "b": "sincos", "label": "不同频率的三角函数"},
            {"a": "center", "b": "rope", "label": "旋转 Q 和 K"},
            {"a": "center", "b": "p-multi", "label": "加在输入上"},
            {"a": "center", "b": "n-arch", "label": "每个 block 都带"},
            {"a": "center", "b": "s-extrapolate", "label": "训练短、推理长怎么办"},
        ],
    },
    "tf-06": {
        "oneliner": (
            "每个子层都是「算完再加回原输入」的残差，再接 LayerNorm；"
            "学完你能画出 Encoder 和 Decoder 的完整结构图，并说清归一化放在哪。"
        ),
        "center": "整体架构",
        "nodes": [
            {"id": "encdec", "label": "Encoder / Decoder", "kind": "core", "zone": "t"},
            {"id": "residual", "label": "残差连接", "kind": "core", "zone": "bl"},
            {"id": "norm", "label": "归一化放哪", "kind": "core", "zone": "br"},
            {"id": "p-pos", "label": "位置编码", "kind": "prev", "zone": "l", "code": "tf-05"},
            {"id": "n-bert", "label": "BERT 与 GPT", "kind": "next", "zone": "r", "code": "tf-07"},
            {"id": "s-preln", "label": "Post-LN vs Pre-LN", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "encdec", "label": "编码器堆栈 + 解码器堆栈"},
            {"a": "center", "b": "residual", "label": "梯度能直接回传"},
            {"a": "center", "b": "norm", "label": "层内归一化稳定训练"},
            {"a": "center", "b": "p-pos", "label": "进第一层前就加上"},
            {"a": "center", "b": "n-bert", "label": "只用其中一半"},
            {"a": "center", "b": "s-preln", "label": "深层训练差很多"},
        ],
    },
    "tf-07": {
        "oneliner": (
            "BERT 用双向编码做填空、GPT 用单向解码接下一个词；"
            "学完你能按任务选路线，也说得清 encoder-only 适合什么场景。"
        ),
        "center": "BERT 与 GPT",
        "nodes": [
            {"id": "obj", "label": "训练目标差异", "kind": "core", "zone": "t"},
            {"id": "mask", "label": "注意力掩码", "kind": "core", "zone": "bl"},
            {"id": "task", "label": "适用任务", "kind": "core", "zone": "br"},
            {"id": "p-arch", "label": "整体架构", "kind": "prev", "zone": "l", "code": "tf-06"},
            {"id": "n-kv", "label": "推理加速", "kind": "next", "zone": "r", "code": "tf-08"},
            {"id": "s-t5", "label": "T5 两半都要", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "obj", "label": "完形填空 vs 续写"},
            {"a": "center", "b": "mask", "label": "能不能看到后面"},
            {"a": "center", "b": "task", "label": "分类检索 vs 生成"},
            {"a": "center", "b": "p-arch", "label": "同一套 block"},
            {"a": "center", "b": "n-kv", "label": "生成才需要缓存"},
            {"a": "center", "b": "s-t5", "label": "encoder 加 decoder"},
        ],
    },
    "tf-08": {
        "oneliner": (
            "生成第 n 个词时，前面词的 K、V 可以复用，不必每次重算；"
            "学完你能算清 KV Cache 省了多少计算、又多占多少显存。"
        ),
        "center": "KV Cache",
        "nodes": [
            {"id": "why", "label": "为什么要缓存", "kind": "core", "zone": "t"},
            {"id": "trade", "label": "显存换计算", "kind": "core", "zone": "bl"},
            {"id": "paged", "label": "批处理与分页", "kind": "core", "zone": "br"},
            {"id": "p-bert", "label": "BERT 与 GPT", "kind": "prev", "zone": "l", "code": "tf-07"},
            {"id": "s-ttft", "label": "首 token 延迟", "kind": "side", "zone": "r"},
            {"id": "s-quant", "label": "量化与蒸馏", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "why", "label": "每步只算新词"},
            {"a": "center", "b": "trade", "label": "缓存长度线性增长"},
            {"a": "center", "b": "paged", "label": "显存碎片也要管"},
            {"a": "center", "b": "p-bert", "label": "只有自回归解码才用"},
            {"a": "center", "b": "s-ttft", "label": "预填充阶段最慢"},
            {"a": "center", "b": "s-quant", "label": "压小模型权重"},
        ],
    },
    # ---------- RAG 检索工程 ----------
    "rag-chunk": {
        "oneliner": (
            "按标题层级切、块之间留一点重叠，块太大检索不准、太小丢上下文；"
            "学完你能给一份文档定出合理的块大小和重叠长度。"
        ),
        "center": "文本分块",
        "nodes": [
            {"id": "heading", "label": "标题层级切分", "kind": "core", "zone": "t"},
            {"id": "overlap", "label": "重叠窗口", "kind": "core", "zone": "bl"},
            {"id": "size", "label": "块大小权衡", "kind": "core", "zone": "br"},
            {"id": "n-token", "label": "中文分词", "kind": "next", "zone": "r", "code": "rag-tokenize"},
            {"id": "s-semantic", "label": "语义分块", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "heading", "label": "跟着文档结构走"},
            {"a": "center", "b": "overlap", "label": "别把一句话切断"},
            {"a": "center", "b": "size", "label": "300~800 字起步"},
            {"a": "center", "b": "n-token", "label": "切完才能分词"},
            {"a": "center", "b": "s-semantic", "label": "按语义边界切更贵"},
        ],
    },
    "rag-tokenize": {
        "oneliner": (
            "中文没有空格，得靠分词把句子切成词，专有名词还要加自定义词典；"
            "学完你能让关键词检索正确召回到「召回率」这类术语。"
        ),
        "center": "中文分词",
        "nodes": [
            {"id": "jieba", "label": "分词器选型", "kind": "core", "zone": "t"},
            {"id": "dict", "label": "自定义词典", "kind": "core", "zone": "bl"},
            {"id": "stop", "label": "停用词", "kind": "core", "zone": "br"},
            {"id": "p-chunk", "label": "文本分块", "kind": "prev", "zone": "l", "code": "rag-chunk"},
            {"id": "n-bm25", "label": "BM25 检索", "kind": "next", "zone": "r", "code": "rag-bm25"},
            {"id": "s-term", "label": "专有名词召回", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "jieba", "label": "jieba / pkuseg"},
            {"a": "center", "b": "dict", "label": "把业务词加进去"},
            {"a": "center", "b": "stop", "label": "的了吗要去掉"},
            {"a": "center", "b": "p-chunk", "label": "块切好再分词"},
            {"a": "center", "b": "n-bm25", "label": "分词质量决定召回"},
            {"a": "center", "b": "s-term", "label": "「召回率」别被切成两个词"},
        ],
    },
    "rag-bm25": {
        "oneliner": (
            "BM25 靠词频和逆文档频率打分，再用 k1、b 两个参数压住长文档刷分；"
            "学完你能解释为什么关键词检索在专名和代码上比向量更准。"
        ),
        "center": "BM25",
        "nodes": [
            {"id": "tfidf", "label": "TF 与 IDF", "kind": "core", "zone": "t"},
            {"id": "params", "label": "k1 与 b 参数", "kind": "core", "zone": "bl"},
            {"id": "formula", "label": "打分公式", "kind": "core", "zone": "br"},
            {"id": "p-token", "label": "中文分词", "kind": "prev", "zone": "l", "code": "rag-tokenize"},
            {"id": "n-hybrid", "label": "混合检索", "kind": "next", "zone": "r", "code": "rag-hybrid"},
            {"id": "s-code", "label": "代码和报错检索", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "tfidf", "label": "越稀有越值钱"},
            {"a": "center", "b": "params", "label": "b 控制长度惩罚"},
            {"a": "center", "b": "formula", "label": "分母是词频饱和项"},
            {"a": "center", "b": "p-token", "label": "分错词就全错"},
            {"a": "center", "b": "n-hybrid", "label": "和向量互补"},
            {"a": "center", "b": "s-code", "label": "精确匹配更强"},
        ],
    },
    "rag-hybrid": {
        "oneliner": (
            "向量管语义、BM25 管专名，两路结果要用 RRF 或加权的方式合成一个排名；"
            "学完你能搭出召回率明显更高的混合检索。"
        ),
        "center": "混合检索",
        "nodes": [
            {"id": "dual", "label": "两路召回", "kind": "core", "zone": "t"},
            {"id": "rrf", "label": "RRF 融合", "kind": "core", "zone": "bl"},
            {"id": "weight", "label": "权重调参", "kind": "core", "zone": "br"},
            {"id": "p-bm25", "label": "BM25", "kind": "prev", "zone": "l", "code": "rag-bm25"},
            {"id": "n-rerank", "label": "Reranker", "kind": "next", "zone": "r", "code": "rag-rerank"},
            {"id": "s-scale", "label": "两路分数不可比", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "dual", "label": "各取 Top-50"},
            {"a": "center", "b": "rrf", "label": "按名次融合不看分数"},
            {"a": "center", "b": "weight", "label": "归一化后再加权"},
            {"a": "center", "b": "p-bm25", "label": "其中一路"},
            {"a": "center", "b": "n-rerank", "label": "融合完再精排"},
            {"a": "center", "b": "s-scale", "label": "一个是 0~1 一个是无穷"},
        ],
    },
    "rag-rerank": {
        "oneliner": (
            "粗排要快要全、精排要准，交叉编码器把 query 和文档一起送进模型打分；"
            "学完你能用重排把 Top-20 收敛成真正有用的 Top-5。"
        ),
        "center": "重排",
        "nodes": [
            {"id": "stage", "label": "两阶段架构", "kind": "core", "zone": "t"},
            {"id": "cross", "label": "交叉编码器", "kind": "core", "zone": "bl"},
            {"id": "latency", "label": "延迟与收益", "kind": "core", "zone": "br"},
            {"id": "p-hybrid", "label": "混合检索", "kind": "prev", "zone": "l", "code": "rag-hybrid"},
            {"id": "n-embed", "label": "Embedding", "kind": "next", "zone": "r", "code": "rag-embedding"},
            {"id": "s-metric", "label": "看 R@K 指标", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "stage", "label": "先粗后精"},
            {"a": "center", "b": "cross", "label": "两段文本一起进模型"},
            {"a": "center", "b": "latency", "label": "只能排几十条"},
            {"a": "center", "b": "p-hybrid", "label": "重排的输入"},
            {"a": "center", "b": "n-embed", "label": "粗排靠它"},
            {"a": "center", "b": "s-metric", "label": "重排后 R@4 有没有涨"},
        ],
    },
    "rag-embedding": {
        "oneliner": (
            "Embedding 把文本映射成向量，归一化之后点积就等于余弦相似度；"
            "学完你能选对模型、处理维度与距离度量，也知道换模型要重建索引。"
        ),
        "center": "Embedding",
        "nodes": [
            {"id": "vec", "label": "文本转向量", "kind": "core", "zone": "t"},
            {"id": "norm", "label": "归一化", "kind": "core", "zone": "bl"},
            {"id": "metric", "label": "距离度量", "kind": "core", "zone": "br"},
            {"id": "p-rerank", "label": "重排", "kind": "prev", "zone": "l", "code": "rag-rerank"},
            {"id": "n-vectordb", "label": "向量数据库", "kind": "next", "zone": "r", "code": "rag-vector-db"},
            {"id": "s-rebuild", "label": "换模型要重建", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "vec", "label": "一句一个定长向量"},
            {"a": "center", "b": "norm", "label": "长度统一成 1"},
            {"a": "center", "b": "metric", "label": "cos / 点积 / L2"},
            {"a": "center", "b": "p-rerank", "label": "粗排的主力"},
            {"a": "center", "b": "n-vectordb", "label": "存进去才有得查"},
            {"a": "center", "b": "s-rebuild", "label": "维度变了索引就废"},
        ],
    },
    "rag-vector-db": {
        "oneliner": (
            "全库扫描太慢，要用 HNSW 或 IVF 做近似最近邻，用 nprobe 换速度与召回；"
            "学完你能选对索引类型，也知道参数调大调小各自牺牲什么。"
        ),
        "center": "向量数据库",
        "nodes": [
            {"id": "ann", "label": "ANN 索引", "kind": "core", "zone": "t"},
            {"id": "index", "label": "HNSW 与 IVF", "kind": "core", "zone": "bl"},
            {"id": "nprobe", "label": "nprobe 与召回", "kind": "core", "zone": "br"},
            {"id": "p-embed", "label": "Embedding", "kind": "prev", "zone": "l", "code": "rag-embedding"},
            {"id": "n-ingest", "label": "入库流水线", "kind": "next", "zone": "r", "code": "rag-ingest"},
            {"id": "s-filter", "label": "过滤与分区", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "ann", "label": "牺牲一点精度换速度"},
            {"a": "center", "b": "index", "label": "图索引 vs 聚类索引"},
            {"a": "center", "b": "nprobe", "label": "探测越多越准越慢"},
            {"a": "center", "b": "p-embed", "label": "存的就是它的输出"},
            {"a": "center", "b": "n-ingest", "label": "数据从流水线来"},
            {"a": "center", "b": "s-filter", "label": "带条件检索会掉召回"},
        ],
    },
    "rag-ingest": {
        "oneliner": (
            "解析、切块、向量化、写库是一条流水线，靠文件指纹比对只处理变动的部分；"
            "学完你能把全量重建改成增量更新，省下大部分时间。"
        ),
        "center": "入库流水线",
        "nodes": [
            {"id": "steps", "label": "四步流水线", "kind": "core", "zone": "t"},
            {"id": "hash", "label": "指纹比对", "kind": "core", "zone": "bl"},
            {"id": "delta", "label": "增量与删除", "kind": "core", "zone": "br"},
            {"id": "p-vectordb", "label": "向量数据库", "kind": "prev", "zone": "l", "code": "rag-vector-db"},
            {"id": "n-dedup", "label": "知识库去重", "kind": "next", "zone": "r", "code": "rag-dedup"},
            {"id": "s-idem", "label": "失败重试要幂等", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "steps", "label": "解析→切块→向量→写库"},
            {"a": "center", "b": "hash", "label": "内容哈希没变就跳过"},
            {"a": "center", "b": "delta", "label": "删文档要连向量一起删"},
            {"a": "center", "b": "p-vectordb", "label": "写进哪里"},
            {"a": "center", "b": "n-dedup", "label": "入库前先查重"},
            {"a": "center", "b": "s-idem", "label": "重复跑不会写两遍"},
        ],
    },
    "rag-dedup": {
        "oneliner": (
            "重复文档会挤占 Top-K、让模型误判重要性，得同时去掉完全重复和语义近似；"
            "学完你能用哈希加向量阈值这两道筛，把知识库清干净。"
        ),
        "center": "知识库去重",
        "nodes": [
            {"id": "hash", "label": "哈希精确去重", "kind": "core", "zone": "t"},
            {"id": "norm", "label": "文本归一化", "kind": "core", "zone": "bl"},
            {"id": "semantic", "label": "语义阈值", "kind": "core", "zone": "br"},
            {"id": "p-ingest", "label": "入库流水线", "kind": "prev", "zone": "l", "code": "rag-ingest"},
            {"id": "s-topk", "label": "Top-K 被挤占", "kind": "side", "zone": "r"},
            {"id": "s-version", "label": "版本更新怎么留", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "hash", "label": "一模一样直接丢"},
            {"a": "center", "b": "norm", "label": "空格全半角先统一"},
            {"a": "center", "b": "semantic", "label": "相似度 0.95 以上算重复"},
            {"a": "center", "b": "p-ingest", "label": "流水线里的一道闸"},
            {"a": "center", "b": "s-topk", "label": "四条结果三条一样"},
            {"a": "center", "b": "s-version", "label": "留最新版、软删旧版"},
        ],
    },
    # ---------- 后端服务工程 ----------
    "be-fastapi": {
        "oneliner": (
            "路由按注册顺序匹配、依赖注入负责把数据库和当前用户送进函数；"
            "学完你能说清 404 和 405 的区别，也知道路由顺序会埋什么坑。"
        ),
        "center": "FastAPI",
        "nodes": [
            {"id": "route", "label": "路由注册与顺序", "kind": "core", "zone": "t"},
            {"id": "di", "label": "依赖注入", "kind": "core", "zone": "bl"},
            {"id": "model", "label": "请求与响应模型", "kind": "core", "zone": "br"},
            {"id": "n-auth", "label": "JWT 认证", "kind": "next", "zone": "r", "code": "be-auth"},
            {"id": "s-405", "label": "405 和 404 不一样", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "route", "label": "先注册的先匹配"},
            {"a": "center", "b": "di", "label": "Depends 自动注入"},
            {"a": "center", "b": "model", "label": "Pydantic 管进出"},
            {"a": "center", "b": "n-auth", "label": "鉴权也是个依赖"},
            {"a": "center", "b": "s-405", "label": "路径对方法错就是 405"},
        ],
    },
    "be-auth": {
        "oneliner": (
            "JWT 是签名不是加密，payload 谁都能解开；密码要用 bcrypt 这类慢哈希。"
            "学完你能做出登录、鉴权和密码存储的正确姿势。"
        ),
        "center": "认证",
        "nodes": [
            {"id": "jwt", "label": "JWT 结构", "kind": "core", "zone": "t"},
            {"id": "bcrypt", "label": "密码慢哈希", "kind": "core", "zone": "bl"},
            {"id": "stateless", "label": "无状态与过期", "kind": "core", "zone": "br"},
            {"id": "p-fastapi", "label": "FastAPI", "kind": "prev", "zone": "l", "code": "be-fastapi"},
            {"id": "n-sse", "label": "SSE 流式输出", "kind": "next", "zone": "r", "code": "be-sse"},
            {"id": "s-refresh", "label": "刷新 token", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "jwt", "label": "三段用点号拼"},
            {"a": "center", "b": "bcrypt", "label": "加盐 + 慢，抗爆破"},
            {"a": "center", "b": "stateless", "label": "服务端不用存会话"},
            {"a": "center", "b": "p-fastapi", "label": "挂在依赖里"},
            {"a": "center", "b": "n-sse", "label": "流式接口也要鉴权"},
            {"a": "center", "b": "s-refresh", "label": "两个 token 分工"},
        ],
    },
    "be-sse": {
        "oneliner": (
            "SSE 用 text/event-stream 一条条推 data，多行内容每行都要加 data: 前缀；"
            "学完你能写出不掉包、有心跳保活的流式接口。"
        ),
        "center": "SSE",
        "nodes": [
            {"id": "format", "label": "事件流格式", "kind": "core", "zone": "t"},
            {"id": "multi", "label": "多行 data", "kind": "core", "zone": "bl"},
            {"id": "heartbeat", "label": "心跳与重连", "kind": "core", "zone": "br"},
            {"id": "p-auth", "label": "JWT 认证", "kind": "prev", "zone": "l", "code": "be-auth"},
            {"id": "n-limit", "label": "限流", "kind": "next", "zone": "r", "code": "be-ratelimit"},
            {"id": "s-ws", "label": "对比 WebSocket", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "format", "label": "data: xxx 加两个换行"},
            {"a": "center", "b": "multi", "label": "少一个前缀就断包"},
            {"a": "center", "b": "heartbeat", "label": "定时发注释保活"},
            {"a": "center", "b": "p-auth", "label": "先鉴权再开流"},
            {"a": "center", "b": "n-limit", "label": "长连接更怕被打满"},
            {"a": "center", "b": "s-ws", "label": "单向推送用 SSE 就够"},
        ],
    },
    "be-ratelimit": {
        "oneliner": (
            "固定窗口会在边界处放进来两倍流量，滑动窗口用 ZSet 记录每次请求的时间戳；"
            "学完你能写出精确限流，也能用令牌桶控制突发。"
        ),
        "center": "限流",
        "nodes": [
            {"id": "fixwin", "label": "固定窗口的边界", "kind": "core", "zone": "t"},
            {"id": "slide", "label": "滑动窗口 ZSet", "kind": "core", "zone": "bl"},
            {"id": "token", "label": "令牌桶", "kind": "core", "zone": "br"},
            {"id": "p-sse", "label": "SSE 流式输出", "kind": "prev", "zone": "l", "code": "be-sse"},
            {"id": "n-task", "label": "后台异步任务", "kind": "next", "zone": "r", "code": "be-async-task"},
            {"id": "s-429", "label": "超限要返回 429", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "fixwin", "label": "59 秒和 61 秒各来一批"},
            {"a": "center", "b": "slide", "label": "先清窗口外的"},
            {"a": "center", "b": "token", "label": "允许一定突发"},
            {"a": "center", "b": "p-sse", "label": "长连接要限并发"},
            {"a": "center", "b": "n-task", "label": "限流后可以排队"},
            {"a": "center", "b": "s-429", "label": "带上 Retry-After"},
        ],
    },
    "be-async-task": {
        "oneliner": (
            "耗时任务丢到队列里异步跑，失败要退避重试、还要防重复执行；"
            "学完你能做到一个任务失败不拖死整批。"
        ),
        "center": "异步任务",
        "nodes": [
            {"id": "queue", "label": "队列与 worker", "kind": "core", "zone": "t"},
            {"id": "retry", "label": "退避重试", "kind": "core", "zone": "bl"},
            {"id": "idem", "label": "幂等与死信", "kind": "core", "zone": "br"},
            {"id": "p-limit", "label": "限流", "kind": "prev", "zone": "l", "code": "be-ratelimit"},
            {"id": "n-pay", "label": "支付订单", "kind": "next", "zone": "r", "code": "be-payment"},
            {"id": "s-status", "label": "任务状态可查", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "queue", "label": "生产者只管投递"},
            {"a": "center", "b": "retry", "label": "指数退避加热抖动"},
            {"a": "center", "b": "idem", "label": "重试多次也只生效一次"},
            {"a": "center", "b": "p-limit", "label": "限流后正好排队"},
            {"a": "center", "b": "n-pay", "label": "回调也当成任务"},
            {"a": "center", "b": "s-status", "label": "前端轮询进度"},
        ],
    },
    "be-payment": {
        "oneliner": (
            "下单锁金额、回调要验签、同一笔回调可能来多次必须幂等；"
            "学完你能避开重复发卡这种真实的资金损失。"
        ),
        "center": "支付",
        "nodes": [
            {"id": "lock", "label": "金额与库存锁定", "kind": "core", "zone": "t"},
            {"id": "sign", "label": "回调验签", "kind": "core", "zone": "bl"},
            {"id": "idem", "label": "幂等键", "kind": "core", "zone": "br"},
            {"id": "p-task", "label": "异步任务", "kind": "prev", "zone": "l", "code": "be-async-task"},
            {"id": "s-recon", "label": "对账与补偿", "kind": "side", "zone": "r"},
            {"id": "s-fsm", "label": "订单状态机", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "lock", "label": "先占住再付"},
            {"a": "center", "b": "sign", "label": "不验签谁都能伪造"},
            {"a": "center", "b": "idem", "label": "同一订单号只处理一次"},
            {"a": "center", "b": "p-task", "label": "发货丢到后台"},
            {"a": "center", "b": "s-recon", "label": "每天比对流水"},
            {"a": "center", "b": "s-fsm", "label": "待付→已付→已发"},
        ],
    },
    # ---------- 多模态与部署 ----------
    "mm-vision": {
        "oneliner": (
            "把图片和文字一起送进模型，再要求它按 schema 返回 JSON；"
            "学完你能从截图里稳定抽出字段，而不是拿到一段散文。"
        ),
        "center": "视觉理解",
        "nodes": [
            {"id": "msg", "label": "图文消息格式", "kind": "core", "zone": "t"},
            {"id": "struct", "label": "结构化输出", "kind": "core", "zone": "bl"},
            {"id": "check", "label": "字段校验", "kind": "core", "zone": "br"},
            {"id": "n-ocr", "label": "OCR 解析", "kind": "next", "zone": "r", "code": "mm-ocr"},
            {"id": "s-cost", "label": "图片压缩省成本", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "msg", "label": "image_url + text"},
            {"a": "center", "b": "struct", "label": "让它按字段吐"},
            {"a": "center", "b": "check", "label": "缺字段就打回重来"},
            {"a": "center", "b": "n-ocr", "label": "纯文字识别另有路线"},
            {"a": "center", "b": "s-cost", "label": "大图 token 很贵"},
        ],
    },
    "mm-ocr": {
        "oneliner": (
            "OCR 给的是带坐标的碎行，要按坐标聚成段落、再还原表格结构；"
            "学完你能把扫描件整理成可检索的干净文本。"
        ),
        "center": "OCR 解析",
        "nodes": [
            {"id": "coord", "label": "坐标与行合并", "kind": "core", "zone": "t"},
            {"id": "para", "label": "段落还原", "kind": "core", "zone": "bl"},
            {"id": "table", "label": "表格结构", "kind": "core", "zone": "br"},
            {"id": "p-vision", "label": "视觉理解", "kind": "prev", "zone": "l", "code": "mm-vision"},
            {"id": "n-docker", "label": "Docker 部署", "kind": "next", "zone": "r", "code": "mm-docker"},
            {"id": "s-skew", "label": "倾斜与模糊", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "coord", "label": "同一行 y 接近"},
            {"a": "center", "b": "para", "label": "空行和缩进是线索"},
            {"a": "center", "b": "table", "label": "按列对齐还原"},
            {"a": "center", "b": "p-vision", "label": "复杂版面交给多模态"},
            {"a": "center", "b": "n-docker", "label": "OCR 服务要单独部署"},
            {"a": "center", "b": "s-skew", "label": "先纠偏再识别"},
        ],
    },
    "mm-docker": {
        "oneliner": (
            "镜像分层能复用缓存、compose 用一个文件起多个服务；depends_on 只管启动顺序、不管就绪。"
            "学完你能写出一份到哪都能跑的部署配置。"
        ),
        "center": "容器部署",
        "nodes": [
            {"id": "dockerfile", "label": "Dockerfile 分层", "kind": "core", "zone": "t"},
            {"id": "compose", "label": "compose 编排", "kind": "core", "zone": "bl"},
            {"id": "health", "label": "健康检查", "kind": "core", "zone": "br"},
            {"id": "p-ocr", "label": "OCR 解析", "kind": "prev", "zone": "l", "code": "mm-ocr"},
            {"id": "n-mp", "label": "微信小程序", "kind": "next", "zone": "r", "code": "mm-miniprogram"},
            {"id": "s-depends", "label": "depends_on 的局限", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "dockerfile", "label": "依赖先装、代码后拷"},
            {"a": "center", "b": "compose", "label": "服务 / 网络 / 卷"},
            {"a": "center", "b": "health", "label": "healthy 才算起来"},
            {"a": "center", "b": "p-ocr", "label": "重依赖的服务更该容器化"},
            {"a": "center", "b": "n-mp", "label": "后端照样跑在容器里"},
            {"a": "center", "b": "s-depends", "label": "起来了不代表能连"},
        ],
    },
    "mm-miniprogram": {
        "oneliner": (
            "小程序登录要拿 code 换 session、401 不能直接弹给用户而要静默重登一次；"
            "学完你能做出不打断用户的登录态续期。"
        ),
        "center": "小程序",
        "nodes": [
            {"id": "login", "label": "code 换 session", "kind": "core", "zone": "t"},
            {"id": "relogin", "label": "401 静默重登", "kind": "core", "zone": "bl"},
            {"id": "retry", "label": "请求重试幂等", "kind": "core", "zone": "br"},
            {"id": "p-docker", "label": "Docker 部署", "kind": "prev", "zone": "l", "code": "mm-docker"},
            {"id": "s-size", "label": "分包与体积限制", "kind": "side", "zone": "r"},
            {"id": "s-domain", "label": "域名要备案", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "login", "label": "wx.login 拿 code"},
            {"a": "center", "b": "relogin", "label": "重登后重放原请求"},
            {"a": "center", "b": "retry", "label": "别把重试做成重复下单"},
            {"a": "center", "b": "p-docker", "label": "后端还是那套"},
            {"a": "center", "b": "s-size", "label": "主包 2MB 起步"},
            {"a": "center", "b": "s-domain", "label": "请求域名必须白名单"},
        ],
    },
    # ---------- AI 工程质量 ----------
    "ai-grounding": {
        "oneliner": (
            "允许模型说「不知道」比让它硬编强得多，答案还要能指回原文；"
            "学完你能给回答加引用、加置信度，并用拒答兜住超纲问题。"
        ),
        "center": "防幻觉",
        "nodes": [
            {"id": "refuse", "label": "拒答策略", "kind": "core", "zone": "t"},
            {"id": "cite", "label": "引用与溯源", "kind": "core", "zone": "bl"},
            {"id": "score", "label": "置信度", "kind": "core", "zone": "br"},
            {"id": "n-router", "label": "三级路由", "kind": "next", "zone": "r", "code": "ai-router"},
            {"id": "s-nocontext", "label": "检索不到就别硬答", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "refuse", "label": "阈值不到就说不知道"},
            {"a": "center", "b": "cite", "label": "每句都能点回原文"},
            {"a": "center", "b": "score", "label": "检索分数当置信度"},
            {"a": "center", "b": "n-router", "label": "低置信的交给更强模型"},
            {"a": "center", "b": "s-nocontext", "label": "空结果直接兜底"},
        ],
    },
    "ai-router": {
        "oneliner": (
            "能用规则判的别调模型、小模型能搞定的别上大模型，只有兜底才走全量；"
            "学完你能把热路径的延迟和成本一起压下来。"
        ),
        "center": "三级路由",
        "nodes": [
            {"id": "rule", "label": "规则优先", "kind": "core", "zone": "t"},
            {"id": "small", "label": "小模型判类", "kind": "core", "zone": "bl"},
            {"id": "big", "label": "大模型兜底", "kind": "core", "zone": "br"},
            {"id": "p-ground", "label": "防幻觉", "kind": "prev", "zone": "l", "code": "ai-grounding"},
            {"id": "n-chart", "label": "图表渲染", "kind": "next", "zone": "r", "code": "ai-chart"},
            {"id": "s-observe", "label": "路由要可观测", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "rule", "label": "关键词命中直接走"},
            {"a": "center", "b": "small", "label": "便宜、够快"},
            {"a": "center", "b": "big", "label": "只处理疑难"},
            {"a": "center", "b": "p-ground", "label": "兜底前先查检索"},
            {"a": "center", "b": "n-chart", "label": "出图也是一条分支"},
            {"a": "center", "b": "s-observe", "label": "各层命中率要统计"},
        ],
    },
    "ai-chart": {
        "oneliner": (
            "服务端先把数据整成前端要的形状、再渲染成图，别把二十根柱子塞给用户；"
            "学完你能做出真正读得懂的图表，而不是挤成一团的标签。"
        ),
        "center": "图表渲染",
        "nodes": [
            {"id": "shape", "label": "数据整形", "kind": "core", "zone": "t"},
            {"id": "type", "label": "图型与聚合", "kind": "core", "zone": "bl"},
            {"id": "server", "label": "服务端渲染", "kind": "core", "zone": "br"},
            {"id": "p-router", "label": "三级路由", "kind": "prev", "zone": "l", "code": "ai-router"},
            {"id": "s-topn", "label": "Top-N 加其他", "kind": "side", "zone": "r"},
            {"id": "s-tick", "label": "标签要能读", "kind": "side", "zone": "b"},
        ],
        "edges": [
            {"a": "center", "b": "shape", "label": "列名和单位要统一"},
            {"a": "center", "b": "type", "label": "趋势折线、占比饼图"},
            {"a": "center", "b": "server", "label": "生成图片或配置"},
            {"a": "center", "b": "p-router", "label": "路由决定要不要画"},
            {"a": "center", "b": "s-topn", "label": "别让长尾挤满坐标轴"},
            {"a": "center", "b": "s-tick", "label": "斜着放或者抽稀"},
        ],
    },
}


def sketch_of(code: str) -> dict | None:
    """取某课的知识图数据；没铺到的课返回 None（前端自动不渲染）。"""
    return SKETCHES.get(code)
