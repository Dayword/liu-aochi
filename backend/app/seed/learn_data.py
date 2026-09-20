"""数据分析与处理：NumPy、Pandas 与一份完整分析。

动手题用真实运行的数据分析代码，由服务端断言判定。
"""

DA01_CHECKER = """
import numpy as np
try:
    assert np.allclose(amount, [200.0, 250.0, 320.0, 960.0]), "amount 应该是逐元素相乘的结果 [200, 250, 320, 960]，检查是不是用 prices * qty（写成 np.dot 或 @ 会得到一个标量）"
    assert abs(float(revenue) - 1730.0) < 1e-9, "总销售额 revenue 应该是 200 + 250 + 320 + 960 = 1730"
    _second = total_amount(np.array([10.0, 20.0]), np.array([3, 5]))
    assert _second is not None, "total_amount 要把结果 return 出来，只 print 不算"
    assert abs(float(_second) - 130.0) < 1e-9, "换一组输入：单价 [10, 20] 乘销量 [3, 5] 应得总额 130，说明代码不能把 1730 写死"
    assert np.allclose(high, [250.0, 320.0]), "high 要用布尔索引 prices[prices > 100] 取出单价大于 100 的两个值，应该是 [250, 320]"
    assert np.allclose(col_mean, [82.66666667, 89.33333333, 78.66666667]), "col_mean 是每门课（每一列）的均分，scores.mean(axis=0) 应该约等于 [82.67, 89.33, 78.67]"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DA02_CHECKER = """
import pandas as pd
try:
    assert tuple(shape) == (4, 4), "df.shape 应该是 (4, 4)：4 行 4 列，别把行列写反"
    assert abs(float(avg_salary) - 16000.0) < 1e-9, "平均薪资 avg_salary 应该是 (18000 + 22000 + 15000 + 9000) / 4 = 16000"
    assert "salary_k" in df.columns, "要新增一列 salary_k（df.assign 或 df['salary_k'] = ... 都可以）"
    assert list(df["salary_k"]) == [18.0, 22.0, 15.0, 9.0], "salary_k 是薪资除以 1000，应该得到 [18.0, 22.0, 15.0, 9.0]"
    assert list(high) == ["张伟", "李娜"], "high 要筛出薪资高于平均值 16000 的人名，应该是 ['张伟', '李娜']，写法是 df.loc[df['salary'] > avg_salary, 'name']"
    _d2 = pd.DataFrame({"score": [5, 9, 1, 7]})
    _top3 = top_values(_d2, "score", 3)
    assert _top3 is not None, "top_values 要把结果 return 出来"
    assert list(_top3) == [9, 7, 5], "换一张表：score 列降序取前 3 个应该是 [9, 7, 5]，说明列名和数量要按参数来，不能写死"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DA03_CHECKER = """
import pandas as pd
try:
    assert tuple(raw.shape) == (6, 3), "raw 是题目给好的 6 行 3 列，不要改它"
    assert bad == 2, "amount 里转不成数字的有 2 条（'88元' 和 'abc'），用 pd.to_numeric(..., errors='coerce') 之后再数 isna()"
    assert list(amount.fillna(-1)) == [128.5, 99.0, -1.0, -1.0, 230.0, 45.0], "转换后的 amount 应该是 [128.5, 99, NaN, NaN, 230, 45]，重点看两个 NaN 的位置对不对"
    assert unknown == 1, "city 里值为 'Unknown' 的只有 1 条，先把 'Unknown' 换成缺失值再数 isna()"
    assert list(city.fillna("缺失")) == ["北京", "上海", "北京", "北京", "缺失", "北京"], "city 要先 .str.strip() 去首尾空格，再把 'Unknown' 换成缺失值，得到 ['北京', '上海', '北京', '北京', 缺失, '北京']"
    assert not amount_is_numeric, "raw['amount'] 现在还是字符串列（dtype 是 str），is_numeric_dtype 应该是 False，说明这批数据还没转干净"
    _n2 = to_number(" 7 ")
    assert _n2 is not None and abs(float(_n2) - 7.0) < 1e-9, "换一个输入：to_number(' 7 ') 应该返回 7.0，字符串两边可能有空格"
    assert abs(float(to_number("12.5")) - 12.5) < 1e-9, "to_number('12.5') 应该返回 12.5"
    assert to_number("abc") is None, "to_number('abc') 应该返回 None，表示这条数据转不出来，而不是让程序崩掉"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DA04_CHECKER = """
import numpy as np
import pandas as pd
try:
    assert tuple(dedup.shape) == (7, 3), "orders 有 8 行，其中 A04 整行重复了一次，drop_duplicates() 之后应该是 7 行"
    assert list(dedup["order_id"]) == ["A01", "A02", "A03", "A04", "A06", "A07", "A08"], "去重后留下的是第一次出现的那批行，order_id 应该是 A01 A02 A03 A04 A06 A07 A08"
    assert list(amount_filled) == [120.0, 145.0, 130.0, 150.0, 160.0, 140.0, 99999.0], "amount 列的非空值是 [120, 130, 150, 160, 140, 99999]，中位数 145，所以填完应该是 [120, 145, 130, 150, 160, 140, 99999]"
    assert abs(float(upper) - 195.0) < 1e-9, "IQR 上界 upper = Q3 + 1.5 * (Q3 - Q1)，本题 Q1=132.5、Q3=157.5，upper 应该是 195.0"
    assert n_outlier == 1, "金额 99999 超过了上界 195，异常值应该有 1 个"
    assert list(city_filled) == ["北京", "上海", "未知", "北京", "上海", "北京", "广州"], "city 的缺失值要填成 '未知'，得到 ['北京', '上海', '未知', '北京', '上海', '北京', '广州']"
    _s2 = pd.Series([1.0, 2.0, np.nan, 3.0])
    _filled2 = fill_by_median(_s2)
    assert _filled2 is not None, "fill_by_median 要把填充后的 Series return 出来"
    assert list(_filled2) == [1.0, 2.0, 2.0, 3.0], "换一组数据：[1, 2, NaN, 3] 的中位数是 2，填完应该是 [1, 2, 2, 3]"
    assert int(_s2.isna().sum()) == 1, "fill_by_median 不能改动传进来的 Series 本身（不要用 inplace=True），只返回新结果"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DA05_CHECKER = """
import pandas as pd
try:
    assert len(by_dept) == 3, "按 dept 分组应该有 3 组：研发、产品、测试"
    assert abs(float(by_dept["研发"]) - 65000 / 3) < 1e-6, "研发组 3 人，(18000 + 22000 + 25000) / 3 约等于 21666.67"
    assert int(agg_table.loc["研发", "total"]) == 65000, "agg 里研发组的 total 应该是 65000，聚合列要按题目命名成 total 和 avg"
    assert abs(float(agg_table.loc["测试", "avg"]) - 11500.0) < 1e-9, "agg 里测试组的 avg 应该是 (12000 + 11000) / 2 = 11500"
    assert dict(dept_size) == {"研发": 3, "产品": 2, "测试": 2}, "size() 是每组的行数：研发 3、产品 2、测试 2"
    assert abs(float(ratio.sum()) - 7.0) < 1e-9, "ratio 是「本人薪资 除以 组内均值」，每组内部的比值加起来正好等于人数，7 行合起来应该是 7.0"
    assert abs(float(ratio.iloc[0]) - 18000 / (65000 / 3)) < 1e-9, "第 0 行是研发的张伟，ratio 应该是 18000 除以研发组均值，用 transform('mean') 把组均值贴回每一行"
    _d2 = pd.DataFrame({"g": ["a", "a", "b"], "v": [1.0, 3.0, 10.0]})
    _g2 = group_avg(_d2, "g", "v")
    assert _g2 is not None, "group_avg 要把结果 return 出来"
    assert abs(float(_g2["a"]) - 2.0) < 1e-9 and abs(float(_g2["b"]) - 10.0) < 1e-9, "换一张表：a 组均值是 (1 + 3) / 2 = 2，b 组是 10，分组键和数值列都要从参数里来"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except KeyError as e:
    print("__FAIL__ 取不到这个键或列名：" + str(e) + "，检查聚合列的命名和分组键是否和题目要求一致")
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DA06_CHECKER = """
import pandas as pd
try:
    assert tuple(merged.shape) == (5, 5), "how='left' 要保留左表 orders 的 5 行，4 列订单 + name 和 city 共 5 列"
    assert list(merged["order_id"]) == [101, 102, 103, 104, 105], "左连接要保持订单原顺序，order_id 应该是 101 到 105"
    assert n_missing == 1, "user_id=9 在 users 里没有对应的人，左连接后 name 是 NaN，缺失 1 条"
    assert tuple(inner.shape) == (4, 5), "how='inner' 只保留两边都匹配的行，5 条订单里只有 4 条能匹配上用户"
    assert abs(float(pivot.loc["北京", "amount"]) - 510.0) < 1e-9, "北京的成交额是 120 + 300 + 90 = 510，pivot_table 的 index 用 city、values 用 amount"
    assert abs(float(pivot.loc["上海", "amount"]) - 150.0) < 1e-9, "上海的成交额是 150"
    _o2 = pd.DataFrame({"order_id": [1, 2, 3], "user_id": [7, 8, 7], "amount": [10.0, 20.0, 30.0]})
    _u2 = pd.DataFrame({"user_id": [7], "name": ["张伟"]})
    _j2 = join_orders(_o2, _u2)
    assert _j2 is not None, "join_orders 要把连接后的 DataFrame return 出来"
    assert tuple(_j2.shape)[0] == 3, "换一组数据：左表 3 条订单必须全部保留，匹配不上的给 NaN，行数还得是 3"
    assert int(_j2["name"].isna().sum()) == 1, "换一组数据：user_id=8 匹配不上，name 应该正好有 1 个 NaN"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except KeyError as e:
    print("__FAIL__ 取不到这个键或列名：" + str(e) + "，检查列名以及 pivot_table 的 index/values 是否和题目要求一致")
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DA07_CHECKER = """
import pandas as pd
try:
    assert pd.api.types.is_datetime64_any_dtype(df["date"]), "df['date'] 现在还是字符串，要先 pd.to_datetime 转成 datetime64，后面才能用 .dt"
    assert list(df["month"]) == ["2026-01", "2026-01", "2026-02", "2026-02", "2026-03", "2026-03"], "month 列要用 dt.strftime('%Y-%m') 取出「年-月」"
    assert list(df["weekday"]) == [0, 6, 1, 4, 5, 3], "weekday 列用 dt.dayofweek：2026-01-05 是周一(0)，2026-01-18 是周日(6)，六个日期依次是 0 6 1 4 5 3"
    assert len(monthly) == 3, "按月汇总应该有 3 个月：2026-01、2026-02、2026-03"
    assert abs(float(monthly["2026-01"]) - 200.0) < 1e-9, "2026-01 的销售额是 120 + 80 = 200"
    assert abs(float(monthly["2026-03"]) - 350.0) < 1e-9, "2026-03 的销售额是 90 + 260 = 350"
    _d2 = pd.DataFrame({"day": ["2025-01-01", "2025-01-15", "2025-02-02"], "amount": [1.0, 2.0, 3.0]})
    _m2 = monthly_amount(_d2, "day", "amount")
    assert _m2 is not None, "monthly_amount 要把结果 return 出来"
    assert abs(float(_m2["2025-01"]) - 3.0) < 1e-9 and abs(float(_m2["2025-02"]) - 3.0) < 1e-9, "换一张表：日期列叫 day，2025-01 合计 1 + 2 = 3，2025-02 是 3，列名要按参数传不能写死"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except KeyError as e:
    print("__FAIL__ 取不到这个键：" + str(e) + "，检查月份字符串是不是 '%Y-%m' 格式，比如 2026-01")
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

DA08_CHECKER = """
import pandas as pd
try:
    assert len(by_month) == 3, "按月汇总应该有 3 个月"
    assert abs(float(by_month["2026-03"]) - 390.0) < 1e-9, "2026-03 的销售额是 90 + 260 + 40 = 390"
    assert abs(float(mom["2026-02"]) - 0.3) < 1e-9, "2026-02 的环比增长率是 260 / 200 - 1 = 0.3，用 pct_change() 算"
    assert top_month == "2026-03", "top_month 要取销售额最高的月份，用 by_month.idxmax() 得到 2026-03"
    assert abs(float(pivot.loc["2026-01", "广州"]) - 0.0) < 1e-9, "广州在 2026-01 没有下单，pivot_table 加 fill_value=0 之后应该是 0.0 而不是 NaN"
    assert abs(float(pivot.loc["2026-03", "上海"]) - 260.0) < 1e-9, "2026-03 上海的成交额是 260"
    assert isinstance(conclusion, str), "conclusion 要是一句话结论，类型是字符串"
    assert "2026-03" in conclusion and "390" in conclusion, "结论里必须带上峰值月份和金额，比如「2026-03 销售额 390 元，环比 +50%」"
    _s2 = pd.Series([100.0, 150.0, 120.0])
    _mom2 = mom_growth(_s2)
    assert _mom2 is not None, "mom_growth 要把结果 return 出来"
    assert abs(float(_mom2.iloc[2]) - (-0.2)) < 1e-9, "换一组数据：[100, 150, 120] 的环比，第三期是 120 / 150 - 1 = -0.2"
    assert pd.isna(_mom2.iloc[0]), "第一期没有上一期可比，环比应该是 NaN（pct_change 的默认行为），不要用 0 顶替"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except KeyError as e:
    print("__FAIL__ 取不到这个键：" + str(e) + "，检查月份键名以及 pivot_table 的 index/columns 是否和题目要求一致")
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

