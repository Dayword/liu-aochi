"""科目：RAG 检索工程（第二批 · 4 课）。

承接 `learn_rag.py`：那边讲完「怎么切、怎么分词、怎么打分、怎么融合、怎么精排」，
这边补向量侧和工程侧 —— 文本怎么变成向量、向量存在哪、文档怎么入库、重复内容怎么处理。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）
"""

EMBEDDING_CHECKER = """
try:
    v = normalize([3, 4])
    assert abs(v[0] - 0.6) < 1e-9 and abs(v[1] - 0.8) < 1e-9, "3-4-5 直角三角形：[3,4] 归一化后应该是 [0.6, 0.8]，现在是 %r" % (v,)
    assert normalize([0, 0]) == [0, 0], "零向量没有方向，原样返回，不能除零"
    assert normalize([1]) == [1], "一维向量归一化后就是 1.0"
    assert abs(sum(x * x for x in normalize([2, 3, 6])) - 1.0) < 1e-9, "归一化后模长必须为 1"

    m = [[3, 4], [0.6, 0.8], [0, 1]]
    r = top_k_by_ip([1, 0], m, 2)
    assert len(r) == 2, "top_k=2 就返回 2 条"
    assert r[0][0] == 0 and r[1][0] == 1, "前两条方向完全相同（都是 [0.6,0.8]），同分时要保持原顺序，现在是 %r" % (r,)
    assert abs(r[0][1] - 0.6) < 1e-9, "归一化后与 [1,0] 的内积应等于 0.6，现在是 %.6f" % r[0][1]
    assert abs(r[1][1] - 0.6) < 1e-9, "长向量 [3,4] 和短向量 [0.6,0.8] 归一化后分数必须相同 —— 这就是归一化的意义"

    r2 = top_k_by_ip([1, 0], m, 10)
    assert len(r2) == 3, "top_k 超过向量条数时返回全部 3 条"
    assert abs(r2[2][1]) < 1e-9, "第三条 [0,1] 与 [1,0] 正交，分数应为 0"
    assert top_k_by_ip([1, 0], [], 3) == [], "空向量库返回空列表"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError, ZeroDivisionError) as e:
    print("__FAIL__ 参数或计算出错（零向量要单独处理）：" + str(e))
"""

VECTORDB_CHECKER = """
try:
    s = MiniVectorStore()
    assert s.search([1, 0], top_k=3) == [], "空库检索要返回空列表"
    s.add("a", [1, 0], {"cat": "票"})
    s.add("b", [0, 1], {"cat": "票"})
    s.add("c", [2, 0], {"cat": "路"})

    r = s.search([1, 0], top_k=2)
    assert r == [("c", 2), ("a", 1)], "按内积排序：c 得 2 分排第一，a 得 1 分第二，现在是 %r" % (r,)
    r2 = s.search([1, 0], top_k=10)
    assert len(r2) == 3, "top_k 超过条数时返回全部"
    assert r2[2] == ("b", 0), "正交向量得 0 分，排在最后"

    r3 = s.search([1, 0], top_k=10, where={"cat": "票"})
    assert r3 == [("a", 1), ("b", 0)], "where 要只保留 cat=='票' 的两条，现在是 %r" % (r3,)
    r4 = s.search([1, 0], where={"cat": "不存在"})
    assert r4 == [], "过滤后没有匹配项时返回空列表，不能退回成不过滤"

    s.add("a", [9, 9], {"cat": "票"})
    r5 = s.search([0, 1], top_k=10, where={"cat": "票"})
    assert ("a", 9) in r5, "同一个 id 再次 add 要覆盖旧记录（不是追加），现在 a 的分数应该是 9，实际 %r" % (r5,)
    assert len([x for x in r5 if x[0] == "a"]) == 1, "同一个 id 不能出现两次，说明 add 没有去重"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, ValueError) as e:
    print("__FAIL__ 参数或数据结构不对：" + str(e))
"""

