"""科目：RAG 检索工程（第一批 · 5 课）。

这批课补的是「向量检索之后」整条检索链的中段：怎么切、怎么分词、关键词怎么打分、
两路召回怎么融合、候选怎么精排。主线里的 `ai-rag` 只讲了「切分 → 向量化 → Top-K」
这三步的骨架，中间真正决定召回质量的部分全在这里。

每一课都对得上「鸭先知 · 游乐园智能体」里的真实实现，`definition` 末尾的
「项目落点」标了文件与函数名。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）
"""

CHUNK_CHECKER = """
try:
    r = chunk_text(["aaaa", "bbbb", "cccc"], 10)
    assert r == ["aaaa\\nbbbb", "cccc"], "两段能拼下就拼（4+1+4=9<=10），第三段放不下要另起一块，现在是 %r" % (r,)
    r2 = chunk_text(["aaaaaaa"], 3)
    assert r2 == ["aaa", "aaa", "a"], "单段超过 max_chars 要硬切成 ['aaa','aaa','a']，现在是 %r" % (r2,)
    assert chunk_text([], 5) == [], "空输入要返回空列表"
    assert chunk_text(["", "aa"], 5) == ["aa"], "空段落要跳过，不要产生空块"
    assert chunk_text(["ab", ""], 5) == ["ab"], "结尾空段落也不能多出一个空块"
    r3 = add_overlap(["abcdef", "ghij"], 2)
    assert r3 == ["abcdef", "efghij"], "第二块要带上前一块最后 2 个字符 'ef'，现在是 %r" % (r3,)
    assert add_overlap(["abc"], 3) == ["abc"], "只有一块时没有前文可重叠，原样返回"
    assert add_overlap(["abc", "d"], 5) == ["abc", "abcd"], "n 超过前一块长度时取整块"
    assert add_overlap(["abc", "d"], 0) == ["abc", "d"], "n<=0 表示不加重叠"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError) as e:
    print("__FAIL__ 参数或返回类型不对：" + str(e))
"""

TOKENIZE_CHECKER = """
try:
    vocab = {"旋转木马", "旋转", "木马", "大炮乐园"}
    assert max_match("大炮乐园的旋转木马", vocab) == ["大炮乐园", "的", "旋转木马"], "要优先取最长词：'大炮乐园' 不能切成 '大炮'+'乐园'，'旋转木马' 也不能切成 '旋转'+'木马'"
    assert max_match("木马", vocab) == ["木马"], "整词命中时不要退化成单字"
    assert max_match("", vocab) == [], "空串要返回空列表，不能返回 ['']"
    assert max_match("abc", set()) == ["a", "b", "c"], "词表为空时只能逐字切"
    assert max_match("xy", {"xyz"}) == ["x", "y"], "词比剩余文本长时不能越界，要退到单字"
    assert drop_stopwords(["的", "旋转木马", "在"], {"的", "在"}) == ["旋转木马"], "停用词要过滤掉，且保持原顺序"
    assert drop_stopwords(["a"], set()) == ["a"], "停用词表为空时原样返回"
    assert drop_stopwords([], {"a"}) == [], "空 token 列表返回空列表"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError) as e:
    print("__FAIL__ 参数或返回类型不对：" + str(e))
"""

BM25_CHECKER = """
try:
    import math
    docs = [["旋转木马", "票价", "十元"],
            ["旋转木马", "旋转木马", "夜场", "关闭"],
            ["过山车", "票价", "排队"]]
    s = bm25_scores(["旋转木马", "票价"], docs)
    assert len(s) == 3, "每篇文档都要有一个分数，应该有 3 个"
    assert abs(s[0] - 0.9843) < 1e-3, "第 1 篇两个词都命中，分数应约 0.9843，现在是 %.4f" % s[0]
    assert abs(s[1] - 0.6309) < 1e-3, "第 2 篇命中两次'旋转木马'但文档更长，分数应约 0.6309，现在是 %.4f" % s[1]
    assert abs(s[2] - 0.4922) < 1e-3, "第 3 篇只命中'票价'，分数应约 0.4922，现在是 %.4f" % s[2]
    assert bm25_scores([], docs) == [0.0, 0.0, 0.0], "查询词为空时所有分数应为 0.0"
    assert bm25_scores(["不存在的词"], docs) == [0.0, 0.0, 0.0], "词在语料里一次都没出现时分数应为 0.0（不要因为 df=0 就算出巨大权重）"
    assert bm25_scores(["旋转木马"], []) == [], "空语料要返回空列表，不能除零崩掉"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError, ZeroDivisionError) as e:
    print("__FAIL__ 计算出错（注意空语料要提前返回）：" + str(e))
"""

