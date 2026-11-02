# -*- coding: utf-8 -*-
"""数据分析与处理 / Transformer / RAG 检索工程：14 个分支的知识点与标准答案。

数据来源：原 learn_mindmap.py 的考点树 + 人工补写的 kp / answer。
每条 = 一个面试考点：
    name   考官的问法（面试考题页的题干）
    kp     浓缩成名词的知识点标签（思维导图页的节点）
    answer 40~80 字的标准答案，能落到鸭先知项目的地方直接带项目细节
    code   对应的站内课程，None 表示「会考但站内还没课」
    hot    3 必问 / 2 常问 / 1 纵深

⚠️ 改完跑 `python learn_mindmap_check.py`：它会校验 code 是否存在、
答案长度、kp 是否为空，退出码 0 才算过。
"""

TREES: dict[str, dict] = {
    "数据分析与处理": {
        "intro": 'AI 岗考这块不是考你会不会画图，是考「脏数据交给你能不能收敛成结论」，以及 Pandas 里那几个经典的坑（链式赋值、SettingWithCopy、groupby 的索引）。',
        "branches": [
            {
                "name": 'NumPy 与向量化',
                "items": [
                {"name": 'ndarray 与 list 的性能差从哪来', "kp": 'ndarray vs list', "code": 'da-01', "hot": 3,
                 "answer": 'ndarray 是同类型连续内存加 C 层循环，list 是指针数组；numpy 快在省掉解释器开销和类型检查，还能走 SIMD。'},
                {"name": '广播机制的规则，形状不匹配怎么补', "kp": '广播规则', "code": 'da-01', "hot": 3,
                 "answer": '从最后一维往前比，维度相等或有一方是 1 就能广播，否则报错；补维度用 reshape 或 None 索引。'},
                {"name": '视图与副本：切片赋值会不会改原数组', "kp": '视图与副本', "code": 'da-01', "hot": 3,
                 "answer": '切片返回视图，改它会改原数组；花式索引和布尔索引返回副本。要彻底断开就用 .copy()。'},
                {"name": '花式索引、布尔索引、np.where 的用法', "kp": '花式/布尔/where', "code": 'da-01', "hot": 2,
                 "answer": '`a[[0,2]]` 按位置取，`a[a>0]` 按条件筛，`np.where(cond,x,y)` 是向量化三元表达式，都比 for 循环快。'},
                {"name": '为什么循环里逐元素算比向量化慢两个数量级', "kp": '为什么循环慢', "code": 'da-01', "hot": 2,
                 "answer": '每次迭代都要建 Python 对象、做类型检查和派发；numpy 把整段计算交给 C 循环还能用 SIMD，差两个数量级很正常。'},
                ],
            },
            {
                "name": 'Pandas 核心操作',
                "items": [
                {"name": 'Series 与 DataFrame 的索引对齐机制', "kp": '索引对齐', "code": 'da-02', "hot": 3,
                 "answer": '运算按索引对齐，不是按位置；索引不一致会产出 NaN。要按位置算就 reset_index 或取 .values。'},
                {"name": 'loc、iloc、at、iat 的区别，什么时候用哪个', "kp": 'loc/iloc/at/iat', "code": 'da-02', "hot": 3,
                 "answer": 'loc 按标签、iloc 按位置；at/iat 是取单个值的快速版。切片时 loc 含右端，iloc 不含。'},
                {"name": 'SettingWithCopyWarning 到底在警告什么', "kp": 'SettingWithCopy', "code": 'da-02', "hot": 3,
                 "answer": "链式索引可能改的是临时副本，pandas 判断不了就警告。用 `df.loc[mask, 'b'] = 1` 一次写完。"},
                {"name": 'apply 与 map 与 vectorized 操作怎么选', "kp": 'apply/map/向量化', "code": 'da-05', "hot": 2,
                 "answer": '优先向量化表达式，其次 map（逐元素），apply 最慢（逐行走 Python）。必须 apply 就加 raw=True。'},
                {"name": 'merge 的四种连接方式与索引重置', "kp": 'merge 四种连接', "code": 'da-06', "hot": 3,
                 "answer": 'inner 交集、left 保左、right 保右、outer 并集；没匹配的补 NaN，合并后索引会重置，要自己 set_index。'},
                {"name": 'pivot_table、melt、stack/unstack 的转换关系', "kp": 'pivot/melt/stack', "code": 'da-06', "hot": 2,
                 "answer": 'pivot 长表转宽表，melt 宽转长，stack/unstack 在行列与索引层级之间转。三者本质是同一种 reshape。'},
                ],
            },
            {
                "name": '脏数据处理',
                "items": [
                {"name": '读 CSV 时编码、分隔符、列类型错乱怎么处理', "kp": '读 CSV 出错', "code": 'da-03', "hot": 3,
                 "answer": '先试 utf-8 再试 gbk；分隔符用 sep 指定或 sep=None 让引擎猜；列类型错乱就 dtype=str 全读进来再自己转。'},
                {"name": '缺失值该删、该填还是该标记，判断依据是什么', "kp": '缺失值处理', "code": 'da-04', "hot": 3,
                 "answer": '看缺失比例和机制：随机缺失可填均值/中位数，有成因就单独标记一列，超过 60% 且无信息直接删列。'},
                {"name": '重复值判定为什么不能只按主键', "kp": '重复值判定', "code": 'da-04', "hot": 2,
                 "answer": '主键重复不代表业务重复，要按业务唯一键（用户+日期+商品）判重；去重前先排序保留最新一条。'},
                {"name": '异常值用 3σ 还是 IQR，业务上要不要保留', "kp": '异常值 3σ/IQR', "code": 'da-04', "hot": 3,
                 "answer": '3σ 假设近似正态，IQR 更稳不受极端值影响。业务上先判断是不是真实事件（大客户下单），别一删了之。'},
                {"name": '时间字段解析、时区与重采样', "kp": '时间字段', "code": 'da-07', "hot": 2,
                 "answer": "统一转 datetime 并显式指定时区，跨时区比较先转 UTC；重采样用 resample('D').agg(...)，注意闭区间和标签位置。"},
                {"name": 'groupby 之后索引变成多层怎么拍平', "kp": 'groupby 多层索引', "code": 'da-05', "hot": 2,
                 "answer": '加 as_index=False 直接出列，或事后 reset_index()；多聚合时列名是 MultiIndex，用 agg 命名元组拍平。'},
                ],
            },
            {
                "name": '分析与结论产出',
                "items": [
                {"name": '拿到一份陌生数据，先看哪几个指标', "kp": '陌生数据先看什么', "code": 'da-03', "hot": 3,
                 "answer": '先看行数、字段类型、缺失率、唯一值数，再看核心指标的量级和分布，最后确认时间范围和统计口径。'},
                {"name": '相关性不等于因果，怎么避免下错结论', "kp": '相关不等于因果', "code": 'da-08', "hot": 3,
                 "answer": '可能有第三变量、反向因果或选择偏差。要证因果得做 A/B 或断点回归，观察数据只能提假设。'},
                {"name": '图表选型：趋势、对比、分布、占比各用什么图', "kp": '图表选型', "code": 'da-08', "hot": 2,
                 "answer": '趋势用折线，对比用柱状，分布用直方图/箱线图，占比用堆叠柱或饼图（类别少于 5 个），关系用散点。'},
                {"name": '分析报告怎么组织才让人看得懂结论', "kp": '报告结构', "code": 'da-08', "hot": 2,
                 "answer": '先给结论和行动建议，再给支撑证据和口径，最后放明细与局限。别让人翻到最后才知道你想说什么。'},
                ],
            },
        ],
    },
    "Transformer": {
        "intro": 'AI Agent 岗必考，但深度有差别：应用岗要能讲清注意力怎么算、为什么除 √d、KV Cache 省了什么；算法岗还会问位置编码外推和 FlashAttention。',
        "branches": [
            {
                "name": '注意力机制',
                "items": [
                {"name": 'RNN 的序列依赖问题，Attention 怎么解决', "kp": 'RNN 的序列依赖', "code": 'tf-01', "hot": 3,
                 "answer": 'RNN 必须串行，长距离信息在反复相乘中衰减，也没法并行。Attention 让任意两个位置直连，路径长度变成 1。'},
                {"name": 'Q/K/V 分别是什么，为什么叫 Query 和 Key', "kp": 'Q/K/V 是什么', "code": 'tf-02', "hot": 3,
                 "answer": 'Q 是「我在找什么」，K 是「我有什么标签」，V 是「我能给的内容」；Q·K 算相关性权重，再对 V 加权求和。'},
                {"name": 'Self-Attention 的计算公式，矩阵维度怎么变', "kp": 'Self-Attention 公式', "code": 'tf-02', "hot": 3,
                 "answer": '`softmax(QKᵀ/√d_k)V`：Q、K、V 都是 [n,d]，QKᵀ 得 [n,n] 注意力矩阵，再乘 V 回到 [n,d]。'},
                {"name": '为什么除以 √d_k，不除会怎样', "kp": '为什么除 √d_k', "code": 'tf-03', "hot": 3,
                 "answer": '维度越大点积方差越大，softmax 会被推到极端饱和、梯度接近 0；除 √d_k 把方差拉回 1。'},
                {"name": 'Softmax 的数值稳定性，为什么要减最大值', "kp": 'Softmax 数值稳定', "code": 'tf-03', "hot": 2,
                 "answer": 'exp 大数会溢出，先减去该行最大值再 exp，结果不变但不会 inf；分母同样处理。'},
                {"name": '注意力的复杂度 O(n²d)，长文本怎么缓解', "kp": '复杂度 O(n²d)', "code": 'tf-03', "hot": 3,
                 "answer": '注意力矩阵是 n×n。长文本靠滑动窗口、稀疏注意力、分块或线性近似；RAG 则是从源头减少 n。'},
                ],
            },
            {
                "name": '模型结构',
                "items": [
                {"name": '多头注意力为什么要拆成多个头', "kp": '多头注意力的意义', "code": 'tf-04', "hot": 3,
                 "answer": '单头只能学一种相关性，多头在不同子空间并行学语法、指代、位置等关系，拼起来表达更丰富。'},
                {"name": '多头之间怎么拼接，参数量和单头比差多少', "kp": '多头怎么拼接', "code": 'tf-04', "hot": 2,
                 "answer": 'd_model 拆成 h 份、每份 d_k=d_model/h，各自算完 concat 回 d_model 再过 W_o；总参数量和单头同维度基本持平。'},
                {"name": '位置编码为什么必需，正弦编码与可学习编码的区别', "kp": '位置编码', "code": 'tf-05', "hot": 3,
                 "answer": 'Attention 对顺序无感，打乱词序结果不变，所以必须注入位置。正弦编码固定可外推，可学习编码灵活但受限于训练长度。'},
                {"name": 'RoPE 相对位置编码的原理，为什么成了主流', "kp": 'RoPE', "code": 'tf-05', "hot": 3,
                 "answer": '把 q/k 按二维子空间旋转，旋转角随位置变化，点积自然只依赖相对距离；调旋转底数还能做长度外推，所以成了主流。'},
                {"name": '残差连接与 LayerNorm 各解决什么问题', "kp": '残差与 LayerNorm', "code": 'tf-06', "hot": 3,
                 "answer": '残差让梯度有直连通路、缓解深层退化；LayerNorm 归一化每个 token 的特征维度，稳定分布、加速收敛。'},
                {"name": 'Pre-LN 与 Post-LN 的差别，训练稳定性', "kp": 'Pre-LN 与 Post-LN', "code": 'tf-06', "hot": 2,
                 "answer": 'Post-LN 是原始结构但深层要 warmup 才稳；Pre-LN 把 norm 放子层前，梯度更稳可省 warmup，代价是表达略弱。'},
                {"name": 'Encoder-Decoder、Decoder-only、Encoder-only 怎么选', "kp": '三种架构怎么选', "code": 'tf-06', "hot": 3,
                 "answer": 'Encoder-only（BERT）适合理解分类，Decoder-only（GPT）适合生成且易扩展，Encoder-Decoder（T5）适合翻译类序列到序列。'},
                ],
            },
            {
                "name": '预训练与模型选型',
                "items": [
                {"name": 'BERT 与 GPT 的架构和训练目标差异', "kp": 'BERT vs GPT', "code": 'tf-07', "hot": 3,
                 "answer": 'BERT 是双向编码器、用 MLM 掩码预测，擅长理解；GPT 是单向解码器、预测下一个词，擅长生成。'},
                {"name": 'MLM、CLM、Seq2Seq 三种预训练目标', "kp": '三种预训练目标', "code": 'tf-07', "hot": 3,
                 "answer": 'MLM 挖空填词（双向），CLM 预测下一个词（单向），Seq2Seq 用编码器读输入、解码器生成输出。'},
                {"name": '为什么现在大模型几乎都是 Decoder-only', "kp": 'Decoder-only 为主流', "code": 'tf-07', "hot": 3,
                 "answer": '一个 CLM 目标就能同时学理解和生成，结构简单、scaling 好，in-context learning 也更强；双向注意力反而不利于自回归。'},
                {"name": '参数量、上下文长度、词表大小怎么权衡', "kp": '参数/上下文/词表', "code": 'tf-07', "hot": 2,
                 "answer": '参数决定容量和成本，上下文决定一次能看多少，词表大则 embedding 占比高、中文覆盖好但输出层更贵。'},
                {"name": 'Embedding 模型和生成模型能混用吗', "kp": 'Embedding 与生成模型', "code": 'rag-embedding', "hot": 2,
                 "answer": '能配合但别混用：embedding 模型输出向量做检索，生成模型输出文本；拿生成模型隐状态当向量通常不如专用 embedding。'},
                ],
            },
            {
                "name": '推理与加速',
                "items": [
                {"name": 'KV Cache 缓存了什么，为什么能省算力', "kp": 'KV Cache', "code": 'tf-08', "hot": 3,
                 "answer": '自回归每步都要和历史做注意力，把已算过的 K、V 缓存下来就不必重算，每步从 O(n²) 降到 O(n)。'},
                {"name": 'KV Cache 显存怎么估算，长上下文为什么爆显存', "kp": 'KV Cache 显存', "code": 'tf-08', "hot": 3,
                 "answer": '约 2×层数×头数×head_dim×序列长度×batch×字节数；随长度线性涨，所以长上下文最先爆的是显存不是算力。'},
                {"name": 'prefill 与 decode 两阶段的瓶颈差异', "kp": 'prefill 与 decode', "code": 'tf-08', "hot": 3,
                 "answer": 'prefill 一次并行处理整个 prompt，算力密集；decode 每步只出一个 token，反复读权重和 KV，显存带宽密集。'},
                {"name": '量化 INT8 / INT4 损失在哪，什么场景能用', "kp": '量化损失', "code": None, "hot": 2,
                 "answer": 'INT8 基本无损，INT4 对权重还行、对激活更敏感；通用对话可上 4bit，数学和长链推理建议 8bit 或做 AWQ/GPTQ 校准。'},
                {"name": '投机采样、PagedAttention 各自优化什么', "kp": '投机采样/PagedAttention', "code": None, "hot": 2,
                 "answer": '投机采样用小模型草拟多 token、大模型一次校验，提吞吐；PagedAttention 把 KV 按页管理，消碎片、提并发。'},
                {"name": '温度、top_p、top_k 采样参数怎么影响输出', "kp": '采样参数', "code": 'ai-llm-api', "hot": 3,
                 "answer": '温度低更确定，top_p 截概率长尾，top_k 只留前 k 个；一般只调温度或 top_p 一个，两个都调会双重收紧。'},
                ],
            },
        ],
    },
    "RAG 检索工程": {
        "intro": '这是 AI Agent 岗区分度最高的一科。面试官会从一个具体故障切入：「检索结果不对，你怎么定位是分块、召回还是精排的问题」，答得出链路就赢了。',
        "branches": [
            {
                "name": '分块与预处理',
                "items": [
                {"name": '固定长度切分为什么不能直接用，标题层级切分好在哪', "kp": '定长切分 vs 标题切分', "code": 'rag-chunk', "hot": 3,
                 "answer": '定长切分会把一句话、一张表切断，语义残缺；按标题层级切能保住「这一节在讲什么」，超长段落再二次切。'},
                {"name": 'chunk size 和 overlap 怎么定，多大会丢语义', "kp": 'chunk size / overlap', "code": 'rag-chunk', "hot": 3,
                 "answer": '按语义单元定大小（中文 300~600 字），overlap 取 10~15% 防止边界切断；太大稀释相关性，太小丢上下文。'},
                {"name": '表格、代码块、公式怎么单独处理', "kp": '表格/代码/公式', "code": 'rag-chunk', "hot": 2,
                 "answer": '表格转成「表头 + 每行一句」的结构化文本，代码按函数切并保留语言标记，公式转 LaTeX 并保留上下文说明。'},
                {"name": '中文分词为什么不能只用空格，jieba 自定义词典解决什么', "kp": '中文分词', "code": 'rag-tokenize', "hot": 3,
                 "answer": '中文没有空格，按空格切等于没切；jieba 加自定义词典能把「向量数据库」「召回率」这类领域词当成一个词。'},
                {"name": '分块粒度与召回粒度的矛盾，parent-child 检索', "kp": '分块与召回粒度矛盾', "code": None, "hot": 3,
                 "answer": '小块召回准但上下文碎，大块上下文全但噪声多。parent-child：用小块建索引召回，返回它所属的大块给模型。'},
                {"name": 'PDF 解析出来的文本乱序怎么修', "kp": 'PDF 文本乱序', "code": 'mm-ocr', "hot": 2,
                 "answer": '多栏和页眉页脚会让阅读顺序错乱。按坐标做版面分析重排、去掉页眉页脚，再按栏切分，必要时走 OCR。'},
                ],
            },
            {
                "name": '检索算法',
                "items": [
                {"name": 'BM25 的打分公式，k1 和 b 各控制什么', "kp": 'BM25 公式', "code": 'rag-bm25', "hot": 3,
                 "answer": '`score = Σ IDF(qi)·tf(k1+1)/(tf + k1(1-b+b·dl/avgdl))`；k1 控词频饱和速度，b 控长度归一强度。'},
                {"name": '稀疏检索与稠密检索各自的强项和盲区', "kp": '稀疏 vs 稠密', "code": 'rag-hybrid', "hot": 3,
                 "answer": '稀疏（BM25）精确匹配强、可解释、不用训练，但不认同义词；稠密（向量）认语义，却对专有名词和数字不敏感。'},
                {"name": '为什么必须做混合检索，什么 query 只有 BM25 能救', "kp": '为什么做混合检索', "code": 'rag-hybrid', "hot": 3,
                 "answer": '查型号、报错码、人名这类只有 BM25 能精确命中，语义模型会当近义词糊过去；鸭先知的文档检索就是 BM25 + 向量双路召回再融合。'},
                {"name": 'Embedding 模型的选型依据，维度越高越好吗', "kp": 'Embedding 选型', "code": 'rag-embedding', "hot": 3,
                 "answer": '看语言、领域和检索粒度，不是维度越高越好；要在自己的评测集上比 Recall@K，中文可选 bge/m3e 系列。'},
                {"name": '向量归一化与余弦相似度、内积的关系', "kp": '归一化与相似度', "code": 'rag-embedding', "hot": 3,
                 "answer": '归一化后内积等于余弦相似度；不归一化时内积受模长影响，长文档更容易高分，所以一般先归一化再建索引。'},
                {"name": 'Recall@K、MRR、NDCG 分别衡量什么', "kp": 'Recall@K/MRR/NDCG', "code": None, "hot": 3,
                 "answer": 'Recall@K 看前 K 有没有正确文档，MRR 看第一个正确结果排多前，NDCG 还考虑多个结果的位置和分级相关性。'},
                ],
            },
            {
                "name": '融合与精排',
                "items": [
                {"name": 'RRF 倒数排名融合为什么比加权分数稳', "kp": 'RRF', "code": 'rag-hybrid', "hot": 3,
                 "answer": '`score = Σ 1/(k+rank)`，只用排名不用分数，所以能合并量纲完全不同的多路结果，k 一般取 60。'},
                {"name": '交叉编码器 Reranker 为什么比双塔准，代价在哪', "kp": '交叉编码器 Reranker', "code": 'rag-rerank', "hot": 3,
                 "answer": '把 query 和文档拼一起过模型，有词级交互所以更准；代价是不能预计算，每对都要跑一次前向，只能精排少量候选。'},
                {"name": '召回 top50 再精排到 top4，参数怎么调', "kp": 'top50 到 top4', "code": 'rag-rerank', "hot": 3,
                 "answer": '先保证召回够（top50 覆盖答案），再精排压到 4 条控 token；只看 4 条召回不够，全给 50 条噪声太多还贵。'},
                {"name": '精排模型和 LLM 直接打分怎么选', "kp": '精排模型 vs LLM 打分', "code": 'rag-rerank', "hot": 2,
                 "answer": '专用 reranker 快且稳定，适合线上；LLM 打分更懂语义但慢且贵，适合离线评估或少量重排。'},
                {"name": '多路召回结果怎么去重合并', "kp": '多路去重合并', "code": 'rag-hybrid', "hot": 2,
                 "answer": '先按文档 id 去重，再按内容哈希或相似度阈值去近似重复；合并时保留各路排名做 RRF，别直接拼列表。'},
                ],
            },
            {
                "name": '向量库与索引',
                "items": [
                {"name": 'HNSW 的分层图结构，ef 和 M 参数影响什么', "kp": 'HNSW 参数', "code": 'rag-vector-db', "hot": 3,
                 "answer": 'M 控每节点连边数（越大越准越占内存），efConstruction 控建索引搜索宽度，efSearch 控查询候选数，越大越准越慢。'},
                {"name": 'IVF、PQ 量化牺牲了什么换来了内存', "kp": 'IVF / PQ', "code": 'rag-vector-db', "hot": 2,
                 "answer": 'IVF 先聚类只搜最近的几个簇，PQ 把向量分段量化成码本编号，用精度换内存和速度，召回掉了要重排补。'},
                {"name": 'Milvus 的 collection、partition、segment 概念', "kp": 'Milvus 概念', "code": 'rag-vector-db', "hot": 2,
                 "answer": 'collection 相当于表，partition 是按业务切的物理分组（可缩小检索范围），segment 是底层数据段，写入先 growing 再 compact。'},
                {"name": '暴力检索在什么数据量下反而更合适', "kp": '暴力检索何时更合适', "code": 'rag-vector-db', "hot": 2,
                 "answer": '数据量小（几万条以内）或要求 100% 召回时，flat 检索延迟也能接受，还省了建索引和调参。'},
                {"name": '元数据过滤和向量检索怎么组合才不丢召回', "kp": '元数据过滤组合', "code": 'rag-vector-db', "hot": 3,
                 "answer": '先过滤再检索可能把 ANN 候选全滤掉导致召回暴跌；用带过滤能力的索引，或过滤后不足时补检索。'},
                ],
            },
            {
                "name": '数据治理与入库',
                "items": [
                {"name": '文档入库流水线有哪几步，哪步最容易出问题', "kp": '入库流水线', "code": 'rag-ingest', "hot": 3,
                 "answer": '解析 → 清洗去噪 → 分块 → 元数据抽取 → 向量化 → 入库；最容易出问题的是解析和分块，脏文本进去后面全白搭。'},
                {"name": '增量更新怎么保证不重不漏，幂等键怎么设计', "kp": '增量与幂等', "code": 'rag-ingest', "hot": 3,
                 "answer": '用「文档 id + 内容哈希 + 分块序号」做幂等键，写入用 upsert；先写新版本再删旧版本，避免中途失败丢数据。'},
                {"name": '去重的三层：哈希、归一化、语义阈值', "kp": '三层去重', "code": 'rag-dedup', "hot": 3,
                 "answer": '先哈希完全相同，再归一化（去空白、统一标点）比对，最后向量相似度超阈值判语义重复；阈值要按领域调。'},
                {"name": '文档删除了，向量库怎么同步删除', "kp": '删除同步', "code": 'rag-ingest', "hot": 2,
                 "answer": '向量库按文档 id 批量删对应分块，删除任务也落表以便重试；Milvus 用 delete 表达式按 metadata 过滤删。'},
                {"name": '知识库更新后旧答案还在，是缓存还是索引问题', "kp": '更新后旧答案还在', "code": 'rag-ingest', "hot": 2,
                 "answer": '先查缓存是否含旧文档，再查索引是否删干净，最后看是不是上下文里残留了旧片段。'},
                ],
            },
            {
                "name": '效果归因与调优',
                "items": [
                {"name": '答案不对，怎么判断是检索问题还是生成问题', "kp": '检索问题还是生成问题', "code": 'ai-eval', "hot": 3,
                 "answer": '看引用：片段里有正确答案却答错是生成问题；片段里根本没答案是检索问题。先看 top-k 命中率再谈 prompt。'},
                {"name": '怎么构造一套不泄漏的评测集', "kp": '不泄漏的评测集', "code": 'ai-eval', "hot": 3,
                 "answer": '从真实提问里抽样改问法，确保答案只在目标文档里出现；换人出题，跑之前不调 prompt，否则是自己考自己。鸭先知用 28 题零泄漏集。'},
                {"name": '召回率上不去，按什么顺序排查', "kp": '召回率排查顺序', "code": None, "hot": 3,
                 "answer": '按「分词 → 切块 → embedding → 索引 → 过滤条件 → 融合权重」查：先看 gold 文档在不在库里，再看它排第几。'},
                {"name": 'query 改写与 HyDE 什么时候有用', "kp": 'query 改写与 HyDE', "code": None, "hot": 2,
                 "answer": 'query 太短、口语化、多轮指代时改写有用；HyDE 让模型先编一段假答案再检索，适合抽象问题，但会引入幻觉风险。'},
                ],
            },
        ],
    },
}