INGEST_CHECKER = """
try:
    existing = {"doc-a": "h1", "doc-b": "h2", "doc-c": "h3"}
    incoming = {"doc-a": "h1", "doc-b": "h2-new", "doc-d": "h4"}
    add, upd, skip = plan_ingest(existing, incoming)
    assert add == ["doc-d"], "doc-d 是新文档，应进新增列表，现在是 %r" % (add,)
    assert upd == ["doc-b"], "doc-b 的指纹变了，应进更新列表，现在是 %r" % (upd,)
    assert skip == ["doc-a"], "doc-a 指纹没变，应跳过（这正是增量更新省下来的工作量），现在是 %r" % (skip,)

    add2, upd2, skip2 = plan_ingest({}, {"x": "h"})
    assert add2 == ["x"] and upd2 == [] and skip2 == [], "空库时所有文档都是新增"

    add3, upd3, skip3 = plan_ingest({"x": "h"}, {})
    assert add3 == [] and upd3 == [] and skip3 == [], "没有新文件时什么都不用做，尤其不能返回需要删除的指令"

    add4, upd4, skip4 = plan_ingest({"x": "h1"}, {"x": "h1"})
    assert skip4 == ["x"] and add4 == [] and upd4 == [], "指纹相同必须跳过，否则每次全量重跑都在重复编码"

    add5, upd5, skip5 = plan_ingest({"x": "h1", "y": "h2"}, {"y": "h2", "x": "h9", "z": "h3"})
    assert upd5 == ["x"], "只有 x 的指纹变了"
    assert add5 == ["z"], "只有 z 是新的"
    assert skip5 == ["y"], "y 没变"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError, AttributeError) as e:
    print("__FAIL__ 返回结构不对（约定返回三元组 add/update/skip）：" + str(e))
"""

DEDUP_CHECKER = """
try:
    items = [
        {"id": "a", "vec": [1, 0]},
        {"id": "b", "vec": [1, 0]},
        {"id": "c", "vec": [0, 1]},
        {"id": "d", "vec": [0.9, 0.1]},
    ]
    assert dedup_by_similarity(items, 0.95) == ["a", "c"], "b 与 a 完全相同要丢弃；d 与 a 的余弦约 0.9939 也超过 0.95 要丢弃；c 方向垂直要保留"
    assert dedup_by_similarity(items, 1.01) == ["a", "b", "c", "d"], "阈值大于 1 时没有谁算重复，应全部保留（判定是严格大于）"
    assert dedup_by_similarity([], 0.9) == [], "空列表返回空列表"
    assert dedup_by_similarity([{"id": "x", "vec": [1, 1]}], 0.9) == ["x"], "只有一条时直接保留，不要和自己比"
    assert cosine([0, 0], [1, 1]) == 0.0, "零向量没有方向，相似度约定为 0.0，不能除零"
    assert abs(cosine([1, 0], [0, 1])) < 1e-9, "垂直向量余弦为 0"
    assert abs(cosine([1, 0], [3, 0]) - 1.0) < 1e-9, "同方向不同长度余弦仍是 1（余弦只看方向）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, ZeroDivisionError) as e:
    print("__FAIL__ 参数或数据结构不对：" + str(e))
"""