LESSONS: list[dict] = [
    # ----------------------------------------------------------------- da-01
    {
        "code": "da-01",
        "subject": "数据分析与处理",
        "stage": "NumPy 基础",
        "runner": "python",
        "title": "NumPy 数组与向量化运算",
        "summary": "整块数组一起算，比 for 循环快几十倍",
        "definition": (
            "**ndarray（数组）** 是 NumPy 的核心对象：一块连续内存里放着**同一种类型**的数据，"
            "带一个描述形状的 `shape`。`np.array([1, 2, 3])` 是一维，"
            "`np.array([[1, 2], [3, 4]])` 是二维（2 行 2 列）。\n\n"
            "**向量化（vectorization）** 指的是：把运算写成「对整个数组做一次」，"
            "而不是「对每个元素循环一次」。写法上的区别只有一处，"
            "但执行路径完全不同：\n\n"
            "- 标量乘法：`prices * qty` —— 一次调用，4 个元素一起算完\n"
            "- 布尔索引：`prices[prices > 100]` —— 先用比较得到布尔数组，再用它当筛选条件\n"
            "- 聚合：`arr.sum()`、`arr.mean()`、`arr.max()` —— 一次算完整个数组\n"
            "- 轴（axis）：`axis=0` 表示**沿着行的方向压缩**，结果是「每列一个值」；`axis=1` 得到「每行一个值」\n\n"
            "**为什么向量化快**：Python 循环每处理一个元素都要做一次解释器派发、类型检查、"
            "以及把 `int`/`float` 装箱成对象，开销可能是真正算数的一百倍；"
            "NumPy 把这层循环下沉到编译好的 C 里，直接在连续内存上按定长类型运算，"
            "还能让 CPU 用 SIMD 一条指令同时算多个元素。所以它解决的是"
            "「**数据量一大，Python 循环就慢到不可用**」这个问题。\n\n"
            "**广播（broadcasting）** 是配套规则：形状不同的数组做运算时，"
            "NumPy 会自动把小的一方「撑开」对齐，比如 `(3, 4) / (4,)` 表示每一列都除以同一个数，"
            "不用手写循环。**轴和广播是 NumPy 面试的两大核心考点。**"
        ),
        "plain": (
            "把 NumPy 数组想成**一列排好队、身高一致的士兵**（类型相同、内存连续）。"
            "命令「全体向右看齐」一次下达就完事 —— 这就是向量化。\n\n"
            "而 Python 的 for 循环，相当于**挨个走到每个士兵面前单独喊一遍**："
            "要走 100 万次路，喊 100 万次话，当然慢。NumPy 把「走路喊话」这部分交给了 C，"
            "你只管下达一次命令。\n\n"
            "`axis` 别死记，想成**「哪一个维度被压扁了」**：`scores.mean(axis=0)` 把「行」压扁，"
            "于是每一列剩下一个均值（每门课的平均分）；`axis=1` 把「列」压扁，得到每个学生的平均分。"
        ),
        "example": (
            "import numpy as np\n"
            "\n"
            "prices = np.array([100.0, 250.0, 80.0, 320.0])\n"
            "qty = np.array([2, 1, 4, 3])\n"
            "\n"
            "amount = prices * qty            # 一次算完 4 个商品，中间没有 Python 循环\n"
            "print(amount)\n"
            "print(amount.sum())              # 总销售额\n"
            "\n"
            "print(prices[prices > 100])      # 布尔索引：挑出单价大于 100 的\n"
            "\n"
            "scores = np.array([[90, 85, 88],\n"
            "                   [70, 95, 60],\n"
            "                   [88, 88, 88]])\n"
            "print(scores.mean(axis=0))       # 每列（每门课）的均分\n"
            "print(scores.mean(axis=1))       # 每行（每个学生）的均分\n"
            "\n"
            "total = 0.0                      # for 循环版本：结果一样，但慢得多\n"
            "for i in range(len(prices)):\n"
            "    total += prices[i] * qty[i]\n"
            "print(total)"
        ),
        "example_output": (
            "[200. 250. 320. 960.]\n"
            "1730.0\n"
            "[250. 320.]\n"
            "[82.66666667 89.33333333 78.66666667]\n"
            "[87.66666667 75.         88.        ]\n"
            "1730.0"
        ),
        "pitfalls": [
            "**`*` 是逐元素相乘，`@` / `np.dot` 是内积**：`a * b` 得到同形状的新数组，`a @ b` 得到一个标量。算「单价 × 销量」要用 `*`，用错了不报错但结果类型完全不对。",
            "**`axis` 记反**：`axis=0` 压掉行、得到每列一个值；`axis=1` 压掉列、得到每行一个值。记不住就想「axis 是要被消掉的那个维度」。",
            "**np.int32/int64 会溢出**：定长整数超过范围会**静默**变成负数（不像 Python 的 int 会自动变大）。涉及金额、ID 乘积时优先用浮点或 `int64`。",
            "**别用 for 循环逐元素处理数组**：百万级数据下慢几十倍到上百倍。凡是「对每个元素做同样的事」，先想有没有向量化写法。",
        ],
        "task": (
            "题目已经给好了 `prices`（单价）、`qty`（销量）、`scores`（3 个学生 3 门课的成绩）。\n\n"
            "1. 用**向量化**算出每个商品的销售额，存到 `amount`（不用 for 循环）\n"
            "2. 算出总销售额，存到 `revenue`\n"
            "3. 用**布尔索引**取出单价大于 100 的值，存到 `high`\n"
            "4. 算出每门课的均分存到 `col_mean`（想清楚用哪个 `axis`）\n"
            "5. 写一个函数 `total_amount(prices, qty)`：接收两个数组，返回**逐元素相乘后的总和**"
            "（要 `return`，不要只 print）\n\n"
            "系统会换一组 `prices` / `qty` 再调一次你的函数，所以别把 1730 写死。"
        ),
        "setup": (
            "import numpy as np\n"
            "\n"
            "prices = np.array([100.0, 250.0, 80.0, 320.0])   # 四个商品的单价\n"
            "qty = np.array([2, 1, 4, 3])                     # 对应的销量\n"
            "scores = np.array([[90, 85, 88],\n"
            "                   [70, 95, 60],\n"
            "                   [88, 88, 88]])                # 3 个学生、3 门课\n"
        ),
        "starter": (
            "# prices / qty / scores 已经给好了\n"
            "\n"
            "amount = None        # 用 prices * qty 得到逐元素相乘的结果\n"
            "revenue = None       # amount 的总和\n"
            "high = None          # 布尔索引：prices 里大于 100 的元素\n"
            "col_mean = None      # 每门课（每一列）的均分\n"
            "\n"
            "\n"
            "def total_amount(prices, qty):\n"
            "    \"\"\"返回 prices 和 qty 逐元素相乘后的总和。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "乘法直接写 `prices * qty`，求和用 `.sum()`。布尔索引用 `prices[prices > 100]`。"
            "均分要沿行方向压缩，也就是 `axis=0`。函数里一行就够：先相乘再 `.sum()`，"
            "注意要把结果 return 出去。"
        ),
        "checker": DA01_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官问：为什么 NumPy 的向量化运算能比 Python 的 for 循环快几十倍？下面哪条解释最准确？",
                "options": [
                    "运算下沉到编译好的 C 循环里，数组是同类型的连续内存，还能用 SIMD 一条指令算多个元素",
                    "因为 NumPy 会自动开多线程，把数组拆到多个 CPU 核上并行算",
                    "因为 NumPy 用了更快的 Python 解释器",
                    "因为 NumPy 会把循环里多余的语句优化掉",
                ],
                "answer_index": 0,
                "explanation": (
                    "Python 循环慢的根源是解释器逐元素派发、类型检查和对象装箱；"
                    "NumPy 把这三样都消掉了：循环在 C 里跑、元素是同类型定长数据、内存连续可以被 SIMD 向量化。"
                    "B 不对，单次 ufunc 一般不开多线程（BLAS 矩阵乘法才会）；C 根本没有这回事。"
                ),
            },
            {
                "type": "choice",
                "stem": "`a = np.array([1, 2, 3])`、`b = np.array([4, 5, 6])`，那么 `a * b` 和 `a @ b` 分别是？",
                "options": [
                    "[4, 10, 18] 和 32",
                    "32 和 [4, 10, 18]",
                    "都是 [4, 10, 18]",
                    "都是 32",
                ],
                "answer_index": 0,
                "explanation": (
                    "`*` 是逐元素相乘，`@` 是矩阵乘法（一维数组之间就是内积）："
                    "1×4 + 2×5 + 3×6 = 32。这两个符号写反了不会报错，只会得到完全不同的结果。"
                ),
            },
            {
                "type": "judge",
                "stem": "`scores = np.array([[1, 2], [3, 4]])`，那么 `scores.mean(axis=1)` 得到的是每一列的平均值。",
                "answer": False,
                "explanation": "`axis=1` 压掉的是列，得到每一行一个值（[1.5, 3.5]）。要每列一个均值得用 `axis=0`。",
            },
            {
                "type": "blank",
                "stem": "要从数组 `arr` 里取出所有大于 2 的元素，补全这一行：\nprint(arr[arr ___ 2])",
                "answer": ">",
                "accept": [">"],
                "hint": "填一个比较运算符",
                "explanation": "`arr > 2` 先得到一个布尔数组，再用它当索引就只留下 True 的位置，这叫布尔索引。",
            },
            {
                "type": "short",
                "stem": "面试官问：向量化快在哪里？反过来，什么情况下向量化不但不快、还会更慢？",
                "keywords": ["C 循环", "连续内存", "SIMD", "临时数组", "内存", "调用开销"],
                "reference": (
                    "快在三件事：循环下沉到 C 层（省掉解释器逐元素派发和类型检查）、"
                    "元素同类型且内存连续（省掉对象装箱）、以及 CPU 能用 SIMD 一条指令算多个元素。"
                    "失效场景也有三种：一是数据被切成很多小段，每次调用 ufunc 都有固定开销，"
                    "反而比一次循环慢；二是表达式复杂时会生成多个同等大小的临时数组，内存翻几倍甚至触发换页；"
                    "三是「本行依赖上一行结果」的强串行逻辑（比如带状态的累积），硬向量化要写很绕的技巧，不如直接循环。"
                ),
                "explanation": "能把「为什么快」和「什么情况下不快」都讲出来，才算真懂向量化。",
            },
        ],
    },
    # ----------------------------------------------------------------- da-02
    {
        "code": "da-02",
        "subject": "数据分析与处理",
        "stage": "NumPy 基础",
        "runner": "python",
        "title": "Pandas Series 与 DataFrame",
        "summary": "一列是 Series，整表是 DataFrame",
        "definition": (
            "Pandas 只有两个核心数据结构：\n\n"
            "- **Series**：带索引的一维数组。`df[\"salary\"]`、`df.loc[0]`、`s.mean()` 都是 Series\n"
            "- **DataFrame**：带行列索引的二维表，可以理解成「共享同一个行索引的多个 Series」\n\n"
            "取数的四个入口（面试必问）：\n\n"
            "- `df[\"col\"]` → Series（一列）；`df[[\"a\", \"b\"]]` → DataFrame（多列）\n"
            "- `df.loc[行标签, 列名]` → **按标签**取\n"
            "- `df.iloc[行位置, 列位置]` → **按位置**取（从 0 开始的整数）\n"
            "- `df[布尔条件]` → 按条件筛行\n\n"
            "看数据的三个方法：`df.shape`（行列数）、`df.dtypes` / `df.info()`（每列类型、非空数量）、"
            "`df.describe()`（数值列的分布）。\n\n"
            "**它解决什么问题**：把「一行是一条记录、一列是一个字段」的表格数据，"
            "变成可以用列名直接操作的对象。你不再需要维护「第 3 列是薪资」这种下标记忆，"
            "而且一整列的运算会自动向量化。"
        ),
        "plain": (
            "DataFrame 就是**一张 Excel 表**：有表头（列名）、有行号（索引），"
            "可以按名字取一列、按条件筛行。\n\n"
            "Series 则是**从表里抽出来的单独一列**，或者单独的一行 —— 一条带标签的数据。"
            "把表里的一列拿去算平均，得到的是 Series 的 `mean()`；"
            "这就是为什么 Pandas 里到处都在 `df[\"列名\"]`。\n\n"
            "最容易搞混的是**一个方括号和两个方括号**："
            "`df[\"salary\"]` 拿到的是一列（Series，一维）；"
            "`df[[\"salary\"]]` 拿到的还是「一列的表」（DataFrame，二维）。"
            "就像「一根薯条」和「装着一根薯条的袋子」—— 看起来都有薯条，但东西不是一种。"
        ),
        "example": (
            "import pandas as pd\n"
            "\n"
            "df = pd.DataFrame({\n"
            "    \"name\":   [\"张伟\", \"李娜\", \"刘洋\", \"王强\"],\n"
            "    \"salary\": [18000, 22000, 15000, 9000],\n"
            "})\n"
            "\n"
            "print(df.shape)                          # (行数, 列数)\n"
            "print(df.dtypes.astype(str).to_dict())\n"
            "print(df[\"salary\"].mean())               # 取一列得到 Series\n"
            "print(df[[\"name\", \"salary\"]].head(2))    # 取多列得到 DataFrame\n"
            "\n"
            "df[\"salary_k\"] = df[\"salary\"] / 1000     # 新增一列\n"
            "print(df.loc[df[\"salary\"] > 16000, \"name\"].tolist())\n"
            "print(df.iloc[0, 1])                     # 按位置取：第 0 行第 1 列"
        ),
        "example_output": (
            "(4, 2)\n"
            "{'name': 'str', 'salary': 'int64'}\n"
            "16000.0\n"
            "  name  salary\n"
            "0   张伟   18000\n"
            "1   李娜   22000\n"
            "['张伟', '李娜']\n"
            "18000"
        ),
        "pitfalls": [
            "**`df[\"c\"]` 和 `df[[\"c\"]]` 不是一个东西**：前者是 Series（一维），后者是只有一列的 DataFrame（二维）。多一个方括号，`.mean()` 之类的结果结构就变了。",
            "**`loc` 按标签、`iloc` 按位置**：`loc` 的切片**两端都包含**，`iloc` 的切片**含头不含尾**。行索引恰好是默认整数时最容易搞混。",
            "**链式赋值不生效**：`df[df[\"a\"] > 1][\"b\"] = 0` 改不到原表（pandas 3 的 Copy-on-Write 下是静默失败，没有警告）。永远写成 `df.loc[df[\"a\"] > 1, \"b\"] = 0`。",
            "**对齐是按索引的**：两个索引不一致的 Series 相加会得到一堆 NaN，而不是报错。运算前确认索引一致，或者用 `.reset_index(drop=True)` / `.values`。",
        ],
        "task": (
            "题目已经给好了 DataFrame `df`（姓名、部门、薪资、司龄）。\n\n"
            "1. 把表的形状存到 `shape`\n"
            "2. 把薪资列的平均值存到 `avg_salary`\n"
            "3. 给 `df` 新增一列 `salary_k`，值是薪资除以 1000（用 `df.assign` 或直接赋值都行）\n"
            "4. 筛出薪资**高于平均值**的人的姓名列表，存到 `high`（用 `df.loc[条件, \"name\"]`）\n"
            "5. 写函数 `top_values(df, col, n)`：按 `col` 列**降序**取前 `n` 个值，"
            "返回一个 Python 列表（要 `return`）\n\n"
            "系统会换一张表、换一列再调一次你的函数，所以列名和数量必须从参数里来。"
        ),
        "setup": (
            "import pandas as pd\n"
            "\n"
            "df = pd.DataFrame({\n"
            "    \"name\":   [\"张伟\", \"李娜\", \"刘洋\", \"王强\"],\n"
            "    \"dept\":   [\"研发\", \"研发\", \"产品\", \"产品\"],\n"
            "    \"salary\": [18000, 22000, 15000, 9000],\n"
            "    \"years\":  [3, 5, 2, 1],\n"
            "})\n"
        ),
        "starter": (
            "# df 已经给好了\n"
            "\n"
            "shape = None         # df.shape\n"
            "avg_salary = None    # 薪资列的平均值\n"
            "# 给 df 新增一列 salary_k = 薪资 / 1000\n"
            "\n"
            "high = None          # 薪资高于平均值的人名列表\n"
            "\n"
            "\n"
            "def top_values(df, col, n):\n"
            "    \"\"\"按 col 列降序取前 n 个值，返回列表。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "形状直接取 `df.shape`；均值是 `df[\"salary\"].mean()`；"
            "新列用 `df.assign(salary_k=df[\"salary\"] / 1000)` 或 `df[\"salary_k\"] = ...`。"
            "筛选用 `df.loc[df[\"salary\"] > avg_salary, \"name\"].tolist()`。"
            "函数里先排序再取头部：`df.sort_values(col, ascending=False)[col].head(n).tolist()`。"
        ),
        "checker": DA02_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`df[\"salary\"]` 和 `df[[\"salary\"]]` 的区别是？",
                "options": [
                    "前者是 Series（一维），后者是只含这一列的 DataFrame（二维）",
                    "两者完全一样",
                    "前者是 DataFrame，后者是 Series",
                    "后者会报错",
                ],
                "answer_index": 0,
                "explanation": (
                    "一个方括号取列 → Series；两个方括号（列表）取列 → DataFrame。"
                    "要同时取多列只能用两个方括号的写法，这也是区分两种类型的记忆点。"
                ),
            },
            {
                "type": "choice",
                "stem": "面试官说：取出「第 2 到第 4 行（只要 3 行）、且只保留 name 列」，要按位置取，写哪个最稳妥？",
                "options": [
                    "df.iloc[1:4][\"name\"]",
                    "df.loc[1:4, \"name\"]",
                    "df[1:4][\"name\"]",
                    "df.head(4)[\"name\"]",
                ],
                "answer_index": 0,
                "explanation": (
                    "按位置取一律用 `iloc`，切片含头不含尾，`1:4` 正好是第 2、3、4 行。"
                    "B 的 `loc` 是按标签切且**两端都包含**，默认整数索引下会多取一行；"
                    "C 对 DataFrame 按下标切片语义不明确；D 取的是前 4 行，多了第一行。"
                ),
            },
            {
                "type": "judge",
                "stem": "`df.loc[df[\"salary\"] > 10000, \"level\"] = \"高\"` 会把满足条件的行的 level 列写上「高」。",
                "answer": True,
                "explanation": (
                    "`loc[条件, 列名] = 值` 是标准的条件赋值写法，能真正改到原表。"
                    "换成 `df[df[\"salary\"] > 10000][\"level\"] = \"高\"`（链式赋值）就改不到了，这是最常见的静默 bug。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全这一行，打印 df 的前 3 行：\nprint(df.___(3))",
                "answer": "head",
                "accept": ["head"],
                "hint": "一个方法名",
                "explanation": "`df.head(n)` 取前 n 行，默认 5；对应的还有 `df.tail(n)` 取末尾 n 行。看数据第一步就是它们。",
            },
            {
                "type": "short",
                "stem": "面试官把一份 10 万行、40 列的表丢给你，问：你拿到数据的第一件事做什么？",
                "keywords": ["shape", "dtypes", "info", "缺失值", "describe", "口径"],
                "reference": (
                    "先看规模和类型，不看内容：`df.shape` 确认行列数，`df.dtypes` / `df.info()` 看每列是什么类型、"
                    "有没有该是数字却读成字符串的列、每列非空多少；再 `df.describe()` 看数值列的量级和分布，"
                    "`df.head()` 扫一眼具体长什么样。做完这四步，才能回答「这份数据能不能直接用」，"
                    "而不是上来就写 groupby —— 类型不对、口径不清的分析，跑出来也是错的。"
                ),
                "explanation": "面试官想听的是「先体检再分析」的习惯，而不是某个具体函数。",
            },
        ],
    },
    # ----------------------------------------------------------------- da-03
    {
        "code": "da-03",
        "subject": "数据分析与处理",
        "stage": "Pandas 处理",
        "runner": "python",
        "title": "数据读取与脏数据识别",
        "summary": "先看清类型，再谈分析",
        "definition": (
            "真实数据（CSV、Excel、接口返回）读进来之后，Pandas 一般会把无法确定类型的列当作**字符串**："
            "在 pandas 3 里 dtype 显示为 `str`（老版本显示 `object`）。"
            "一列数字变成字符串，后果是 `sum()` 变成字符串拼接、比较变成字典序比较 —— 全都错，而且不报错。\n\n"
            "**识别脏数据的三步**：\n\n"
            "1. 看类型：`df.dtypes`、`df.info()`。该是数字的列是 `str`，就说明还没转干净\n"
            "2. 转换：`pd.to_numeric(s, errors=\"coerce\")` —— 转得动的变数字，转不动的变 `NaN`（不中断流程）\n"
            "3. 计数：`s.isna().sum()` 数出有多少条转失败，`df.isna().mean()` 得到每列缺失率\n\n"
            "常见的脏数据形态：`\"88元\"`（带单位）、`\"abc\"`（乱码）、`\" 北京\"`（首尾空格）、"
            "`\"Unknown\"` / `\"N/A\"` / `\"-\"`（假缺失值，不会自动变成 NaN）。\n\n"
            "**它解决什么问题**：让「数据到底能不能用」变成一个可以量化回答的问题 —— "
            "缺失率 2% 和 30% 是两种完全不同的处理策略，而这个数字必须在动手清洗之前拿到。"
        ),
        "plain": (
            "读进来的原始数据就像**从仓库刚搬回来的一箱零件**：标签写得歪歪扭扭，"
            "有的箱子标着「88元」，有的干脆写着「未知」。你不能直接拿去装机器，得先清点一遍 —— "
            "有几件能用的、几件要返工、几件只能报废。\n\n"
            "`pd.to_numeric(..., errors=\"coerce\")` 就是那个「按规格分拣」的动作："
            "能当数字用的挑出来，不能用的先丢进「待处理」箱（变成 NaN），**而不是整条流水线停下来**。\n\n"
            "为什么要特别注意 `\"Unknown\"`、`\"N/A\"`、`\"-\"` 这类值？"
            "因为它们在 Pandas 眼里是**好好的字符串**，不是缺失值。"
            "缺口是透明的（NaN 一眼看得出），而这些是**画上去的假窗户** —— "
            "不主动把它们抠掉，后面算平均值时它们会被当成正常数据混进去。"
        ),
        "example": (
            "import pandas as pd\n"
            "\n"
            "raw = pd.DataFrame({\n"
            "    \"amount\": [\"128.5\", \"99\", \"88元\", \"abc\"],\n"
            "    \"city\":   [\"北京\", \"上海\", \" 北京\", \"北京 \"],\n"
            "})\n"
            "\n"
            "print(raw.dtypes.astype(str).to_dict())          # 全是 str，说明还没转成数字\n"
            "amount = pd.to_numeric(raw[\"amount\"], errors=\"coerce\")\n"
            "print(amount.tolist())                           # 转不了的变成 NaN\n"
            "print(int(amount.isna().sum()))                  # 2 条脏数据\n"
            "\n"
            "print(raw[\"city\"].str.strip().tolist())          # 去掉首尾空格\n"
            "print(raw[\"amount\"].str.contains(\"元\").tolist())  # 找出带单位的"
        ),
        "example_output": (
            "{'amount': 'str', 'city': 'str'}\n"
            "[128.5, 99.0, nan, nan]\n"
            "2\n"
            "['北京', '上海', '北京', '北京']\n"
            "[False, False, True, False]"
        ),
        "pitfalls": [
            "**读进来是 `str` 说明数字没被识别**：pandas 3 的字符串列 dtype 是 `str`（老版本是 `object`）。这种列去求 `mean()` 会直接报错，去 `sum()` 则悄悄变成字符串拼接。",
            "**`errors=\"coerce\"` 是「把错误变成 NaN」，不是「修好它」**：流程不会中断，代价是数据悄悄少了一块。所以转换之后**必须**再数一次 `isna().sum()`。",
            "**默认的 `errors=\"raise\"` 一条脏数据就炸**：整批文件读不进来。生产上一般是先 coerce + 记日志，再决定是修、是丢、还是打回上游。",
            "**假缺失值不会自己变成 NaN**：`\"Unknown\"`、`\"N/A\"`、`\"-\"`、`\"\"` 都是合法字符串。读文件时用 `na_values=[\"NA\", \"Unknown\", \"-\"]` 声明，或者读后用 `replace` 统一成缺失值。",
        ],
        "task": (
            "题目已经给好了从「上游 CSV」读进来的 `raw`（6 行 3 列，`amount` 和 `city` 都是字符串）。\n\n"
            "1. 把 `amount` 转成数值存到 `amount`，**转不动的先变成缺失值**（不要报错中断）\n"
            "2. 数出 `amount` 里有多少条没转成功，存到 `bad`（整数）\n"
            "3. 把 `city` 清理成 `city`：先去首尾空格，再把 `\"Unknown\"` 也当成缺失值；"
            "数出清理后有多少个缺失值存到 `unknown`（本题是 1，因为只有 1 个 `\"Unknown\"`，没有原生空值）\n"
            "4. 判断 `raw` 的 `amount` 列当前是不是数值类型，结果存到 `amount_is_numeric`（布尔值）\n"
            "5. 写函数 `to_number(s)`：能转成数字就返回**数字**，转不了返回 `None`（不要抛异常）"
        ),
        "setup": (
            "import pandas as pd\n"
            "\n"
            "raw = pd.DataFrame({\n"
            "    \"order_id\": [\"A01\", \"A02\", \"A03\", \"A04\", \"A05\", \"A06\"],\n"
            "    \"amount\":   [\"128.5\", \"99\", \"88元\", \"abc\", \"230\", \"45.0\"],\n"
            "    \"city\":     [\"北京\", \"上海\", \" 北京\", \"北京 \", \"Unknown\", \"北京\"],\n"
            "})\n"
        ),
        "starter": (
            "# raw 已经给好了\n"
            "\n"
            "amount = None              # 把 amount 列转成数值，转不动的变 NaN\n"
            "bad = None                 # amount 里没转成功的条数（整数）\n"
            "city = None                # 去空格 + 把 'Unknown' 当缺失值\n"
            "unknown = None             # 清理后 city 的缺失值个数（整数）\n"
            "amount_is_numeric = None   # raw['amount'] 是不是数值类型（布尔值）\n"
            "\n"
            "\n"
            "def to_number(s):\n"
            "    \"\"\"能转成数字就返回数字，转不了返回 None。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "转换用 `pd.to_numeric(raw[\"amount\"], errors=\"coerce\")`；数缺失用 `amount.isna().sum()`，"
            "记得 `int()` 一下。city 用 `raw[\"city\"].str.strip().replace(\"Unknown\", pd.NA)` 链式写下来，"
            "再数 `isna()`。判断类型用 `pd.api.types.is_numeric_dtype(raw[\"amount\"])`。"
            "函数里可以借 `pd.to_numeric(s, errors=\"coerce\")` 的结果，再用 `pd.isna(...)` 判断是不是 `None`。"
        ),
        "checker": DA03_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`pd.read_csv` 读进来之后，本该是数字的列 dtype 显示成 `str`，最先该做什么？",
                "options": [
                    "用 pd.to_numeric(..., errors=\"coerce\") 转成数值，并数一遍有多少条转失败",
                    "直接 df.sum() 求和看看总量",
                    "把这些列删掉",
                    "把 DataFrame 转成 list 再处理",
                ],
                "answer_index": 0,
                "explanation": (
                    "字符串列求均值会报错、求和会变成拼接，所以必须先转类型；"
                    "转的时候用 `coerce` 让脏值变 NaN 而不是中断，然后数一遍转失败的条数，"
                    "才知道这批数据的可用比例。"
                ),
            },
            {
                "type": "choice",
                "stem": "面试官问：上游给的 CSV 里 city 列混着「北京」「 北京 」「N/A」「Unknown」「-」，你会怎么处理？",
                "options": [
                    "先把这些写法统一成缺失值（strip 去空格 + replace 假缺失值），再决定这一列到底该填、该删还是该留",
                    "直接 fillna(0)，简单省事",
                    "直接 dropna() 把这几十行删掉，眼不见为净",
                    "把整列做 one-hot 编码，当作正常类别处理",
                ],
                "answer_index": 0,
                "explanation": (
                    "「 北京」和「北京」是同一个城市，「Unknown」「N/A」「-」都是假缺失值。"
                    "不先统一口径，value_counts 会给出几个假类别，group by 也会把同一个城市拆成两组。"
                    "B 把类别列填成 0 毫无意义；C 在缺失率不高时可行但要看比例；D 等于把脏值固化成特征。"
                ),
            },
            {
                "type": "judge",
                "stem": "`pd.to_numeric(s, errors=\"coerce\")` 遇到无法转成数字的值时会抛出异常，中断程序。",
                "answer": False,
                "explanation": "`coerce` 的语义就是「转不了的就变成 NaN」。会抛异常的是默认的 `errors=\"raise\"`。",
            },
            {
                "type": "blank",
                "stem": "要数出一列里有多少缺失值，补全这一行：\nprint(int(df[\"amount\"].isna().___()))",
                "answer": "sum",
                "accept": ["sum"],
                "hint": "一个聚合方法名",
                "explanation": "`isna()` 返回布尔序列（True 当作 1），`sum()` 就把 True 的个数加起来。想直接看每列缺失率用 `df.isna().mean()`。",
            },
            {
                "type": "short",
                "stem": "面试官问：你怎么判断一份数据「脏」？拿到数据你会先跑哪几行代码？",
                "keywords": ["dtypes", "isna", "duplicated", "describe", "唯一值", "取值范围"],
                "reference": (
                    "先看类型（`df.dtypes` / `df.info()`），重点找「该是数字却是字符串」的列；"
                    "再看缺失（`df.isna().mean()`），拿到每列缺失率而不只是缺失个数；"
                    "再看重复（`df.duplicated().sum()` 和主键的 `value_counts()` 有没有重复值）；"
                    "最后看分布（`describe()`、唯一值 `nunique()`、类别的取值集合），确认量级和取值范围合理，"
                    "比如年龄出现 300、金额出现负数。这四步跑完，脏不脏、怎么脏就有据可依了。"
                ),
                "explanation": "面试官想听的是「有顺序的体检清单」，而不是零散地提某个函数。",
            },
        ],
    },
    # ----------------------------------------------------------------- da-04
    {
        "code": "da-04",
        "subject": "数据分析与处理",
        "stage": "Pandas 处理",
        "runner": "python",
        "title": "缺失值、重复值、异常值处理",
        "summary": "缺失、重复、异常——清洗三板斧",
        "definition": (
            "清洗的三类问题要分开处理：\n\n"
            "**1. 缺失值 NaN**\n"
            "- `df.isna().mean()` → 每列的缺失率，这是决定策略的依据\n"
            "- `df.dropna(subset=[...])` 删行；`s.fillna(值)` 填值\n"
            "- 填什么：数值列用**中位数**（比均值抗极值），类别列用 `\"未知\"` 或众数；"
            "**绝不能默认填 0**，除非 0 真的有业务含义\n\n"
            "**2. 重复值**\n"
            "- `df.duplicated(subset=..., keep=...)` 找出重复；`df.drop_duplicates(...)` 删掉\n"
            "- 默认比较**所有列**；按业务主键去重必须写 `subset=\"order_id\"`，并明确保留第一条还是最后一条\n\n"
            "**3. 异常值**\n"
            "- IQR 规则：`upper = Q3 + 1.5 * (Q3 - Q1)`，`lower = Q1 - 1.5 * (Q3 - Q1)`，在此范围外的算候选异常\n"
            "- 3σ 规则：偏离均值超过 3 倍标准差\n"
            "- 业务规则：金额不能为负、年龄不能超过 100 —— **这条通常比统计规则更可靠**\n\n"
            "**它解决什么问题**：让后续的统计量不被少数坏值带偏。"
            "一个 99999 的金额就能把平均值、方差、相关系数全部拉歪，而这些坏值往往只占 0.1%。"
        ),
        "plain": (
            "清洗数据像**做菜前的洗菜择菜**：\n\n"
            "**缺失值**是菜叶上的破洞 —— 直接把整片叶子扔了太浪费，"
            "但补的时候要补得像：金额缺了填 0，等于说「这单没花钱」，比留着窟窿还糟；"
            "填中位数相当于用「这堆菜的正常大小」去补，至少不偏。\n\n"
            "**重复值**是同一颗菜被数了两遍，会让总数虚高。\n\n"
            "**异常值**最难办：一个 99999 的订单，可能是录入时多按了两个键（要修），"
            "也可能是真有一笔大单（要留）。统计规则（IQR、3σ）只负责**圈出嫌疑人**，"
            "到底是不是坏人，得靠业务规则来判。**「先标记，不要直接删」是这一课最重要的一句话。**"
        ),
        "example": (
            "import numpy as np\n"
            "import pandas as pd\n"
            "\n"
            "orders = pd.DataFrame({\n"
            "    \"order_id\": [\"A01\", \"A02\", \"A03\", \"A04\", \"A04\", \"A06\", \"A07\", \"A08\"],\n"
            "    \"city\":     [\"北京\", \"上海\", None, \"北京\", \"北京\", \"上海\", \"北京\", \"广州\"],\n"
            "    \"amount\":   [120.0, np.nan, 130.0, 150.0, 150.0, 160.0, 140.0, 99999.0],\n"
            "})\n"
            "\n"
            "dedup = orders.drop_duplicates()                 # A04 整行重复了一次，删掉\n"
            "print(dedup.shape)\n"
            "\n"
            "amount = dedup[\"amount\"].fillna(dedup[\"amount\"].median())\n"
            "print(amount.tolist())\n"
            "\n"
            "q1 = dedup[\"amount\"].quantile(0.25)\n"
            "q3 = dedup[\"amount\"].quantile(0.75)\n"
            "upper = q3 + 1.5 * (q3 - q1)\n"
            "print(round(q1, 2), round(q3, 2), round(upper, 2))\n"
            "print(int((dedup[\"amount\"] > upper).sum()))\n"
            "\n"
            "print(dedup[\"city\"].value_counts(dropna=False).to_dict())\n"
            "print(dedup[\"city\"].isna().mean())             # 缺失率：面试必问的指标"
        ),
        "example_output": (
            "(7, 3)\n"
            "[120.0, 145.0, 130.0, 150.0, 160.0, 140.0, 99999.0]\n"
            "132.5 157.5 195.0\n"
            "1\n"
            "{'北京': 3, '上海': 2, nan: 1, '广州': 1}\n"
            "0.14285714285714285"
        ),
        "pitfalls": [
            "**`drop_duplicates()` 默认比较所有列**：两行只要有一列不同就不算重复。按业务主键去重要写 `subset=\"order_id\"`，并且想清楚 `keep=\"first\"` 还是 `keep=\"last\"`。",
            "**`fillna(0)` 是最危险的默认动作**：金额缺失填 0 会把均值拉低，还把「没发生」和「发生且为 0」混为一谈。数值列优先中位数。",
            "**删行之前先看缺失率**：一列缺 80% 说明采集链路有问题，填也没意义；缺失率低的才值得填。一行代码 `df.isna().mean()` 就能拿到。",
            "**IQR 在小样本上会被极值本身带偏**：样本只有几条时，那个超大的异常值会把 Q3 一起拉高，上下界跟着变形。样本少时优先用业务规则判断。",
        ],
        "task": (
            "题目已经给好了 `orders`（8 行，其中 `A04` 整行重复了一次，`amount` 有 1 个缺失值、1 个极大值）。\n\n"
            "1. 去掉完全重复的行，结果存到 `dedup`\n"
            "2. 用**中位数**填充 `dedup` 的 `amount` 缺失值，结果存到 `amount_filled`（不要改 `dedup` 本身）\n"
            "3. 用 IQR 规则算异常上界存到 `upper`（`Q3 + 1.5 * (Q3 - Q1)`），超过上界的个数存到 `n_outlier`（整数）\n"
            "4. 把 `dedup` 的 `city` 缺失值填成 `\"未知\"`，结果存到 `city_filled`\n"
            "5. 写函数 `fill_by_median(s)`：用**中位数**填充传入 Series 的缺失值，"
            "返回新 Series，**不允许改动传入的 Series 本身**"
        ),
        "setup": (
            "import numpy as np\n"
            "import pandas as pd\n"
            "\n"
            "orders = pd.DataFrame({\n"
            "    \"order_id\": [\"A01\", \"A02\", \"A03\", \"A04\", \"A04\", \"A06\", \"A07\", \"A08\"],\n"
            "    \"city\":     [\"北京\", \"上海\", None, \"北京\", \"北京\", \"上海\", \"北京\", \"广州\"],\n"
            "    \"amount\":   [120.0, np.nan, 130.0, 150.0, 150.0, 160.0, 140.0, 99999.0],\n"
            "})\n"
        ),
        "starter": (
            "# orders 已经给好了\n"
            "\n"
            "dedup = None           # 去掉完全重复的行\n"
            "amount_filled = None   # 用中位数填充 amount 的缺失值\n"
            "upper = None           # IQR 上界 Q3 + 1.5 * (Q3 - Q1)\n"
            "n_outlier = None       # 超过上界的条数（整数）\n"
            "city_filled = None     # city 的缺失值填成 '未知'\n"
            "\n"
            "\n"
            "def fill_by_median(s):\n"
            "    \"\"\"返回用中位数填充缺失后的新 Series，不改动传入的 s。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "去重：`orders.drop_duplicates()`。填充：`dedup[\"amount\"].fillna(dedup[\"amount\"].median())`，"
            "注意 fillna 返回新对象，赋值给 `amount_filled` 就不会改到 `dedup`。"
            "IQR：`q1 = dedup[\"amount\"].quantile(0.25)`、`q3 = ...quantile(0.75)`，"
            "上界就是 `q3 + 1.5 * (q3 - q1)`，数超标的用 `(dedup[\"amount\"] > upper).sum()`。"
            "函数里一行 `return s.fillna(s.median())` 就够了，别用 `inplace=True`。"
        ),
        "checker": DA04_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官问：一份用户表有 30% 的 age 字段缺失，你会怎么处理？",
                "options": [
                    "先查缺失是不是随机的（和其它列有没有关系），再按用途定策略：只做分布分析就用中位数填充并加一列「是否填充」标记；要建模可以考虑剔除或者用其它列预测填充",
                    "全部填 0，最简单",
                    "缺失 30% 太高了，整列删掉",
                    "把所有缺失行删掉，剩下的才干净",
                ],
                "answer_index": 0,
                "explanation": (
                    "30% 不是「填」或「删」的自动化阈值，得先判断缺失机制：随机缺失（MCAR）填中位数误差可控，"
                    "系统性缺失（比如年轻用户不爱填）填出来的就是假数据。"
                    "B 会把平均年龄严重拉低；C 丢掉整列等于放弃信息；D 丢掉 30% 的行会让样本严重偏斜。"
                    "加一列「是否填充」标记是常被忽略但很实用的一招 —— 让下游知道哪些值是猜的。"
                ),
            },
            {
                "type": "choice",
                "stem": "`df.drop_duplicates()` 默认按什么判断两行重复？",
                "options": [
                    "所有列的值都相同才算重复",
                    "只按第一列的值",
                    "按行索引",
                    "按行号加列名的组合",
                ],
                "answer_index": 0,
                "explanation": (
                    "默认是「整行所有列都相同」。业务上通常要按主键去重，"
                    "这时必须显式写 `subset=\"order_id\"`，否则一条订单改过一次金额就不会被判为重复。"
                ),
            },
            {
                "type": "judge",
                "stem": "金额列有缺失值时，用 0 填充是安全的，不会影响后续的平均值计算。",
                "answer": False,
                "explanation": "填 0 会把平均值拉低，还把「这单没花钱」和「这单没记录」混成一种情况。数值列优先中位数，或者干脆保留 NaN 让统计函数按需跳过。",
            },
            {
                "type": "blank",
                "stem": "用中位数填充 amount 列的缺失值，补全这一行：\ndf[\"amount\"] = df[\"amount\"].fillna(df[\"amount\"].___())",
                "answer": "median",
                "accept": ["median"],
                "hint": "一个统计量",
                "explanation": "`median()` 是中位数，抗极值能力比 `mean()` 强，是数值列填充的默认选择。",
            },
            {
                "type": "short",
                "stem": "面试官问：你怎么发现异常值？发现之后会直接删掉吗？",
                "keywords": ["IQR", "3σ", "业务规则", "describe", "标记而不是删", "说明"],
                "reference": (
                    "分三步：先用 `describe()` 和箱线图看量级，找明显不合理的数据；"
                    "再用统计规则圈候选 —— `Q3 + 1.5 * IQR` 或偏离均值 3σ；"
                    "最后用业务规则兜底，比如金额不能为负、年龄不能超过 100，这一条通常比统计规则更可靠。"
                    "发现之后不会直接删：先判断是录入错误（可修正）还是真实极值（应保留但要在报告里说明），"
                    "而且至少要留痕 —— 删了多少条、按什么规则删的，否则结论没法复核。"
                ),
                "explanation": "「先标记、不直接删」是数据清洗的基本职业素养，面试官很在意这一点。",
            },
        ],
    },
    # ----------------------------------------------------------------- da-05
    {
        "code": "da-05",
        "subject": "数据分析与处理",
        "stage": "Pandas 处理",
        "runner": "python",
        "title": "分组聚合 groupby",
        "summary": "分组算指标，分析的主力工具",
        "definition": (
            "`groupby` 的模型是 **split-apply-combine**：按键把行拆成若干组（split），"
            "每组算一次（apply），再把结果拼回来（combine）。\n\n"
            "三种输出形态，用途完全不同：\n\n"
            "- **聚合 `agg`**：每组压成一个值，**行数变少**。"
            "`df.groupby(\"dept\")[\"salary\"].mean()`；多指标用命名聚合 "
            "`df.groupby(\"dept\").agg(total=(\"salary\", \"sum\"), avg=(\"salary\", \"mean\"))`\n"
            "- **变换 `transform`**：返回和原组**等长**的结果，**行数不变**，"
            "所以能把组内统计量贴回每一行，比如算「本人薪资占组内均值的比例」\n"
            "- **过滤 `filter`**：按组的整体情况筛掉整组，比如只要「人数大于 10 的部门」\n\n"
            "分组键可以是多列：`df.groupby([\"dept\", \"city\"])`，此时结果是 MultiIndex，"
            "用 `reset_index()` 变回普通表。\n\n"
            "**它解决什么问题**：把「按某个维度看指标」这件事从手工循环变成一行代码。"
            "面试里问 groupby，本质是在问：**你知不知道 `agg` 和 `transform` 的输出形状不一样**。"
        ),
        "plain": (
            "groupby 就像**把一叠扑克牌按花色分成几堆**（split），"
            "每堆各自数一数（apply），最后把各堆的结果写在纸上（combine）。\n\n"
            "`agg` 和 `transform` 的区别，用分堆打比方最清楚：\n\n"
            "- `agg` 是「每堆算出**一个**数字」，比如每堆的平均点数 —— 写完纸上的行数变少了\n"
            "- `transform` 是「给**每一张牌**都贴上它所在堆的平均点数」—— 牌还是那么多张，"
            "每张都多了一个信息，这样才能拿它和牌本身的点数做比较\n\n"
            "所以「算每个人的薪资是部门均值的几倍」只能用 `transform`："
            "你需要一列和原表等长的部门均值，贴回每一行才能相除。"
        ),
        "example": (
            "import pandas as pd\n"
            "\n"
            "sales = pd.DataFrame({\n"
            "    \"dept\":   [\"研发\", \"研发\", \"研发\", \"产品\", \"产品\", \"测试\", \"测试\"],\n"
            "    \"city\":   [\"北京\", \"上海\", \"北京\", \"北京\", \"上海\", \"北京\", \"上海\"],\n"
            "    \"salary\": [18000, 22000, 25000, 15000, 9000, 12000, 11000],\n"
            "})\n"
            "\n"
            "print(sales.groupby(\"dept\")[\"salary\"].mean().to_dict())   # 每组一个均值\n"
            "\n"
            "agg = sales.groupby(\"dept\").agg(total=(\"salary\", \"sum\"), avg=(\"salary\", \"mean\"))\n"
            "print(agg)\n"
            "\n"
            "print(sales.groupby([\"dept\", \"city\"])[\"salary\"].size().to_dict())   # 多列分组\n"
            "\n"
            "# transform：把「组内均值」贴回每一行，行数不变，方便和原值相除\n"
            "avg = sales.groupby(\"dept\")[\"salary\"].transform(\"mean\")\n"
            "print((sales[\"salary\"] / avg).round(3).tolist())"
        ),
        "example_output": (
            "{'产品': 12000.0, '测试': 11500.0, '研发': 21666.666666666668}\n"
            "      total           avg\n"
            "dept                     \n"
            "产品    24000  12000.000000\n"
            "测试    23000  11500.000000\n"
            "研发    65000  21666.666667\n"
            "{('产品', '上海'): 1, ('产品', '北京'): 1, ('测试', '上海'): 1, ('测试', '北京'): 1, ('研发', '上海'): 1, ('研发', '北京'): 2}\n"
            "[0.831, 1.015, 1.154, 1.25, 0.75, 1.043, 0.957]"
        ),
        "pitfalls": [
            "**`agg` 和 `transform` 的输出形状不同**：`agg` 每组一个值（行数变少），`transform` 必须返回等长结果（行数不变）。要把组内统计量贴回原行，只能用 `transform`。",
            "**groupby 默认丢掉 NaN 分组**：分组键是 NaN 的行会整组消失，要 `dropna=False` 才保留；数值列的 `mean()` 也默认跳过 NaN（这通常是你要的，但要知道）。",
            "**多列分组的结果是 MultiIndex**：取某个组合要写 `result.loc[(\"研发\", \"北京\")]`，想变回普通列用 `reset_index()`。",
            "**别用 `groupby(...).apply(...)` 做简单运算**：pandas 3 里它慢、返回形状还不稳定。优先 `agg`（压成一个值）或 `transform`（贴回原行），只有返回结构真的不规则时才用 `apply`。",
        ],
        "task": (
            "题目已经给好了 `sales`（部门、城市、薪资）。\n\n"
            "1. 按 `dept` 分组算薪资均值，结果存到 `by_dept`\n"
            "2. 用**命名聚合**一次算出每组的总薪资和平均薪资，结果存到 `agg_table`，"
            "聚合列名必须是 `total` 和 `avg`\n"
            "3. 按 `dept` 分组算每组行数，结果存到 `dept_size`\n"
            "4. 用 `transform` 算出「组内均值」，再用「本人薪资 ÷ 组内均值」得到 `ratio`\n"
            "5. 写函数 `group_avg(df, key, value)`：按 `key` 列分组，返回 `value` 列的均值"
            "（返回 Series 或字典都可以，要能按组名取值）"
        ),
        "setup": (
            "import pandas as pd\n"
            "\n"
            "sales = pd.DataFrame({\n"
            "    \"dept\":   [\"研发\", \"研发\", \"研发\", \"产品\", \"产品\", \"测试\", \"测试\"],\n"
            "    \"city\":   [\"北京\", \"上海\", \"北京\", \"北京\", \"上海\", \"北京\", \"上海\"],\n"
            "    \"name\":   [\"张伟\", \"李娜\", \"刘洋\", \"王强\", \"陈静\", \"赵敏\", \"周涛\"],\n"
            "    \"salary\": [18000, 22000, 25000, 15000, 9000, 12000, 11000],\n"
            "})\n"
        ),
        "starter": (
            "# sales 已经给好了\n"
            "\n"
            "by_dept = None     # 按 dept 分组算薪资均值\n"
            "agg_table = None   # 命名聚合：total=sum, avg=mean\n"
            "dept_size = None   # 每组行数\n"
            "ratio = None       # 本人薪资 / 组内均值（用 transform）\n"
            "\n"
            "\n"
            "def group_avg(df, key, value):\n"
            "    \"\"\"按 key 列分组，返回 value 列的均值。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "`by_dept = sales.groupby(\"dept\")[\"salary\"].mean()`；"
            "命名聚合写成 `sales.groupby(\"dept\").agg(total=(\"salary\", \"sum\"), avg=(\"salary\", \"mean\"))`；"
            "行数用 `.size()`。ratio 的关键是 `sales.groupby(\"dept\")[\"salary\"].transform(\"mean\")` "
            "得到一列和原表等长的组内均值，再拿薪资去除。"
        ),
        "checker": DA05_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官问：`groupby().apply()` 和 `groupby().transform()` 的区别是什么？",
                "options": [
                    "apply 每组可以返回任意形状（结果行数可变），transform 必须返回和原组等长的结果（行数不变），所以「把组内统计量贴回每一行」只能用 transform",
                    "两者只是名字不同，结果完全一样",
                    "transform 只能算 sum 和 mean，apply 什么都能算",
                    "apply 更快，所以应该优先用 apply",
                ],
                "answer_index": 0,
                "explanation": (
                    "核心区别是**输出形状**：`transform` 返回与原表等长的一列，能直接和原列做运算（比如算组内占比、组内排序）；"
                    "`apply` 每组可以返回标量、Series 或 DataFrame，形状不规则。"
                    "pandas 3 里简单聚合一律用 `agg`、贴回原行用 `transform`，`apply` 只在返回结构真不规则时用。"
                ),
            },
            {
                "type": "choice",
                "stem": "`df.groupby(\"dept\")[\"salary\"].mean()` 返回的是什么？",
                "options": [
                    "一个 Series：index 是 dept，值是每组的平均薪资",
                    "一个 DataFrame，行数和原表一样多",
                    "一个标量（所有薪资的均值）",
                    "一个字典",
                ],
                "answer_index": 0,
                "explanation": (
                    "这是「分组的键 + 一列 + 一个聚合函数」的典型结果：返回 Series，索引是分组键。"
                    "想变回普通表用 `.reset_index()`，想去掉索引用 `.to_dict()`。"
                ),
            },
            {
                "type": "judge",
                "stem": "用 groupby 分组时，分组键为 NaN 的那些行默认会被丢掉。",
                "answer": True,
                "explanation": "默认 `dropna=True`。如果「缺失」本身是一个有意义的类别（比如「未填城市」），要写 `dropna=False` 把它保留成一个组。",
            },
            {
                "type": "blank",
                "stem": "要把每组的平均薪资贴回原表、且行数保持不变，补全这一行：\ndf[\"dept_avg\"] = df.groupby(\"dept\")[\"salary\"].___(\"mean\")",
                "answer": "transform",
                "accept": ["transform"],
                "hint": "填方法名",
                "explanation": "`transform` 保证结果长度和原组一致，所以能直接写成新列；换成 `agg` 行数会变少，赋值时会因长度不匹配而失败。",
            },
            {
                "type": "short",
                "stem": "面试官问：一张订单表，要算「每个城市每个月的 GMV 和订单数」，还要保留当月没有订单的城市，你会怎么写？",
                "keywords": ["groupby", "多列分组", "agg", "size", "merge", "fillna"],
                "reference": (
                    "先聚合：`df.groupby([\"city\", \"month\"]).agg(gmv=(\"amount\", \"sum\"), orders=(\"order_id\", \"nunique\"))`。"
                    "但 groupby 只会输出有订单的组合，所以「零订单的城市」拿不到。"
                    "要补齐就得构造「城市 × 月份」的完整组合（城市维表 cross join 月份列表），"
                    "再把聚合结果 `left merge` 上去，缺失的行用 `fillna(0)` 补 0，"
                    "这样才是完整的报表口径。顺带要说明 GMV 是按什么时间口径算的。"
                ),
                "explanation": "「groupby 拿不到零值」是实战里最常见的报表口径坑，能答出来很加分。",
            },
        ],
    },
    # ----------------------------------------------------------------- da-06
    {
        "code": "da-06",
        "subject": "数据分析与处理",
        "stage": "Pandas 处理",
        "runner": "python",
        "title": "表连接、透视与重塑",
        "summary": "merge 对齐数据，pivot 换方向",
        "definition": (
            "**连接（merge）** 把两张表按一个或多个键对齐。`how` 参数决定保留哪些行：\n\n"
            "- `how=\"inner\"`：只保留**两边都能匹配上**的行\n"
            "- `how=\"left\"`：保留**左表全部**行，右表没匹配到的列填 NaN\n"
            "- `how=\"right\"` / `how=\"outer\"`：保留右表 / 两边全部\n\n"
            "匹配关系决定行数：一对一不变、一对多会**放大**、多对多会**成倍放大**。"
            "所以 merge 前后各看一次 `len()` 是个好习惯。\n\n"
            "**透视（pivot）** 把「长表」变成「宽表」，把某个字段的取值拉成列。\n\n"
            "- `pivot_table(index=..., columns=..., values=..., aggfunc=\"sum\", fill_value=0)`："
            "**会聚合**，遇到重复的 (index, columns) 组合按 `aggfunc` 算掉，还支持 `fill_value` 补空\n"
            "- `pivot(...)`：**只做形状变换**，遇到重复组合直接报错\n\n"
            "反向操作是 `melt`（宽表转长表）和 `stack` / `unstack`。\n\n"
            "**它解决什么问题**：真实数据分散在多张表里（订单、用户、商品），"
            "要按业务维度看指标就必须先对齐（merge）再换视角（pivot）。"
            "面试里问 merge 的 `how`、问 merge 后行数变了怎么办，考的都是这个。"
        ),
        "plain": (
            "`merge` 像**把两份名单按姓名对齐合并**：\n\n"
            "- `left` 是「以我这份名单为准」—— 我名单上的人一个都不能少，对方那份没查到的先空着\n"
            "- `inner` 是「只要两边都有的」—— 名单上查不到的人直接不列\n"
            "- 如果对方那份名单里同一个名字出现了两次，你合并后就变成两行 —— "
            "这就是「merge 之后行数变多」的真相，不是 bug，是一对多\n\n"
            "`pivot_table` 像**把一张竖着记的流水账摆成一张交叉表**："
            "原来是「月份 + 城市 + 金额」一行行记，摆开之后行是月份、列是城市，"
            "格子里是金额合计 —— 就是 Excel 里的数据透视表。"
        ),
        "example": (
            "import pandas as pd\n"
            "\n"
            "users = pd.DataFrame({\n"
            "    \"user_id\": [1, 2, 3, 4],\n"
            "    \"name\":    [\"张伟\", \"李娜\", \"刘洋\", \"王强\"],\n"
            "    \"city\":    [\"北京\", \"上海\", \"北京\", \"杭州\"],\n"
            "})\n"
            "orders = pd.DataFrame({\n"
            "    \"order_id\": [101, 102, 103, 104, 105],\n"
            "    \"user_id\":  [1, 1, 2, 3, 9],\n"
            "    \"amount\":   [120.0, 300.0, 150.0, 90.0, 200.0],\n"
            "})\n"
            "\n"
            "left = orders.merge(users, on=\"user_id\", how=\"left\")\n"
            "print(left.shape, int(left[\"name\"].isna().sum()))   # 左连接保留全部订单，缺人的那行 name 是 NaN\n"
            "\n"
            "inner = orders.merge(users, on=\"user_id\", how=\"inner\")\n"
            "print(inner.shape)                                  # 内连接只留两边都匹配的\n"
            "\n"
            "print(inner.pivot_table(index=\"city\", values=\"amount\", aggfunc=[\"count\", \"sum\"]))\n"
            "print(inner.pivot_table(index=\"city\", columns=\"name\", values=\"amount\",\n"
            "                        aggfunc=\"sum\", fill_value=0))"
        ),
        "example_output": (
            "(5, 5) 1\n"
            "(4, 5)\n"
            "      count    sum\n"
            "     amount amount\n"
            "city              \n"
            "上海        1  150.0\n"
            "北京        3  510.0\n"
            "name    刘洋     张伟     李娜\n"
            "city                    \n"
            "上海     0.0    0.0  150.0\n"
            "北京    90.0  420.0    0.0"
        ),
        "pitfalls": [
            "**`how` 决定保留谁**：`left` 保留左表全部（匹配不到填 NaN），`inner` 只留两边都匹配的。用 left 之后数一下 `isna().sum()`，这个数就是「多少条找不到对应记录」。",
            "**merge 会悄悄放大行数**：右表键有重复值时，一条左表记录会匹配出多行。merge 前后都 `len()` 一下、必要时先对右表去重，能避免结果总量算错。",
            "**`pivot` 遇到重复组合会报错**：同一个 (index, columns) 组合出现两次时只能 `pivot_table` 加 `aggfunc` 聚合，`pivot` 会直接抛异常。",
            "**连接键的类型要一致**：一边 `int64`、一边 `str`（比如 `1` 和 `\"1\"`）匹配不上，结果是整列 NaN，而且**不报错**。merge 前先 `astype` 对齐类型。",
        ],
        "task": (
            "题目已经给好了 `users`（用户维度表）和 `orders`（订单表）。"
            "注意 `orders` 里有一条 `user_id=9` 找不到对应的人。\n\n"
            "1. 用**左连接**把用户信息拼到订单上，结果存到 `merged`\n"
            "2. 数出 `merged` 里 `name` 缺失的行数，存到 `n_missing`（整数）\n"
            "3. 用**内连接**得到只含有效用户的订单，结果存到 `inner`\n"
            "4. 用 `inner` 做透视：行是 `city`、值是 `amount` 的合计，结果存到 `pivot`\n"
            "5. 写函数 `join_orders(orders, users)`：返回两个表按 `user_id` **左连接**的结果"
        ),
        "setup": (
            "import pandas as pd\n"
            "\n"
            "users = pd.DataFrame({\n"
            "    \"user_id\": [1, 2, 3, 4],\n"
            "    \"name\":    [\"张伟\", \"李娜\", \"刘洋\", \"王强\"],\n"
            "    \"city\":    [\"北京\", \"上海\", \"北京\", \"杭州\"],\n"
            "})\n"
            "orders = pd.DataFrame({\n"
            "    \"order_id\": [101, 102, 103, 104, 105],\n"
            "    \"user_id\":  [1, 1, 2, 3, 9],\n"
            "    \"amount\":   [120.0, 300.0, 150.0, 90.0, 200.0],\n"
            "})\n"
        ),
        "starter": (
            "# users / orders 已经给好了\n"
            "\n"
            "merged = None      # 左连接：orders + users\n"
            "n_missing = None   # merged 里 name 缺失的行数（整数）\n"
            "inner = None       # 内连接：只留两边都匹配的\n"
            "pivot = None       # 按 city 汇总 amount\n"
            "\n"
            "\n"
            "def join_orders(orders, users):\n"
            "    \"\"\"按 user_id 左连接，返回新的 DataFrame。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "`orders.merge(users, on=\"user_id\", how=\"left\")`，内连接把 `how` 换成 `\"inner\"`。"
            "缺失数用 `merged[\"name\"].isna().sum()`。"
            "透视用 `inner.pivot_table(index=\"city\", values=\"amount\", aggfunc=\"sum\")`，"
            "结果里 `pivot.loc[\"北京\", \"amount\"]` 就是北京的合计。"
        ),
        "checker": DA06_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "面试官问：merge 的 `how=\"left\"` 和 `how=\"inner\"` 有什么区别？",
                "options": [
                    "left 保留左表全部行、右表匹配不到的列填 NaN；inner 只保留两边都能匹配上的行",
                    "left 只保留左表的列，inner 保留两边的列",
                    "没有区别，只是写法不同",
                    "left 会按左表排序，inner 不排序",
                ],
                "answer_index": 0,
                "explanation": (
                    "区别只在**保留哪些行**。列总是两边都带上（除非用 `suffixes` 处理重名列）。"
                    "实战里用 left 连接的常见用途是「查有多少条数据找不到主表记录」，"
                    "直接数结果里的 NaN 就行。"
                ),
            },
            {
                "type": "choice",
                "stem": "`pivot_table` 和 `pivot` 的关键区别是什么？",
                "options": [
                    "pivot 遇到重复的 (index, columns) 组合会直接报错，pivot_table 会用 aggfunc 把重复聚合掉，还支持 fill_value",
                    "pivot_table 只能做求和，pivot 可以算其它聚合",
                    "pivot 支持 fill_value，pivot_table 不支持",
                    "两者完全等价",
                ],
                "answer_index": 0,
                "explanation": (
                    "`pivot` 是纯形状变换，它要求每个 (行, 列) 组合唯一，否则不知道该填哪个值；"
                    "`pivot_table` 是「透视表」，重复组合按 `aggfunc`（默认 mean）算掉，"
                    "还能加 `fill_value=0` 把空组合补 0、`margins=True` 加合计行。"
                ),
            },
            {
                "type": "judge",
                "stem": "两张表用 merge 连接之后，结果的行数不可能比原来多。",
                "answer": False,
                "explanation": "一对多与多对多连接都会放大结果行数：左表一条记录匹配到右表多条，就会变成多行。merge 前后各 `len()` 一次，是对账的最低要求。",
            },
            {
                "type": "blank",
                "stem": "要把用户表里「所有用户」都保留下来做连接，`how` 参数应该填：\norders.merge(users, on=\"user_id\", how=\"___\")",
                "answer": "left",
                "accept": ["left", "'left'"],
                "hint": "一个英文单词",
                "explanation": "要保留 users 的全部行，就把 users 放在右表、用 `how=\"left\"`（左表保留全部）。反过来把 users 放左表用 right 也行，但可读性差，不推荐。",
            },
            {
                "type": "short",
                "stem": "面试官问：merge 之后你发现行数比原来多了，会怎么排查？",
                "keywords": ["一对多", "重复键", "value_counts", "去重", "核对总量", "口径"],
                "reference": (
                    "先确认放大的是哪一侧：对连接键做 `value_counts()`，看右表（或左表）的键有没有重复；"
                    "有重复就说明这是一对多，放大是正常行为，但要判断业务上是否合理，"
                    "比如订单表按 user_id 连用户表，一个人有 5 单就必然出 5 行。"
                    "如果右表本该唯一却有重复（维度表脏了），要先 `drop_duplicates(subset=\"主键\")` 再连；"
                    "另外要核对连接后的金额总和有没有变 —— 行数放大会让 sum 跟着翻倍，这是最容易翻车的地方。"
                ),
                "explanation": "面试官想听的判断顺序是：先确认匹配关系（一对一/一对多），再决定是修哪张表。",
            },
        ],
    },
    # ----------------------------------------------------------------- da-07
    {
        "code": "da-07",
        "subject": "数据分析与处理",
        "stage": "分析与可视化",
        "runner": "python",
        "title": "时间序列处理",
        "summary": "时间列要先转类型，dt 才能取年月日",
        "definition": (
            "时间列从 CSV 读进来时是**字符串**，字符串没有月份、星期这些概念，"
            "所以第一步永远是 `pd.to_datetime(s)`，把它变成 `datetime64` 类型。"
            "转换之后才有 `.dt` 访问器：\n\n"
            "- `df[\"date\"].dt.year / .month / .day / .hour`\n"
            "- `df[\"date\"].dt.dayofweek`（周一 = 0，周日 = 6）\n"
            "- `df[\"date\"].dt.strftime(\"%Y-%m\")` → 变成 `\"2026-01\"` 这样的字符串，适合直接做分组键\n"
            "- 想做真正的周期运算用 `dt.to_period(\"M\")`（同一月视为相等）\n\n"
            "**按月/按周汇总**有两条路：\n\n"
            "- `df.assign(m=df[\"date\"].dt.strftime(\"%Y-%m\")).groupby(\"m\")[...].sum()`：灵活，能按月、按周、按任意键\n"
            "- `df.set_index(\"date\")[...].resample(\"ME\").sum()`：要求时间做索引，`\"ME\"` 是月末，"
            "好处是**空月份会自动补出来**（groupby 不会）\n\n"
            "**环比**用 `pct_change()`：第一期没有可比对象，**必然是 NaN**，不要用 0 顶替。\n\n"
            "**它解决什么问题**：让「最近 7 天」「同比环比」「工作日 vs 周末」这类问题变成一行代码，"
            "而不是手工切字符串。面试里问时间序列，八成就是问 `to_datetime` + `resample` + 环比。"
        ),
        "plain": (
            "字符串日期就像**一张写着「2026-01-05」的纸条**：你能读，但它不知道那天是星期几。"
            "`pd.to_datetime` 相当于把纸条换成**一个真正的日历对象**，"
            "从此问它「几月」「星期几」「上一条差几天」都能立刻回答 —— 这就是 `.dt`。\n\n"
            "`resample` 可以想成**把流水账按时间刻度装进不同的抽屉**："
            "按天、按周、按月各装一盒，再对每盒做一次汇总。"
            "它比 groupby 多做的关键一件事：**空抽屉也会留着**。"
            "某个月一单都没有，groupby 会把这个月整个跳过（环比就断链了），"
            "resample 会给你一个 0 或者 NaN —— 报表要的就是这种「不缺行」。"
        ),
        "example": (
            "import pandas as pd\n"
            "\n"
            "df = pd.DataFrame({\n"
            "    \"date\":   [\"2026-01-05\", \"2026-01-18\", \"2026-02-03\", \"2026-02-20\", \"2026-03-07\"],\n"
            "    \"amount\": [120.0, 80.0, 200.0, 150.0, 90.0],\n"
            "})\n"
            "\n"
            "df[\"date\"] = pd.to_datetime(df[\"date\"])          # 先转 datetime，否则没有 .dt\n"
            "df[\"month\"] = df[\"date\"].dt.strftime(\"%Y-%m\")    # 取出「年-月」\n"
            "df[\"weekday\"] = df[\"date\"].dt.dayofweek          # 0 = 周一\n"
            "\n"
            "print(df.groupby(\"month\")[\"amount\"].sum().to_dict())\n"
            "\n"
            "df = df.sort_values(\"date\")\n"
            "print(df[\"amount\"].diff().tolist())              # 和上一条记录的差\n"
            "print(df.set_index(\"date\")[\"amount\"].resample(\"ME\").sum().tolist())"
        ),
        "example_output": (
            "{'2026-01': 200.0, '2026-02': 350.0, '2026-03': 90.0}\n"
            "[nan, -40.0, 120.0, -50.0, -60.0]\n"
            "[200.0, 350.0, 90.0]"
        ),
        "pitfalls": [
            "**字符串日期没有 `.dt`**：直接写 `df[\"date\"].dt.month` 会报 `AttributeError`，必须先 `pd.to_datetime`。",
            "**混合格式要显式声明**：`2026-01-05` 和 `2026/01/06` 混在同一列时，新版 pandas 会要求写 `format=\"mixed\"`，否则报错。",
            "**`resample` 要求时间列做索引**：`df.set_index(\"date\")[...].resample(\"ME\")`；另外 `\"M\"` 已废弃，月末用 `\"ME\"`。",
            "**不要用 `.dt.week`**：ISO 周编号在跨年时含义有歧义，新版 pandas 已废弃，要周编号用 `.dt.isocalendar().week`。",
        ],
        "task": (
            "题目已经给好了 `df`（`date` 是字符串、`amount` 是金额）。\n\n"
            "1. 把 `df[\"date\"]` 转成 datetime 类型（结果留在 `df` 里）\n"
            "2. 给 `df` 新增 `month` 列，值是 `\"2026-01\"` 这样的「年-月」字符串\n"
            "3. 给 `df` 新增 `weekday` 列，值是星期编号（周一 = 0）\n"
            "4. 按 `month` 汇总 `amount` 得到 `monthly`\n"
            "5. 写函数 `monthly_amount(df, date_col, value_col)`：按「年-月」分组对 `value_col` 求和，"
            "返回结果（Series 或字典都行，要能按 `\"2025-01\"` 这种键取值）\n\n"
            "注意函数里的列名必须从参数来 —— 系统会换一张日期列叫 `day` 的表再测一次。"
        ),
        "setup": (
            "import pandas as pd\n"
            "\n"
            "df = pd.DataFrame({\n"
            "    \"date\":   [\"2026-01-05\", \"2026-01-18\", \"2026-02-03\", \"2026-02-20\", \"2026-03-07\", \"2026-03-19\"],\n"
            "    \"amount\": [120.0, 80.0, 200.0, 150.0, 90.0, 260.0],\n"
            "})\n"
        ),
        "starter": (
            "# df 已经给好了，date 现在还是字符串\n"
            "\n"
            "# 1. 把 df['date'] 转成 datetime\n"
            "# 2. 新增 month 列（'2026-01' 这种）\n"
            "# 3. 新增 weekday 列（周一 = 0）\n"
            "\n"
            "monthly = None     # 按 month 汇总 amount\n"
            "\n"
            "\n"
            "def monthly_amount(df, date_col, value_col):\n"
            "    \"\"\"按年-月分组，对 value_col 求和。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "`pd.to_datetime(df[\"date\"])` 转类型，`df[\"date\"].dt.strftime(\"%Y-%m\")` 取年月，"
            "`df[\"date\"].dt.dayofweek` 取星期编号。"
            "汇总用 `df.groupby(\"month\")[\"amount\"].sum()`。"
            "函数里先把 `date_col` 转成 datetime，再拼一列年月字符串（`assign` 或先复制一份小表都行），"
            "最后 `groupby(...)[value_col].sum()` 返回。"
        ),
        "checker": DA07_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "时间列读进来是字符串，要取「月份」的正确做法是？",
                "options": [
                    "先 pd.to_datetime 转成 datetime，再用 .dt.month 或 .dt.strftime(\"%Y-%m\")",
                    "直接写 df[\"date\"].month",
                    "用 df[\"date\"].str[5:7] 切字符串",
                    "不用转换，pd.to_period 能直接作用在字符串上",
                ],
                "answer_index": 0,
                "explanation": (
                    "字符串没有 `.dt` 也没有 `.month`，必须先 `pd.to_datetime`。"
                    "C 能切出「01」，但跨年、格式不统一时立刻出错（比如 `2026/1/5` 只有 9 个字符），"
                    "而且切出来是字符串，没法做真正的时间运算。"
                ),
            },
            {
                "type": "choice",
                "stem": "`df.set_index(\"date\")[\"amount\"].resample(\"ME\").sum()` 里的 `\"ME\"` 表示什么？",
                "options": [
                    "按月聚合，且结果落在月末（Month End）",
                    "按分钟聚合",
                    "按每月的中间一天聚合",
                    "按年平均",
                ],
                "answer_index": 0,
                "explanation": (
                    "`ME` = Month End，按月划分、标签取月末；旧的 `\"M\"` 已废弃。"
                    "同族还有 `\"D\"`（日）、`\"W\"`（周）、`\"QE\"`（季末）、`\"YE\"`（年末）。"
                ),
            },
            {
                "type": "judge",
                "stem": "用 resample 之前，必须先把时间列设为索引。",
                "answer": True,
                "explanation": "`resample` 是「按时间索引重采样」，所以时间列必须是索引（且最好排过序）。数据没排序时结果顺序可能不符合预期。",
            },
            {
                "type": "blank",
                "stem": "要取 ISO 周编号，补全这一行：\nweek = df[\"date\"].dt.___().week",
                "answer": "isocalendar",
                "accept": ["isocalendar"],
                "hint": "一个方法名",
                "explanation": "`.dt.isocalendar()` 返回年、周、星期编号三列，`.week` 就是 ISO 周。旧的 `.dt.week` 有跨年歧义，已废弃。",
            },
            {
                "type": "short",
                "stem": "面试官问：要算一份订单表每个月的 GMV 环比增长率，你会怎么写？有哪些坑？",
                "keywords": ["to_datetime", "resample", "pct_change", "排序", "第一期 NaN", "空月份"],
                "reference": (
                    "先 `pd.to_datetime` 转时间列并设为索引、排好序，再 `resample(\"ME\").sum()`（或按月 groupby）"
                    "得到月度序列，最后 `pct_change()` 得到环比。三个坑："
                    "一是第一期没有上一期，环比一定是 NaN；"
                    "二是某个月完全没有订单时 groupby 会缺这一行，环比就断链，需要 reindex 补齐或用 resample；"
                    "三是口径要写清楚 —— 按付款时间还是下单时间、是否含退款，不同口径的环比可能完全相反。"
                ),
                "explanation": "能主动提「空月份会断链」和「口径」，就说明真做过时间序列报表。",
            },
        ],
    },
    # ----------------------------------------------------------------- da-08
    {
        "code": "da-08",
        "subject": "数据分析与处理",
        "stage": "分析与可视化",
        "runner": "python",
        "title": "可视化与一份完整分析结论",
        "summary": "图给结论做证据，结论必须带数字",
        "definition": (
            "**选图只有一个判断标准：你想让对方看出什么关系。**\n\n"
            "- 看趋势（随时间变化）→ 折线图，时间放横轴\n"
            "- 比大小（类别之间）→ 柱状图，类别放横轴；类别多于 10 个就先排序取 Top N\n"
            "- 看构成 → 堆叠柱状图；饼图最多 5 个类别，再多就没法读\n"
            "- 看相关（两个数值变量）→ 散点图\n"
            "- 看分布 → 直方图 / 箱线图（箱线图还能直接看出异常值）\n\n"
            "**画图前必须先聚合**：直接画原始明细只会得到一张糊住的图。"
            "标准流程是「**分组 → 聚合 → 排序 → 只画前 N 个 → 标注单位和口径**」。\n\n"
            "**一套完整分析的四步**：\n\n"
            "1. 算基数：总量、环比、同比\n"
            "2. 找结构：按维度拆开（哪个城市、哪个渠道）\n"
            "3. 找极值：`idxmax()` / `max()` 定位峰值，`sort_values()` 排 Top N\n"
            "4. 下结论：**带数字、带口径、可复核**，例如"
            "「2026-03 销售额 390 元，环比 +50%，其中上海贡献 260 元」\n\n"
            "**它解决什么问题**：把一堆数字变成一句能直接拿去做决策的话。"
            "面试官最常追问的就是最后一步 —— 图和方法都是手段，**结论才是交付物**。"
        ),
        "plain": (
            "画图这件事，跟**给朋友讲一件事**一样：你希望对方记住什么，就给他看什么。\n\n"
            "想知道「有没有涨」 → 折线，像看心电图，一眼看出走势；"
            "想知道「谁最大」 → 柱状，像排队比身高，矮的高的并排站着；"
            "想知道「这块饼分给了谁」 → 但要小心，饼一切成七八块就没人能读出百分比了。\n\n"
            "而结论就像**给老板发的那条微信**："
            "「3 月涨了」这种话没人能用，因为他不知道涨了多少、靠什么涨的、要不要下一步动作。"
            "换成「3 月销售额 390 元、环比 +50%、其中上海贡献 260 元」，"
            "老板立刻能决定是加投上海还是去看别的地方。**结论的价值不在于形容词，在于数字和口径。**"
        ),
        "example": (
            "import pandas as pd\n"
            "\n"
            "sales = pd.DataFrame({\n"
            "    \"month\":  [\"2026-01\", \"2026-01\", \"2026-02\", \"2026-02\", \"2026-03\", \"2026-03\", \"2026-03\"],\n"
            "    \"city\":   [\"北京\", \"上海\", \"北京\", \"上海\", \"北京\", \"上海\", \"广州\"],\n"
            "    \"amount\": [120.0, 80.0, 200.0, 60.0, 90.0, 260.0, 40.0],\n"
            "})\n"
            "\n"
            "by_month = sales.groupby(\"month\")[\"amount\"].sum()\n"
            "print(by_month.to_dict())\n"
            "\n"
            "mom = by_month.pct_change()                      # 环比增长率，第一期一定是 NaN\n"
            "print(mom.round(3).to_dict())\n"
            "print(by_month.idxmax(), by_month.max())         # 峰值在哪个月、是多少\n"
            "\n"
            "pivot = sales.pivot_table(index=\"month\", columns=\"city\", values=\"amount\",\n"
            "                          aggfunc=\"sum\", fill_value=0)\n"
            "print(pivot)\n"
            "\n"
            "top_month = by_month.idxmax()\n"
            "print(f\"{top_month} 销售额最高，为 {by_month[top_month]:.0f} 元，环比 +{mom[top_month]:.0%}\")"
        ),
        "example_output": (
            "{'2026-01': 200.0, '2026-02': 260.0, '2026-03': 390.0}\n"
            "{'2026-01': nan, '2026-02': 0.3, '2026-03': 0.5}\n"
            "2026-03 390.0\n"
            "city        上海     北京    广州\n"
            "month                      \n"
            "2026-01   80.0  120.0   0.0\n"
            "2026-02   60.0  200.0   0.0\n"
            "2026-03  260.0   90.0  40.0\n"
            "2026-03 销售额最高，为 390 元，环比 +50%"
        ),
        "pitfalls": [
            "**选错图**：拿饼图看趋势、拿折线图比类别，都会让人读错。口诀是「时间用折线、类别用柱状、相关用散点、分布用直方」。（本课的沙箱没有装 matplotlib，画图在本地或 notebook 里做，这里练的是喂给图的数。）",
            "**不聚合就画**：把几万行明细直接画成图，得到的是糊成一片的散点。永远是「分组 → 聚合 → 排序 → 画前 N 个」。",
            "**让离群点压扁整张图**：一个 99999 会让其它数据全挤在坐标轴底部。画图前先按 da-04 的办法处理异常值，或者改用对数轴。",
            "**结论里没有数字和口径**：写「3 月增长明显」等于没写。必须是「2026-03 销售额 390 元，环比 +50%，其中上海贡献 260 元」这种能被复核的句子。",
        ],
        "task": (
            "题目已经给好了 `sales`（月份、城市、金额）。请把一份完整分析的结论算出来。\n\n"
            "1. 按月汇总销售额，存到 `by_month`\n"
            "2. 算环比增长率，存到 `mom`\n"
            "3. 找出销售额最高的月份存到 `top_month`\n"
            "4. 做一个透视表存到 `pivot`：行是 `month`、列是 `city`、值是 `amount` 合计，"
            "**空组合要显示 0 而不是 NaN**\n"
            "5. 写一句话结论存到 `conclusion`（字符串），"
            "里面**必须同时出现峰值月份和该月的销售额数字**\n"
            "6. 写函数 `mom_growth(s)`：接收一个数值 Series，返回它的环比增长率 Series"
        ),
        "setup": (
            "import pandas as pd\n"
            "\n"
            "sales = pd.DataFrame({\n"
            "    \"month\":  [\"2026-01\", \"2026-01\", \"2026-02\", \"2026-02\", \"2026-03\", \"2026-03\", \"2026-03\"],\n"
            "    \"city\":   [\"北京\", \"上海\", \"北京\", \"上海\", \"北京\", \"上海\", \"广州\"],\n"
            "    \"amount\": [120.0, 80.0, 200.0, 60.0, 90.0, 260.0, 40.0],\n"
            "})\n"
        ),
        "starter": (
            "# sales 已经给好了\n"
            "\n"
            "by_month = None    # 按月汇总 amount\n"
            "mom = None         # 环比增长率\n"
            "top_month = None   # 销售额最高的月份\n"
            "pivot = None       # 行=month，列=city，值=amount 合计，空格补 0\n"
            "conclusion = \"\"    # 一句话结论，必须有峰值月份和金额\n"
            "\n"
            "\n"
            "def mom_growth(s):\n"
            "    \"\"\"返回 Series s 的环比增长率。\"\"\"\n"
            "    # 在这里写 return\n"
            "    pass\n"
        ),
        "hint": (
            "汇总用 `sales.groupby(\"month\")[\"amount\"].sum()`；环比直接 `.pct_change()`，"
            "第一期会是 NaN，这是正常的。峰值用 `by_month.idxmax()`。"
            "透视表用 `pivot_table(index=\"month\", columns=\"city\", values=\"amount\", "
            "aggfunc=\"sum\", fill_value=0)`。结论用 f-string 把 `top_month` 和 "
            "`by_month[top_month]` 拼进去，记得用 `:.0f` 把 390.0 变成 390。"
        ),
        "checker": DA08_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要展示三个城市最近 6 个月的销售额变化，最合适的图是？",
                "options": [
                    "每个城市一条折线、横轴是月份",
                    "每个城市一块的饼图",
                    "把所有明细行画成散点图",
                    "把城市画成横轴的折线图，月份用颜色区分",
                ],
                "answer_index": 0,
                "explanation": (
                    "「随时间变化」用折线，时间必须在横轴；三条线并排还能直接比较城市之间的差距和斜率。"
                    "B 的饼图看不了趋势；C 的明细散点只会糊成一片；D 把时间塞进颜色，读者无法比较先后顺序。"
                ),
            },
            {
                "type": "choice",
                "stem": "面试官问：分析报告里最后那句结论，应该写成什么样？",
                "options": [
                    "2026-03 销售额 390 元，环比 +50%，其中上海贡献 260 元",
                    "整体趋势向好，建议继续保持",
                    "数据波动较大，建议持续关注",
                    "销售额有增有减，符合预期",
                ],
                "answer_index": 0,
                "explanation": (
                    "结论必须**带数字、带口径、可复核**：有月份、有金额、有环比、还指出了主要贡献方。"
                    "另外三个都是「正确的废话」—— 没数字就没法验证，也没法据此做决策。"
                ),
            },
            {
                "type": "judge",
                "stem": "画图之前应该先把数据聚合好，直接画原始明细能提供更多信息。",
                "answer": False,
                "explanation": "明细行数一多图就糊了，读者什么也读不出来。正确顺序是「分组 → 聚合 → 排序 → 只画关心的前 N 项」。",
            },
            {
                "type": "blank",
                "stem": "要算月度销售额的环比增长率，补全这一行：\nmom = by_month.___()",
                "answer": "pct_change",
                "accept": ["pct_change"],
                "hint": "一个方法名",
                "explanation": "`pct_change()` 算的是相对上一期的变化比例，第一期没有上一期，结果是 NaN —— 这比填 0 更诚实。",
            },
            {
                "type": "short",
                "stem": "面试官问：你交了一份分析报告，他说「这个结论可信吗」，你会怎么回答？",
                "keywords": ["口径", "样本量", "异常值", "反例", "交叉验证", "局限"],
                "reference": (
                    "先讲口径：数据从哪来、覆盖哪个时间段、指标怎么定义的，"
                    "比如 GMV 是按付款时间还是下单时间、有没有剔除退款 —— 口径不同结论可能反过来。"
                    "再讲样本量和覆盖率：每个结论背后有多少条数据撑着，"
                    "分成 20 个城市看趋势时，很可能每个城市只有几十单，那就只是噪声，不能当结论。"
                    "然后讲异常值和反例：有没有被极值影响的均值、有没有和结论相反的分组。"
                    "最后主动说局限：这份数据回答不了什么、还需要哪份数据来验证。"
                ),
                "explanation": "能主动交代口径和局限，是分析可信度最直接的体现。",
            },
        ],
    },
]