HYBRID_CHECKER = """
try:
    assert minmax([1, 2, 3]) == [0.0, 0.5, 1.0], "min-max 归一化：最小值->0.0，最大值->1.0，中间线性"
    assert minmax([5, 5, 5]) == [0.5, 0.5, 0.5], "所有分数相同时不能除以 0，统一返回 0.5"
    assert minmax([]) == [], "空列表返回空列表"
    assert minmax([7]) == [0.5], "只有一个元素时按「全等」处理，返回 0.5"
    r = fuse([0.9, 0.5, 0.1], [0.1, 0.5, 0.9])
    assert [round(x, 6) for x in r] == [0.6, 0.5, 0.4], "默认 alpha=0.6：第一项语义满分得 0.6，第三项关键词满分得 0.4，中间项两路都居中得 0.5，现在是 %r" % (r,)
    r2 = fuse([1, 1], [1, 1])
    assert r2 == [0.5, 0.5], "两路都全等时各自归一化成 0.5，加权后仍是 0.5"
    r3 = fuse([0.9, 0.1], [9, 0], 1.0)
    assert r3 == [1.0, 0.0], "alpha=1 表示完全信向量路，关键词路不再影响结果"
    try:
        fuse([1, 2], [1])
        assert False, "两路长度不一致时应该抛 ValueError，而不是静默错位相加"
    except ValueError:
        pass
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, IndexError) as e:
    print("__FAIL__ 参数或返回类型不对：" + str(e))
"""

RERANK_CHECKER = """
try:
    docs = ["d1", "d2", "d3", "d4"]
    coarse = {"d1": 0.9, "d2": 0.8, "d3": 0.7, "d4": 0.6}
    fine = {"d1": 0.1, "d2": 0.95, "d3": 0.5, "d4": 0.99}

    r = two_stage("q", docs, lambda q, d: coarse[d], lambda q, d: fine[d], recall_k=2, top_n=2)
    assert r == [("d2", 0.95), ("d1", 0.1)], "先按粗排取前 2 个（d1,d2），再按精排重排：d2 的 0.95 要排到 d1 的 0.1 前面，现在是 %r" % (r,)
    r2 = two_stage("q", docs, lambda q, d: coarse[d], lambda q, d: fine[d], recall_k=10, top_n=2)
    assert r2 == [("d4", 0.99), ("d2", 0.95)], "候选放宽到全部 4 篇后，精排分最高的 d4 必须能翻上来，现在是 %r" % (r2,)
    r3 = two_stage("q", docs, lambda q, d: coarse[d], lambda q, d: fine[d], recall_k=1, top_n=5)
    assert r3 == [("d1", 0.1)], "top_n 超过候选数时只返回现有的候选，不能补空位"
    assert two_stage("q", [], lambda q, d: 0, lambda q, d: 0) == [], "空文档列表要返回空列表"

    calls = {"n": 0}

    def fine_count(q, d):
        calls["n"] += 1
        return fine[d]

    two_stage("q", docs, lambda q, d: coarse[d], fine_count, recall_k=2, top_n=2)
    assert calls["n"] == 2, "精排模型很贵，只能对 2 个候选各调用 1 次；现在是 %d 次 —— 不要在排序比较函数里反复调模型" % calls["n"]

    r4 = two_stage("q", ["a", "b", "c"], lambda q, d: 0.5, lambda q, d: 0.5, recall_k=3, top_n=2)
    assert r4 == [("a", 0.5), ("b", 0.5)], "分数全相同时要保持原顺序（稳定排序），不能随机打乱"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, ValueError) as e:
    print("__FAIL__ 参数或返回结构不对：" + str(e))
"""