LESSONS = [
    {
        "code": "rag-embedding",
        "subject": "RAG 检索工程",
        "stage": "融合与精排",
        "runner": "python",
        "title": "Embedding 模型与向量归一化",
        "summary": "文本怎么变成向量，以及为什么必须归一化",
        "definition": """**Embedding = 把一段文本映射成固定长度的浮点向量，让「语义相近」变成「向量距离近」。**

一次完整的向量化链路：

```
文本 → tokenizer 切 token → 模型前向 → 池化（[CLS] 或 mean）→ L2 归一化 → 向量
```

**模型选型看四个维度**：

- **语言**：中文场景别用纯英文模型（`all-MiniLM-L6-v2` 对中文几乎是噪声）。BGE-M3 是中英多语言里性价比很高的一档。
- **维度**：常见 768 / 1024。维度越高表达力越强，但存储和检索成本线性上涨——10 万条 × 1024 维 × 4 字节 ≈ 400MB。
- **最大长度**：模型有 token 上限（BGE-M3 是 8192），超长会被静默截断。这也是 chunk_size 不能设太大的另一个原因。
- **对称 vs 非对称**：部分模型区分「查询侧」和「文档侧」的编码方式（query instruction），用错会明显掉分。

**为什么一定要归一化**：归一化后向量模长为 1，此时**内积就等于余弦相似度**。不归一化的话，模长大的向量内积天然更大——长文本会被无关查询顶到前面。这不是理论洁癖，是实打实的排序 bug。

**归一化要在写入时做，不是查询时做**。库里的向量和查询向量必须用同一套规则，否则度量方式就对不上。所以项目的 `encode_kwargs={"normalize_embeddings": True}` 是在编码阶段统一处理。

**项目落点**：`core/embedding.py` 的 `EmbeddingEngine`（单例）用 `HuggingFaceEmbeddings`，`EMBEDDING_DIM` 与 Milvus collection 的 `dim` 必须严格一致，改模型就要重建集合。""",
        "plain": """把每句话压缩成一串数字，意思越像，数字串的方向越接近。

但有个坑：**长短不同的两段话，数字串的「长度」也不一样**。就像两支箭头指向同一个方向，一支长 5 米、一支长 1 米。你要是比「箭头末端离原点多远」，长的那支永远赢——可它俩指的其实是同一个方向。

归一化就是把所有箭头都缩到 1 米长。这样比「末端位置」就等于比「方向」，才是真正的语义相似度。""",
        "example": """import math

a = [3.0, 4.0]
b = [0.6, 0.8]
q = [1.0, 0.0]

def ip(x, y):
    return sum(i * j for i, j in zip(x, y))

def norm(v):
    n = math.sqrt(sum(i * i for i in v))
    return [i / n for i in v]

print('a 模长:', round(math.sqrt(sum(i*i for i in a)), 2))
print('b 模长:', round(math.sqrt(sum(i*i for i in b)), 2))
print('未归一化 a·q =', ip(a, q))
print('未归一化 b·q =', ip(b, q))
print('归一化后 a·q =', round(ip(norm(a), norm(q)), 2))
print('归一化后 b·q =', round(ip(norm(b), norm(q)), 2))""",
        "example_output": """a 模长: 5.0
b 模长: 1.0
未归一化 a·q = 3.0
未归一化 b·q = 0.6
归一化后 a·q = 0.6
归一化后 b·q = 0.6""",
        "pitfalls": [
            "入库时不归一化、查询时归一化：两边规则不一致，内积算出来的分数毫无意义",
            "以为「维度越高越好」：768 提到 1024 只涨几个点召回，存储和检索成本却涨 33%",
            "忽略模型的最大长度：超长 chunk 被静默截断，后半段内容等于没入库",
            "换 embedding 模型却不重建索引：新旧向量不同空间，检索结果直接乱掉",
        ],
        "task": """请实现两个函数：

1. `normalize(vec)`：L2 归一化
   - 返回每个分量除以模长后的新列表
   - **零向量原样返回**（模长为 0，不能除零）

2. `top_k_by_ip(query, matrix, k=3)`：归一化内积检索
   - 把 `query` 和 `matrix` 的每一行都先归一化，再算内积
   - 返回 `[(行下标, 分数), ...]`，按分数从高到低，取前 `k` 条
   - 分数相同时保持原下标顺序（稳定排序）
   - `matrix` 为空返回 `[]`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """模长 `math.sqrt(sum(x*x for x in vec))`，先判 0 再除。检索时用 `enumerate(matrix)` 拿下标，攒成 `(i, score)` 后 `sort(key=lambda t: -t[1])`，切片取前 k。""",
        "checker": EMBEDDING_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "`encode_kwargs={\"normalize_embeddings\": True}` 的作用是什么？",
                "options": [
                    "把向量维度压缩到更低",
                    "把每个向量缩放到模长 1，使内积等价于余弦相似度",
                    "自动去掉文本里的停用词",
                    "让模型支持更长输入",
                ],
                "answer_index": 1,
                "explanation": "归一化只改模长不改方向。归一化后 `a·b = |a||b|cosθ = cosθ`，内积就是余弦，检索可以直接用最快的 IP 度量。",
            },
            {
                "type": "choice",
                "stem": "把向量维度从 768 提高到 1024，最直接的代价是什么？",
                "options": [
                    "检索结果一定变差",
                    "存储和检索计算量按比例上升",
                    "模型不再支持中文",
                    "必须改用 BM25",
                ],
                "answer_index": 1,
                "explanation": "向量条数 × 维度 × 每维字节数就是存储量。维度涨 33%，存储和距离计算都跟着涨，而召回提升往往有限。",
            },
            {
                "type": "judge",
                "stem": "向量没有归一化时，内积可以直接当作余弦相似度使用。",
                "answer": False,
                "explanation": "内积还乘上了两个向量的模长。只有模长都为 1 时，内积才等于余弦。不归一化会让长向量占便宜。",
            },
            {
                "type": "blank",
                "stem": "向量归一化之后，内积等于______相似度。",
                "answer": "余弦",
                "hint": "填两个字，就是那个「看方向不看长度」的相似度",
                "explanation": "余弦相似度 = 内积 / (|a||b|)。归一化后 |a|=|b|=1，分母为 1，内积就等于余弦。",
            },
        ],
    },
    {
        "code": "rag-vector-db",
        "subject": "RAG 检索工程",
        "stage": "融合与精排",
        "runner": "python",
        "title": "向量数据库 Milvus 与 ANN 索引",
        "summary": "为什么不能全库扫，nprobe 又牺牲了什么",
        "definition": """**向量数据库 = 专门为「高维向量最近邻检索」设计的存储，核心价值是别把全库扫一遍。**

暴力检索（FLAT）要算 query 和每一条的相似度，10 万条就是 10 万次乘加。向量库靠**近似最近邻（ANN）**把它降到亚线性：

| 索引 | 思路 | 特点 |
|---|---|---|
| FLAT | 不建索引，全量比对 | 100% 召回，最慢；小数据集够用 |
| IVF_FLAT | 先聚成 nlist 个桶，查询只搜最近的 nprobe 个桶 | 快，nprobe 小会漏召回 |
| HNSW | 多层图，逐层贪心下降 | 综合最优，内存占用高 |
| PQ / SQ | 量化压缩向量 | 省内存，有精度损失 |

**nprobe 是精度与延迟的旋钮**：`nprobe=1` 只搜一个桶，快但可能漏；`nprobe=nlist` 退化成全量扫描。这就是「近似」二字的来源——ANN 不保证 100% 召回。

**度量方式必须和归一化配套**：

- `IP`（内积）：向量已归一化时等价于余弦，最快
- `L2`（欧氏距离）：未归一化时用，注意**距离越小越相似**，排序方向和 IP 相反
- `COSINE`：库内部自己做归一化，多一次计算

**metadata 过滤的顺序有讲究**：`where cat == "票价"` 这类过滤，如果先 ANN 取 top_k 再过滤，可能 top_k 里大半被滤掉、结果不够数。要么先过滤后检索，要么把 `top_k` 放大到 `k * 3` 再滤。

**项目落点**：`core/vector_store.py` 用 pymilvus 建 `Collection`，schema 是 `id / vector / metadata`，检索走 IP 内积；`connections.connect()` 是懒加载单例，第一次真正用到才连，避免启动时 Milvus 没起来就整个服务挂掉。""",
        "plain": """在图书馆找一本书：

- **FLAT** = 把 10 万本书一本本翻一遍，肯定不漏，但慢得离谱
- **IVF** = 先把书按主题分到 100 个书架，找的时候只看「最像的 1 个书架」（nprobe=1）

问题来了：如果这本书被分到了隔壁书架，你就永远找不到——这就是「近似」的代价。nprobe 调到 2、3，多翻几个书架，漏的概率下降，但速度也慢下来。

没有一个 nprobe 能同时满足「绝对不漏」和「极快」，工程上只能按业务选。""",
        "example": """def ip(x, y):
    return sum(i * j for i, j in zip(x, y))

items = [('d1', [0.90, 0.10]), ('d2', [-0.90, 0.20]),
         ('d3', [0.00, 1.00]), ('d4', [0.80, -0.30])]
query = [0.10, 1.00]

bucket_a = [(k, round(ip(query, v), 2)) for k, v in items if v[0] > 0]
bucket_b = [(k, round(ip(query, v), 2)) for k, v in items if v[0] <= 0]

print('桶A:', sorted(bucket_a, key=lambda x: -x[1]))
print('桶B:', sorted(bucket_b, key=lambda x: -x[1]))
print('nprobe=1 返回:', max(bucket_a, key=lambda x: x[1]))
print('nprobe=2 返回:', max(bucket_a + bucket_b, key=lambda x: x[1]))""",
        "example_output": """桶A: [('d1', 0.19), ('d4', -0.22)]
桶B: [('d3', 1.0), ('d2', 0.11)]
nprobe=1 返回: ('d1', 0.19)
nprobe=2 返回: ('d3', 1.0)""",
        "pitfalls": [
            "nprobe 设成 1 就以为万事大吉：真正最相似的向量可能在没搜的桶里，召回率静默下降",
            "向量已归一化却用 L2 度量：内积和欧氏距离的排序不一致，明明对的排到后面",
            "先 ANN 取 top_k 再按 metadata 过滤：过滤后可能一条不剩，接口返回空",
            "同一个 id 重复 add 却变成追加：库里出现多条重复记录，白占 Top-K 名额",
        ],
        "task": """请实现一个极简向量库 `MiniVectorStore`：

1. `add(doc_id, vec, meta=None)`
   - 存入一条记录，metadata 是 dict
   - **同一个 doc_id 再次 add 要覆盖旧记录**，不能变成两条

2. `search(query, top_k=3, where=None)`
   - `where` 是 dict，形如 `{"cat": "票"}`，只保留 metadata 里**所有**键值都匹配的记录；`where=None` 表示不过滤
   - 对过滤后的记录算内积（不归一化，直接点积）
   - 返回 `[(doc_id, score), ...]`，按分数从高到低取前 `top_k`
   - 空库或过滤后无结果都返回 `[]`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """用一个列表存 `{"id","vec","meta"}`。`add` 时先看列表里有没有同 id，有就替换、没有就 append。`search` 里 `all(meta.get(k) == v for k, v in where.items())` 判断过滤。""",
        "checker": VECTORDB_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "把 nprobe 从 1 调大到 10，会发生什么？",
                "options": [
                    "召回率上升，但查询变慢",
                    "召回率下降，查询变快",
                    "存储空间变大",
                    "向量维度自动降低",
                ],
                "answer_index": 0,
                "explanation": "nprobe 是「搜几个桶」。搜得越多越不容易漏，但计算量也越大。存储和维度都不受影响。",
            },
            {
                "type": "choice",
                "stem": "向量已经做过 L2 归一化，检索时最适合用哪种度量？",
                "options": [
                    "IP（内积）",
                    "L2（欧氏距离）",
                    "Hamming 距离",
                    "Jaccard 相似度",
                ],
                "answer_index": 0,
                "explanation": "归一化后 `IP = cosθ`，一次乘加就够。L2 也能用（两者排序单调对应），但要多算平方和，没有必要。",
            },
            {
                "type": "judge",
                "stem": "使用 IVF、HNSW 这类 ANN 索引后，检索结果能保证 100% 召回。",
                "answer": False,
                "explanation": "ANN 是「近似」最近邻。IVF 可能漏掉别的桶里的最近邻，HNSW 的贪心也可能走进局部最优。要 100% 召回只能用 FLAT 全量扫。",
            },
            {
                "type": "blank",
                "stem": "补全 Milvus 的检索调用（用 ___ 表示要填的部分）：\\ncollection.___(data=[query_vec], anns_field=\"vector\", param=param, limit=5)",
                "answer": "search",
                "hint": "填一个英文单词，就是「检索」",
                "explanation": "pymilvus 的检索方法是 `collection.search(...)`；插入是 `insert`，删除是 `delete`。",
            },
        ],
    },
    {
        "code": "rag-ingest",
        "subject": "RAG 检索工程",
        "stage": "数据治理",
        "runner": "python",
        "title": "文档入库流水线与增量更新",
        "summary": "别每次都全量重建，指纹比对能省下 90% 的活",
        "definition": """**入库流水线 = 把「一堆原始文件」变成「向量库里可检索的 chunk」的完整流程。**

五个阶段，每一段都可能出错：

1. **抽取**：PDF（电子版直接抽文字，扫描件要 OCR）、Word（python-docx）、PPT、网页
2. **清洗**：去页眉页脚、去多余空白、修断行、统一全半角
3. **分块**：标题层级 + 递归切分 + overlap（见 `rag-chunk`）
4. **向量化**：批量 encode（批量比逐条快得多，GPU 更明显）
5. **入库**：写向量 + 原文 + metadata（来源文件、页码、章节）

**增量更新是工程重点**。全量重建是「清库 → 重新编码所有文档」，文档一多就要跑几十分钟，期间服务不可用。正确做法是给每篇文档算一个**内容指纹**（hash）：

- 指纹没变 → 跳过
- 指纹变了 → 删掉旧 chunk，重新入库
- 新文档 → 新增

**幂等**：同一篇文档重复入库不能产生重复 chunk。做法是「按 doc_id 先删后插」，而不是无脑 append。这样任务失败重试、消息重复投递都不会把库搞脏。

**异步化**：入库可能跑几分钟，绝不能放在 HTTP 请求里同步做。`core/async_tasks.py` 用线程 + 队列 + 状态机（PENDING / PROCESSING / COMPLETED / FAILED）把入库变成后台任务，接口立刻返回任务 id，前端轮询进度。

**失败要能重试，且重试是安全的**：因为幂等，重跑同一条任务只会覆盖同一批 chunk，不会翻倍。

**项目落点**：`data_pipeline.py` 负责抽取与分块，`rebuild_index.py` 是重建入口，`core/async_tasks.py` 管理异步任务状态。""",
        "plain": """给图书馆上架新书：

- 笨办法：每次来新书，把所有书搬下来重新贴一遍标签（全量重建）—— 来一本也要干一整天
- 聪明办法：每本书有个「版本号」。版本号没变的跳过，变了的只换那一本，新书直接上架（增量更新）

指纹就是版本号。文件内容一变，hash 就变；内容没变，hash 一模一样。""",
        "example": """existing = {'doc-a': 'h1', 'doc-b': 'h2', 'doc-c': 'h3'}
incoming = {'doc-a': 'h1', 'doc-b': 'h2-new', 'doc-d': 'h4'}

to_add, to_update, to_skip = [], [], []
for k, h in incoming.items():
    if k not in existing:
        to_add.append(k)
    elif existing[k] != h:
        to_update.append(k)
    else:
        to_skip.append(k)

print('新增:', to_add)
print('更新:', to_update)
print('跳过:', to_skip)
print('增量需编码:', len(to_add) + len(to_update))
print('全量需编码:', len(existing) + len(incoming))""",
        "example_output": """新增: ['doc-d']
更新: ['doc-b']
跳过: ['doc-a']
增量需编码: 2
全量需编码: 6""",
        "pitfalls": [
            "不做指纹比对，每次全量重编码：文档一多就要跑几十分钟，期间检索结果还是旧的",
            "入库用 append 而不是「先删后插」：任务重试一次，库里就多一整套重复 chunk",
            "把入库放在 HTTP 请求里同步执行：前端转圈几分钟，网关超时直接 504",
            "清洗阶段把换行全删掉：段落边界没了，后面的标题层级切分和递归切分全部失效",
        ],
        "task": """请实现 `plan_ingest(existing, incoming)`：

- `existing`：库里已有的 `{doc_id: hash}`（dict）
- `incoming`：这次要入库的 `{doc_id: hash}`（dict）
- 返回三元组 `(to_add, to_update, to_skip)`，每个都是 doc_id 的列表
  - 库里没有 → 进 `to_add`
  - 库里指纹不同 → 进 `to_update`
  - 指纹相同 → 进 `to_skip`
- 列表顺序跟随 `incoming` 的遍历顺序""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """遍历 `incoming.items()`，三个 if/elif/else 分支分别 append。注意判断顺序：先判「不在 existing 里」，再判「hash 不同」，否则新文档会掉进 update。""",
        "checker": INGEST_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "增量更新靠什么判断一篇文档需不需要重新入库？",
                "options": [
                    "文件名有没有变",
                    "文件大小和内容指纹（hash）有没有变",
                    "文件的上传时间",
                    "文档的 chunk 数量",
                ],
                "answer_index": 1,
                "explanation": "指纹是内容的摘要。文件名相同内容可能改过，大小相同也可能改了几个字，只有内容 hash 能准确反映「变了没有」。",
            },
            {
                "type": "choice",
                "stem": "为什么文档入库要做成异步任务？",
                "options": [
                    "因为 Python 不支持同步代码",
                    "入库耗时长，同步执行会让 HTTP 请求超时、服务不可用",
                    "异步能让向量维度变小",
                    "异步可以跳过清洗步骤",
                ],
                "answer_index": 1,
                "explanation": "抽取 + 分块 + 批量编码可能要几分钟。放在请求里会撑爆连接和网关超时，异步化后接口立即返回任务 id。",
            },
            {
                "type": "judge",
                "stem": "同一篇文档重复入库时，直接往向量库 append 新 chunk 是可以接受的。",
                "answer": False,
                "explanation": "会产生重复 chunk，挤占 Top-K 名额、放大同一段信息在 prompt 里的权重。必须「按 doc_id 先删后插」保证幂等。",
            },
            {
                "type": "blank",
                "stem": "「同一操作执行一次和执行多次，结果相同」这种性质叫______。",
                "answer": "幂等",
                "hint": "填两个字，英文是 idempotent",
                "explanation": "先删后插是入库实现幂等的标准手法：重试、重复投递都只会覆盖同一批数据，不会翻倍。",
            },
        ],
    },
    {
        "code": "rag-dedup",
        "subject": "RAG 检索工程",
        "stage": "数据治理",
        "runner": "python",
        "title": "知识库去重：哈希、归一化与语义阈值",
        "summary": "重复文档会挤占 Top-K，还会让模型误判重要性",
        "definition": """**知识库去重 = 在入库前或检索后，把「说的是同一件事」的内容合并掉。**

重复来源很现实：同一份 FAQ 被运营导了两次、PDF 和 Word 版本同时上传、不同文档抄了同一段话。

**三种去重粒度**：

| 方式 | 判据 | 能抓什么 | 抓不到什么 |
|---|---|---|---|
| 精确哈希 | `md5(原文)` 相同 | 完全一样的副本 | 多一个空格、改一个字 |
| 归一化哈希 | 去空白/标点后再 hash | 格式差异的副本 | 同义改写 |
| 语义去重 | 向量余弦 > 阈值 | 「旋转木马票价十元」vs「十元一次旋转木马」 | 需要向量，成本高 |

**阈值是双刃剑**：设 0.99 只能抓几乎一模一样的，漏掉改写版；设 0.85 会把「票价十元」和「票价二十元」判成重复——**表述极像但数字不同**是最容易被误杀的情况。所以阈值要按业务调，最好保留「疑似重复」的人工复核队列，而不是直接删。

**为什么必须去重**：

1. 重复 chunk 会挤占 Top-K 名额，本来能召回 5 条不同信息，结果 3 条是同一段副本
2. 重复内容在 prompt 里被反复强调，模型会误以为这个信息「更重要」
3. 存储和编码成本白花

**去重和缓存不是一回事**：`core/cache.py` 的问答缓存按「问题」去重，命中只是省一次模型调用；知识库去重按「内容」去重，影响的是检索质量。两者不要混为一谈。

**项目落点**：`services/kb_dedup.py` 做知识库层面的重复检测；它跑在入库流程里，属于数据治理而不是在线链路。""",
        "plain": """整理衣柜：

- **精确哈希**：两件一模一样的白 T 恤，一眼看出重复
- **归一化哈希**：一件皱的一件叠好的，还是同一件
- **语义去重**：一件圆领一件 V 领，但都是「白色短袖」，要不要算重复？这就得看你的标准（阈值）了

标准定太严，衣柜里塞满重复；定太松，把「白色」和「米白」当成一件扔了——**看起来几乎一样但细节不同**的东西，永远是去重最危险的地方。""",
        "example": """import hashlib

texts = ["旋转木马票价十元", "旋转木马票价十元 ", "夜场八点开始"]

def dedup_by_hash(texts):
    \"\"\"精确去重：只认「去空格后完全一样」的文本\"\"\"
    seen, out = set(), []
    for t in texts:
        h = hashlib.md5(t.strip().encode("utf-8")).hexdigest()
        if h not in seen:
            seen.add(h)
            out.append(t.strip())
    return out

print(dedup_by_hash(texts))""",
        "example_output": "['旋转木马票价十元', '夜场八点开始']",
        "pitfalls": [
            "把阈值调到 0.85 就上线：'票价十元' 和 '票价二十元' 会被判成重复，直接删掉一条真实信息",
            "只做精确哈希：改写一句、多个标点就漏掉，实际重复率被严重低估",
            "去重时保留的是旧版本：内容更新了却留下老 chunk，用户永远查到过期信息",
            "把知识库去重和问答缓存混为一谈：前者影响检索质量，后者只影响调用成本",
        ],
        "task": """请实现两个函数：

1. `cosine(a, b)`：余弦相似度
   - 任一向量为零向量时返回 `0.0`（不能除零）
   - 正常情况返回 `[−1, 1]` 之间的浮点数

2. `dedup_by_similarity(items, threshold=0.95)`：语义去重
   - `items` 是 `[{"id": ..., "vec": [...]}, ...]`
   - 按顺序遍历，新条目只要与**已保留**的任意一条余弦相似度 **严格大于** `threshold`，就判定为重复并丢弃
   - 返回保留下来的 `id` 列表（保持原顺序）""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """`cosine` 里先算两个模长，任一为 0 就 `return 0.0`。`dedup_by_similarity` 用一个 `kept` 列表存已保留的条目，新条目和 `kept` 逐条比，一旦超过阈值就 `break` 跳出。""",
        "checker": DEDUP_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下面哪种重复是「精确哈希」抓不到的？",
                "options": [
                    "同一个文件被上传了两次",
                    "同一段话改写了一个词后再次上传",
                    "文件内容一字不差但文件名不同",
                    "同一份 FAQ 导入了两个副本",
                ],
                "answer_index": 1,
                "explanation": "改一个词 md5 就完全不同。这类需要归一化哈希（处理格式差异）或语义去重（处理改写）才能抓到。",
            },
            {
                "type": "choice",
                "stem": "语义去重的阈值设得过低（例如 0.7）会有什么风险？",
                "options": [
                    "漏掉大量真正的重复",
                    "把内容不同但表述相近的条目误判成重复并删掉",
                    "检索速度变快但没有副作用",
                    "向量维度会下降",
                ],
                "answer_index": 1,
                "explanation": "阈值越低越激进。0.7 时「票价十元」和「票价二十元」很可能被判为重复，造成真实信息丢失，而且这种错误很难被发现。",
            },
            {
                "type": "judge",
                "stem": "知识库里的重复文档只会浪费存储空间，不影响回答质量。",
                "answer": False,
                "explanation": "重复 chunk 会挤占 Top-K 名额，让本该召回的其它信息进不来；同时重复内容在 prompt 里被反复强调，模型会误判其重要性。",
            },
            {
                "type": "blank",
                "stem": "补全余弦相似度公式（用 ___ 表示要填的部分）：\\ncos = dot(a, b) / (|a| * ___)",
                "answer": "|b|",
                "hint": "填 b 向量的模长，写成带竖线的形式",
                "explanation": "余弦 = 内积除以两个模长之积。分母为 0（零向量）时必须单独返回 0.0。",
            },
        ],
    },
]
