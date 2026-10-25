"""「RAG 检索工程」9 课在鸭先知项目里的真实落点。

这批课本身就是照着项目反推出来的，所以每一条都是 `used` —— 除了 `rag-ingest`：
项目做的是**全量重建**，没有增量更新，如实标成 `absent`。

行号对应 2026-10 的代码状态；项目改动后按函数名重新定位。
"""

from .learn_project_base import absent, choice, judge, used

REFS: dict[str, dict] = {
    "rag-chunk": used(
        "data_pipeline.py", "24-40",
        '''def split_text(text: str):
    """文本语义分块 - 标题层级切块 + 递归切块 + 80-100token重叠"""
    # Step 1: 标题层级切块（按 Markdown 标题 # / ## / ### 拆分）
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]

    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=True,
    )''',
        "`split_text()` 的第 1 步。第 2 步会用 RecursiveCharacterTextSplitter 继续递归切，"
        "并保留 80~100 token 的重叠。",
        "这就是课程里说的「标题层级 + 递归 + overlap」三件套，顺序也是对的：先按语义边界"
        "（`#`/`##`/`###`）切大块，块内再按字符递归切，最后给相邻块加重叠。"
        "注意 `strip_headers=True` —— 标题被从正文里剥掉了，所以项目在后续步骤里要把"
        "header 重新拼回每块开头（`header_parts`），否则块会失去「这一节讲什么」的上下文。"
        "这正是课程易错点里写的「标题和正文不能切开」。",
        [
            choice("`split_text()` 为什么先按 Markdown 标题切，而不是直接按固定长度切？",
                   ["标题切分速度更快", "标题天然是语义边界，先切大块能保证每块主题单一", "固定长度切不支持中文", "为了让 chunk 数量变少"],
                   1, "标题是作者划好的语义分割线。先按它切，能避免「票价」和「退票」被混进同一块。"),
            judge("设置 `strip_headers=True` 之后，就不需要再把标题拼回正文了。", 0,
                  "错。剥掉标题是为了不让标题单独成块，但正文块必须把标题前缀补回去，否则块内不知道在讲哪一节。项目后续的 header_parts 就是干这个的。"),
        ],
    ),
    "rag-tokenize": used(
        "core/keywords.py", "33-45",
        '''def ensure_business_words() -> None:
    """向 jieba 全局词典注册业务词（幂等，可在任意模块安全调用）"""
    global _registered
    if _registered:
        return
    with _reg_lock:
        if _registered:
            return
        for word in BUSINESS_WORDS:
            jieba.add_word(word, freq=100)
        _registered = True''',
        "`ensure_business_words()`，被 `core/bm25_index.py` 和 `core/cache.py` 在模块加载时各调用一次。",
        "这段代码正面回答了课程里那个问题：**为什么分词结果必须稳定**。"
        "`jieba.add_word` 改的是**进程级全局词典**，一旦两个模块以不同顺序初始化，"
        "切出来的词就可能不一样 —— 于是 BM25 索引里存的分词和查询时分词对不上，"
        "缓存 key 也会算不一致。项目的解法是「双重检查锁 + `_registered` 标志」，"
        "保证不管谁先调用，词典只注册一次、结果唯一。`freq=100` 是人工调高的词频，"
        "让这些业务词在和通用词竞争切分时赢。",
        [
            choice("`ensure_business_words()` 用双重检查锁 + `_registered` 标志，主要是为了解决什么？",
                   ["加快 jieba 启动速度", "保证业务词典只注册一次，任何模块以任何顺序调用结果都一致", "防止 jieba 崩溃", "支持多语言分词"],
                   1, "词典是进程级全局状态。重复注册会让词频累加，不同加载顺序会导致不同分词结果，最终让索引和查询对不上。"),
            judge("jieba 的自定义词典是每个函数独立的，所以不用担心模块加载顺序。", 0,
                  "错。jieba 的词典是**进程级全局**的，add_word 会一直生效。这正是要用幂等注册锁的原因。"),
        ],
    ),
    "rag-bm25": used(
        "core/bm25_index.py", "49-59",
        '''    @staticmethod
    def _tokenize(text: str) -> list:
        """中文分词（jieba cut_for_search + 自定义词典 + 2-gram字符回退）

        cut_for_search 会将复合词拆分为子词以提升召回：
          例："怎么办卡充值" → ["怎么", "怎么办", "办卡", "卡", "充值"]
        而普通 cut 只会得到：["怎么办", "卡", "充值"]
        """
        # 1. jieba cut_for_search 分词（搜索引擎模式，召回率更高）
        tokens = list(jieba.cut_for_search(text))
        tokens = [t.strip() for t in tokens if t.strip() and len(t.strip()) >= 1]''',
        "`BM25Index._tokenize()`，建索引和查询时都走它。",
        "课程里 BM25 的公式只管「拿到词之后怎么打分」，真正决定效果的其实是**怎么切词**。"
        "项目在 BM25 之前做了两层工程补强：① 用 `cut_for_search` 而不是 `cut` —— "
        "「怎么办卡充值」会被切成 `怎么/怎么办/办卡/卡/充值`，多出来的子词让「办卡」也能命中；"
        "② 再加一层字符级 2-gram 兜底，防止 jieba 把某个关键短词整个漏掉。"
        "这两层都是纯召回导向的，代价是索引变大、噪声变多 —— 属于典型的「召回换精确」。",
        [
            choice("项目为什么用 `jieba.cut_for_search` 而不是 `jieba.cut` 来建 BM25 索引？",
                   ["cut_for_search 更快", "它会把复合词额外拆出子词，提升召回", "cut 不支持自定义词典", "cut_for_search 会去掉停用词"],
                   1, "搜索引擎模式会把「怎么办卡充值」拆出「办卡」「充值」等子词，用户只输入其中一个也能命中。代价是索引膨胀。"),
            judge("BM25 的分数完全由公式决定，前面的分词方式不影响最终排序。", 0,
                  "错。BM25 的输入是 token 列表，切法不同 tf/df 就不同，排序会直接变。分词是 BM25 效果的上限。"),
        ],
    ),
    "rag-hybrid": used(
        "agents/retrieval_agent.py", "281-289",
        '''        # --- Min-Max 归一化到 [0, 1] ---
        def _minmax(scores: list) -> list:
            mn, mx = min(scores), max(scores)
            if mx == mn:
                return [1.0] * len(scores)
            return [(s - mn) / (mx - mn) for s in scores]

        vec_norm = _minmax(vec_scores_raw)
        bm25_norm = _minmax(bm25_scores_raw)''',
        "`RetrievalAgent._score_fusion()`，融合 BGE-M3 向量分和 BM25 分，`alpha` 默认 0.6。",
        "融合公式与课程一致：`alpha * vec_norm + (1-alpha) * bm25_norm`，alpha 还是可热更的"
        "（商家 PC 端「Agent 参数」页能直接调）。**但有一处和课程约定不同，值得单独记一笔**："
        "课程里写「所有分数相同时返回全 0.5」，项目这里返回的是 `[1.0] * len(scores)`。"
        "两者都能避免除零，但语义不一样 —— 0.5 表示「这一路没有区分度，给个中性分」，"
        "1.0 表示「这一路大家都满分」。后者会让两路都无区分度时总分恒为 1.0，"
        "下游如果拿绝对分数做阈值过滤，就会全部放行。**看代码时发现这种分歧，"
        "不要默认谁写错了，先想清楚它对下游有什么影响。**",
        [
            choice("项目 `_minmax` 在 `mx == mn` 时返回 `[1.0] * len(scores)`，而不是课程约定的 0.5，最直接的后果是什么？",
                   ["会抛 ZeroDivisionError", "两路都无区分度时总分恒为 1.0，按绝对分数做的阈值过滤会全部放行", "融合结果会变成负数", "BM25 会失效"],
                   1, "1.0 表示「都满分」。如果下游用 `score > 0.8` 过滤，这种没有区分度的结果会被全部保留，反而把噪声放进来。"),
            judge("分数级融合之前不归一化也能工作，只要把 alpha 调小一点就行。", 0,
                  "错。余弦分在 0~1、BM25 可能到十几，量纲差一个数量级，alpha 再怎么调也压不住，实际退化成纯 BM25。"),
        ],
    ),
    "rag-rerank": used(
        "core/reranker.py", "33-47",
        '''    def rerank(self, query: str, docs: list, top_n: int = None,
               max_chars: int = None) -> list:
        """
        对检索结果重排序
        Args:
            query: 查询文本
            docs: [(text, source, score), ...]
            top_n: 返回 TopN，默认 RERANK_TOP
            max_chars: 参与打分的单篇字符上限（默认 RERANK_DOC_MAX_CHARS）。
                       CrossEncoder 耗时随输入长度近似线性增长，CPU 上 6 篇 1000 字
                       需 10s+、4 篇 200 字仅约 2.5s；相关性主要由片段开头决定，
                       因此只截断"打分用文本"，返回的仍是完整原文（供 LLM 生成）。''',
        "`RerankerEngine.rerank()`，用 BAAI/bge-reranker-v2-m3 做交叉编码器精排。",
        "这段注释把课程里「交叉编码器很贵」从一句口号变成了具体数字：**6 篇 1000 字要 10 秒以上，"
        "4 篇 200 字只要 2.5 秒** —— CPU 上耗时随输入长度近似线性增长。所以项目做了一个很聪明的取舍："
        "截断「**打分用的文本**」，但返回给 LLM 的仍是**完整原文**。理由是相关性主要由片段开头决定，"
        "后面的细节不影响「这段讲的是不是票价」这个判断，但会影响 LLM 生成时的信息完整度。"
        "这就是课程说的「候选集大小和输入长度是两个独立的成本旋钮」。",
        [
            choice("项目只对「打分用文本」截断、返回完整原文，主要理由是什么？",
                   ["截断能提高精排准确率", "相关性主要由片段开头决定，截断能大幅降延迟且不损失生成所需信息", "完整原文没法过模型", "为了省存储"],
                   1, "打分只需要判断「讲的是不是这件事」，开头足够；生成需要全部细节。两个用途用两份文本，各取所需。"),
            judge("把精排候选从 20 条加到 200 条，召回会明显提升，延迟基本不变。", 0,
                  "错。交叉编码器是逐条前向，成本随候选数线性增长。20→200 意味着 10 倍耗时，而召回提升通常很有限，因为粗排已经把大部分好文档捞进来了。"),
        ],
    ),
    "rag-embedding": used(
        "core/embedding.py", "26-33",
        '''    @property
    def model(self):
        if self._model is None:
            self._model = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={"device": EMBEDDING_DEVICE},
                encode_kwargs={"normalize_embeddings": True}
            )
        return self._model''',
        "`EmbeddingEngine.model`，全项目所有向量化都从这里出（`embed_query` / `embed_documents`）。",
        "`normalize_embeddings=True` 就是课程强调的那一步，而且**放在了编码器配置里**，"
        "而不是每次调用完手动除模长 —— 这样入库和查询天然用同一套规则，不会出现"
        "「入库归一化了、查询忘了归一化」这种隐蔽 bug。"
        "另外注意它是 `@property` + 懒加载单例：模型只在第一次真正用到时加载，"
        "避免服务启动就卡在几个 GB 的权重加载上。`EMBEDDING_DIM` 在 `config.py` 里，"
        "必须和 Milvus collection 的 `dim` 严格一致，换模型就要重建集合。",
        [
            choice("`normalize_embeddings=True` 写在编码器配置里、而不是调用后手动归一化，好处是什么？",
                   ["速度更快", "入库和查询走同一套规则，不会漏掉某条路径", "能自动降低维度", "支持多语言"],
                   1, "手动归一化容易在某个分支漏掉，一旦入库和查询规则不一致，内积分数就失去意义。写进配置是「默认正确」。"),
            judge("换一个更强的 embedding 模型，只要维度一样，就不用重建 Milvus 索引。", 0,
                  "错。不同模型的向量空间不可比，维度相同也不行。换了模型必须重新编码全部文档，否则新旧向量混在一个空间里，检索结果会乱掉。"),
        ],
    ),
    "rag-vector-db": used(
        "core/vector_store.py", "33-46",
        '''            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=200)
            ]
            schema = CollectionSchema(fields=fields, description="Amusement Park Knowledge Base")
            self._collection = Collection(COLLECTION_NAME, schema)
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "IP",
                "params": {"nlist": 128}
            }''',
        "`VectorStore._ensure_connected()`，首次调用时才 `connections.connect()` 并建集合。",
        "这条把课程里几个抽象概念全对上了：**index_type = IVF_FLAT**（聚成 nlist 个桶，"
        "查询时只搜最近的 nprobe 个桶）、**metric_type = IP**（因为 embedding 已经归一化，"
        "内积就等于余弦）、**dim = EMBEDDING_DIM**（必须和模型输出维度一致，否则建索引直接报错）。"
        "`nlist=128` 是桶数，`nprobe` 不在建索引时定、而在**查询时**传 —— 这正是课程强调的"
        "「精度与延迟的旋钮」。另外 schema 只存 `text/vector/source` 三个业务字段，没有存 chunk_id："
        "Milvus 的 `auto_id=True` 会自己生成主键，够用了。",
        [
            choice("项目建索引用 `IVF_FLAT` + `nlist=128` + `metric_type=IP`，这套组合说明什么？",
                   ["向量没有归一化，所以用内积", "向量已归一化（IP 等价余弦），并用聚类分桶做近似检索", "数据量太小，用不了 HNSW", "索引类型和度量方式无关"],
                   1, "IP 能直接用是因为 embedding 归一化了；IVF_FLAT 是聚类分桶，查询时用 nprobe 控制搜几个桶。"),
            judge("`nprobe` 是在 `create_index` 时指定的，建完索引就不能改。", 0,
                  "错。nprobe 是**查询参数**（search 时传），可以按请求动态调；nlist 才是建索引时定的。"),
        ],
    ),
    "rag-ingest": absent(
        '''# 2. 清空旧集合（旧索引只有10篇旧chunk，与新知识库不一致）
_ = vector_store.collection  # 先触发连接
vector_store.drop_collection()
print("旧 Milvus 集合已清除")

# 3. 批量向量化 + 入库''',
        "`rebuild_index.py` —— 项目现在的入库方式是「删集合 → 全量重新编码」，脚本第一行写明是「临时脚本」。",
        "课程讲的是「指纹比对 + 增量更新」，**项目这块还没做**，用的是最朴素的全量重建："
        "`drop_collection()` 之后把所有 chunk 重新向量化入库。25 个 chunk 时这没问题，"
        "但知识库涨到几千条，每次改一篇文档都要把全部内容重新编码一遍。"
        "缺的正是课程里那三步：① 给每篇文档算内容指纹；② 指纹没变就跳过；"
        "③ 按 doc_id「先删后插」保证幂等。另一个隐患是 `drop_collection()` 期间库是空的，"
        "如果这时有用户提问，检索会拿到零结果 —— 生产环境必须改成「双集合切换」或增量写。",
        [
            choice("项目当前的全量重建方式，在知识库变大后最主要的问题是什么？",
                   ["向量维度会变", "改一篇文档要重新编码全部内容，且重建期间检索结果为空", "Milvus 不支持删除集合", "无法使用 IP 度量"],
                   1, "全量重建的成本随文档数线性增长，而且 drop 到重建完成之间有一段「空窗期」，线上会查到空结果。"),
            judge("全量重建虽然慢，但至少能保证没有重复 chunk。", 0,
                  "错。全量重建确实不会重复（因为先删了集合），但代价是所有文档重新编码，且重建期间服务不可用。正确方向是增量 + 幂等。"),
        ],
    ),
    "rag-dedup": used(
        "services/kb_dedup.py", "125-133",
        '''def dedup_key(text: str) -> str:
    """去重键：块主问题的归一化结果（**剥掉编号前缀**）。

    剥掉 Qn./1.1/一、 这类编号是必须的 —— 同一个问题在不同文档里编号不同
    （B 的 `## Q8. 园区允许带宠物入园吗` 与 C 的 `## Q1. 园区允许带宠物入园吗`），
    不剥就永远判不成同一个问题。检索侧兜底去重直接用它。
    """
    return normalize_question(_NUM_PREFIX_RE.sub("", question_of(text)).strip())''',
        "`services/kb_dedup.py` 的 `dedup_key()`，另有 `vector_candidates()` 做语义级候选召回。",
        "这条补上了课程里没讲到的一个真实细节：**归一化不只要去空白标点，还要剥掉编号前缀**。"
        "同一个问题在 B 文档里是 `Q8.`、在 C 文档里是 `Q1.`，不剥编号，两个字符串永远不相等，"
        "精确去重直接失效。项目是「归一化哈希」这一档（不是纯 md5），再加上 `vector_candidates()` "
        "做语义召回 —— 也就是课程说的**两级去重**：先用便宜的字符串归一化挡掉大部分，"
        "再用向量余弦兜住改写版本。注释里还写了一个容易被忽略的工程点："
        "去重索引不靠 TTL 过期，而靠知识库变更后的显式 `invalidate_cache()`，"
        "因为重建要 8~20 秒，绝不能出现在问答热路径上。",
        [
            choice("`dedup_key()` 为什么要剥掉 `Q8.` / `一、` 这类编号前缀？",
                   ["减少字符串长度", "同一问题在不同文档里编号不同，不剥就永远判不成重复", "编号会影响向量维度", "防止 SQL 注入"],
                   1, "去重比的是「问题内容」。编号是文档排版产物，同一问题换个文档就变，必须剥掉才能对齐。"),
            judge("知识库去重只要做精确哈希就够了，语义去重是过度设计。", 0,
                  "错。用户/运营改写一句话就换一个哈希，精确哈希会漏掉大量真实重复。项目是「归一化哈希 + 语义候选」两级并用。"),
        ],
    ),
}
