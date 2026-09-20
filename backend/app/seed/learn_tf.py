"""Transformer：注意力机制、模型结构与推理优化。

按"从原理到工程"的顺序编排，关键机制用手写 Python 实现来验证理解。
"""

TF03_CHECKER = """
try:
    assert callable(softmax), "要定义一个叫 softmax 的函数"
    p = softmax([1, 1, 1])
    assert isinstance(p, list) and len(p) == 3, "softmax 要返回一个和输入等长的列表，softmax([1, 1, 1]) 应该返回 3 个数"
    assert abs(sum(p) - 1.0) < 1e-9, "softmax([1, 1, 1]) 的三个权重加起来应该是 1，检查是不是忘了除以指数之和"
    assert all(abs(v - 1 / 3) < 1e-9 for v in p), "softmax([1, 1, 1]) 三项应该完全相等，每个都是 0.3333…，现在得到的是 " + str(p)

    big = softmax([1000.0, 1000.0, 1000.0])
    assert all(abs(v - 1 / 3) < 1e-9 for v in big), "softmax([1000, 1000, 1000]) 也应该返回三个 1/3 —— 要先减去最大值再取 exp，否则 exp(1000) 会直接溢出"

    order = softmax([0.0, 1.0, 2.0])
    assert order[0] < order[1] < order[2], "softmax 要保持大小关系：输入是 2 的那一项，权重必须比输入是 0 的大"

    s1 = scaled_scores([[1.0, 1.0]], [[1.0, 1.0]])
    assert isinstance(s1, list) and isinstance(s1[0], list), "scaled_scores 要返回二维列表，形状是 (len(Q), len(K))"
    assert abs(s1[0][0] - 2 ** 0.5) < 1e-9, "scaled_scores([[1,1]], [[1,1]]) 应该是 2 / sqrt(2) = 1.4142…；如果得到 2.0，说明分母写成了 d_k 而不是 sqrt(d_k)"
    s2 = scaled_scores([[3.0, 4.0]], [[3.0, 4.0], [4.0, 3.0]])
    assert abs(s2[0][0] - 25 / 2 ** 0.5) < 1e-9, "换一组输入验一遍：dot([3,4], [3,4]) = 25，除以 sqrt(2) 应该得到 17.6776…"
    assert abs(s2[0][1] - 24 / 2 ** 0.5) < 1e-9, "第二个 key 的点积是 3*4 + 4*3 = 24，除以 sqrt(2) 应该是 16.9705…，检查是不是只算了第一个 key"

    o0 = attention([[1.0, 2.0]], [[1.0, 2.0]], [[5.0, 6.0]])
    assert isinstance(o0, list) and isinstance(o0[0], list) and len(o0[0]) == 2, "attention 的输出形状要和 V 一致：(len(Q), len(V[0]))"
    assert abs(o0[0][0] - 5.0) < 1e-9 and abs(o0[0][1] - 6.0) < 1e-9, "只有一个 key 时权重必然是 1，输出应该原样等于 V，也就是 [5.0, 6.0]"

    Q = [[1.0, 0.0]]
    O1 = attention(Q, [[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.0], [0.0, 1.0]])
    assert abs(O1[0][0] + O1[0][1] - 1.0) < 1e-9, "当 V 的两行是 [1,0] 和 [0,1] 时，两个权重相加应该等于 1（每行 softmax 归一化）"
    assert O1[0][0] > O1[0][1], "query [1,0] 和 key [1,0] 更相关，所以第一列的权重应该更大"
    assert abs(O1[0][1] - 0.3302384506733431) < 1e-6, "这一组结果应该是 [0.6698, 0.3302]；如果得到 [0.7311, 0.2689]，就是 scores 忘了除以 sqrt(d_k)"

    O2 = attention([[0.0, 1.0]], [[1.0, 0.0], [0.0, 1.0]], [[10.0, 0.0], [0.0, 20.0]])
    assert O2[0][1] > O2[0][0], "换一组输入：query 换成 [0,1]，这次应该和第二个 key 更相关，第二列权重更大 —— 检查是不是把 query 写死了"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

TF04_CHECKER = """
try:
    assert callable(split_heads) and callable(merge_heads) and callable(multi_head_attention), "要定义 split_heads / merge_heads / multi_head_attention 三个函数"

    parts = split_heads([[1, 2, 3, 4]], 2)
    assert isinstance(parts, list) and len(parts) == 2, "split_heads(X, 2) 应该返回 2 个头，也就是一个长度为 2 的列表"
    assert parts[0] == [[1, 2]] and parts[1] == [[3, 4]], "split_heads 切的是特征维：[[1,2,3,4]] 按 2 个头切成 [[1,2]] 和 [[3,4]]，按顺序切、不交叉"

    X = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]
    assert merge_heads(split_heads(X, 3)) == X, "merge_heads 必须是 split_heads 的逆操作：切完再拼回来要和原来完全一样"
    assert len(split_heads(X, 3)) == 3 and len(split_heads(X, 3)[0]) == 2, "split_heads 只切特征维，不能动序列长度：h=3 时每个头仍然是 2 行"

    Q = [[1.0, 0.0, 0.0, 1.0]]
    K = [[1.0, 0.0, 0.0, 1.0], [0.0, 1.0, 1.0, 0.0]]
    V = [[1.0, 0.0, 0.0, 1.0], [0.0, 1.0, 1.0, 0.0]]
    out = multi_head_attention(Q, K, V, 2)
    assert isinstance(out, list) and isinstance(out[0], list) and len(out[0]) == 4, "多头注意力的输出形状要和 V 一致 —— 这里是 (1, 4)"
    assert abs(out[0][0] - 0.6697615493266569) < 1e-6, "第 1 个头（前两列）应该是 [0.6698, 0.3302]，检查切分和拼接的位置"
    assert abs(out[0][3] - 0.6697615493266569) < 1e-6, "第 2 个头（后两列）应该是 [0.3302, 0.6698]，所以第 4 列是 0.6698；如果 4 列都等于单头的结果，说明根本没有分头算"
    assert abs(out[0][1] - 0.3302384506733431) < 1e-6, "第 2 列应该是 0.3302 —— 4 列依次是「头 1 的两列 + 头 2 的两列」，不是交替排列"

    out2 = multi_head_attention(Q, K, V, 1)
    ref = attention(Q, K, V)
    assert max(abs(a - b) for a, b in zip(out2[0], ref[0])) < 1e-9, "h=1 时多头必须退化成单头 attention，结果要完全一致；这里差了说明切分或拼回的维度错了"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

