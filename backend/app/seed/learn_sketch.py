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

⚠️ 覆盖进度：2026-10-27 先做 Python 前 10 课试点，其余课走 `summary` 兜底（前端自动降级，
   不显示知识图）。铺完 135 课再把 `SKETCHES` 补满。
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
            {"a": "center", "b": "basic", "label": "int / float / str / bool"},
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
}


def sketch_of(code: str) -> dict | None:
    """取某课的知识图数据；没铺到的课返回 None（前端自动不渲染）。"""
    return SKETCHES.get(code)