LESSONS = [
    {
        "code": "rag-chunk",
        "subject": "RAG 检索工程",
        "stage": "检索基础",
        "runner": "python",
        "title": "文本分块：标题层级与重叠切分",
        "summary": "切得不好，后面检索再强也白搭",
        "definition": """**分块（chunking）= 把长文档切成「能被检索的最小单元」。**

RAG 的检索单位不是「一篇文档」，而是「一个 chunk」。切得太粗，检索到一整个章节，塞进 prompt 既超长又全是噪声；切得太细，一句话被拦腰截断，检索到了也答不全。

四种常见策略，从差到好：

1. **固定长度切**：每 N 个字符一刀。实现最简单，但会在句子中间下刀——`...八点开始。雨` / `天部分项目关闭。`
2. **按段落切**：保留自然边界，但段落长短极不均匀，可能一段就 3000 字。
3. **按标题层级切**：先用 `#` / `##` / `###` 把文档拆成章节，章节内再递归切。游乐园的 FAQ、票价表最适合这种——「票价」和「退票规则」天然是两个知识块。
4. **递归切**（`RecursiveCharacterTextSplitter`）：按分隔符优先级 `["\\n\\n", "\\n", "。", "，", ""]` 依次尝试，先用段落切，切不动再用句号，最后才硬切字符。

两个关键参数：

- `chunk_size`：单块上限（按字符或 token 计）。太小丢上下文，太大召回不准。
- `chunk_overlap`：相邻块的重叠长度。作用是**防止关键句正好落在切点上被劈成两半**——有了重叠，这句话至少会完整出现在其中一块里。

还有一个容易忽略的点：**标题要和正文绑在一起**。把标题单独切出去，它没有信息量；正文丢了标题，又不知道在讲哪一节。工程上的做法是给每块补一段标题前缀（`票价 > 夜场票 > 退改规则`）。""",
        "plain": """把一本手册撕成卡片，一张卡片就是一块。

- 固定长度切 = 拿尺子量着撕，经常把一句话从中间撕断：「雨天部分项目关」/「闭。」
- 按标题切 = 顺着目录撕，「票价」一章、「退票」一章，每张卡片自己说得清
- overlap = 相邻两张卡片故意留一小段重复，免得关键句正好压在撕口上，两张都不完整""",
        "example": """def naive_cut(text, size=12):
    \"\"\"反例：不看段落，只按固定长度硬切\"\"\"
    return [text[i:i + size] for i in range(0, len(text), size)]

doc = "旋转木马适合低龄儿童。\\n夜场烟花在八点开始。\\n雨天部分项目关闭。"
for i, piece in enumerate(naive_cut(doc), 1):
    print("块%d: %r" % (i, piece))""",
        "example_output": """块1: '旋转木马适合低龄儿童。\\n'
块2: '夜场烟花在八点开始。\\n雨'
块3: '天部分项目关闭。'""",
        "pitfalls": [
            "只按固定长度切，句子被拦腰截断——检索到的片段缺主语，模型只能瞎猜",
            "chunk 太大：一块塞进整章，召回分数被稀释，还挤占 prompt 预算",
            "忘记设 overlap：关键句刚好跨在边界上，两块各拿一半，谁都答不全",
            "把标题和正文切开：标题单独成块没有信息量，正文丢了标题又不知道在讲哪一节",
        ],
        "task": """请实现两个函数：

1. `chunk_text(paragraphs, max_chars)`：把段落列表合并成块
   - 段落之间用 `"\\n"` 连接
   - 当前块加上下一段后不超过 `max_chars`，就继续拼；否则先把当前块存起来，从新的一段开始
   - 单个段落本身就超过 `max_chars` 时，按 `max_chars` 硬切成多块
   - 空字符串段落直接跳过；输入为空返回 `[]`

2. `add_overlap(chunks, n)`：给相邻块加重叠
   - 第 1 块原样保留；之后每一块都在前面拼上「前一块的最后 n 个字符」
   - `n <= 0` 时原样返回""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """合并时用 `len(cur) + 1 + len(p)` 判断（`+1` 是那个 `"\\n"`）。硬切用 `while` 循环不断 `p = p[max_chars:]`。重叠取 `chunks[i-1][-n:]`，注意 `n` 可能比前一块还长。""",
        "checker": CHUNK_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "chunk_size 设得太小，最直接的后果是什么？",
                "options": [
                    "每块缺少上下文，检索到的片段答不全问题",
                    "向量维度会变高，存储成本上升",
                    "BM25 会失效，只能走向量检索",
                    "embedding 模型无法编码",
                ],
                "answer_index": 0,
                "explanation": "切得太碎，一块可能只剩半句话，模型拿不到完整语义；维度由 embedding 模型决定，与 chunk 大小无关。",
            },
            {
                "type": "choice",
                "stem": "chunk_overlap 解决的是什么问题？",
                "options": [
                    "降低 embedding 的计算成本",
                    "防止关键句正好落在切点被劈成两半",
                    "让所有块的长度完全一致",
                    "提升向量库的写入速度",
                ],
                "answer_index": 1,
                "explanation": "重叠的本质是给切点买保险：关键句至少会完整出现在相邻两块中的一块里。它反而会增加存储和计算量。",
            },
            {
                "type": "judge",
                "stem": "分块只需要按固定长度切，不需要考虑标题层级。",
                "answer": False,
                "explanation": "固定长度切会破坏语义边界。按标题层级切能让每块自带上下文（例如「票价 > 夜场票」），召回和回答质量都更高。",
            },
            {
                "type": "blank",
                "stem": "补全下面这一行（用 ___ 表示要填的部分）：\\nRecursiveCharacterTextSplitter(chunk_size=500, chunk___=80)",
                "answer": "overlap",
                "hint": "填一个英文单词，表示「重叠」",
                "explanation": "参数名是 `chunk_overlap`，表示相邻块重叠的字符（或 token）数。",
            },
        ],
    },
    {
        "code": "rag-tokenize",
        "subject": "RAG 检索工程",
        "stage": "检索基础",
        "runner": "python",
        "title": "中文分词与自定义词典",
        "summary": "不分词，关键词检索根本无从下手",
        "definition": """英文单词之间有空格，`"park ticket"` 天然是两个 token；中文是连续字串，`"旋转木马票价"` 机器不知道哪几个字该连在一起。

**分词（tokenization）= 把连续的中文串切成有意义的词。**

jieba 的三种粒度：

- **精确模式** `jieba.cut(text)`：尽量切得合理，适合做检索
- **全模式** `jieba.cut(text, cut_all=True)`：所有可能成词的都切出来，召回高但噪声大
- **搜索引擎模式** `jieba.cut_for_search(text)`：在精确模式基础上，把长词再切出短词（`旋转木马` → `旋转`、`木马`、`旋转木马`），适合建倒排索引

**为什么必须自定义词典**：通用词典不认识你的业务术语。`大炮乐园` 会被切成 `大炮 / 乐园`，`浴室大作战` 会被切成 `浴室 / 大 / 作战`。一旦切碎，BM25 就再也匹配不上用户问的「大炮乐园」——因为索引里存的词和查询切出来的词不是同一个。

**分词结果必须稳定**。同一句话在不同模块里切出不同的词，会导致两个隐蔽 bug：BM25 命中不了、Redis 缓存 key 算不一致（同一问题反复回源）。所以业务词典要在**模块加载时幂等注册**，而不是散落在各处。

**项目落点**：`core/keywords.py` 的 `ensure_business_words()` 把园区项目名、办卡/退卡/失物等业务词注册进 jieba，`core/bm25_index.py` 和 `core/cache.py` 共用这一份词典。

**最长匹配的局限**：正向最大匹配是贪心算法，只看眼前能匹配多长，不保证全局最优。`"北京大学生"` 可能切错。工程上靠「词典质量 + 统计模型（HMM）」兜底，jieba 默认就带 HMM 处理未登录词。""",
        "plain": """中文是一串连笔字，分词就是给它断句。

「大炮乐园」在通用词典里是「大炮 / 乐园」两个词。用户搜「大炮乐园」时，如果索引里存的是「大炮」「乐园」，那也能匹配上；但如果用户搜的是整个词、索引里被切成了「大炮」「乐园」，短语匹配就散了。更糟的是「浴室大作战」被切成「浴室 / 大 / 作战」——「大」这种单字进索引，等于给所有文档加噪声。

自定义词典就是告诉分词器：「这几个字必须当成一个词，别拆。」""",
        "example": """vocab = {"旋转木马", "旋转", "木马", "大炮乐园"}
text = "大炮乐园的旋转木马"

# 反例：只挑词表里长度恰好为 2 的词去匹配，不做最长匹配
def greedy2(text, vocab):
    two = {w for w in vocab if len(w) == 2}
    out, i = [], 0
    while i < len(text):
        if text[i:i + 2] in two:
            out.append(text[i:i + 2])
            i += 2
        else:
            out.append(text[i])
            i += 1
    return out

print(greedy2(text, vocab))""",
        "example_output": "['大', '炮', '乐', '园', '的', '旋转', '木马']",
        "pitfalls": [
            "只按单字切：索引里全是「旋」「转」「木」「马」，任何含这些字的文档都会被误召回",
            "不注册业务词典：「大炮乐园」被切成「大炮 / 乐园」，用户搜全称反而匹配不上",
            "分词结果不稳定：不同模块加载顺序不同导致切法不同，缓存 key 算不一致",
            "把停用词也进索引：「的」「了」「在」几乎每篇都有，idf 接近 0，只增加噪声",
        ],
        "task": """请实现两个函数：

1. `max_match(text, vocab)`：正向最大匹配分词
   - 从当前位置开始，尝试 `vocab` 里能匹配到的**最长**词
   - 一个都匹配不上时，单个字符单独成词
   - `text` 为空返回 `[]`；`vocab` 为空时逐字切

2. `drop_stopwords(tokens, stops)`：过滤停用词
   - 返回不在 `stops` 里的 token，保持原顺序""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """用一个 `while i < len(text)` 循环，内层 `for L in range(min(maxlen, len(text)-i), 0, -1)` 从长到短试 `text[i:i+L] in vocab`；`for...else` 可以在一个都没匹配上时补单字。""",
        "checker": TOKENIZE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "中文检索为什么不能像英文那样直接按空格切词？",
                "options": [
                    "中文词之间没有空格，必须靠词典或模型判断词边界",
                    "中文的字符编码不是 UTF-8",
                    "中文没有停用词",
                    "中文的词长固定为两个字",
                ],
                "answer_index": 0,
                "explanation": "中文书写不带词边界标记，这正是需要分词器的根本原因；编码、停用词、词长都不是原因。",
            },
            {
                "type": "choice",
                "stem": "把「大炮乐园」加入 jieba 自定义词典，主要解决什么问题？",
                "options": [
                    "让这个词的 idf 变高",
                    "保证它不会在索引和查询中被切成不同的碎片",
                    "减少向量维度",
                    "让 BM25 自动忽略这个词",
                ],
                "answer_index": 1,
                "explanation": "自定义词典保证「索引时」和「查询时」切法一致。切法不一致就永远匹配不上，这是最隐蔽的一类召回 bug。",
            },
            {
                "type": "judge",
                "stem": "正向最大匹配是贪心算法，能保证得到全局最优的分词结果。",
                "answer": False,
                "explanation": "最大匹配每一步只看当前能匹配多长，可能为了眼前的词牺牲更合理的整体切法。它是工程近似，不是全局最优。",
            },
            {
                "type": "blank",
                "stem": "补全 jieba 精确模式分词（用 ___ 表示要填的部分）：\\nlist(jieba.___(text))",
                "answer": "cut",
                "hint": "填一个三个字母的方法名",
                "explanation": "`jieba.cut(text)` 返回生成器，转成 list 才能看到全部结果；`cut_all=True` 是全模式，`cut_for_search` 是搜索引擎模式。",
            },
        ],
    },
    {
        "code": "rag-bm25",
        "subject": "RAG 检索工程",
        "stage": "检索基础",
        "runner": "python",
        "title": "BM25 稀疏检索与打分公式",
        "summary": "关键词检索的事实标准，靠两个参数治住刷分",
        "definition": """**BM25 = 带「词频饱和」和「长度惩罚」的 TF-IDF，是关键词检索的事实标准。**

它的出发点是很朴素的两个观察：

1. **一个词出现 10 次，不该比出现 1 次重要 10 倍**。所以 TF 要饱和：涨到一定程度就压平。这就是参数 `k1`（常用 1.2~2.0）。
2. **长文档天然容易命中更多词，这不公平**。所以要按文档长度惩罚。参数 `b`（0~1，常用 0.75）控制强度：`b=0` 完全不惩罚，`b=1` 完全按长度归一。

打分公式（对 query 里每个词累加）：

```
idf(t)    = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
tf_part   = tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))
score     = Σ  idf(t) * tf_part
```

- `N` 文档总数，`df(t)` 含词 t 的文档数
- `tf` 词 t 在本篇出现次数，`dl` 本篇长度，`avgdl` 平均文档长度
- idf 里的 `+0.5` 是平滑项：保证 `df` 再大 idf 也不会变成负数

**为什么不用纯 TF**：纯 TF 下，把「旋转木马」重复 50 遍就能把任何文档顶到第一位——这是最原始的刷分漏洞。BM25 的 `tf_part` 有上界 `(k1+1)`，重复再多也只能逼近这个上限。

**IDF 的方向别记反**：越常见的词 idf 越小（「的」几乎每篇都有 → 接近 0），越稀有的词 idf 越大。这正是「稀有词更能区分类别」的数学表达。

**项目落点**：`core/bm25_index.py` 用 `rank_bm25.BM25Okapi` 建内存索引，配合 jieba 分词；索引 pickle 到 `index/bm25_index.pkl`，服务重启直接加载，不用重新分词。""",
        "plain": """老师的评分办法：

- **答对一次给分，但答对十次不给十分**（tf 饱和）—— 防止学生靠重复一句话刷分
- **答卷越长，同样答对一次给的分越少**（长度惩罚 b）—— 因为长卷子本来就更容易「蒙对」更多关键词
- **越偏的题答对给分越高**（idf）—— 全班都答对的常识题，区分不出谁更强""",
        "example": """import math

CORPUS = [["旋转木马", "票价"], ["旋转木马", "夜场"], ["过山车", "排队"], ["雨天", "退票"]]

def score_linear(term, doc, docs):
    \"\"\"反例：直接把词频当分数，没有 k1 饱和 —— 堆词就能刷分\"\"\"
    tf = doc.count(term)
    df = sum(1 for d in docs if term in d)
    return round(tf * math.log(len(docs) / df), 4)

print("出现1次:", score_linear("旋转木马", ["旋转木马", "票价", "排队"], CORPUS))
print("出现3次:", score_linear("旋转木马", ["旋转木马", "票价", "排队"] + ["旋转木马"] * 2, CORPUS))
print("出现5次:", score_linear("旋转木马", ["旋转木马", "票价", "排队"] + ["旋转木马"] * 4, CORPUS))""",
        "example_output": """出现1次: 0.6931
出现3次: 2.0794
出现5次: 3.4657""",
        "pitfalls": [
            "漏掉长度归一（b=0）：长文档只要把所有词都提一遍就稳居第一，短文档永远排不上",
            "漏掉 TF 饱和（k1 趋近无穷）：同一篇里堆关键词就能刷分，这是最典型的作弊路径",
            "idf 用了 log(N/df) 却忘了平滑：某个词在所有文档都出现时 idf=0，甚至出现负数把分数拉低",
            "query 里出现在语料中不存在的词还硬算 idf：df=0 会算出巨大权重，正确做法是 tf=0 直接跳过",
        ],
        "task": """请实现 `bm25_scores(query_terms, docs, k1=1.5, b=0.75)`：

- `query_terms` 是查询词列表，`docs` 是「已经分好词」的文档列表（`list[list[str]]`）
- 返回每篇文档的 BM25 分数列表（`list[float]`），顺序与 `docs` 一致
- 某个词在本篇出现 0 次就跳过，不贡献分数
- `docs` 为空时返回 `[]`（注意别让 `avgdl` 除零）
- `query_terms` 为空时，所有文档分数都是 `0.0`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先算 `N` 和 `avgdl`，然后对每篇文档遍历 query 词：`tf = d.count(t)`，`df = sum(1 for x in docs if t in x)`，`idf = math.log(1 + (N - df + 0.5) / (df + 0.5))`，最后累加 `idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))`。""",
        "checker": BM25_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "BM25 里的 k1 参数控制什么？",
                "options": [
                    "文档长度惩罚的强度",
                    "词频增长的饱和速度：k1 越小越快饱和",
                    "参与检索的文档总数",
                    "idf 的平滑系数",
                ],
                "answer_index": 1,
                "explanation": "k1 控制 tf 曲线的曲率。k1 越小，词频很快就饱和；k1 趋近无穷时退化成线性 TF。长度惩罚是 b 控制的。",
            },
            {
                "type": "choice",
                "stem": "b 参数设成 0 会发生什么？",
                "options": [
                    "完全不按文档长度做惩罚，长文档占便宜",
                    "完全不使用 idf",
                    "所有文档分数变成 0",
                    "只保留停用词",
                ],
                "answer_index": 0,
                "explanation": "`b=0` 时公式里的 `b * dl / avgdl` 项消失，长度因子恒为 1，长文档因为更容易命中关键词而占优。",
            },
            {
                "type": "judge",
                "stem": "在 BM25 中，一个词出现 10 次的得分是出现 1 次的 10 倍。",
                "answer": False,
                "explanation": "`tf_part` 有上界 `k1+1`，词频增长是饱和的。这正是 BM25 相对纯 TF 的核心改进——防止堆词刷分。",
            },
            {
                "type": "blank",
                "stem": "补全 BM25 的 idf 平滑公式（用 ___ 表示要填的部分）：\\nidf = ln(1 + (N - df + 0.5) / (df + ___))",
                "answer": "0.5",
                "hint": "填一个数字，和分子里的平滑项对称",
                "explanation": "分子分母各加 0.5，是标准的概率平滑，保证 df 再大 idf 也不为负。",
            },
        ],
    },
    {
        "code": "rag-hybrid",
        "subject": "RAG 检索工程",
        "stage": "融合与精排",
        "runner": "python",
        "title": "混合检索与分数融合",
        "summary": "向量管语义、BM25 管专名，怎么合成一个排名",
        "definition": """**混合检索 = 同时跑「稠密向量检索」和「稀疏关键词检索」，再把两路结果合成一个排名。**

为什么要两路：

| | 向量检索（稠密） | BM25（稀疏） |
|---|---|---|
| 擅长 | 换个说法也能找到（「小孩子能玩吗」≈「儿童身高限制」） | 专有名词、型号、错误码、人名（「大炮乐园」「E1024」） |
| 短板 | 罕见词、精确匹配差 | 同义改写完全失效 |
| 成本 | 要过 Embedding 模型 | 纯统计，极快 |

**两种融合方式，别搞混：**

1. **分数级融合（加权）**：两路分数先各自 min-max 归一化到 `[0,1]`，再 `alpha * 向量分 + (1-alpha) * 关键词分`。
   - 必须先归一化：向量分可能是 0.83，BM25 分可能是 12.7，量纲不同直接相加，等于让 BM25 单方面决定结果。
   - 缺点：两路分数的分布会随 query 变化，`alpha` 的语义并不稳定。
2. **排名级融合（RRF）**：不看分数只看名次，`score(doc) = Σ 1/(k + rank)`，`k` 常取 60。
   - 优点：完全免疫量纲问题，不用调 alpha。
   - 缺点：丢掉了「第一名领先第二名多少」的信息。

**min-max 的坑**：如果所有分数都相同，`max - min = 0`，会除零。工程上约定返回全 `0.5`——表示「这一路给不出区分度，大家都一样」。

**alpha 怎么定**：没有万能值。业务问句偏口语（「这卡还能用吗」）→ 语义权重高；偏精确（「退票手续费几个点」）→ 关键词权重高。所以 alpha 应该是可配置、可热更的参数，而不是硬编码。

**项目落点**：`agents/retrieval_agent.py` 的 `_score_fusion()` 用分数级融合，`alpha` 默认 0.6（语义 0.6 / 关键词 0.4），支持运行时热更新——商家 PC 端的「Agent 参数」页可以直接调；`bench_alpha_sweep.py` 是扫不同 alpha 找最优值的脚本。""",
        "plain": """两个老师同时批同一批卷子：

- 语文老师（向量）看「意思对不对」，你换个说法他也给分
- 数学老师（BM25）看「关键词写没写对」，你意思再对，公式名写错就是零分

最后要合成一个总分。两个老师的满分标准不一样（一个给 0.83，一个给 12.7），得先各自折算成百分制，再按权重加。这就是 min-max 归一化 + alpha 加权。

RRF 是另一种思路：不看分数，只看「你在每个老师那里排第几」，第 1 名得 1/61 分，第 2 名得 1/62 分…… 好处是彻底不用管两边的分数量纲。""",
        "example": """def rrf(rank_lists, k=60):
    \"\"\"倒数排名融合：只看得票名次，不看原始分数\"\"\"
    score = {}
    for ranks in rank_lists:
        for pos, doc in enumerate(ranks, 1):
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + pos)
    return sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))

vector_rank = ["docA", "docB", "docC"]
bm25_rank = ["docC", "docA", "docB"]
for doc, sc in rrf([vector_rank, bm25_rank]):
    print(doc, round(sc, 5))""",
        "example_output": """docA 0.03252
docC 0.03227
docB 0.032""",
        "pitfalls": [
            "不归一化直接相加：BM25 分数量级远大于余弦相似度，alpha 形同虚设，实际退化成纯关键词检索",
            "归一化时没处理「全部分数相同」：max-min=0 直接除零崩掉",
            "两路候选集大小不一致却按位置硬加：必须按 doc_id 对齐，否则张冠李戴",
            "把 RRF 和加权融合混着讲：RRF 用名次、加权用分数，两者的调参逻辑完全不同",
        ],
        "task": """请实现两个函数：

1. `minmax(scores)`：把一组分数线性归一化到 `[0, 1]`
   - 最小值映射到 `0.0`，最大值映射到 `1.0`
   - 所有值相同时（含只有一个元素）返回全 `0.5`，不能除零
   - 空列表返回 `[]`

2. `fuse(vec_scores, kw_scores, alpha=0.6)`：两路分数加权融合
   - 两路各自先做 `minmax`，再算 `alpha * 向量分 + (1 - alpha) * 关键词分`
   - 两个列表长度不一致时抛 `ValueError`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """`minmax` 里先判 `if not scores: return []`，再算 `lo, hi`，`if hi == lo` 就返回等长的 `0.5` 列表。`fuse` 里用 `zip` 把两个归一化后的列表配起来。""",
        "checker": HYBRID_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "混合检索中 alpha=0.6 通常表示什么？",
                "options": [
                    "向量路占 60% 权重，关键词路占 40%",
                    "只保留 60% 的检索结果",
                    "BM25 的 k1 参数等于 0.6",
                    "60% 的文档走向量检索，40% 走 BM25",
                ],
                "answer_index": 0,
                "explanation": "alpha 是加权融合里向量路的权重，`1-alpha` 给关键词路。它不是过滤比例，也不是 k1。",
            },
            {
                "type": "choice",
                "stem": "加权融合之前为什么一定要做 min-max 归一化？",
                "options": [
                    "为了让检索速度更快",
                    "两路分数量纲不同，不归一化就等于让量级大的那一路独占权重",
                    "为了消除停用词",
                    "因为 BM25 的分数一定是负数",
                ],
                "answer_index": 1,
                "explanation": "余弦相似度在 0~1 之间，BM25 可能到十几。直接相加时 alpha 几乎不起作用，结果会被 BM25 主导。",
            },
            {
                "type": "judge",
                "stem": "RRF（倒数排名融合）要求两路检索的分数在同一量纲上。",
                "answer": False,
                "explanation": "RRF 只用名次 `1/(k+rank)`，完全不看原始分数，所以天然免疫量纲差异——这正是它相对加权融合的最大优势。",
            },
            {
                "type": "blank",
                "stem": "补全加权融合的表达式（用 ___ 表示要填的部分）：\\nscore = alpha * v + (1 - ___) * k",
                "answer": "alpha",
                "hint": "填一个英文单词，和前面的 alpha 相同",
                "explanation": "两路权重之和必须为 1：向量路 alpha，关键词路 1-alpha。写错成 `1-beta` 之类的会让总分不再可比。",
            },
        ],
    },
    {
        "code": "rag-rerank",
        "subject": "RAG 检索工程",
        "stage": "融合与精排",
        "runner": "python",
        "title": "Reranker 交叉编码器重排",
        "summary": "粗排要快要全，精排要准，两阶段各司其职",
        "definition": """**重排（rerank）= 用更贵但更准的模型，把召回的前 N 条重新排一遍。**

两阶段检索的标准结构：

```
全库 10 万条
   │  ① 粗排（召回）：向量检索 + BM25，要快要全
   ▼
候选 20~100 条
   │  ② 精排：交叉编码器逐条打分，要准
   ▼
最终 3~5 条 → 塞进 prompt
```

**双塔（bi-encoder）vs 交叉编码器（cross-encoder）**：

- 双塔：query 和 doc **分别**编码成向量，再算相似度。doc 向量可以离线预计算进 Milvus，查询时只算 query 一次 → 快，但 query 和 doc 从未「见过面」。
- 交叉编码器：把 `[query, doc]` **拼成一个输入**过模型，输出相关性分数。它能捕捉词与词的交互 → 准，但**没法预计算**：10 万篇就要跑 10 万次前向。

这就是为什么必须两阶段：**交叉编码器的精度只在候选集上有意义，因为它根本跑不了全库。**

**代价意识（最容易写错的地方）**：精排模型很贵，所以只能对候选各调用一次。如果用 `sorted(docs, key=lambda d: model(q, d))`，`key` 函数会被调用 `n log n` 次，延迟直接翻十几倍。正确写法是先算一次分数存成 `(doc, score)`，再按 score 排序。

**排序要稳定**：分数相同时保持粗排的相对顺序，别让同一批 query 每次跑出不同结果——不可复现的检索结果没法做评测。

**项目落点**：`core/reranker.py` 用 `BAAI/bge-reranker-v2-m3`（CrossEncoder）；`RERANK_TOP` 控制精排后保留几条，`RERANK_DOC_MAX_CHARS` 截断过长文档（交叉编码器输入长度有限），`RERANK_PRE_FILTER` 控制进精排的候选数。""",
        "plain": """找工作筛简历：

- **粗排** = HR 用关键词扫一遍，5 秒一份，从 1 万份里挑出 50 份。快，但会漏人——简历里写「推荐系统」的，可能实际做的是广告排序。
- **精排** = 面试官一份份仔细读，50 份挑 3 个。准，但一天只能读 50 份。

你不可能让面试官去读 1 万份简历——这就是为什么交叉编码器只能用在候选集上。""",
        "example": """docs = ["旋转木马票价", "旋转木马在哪里", "过山车身高限制", "旋转木马几点关"]
bi = [0.81, 0.79, 0.62, 0.60]       # 双塔：只比「向量像不像」，措辞相近就高分
cross = [0.93, 0.41, 0.12, 0.88]    # 交叉编码器：真读了一遍 query+doc

order_bi = [d for _, d in sorted(zip(bi, docs), key=lambda x: -x[0])]
order_cross = [d for _, d in sorted(zip(cross, docs), key=lambda x: -x[0])]
print("粗排:", order_bi)
print("精排:", order_cross)""",
        "example_output": """粗排: ['旋转木马票价', '旋转木马在哪里', '过山车身高限制', '旋转木马几点关']
精排: ['旋转木马票价', '旋转木马几点关', '旋转木马在哪里', '过山车身高限制']""",
        "pitfalls": [
            "在 sorted 的 key 函数里调精排模型：比较次数是 n log n，延迟翻十几倍",
            "把交叉编码器用在全库上：10 万篇跑 10 万次前向，接口直接超时",
            "精排候选集开得太大：`RERANK_TOP` 设成 500，精度没涨多少，P99 延迟先炸了",
            "忽略输入长度限制：超长文档不截断，CrossEncoder 会截断在奇怪的位置或直接报错",
        ],
        "task": """请实现 `two_stage(query, docs, coarse_fn, fine_fn, recall_k=20, top_n=3)`：

1. 用 `coarse_fn(query, doc)` 给所有文档打粗排分，取分数最高的 `recall_k` 篇作为候选
2. 对每个候选调用**一次** `fine_fn(query, doc)` 得精排分
3. 按精排分从高到低排序，取前 `top_n` 篇
4. 返回 `[(doc, fine_score), ...]`

要求：
- `docs` 为空返回 `[]`
- `recall_k` 或 `top_n` 超过实际数量时，有多少返回多少
- 分数相同时保持候选进入精排时的顺序（稳定排序）""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先用 `sorted(docs, key=lambda d: -coarse_fn(query, d))[:recall_k]` 取候选；再用列表推导 `[(d, fine_fn(query, d)) for d in cand]` 每个候选只算一次；最后 `scored.sort(key=lambda x: -x[1])` 取前 `top_n`。""",
        "checker": RERANK_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "为什么交叉编码器不能直接用于全库检索？",
                "options": [
                    "它的向量维度太高，存不下",
                    "它必须把 query 和 doc 拼在一起过模型，无法预计算文档表示",
                    "它只支持英文",
                    "它的准确率比双塔低",
                ],
                "answer_index": 1,
                "explanation": "双塔可以为每篇文档离线算好向量；交叉编码器的输入依赖 query，同一篇文档对不同 query 的分数都不同，所以只能在线逐条算。",
            },
            {
                "type": "choice",
                "stem": "精排阶段的候选集（recall_k）一般设多大比较合理？",
                "options": [
                    "等于全库大小，越多越准",
                    "几十到一两百条，兼顾精度与延迟",
                    "固定为 1 条，最快",
                    "必须正好等于 top_n",
                ],
                "answer_index": 1,
                "explanation": "候选越多召回越全，但交叉编码器是线性成本。工程上是几十到一两百的折中；等于 top_n 就失去了重排的意义。",
            },
            {
                "type": "judge",
                "stem": "在精排阶段，同一篇文档对不同的 query 可以复用同一个相关性分数。",
                "answer": False,
                "explanation": "交叉编码器的输入是 `[query, doc]` 拼起来的整体，分数天然依赖 query，无法像双塔那样缓存文档向量。",
            },
            {
                "type": "blank",
                "stem": "补全两阶段检索的第二步（用 ___ 表示要填的部分）：\\ntop = reranker.___(query, candidates)",
                "answer": "rerank",
                "hint": "填一个英文单词，就是「重排」",
                "explanation": "方法名是 `rerank`。项目里 `RerankerEngine.rerank(query, docs, top_n)` 返回重排后的文档列表。",
            },
        ],
    },
]
