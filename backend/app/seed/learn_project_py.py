"""Python 基础 30 课（py-*）在鸭先知项目里的真实落点。

每条都带 文件:行号，代码从源文件复制。行号对应 2026-10 的代码状态，
如果项目后续改动，按注释里的函数名能重新定位。
"""

from .learn_project_base import absent, choice, judge, used

REFS: dict[str, dict] = {
    "py-var": used(
        "config.py", "228",
        "CACHE_TTL = 3600                            # 缓存过期时间（秒）",
        "全项目共享的缓存过期时间，写在 config.py 里，core/cache.py 直接 import 使用。",
        "全大写是 Python 对「常量」的命名约定，读代码的人一眼就知道不该改它。"
        "这里把 3600 提成一个具名变量，而不是在 setex 里写死数字：改一处，所有缓存写入点同时生效。"
        "注意 Python 没有真正的常量，全大写只是约定——要真拦住修改得靠模块级只读设计。",
        [
            choice("项目里把 CACHE_TTL 写成全大写，主要目的是什么？",
                   ["提高运行速度", "告诉读代码的人「这是常量，不要改」", "让变量变成只读", "方便被 Redis 读取"],
                   1, "全大写是命名约定，Python 不会因此禁止修改。它传递的是「这是全局配置，不该在这里改」的信号。"),
            judge("在 Python 里把变量写成 CACHE_TTL = 3600，之后就绝对无法修改它的值。", 0,
                  "错。Python 没有 const 关键字，全大写只是约定。真要防修改得用只读属性或不可变结构，靠命名是拦不住的。"),
        ],
    ),
    "py-type": used(
        "core/cache.py", "310",
        'result[name] = int(self._client.get(k) or 0)',
        "统计看板从 Redis 读各个计数器，拼成字典返回。",
        "Redis 只有一个 String 类型，取回来的永远是字符串，`int(...)` 是必须的一步，否则 `\"3\" + \"5\"` 会拼成 `\"35\"`。"
        "`or 0` 兜住两种情况：键不存在返回 None、或者取到空串。注意这里不能写 `int(... or 0)` 就以为万事大吉——"
        "如果取回的是 `\"abc\"`，`int()` 照样抛 ValueError，所以真实代码外面还包了 try/except。",
        [
            choice("Redis 里存的是数字 3，取回来执行 int(...) 后与 5 相加，结果是多少？",
                   ["35", "8", "报错", "None"], 1,
                   "Redis 返回的是字符串 \"3\"，不做转换会拼成 \"35\"；int(\"3\") 之后才能得到 8。"),
            judge("int(\"3.5\") 能正常得到 3（截断小数）。", 0,
                  "错。int() 只接受整数字符串，int(\"3.5\") 会抛 ValueError；要转得先 float(\"3.5\") 再 int()，或用 int(float(\"3.5\"))。"),
        ],
    ),
    "py-op": used(
        "core/llm_client.py", "44",
        'd["hit_rate"] = round(100.0 * (d.get("cached_tokens") or 0) / pt, 2) if pt else 0.0',
        "算大模型前缀缓存的命中率，输出到统计接口。",
        "`/` 是真除法，7/2 得 3.5；要整除得写 `//`。这里先乘 100 再除，是为了让中间结果保持浮点、"
        "同时把「百分比」的语义写清楚。`if pt else 0.0` 是防除零——pt 为 0 时直接给 0，避免 ZeroDivisionError。",
        [
            choice("Python 里 7 / 2 和 7 // 2 分别得到什么？",
                   ["3.5 和 3", "3 和 3.5", "3.5 和 3.5", "都报错"], 0,
                   "/ 是真除法返回 float，// 是向下取整的整除。"),
            judge("表达式 100.0 * 3 / 4 会先算乘法再算除法，结果和 3 / 4 * 100.0 完全一样。", 0,
                  "错。虽然这个例子里结果相同，但浮点运算顺序会影响精度，大数相乘后再除才不容易丢精度。"),
        ],
    ),
    "py-str": used(
        "api/chat.py", "96",
        "yield f\"data: {json.dumps({'type': 'meta', 'reference_doc': []}, ensure_ascii=False)}\\n\\n\"",
        "把结构化数据拼成 SSE 帧推给前端，实现打字机效果。",
        "f-string 里可以嵌任意表达式，这里直接嵌了一次 `json.dumps(...)` 调用。"
        "末尾的 `\\n\\n` 不是随手加的：SSE 协议规定**两个换行**才算一帧结束，少一个前端就永远等不到消息。"
        "`ensure_ascii=False` 让中文原样输出，否则会被转成 `\\u6e38\\u4e50` 这种形式，体积翻几倍还看不懂。",
        [
            choice("SSE 帧末尾必须写 \\n\\n 的原因是什么？",
                   ["为了好看", "协议规定空行才代表一帧结束", "防止 JSON 乱码", "让浏览器自动重连"],
                   1, "SSE 用空行（连续两个 \\n）分隔事件帧，少一个换行前端会一直等这一帧，界面就卡住不动。"),
            judge("json.dumps(..., ensure_ascii=False) 会让中文以原字符输出，而不是 \\uXXXX 转义。", 1,
                  "对。默认 ensure_ascii=True 会把所有非 ASCII 字符转义，中文场景下既占体积又不利于排查日志。"),
        ],
    ),
    "py-if": used(
        "core/cache.py", "213",
        "if not self.available:\n    return",
        "写缓存前先判断 Redis 是否可用，不可用就不写，直接返回。",
        "这是典型的「卫语句」：把例外情况挡在最前面，后面的主逻辑就不用再套一层 if。"
        "`not self.available` 依赖对象的布尔语义——如果 available 是 False 或 None 都会进来。"
        "缓存是旁路组件，它挂了不能让问答跟着挂，所以这里选择静默跳过而不是抛异常。",
        [
            choice("把 `if not self.available: return` 写在函数开头，主要好处是什么？",
                   ["运行更快", "后面的主逻辑不用再多缩进一层，读起来更直", "能自动重连 Redis", "避免抛异常"],
                   1, "这叫卫语句（guard clause）。它把异常分支提前挡掉，主路径保持平铺，可读性比层层嵌套好。"),
            judge("如果 self.available 是 None，`if not self.available` 会报 TypeError。", 0,
                  "错。None 的布尔值是 False，not None 得 True，不会报错。要小心的是把 None 和 False 混在一起判断，逻辑上容易出错。"),
        ],
    ),
    "py-while": used(
        "database/db_mysql.py", "2385-2387",
        "while cursor_day.isoformat() in dset:\n    streak += 1\n    cursor_day -= timedelta(days=1)",
        "算连续签到天数：从今天（今天没签就退到昨天）往前逐天检查，签到过就 +1，直到断签为止。",
        "循环次数事先不知道——能连几天取决于用户实际签到记录，所以用 while 而不是 for。"
        "这类循环最容易踩的两个坑：**忘了推进条件**（漏掉 `cursor_day -= ...` 就死循环），"
        "以及**推进方向写反**（这里要往前翻，所以是 `-=`；写成 `+=` 会一直往未来走，一次都命中不了）。"
        "写 while 时先问自己：哪一行负责让它结束？",
        [
            choice("这段 while 循环如果删掉 `cursor_day -= timedelta(days=1)` 会发生什么？",
                   ["正常结束", "条件永远为真，死循环", "抛 ValueError", "只循环一次"],
                   1, "循环变量不推进，条件恒为真，程序卡死。任何 while 都要有一个明确的「退出推动器」。"),
            judge("只要知道循环要进行 10 次，就应该用 while 而不是 for。", 0,
                  "错。次数已知优先用 for（更不容易漏掉推进条件）；while 适合「次数事先不确定、由条件决定」的场景。"),
        ],
    ),
    "py-for": used(
        "core/bm25_index.py", "125-127",
        "for idx in top_indices:\n    if scores[idx] > 0:\n        results.append((self._corpus[idx], self._sources[idx], float(scores[idx])))",
        "遍历排好序的下标，把命中的文档拼成 (正文, 来源, 分数) 三元组。",
        "这里迭代的是**元素本身**（下标值），不是 `range(len(top_indices))`——Python 的 for 直接拿元素，"
        "只有真的需要「第几个」时才用 enumerate。三个列表按下标对齐取值，是典型的「并行数组」写法，"
        "能跑但不够安全：一旦某个列表长度不一致就会 IndexError。",
        [
            choice("要同时拿到下标和元素，最地道的写法是哪个？",
                   ["for i in range(len(xs)): x = xs[i]", "for i, x in enumerate(xs):", "for x in xs: i = xs.index(x)", "while i < len(xs):"],
                   1, "enumerate 一次给出 (下标, 元素)，比 range(len()) 干净，也不会因为 xs.index(x) 在重复元素时取错位置。"),
            judge("for idx in top_indices 里的 idx 是列表下标，不是列表里的值。", 0,
                  "错。top_indices 本身就是一串下标值，for 拿到的是它的元素；叫 idx 只是命名，语义上它就是值。"),
        ],
    ),
    "py-list": used(
        "core/bm25_index.py", "123-127",
        "results = []\ntop_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]\nfor idx in top_indices:\n    if scores[idx] > 0:\n        results.append((self._corpus[idx], self._sources[idx], float(scores[idx])))\nreturn results",
        "BM25 检索的主流程：先建空列表，再逐条 append 命中结果。",
        "列表是有序、可变、允许重复的容器，`append` 均摊 O(1)，所以「先建空列表再往里塞」是 Python 里最常见的收集模式。"
        "注意最后必须 `return results`——新手常把 `results = []` 写在循环里，每轮都清空，最后只剩一条。",
        [
            choice("把 `results = []` 写进 for 循环体内，会发生什么？",
                   ["没影响", "每轮都清空，最后只剩最后一条", "报 UnboundLocalError", "结果顺序变反"],
                   1, "初始化必须在循环外。放进去等于每轮重新开始收集。"),
            judge("Python 列表的 append 在尾部追加，平均时间复杂度是 O(1)。", 1,
                  "对。CPython 的 list 会预分配额外容量，尾部 append 均摊 O(1)；但在头部 insert(0, x) 是 O(n)。"),
        ],
    ),
    "py-tuple-set": used(
        "core/cache.py", "32",
        '_KEEP_POS = {"n", "nr", "ns", "nt", "nz", "v", "vd", "vn", "eng"}',
        "保留词性的白名单，用来过滤停用词；判断某个词性要不要留下时直接 `in` 查。",
        "这是 set 最典型的用法：只关心「在不在」，不关心顺序，也不允许重复。"
        "`in` 对 set 是哈希查找 O(1)，对 list 是逐个比对 O(n)——白名单一长，差别就出来了。"
        "而检索结果 `(text, source, score)` 用 tuple 返回，是因为一条结果不该被调用方偷偷改掉，"
        "元组不可变正好表达这个契约，还能直接 `text, source, score = item` 解包。",
        [
            choice("判断 `x in 容器` 时，容器选 set 而不是 list 的关键原因是？",
                   ["set 能保持顺序", "set 是哈希查找，平均 O(1)", "set 占内存更少", "list 不能存字符串"],
                   1, "set 靠哈希表定位元素，平均 O(1)；list 要逐个比较，O(n)。"),
            judge("元组一旦创建就不能修改其中的元素，所以更适合表达「一条不该被改的记录」。", 1,
                  "对。但要注意「不可变」只到第一层：元组里如果放了 list，那个 list 的内容仍然可以改。"),
        ],
    ),
    "py-dict": used(
        "core/llm_client.py", "29-44",
        '_USAGE = {"calls": 0, "prompt_tokens": 0, "cached_tokens": 0}\n...\nd["hit_rate"] = round(100.0 * (d.get("cached_tokens") or 0) / pt, 2) if pt else 0.0',
        "进程内累计大模型调用次数与 token 用量，供统计接口读取。",
        "字典是哈希表，按键取值平均 O(1)，所以「计数器」这类场景天然适合 dict。"
        "`d.get(\"cached_tokens\")` 而不是 `d[\"cached_tokens\"]`：键不存在时 get 返回 None，"
        "下标访问会直接 KeyError。配合 `or 0` 就把 None 兜成了 0。"
        "注意 `_USAGE[\"calls\"] += 1` 是**就地修改**这个可变字典，不需要写 global——只有给名字重新赋值才需要。",
        [
            choice("`d.get(\"k\")` 和 `d[\"k\"]` 的区别是什么？",
                   ["完全一样", "键不存在时 get 返回 None，下标访问抛 KeyError", "get 会创建键", "下标访问更快所以永远该用它"],
                   1, "get 提供默认值兜底，读配置/统计这类「键可能没有」的场景更安全；下标访问适合确定存在的键，出错早暴露。"),
            judge("在函数里执行 `_USAGE[\"calls\"] += 1` 之前必须写 global _USAGE，否则报错。", 0,
                  "错。这里改的是字典的内容，不是把 _USAGE 这个全局名字重新绑定，所以不需要 global。只有 `_USAGE = ...` 这种赋值才需要。"),
        ],
    ),
    "py-func": used(
        "core/cache.py", "205-208",
        'def get_cached_answer(self, question: str, profile_note: str = "") -> str:\n    """获取缓存的答案文本（命中时刷新TTL）；只关心文本的调用方用它即可"""\n    entry = self.get_cached_entry(question, profile_note)\n    return entry.get("answer") if entry else None',
        "缓存读取的薄封装：内部拿完整条目，对外只返回答案文本。",
        "这个函数只做两件事：转调、取字段。它的价值在于**降低调用方的认知负担**——"
        "只想拿文本的地方不用关心缓存条目的结构。`profile_note: str = \"\"` 用了默认值，"
        "所以 `get_cached_answer(\"怎么退票\")` 和 `get_cached_answer(\"怎么退票\", \"\")` 等价。"
        "注意默认值只在函数定义时求值一次，千万别写 `def f(x=[])`。",
        [
            choice("`def f(x, memo=[])` 这种写法的问题是什么？",
                   ["语法错误", "所有调用共享同一个列表，数据会串", "每次调用都新建列表", "不能传第二个参数"],
                   1, "默认值在函数定义时创建一次，被所有调用共享。要可变默认值请写 None，进函数再 `if memo is None: memo = []`。"),
            judge("`def f(x, y=\"\")` 里的默认值表达式在每次调用时都会重新求值。", 0,
                  "错。默认值只在 def 执行时求值一次，之后固定复用。这也是可变默认值出问题的根源。"),
        ],
    ),
    "py-none": used(
        "database/db_mysql.py", "170-173",
        "def _row_to_dict(row) -> Optional[Dict]:\n    if row is None:\n        return None\n    return dict(row)",
        "按条件查一条记录，查不到时游标返回 None，必须先判断再取字段。",
        "查库结果有三种可能：有数据、没数据（None）、报错。不判断就直接 `row[0]` 会得到 `TypeError: 'NoneType' object is not subscriptable`。"
        "这里必须用 `is None`，不能写 `if not row`——因为如果 row 是一个空元组或空字典，`not row` 也为真，"
        "那就把「查到了但内容为空」误判成「没查到」。",
        [
            choice("判断数据库查询结果是否为空，为什么推荐 `is None` 而不是 `not row`？",
                   ["is None 更快", "not row 会把空元组/空字典也当成没查到", "两者完全等价", "is None 能防止 SQL 注入"],
                   1, "not row 依赖布尔值，空容器同样是假值。is None 只认「真的没有这个对象」，语义更精确。"),
            judge("`0 == None` 的结果是 True。", 0,
                  "错。0 == None 是 False。0 是有效值，这正是为什么判断「有没有值」不能用真值判断。"),
        ],
    ),
    "py-lambda": used(
        "core/bm25_index.py", "124",
        "top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]",
        "BM25 给每个文档打完分后，按下标排序取分数最高的 top_k 个。",
        "`key=lambda i: scores[i]` 里的 i 是 range 产生的**下标**，lambda 返回的是「这个下标的排序依据」——"
        "也就是分数本身，不是 True/False。key 只负责给出依据，升降序由 reverse 控制。"
        "排序对象是下标而不是分数，是为了排完还能回到原文档（分数可能有重复，直接排分数会丢位置）。"
        "同一门课刚做的动手题就是它的简化版：多级排序时把 key 换成元组。",
        [
            choice("`sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)` 排完之后，列表里装的是什么？",
                   ["排好序的分数", "排好序的下标", "排好序的文档正文", "(下标, 分数) 元组"],
                   1, "排序对象是 range 生成的下标，key 只是决定比较依据。所以结果是一串下标，用它再回查原列表。"),
            judge("key 函数需要返回 True/False 来表示谁排在前面。", 0,
                  "错。key 返回的是排序依据（任何可比较的值，如数字、字符串、元组），比较规则由 sorted 内部完成。"),
        ],
    ),
    "py-iterate": used(
        "core/reranker.py", "59-68",
        "pairs = [[query, (doc[0][:max_chars] if max_chars and max_chars > 0 else doc[0])]\n         for doc in docs]\nscores = [float(s) for s in self.model.predict(pairs)]\n...\nsorted_docs = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)",
        "把「文档」和「相关性分数」两个平行列表用 zip 配对，再按分数排序。",
        "zip 把两个可迭代对象按位置粘成 `(doc, score)`，配合 `key=lambda x: x[1]` 就能按分数排序；"
        "解包时 `x[0]` 是文档、`x[1]` 是分数，下标写错就会按文档内容排序，结果全乱。"
        "zip 以**最短的那个**为准：如果 scores 比 docs 少一个，最后一个文档会被静默丢掉，不报错——"
        "这是 zip 最隐蔽的坑，所以要保证两个列表确实等长。",
        [
            choice("zip([1,2,3], [\"a\",\"b\"]) 得到什么？",
                   ["[(1,'a'), (2,'b'), (3, None)]", "[(1,'a'), (2,'b')]", "报错", "[(1,2,3), ('a','b')]"],
                   1, "zip 以最短为准，多余的 3 被丢弃，不报错。所以配平长度是调用方的责任。"),
            judge("要同时遍历两个等长列表，`for a, b in zip(xs, ys)` 比按下标遍历更安全。", 1,
                  "对。zip 直接给出配对，不会写下标写错；但要注意它会在最短处静默截断，需要严格校验时用 zip(strict=True)（Python 3.10+）。"),
        ],
    ),
    "py-scope": used(
        "core/llm_client.py", "42-44",
        "d = dict(_USAGE)\npt = d.get(\"prompt_tokens\") or 0\nd[\"hit_rate\"] = round(100.0 * (d.get(\"cached_tokens\") or 0) / pt, 2) if pt else 0.0",
        "返回统计前先复制一份，避免把 hit_rate 写进全局的那个字典。",
        "`dict(_USAGE)` 是**浅拷贝**：新建一个字典，键值照抄一遍。这样 `d[\"hit_rate\"] = ...` 只改副本，"
        "全局 `_USAGE` 保持干净。这里用浅拷贝就够了，因为值是 int，不可变；"
        "如果值本身是 list 或 dict，浅拷贝只复制引用，改内层仍会连带改到原对象，那就得 `copy.deepcopy`。",
        [
            choice("`d = dict(_USAGE)` 属于哪种拷贝？",
                   ["深拷贝", "浅拷贝", "引用赋值", "视图"], 1,
                   "dict(x) 新建外层容器、复制键值引用，是浅拷贝。嵌套的可变对象仍然共享。"),
            judge("对浅拷贝出来的字典修改内层列表，原字典里的那个列表也会变。", 1,
                  "对。浅拷贝只复制第一层容器，内层对象是同一份引用。需要完全独立就用 copy.deepcopy。"),
        ],
    ),
    "py-comprehension": used(
        "core/bm25_index.py", "59",
        "tokens = [t.strip() for t in tokens if t.strip() and len(t.strip()) >= 1]",
        "分词之后过滤掉空白 token，顺便去掉首尾空格。",
        "推导式的顺序是「先写结果表达式，再写 for，最后写 if」，和普通 for 循环的书写顺序相反，"
        "新手常把 if 写在 for 前面导致语法错误。这里 `if t.strip()` 既过滤空串也过滤纯空白。"
        "注意 `t.strip()` 被算了三次——推导式里没法赋值，真要优化得用生成器表达式配 walrus（`:=`）。",
        [
            choice("把 `[x*2 for x in xs if x > 0]` 改写成普通 for 循环，if 应该放在哪？",
                   ["for 之前", "for 之后（循环体内）", "循环之外", "不能改写"],
                   1, "推导式的 for 相当于外层循环，if 是循环体内的过滤条件。"),
            judge("列表推导式一定比等价的 for + append 快。", 1,
                  "对。推导式在 CPython 里有专门的字节码路径，省掉了反复调用 append 的开销，通常快 20%~30%。"),
        ],
    ),
    "py-func-adv": used(
        "core/llm_client.py", "135-145",
        "def create_with_thinking_switch(*args, **kwargs):\n    ...\n    resp = original(*args, **kwargs)",
        "给底层客户端套一层：默认关掉「思考模式」，需要时再打开，其他参数原样透传。",
        "`*args` 收位置参数成 tuple，`**kwargs` 收关键字参数成 dict；调用时再 `original(*args, **kwargs)` 把它们摊开——"
        "一收一放，包装函数就不用逐个复述原函数的签名。这是写中间件/装饰器的基础套路。"
        "代价是可读性：签名变成「什么都收」，IDE 提示不出具体参数，所以只在包装场景用，业务函数别这么写。",
        [
            choice("在函数内部，`kwargs` 是什么类型？",
                   ["tuple", "dict", "list", "set"], 1,
                   "**kwargs 收集关键字参数成 dict；*args 收集位置参数成 tuple。"),
            judge("`def f(*args, **kwargs)` 之后，调用 f(1, 2, a=3) 得到的 args 是 (1, 2)、kwargs 是 {'a': 3}。", 1,
                  "对。位置参数全进 args（元组），关键字参数全进 kwargs（字典）。"),
        ],
    ),
    "py-exception": used(
        "core/llm_client.py", "54-58",
        "try:\n    if stream:\n        return\n    u = getattr(resp, \"usage\", None)\n    if u is None:\n        return",
        "记录 token 用量时把整段逻辑包进 try，取不到 usage 就静默跳过。",
        "这里的 except 是**故意静默**的：统计只是旁路，不能因为它出错就让用户的问答失败。"
        "但要看清它捕获的范围——只包住了「读 usage、累加统计」这几行，没有把业务调用一起包进去。"
        "反例是 `except: pass` 包住整个函数：真出 bug 时你连日志都看不到，这是最难查的一类问题。",
        [
            choice("把整个业务函数用 `except: pass` 包起来，最大的风险是什么？",
                   ["运行变慢", "真实错误被吞掉，出问题完全没线索", "内存泄漏", "无法返回值"],
                   1, "静默吞异常等于把报错误导成「功能不好用」。捕获范围要尽量小，并且至少记一条日志。"),
            judge("捕获异常的 try 块范围越大越安全。", 0,
                  "错。范围越大越容易把不相干的错误一起吞掉。原则是「只包住真正可能出错且能处理的那几行」。"),
        ],
    ),
    "py-class": used(
        "core/async_tasks.py", "23-24",
        "@dataclass\nclass AsyncTask:",
        "后台任务的载体：一个任务一条记录，装着任务号、状态、结果和创建时间。",
        "类把「数据」和「操作」绑在一起，这里还用了 `@dataclass` 自动生成 `__init__`、`__repr__`，"
        "省掉一堆样板代码。相比裸 dict，类的优势是字段名固定、有类型提示、能挂方法（如 `to_dict`）。"
        "判断要不要建类：如果这堆数据总是和同一组操作一起出现，就该建类；只是临时传参，用 dict 更轻。",
        [
            choice("@dataclass 装饰器主要帮你自动生成什么？",
                   ["__init__ 和 __repr__ 等方法", "数据库表结构", "线程池", "JSON 序列化"],
                   0, "dataclass 根据字段声明生成 __init__、__repr__、__eq__，省掉手写样板代码。"),
            judge("用 class 表示一条数据，比用 dict 更容易在字段名写错时报错。", 1,
                  "对。属性名拼错会 AttributeError，dict 的键拼错往往只是静默取到默认值，错误暴露得更晚。"),
        ],
    ),
    "py-generator": used(
        "core/llm_client.py", "231-233",
        "for chunk in stream:\n    if chunk.choices and chunk.choices[0].delta.content:\n        yield chunk.choices[0].delta.content",
        "大模型流式返回时，每收到一个 token 就往上抛一个，前端因此能边生成边显示。",
        "用 `yield` 的函数调用时不执行函数体，只返回一个生成器；每次 `next()` 才跑到下一个 yield 并**暂停在那里**。"
        "好处是内存不随回答长度增长——不会先把整段回答攒在列表里再发；"
        "同时首字延迟从「等全文生成完」降到「第一个 token 到达」。这也解释了为什么流式接口要用生成器而不是 return。",
        [
            choice("调用一个含 yield 的函数，函数体会在什么时候执行？",
                   ["立刻执行完", "调用时完全不执行，第一次取值才跑到第一个 yield", "import 时执行", "yield 之后才执行"],
                   1, "含 yield 的函数返回生成器对象，函数体要等 next()/for 迭代时才真正开始跑，并且每次停在 yield 处。"),
            judge("把流式返回的每个 token 先 append 到列表里，等全部结束后再统一返回，内存占用和流式一样。", 0,
                  "错。攒列表意味着内存随回答长度线性增长，而且首字延迟变成「全文生成完」，流式的两个好处都没了。"),
        ],
    ),
    "py-decorator": used(
        "api/lost_found.py", "221",
        '@admin_router.post("/items", summary="商家登记失物（名称 + 照片，时间自动生成）")\nasync def merchant_add_lost(',
        "用装饰器把一个普通 async 函数注册成 HTTP 接口。",
        "装饰器的本质是「接收函数、返回函数」的高阶函数，`@admin_router.post(...)` 是「带参数的装饰器」——"
        "先执行 `post(...)` 得到一个装饰器，再拿它去装 `merchant_add_lost`。"
        "FastAPI 靠这个时机把路径、参数类型、依赖关系收集到路由表里，所以函数一注册就能被访问。"
        "老实说：项目里**没有自己手写装饰器**（全项目 0 处 `@wraps`），用到的都是框架提供的，"
        "知道原理即可，真要自己写请记得用 functools.wraps 保留原函数名。",
        [
            choice("`@app.get(\"/x\")` 这种写法，被装饰的函数最终会变成什么？",
                   ["原函数本身", "装饰器返回的新对象（通常是包装后的函数）", "一个字符串", "一个类"],
                   1, "装饰器返回值会替换掉原名字。框架通常返回包装函数，并在包装时登记路由信息。"),
            judge("自己写装饰器时不加 functools.wraps，会导致被装饰函数的名字变成 wrapper。", 1,
                  "对。wraps 会把原函数的 __name__、__doc__ 复制到包装函数上，否则日志和调试里全是 wrapper。"),
        ],
    ),
    "py-module": used(
        "core/cache.py", "15-17",
        "from core.keywords import ensure_business_words, BUSINESS_WORDS_SET\n\nensure_business_words()",
        "缓存模块导入时，顺手把业务词典注册到 jieba 里，保证分词结果和 BM25 那边一致。",
        "`from core.keywords import ...` 是绝对导入：从项目根目录开始算路径，不依赖当前文件在哪一层，"
        "比 `from ..keywords import ...` 更稳。模块级的那行 `ensure_business_words()` 会在**第一次 import 时执行一次**，"
        "之后再 import 不会重复执行（模块有缓存），所以这个注册天然是幂等的。"
        "这也是「模块导入有副作用」的典型例子——方便，但要小心循环导入。",
        [
            choice("同一个模块被 import 两次，模块顶层代码会执行几次？",
                   ["两次", "一次（之后走缓存）", "零次", "看 Python 版本"],
                   1, "模块第一次导入后缓存在 sys.modules，后续 import 直接取缓存，顶层语句不会重复执行。"),
            judge("在大型项目里，模块顶层写耗时逻辑（如读大文件、连数据库）是好习惯。", 0,
                  "错。导入会变慢，而且一旦失败整个 import 链都崩。耗时初始化应延迟到真正用到时（惰性初始化）。"),
        ],
    ),
    "py-file": used(
        "core/bm25_index.py", "87-94",
        'tmp_path = _PERSIST_PATH + ".tmp"\nwith open(tmp_path, "wb") as f:\n    pickle.dump(\n        {"corpus": self._corpus, "sources": self._sources,\n         "tokenized": self._tokenized},\n        f, protocol=pickle.HIGHEST_PROTOCOL\n    )\nos.replace(tmp_path, _PERSIST_PATH)',
        "把 BM25 索引写到磁盘，下次启动直接加载，省掉重新分词的时间。",
        "`with open(...)` 保证文件句柄一定关闭，异常路径也不例外——比手写 try/finally 干净。"
        "`\"wb\"` 是二进制写模式，因为 pickle 产出的是字节流，用文本模式会破坏数据。"
        "更关键的是那个 `.tmp`：先写临时文件，写完整了再 `os.replace` 覆盖正式文件。"
        "如果直接往正式文件写，写到一半进程被杀，留下的就是一个损坏的索引，下次启动直接读崩。",
        [
            choice("写文件时先写 .tmp 再 os.replace，主要解决什么问题？",
                   ["提高写入速度", "避免写到一半崩溃留下损坏的正式文件", "节省磁盘空间", "让文件自动加密"],
                   1, "这是原子写：replace 在同一文件系统内是原子操作，要么旧文件、要么完整新文件，不会出现半截文件。"),
            judge("`with open(...) as f` 在代码块内抛异常时，文件也会被正确关闭。", 1,
                  "对。with 走的是上下文管理器的 __exit__，异常路径同样会关闭文件。"),
        ],
    ),
    "py-oop": used(
        "api/admin.py", "207",
        "class CardUpsertRequest(_BaseModel):",
        "后台「新增/修改卡种」接口的请求体，继承 pydantic 的 BaseModel。",
        "继承让子类直接拿到父类的全部能力——这里继承 BaseModel 后，字段类型校验、缺失字段报错、"
        "多余字段处理全都不用自己写，子类只负责声明有哪些字段。"
        "这也是「继承是为了复用行为」而不是「为了复用字段」的典型：父类提供的是**校验机制**。"
        "如果只是想组合数据，优先用组合（一个对象持有另一个），继承只在「is-a」关系成立时用。",
        [
            choice("`class CardUpsertRequest(_BaseModel)` 继承 BaseModel 后，最直接的收益是什么？",
                   ["自动获得字段校验和类型转换", "自动生成数据库表", "自动写单元测试", "自动生成前端页面"],
                   0, "pydantic 的 BaseModel 在实例化时就按类型注解校验并转换，省掉手写一堆 if 判断。"),
            judge("只要两个类有相同的字段，就应该用继承来复用。", 0,
                  "错。字段相同不代表 is-a 关系成立。滥用继承会让耦合变紧，组合通常更灵活。"),
        ],
    ),
    "py-magic": used(
        "core/cache.py", "57-64",
        "_instance = None\n...\ndef __new__(cls):\n    if cls._instance is None:\n        with _lock:\n            if cls._instance is None:\n                cls._instance = super().__new__(cls)",
        "RedisCache 做成单例：全进程只建一个连接对象，避免每次请求都重新连 Redis。",
        "`__new__` 负责**创建**对象，`__init__` 负责**初始化**；拦在 `__new__` 里返回同一个实例，就实现了单例。"
        "两次 `if cls._instance is None` 是双重检查锁：外层判断避免每次都抢锁（性能），内层判断防止两个线程同时通过外层检查后各建一个。"
        "`@property` 也在这份代码里被大量使用（15 处），本质是把方法伪装成属性，让 `obj.available` 这种读取能在背后做惰性连接。",
        [
            choice("单例里写两次 `if cls._instance is None` 的目的是什么？",
                   ["代码好看", "外层省掉重复抢锁，内层防止并发时创建出两个实例", "兼容 Python 2", "防止内存泄漏"],
                   1, "这就是双重检查锁：外层的存在是为了性能（大多数时候实例已存在，不必进锁），内层才是正确性保证。"),
            judge("`__init__` 在对象创建后调用，每次实例化都会执行；`__new__` 负责真正创建对象。", 1,
                  "对。所以单例要拦 __new__，只拦 __init__ 是拦不住的——对象已经造出来了。"),
        ],
    ),
    "py-abc": absent(
        "class TaskStatus(str, Enum):\n    PENDING = \"pending\"\n    RUNNING = \"running\"\n    ...",
        "项目里没有任何抽象基类（全项目 0 处 `abc` / `abstractmethod`）。接口约束靠 pydantic 模型、Enum 和鸭子类型。",
        "抽象基类的价值是「强制子类实现某个方法」，在多人协作、插件式扩展时很有用。"
        "这个项目规模不大、扩展点少，用 `str, Enum` 限定取值、用 pydantic 限定请求结构就够了，"
        "引入 abc 只会多一层样板。反过来说：如果你在设计一个「必须由别人实现 3 个方法」的框架接口，"
        "那就该用 `ABCMeta + @abstractmethod`，让漏实现的方法在**实例化时**就报错，而不是运行到一半才 AttributeError。",
        [
            choice("用抽象基类（ABC）声明 `@abstractmethod`，漏实现时什么时候报错？",
                   ["调用该方法时", "实例化子类时", "import 时", "永远不报错"],
                   1, "ABC 在实例化阶段就检查抽象方法是否都实现了，比运行到调用处才炸更早暴露问题。"),
            judge("项目里没有用 abc，说明 abc 没有价值。", 0,
                  "错。工具的价值取决于场景。小项目里鸭子类型足够；要强制契约、要做插件体系时 abc 才划算。"),
        ],
    ),
    "py-regex": used(
        "core/chat_memory.py", "310-311",
        't = re.sub(r"【来源文档】[^\\n]*", " ", t)\nt = re.sub(r"【来源】[^\\n]*", " ", t)',
        "生成追问建议前，把上一条回答里的「【来源文档】xxx」标记清掉，避免带着引用去问下一轮。",
        "`[^\\n]*` 的意思是「除换行以外的任意字符，重复 0 次或多次」——它一直吃到行尾就停，不会越过换行。"
        "如果写成 `.*`，默认不匹配换行所以结果相同，但显式写 `[^\\n]` 意图更清楚。"
        "`re.sub` 默认替换**所有**匹配，要只换第一个得传 `count=1`。"
        "另外：正则里的括号、点号、星号都是特殊字符，字面量匹配要用 `re.escape()` 转义。",
        [
            choice("正则 `[^\\n]*` 匹配的是什么？",
                   ["任意字符直到字符串结尾（含换行）", "除换行外的字符，直到行尾", "只有字母", "一个空行"],
                   1, "字符类里的 ^ 表示取反，[^\\n] 就是「不是换行的任意字符」，* 让它连续吃掉整行剩余内容。"),
            judge("`re.sub` 默认只替换第一个匹配。", 0,
                  "错。默认替换全部匹配，只换第一个要显式传 count=1。写清理逻辑时搞反会留下大量残留。"),
        ],
    ),
    "py-stdlib": used(
        "bench_eval.py", "9",
        "from collections import defaultdict",
        "评测脚本按「意图」分组统计指标，用 defaultdict 省掉「键不存在先建空列表」的判断。",
        "`defaultdict(list)` 在访问不存在的键时会自动建一个空 list，所以 `groups[intent].append(x)` 可以直接写，"
        "不用先 `if intent not in groups: groups[intent] = []`。这是 collections 里最常用的一个。"
        "但要说清楚：全项目 **0 处 `itertools`、0 处 `functools`**——说明这两个模块不是必需品，"
        "别为了「显得专业」硬套 `functools.lru_cache`，缓存该交给 Redis 做，进程内缓存多进程部署时会不一致。",
        [
            choice("`defaultdict(list)` 相比普通 dict，最直接的好处是？",
                   ["自动排序", "访问不存在的键时自动建空列表，不用先判断", "线程安全", "省内存"],
                   1, "它给缺失的键提供了一个默认工厂（list），所以可以直接 append 而不会 KeyError。"),
            judge("`functools.lru_cache` 可以直接替代 Redis 做多进程部署下的缓存。", 0,
                  "错。lru_cache 是进程内缓存，多进程/多实例部署各存一份，会出现「A 写入了 B 读不到」的一致性问题。"),
        ],
    ),
    "py-context": used(
        "core/bm25_index.py", "116-117",
        "with _lock:\n    if self._index is None or not self._corpus:\n        return []",
        "检索前先拿锁，防止「索引正在重建」时读到半成品。",
        "`with` 走的是上下文管理器协议：进入时调 `__enter__`（加锁），退出时**无论如何**都调 `__exit__`（释放锁），"
        "包括 return、break、抛异常这些路径。手写 `lock.acquire(); ...; lock.release()` 一旦中间抛异常就永久死锁，"
        "所以加锁永远用 with。自己写上下文管理器有两种方式：类实现 `__enter__`/`__exit__`，或者用 `@contextmanager` 装饰生成器。",
        [
            choice("用 `with lock:` 而不是手动 acquire/release，最关键的原因是？",
                   ["写起来短", "无论正常返回还是抛异常都保证释放锁", "性能更好", "支持多线程共享"],
                   1, "with 把释放放在 __exit__ 里，异常路径也会执行，避免死锁。"),
            judge("用 @contextmanager 装饰一个生成器函数，也能做出上下文管理器。", 1,
                  "对。yield 之前是 __enter__ 的逻辑，yield 之后是 __exit__ 的逻辑，异常会抛到 yield 处。"),
        ],
    ),
    "py-concurrency": used(
        "core/async_tasks.py", "57-66",
        "cls._instance._queue = queue.Queue()\n...\nself._worker = threading.Thread(target=self._process_queue, daemon=True)\nself._worker.start()",
        "文档解析这类慢任务丢进队列，由一个后台线程慢慢消费，接口立刻返回任务号。",
        "`queue.Queue` 内部自带锁，多线程 put/get 不会丢数据，比自己维护 list + 锁安全。"
        "`daemon=True` 让这个线程随主进程退出，否则关服务时会卡住等它跑完。"
        "为什么选线程而不是进程：这类任务大部分时间在等 IO（读文件、调模型），GIL 在等 IO 时会释放，"
        "所以线程够用。真正的 CPU 密集计算（比如大批量向量化）才需要 `ProcessPoolExecutor` 绕开 GIL。",
        [
            choice("后台任务主要是等网络/磁盘 IO 时，为什么用线程就够？",
                   ["线程比进程快", "等 IO 时 GIL 会释放，线程能并发", "线程不受 GIL 限制", "进程不能等待 IO"],
                   1, "GIL 只在执行 Python 字节码时独占，IO 等待期间会释放，所以 IO 密集用线程是有收益的。"),
            judge("创建线程时设置 daemon=True，主程序退出时这个线程会被强制结束，不会阻塞退出。", 1,
                  "对。非守护线程会阻止进程退出，后台轮询这类线程都应该设成 daemon。"),
        ],
    ),
}