TF05_CHECKER = """
try:
    assert callable(positional_encoding), "要定义一个叫 positional_encoding 的函数"
    PE = positional_encoding(8, 8)
    assert isinstance(PE, list) and len(PE) == 8, "positional_encoding(8, 8) 应该返回 8 行（每个位置一行）"
    assert isinstance(PE[0], list) and len(PE[0]) == 8, "每一行应该有 d_model = 8 个数"
    assert all(abs(v - 0.0) < 1e-12 for v in PE[0][0::2]), "位置 0 的偶数维是 sin(0) = 0"
    assert all(abs(v - 1.0) < 1e-12 for v in PE[0][1::2]), "位置 0 的奇数维是 cos(0) = 1，所以位置 0 的编码是 [0, 1, 0, 1, …]"

    assert abs(PE[1][0] - math.sin(1.0)) < 1e-9, "第 1 个位置第 0 维用的是最高频那对（指数为 0）：sin(1 / 10000**0) = sin(1) ≈ 0.8415"
    assert abs(PE[1][2] - math.sin(0.1)) < 1e-9, "第 1 个位置第 2 维的指数是 2*i/d_model = 2/8，10000**0.25 = 10，所以应该是 sin(1/10) ≈ 0.0998 —— 检查指数里用的是 2*i/d_model 而不是 i/d_model"
    assert abs(PE[1][1] - math.cos(1.0)) < 1e-9, "奇数维要放 cos，而且角度和它前面的 sin 完全一样（同一个频率）"
    assert abs(PE[2][1] - math.cos(2.0)) < 1e-9, "第 2 个位置第 1 维是 cos(2 / 10000**0) = cos(2) ≈ -0.4161"
    assert max(max(abs(v) for v in row) for row in PE) <= 1.0, "sin / cos 的值必须在 [-1, 1] 之间，超出说明频率算错了"

    same = [sum(a * b for a, b in zip(PE[p], PE[p + 3])) for p in range(5)]
    assert max(same) - min(same) < 1e-9, "关键性质：PE[pos] 和 PE[pos+3] 的点积只跟间隔 3 有关、与 pos 无关（因为 sin(a)sin(a+b) + cos(a)cos(a+b) = cos(b)）。现在几组结果不一致，说明同一对 sin/cos 没有共用同一个频率"

    P2 = positional_encoding(3, 4)
    assert isinstance(P2, list) and len(P2) == 3 and len(P2[0]) == 4, "换一组参数验一遍：positional_encoding(3, 4) 应该是 3 行 4 列"
    assert abs(P2[2][0] - math.sin(2.0)) < 1e-9, "第 2 个位置第 0 维是 sin(2) ≈ 0.9093"
    assert abs(P2[2][2] - math.sin(0.02)) < 1e-9, "d_model 变成 4 之后，第 2 维的指数是 2/4 = 0.5，10000**0.5 = 100，所以是 sin(2/100) = sin(0.02) —— 指数必须跟着 d_model 走，不能写死"
    d2 = [sum(a * b for a, b in zip(P2[p], P2[p + 1])) for p in range(2)]
    assert abs(d2[0] - d2[1]) < 1e-9, "换成间隔 1 也要成立：点积只依赖间隔、与起点无关，这是正弦编码能表达相对位置的数学依据"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

LESSONS: list[dict] = [
    # ------------------------------------------------------------------ tf-01
    {
        "code": "tf-01",
        "subject": "Transformer",
        "stage": "注意力机制",
        "runner": "none",
        "title": "从 RNN 到 Attention",
        "summary": "RNN 的瓶颈，和 Attention 怎么破",
        "definition": (
            "**RNN 的做法**：按时间步递归，`h_t = f(x_t, h_{t-1})`。第 t 步必须拿到第 t-1 步的结果，"
            "于是有两个硬伤：\n\n"
            "- **路径长度随距离线性增长**：位置 i 的信息要传到位置 j，中间隔着 `|i - j|` 次变换。"
            "反向传播时梯度要沿同一条链连乘 `|i-j|` 次，长距离的梯度指数级衰减（梯度消失），"
            "所以 RNN「记得住近处、记不住远处」。LSTM/GRU 的门控能让梯度更稳，"
            "但**信息仍然要逐步传递**，路径长度没变，只是缓解不是根治。\n"
            "- **无法并行**：`h_t` 依赖 `h_{t-1}`，序列只能一个 token 一个 token 地算，"
            "GPU 的大量并行单元在训练时用不满。\n\n"
            "**Attention 的做法**：让每个位置直接和所有位置交互，一次性算出全部输出。"
            "`Attention(Q, K, V) = softmax(QKᵀ/√d_k)V`。\n\n"
            "- **任意两个位置的路径长度恒为 1**，与距离无关，梯度不用穿越长链\n"
            "- **全部位置同时计算**，序列长度这一维完全并行\n"
            "- 代价：注意力矩阵是 `n × n`，对序列长度的复杂度是 `O(n²)`\n\n"
            "一句话总结：RNN 把「找相关信息」这件事交给递归按顺序做，"
            "Attention 把它改成**内容寻址的检索** —— 用 Query 去和所有 Key 比对，"
            "谁的 Key 和我的 Query 匹配，就取谁的 Value。"
        ),
        "plain": (
            "**RNN 像传话游戏**：一排人站成一列，第一个人说一句话，然后挨个往后传。"
            "传到第五个人，内容早就变形了；而且必须等前一个人说完，后一个人才能开口，"
            "整排人只能一个一个来。\n\n"
            "**Attention 像开圆桌会议**：每个人同时把「我想知道什么」写成一张纸条（Query），"
            "每个人面前也放着一块写着「我这儿有什么」的牌子（Key）。"
            "所有人**一次性**互相看牌打分，谁跟我的问题最相关，我就重点听谁的发言内容（Value）。"
            "不管坐第几个位置，看一眼就能拿到信息 —— 这就是「路径长度为 1」。\n\n"
            "代价也来自同一件事：既然要互相看牌，就得为**每一对位置**算一次相关度，"
            "n 个人就有 `n × n` 对。n 从 1 千涨到 10 万，注意力矩阵就从 10⁶ 涨到 10¹⁰ 个元素 —— "
            "这正是长文本推理显存吃紧的根源。"
        ),
        "example": (
            "输入序列： [我, 喜欢, 自然, 语言, 处理]      n = 5，d_model = 512\n"
            "\n"
            "── RNN：串行，路径随距离变长 ─────────────────────\n"
            "  h1 = f(x1, h0)\n"
            "  h2 = f(x2, h1)        # x1 的信息要先穿过 h1\n"
            "  h5 = f(x5, h4)        # 想用到 x1，中间隔着 4 次传递\n"
            "\n"
            "  任意两步之间的路径长度 = |i - j|     → 最远 O(n)\n"
            "  必须先算完 h(t-1) 才能算 h(t)        → 不能并行\n"
            "  梯度沿同一条链连乘                   → 长距离梯度消失\n"
            "\n"
            "── Self-Attention：一次看全，路径恒为 1 ──────────\n"
            "  X = 词嵌入 + 位置编码                (5, 512)\n"
            "  Q = X @ W_q                          (5, 512) -> (5, 64)\n"
            "  K = X @ W_k                          (5, 512) -> (5, 64)\n"
            "  V = X @ W_v                          (5, 512) -> (5, 64)\n"
            "  S = Q @ Kᵀ                           (5, 64) x (64, 5) -> (5, 5)\n"
            "  A = softmax(S / √64)                 (5, 5)   每行和为 1\n"
            "  O = A @ V                            (5, 5) x (5, 64) -> (5, 64)\n"
            "\n"
            "  任意两步之间的路径长度 = 1（与 n 无关）\n"
            "  所有位置同时计算                     → 完全并行\n"
            "  代价：S 是 n × n                      → O(n²) 时间与显存"
        ),
        "example_output": (
            "RNN         : 路径长度 |i-j|，最远 O(n)；必须串行；梯度消失在长距离\n"
            "Attention   : 路径长度恒为 1；可并行；代价是 n × n 的注意力矩阵（O(n²)）\n"
            "输出形状    : Self-Attention 的形状是 (n, d_v)，序列长度和维度都不变"
        ),
        "pitfalls": [
            "**把 Attention 当成「可视化出来的注意力热力图」**：热力图只是副产品。它的本质是**内容寻址的检索**（用 Query 去匹配 Key、取 Value），是可以端到端训练的一个算子，不是事后解释工具。",
            "**以为 Attention 没有代价**：任意两点路径短，换来的就是 `O(n²)` 的注意力矩阵。n = 4096 时是 1600 万个分数，n = 100k 时是 10¹⁰ 个 —— 长文本优化的所有工作几乎都在对付这一项。",
            "**以为 RNN 的问题只是「慢」**：慢（不能并行）只是表象，真正致命的是**长距离梯度消失**和路径长度随距离增长。所以 LSTM/GRU 只算缓解，Transformer 才是换掉了这个结构。",
            "**忘了 Attention 本身没有位置概念**：它做的是「把一组向量按相关度加权求和」，把输入顺序打乱，输出只是跟着打乱。这一步少了位置信息，就必须靠位置编码补回来（见 tf-05）。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：Self-Attention 相比 RNN，最本质的优势是什么？"
                ),
                "options": [
                    "任意两个位置的交互路径长度为 1、与距离无关，而且整条序列可以并行计算",
                    "参数量更少，所以训练更快",
                    "它天然知道词的先后顺序，不需要位置编码",
                    "计算复杂度更低，从 O(n²) 降到了 O(n)",
                ],
                "answer_index": 0,
                "explanation": (
                    "核心是两件事：**路径长度 O(1)**（梯度不用穿越长链，长距离依赖不衰减）和**可并行**（不依赖 h(t-1)）。"
                    "B 不对，Attention 的参数量并不更少；C 恰恰相反，它没有顺序概念、必须加位置编码；"
                    "D 说反了，Attention 对序列长度是 O(n²)，RNN 才是 O(n)。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "LSTM / GRU 用门控缓解了梯度消失，为什么仍然没有解决长距离依赖问题？"
                ),
                "options": [
                    "门控让梯度更稳定，但信息仍需按时间步逐步传递，路径长度依然随距离线性增长",
                    "因为 LSTM 的参数量比 Transformer 少",
                    "因为 LSTM 无法使用 GPU 训练",
                    "因为 LSTM 会把超过固定长度的序列直接截断",
                ],
                "answer_index": 0,
                "explanation": (
                    "门控改变的是「梯度衰减的速度」，没有改变「信息必须一步步走」这个事实。"
                    "距离越远，中间经过的非线性变换越多，信息就被稀释得越多。"
                    "Transformer 是直接把路径长度变成 1，属于结构性的改变。"
                ),
            },
            {
                "type": "judge",
                "stem": "Self-Attention 对序列长度的计算复杂度是 O(n²)，这是长文本场景下显存和延迟的主要瓶颈之一。",
                "answer": True,
                "explanation": (
                    "注意力矩阵是 n × n，还要存下来做 softmax。"
                    "所以长文本优化（稀疏注意力、滑窗、线性注意力、FlashAttention 的显存优化）几乎都在对付这一项。"
                ),
            },
            {
                "type": "blank",
                "stem": "RNN 无法并行，是因为第 t 步必须等第 ___ 步的输出算完才能开始。",
                "hint": "填一个下标表达式",
                "answer": "t-1",
                "accept": ["t-1", "t - 1", "t−1"],
                "explanation": "`h_t = f(x_t, h_{t-1})`，`h_t` 依赖 `h_{t-1}`，形成串行依赖链，这就是没法并行的原因。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：为什么 Transformer 能取代 RNN 成为主流？"
                    "请从「长距离依赖」「并行性」「代价」三个方面说清楚。"
                ),
                "keywords": ["路径长度", "并行", "O(n²)", "梯度消失", "内容寻址", "长距离依赖"],
                "reference": (
                    "一是**长距离依赖**：RNN 里位置 i 到 j 要经过 |i-j| 次递归变换，梯度连乘后指数衰减，"
                    "LSTM 的门控只是缓解；Self-Attention 里任意两点直接相连，路径长度恒为 1。"
                    "二是**并行性**：RNN 的 h_t 依赖 h_{t-1}，只能串行，GPU 利用率低；"
                    "Attention 一次算出全部位置，而大模型的规模优势正建立在「能用更多算力并行训练」上。"
                    "三是**代价**：Attention 对序列长度是 O(n²) 的时间和显存，"
                    "所以长文本反而成了它的新瓶颈，后续大量工作都在优化这一项。"
                ),
                "explanation": "答这个问题要给出「优势 + 代价」两面，只说优势显得没实战过。",
            },
        ],
    },
    # ------------------------------------------------------------------ tf-02
    {
        "code": "tf-02",
        "subject": "Transformer",
        "stage": "注意力机制",
        "runner": "none",
        "title": "Self-Attention 与 Q/K/V",
        "summary": "每个词都去问所有词：你和我多相关",
        "definition": (
            "**Q / K / V 是同一份输入的三种角色**，由三个不同的、可学习的投影矩阵得到：\n\n"
            "```\nQ = X @ W_q     Query —— 我在找什么\nK = X @ W_k     Key   —— 我能被什么找到\nV = X @ W_v     Value —— 我实际能提供的内容\n```\n\n"
            "`X` 的形状是 `(n, d_model)`，`W_q / W_k / W_v` 的形状是 `(d_model, d_k)`，"
            "所以 `Q / K / V` 都是 `(n, d_k)`。\n\n"
            "**计算分三步**：\n\n"
            "1. **打分**：`S = Q @ Kᵀ`，形状 `(n, n)`。`S[i][j]` 是「第 i 个位置向第 j 个位置问：你和我多相关」。\n"
            "2. **归一化**：`A = softmax(S / √d_k)`，**按行**做 softmax，每一行加起来是 1，"
            "得到「第 i 个位置应该用多少比例的注意力分给各个 j」。\n"
            "3. **加权求和**：`O = A @ V`，形状 `(n, d_v)`。第 i 个位置的新表示，就是所有位置的 V 按 `A[i]` 加权求和。\n\n"
            "叫 **Self**-Attention 是因为 Q、K、V **同源**（都来自同一个 X）。"
            "Decoder 里的 **Cross-Attention** 则是 Q 来自 decoder、K/V 来自 encoder，来源不同。\n\n"
            "**为什么不能省掉投影、直接拿 X 自己算相似度？** 因为同一个词在不同上下文里要扮演不同角色："
            "「他」作为 Query 要去找前文的人名，作为 Key 却要被别的词指代。"
            "三个独立投影让「我想找什么」和「我提供什么」解耦，模型能学出「指代可传递」这类关系；"
            "直接用 X 会把这个能力锁死成对称的相似度。"
        ),
        "plain": (
            "**去图书馆找书**：你脑子里想的是「我想找关于深度学习的、入门的书」—— 这是 **Query**。"
            "每本书书脊上贴着标签和书名 —— 那是 **Key**。书里的正文内容 —— 那是 **Value**。\n\n"
            "你先拿自己的需求（Query）去和每本书的标签（Key）比对，算一个匹配度；"
            "然后按匹配度把书的内容（Value）**按比例**抄进笔记："
            "最相关的抄 60%，次相关的抄 30%，基本无关的抄 10%。"
            "注意你抄的是**内容**，不是标签 —— 标签只用来打分，这就是 K 和 V 分工的意义。\n\n"
            "Self-Attention 里，句子中**每个词都同时是这三样**："
            "它拿着自己的 Query 去问所有词（包括它自己），"
            "也把自己的 Key 挂出来等着被问，最后把大家的 Value 加权揉进自己的新表示里。"
            "「它」这个词的 Query 学到「我要找一个指人的名词」，"
            "而前文的「小猫」的 Key 学到了「我是可被指代的名词」，两者一匹配，权重就高 —— "
            "指代关系就是这么被建模出来的。"
        ),
        "example": (
            "句子： 「小猫 坐在 垫子上」      n = 3，d_model = 512，d_k = 64\n"
            "\n"
            "  X      (3, 512)   词嵌入 + 位置编码\n"
            "  W_q    (512, 64)  ┐\n"
            "  W_k    (512, 64)  ├ 三个**独立**的、可学习的投影矩阵\n"
            "  W_v    (512, 64)  ┘\n"
            "\n"
            "  Q = X @ W_q   (3, 64)   每个词在问：「我要找什么信息」\n"
            "  K = X @ W_k   (3, 64)   每个词挂出牌：「我能被什么找到」\n"
            "  V = X @ W_v   (3, 64)   每个词的实际内容：「我能提供什么」\n"
            "\n"
            "  S = Q @ Kᵀ                (3, 64) × (64, 3)  ->  (3, 3)\n"
            "      S[i][j] = <q_i, k_j> / √64           第 i 个词给第 j 个词打的分\n"
            "  A = softmax(S)            (3, 3)              按行归一化，每行和为 1\n"
            "  O = A @ V                 (3, 3) × (3, 64) -> (3, 64)\n"
            "\n"
            "  O 的第 1 行 = 0.6·V₁ + 0.3·V₂ + 0.1·V₃\n"
            "      —— 第 1 个词的新表示，是「所有词的 V」按相关度加权求和\n"
            "\n"
            "  ⚠️ S 不是对称矩阵：S[i][j] 是「i 问 j」，和「j 问 i」是两回事。\n"
            "  ⚠️ 输出形状 (3, 64) 和 V 一致，**序列长度和维度都没变**，所以可以层层堆叠。"
        ),
        "example_output": (
            "Q (3,64)   K (3,64)   V (3,64)\n"
            "S = Q @ Kᵀ        -> (3,3)，不对称：S[i][j] 是「i 问 j」的打分\n"
            "A = softmax(S)    -> (3,3)，按行归一化，每行和为 1\n"
            "O = A @ V         -> (3,64)，形状和 V 一致，序列长度、特征维都不变\n"
            "第 1 个词的新向量 = 0.6·V₁ + 0.3·V₂ + 0.1·V₃"
        ),
        "pitfalls": [
            "**把 K 和 V 的角色弄混**：K 只参与「打分」，V 才是被加权求和的内容。手推公式时如果写成 `softmax(QKᵀ)K`，那就完全不是注意力了 —— 这是面试现场最容易被抓的硬伤。",
            "**以为 Q / K / V 是三份不同的输入**：Self-Attention 里它们**同源**，都来自同一个 `X`，只是过了三个不同的投影矩阵。真正来源不同的是 Cross-Attention（Q 来自 decoder，K/V 来自 encoder）。",
            "**softmax 的方向搞反**：必须**按行**归一化（固定一个 Query，对所有 Key 分配权重）。按列归一化意味着「所有 Query 分给同一个 Key 的权重和为 1」，那是另一个完全不同的模型。",
            "**把 attention 权重当作因果解释**：权重高不等于「因为这个词所以预测出结果」。同一组权重换一种等价参数化就能变，"
            "而且 Value 本身的模长也会影响输出。面试被问到「能不能用注意力解释模型」，正确答法是「只能作为参考线索，不能当因果证据」。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：注意力里 K 和 V 分别负责什么？为什么算相关度用 K 而不用 V？"
                ),
                "options": [
                    "K 用来和 Query 算相关度打分，V 是被加权求和的内容；两者分工不同，所以用两个独立投影",
                    "K 和 V 是同一个张量，只是名字不同",
                    "K 是内容，V 是索引 —— 和 Q 一起做检索",
                    "K 用来算相关度，V 用来算梯度，前向传播用不到 V",
                ],
                "answer_index": 0,
                "explanation": (
                    "「用什么被找到」（K）和「提供什么内容」（V）是两种不同的需求，"
                    "用两个独立投影矩阵才能分别学。B 错在它们来自不同的权重矩阵，数值并不相同；"
                    "C 把 K/V 说反了；D 完全不对，V 就是前向传播里被加权求和的东西。"
                ),
            },
            {
                "type": "choice",
                "stem": "在 Self-Attention 中，Q、K、V 的来源是？",
                "options": [
                    "都由同一个输入 X 乘上三个不同的权重矩阵得到",
                    "分别来自编码器、解码器和输出层",
                    "是三个独立的输入张量，由用户传入",
                    "Q 来自输入，K 和 V 来自上一层注意力的输出",
                ],
                "answer_index": 0,
                "explanation": (
                    "Self 的含义就是同源。Cross-Attention 才是来源不同（Q 来自 decoder，K/V 来自 encoder）。"
                    "这也是为什么 Self-Attention 层可以无限堆叠：输入输出形状都是 (n, d_model)。"
                ),
            },
            {
                "type": "judge",
                "stem": "如果某一层的 attention 权重显示第 3 个词对第 7 个词权重很高，就可以断定模型是「因为第 3 个词」才做出这个预测。",
                "answer": False,
                "explanation": (
                    "注意力权重只是中间变量，不能当因果证据。同一组权重换一个等价参数化就能得到不同的权重值，"
                    "而且输出还取决于 Value 的模长。它可以作为排查线索，但不能作为结论。"
                ),
            },
            {
                "type": "blank",
                "stem": "补全缩放点积注意力的公式：Attention(Q, K, V) = softmax(QKᵀ / √d_k) · ___",
                "hint": "填一个字母",
                "answer": "V",
                "accept": ["V", "v"],
                "explanation": "最后被加权求和的是 V（内容），K 只参与前面的打分。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：既然 Q、K、V 都来自同一个 X，为什么还要三组投影？"
                    "直接用 X 自己和自己算相似度不行吗？"
                ),
                "keywords": ["角色", "解耦", "对称", "子空间", "指代", "表达能力"],
                "reference": (
                    "因为同一个位置在不同关系里扮演的角色不同：它既要作为 Query 去「找别人」，"
                    "又要作为 Key 去「被别人找」，还要作为 Value 提供内容 —— 这三个需求不一样。"
                    "三组独立投影把「我想找什么」和「我提供什么」解耦，模型才能学出「指代可传递」这类非对称关系。"
                    "如果直接用 X 算，`XXᵀ` 是对称的，「A 指代 B」和「B 指代 A」拿到的分数完全一样，"
                    "表达能力被锁死；另外三个投影也相当于把 Q/K 映射到不同的子空间里比较，"
                    "比在原始空间里比更灵活。"
                ),
                "explanation": "这个问题的核心词是「解耦」和「非对称」，答出对称性被破坏就已经抓住了要点。",
            },
        ],
    },
    # ------------------------------------------------------------------ tf-03
    {
        "code": "tf-03",
        "subject": "Transformer",
        "stage": "注意力机制",
        "runner": "python",
        "title": "缩放点积注意力与 Softmax",
        "summary": "为什么要除以根号 d_k，Softmax 怎么稳",
        "definition": (
            "**公式**：`Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V`\n\n"
            "**Softmax 的作用**：把一串实数分数压成一组「和为 1」的权重，"
            "而且保持大小关系（分数越大权重越大）。\n\n"
            "**为什么要除以 √d_k —— 这是本科目最高频的考点**：\n\n"
            "假设 `q` 和 `k` 的每一维都是均值 0、方差 1 的独立随机变量，那么它们的点积\n"
            "`q · k = Σ q_i k_i` 是 `d_k` 个独立同分布项之和，所以**均值 0、方差 `d_k`** —— "
            "点积的方差随 `d_k` 线性增长，`d_k = 64` 时标准差就有 8，`d_k = 512` 时约 22。\n\n"
            "而 softmax 在输入值差得很大时会进入**饱和区**：最大值那一项权重趋近 1，其他趋近 0。"
            "饱和的直接后果是**梯度趋近 0** —— softmax 的雅可比在饱和处几乎全零，"
            "反向传播几乎传不出有效梯度，训练一开始就卡住。\n\n"
            "除以 `√d_k` 相当于把点积重新标准化回方差 1 的量级，让 softmax 待在梯度健康的区间。"
            "注意分母是 **√d_k（标准差）**，不是 `d_k`（方差）—— 写成 `d_k` 会把分布压得太平，"
            "注意力失去区分度。\n\n"
            "**Softmax 的数值稳定性**：直接 `exp(x)` 时，`x` 稍大就会溢出（`math.exp(1000)` 直接抛 OverflowError）。"
            "标准做法是**每一项先减去最大值**：`exp(x - m) / Σ exp(x - m)`。"
            "分子分母同乘 `e^{-m}`，数学上完全等价，但最大的指数变成 `exp(0) = 1`，不可能溢出。"
            "这也是所有框架里 softmax 实现的第一行。"
        ),
        "plain": (
            "**为什么除以 √d_k，用考试分数理解最直观**：\n\n"
            "softmax 是个「赢家通吃」的裁判。给它一组差距不大的分数，比如 `[1.0, 0.9, 0.8]`，"
            "它会给出比较温和的权重 `[0.36, 0.33, 0.31]`；但给它一组差距悬殊的分数 `[50, 0.9, 0.8]`，"
            "它会直接给出 `[~1, ~0, ~0]` —— 变成「只看第一个，其余全不要」。\n\n"
            "问题在于：`d_k` 越大，点积的**数值本身就越大、差距也越大**。"
            "`d_k = 512` 时点积轻轻松松就是几十上百，还没开始学，softmax 就已经是赢家通吃了。"
            "更糟的是这时候它的梯度几乎是 0，参数根本没法更新 —— 不是「学得慢」，是「几乎学不动」。\n\n"
            "除以 `√d_k` 就是把「考试的满分标准」统一一下："
            "不管这张卷子有多少道题（`d_k` 多大），总分都折算回同一个量级，"
            "让裁判（softmax）始终工作在一个能区分、又不至于一边倒的区间里。\n\n"
            "**减最大值防溢出**也来自生活直觉：你要算 `e^1000 / (e^1000 + e^999)`，"
            "分子分母都是天文数字，算不出来；但上下同除以 `e^1000`，就变成 `1 / (1 + e^{-1})`，"
            "结果一模一样却好算得多。Softmax 的稳定实现就是这个操作。"
        ),
        "example": (
            "import math\n"
            "\n"
            "\n"
            "def softmax(xs):\n"
            "    m = max(xs)                                    # 先减最大值：结果不变，但不会溢出\n"
            "    exps = [math.exp(x - m) for x in xs]\n"
            "    total = sum(exps)\n"
            "    return [e / total for e in exps]\n"
            "\n"
            "\n"
            "def dot(a, b):\n"
            "    return sum(x * y for x, y in zip(a, b))\n"
            "\n"
            "\n"
            "def attention(Q, K, V):\n"
            "    d_k = len(K[0])\n"
            "    scores = [[dot(q, k) / math.sqrt(d_k) for k in K] for q in Q]   # QKᵀ / √d_k\n"
            "    weights = [softmax(row) for row in scores]                      # 按行归一化\n"
            "    return [[sum(weights[i][j] * V[j][c] for j in range(len(V)))\n"
            "             for c in range(len(V[0]))] for i in range(len(Q))]\n"
            "\n"
            "\n"
            "print(\"softmax([1, 1, 1])         =\", [round(v, 4) for v in softmax([1, 1, 1])])\n"
            "print(\"softmax([1000, 1000, 1000]) =\", [round(v, 4) for v in softmax([1000.0, 1000.0, 1000.0])])\n"
            "print(\"softmax([0, 1, 2])         =\", [round(v, 4) for v in softmax([0.0, 1.0, 2.0])])\n"
            "\n"
            "Q = [[1.0, 0.0]]\n"
            "K = [[1.0, 0.0], [0.0, 1.0]]      # 一个 key 和 Q 同向，一个和 Q 正交\n"
            "V = [[1.0, 0.0], [0.0, 1.0]]\n"
            "print(\"attention                  =\", [[round(v, 4) for v in row] for row in attention(Q, K, V)])\n"
            "\n"
            "raw = [dot(Q[0], k) for k in K]\n"
            "print(\"不缩放的权重                =\", [round(v, 4) for v in softmax(raw)])\n"
            "print(\"缩放后的权重                =\", [round(v, 4) for v in softmax([s / math.sqrt(2) for s in raw])])"
        ),
        "example_output": (
            "softmax([1, 1, 1])         = [0.3333, 0.3333, 0.3333]\n"
            "softmax([1000, 1000, 1000]) = [0.3333, 0.3333, 0.3333]\n"
            "softmax([0, 1, 2])         = [0.09, 0.2447, 0.6652]\n"
            "attention                  = [[0.6698, 0.3302]]\n"
            "不缩放的权重                = [0.7311, 0.2689]\n"
            "缩放后的权重                = [0.6698, 0.3302]"
        ),
        "pitfalls": [
            "**忘了除以 √d_k（或写成除以 d_k）**：不除，`d_k` 越大点积方差越大，softmax 被推进饱和区、梯度趋近 0，训练直接卡住；写成 `d_k` 又把分布压得过平，注意力失去区分度。分母必须是 **√d_k**。",
            "**softmax 直接 exp 不减去最大值**：`math.exp(1000)` 会抛 `OverflowError`。要先把每一项减去这行的最大值再取指数 —— 数学上等价，数值上安全。这是面试写代码题的必查点。",
            "**归一化的方向搞错**：必须**按行** softmax（固定 Query、对所有 Key 分配权重）。如果实现时转置了，就变成「固定 Key、对所有 Query 归一化」，那是完全不同的模型，而且维度对不上时还不报错，只能靠数值检查发现。",
            "**Mask 之后整行被遮掉会出 NaN**：padding mask 或全 -inf 的行经 softmax 后是 `0/0`。工程实现要么保证每行至少留一个可见位置，要么用 `masked_fill` + 安全分母（如 `torch.nan_to_num`）兜底，否则线上偶发 NaN、非常难查。",
        ],
        "task": (
            "上一课只有公式，这一课把它写成能跑的代码。请实现三个函数：\n\n"
            "1. `softmax(xs)` —— 输入一组分数（列表），返回**归一化后的权重列表**：长度不变、加起来等于 1。\n"
            "   要求**先减去最大值再取 exp**（结果不变，但 `exp(1000)` 不会溢出）。\n"
            "2. `scaled_scores(Q, K)` —— 返回 `Q @ Kᵀ / √d_k`，形状 `(len(Q), len(K))`。\n"
            "   `d_k` 是 K 的**特征维**，也就是 `len(K[0])`。\n"
            "3. `attention(Q, K, V)` —— 返回 `softmax(scaled_scores(Q, K)) @ V`，Q / K / V 都是二维列表。\n"
            "   输出形状要等于 `(len(Q), len(V[0]))`。\n\n"
            "题目已经给好了 `dot(a, b)` 和 `transpose(M)` 两个小工具，直接用。"
        ),
        "setup": (
            "import math\n"
            "\n"
            "\n"
            "def dot(a, b):\n"
            "    \"\"\"两个等长向量的点积：dot([1, 2], [3, 4]) == 11\"\"\"\n"
            "    return sum(x * y for x, y in zip(a, b))\n"
            "\n"
            "\n"
            "def transpose(M):\n"
            "    \"\"\"矩阵转置：transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]\"\"\"\n"
            "    return [list(col) for col in zip(*M)]\n"
        ),
        "starter": (
            "# dot(a, b) 和 transpose(M) 已经给好了，直接用\n"
            "\n"
            "\n"
            "def softmax(xs):\n"
            "    # 返回归一化后的权重列表：长度和 xs 一样、和为 1\n"
            "    # 提示：先减去最大值再做 exp，避免 exp(1000) 溢出\n"
            "    pass\n"
            "\n"
            "\n"
            "def scaled_scores(Q, K):\n"
            "    # 返回 Q @ Kᵀ / sqrt(d_k)，形状 (len(Q), len(K))\n"
            "    pass\n"
            "\n"
            "\n"
            "def attention(Q, K, V):\n"
            "    # 返回 softmax(scaled_scores(Q, K)) @ V\n"
            "    pass\n"
        ),
        "hint": (
            "`softmax`：`m = max(xs)`，`exps = [math.exp(x - m) for x in xs]`，再每一项除以 `sum(exps)`。\n"
            "`scaled_scores`：`d_k = len(K[0])`，第 i 行第 j 列是 `dot(Q[i], K[j]) / math.sqrt(d_k)`。\n"
            "`attention`：先把 `scaled_scores` 的**每一行** softmax 成权重，"
            "再用权重对 V 的每一行做加权求和：`sum(weights[i][j] * V[j][c] for j in range(len(V)))`。"
        ),
        "checker": TF03_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：Attention 里为什么要除以 √d_k？不除会怎样？"
                ),
                "options": [
                    "点积的方差随 d_k 线性增长，d_k 大时 softmax 会被推进饱和区、梯度趋近 0；除以 √d_k 把方差拉回 1 的量级",
                    "为了让每一行注意力权重之和等于 1",
                    "为了减少点积的计算量，加快训练",
                    "因为 Q 和 K 的维度必须归一化后才能相乘",
                ],
                "answer_index": 0,
                "explanation": (
                    "设 q、k 各维独立且均值 0 方差 1，则 `q·k = Σ q_i k_i` 的方差是 `d_k`，"
                    "所以点积的标准差是 `√d_k`——这就是除数的来源（除标准差，不是除方差）。"
                    "不除的话 d_k=512 时点积动辄 ±20，softmax 输出接近 one-hot，"
                    "雅可比几乎全零，梯度传不回去。B 是 softmax 本身的职责，和缩放无关；"
                    "C 说反了，多一次除法不会更快；D 不是原因。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "面试官问：softmax 在实现时为什么要「先减去最大值」？"
                ),
                "options": [
                    "因为 exp(大数) 会溢出；减去最大值后数学上完全等价，但最大的指数变成 exp(0)=1，不会溢出",
                    "因为不减最大值算出来的结果和标准 softmax 不一样",
                    "为了把输出的最小值固定成 0",
                    "为了把计算复杂度从 O(n²) 降到 O(n)",
                ],
                "answer_index": 0,
                "explanation": (
                    "分子分母同乘 `e^{-m}`，值完全不变。B 正好说反 —— 结果是一样的，只是数值安全；"
                    "C 不对，减最大值不改变最小输出是正数这个事实；D 无关。"
                ),
            },
            {
                "type": "judge",
                "stem": "标准缩放点积注意力里，softmax 是按列归一化的，也就是每一个 Key 分到的所有权重加起来等于 1。",
                "answer": False,
                "explanation": (
                    "是按**行**归一化：固定一个 Query，它分给所有 Key 的权重和为 1。"
                    "换句话说，每一行是一个「怎么分配注意力」的概率分布。"
                ),
            },
            {
                "type": "blank",
                "stem": "缩放点积注意力的标准写法是 `softmax(QKᵀ / √___) · V`，分母上的维度名是什么？",
                "hint": "填一个维度记号",
                "answer": "d_k",
                "accept": ["d_k", "dk", "d_k维", "Key的维度"],
                "explanation": "`d_k` 是 Key（也是 Query）的维度。除以它的**平方根**，把点积的标准差折算回 1。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：如果 Q 和 K 的维度是 512，点积结果大概是什么量级？"
                    "这个量级为什么会让 softmax 出问题？"
                ),
                "keywords": ["方差", "标准差", "√d_k", "饱和", "梯度", "one-hot"],
                "reference": (
                    "假设每一维独立、均值 0 方差 1，点积是 512 项之和，方差就是 512，"
                    "所以标准差是 `√512 ≈ 22.6` —— 分数会散布在 ±20 以上。"
                    "softmax 的指数差 20 就意味着权重比 `e^20 ≈ 5×10⁸`，最大值那一项几乎拿走全部权重，"
                    "输出接近 one-hot。"
                    "麻烦不只是「注意力太集中」，而是**梯度问题**：softmax 在饱和区的一阶导接近 0，"
                    "反向传播时这一层的梯度几乎消失，参数更新停滞。"
                    "除以 √d_k 就是把标准差从 22.6 折回 1，让 softmax 一开始就在梯度健康的区间工作。"
                ),
                "explanation": "答这道题的顺序应该是：先算方差/标准差 → 再说 softmax 饱和 → 最后落到梯度。",
            },
        ],
    },
    # ------------------------------------------------------------------ tf-04
    {
        "code": "tf-04",
        "subject": "Transformer",
        "stage": "模型结构",
        "runner": "python",
        "title": "多头注意力",
        "summary": "把注意力切到多个子空间里并行地看",
        "definition": (
            "**核心操作**：把 `d_model` 按特征维切成 `h` 份，每份维度 `d_head = d_model / h`，"
            "每一份**独立**做一次缩放点积注意力，然后把 h 个输出在特征维拼回来，最后乘一个输出投影 `W_o`：\n\n"
            "```\nheads  = [Attention(Q·W_q^i, K·W_k^i, V·W_v^i) for i in 1..h]\nMultiHead(Q, K, V) = Concat(heads) · W_o\n```\n\n"
            "**关键点：多头几乎不增加参数量。** 单头时 `W_q` 是 `(d_model, d_model)`；"
            "多头时每个头是 `(d_model, d_model/h)`，h 个头加起来还是 `(d_model, d_model)`。"
            "所以多头的收益**不是更多参数**，而是：\n\n"
            "- **多个子空间**：每一头在自己的投影子空间里算相关度，能同时捕捉不同性质的依赖关系"
            "（有的头盯着相邻词、有的头盯着主谓、有的头盯着指代）\n"
            "- **表示子空间解耦**：单头只能给出一种「平均意义上的」注意力分布，"
            "多头让模型不必在一份权重里做取舍\n"
            "- **更多的实际观察**：训练好的模型里确实能看到分工 —— 有的头关注局部、有的头关注句法，"
            "剪掉个别头对性能影响很小（冗余），但剪掉全部就崩\n\n"
            "**形状链**（`n` 序列长度、`h` 头数、`d_head = d_model / h`）：\n\n"
            "```\nQ      (n, d_model)\n切分    -> h 个 (n, d_head)\n每个头  score (n, n)，输出 (n, d_head)\n拼接    -> (n, h * d_head) = (n, d_model)\n乘 W_o  -> (n, d_model)\n```\n\n"
            "`W_o` 不能省：没有它，多头只是把几个独立子空间的输出并排堆着，缺少**跨头的信息融合**。"
        ),
        "plain": (
            "**一个人做判断 vs 一个委员会分头看**：\n\n"
            "单头注意力像一个人读一句话，只能形成**一种**「谁重要」的判断，"
            "逼着他把语法关系、指代关系、修饰关系全揉进同一份权重里，最后只能是折中。\n\n"
            "多头注意力像一个委员会：把 512 维的表示切成 8 份、每份 64 维，"
            "8 位委员**各看各的**，一位专门盯着「形容词修饰哪个名词」，"
            "一位专门盯着「代词指谁」，一位专门看「相邻词搭配」……"
            "最后把 8 个人的意见**拼接**起来，再由 `W_o` 做一次汇总（相当于组长拍板）。\n\n"
            "注意委员会的总人数没变 —— 8 个人每个人看 64 维，加起来还是 512 维的工作量，"
            "所以参数量和单头几乎一样。多头的价值是**视角的数量**，不是人多。"
        ),
        "example": (
            "import math\n"
            "\n"
            "\n"
            "def softmax(xs):\n"
            "    m = max(xs)\n"
            "    exps = [math.exp(x - m) for x in xs]\n"
            "    total = sum(exps)\n"
            "    return [e / total for e in exps]\n"
            "\n"
            "\n"
            "def dot(a, b):\n"
            "    return sum(x * y for x, y in zip(a, b))\n"
            "\n"
            "\n"
            "def attention(Q, K, V):\n"
            "    d_k = len(K[0])\n"
            "    scores = [[dot(q, k) / math.sqrt(d_k) for k in K] for q in Q]\n"
            "    weights = [softmax(row) for row in scores]\n"
            "    return [[sum(weights[i][j] * V[j][c] for j in range(len(V)))\n"
            "             for c in range(len(V[0]))] for i in range(len(Q))]\n"
            "\n"
            "\n"
            "def split_heads(X, h):\n"
            "    size = len(X[0]) // h                       # 每个头分到的特征维 d_head\n"
            "    return [[row[k * size:(k + 1) * size] for row in X] for k in range(h)]\n"
            "\n"
            "\n"
            "def merge_heads(parts):\n"
            "    h, n = len(parts), len(parts[0])\n"
            "    return [[v for k in range(h) for v in parts[k][i]] for i in range(n)]\n"
            "\n"
            "\n"
            "def multi_head_attention(Q, K, V, h):\n"
            "    heads = [attention(q, k, v) for q, k, v in\n"
            "             zip(split_heads(Q, h), split_heads(K, h), split_heads(V, h))]\n"
            "    return merge_heads(heads)                   # 真实模型这里还要再乘 W_o\n"
            "\n"
            "\n"
            "print(\"split_heads([[1,2,3,4]], 2) =\", split_heads([[1, 2, 3, 4]], 2))\n"
            "print(\"merge 拼回来               =\", merge_heads(split_heads([[1, 2, 3, 4, 5, 6]], 3)))\n"
            "\n"
            "Q = [[1.0, 0.0, 0.0, 1.0]]\n"
            "K = [[1.0, 0.0, 0.0, 1.0], [0.0, 1.0, 1.0, 0.0]]\n"
            "V = [[1.0, 0.0, 0.0, 1.0], [0.0, 1.0, 1.0, 0.0]]\n"
            "print(\"multi_head(h=2)            =\", [[round(v, 4) for v in r] for r in multi_head_attention(Q, K, V, 2)])\n"
            "print(\"single_head(h=1)           =\", [[round(v, 4) for v in r] for r in multi_head_attention(Q, K, V, 1)])\n"
            "print(\"attention 直接算           =\", [[round(v, 4) for v in r] for r in attention(Q, K, V)])"
        ),
        "example_output": (
            "split_heads([[1,2,3,4]], 2) = [[[1, 2]], [[3, 4]]]\n"
            "merge 拼回来               = [[1, 2, 3, 4, 5, 6]]\n"
            "multi_head(h=2)            = [[0.6698, 0.3302, 0.3302, 0.6698]]\n"
            "single_head(h=1)           = [[0.7311, 0.2689, 0.2689, 0.7311]]\n"
            "attention 直接算           = [[0.7311, 0.2689, 0.2689, 0.7311]]"
        ),
        "pitfalls": [
            "**以为多头是靠「更多参数」提升容量**：每个头的维度是 `d_model / h`，h 个头加起来的总参数量和单头 `d_model` 基本相同。多头的价值是**多个子空间视角**，不是更多参数——说错这一点，紧接着的追问（那为什么不直接加大 d_model）就答不上来了。",
            "**切错维度**：切的是**特征维**（最后一维 `d_model`），不是序列长度 n、也不是 batch 维。切错序列维就等于把不同的 token 分给不同的头，各头之间永远无法互相看见，模型直接失效。",
            "**忘了拼回去之后再乘 W_o**：`Concat` 只是把 h 段并排接起来，没有跨头混合。`W_o` 提供跨头的信息融合，也是唯一一处不同头的输出能相互影响的地方，不能省。",
            "**头数不是 d_model 的约数**：`d_model = 512, h = 12` 时 `d_head = 42.67`，直接切不动。所以常见配置都是整除关系（768/12=64、4096/32=128）。另外 `d_head` 太小（比如 16）会明显掉点，通常不低于 64。",
        ],
        "task": (
            "上一课的 `attention(Q, K, V)` 已经给好了。这一课实现多头注意力的「切分 → 逐头算 → 拼回」。\n\n"
            "1. `split_heads(X, h)` —— 把 X 的**特征维**（最后一维）按顺序平均切成 h 份，返回一个长度为 h 的列表；\n"
            "   第 k 份由每一行的第 `k*size : (k+1)*size` 列组成，其中 `size = len(X[0]) // h`。\n"
            "   例：`split_heads([[1, 2, 3, 4]], 2)` → `[[[1, 2]], [[3, 4]]]`。\n"
            "2. `merge_heads(parts)` —— `split_heads` 的逆操作：把 h 份按顺序在特征维拼回原形状。\n"
            "3. `multi_head_attention(Q, K, V, h)` —— 对每一头分别调用 `attention`，"
            "把 h 个结果用 `merge_heads` 拼起来返回。输出形状要等于 `(len(Q), len(V[0]))`。\n\n"
            "（真实模型拼完之后还要再乘一个输出投影 `W_o`，这里省略，只练「切分与拼回」。）"
        ),
        "setup": (
            "import math\n"
            "\n"
            "\n"
            "def dot(a, b):\n"
            "    return sum(x * y for x, y in zip(a, b))\n"
            "\n"
            "\n"
            "def transpose(M):\n"
            "    return [list(col) for col in zip(*M)]\n"
            "\n"
            "\n"
            "def softmax(xs):\n"
            "    m = max(xs)\n"
            "    exps = [math.exp(x - m) for x in xs]\n"
            "    total = sum(exps)\n"
            "    return [e / total for e in exps]\n"
            "\n"
            "\n"
            "def attention(Q, K, V):\n"
            "    \"\"\"单头缩放点积注意力，Q / K / V 都是二维列表。\"\"\"\n"
            "    d_k = len(K[0])\n"
            "    scores = [[dot(q, k) / math.sqrt(d_k) for k in K] for q in Q]\n"
            "    weights = [softmax(row) for row in scores]\n"
            "    return [[sum(weights[i][j] * V[j][c] for j in range(len(V)))\n"
            "             for c in range(len(V[0]))] for i in range(len(Q))]\n"
        ),
        "starter": (
            "# attention / softmax / dot / transpose 已经给好了\n"
            "\n"
            "\n"
            "def split_heads(X, h):\n"
            "    # 把特征维切成 h 份，返回长度 h 的列表\n"
            "    # 提示：size = len(X[0]) // h，第 k 份取每行的 [k*size : (k+1)*size]\n"
            "    pass\n"
            "\n"
            "\n"
            "def merge_heads(parts):\n"
            "    # split_heads 的逆操作：把 h 份在特征维按顺序拼回去\n"
            "    pass\n"
            "\n"
            "\n"
            "def multi_head_attention(Q, K, V, h):\n"
            "    # 逐头调用 attention，再把结果拼回来\n"
            "    pass\n"
        ),
        "hint": (
            "`split_heads`：对 `k in range(h)`，取 `[row[k*size:(k+1)*size] for row in X]`。\n"
            "`merge_heads`：第 i 行要按**头顺序**把各头的第 i 行接起来，"
            "写成 `[v for k in range(h) for v in parts[k][i]]` —— 注意 k 在外层，先遍历头。\n"
            "`multi_head_attention`：用 `zip(split_heads(Q, h), split_heads(K, h), split_heads(V, h))` "
            "把三个张量按头配对，每一对调一次 `attention`，最后 `merge_heads`。"
        ),
        "checker": TF04_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：多头注意力为什么不增加参数量？那它的收益到底从哪来？"
                ),
                "options": [
                    "每个头的维度是 d_model/h，h 个头加起来和单头 d_model 的总参数量基本相同；收益是多个子空间能各自捕捉不同类型的依赖关系",
                    "因为多头实际上是同一份权重算 h 次，只是结果取平均",
                    "因为它把 d_model 压缩成了 d_model/h，所以参数更少",
                    "收益来自更多的参数，只是这些参数共享了",
                ],
                "answer_index": 0,
                "explanation": (
                    "单头 `W_q` 是 `(d_model, d_model)`；多头每个头是 `(d_model, d_model/h)`，h 个加起来一样。"
                    "所以多头的价值是**视角数量**（不同子空间里算相关度），而不是容量。"
                    "B 错在每头有独立投影、也不是取平均；C 参数并没有减少；D 自相矛盾。"
                ),
            },
            {
                "type": "choice",
                "stem": "多头注意力在做「切分」时，切的是张量的哪一个维度？",
                "options": [
                    "特征维（最后一维 d_model）",
                    "序列维（token 数量 n）",
                    "batch 维",
                    "位置编码所在的维度，也就是序列维的一半",
                ],
                "answer_index": 0,
                "explanation": (
                    "切的是特征维。如果切了序列维，不同的 token 就被分到了不同的头里，"
                    "各头之间永远看不见对方，注意力机制直接失效。"
                    "这也是为什么要求 `d_model` 能被 h 整除。"
                ),
            },
            {
                "type": "judge",
                "stem": "多头注意力就是把同样的单头注意力重复算 h 次，然后把 h 个结果取平均。",
                "answer": False,
                "explanation": (
                    "错在两点：一是每个头有**各自独立**的投影矩阵（不是同一份权重）；"
                    "二是最后是 **Concat 拼接 + W_o 投影**，不是取平均。"
                    "取平均会把不同子空间的信息混成一团，丢掉「分别关注不同模式」的收益。"
                ),
            },
            {
                "type": "blank",
                "stem": "h 个头、模型维度是 d_model 时，每个头分到的维度 d_head = d_model / ___",
                "hint": "填一个字母",
                "answer": "h",
                "accept": ["h", "H"],
                "explanation": "所以常见配置都取整除关系：768/12=64、4096/32=128。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：多头注意力里「每个头学到不同模式」这个说法有依据吗？"
                    "如果去掉几个头会怎样？"
                ),
                "keywords": ["子空间", "分工", "冗余", "剪枝", "局部", "句法"],
                "reference": (
                    "有观察依据：把训练好的多头模型拿来逐头可视化，能看到明显的分工 —— "
                    "有的头注意力集中在相邻位置（局部搭配），有的头跨越较长距离（句法/指代），"
                    "有的头即使内容不同也稳定看第一个 token（类似「无操作」的头）。"
                    "去掉几个头通常影响很小，说明存在冗余（这也是结构化剪枝能掉一大部分头的原因）；"
                    "但如果把所有头都去掉，或者换成单头再训练，效果会明显下降。"
                    "所以准确的说法是：多头提供了**多个独立子空间的视角**，"
                    "训练后自发形成功能分工，但这种分工是软的、有冗余的，不是严格设计出来的。"
                ),
                "explanation": "这类问题的加分点在于「承认冗余」——直接说「每个头都学到一个独一无二的功能」会显得没动过手。",
            },
        ],
    },
    # ------------------------------------------------------------------ tf-05
    {
        "code": "tf-05",
        "subject": "Transformer",
        "stage": "模型结构",
        "runner": "python",
        "title": "位置编码",
        "summary": "自注意力没有顺序感，位置得手动补",
        "definition": (
            "**为什么需要位置编码**：Self-Attention 是一个**置换等变**的算子 —— "
            "它把每个位置对所有位置做加权求和，唯一的「顺序信息」来自 Query 和 Key 的匹配。"
            "把输入序列打乱，输出只是跟着打乱，模型完全没有区分「猫追狗」和「狗追猫」的能力。\n\n"
            "RNN 的顺序信息是结构自带的（必须按顺序算），而 Attention 必须**显式注入**位置。做法是把位置编码"
            "**逐元素加到词嵌入上**（不是拼接）：`X = Embedding(tokens) + PE`。"
            "两者维度都是 `d_model`，相加不改变维度、也不增加参数。\n\n"
            "**原版 Transformer 用的正弦位置编码**，对每一对维度 `(2i, 2i+1)` 共享一个频率：\n\n"
            "```\nPE[pos][2i]   = sin(pos / 10000 ** (2i / d_model))\nPE[pos][2i+1] = cos(pos / 10000 ** (2i / d_model))\n```\n\n"
            "`i` 从 0 到 `d_model/2 - 1`。第 0 对的波长为 `2π`（周期最短、变化最快），"
            "越往后的维度频率越低，最后一对的波长接近 `10000 · 2π`。"
            "于是每个位置得到一个**由不同频率的正弦波组成的指纹**，"
            "低维负责区分邻近位置，高维负责区分远距离位置。\n\n"
            "**正弦编码为什么能表达相对位置**（核心考点）：\n\n"
            "对同一对维度，设 `a = pos / 10000^(2i/d_model)`、频率为 `w`，则\n\n"
            "```\nPE[pos] · PE[pos + k] = Σ_i [ sin(a)sin(a + k·w) + cos(a)cos(a + k·w) ]\n"
            "                      = Σ_i cos(k · w_i)\n```\n\n"
            "用了和角公式 `cos(α - β) = cosα cosβ + sinα sinβ`。"
            "右边**只含间隔 k，完全不含 pos**！也就是说：任意两个位置的内积只取决于它们的相对距离。"
            "这意味着模型只要用一个线性变换（旋转矩阵）就能从 `PE[pos]` 得到 `PE[pos + k]`，"
            "相对位置关系成了可线性表示的量 —— 这就是正弦编码被选中的理论理由。\n\n"
            "**其他路线**：BERT 用的是**可学习位置编码**（把 PE 当参数一起训，长度固定、无法外推）；"
            "现在长文本大模型基本改用 **RoPE**（把位置信息编码成对 Q/K 的旋转，天然刻画相对位置、外推更好）"
            "或 **ALiBi**（直接给注意力分数按距离加线性偏置）。"
        ),
        "plain": (
            "**Self-Attention 是一群没有座位号的人在开会**。每个人都能看到所有人的发言内容，"
            "谁跟自己的话题相关就多听几句 —— 但会议室里**没有任何座位信息**。"
            "于是「张三先发言、李四后发言」和反过来，对他们来说一模一样，"
            "整个句子的语序被彻底抹平。\n\n"
            "位置编码就是**给每个座位贴上座位号**，而且是贴得很有讲究的座位号："
            "不是简单的 1、2、3……而是一串由快慢不同的正弦波组成的「指纹」。\n\n"
            "为什么要用不同频率的波？想想**钟表**：秒针转得飞快，用来区分「现在这一秒和下一秒」；"
            "分针慢一些；时针更慢，用来区分「上午和下午」。"
            "任何时刻的时间，都是「时针角度 + 分针角度 + 秒针角度」的组合 —— "
            "低维的快速波精确区分邻近位置，高维的慢速波负责拉开远距离的位置。\n\n"
            "**相对位置为什么天然可算**：因为每个座位号的指纹是由 sin/cos 组成的，"
            "两个座位号一做点积，正弦的「和角公式」会**把各自的绝对位置消掉、只剩下两者的距离**。"
            "就像问「你和我隔了几个座位」，答案不需要知道你们具体坐在第几排 —— "
            "这正是模型做注意力时最需要的那种信息。"
        ),
        "example": (
            "import math\n"
            "\n"
            "\n"
            "def positional_encoding(max_len, d_model):\n"
            "    pe = []\n"
            "    for pos in range(max_len):\n"
            "        row = []\n"
            "        for i in range(d_model // 2):\n"
            "            angle = pos / (10000 ** (2 * i / d_model))   # 同一对 sin/cos 共用一个频率\n"
            "            row.append(math.sin(angle))\n"
            "            row.append(math.cos(angle))\n"
            "        pe.append(row)\n"
            "    return pe\n"
            "\n"
            "\n"
            "PE = positional_encoding(6, 8)\n"
            "for pos, row in enumerate(PE):\n"
            "    print(pos, [round(v, 4) for v in row[:4]])\n"
            "\n"
            "\n"
            "def dot(a, b):\n"
            "    return sum(x * y for x, y in zip(a, b))\n"
            "\n"
            "\n"
            "print(\"dot(PE[p], PE[p+2])，p = 0..3：\")\n"
            "for p in range(4):\n"
            "    print(\"  p =\", p, \"->\", round(dot(PE[p], PE[p + 2]), 6))"
        ),
        "example_output": (
            "0 [0.0, 1.0, 0.0, 1.0]\n"
            "1 [0.8415, 0.5403, 0.0998, 0.995]\n"
            "2 [0.9093, -0.4161, 0.1987, 0.9801]\n"
            "3 [0.1411, -0.99, 0.2955, 0.9553]\n"
            "4 [-0.7568, -0.6536, 0.3894, 0.9211]\n"
            "5 [-0.9589, 0.2837, 0.4794, 0.8776]\n"
            "dot(PE[p], PE[p+2])，p = 0..3：\n"
            "  p = 0 -> 2.563718\n"
            "  p = 1 -> 2.563718\n"
            "  p = 2 -> 2.563718\n"
            "  p = 3 -> 2.563718"
        ),
        "pitfalls": [
            "**以为 Transformer 和 RNN 一样「天然知道顺序」**：Self-Attention 是置换等变的，不注入位置信息时打乱词序、输出只是跟着打乱，模型完全无法区分语序。这一条常被追问「那你把位置编码去掉会怎样」。",
            "**位置编码的用法搞错**：是**逐元素相加**（`Embedding + PE`），不是 concat。相加要求两者维度都是 `d_model`，好处是不增加维度也不增加参数量；concat 会让维度翻倍，后面的 `W_q` 也得跟着改。",
            "**把指数写成 `i / d_model` 而不是 `2i / d_model`**：标准公式里第 i 对维度的频率是 `10000^(-2i/d_model)`，写成 `-i/d_model` 会让最低频那一维的波长差出去一大截，位置指纹的整体分布就变了 —— 这个错误不会报错，只能靠数值检查发现。",
            "**认为有了位置编码就能无限外推**：正弦编码在数学上可以算任意 pos，但模型学到的表示未必泛化；"
            "BERT 的可学习 PE 更是写死了长度。真正做长文本外推靠的是 RoPE（旋转位置编码，配合插值/缩放）和 ALiBi，"
            "而不是原始正弦编码。",
        ],
        "task": (
            "请实现 `positional_encoding(max_len, d_model)`：返回一个 `max_len × d_model` 的二维列表，"
            "每一行是一个位置的编码向量。\n\n"
            "用原版 Transformer 的正弦公式。对每一对维度 `(2i, 2i+1)`，共享同一个频率：\n\n"
            "```\n"
            "PE[pos][2i]   = sin(pos / 10000 ** (2 * i / d_model))\n"
            "PE[pos][2i+1] = cos(pos / 10000 ** (2 * i / d_model))\n"
            "```\n\n"
            "其中 `i` 从 0 到 `d_model // 2 - 1`，位置 `pos` 从 0 开始（`0 <= pos < max_len`）。\n\n"
            "注意指数里是 **2 * i**，不是 i。"
        ),
        "setup": "import math\n",
        "starter": (
            "def positional_encoding(max_len, d_model):\n"
            "    # 返回 max_len 行、d_model 列的二维列表\n"
            "    # 第 2i 维放 sin，第 2i+1 维放 cos，两者角度相同\n"
            "    pass\n"
        ),
        "hint": (
            "两层循环：外层 `for pos in range(max_len)`，内层 `for i in range(d_model // 2)`。\n"
            "内层算出 `angle = pos / (10000 ** (2 * i / d_model))`，"
            "然后往这一行 append 两个值：`math.sin(angle)` 和 `math.cos(angle)`。\n"
            "**同一个 i 算一次角度、用两次**，这样才能保证 sin 和 cos 共用频率、相对位置性质才成立。"
        ),
        "checker": TF05_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：Self-Attention 为什么需要位置编码？正弦编码为什么能表达相对位置？"
                ),
                "options": [
                    "Self-Attention 是置换等变的、本身没有顺序概念；正弦编码里 sin(a)sin(a+b)+cos(a)cos(b+…)=cos(b)，点积只依赖间隔而与绝对位置无关",
                    "因为位置编码可以把序列长度补齐到固定长度，方便批处理",
                    "因为正弦函数是有界的，能防止数值溢出",
                    "因为位置编码是可学习参数，可以记住每个位置",
                ],
                "answer_index": 0,
                "explanation": (
                    "前半句的关键词是「置换等变」：打乱输入，输出只是跟着打乱。"
                    "后半句要用和角公式说明「两个位置的内积只和间隔有关」——"
                    "这就是相对位置可线性表示的依据。B、C 都不是原因；"
                    "D 说反了，正弦编码是**固定公式、不参与训练**（BERT 用的才是可学习的那种）。"
                ),
            },
            {
                "type": "choice",
                "stem": "位置编码最终是怎么和词嵌入结合的？",
                "options": [
                    "逐元素相加：X = Embedding(tokens) + PE，两者维度都是 d_model",
                    "拼接到词嵌入后面，维度变成 2 * d_model",
                    "作为额外的一层网络放在 Embedding 之后",
                    "乘到 attention 权重矩阵上，作为权重的一部分",
                ],
                "answer_index": 0,
                "explanation": (
                    "是相加。这样不改变维度也不增加参数量，而且后续的 `W_q/W_k/W_v` 不用改。"
                    "B 会让维度翻倍，与后续所有形状都对不上；"
                    "C、D 都不是标准做法。"
                ),
            },
            {
                "type": "judge",
                "stem": "BERT 和原版 Transformer 一样，都使用固定的正弦位置编码。",
                "answer": False,
                "explanation": (
                    "原版 Transformer 用固定正弦编码；BERT 用的是**可学习位置编码**（把位置向量当参数训练），"
                    "好处是更贴合数据，代价是长度写死、无法外推超过 max_len。"
                ),
            },
            {
                "type": "blank",
                "stem": "正弦位置编码里，第 2i 维放 sin(pos / 10000^(2i/d_model))，第 2i+1 维放 ___（填函数名）",
                "hint": "填一个三角函数",
                "answer": "cos",
                "accept": ["cos", "cosine", "cos函数"],
                "explanation": "同一对维度共用频率，一个 sin 一个 cos，这是「相对位置可线性表示」的前提。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：你说正弦位置编码能表达相对位置，数学原理是什么？"
                    "为什么这个性质对注意力有用？"
                ),
                "keywords": ["和角公式", "点积", "间隔", "cos", "线性变换", "旋转"],
                "reference": (
                    "对同一对维度，PE 的两个分量是 `[sin(a), cos(a)]`（a 由 pos 和该维频率决定）。"
                    "把 `PE[pos]` 和 `PE[pos+k]` 做点积，两项分别是 `sin(a)sin(a+kw)` 和 `cos(a)cos(a+kw)`，"
                    "用和角公式 `cos(α-β)=cosαcosβ+sinαsinβ` 合并后得到 `cos(k·w)` —— "
                    "**绝对位置 pos 被消掉了，只剩下间隔 k**。对所有维度求和也一样，结果只依赖 k。"
                    "对注意力的意义是：模型想知道「我和他隔多远」时，不需要学一套随绝对位置变化的规则，"
                    "只要从这个内积（或一个固定的线性变换/旋转矩阵）里读出来就行，"
                    "所以相对位置的泛化能力比「可学习 PE 直接记位置」更好，也是 RoPE 沿用的思路。"
                ),
                "explanation": "能写出「和角公式 + pos 被消掉」这两步，这道题就满分了。",
            },
        ],
    },
    # ------------------------------------------------------------------ tf-06
    {
        "code": "tf-06",
        "subject": "Transformer",
        "stage": "模型结构",
        "runner": "none",
        "title": "Encoder-Decoder、残差与 LayerNorm",
        "summary": "三层结构、两条残差通路、归一化放哪",
        "definition": (
            "**Encoder 一层** = 多头 Self-Attention + FFN，每个子层外面包「残差 + LayerNorm」。"
            "注意力是**双向**的（不加 mask），每个位置能看到全部位置。`N` 层堆叠，输出仍是 `(n, d_model)`。\n\n"
            "**Decoder 一层** = 三个子层：\n\n"
            "1. **Masked Multi-Head Self-Attention** —— 因果 mask，位置 i 只能看到 `<= i`，"
            "因为自回归生成时不能偷看未来的 token；\n"
            "2. **Cross-Attention** —— `Q` 来自 decoder 的当前状态，`K / V` 来自 encoder 的输出，"
            "这是输入序列信息流入解码端的**唯一通道**（也是机器翻译里「对齐」发生的地方）；\n"
            "3. **FFN**（`d_model -> d_ff -> d_model`，中间 4 倍宽 + 非线性激活，逐位置独立）\n\n"
            "**Mask 的实现**：在注意力分数矩阵的**上三角**（未来位置）加上负无穷，"
            "softmax 之后这些位置的权重就精确为 0。工程上不会真写 `-inf`（会让整行变成 NaN），"
            "而是填一个极大负数，如 `-1e9`。关键是 mask 必须加在 **softmax 之前**，加在权重上就错了。\n\n"
            "**残差连接 `x + Sublayer(x)` 解决什么**：深层网络的反向传播是连乘，梯度容易指数级衰减。"
            "残差给梯度提供一条**恒等通路**：`∂(x + F(x))/∂x = 1 + F'(x)`，"
            "哪怕 `F'(x)` 非常小，梯度也能原样回传。这是网络能堆到几十上百层的前提。"
            "注意残差要求**维度一致**：注意力输出是 `(n, h·d_head)`，必须先过 `W_o` 投影回 `d_model` 才能相加。\n\n"
            "**LayerNorm vs BatchNorm（高频对比题）**：\n\n"
            "- **BatchNorm** 在 **batch 维**统计 mean / var（同一个特征、跨样本），"
            "所以依赖 batch 大小和样本分布；NLP 里序列长度不一、batch 一变小统计就失稳，"
            "推理时还得冻结统计量，训练和推理行为不一致。\n"
            "- **LayerNorm** 在**特征维**（最后一维 `d_model`）统计，**每个位置、每个样本各自独立**：\n"
            "  `y = γ · (x - μ) / √(σ² + ε) + β`，其中 `μ`、`σ` 只对这一条样本的这一个位置求。"
            "  与 batch 大小无关、与序列长度无关，训练和推理完全一致 —— 这就是 NLP 选 LN 的原因。\n\n"
            "**Pre-Norm 与 Post-Norm**：\n\n"
            "```\n"
            "Post-Norm（原版）: LN(x + Sublayer(x))\n"
            "Pre-Norm （主流）: x + Sublayer(LN(x))\n"
            "```\n\n"
            "Post-Norm 把 LN 放在残差**之后**，输出尺度统一，但深层时梯度要穿过归一化层才能回传，"
            "**必须配合 learning rate warmup** 才训得稳。Pre-Norm 把 LN 放在子层**之前**，"
            "残差通路是一条干净的恒等映射，梯度能一路无阻回传，所以训练更稳、能堆更深 —— "
            "现在的大模型（GPT 系列、Llama）基本都用 Pre-Norm，"
            "代价是要在最后一层之后**额外补一个 LN**，否则最后一层输出没有被归一化。"
        ),
        "plain": (
            "**残差连接像装了电梯**：一栋 100 层的大楼，如果只能一层一层爬楼梯，爬到高层早就没力气了"
            "（梯度衰减）；如果每层楼梯旁边都有电梯口，力气不够时可以直接坐电梯上下，"
            "问题就没了。`x + F(x)` 正是这个意思：`F(x)` 是楼梯（子层要学的那部分），`x` 是电梯（原样传下去）。\n\n"
            "有意思的是，装了电梯之后模型反而更愿意让楼梯只学「小改动」——"
            "反正已经有保底的通路，在 `x` 上微调就能变好，不必推倒重来。"
            "**这就是残差让深层网络真正可训练的原因**。\n\n"
            "**LayerNorm 像每层之后重新校准刻度**：过完一层注意力和 FFN，各维的数值尺度可能已经乱七八糟"
            "（有的维飘到 100，有的维缩到 0.01），下一层很难处理。"
            "LayerNorm 就是**把每个位置的特征重新拉回均值 0、方差 1**，再用两个可学习参数微调。"
            "关键在「每个位置自己算自己的」—— 所以 batch 里只有一条数据也能算、句子长短不一也没关系。"
            "BatchNorm 是「跨样本统计同一个特征」，batch 一小统计就失真，NLP 里根本用不了。\n\n"
            "**Mask 像考试时用挡板遮住后面的题**：做第 3 题不能偷看第 4 题的答案，"
            "否则训出来的模型是「抄答案」而不是「解题」。"
            "实现上就是在分数矩阵的上三角填一个极大的负数，softmax 一压，那些位置的权重就变成 0。"
        ),
        "example": (
            "原版 Transformer（N = 6 层）\n"
            "\n"
            "── Encoder 每一层 ────────────────────────────────\n"
            "  x ──> Multi-Head Self-Attention ──> (+) ──> LayerNorm ──┐\n"
            "  └──────────────────────────────────────────────────────┘   （残差）\n"
            "        ──> FFN ──> (+) ──> LayerNorm ──> 输出（形状不变）\n"
            "  （双向：不加 mask，每个位置能看到全部位置）\n"
            "\n"
            "── Decoder 每一层 ────────────────────────────────\n"
            "  1) Masked Self-Attention    因果 mask，位置 i 只能看 <= i\n"
            "  2) Cross-Attention          Q 来自 decoder，K / V 来自 encoder\n"
            "  3) FFN\n"
            "\n"
            "── 形状（d_model = 512，h = 8，d_head = 64）───────\n"
            "  Self-Attention : (n, 512) -> (n, 512)      必须回到 d_model 才能加残差\n"
            "  FFN            : (n, 512) -> (n, 2048) -> (n, 512)\n"
            "  LayerNorm      : 沿最后一维（512）归一化，每个位置独立\n"
            "  Mask           : (n, n) 上三角填 -1e9，softmax 后未来位置权重 = 0\n"
            "\n"
            "── 两种放法 ──────────────────────────────────────\n"
            "  Post-Norm:  LN(x + Sublayer(x))     原版，需要 warmup 才稳\n"
            "  Pre-Norm :  x + Sublayer(LN(x))     主流，更稳更易深\n"
            "              注意 Pre-Norm 要在最后一层后补一个 LN"
        ),
        "example_output": (
            "残差要求维度一致：子层输出必须回到 d_model = 512 才能相加（attention 靠 W_o，FFN 靠第二个线性层）\n"
            "LayerNorm 沿特征维归一化，与 batch 大小、序列长度都无关\n"
            "Masked Self-Attention：位置 i 只能看到 <= i 的位置（分数矩阵上三角填 -1e9）\n"
            "Cross-Attention 是 encoder 信息流入 decoder 的唯一通道\n"
            "Pre-Norm  : x + Sublayer(LN(x))    训练更稳，现在主流（最后一层后要补 LN）\n"
            "Post-Norm : LN(x + Sublayer(x))    原版，深层需要 learning rate warmup"
        ),
        "pitfalls": [
            "**残差相加时维度不匹配**：子层输出必须回到 `d_model`。多头注意力的输出是 `(n, h·d_head)`，要先经 `W_o` 投影；FFN 要先 `d_model -> d_ff` 再 `d_ff -> d_model`。`d_ff` 忘记映射回去、或者忘了 `W_o`，残差那一行直接 shape 报错。",
            "**LayerNorm 的归一化维度搞错**：LN 沿**最后一维（特征维）**归一化，不是 batch 维、也不是序列维。写错维度往往不会报错（形状能对上），但统计量含义完全变了，训练 loss 会一直不降——这种 bug 最难查。",
            "**Mask 用「乘 0」而不是「加 -inf」**：乘 0 是在 softmax **之后**动手，被遮的位置白白分走了概率质量、剩下的权重加不到 1；正确做法是在 softmax **之前**把未来位置的分数设成极大负数（实践用 `-1e9` 而不是 `-inf`，避免整行 `0/0` 出 NaN）。",
            "**Pre-Norm / Post-Norm 混着写**：原版是 Post-Norm，深层训练必须配 warmup；现在的模型普遍是 Pre-Norm，公式是 `x + Sublayer(LN(x))`，而且**最后一层之后要再补一个 LN**（很多人漏掉这一步，导致输出尺度不受控）。面试让你手写一个 Block 时，画错位置直接扣分。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：Decoder 里为什么一定要有 Masked Self-Attention？"
                    "如果去掉 mask 会发生什么？"
                ),
                "options": [
                    "因为生成是自回归的，位置 i 只能依赖已生成的 <= i 个 token；不加 mask 就是训练时偷看答案，而推理时根本拿不到未来 token，训练和推理不一致",
                    "因为不加 mask 会让显存占用翻倍",
                    "因为不加 mask 参数会变多，训练更慢",
                    "因为 mask 可以防止注意力权重过大，起到数值稳定的作用",
                ],
                "answer_index": 0,
                "explanation": (
                    "核心是**训练和推理一致**：训练时如果让位置 i 看到 i 之后的 token，"
                    "模型学的是「抄下一个词」，推理时却没有答案可抄，表现直接崩。"
                    "B、C、D 都不是原因——mask 不改变参数量和显存结构。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "面试官问：Transformer 里为什么用 LayerNorm 而不是 BatchNorm？"
                ),
                "options": [
                    "LN 在特征维上对每个样本独立归一化，不依赖 batch 大小和序列长度，训练与推理行为一致；而 NLP 的 batch 里序列长度不一，BN 的统计量不稳定",
                    "因为 LN 的计算量比 BN 小很多",
                    "因为 BN 只能用于卷积网络，用在全连接层会报错",
                    "因为 LN 有可学习参数，而 BN 没有",
                ],
                "answer_index": 0,
                "explanation": (
                    "关键词是「统计维度」和「变长序列」。BN 在 batch 维统计同一个特征，"
                    "NLP 里样本长度差异大、batch 又不能开很大，统计量很容易失真，"
                    "而且推理时要冻结统计量，和训练不一致。LN 逐样本逐位置独立，天然规避这些问题。"
                    "B、D 都不成立（LN 计算量并不更小，BN 也有可学习参数）；C 说法本身是错的。"
                ),
            },
            {
                "type": "judge",
                "stem": "Pre-Norm（把 LayerNorm 放在子层之前）比 Post-Norm 训练更稳定，所以现在的大模型基本都用 Pre-Norm。",
                "answer": True,
                "explanation": (
                    "Pre-Norm 的残差通路是干净的恒等映射，梯度能无阻回传，所以深层训练稳、对 warmup 依赖小。"
                    "代价是要在最后一层之后额外补一个 LN。"
                ),
            },
            {
                "type": "blank",
                "stem": "Masked Self-Attention 里，被遮住的位置在 softmax 之前加的分数值是什么？（工程实现通常写一个极大负数）",
                "hint": "填一个概念或常见数值",
                "answer": "-inf",
                "accept": ["-inf", "负无穷", "-1e9", "-1e9", "负无穷大", "-infinity", "-INF"],
                "explanation": (
                    "加 `-inf` 后 exp 得到 0，softmax 权重精确为 0。"
                    "实践中写 `-1e9` 这样的极大负数，避免整行全是 `-inf` 时出现 `0/0 = NaN`。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：残差连接到底解决了什么问题？"
                    "为什么没有它深层网络就训不动？"
                ),
                "keywords": ["梯度", "恒等通路", "连乘", "衰减", "退化", "1 + F'"],
                "reference": (
                    "残差 `x + F(x)` 的偏导是 `1 + F'(x)`，那个 `1` 就是一条**恒等通路**："
                    "即使 `F'(x)` 很小，梯度也能原样回传到浅层。"
                    "没有残差时，深层网络的梯度是各层雅可比连乘，"
                    "每层的小于 1 的因子相乘后指数级衰减，浅层几乎收不到有效梯度。"
                    "另外残差还缓解了「深层网络反而更差」的退化问题："
                    "模型可以选择让 `F(x) ≈ 0`，此时这一层退化成恒等映射，"
                    "至少不会比浅层网络更差，于是「加深」变成一件不会有害的事。"
                ),
                "explanation": "答分两点：梯度层面的恒等通路，以及结构层面的「最差也是恒等映射」。",
            },
        ],
    },
    # ------------------------------------------------------------------ tf-07
    {
        "code": "tf-07",
        "subject": "Transformer",
        "stage": "预训练与推理",
        "runner": "none",
        "title": "BERT 与 GPT 的架构差异",
        "summary": "完形填空和接话茬，两条技术路线",
        "definition": (
            "**相同点**：都是 Transformer 家族，骨架都是 Self-Attention + FFN + 残差 + LayerNorm，"
            "预训练 + 下游适配的两阶段范式也一样。**差异全在 mask 和预训练目标上**。\n\n"
            "| | BERT | GPT |\n"
            "| --- | --- | --- |\n"
            "| 结构 | Encoder-only | Decoder-only |\n"
            "| 注意力 | 双向，无 mask | 因果 mask，只能看左边 |\n"
            "| 预训练目标 | MLM：随机遮 15% 的词猜原词（+ NSP）| next-token：预测下一个词 |\n"
            "| loss 密度 | 只对 15% 被遮位置算 | **每个位置都算** |\n"
            "| 特殊 token | `[CLS]` / `[SEP]` | 无（用 prompt 组织）|\n"
            "| 擅长 | 理解：分类 / NER / 抽取式 QA | 生成 / 对话 / 代码 / 推理 |\n"
            "| 适配方式 | 下游 fine-tune | prompt / in-context learning |\n\n"
            "**BERT 的 [MASK] 带来的 train-test mismatch**：预训练时有 `[MASK]` 这个 token，"
            "但下游微调的输入里不会出现 `[MASK]`，模型见到的是「训练时从没见过的输入分布」。"
            "原论文的补丁是「80% 换成 `[MASK]`、10% 换成随机词、10% 保持不变」，"
            "让模型不能只依赖 `[MASK]` 这一种信号。后来的 RoBERTa 进一步去掉 NSP、改用动态 mask 并加大数据。\n\n"
            "**为什么 decoder-only 成了现在的主流**（这是当前最高频的开放题）：\n\n"
            "1. **目标统一**：预测下一个 token 一个目标就能覆盖理解、生成、翻译、代码等所有任务；"
            "而 MLM 需要为下游任务设计额外结构（比如分类头）。\n"
            "2. **训练信号更稠密**：next-token 在**每个位置**都有监督，MLM 只有 15% 的位置有；"
            "同样的数据量，GPT 的梯度信号多好几倍。\n"
            "3. **没有 train-test mismatch**：预训练和推理都是「给前缀、续写」，形式上完全一致。\n"
            "4. **天然支持 in-context learning**：只靠 prompt 就能做新任务，这正是 scaling 之后涌现的能力；"
            "而双向注意力在结构上做不到「按前缀续写」。\n"
            "5. **推理优化友好**：自回归 + 因果 mask 可以直接用 KV Cache 增量解码（见 tf-08）；"
            "双向注意力每一步都要重算全序列。"
        ),
        "plain": (
            "**BERT 是完形填空选手**：给他一句话，把中间几个词挖掉，让他根据**左右两边**的线索把词填回来。"
            "因为左右都能看，他特别擅长理解 —— 判断情感、找实体、从文章里抽出答案所在的片段。"
            "但他不会写文章：他的训练方式就是「填一个已知的空」，从来没有练过「下一个词接什么」。\n\n"
            "**GPT 是接话茬选手**：只给他前半句，让他往下接。他**只能看左边**，"
            "因为如果允许偷看右边，那就变成「抄答案」而不是「续写」了（tf-06 的因果 mask）。"
            "这个约束看起来更亏，但换来了一个巨大的好处：**他练过的就是「生成」这件事本身**。"
            "写代码、写文章、多轮对话，全都是「接着往下写」，所以一个模型能干所有事。\n\n"
            "**为什么后来接话茬赢了**：因为「往下接」这个目标太通用了。"
            "你把问题写进 prompt（当成前半句），答案自然就是「接下来该写的内容」——"
            "**理解任务被包装成了生成任务**。而完形填空选手每次换任务都得重新加一个输出头、重新微调，"
            "规模一大就不划算了。"
        ),
        "example": (
            "同样一副骨架，不同的 mask 和目标：\n"
            "\n"
            "                    BERT                        GPT\n"
            "  结构              Encoder-only                Decoder-only\n"
            "  注意力 mask       无（双向，全可见）           因果 mask（上三角遮住未来）\n"
            "  预训练目标        MLM：随机遮 15% 猜原词        next-token：预测下一个词\n"
            "                    + NSP（下一句是否连续）\n"
            "  loss 覆盖         只算被遮的 15% 位置            每个位置都算\n"
            "  输入形式          [CLS] 句子 [SEP] 句子         <bos> 句子...\n"
            "  [CLS] 用途        句向量，接分类头               无\n"
            "  擅长              分类 / NER / 抽取式 QA        生成 / 对话 / 代码 / 推理\n"
            "  适配方式          预训练 + 下游 fine-tune       预训练 + prompt / ICL\n"
            "  推理优化          一次前向出全部表示            因果结构 -> 可用 KV Cache\n"
            "\n"
            "  一句话：\n"
            "    BERT 是完形填空选手 —— 必须看到空的两边才能填\n"
            "    GPT  是接话茬选手 —— 只能凭前面说过的话往下接"
        ),
        "example_output": (
            "BERT：Encoder-only，双向 mask，MLM 只对 15% 位置算 loss，不能自回归生成，换任务要加输出头微调\n"
            "GPT ：Decoder-only，因果 mask，next-token 每个位置都算 loss，天然支持生成，靠 prompt 就能换任务\n"
            "loss 密度：next-token 比 MLM 多约 6~7 倍的有效监督信号\n"
            "推理：GPT 每步只依赖前缀 -> 可以 KV Cache 增量解码；双向注意力每步都要重算整条序列"
        ),
        "pitfalls": [
            "**一口咬定「双向一定比单向强」**：双向确实让 BERT 在理解类任务上样本效率更高，但 decoder-only 靠规模 + in-context learning 把理解任务也覆盖了。正确的答法是「看任务和数据规模」，而不是把结构钉死成谁更强。",
            "**忽略 BERT 的 train-test mismatch**：预训练里有 `[MASK]`、微调时没有，模型见到的输入分布不一致。原论文用「80% [MASK] / 10% 随机词 / 10% 不动」缓解，RoBERTa 又去掉 NSP、改动态 mask。被追问「MLM 有什么缺点」时要能说出这一条。",
            "**以为 GPT 的因果 mask 只在训练时用**：推理时必须**同样保留** mask。自回归解码时你只能看到已经生成的 token，如果推理时放开 mask，训练/推理不一致，生成会迅速崩坏。",
            "**把 encoder-only 和 encoder-decoder 混为一谈**：BERT 没有 decoder，不能直接做序列到序列的生成；机器翻译那类任务要用原版 Transformer 或 T5 / BART 这种 encoder-decoder 结构。名字里都有 Transformer，结构差别很大。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：BERT 和 GPT 在注意力 mask 上有什么本质区别？这个区别带来了什么后果？"
                ),
                "options": [
                    "BERT 不遮（双向可见），GPT 遮住未来的位置（因果 mask）；前者适合理解类任务，后者因为结构上只能「往前续写」而天然适合生成，也才能用 KV Cache 增量解码",
                    "BERT 遮住未来位置，GPT 双向可见，所以 GPT 理解能力更强",
                    "两者都遮住未来位置，区别只在预训练目标",
                    "BERT 只在训练时遮，GPT 只在推理时遮",
                ],
                "answer_index": 0,
                "explanation": (
                    "mask 决定了每个位置能看到什么，也就决定了模型能做什么。"
                    "双向让表示更「全局」，适合抽特征做理解；"
                    "因果 mask 让「前缀 -> 下一个词」这件事在结构上成立，"
                    "这才使生成和增量解码成为可能。B 说反了；C、D 都不是事实。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "面试官问：为什么现在主流大模型几乎都选 decoder-only，而不是 BERT 那样的 encoder-only？"
                ),
                "options": [
                    "因为 next-token 目标在每个位置都有监督、训练信号更稠密，和推理形式完全一致（没有 train-test mismatch），还能靠 prompt 做 in-context learning 统一所有任务",
                    "因为 decoder-only 的参数量天生比 encoder-only 少",
                    "因为 encoder 不能堆很多层，容量上不去",
                    "因为 decoder-only 不需要位置编码",
                ],
                "answer_index": 0,
                "explanation": (
                    "三个理由：目标统一、loss 密度高约 6~7 倍、训练与推理形式一致（可基于前缀续写、能用 KV Cache）。"
                    "B 不对，参数量和结构类型无关；C 不对，encoder 一样能堆深；"
                    "D 错，decoder-only 同样需要位置编码。"
                ),
            },
            {
                "type": "judge",
                "stem": "BERT 可以直接像 GPT 那样，以自回归的方式一个词一个词地把答案生成出来。",
                "answer": False,
                "explanation": (
                    "BERT 是双向的、没有因果 mask，也没有练过「预测下一个词」，"
                    "结构上就无法保证「生成第 i 个词时不依赖后面」。"
                    "它擅长的是抽特征做判别（分类、NER、抽取式 QA），不能直接做生成。"
                ),
            },
            {
                "type": "blank",
                "stem": "BERT 的预训练任务叫 MLM，它的全称是 Masked Language ___（填一个英文单词）",
                "hint": "填一个英文单词",
                "answer": "Modeling",
                "accept": ["Modeling", "Modelling", "Model"],
                "explanation": "Masked Language Modeling：随机遮住 15% 的词，让模型根据上下文把原词预测回来。",
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：BERT 的 [MASK] token 会带来什么问题？"
                    "原论文和后续工作是怎么缓解的？"
                ),
                "keywords": ["train-test mismatch", "分布不一致", "80%", "随机词", "NSP", "RoBERTa"],
                "reference": (
                    "问题是 **train-test mismatch**：预训练时输入里有 `[MASK]`、"
                    "而下游微调和推理时根本不会出现这个 token，模型面对的是没见过的输入分布；"
                    "而且如果 100% 都替换成 `[MASK]`，模型可能只在「见到 `[MASK]` 时才认真建模」，"
                    "对未被遮位置的表示学习反而不充分。"
                    "原论文的缓解方式是三个比例：80% 换成 `[MASK]`、10% 换成随机词、10% 保持原词不变，"
                    "逼模型始终对每个位置保持警惕。"
                    "RoBERTa 的做法是去掉 NSP、把静态 mask 换成动态 mask（每个 epoch 重新随机遮）、"
                    "大幅增加数据和训练步数，效果明显提升。"
                ),
                "explanation": "能说出「80/10/10」和「动态 mask」这两个具体细节，说明真的读过论文而不是只背结论。",
            },
        ],
    },
    # ------------------------------------------------------------------ tf-08
    {
        "code": "tf-08",
        "subject": "Transformer",
        "stage": "预训练与推理",
        "runner": "none",
        "title": "推理加速与 KV Cache",
        "summary": "缓存 K 和 V 省重复计算，代价是显存",
        "definition": (
            "**没有缓存时的浪费**：自回归生成第 t 个 token 时，模型要把整段序列 `1..t` 重新做一次前向。"
            "而其中前 `t-1` 个 token 的 K、V 在之前每一步都已经算过了，**一模一样，只是被丢掉了**。"
            "于是注意力部分的计算量是 `1² + 2² + ... + n² = O(n³)`。\n\n"
            "**KV Cache 缓存的是什么**：每一层、每一个头、每一个**历史位置**的 Key 和 Value 投影结果，"
            "形状是 `(batch, h, t, d_head)`。每生成一个新 token，"
            "只算这一个 token 的 `q / k / v`，把新的 `k / v` 拼到缓存末尾，"
            "然后用它的 `q` 去和整个 `K_cache` 打分、对 `V_cache` 加权求和。"
            "注意力计算量降到 `1 + 2 + ... + n = O(n²)`。\n\n"
            "**为什么只缓存 K 和 V，不缓存 Q（必考）**：\n\n"
            "- `Q` 是「**当前这一步想问什么**」。第 t 步只需要用**当前 token 的 Q** 去查所有历史 K；"
            "**历史 token 的 Q 在之后的任何一步都不会再被用到**，缓存它们纯属浪费。\n"
            "- `K` 和 `V` 是「**资料**」。当前位置的 Q 要和**全部历史 K** 算分数，"
            "再用这些分数对**全部历史 V** 加权求和。所以每往下一步，所有历史的 K、V 都要被重新使用一次。\n"
            "- 一句话记法：**Q 是一次性的提问，K/V 是会被反复查阅的资料**。\n\n"
            "**显存怎么算**（7B 模型，`L = 32` 层、`h = 32` 头、`d_head = 128`、fp16 每元素 2 字节）：\n\n"
            "```\n每 token 每层的元素数 = 2 (K 和 V) × h × d_head = 2 × 32 × 128 = 8192\n"
            "每 token 每层字节数   = 8192 × 2 = 16384 B = 16 KB\n"
            "每 token 全部层       = 16 KB × 32 = 512 KB ≈ 0.5 MB\n"
            "batch = 32、上下文 4096：512 KB × 32 × 4096 ≈ 64 GB\n"
            "```\n\n"
            "**结论：长上下文推理的显存瓶颈往往不是模型权重（7B fp16 约 14 GB），而是 KV Cache（64 GB）。**"
            "这就是 vLLM、PagedAttention 存在的理由。\n\n"
            "**优化方向**：\n\n"
            "- **MQA**：所有头共享一份 K/V，KV Cache 直接缩到 `1/h`，但效果有损\n"
            "- **GQA**：折中方案，把 h 个头分成 g 组、组内共享 K/V（Llama 2 70B / Llama 3 都用），"
            "显存降到 `g/h`，效果接近 MHA\n"
            "- **KV Cache 量化**：存成 fp8 / int8，显存再减半到四分之一\n"
            "- **PagedAttention**：像操作系统的虚拟内存一样按页管理，消除碎片、支持前缀共享\n"
            "- 稀疏/滑窗注意力、丢弃远距离 KV\n\n"
            "另外要区分推理的两个阶段：**Prefill**（处理整段 prompt）是大矩阵乘，**compute-bound**；"
            "**Decode**（逐个生成 token）每步只算一个 token，**memory-bound** —— "
            "瓶颈在显存带宽而不是算力，这也是 KV Cache 和批处理（continuous batching）特别重要的原因。"
        ),
        "plain": (
            "**KV Cache 就像写论文时手边的小抄**：你每写一段都要回头查之前查过的资料"
            "（每生成一个 token 都要和历史所有 token 做注意力）。"
            "如果每次查资料都重新去图书馆翻一遍（把整段序列重新前向一遍），那就太慢了。"
            "聪明的做法是：**把查过的资料内容抄在便签上贴在桌角**，后面每次直接看便签。\n\n"
            "那为什么不把小抄写得更全一点？因为**「问题」不用抄**。"
            "「我这一段想问什么」这句话只对当前这段有用，写完了就作废；"
            "而「资料内容」是后面每一段都可能再翻出来用的。"
            "这就是「只缓存 K/V、不缓存 Q」的生活化版本：**Q 是一次性的提问，K/V 是会被反复查阅的资料**。\n\n"
            "**小抄的代价是桌子不够放**：模型权重是固定的十几 GB，像书架上那几本书；"
            "而小抄会随对话长度**线性增长** —— 上下文 4096、batch 32 时能长出 60 多 GB，"
            "比书还占地方。所以长上下文推理经常不是「算不动」，而是「放不下」。"
            "GQA、KV 量化、分页管理这些优化，本质上都是在想办法让这张桌子能多摊几张便签。"
        ),
        "example": (
            "自回归生成第 t 个 token：用当前 token 的 Q 去和历史全部 token 的 K 打分。\n"
            "\n"
            "── 不用 KV Cache：每步都把整段重新算一遍 ──────────\n"
            "  第 1 步：算长度 1 的注意力\n"
            "  第 2 步：把长度 2 的整段重新算一遍（第 1 个 token 的 K/V 再算一次）\n"
            "  ...\n"
            "  第 t 步：把长度 t 的整段重新算一遍\n"
            "  注意力计算总量 = 1² + 2² + ... + n² = O(n³)\n"
            "\n"
            "── 用 KV Cache：只算新 token，历史 K/V 直接查表 ──\n"
            "  第 t 步：只算 x_t 的 q_t / k_t / v_t\n"
            "    K_cache = concat(K_cache, k_t)   形状 (batch, h, t, d_head)\n"
            "    V_cache = concat(V_cache, v_t)   形状 (batch, h, t, d_head)\n"
            "    score   = q_t @ K_cacheᵀ / √d_head          (batch, h, 1, t)\n"
            "    out     = softmax(score) @ V_cache          (batch, h, 1, d_head)\n"
            "  注意力计算总量 = 1 + 2 + ... + n = O(n²)\n"
            "\n"
            "── 显存（7B：L = 32, h = 32, d_head = 128, fp16）──\n"
            "  每 token 每层 = 2 × 32 × 128 × 2 B = 16 KB\n"
            "  每 token 全部层 = 16 KB × 32 = 512 KB ≈ 0.5 MB\n"
            "  batch = 32、上下文 4096  ≈ 0.5 MB × 32 × 4096 ≈ 64 GB\n"
            "\n"
            "── 推理两阶段 ────────────────────────────────────\n"
            "  Prefill：一次处理整段 prompt   -> 大矩阵乘，compute-bound\n"
            "  Decode ：每步只生成一个 token  -> 每次都要读全部 KV，memory-bound"
        ),
        "example_output": (
            "缓存内容：每一层、每一个头里所有历史位置的 K 和 V，形状 (batch, h, t, d_head) —— 不含 Q\n"
            "不缓存 Q：Q 只在当前步用一次，历史 Q 之后再也不会被用到；K/V 是「资料」，之后每一步都要被新 Q 查\n"
            "省下的计算：注意力部分从 O(n³) 降到 O(n²)；但每步仍是 O(t) 的读 KV，不是 O(1)\n"
            "显存（7B：L=32, h=32, d_head=128, fp16）：每 token 每层 16 KB -> 全部层约 0.5 MB/token\n"
            "  batch=32、上下文 4096 时约 0.5 MB × 32 × 4096 ≈ 64 GB（远超 7B 权重的约 14 GB）\n"
            "结论：长上下文推理的显存瓶颈往往是 KV Cache，不是权重"
        ),
        "pitfalls": [
            "**以为 KV Cache 缓存的是 hidden states 或 attention 输出**：缓存的是每一层、每个头**做完投影之后**的 K 和 V。所以它是「每层各存一份」，不同层的 cache 不能共用、也不能只存最后一层——把这一点说错，显存估算就全错了。",
            "**以为可以顺手把 Q 也缓存起来复用**：Q 是当前步的「提问」，只参与本步计算；历史 Q 在之后的步骤里不会再被用到。真正被反复复用的是 K（被所有新 Q 打分）和 V（被权重加权求和）。",
            "**只按模型权重估显存、完全不算 KV Cache**：7B fp16 权重约 14 GB，看起来一张卡塞得下；但 batch 32 + 上下文 4096 时 KV Cache 能到 64 GB。上线前必须把「权重 + KV Cache + 激活 + 框架开销」一起算，这也是 GQA / KV 量化 / PagedAttention 被发明出来的原因。",
            "**以为 KV Cache 把复杂度降到 O(n) 了**：它消除的是「每步重算历史」这笔浪费（注意力计算从 `O(n³)` 降到 `O(n²)`），但第 t 步仍然要读全部 t 个历史 K/V，单步是 `O(t)`。KV Cache 换来的是**时间**，付出的是**显存**，而且单步延迟随上下文增长依然是线性的。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "quizzes": [
            {
                "type": "choice",
                "stem": (
                    "面试官问：KV Cache 缓存的具体是什么？为什么不把 Q 也一起缓存？"
                ),
                "options": [
                    "缓存每层每个头里历史位置的 K 和 V；Q 只代表当前步的「提问」，历史 Q 之后再也不会被用到",
                    "缓存每层每个头里历史位置的 Q、K、V，只是为了省显存才省略 Q",
                    "缓存的是每个位置的隐藏层输出 hidden state，复用给下一层",
                    "缓存的是 attention 权重矩阵，避免重复做 softmax",
                ],
                "answer_index": 0,
                "explanation": (
                    "K/V 是会被反复查阅的「资料」，Q 是一次性的「提问」。"
                    "B 说反了因果（不是省显存才省略，是根本不需要）；"
                    "C 混淆了 hidden state 和投影后的 K/V（每层各自的 cache 不能共用）；"
                    "D 不对，权重矩阵是每步新算的，而且它的大小也是 O(t²)，缓存它反而更亏。"
                ),
            },
            {
                "type": "choice",
                "stem": (
                    "面试官问：一个 7B 模型（32 层、32 头、head_dim 128）用 fp16 推理，"
                    "batch 32、上下文长度 4096，KV Cache 大概占多少显存？"
                ),
                "options": [
                    "约 64 GB —— 每 token 每层 2×32×128×2 字节 = 16 KB，乘以 32 层再乘 32×4096",
                    "约 14 GB —— 和模型权重差不多",
                    "约 2 GB —— 只存 K 和 V 两个张量，很小",
                    "约 512 MB —— 每个 token 只占 0.5 MB",
                ],
                "answer_index": 0,
                "explanation": (
                    "`2 × h × d_head × 2B = 2×32×128×2 = 16384 B = 16 KB`（每 token 每层，K 和 V 各一份），"
                    "乘 32 层得 512 KB/token，再乘 `32 × 4096 = 131072` 个 token，约 64 GB。"
                    "D 只算了单个 token、忘了乘 batch 和序列长度，是最常见的算错方式。"
                ),
            },
            {
                "type": "judge",
                "stem": "用了 KV Cache 之后，生成长度为 n 的序列时，注意力部分的计算复杂度从 O(n³) 降到了 O(n²)。",
                "answer": True,
                "explanation": (
                    "省掉的是「每步重算历史 K/V」的重复计算：原来每步 O(t²)、累计 O(n³)，"
                    "现在每步 O(t)（用当前 Q 查全部历史 K/V）、累计 O(n²)。"
                    "注意单步仍是 O(t)，不是 O(1)。"
                ),
            },
            {
                "type": "blank",
                "stem": "7B 模型（32 层、32 头、head_dim 128）用 fp16 推理，每个 token 的 KV Cache 大约是 ___ MB（填数字）",
                "hint": "只填数字",
                "answer": "0.5",
                "accept": ["0.5", "0.5MB", "0.5 MB", "0.51", "0.52"],
                "explanation": (
                    "`2 × 32 × 128 × 2 B = 16 KB`（每 token 每层），乘 32 层得 512 KB ≈ 0.5 MB。"
                    "乘上 batch 和上下文长度，很容易就到几十 GB。"
                ),
            },
            {
                "type": "short",
                "stem": (
                    "面试官问：线上长上下文推理显存不够用了，你会从哪些方向优化？"
                    "请说出至少三个方向并说明各自省在哪。"
                ),
                "keywords": ["GQA", "MQA", "量化", "PagedAttention", "KV Cache", "滑窗"],
                "reference": (
                    "先定位：`权重 + KV Cache + 激活 + 框架开销` 哪一项是大头，通常长上下文时 KV Cache 占主导。"
                    "方向一，**减少 K/V 的份数**：MQA 让所有头共享一份 K/V（省到 `1/h`，效果有损），"
                    "GQA 折中成按组共享（Llama 2/3 的做法，显存降到 `g/h`、效果接近 MHA）。"
                    "方向二，**降低每个元素的位宽**：KV Cache 量化成 fp8 / int8，显存再降 2~4 倍，"
                    "对长上下文通常几乎无损。"
                    "方向三，**消除碎片、提高复用**：PagedAttention 按页管理 KV，"
                    "消除预留造成的碎片，还支持多个请求共享同一段前缀（system prompt 只存一份）。"
                    "方向四，**少存一些**：滑窗/稀疏注意力或丢弃远距离 KV，只保留最近的一部分。"
                    "另外工程上还可以用 continuous batching 提吞吐、把 decode 阶段的 batch 开大以摊薄权重读取。"
                    "要提醒一点：这些手段多数是在「显存换效果」之间权衡，压得太狠会掉点，得按业务指标回归验证。"
                ),
                "explanation": "这题答得好的标志是：先算账定位瓶颈，再给方案，最后说清楚每个方案的代价。",
            },
        ],
    },
]