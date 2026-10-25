"""科目：多模态与部署（4 课）。

前两课讲「非纯文本输入怎么处理」：图片交给多模态模型、扫描件交给 OCR。
后两课讲「做出来的东西怎么跑到线上、怎么跑到手机上」：Docker 编排、小程序登录态。

对应项目 `services/vision_service.py`、`data_pipeline.py`、`Dockerfile`、`miniprogram/`。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）
"""

VISION_CHECKER = """
try:
    import hashlib

    assert extract_json('{"a": 1}') == {"a": 1}, "干净 JSON 要直接解析成功"
    assert extract_json('```json\\n{"a": 1}\\n```') == {"a": 1}, "要去掉 ```json 围栏再解析"
    assert extract_json('结果如下：{"a": 1} 以上。') == {"a": 1}, "模型爱加前后缀，要取第一个 { 到最后一个 }"
    assert extract_json('{"a": {"b": 2}}') == {"a": {"b": 2}}, "嵌套对象要取到最外层的右花括号"
    assert extract_json('{"a": 1') is None, "括号没闭合必须返回 None，不能让异常冒出去"
    assert extract_json('抱歉，我看不清这张图') is None, "完全没有 JSON 时返回 None"
    assert extract_json('') is None, "空字符串返回 None"
    assert extract_json('{"a": 1} 和 {"b": 2}') is None, "两段 JSON 拼在一起时首尾切片不是合法 JSON，应返回 None 而不是硬猜一个"
    assert extract_json('[1, 2]') is None, "数组不是我们要的对象结构，返回 None"

    assert image_key(b"abc") == hashlib.md5(b"abc").hexdigest(), "缓存键就是图片字节的 md5 十六进制"
    assert image_key(b"abc") == image_key(b"abc"), "同一张图必须得到同一个键（这样才能命中缓存）"
    assert image_key(b"abc") != image_key(b"abd"), "内容不同键必须不同"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except Exception as e:
    print("__FAIL__ 解析过程出错（异常必须被吞掉并返回 None）：" + str(e))
"""

OCR_CHECKER = """
try:
    lines = [
        {"text": "失物招领：本园区拾到", "top": 10, "height": 12},
        {"text": "一把黑色折叠伞，请失主", "top": 25, "height": 12},
        {"text": "到游客中心认领。", "top": 40, "height": 12},
        {"text": "第 1 页", "top": 200, "height": 12},
    ]
    r = merge_lines(lines)
    assert r == ["失物招领：本园区拾到一把黑色折叠伞，请失主到游客中心认领。", "第 1 页"], "前三行间距只有 3，要合并成一段；第 4 行隔了 148，要另起一段，现在是 %r" % (r,)

    assert merge_lines([]) == [], "空输入返回空列表"
    assert merge_lines([{"text": "a", "top": 0, "height": 10}]) == ["a"], "只有一行时直接返回它"

    r2 = merge_lines(lines[:2], max_gap=0)
    assert r2 == ["失物招领：本园区拾到", "一把黑色折叠伞，请失主"], "max_gap=0 时只要有间隙就不合并，现在是 %r" % (r2,)

    shuffled = [lines[1], lines[0], lines[2]]
    r3 = merge_lines(shuffled)
    assert r3 == ["失物招领：本园区拾到一把黑色折叠伞，请失主到游客中心认领。"], "输入乱序时要先按 top 排序再合并，现在是 %r" % (r3,)

    r4 = merge_lines([
        {"text": "A", "top": 0, "height": 10},
        {"text": "B", "top": 12, "height": 10},
        {"text": "C", "top": 30, "height": 10},
    ], max_gap=2)
    assert r4 == ["AB", "C"], "A 底边 10、B 的 top 12，间隙 2 <= 2 要合并；B 底边 22、C 的 top 30，间隙 8 > 2 要断开。注意算的是「下一行 top - 上一行底边」，现在是 %r" % (r4,)
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, IndexError) as e:
    print("__FAIL__ 参数或数据结构不对：" + str(e))
"""

DOCKER_CHECKER = """
try:
    svc = {"app": ["milvus"], "milvus": ["etcd", "minio"], "etcd": [], "minio": []}
    o = startup_order(svc)
    assert len(o) == 4, "四个服务都要出现一次，现在是 %r" % (o,)
    assert o.index("etcd") < o.index("milvus"), "etcd 必须在 milvus 之前启动"
    assert o.index("minio") < o.index("milvus"), "minio 必须在 milvus 之前启动"
    assert o.index("milvus") < o.index("app"), "milvus 必须在 app 之前启动"

    assert startup_order({}) == [], "没有服务时返回空列表"
    assert startup_order({"a": []}) == ["a"], "没有依赖的服务直接返回"

    def expect_error(graph, why):
        try:
            startup_order(graph)
        except ValueError:
            return
        raise AssertionError(why)

    expect_error({"a": ["b"], "b": ["a"]}, "a 依赖 b、b 依赖 a 是循环依赖，必须抛 ValueError")
    expect_error({"a": ["a"]}, "服务依赖自己是循环依赖，必须抛 ValueError")
    expect_error({"app": ["nope"]}, "依赖了不存在的服务，必须抛 ValueError，不能静默忽略")

    diamond = {"d": ["b", "c"], "b": ["a"], "c": ["a"], "a": []}
    od = startup_order(diamond)
    assert od.index("a") < od.index("b") and od.index("a") < od.index("c"), "菱形依赖里 a 要最先启动"
    assert od.index("b") < od.index("d") and od.index("c") < od.index("d"), "d 要最后启动"
    assert len(od) == 4, "菱形结构里 a 只能出现一次，不能重复启动"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, AttributeError) as e:
    print("__FAIL__ 参数或返回结构不对：" + str(e))
"""

MINI_CHECKER = """
try:
    calls = []

    def api_ok(t):
        calls.append(t)
        return (200, "ok")

    assert call_with_relogin("t", api_ok, lambda: "new") == (200, "ok"), "第一次就成功时原样返回"
    assert calls == ["t"], "成功时不能多调一次登录，现在是 %r" % (calls,)

    calls2 = []
    logins = {"n": 0}

    def api_401_once(t):
        calls2.append(t)
        return (401, None) if t == "old" else (200, "data")

    def login():
        logins["n"] += 1
        return "new"

    assert call_with_relogin("old", api_401_once, login) == (200, "data"), "401 之后换新 token 重试，应该拿到 200"
    assert calls2 == ["old", "new"], "调用顺序必须是「旧 token 失败 → 新 token 重试」，现在是 %r" % (calls2,)
    assert logins["n"] == 1, "只应该登录一次"

    calls3 = []

    def always_401(t):
        calls3.append(t)
        return (401, None)

    assert call_with_relogin("x", always_401, lambda: "y", max_relogin=1) == (401, None), "重登后还是 401 就放弃，把 401 返回给上层"
    assert len(calls3) == 2, "max_relogin=1 表示首次 + 重试 1 次，共 2 次调用，现在是 %d 次" % len(calls3)

    calls4 = []

    def api401(t):
        calls4.append(t)
        return (401, None)

    assert call_with_relogin("x", api401, lambda: "y", max_relogin=0) == (401, None), "max_relogin=0 表示不重登"
    assert len(calls4) == 1, "不重登时只调用 1 次接口"

    calls5 = []

    def api500(t):
        calls5.append(t)
        return (500, "err")

    assert call_with_relogin("x", api500, lambda: "y") == (500, "err"), "500 不是登录态问题，不能被当成 401 去重登"
    assert len(calls5) == 1, "500 时不应该触发登录"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError) as e:
    print("__FAIL__ 参数或返回结构不对：" + str(e))
"""

LESSONS = [
    {
        "code": "mm-vision",
        "subject": "多模态与部署",
        "stage": "多模态输入",
        "runner": "python",
        "title": "多模态视觉理解与结构化输出",
        "summary": "模型返回的 JSON 从来不是干净 JSON",
        "definition": """**多模态模型 = 能直接吃图片的模型。** 它和 OCR 解决的问题不一样：

| | OCR（PaddleOCR） | 多模态大模型 |
|---|---|---|
| 输出 | 图上有哪些字 + 坐标 | 「这是什么、什么颜色、什么牌子」 |
| 擅长 | 票据、表格、扫描件 | 失物招领、商品识别、场景理解 |
| 成本 | 本地 CPU 就能跑 | 要调 API，2~4 秒 |

失物招领要的是「一把黑色折叠伞」，不是「图上有『折叠伞』三个字」——所以项目最终选了多模态。

**结构化输出是刚需**：下游要存库、要按字段比对，就必须拿到 JSON 而不是一段话。但模型的输出**从来不是干净的 JSON**，常见形态：

```
{"name": "伞"}                          ← 理想情况
```json
{"name": "伞"}
```                                      ← 带 markdown 围栏
识别结果如下：{"name": "伞"} 希望有帮助   ← 带前后缀
{"name": "伞"                            ← 括号没闭合（被截断）
```

所以解析器必须做三件事：**去围栏 → 取第一个 `{` 到最后一个 `}` → try/except 包住 json.loads**。任何一步失败都返回 `None`，**绝不能让异常冒泡泡到业务层**。

**按内容哈希缓存**：同一张图在「选图预识别」和「提交入库」会被调用两次。用图片字节的 md5 当缓存键、TTL 几分钟，第二次直接命中，省一次 2~4 秒的模型往返。多进程部署时缓存不共享，只是多花一次调用，不影响正确性。

**失败必须优雅降级**：识别失败 → 返回 `ok=False` → 调用方退回「用户手填名称」。**识别是增强功能，不能成为报失流程的单点故障。**

**项目落点**：`services/vision_service.py` 的 `invoke_vision()` 直接走 `LLM_VISION_MODEL`（多模态模型），解析逻辑就是「去围栏 + 首尾花括号 + json.loads」，缓存键是图片内容的 md5。""",
        "plain": """你让同事看一眼照片：「这是什么？」

- 他可能只回 `伞`（不带格式）
- 可能回「好的，我看了一下：{"name": "伞"}，还需要什么吗？」（带前后缀）
- 也可能回一半就被打断（括号没闭合）

你要的是那个 JSON，所以得自己从一堆废话里把它抠出来 —— 而且抠不出来时不能当场崩溃，只能说「这次没识别出来，你手动填一下」。""",
        "example": """import json

raw = '```json\\n{"name": "黑色折叠伞", "color": "黑"}\\n```'
try:
    json.loads(raw)
except Exception as e:
    print("直接解析失败:", type(e).__name__)

start, end = raw.find("{"), raw.rfind("}")
print("清洗后:", json.loads(raw[start:end + 1]))""",
        "example_output": """直接解析失败: JSONDecodeError
清洗后: {'name': '黑色折叠伞', 'color': '黑'}""",
        "pitfalls": [
            "直接 `json.loads(response)`：模型带个 ```json 围栏就整条链路崩掉",
            "解析失败让异常冒到业务层：图片识别挂了，连报失单都提交不了",
            "同一张图重复调模型：选图预识别一次、提交再识别一次，白花 2~4 秒",
            "用图片文件名当缓存键：用户换图但文件名一样（都叫 image.jpg）时会命中错误缓存",
        ],
        "task": """请实现两个函数：

1. `extract_json(text)`：从模型返回里抽出 JSON 对象
   - 取**第一个 `{`** 到**最后一个 `}`** 之间的内容
   - 解析成功且结果是 dict → 返回该 dict
   - 找不到花括号、解析失败、结果不是 dict、空字符串 → 返回 `None`
   - **任何异常都不能往外抛**

2. `image_key(data)`：图片字节的缓存键
   - 返回 `md5(data)` 的十六进制字符串""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """`start = text.find("{")`、`end = text.rfind("}")`，任一为 -1 或 `end < start` 就返回 None。切片后 `json.loads` 包在 `try/except Exception: return None` 里，最后再判一次 `isinstance(obj, dict)`。""",
        "checker": VISION_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "失物招领场景为什么选多模态模型而不是 OCR？",
                "options": [
                    "OCR 不能识别中文",
                    "业务要的是「这是什么物品、什么颜色」，而不是「图上有哪些字」",
                    "多模态模型更便宜",
                    "OCR 无法处理 JPG",
                ],
                "answer_index": 1,
                "explanation": "OCR 输出的是文字和坐标，回答不了「这是一把黑色折叠伞」。多模态模型能给出物品语义，正好匹配失物匹配的需求。",
            },
            {
                "type": "choice",
                "stem": "解析模型返回的 JSON 时，为什么要先 `find(\"{\")` 再 `rfind(\"}\")`？",
                "options": [
                    "为了让代码看起来更复杂",
                    "模型常带 markdown 围栏或前后解释文字，直接 json.loads 会失败",
                    "这样可以自动修复语法错误",
                    "为了兼容 Python 2",
                ],
                "answer_index": 1,
                "explanation": "首尾花括号切片能把「好的，结果如下：{...} 希望有帮助」里的 JSON 抠出来。但它不是万能的——两段 JSON 拼一起时仍会失败，所以要 try/except 兜底。",
            },
            {
                "type": "judge",
                "stem": "图片识别失败时，应该抛出异常让调用方知道，这样更有利于排查问题。",
                "answer": False,
                "explanation": "识别是增强功能。抛异常会让报失主流程也失败。正确做法是返回 `ok=False` 并记录日志，业务降级为「用户手填」。",
            },
            {
                "type": "blank",
                "stem": "用图片内容做缓存键时，常用的摘要算法是______（输出 32 位十六进制）。",
                "answer": "md5",
                "hint": "填三个字母，就是最常见的那个摘要算法",
                "explanation": "`hashlib.md5(data).hexdigest()`。用它而不是文件名，是因为不同图片可能同名、同一图片可能改名。",
            },
        ],
    },
    {
        "code": "mm-ocr",
        "subject": "多模态与部署",
        "stage": "多模态输入",
        "runner": "python",
        "title": "OCR 文档解析与版面还原",
        "summary": "OCR 给你的是带坐标的碎行，不是段落",
        "definition": """**OCR 的输出不是「一段文字」，而是「一堆带坐标的文本行」。**

PaddleOCR 的返回大概长这样：

```python
[
  [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], ("失物招领：本园区拾到", 0.98)],
  [[...], ("一把黑色折叠伞，请失主", 0.97)],
]
```

每行都带四个角点坐标和置信度。要还原成可读的段落，得自己做三件事：

**① 按 y 坐标排序并合并**

OCR 是按检测框顺序返回的，不一定从上到下。先按 `top` 排序，再看相邻两行的垂直间隙：

```
gap = 下一行.top - (上一行.top + 上一行.height)
gap <= 阈值  → 同一段，直接拼接
gap >  阈值  → 另起一段
```

**中文拼接不要加空格**。中文换行是排版折行，不是词间分隔；加空格会变成「请 失主 到 游客 中心」。

**② 去页眉页脚**

「第 1 页」「XX 公司机密」这类内容在每页重复，入库后会变成高频噪声：同一句话出现 50 次，BM25 的 idf 被拉低、向量检索也容易被它带偏。常见做法是统计「在多页同一位置重复出现的行」并剔除。

**③ 能抽文字就别 OCR**

电子版 PDF（文字可选）直接 `pdfplumber` / `PyMuPDF` 抽文字，又快又准。只有扫描件才需要 OCR。项目里 `extract_text_from_pdf` 用的是 OCR，是因为那份材料本来就是扫描件。

**项目落点**：`data_pipeline.py` 的 `extract_text_from_pdf()` 调 PaddleOCR、把每页每行的 `line[1][0]` 取出来拼成文本，再做基础清洗（去空格、去制表符）。""",
        "plain": """OCR 像一个不识字的人在抄书：他只能一行一行抄，抄完不知道哪些行属于同一段。

所以你要拿尺子量：**两行之间空得很小 → 是同一段被折行了**；**空了一大块 → 是新段落**。

还有一件事：每页页脚都印着「第 3 页」，你要是全抄进去，检索时「第 3 页」会变成高频词，反而把真正的内容挤下去。""",
        "example": """lines = [
    {"text": "失物招领：本园区拾到", "top": 10, "height": 12},
    {"text": "一把黑色折叠伞，请失主", "top": 25, "height": 12},
    {"text": "到游客中心认领。", "top": 40, "height": 12},
    {"text": "第 1 页", "top": 200, "height": 12},
]
print("OCR 原始行:")
for l in lines:
    print(" ", l["text"])""",
        "example_output": """OCR 原始行:
  失物招领：本园区拾到
  一把黑色折叠伞，请失主
  到游客中心认领。
  第 1 页""",
        "pitfalls": [
            "直接按 OCR 返回顺序拼：检测框顺序不等于阅读顺序，段落会乱序",
            "用「上一行 top」而不是「上一行底边」算间隙：行高不为 0 时会误判成同一段",
            "中文断行合并时加空格：变成「请 失主 到 游客 中心」，检索时一个词都匹配不上",
            "页眉页脚不去掉：同一句「第 X 页」重复几十次，污染整个索引",
        ],
        "task": """请实现 `merge_lines(lines, max_gap=6)`：把 OCR 行还原成段落。

- `lines`：`[{"text": str, "top": int, "height": int}, ...]`（可能乱序）
- 先按 `top` **升序排序**
- 相邻两行的间隙 = `下一行.top - (上一行.top + 上一行.height)`
- 间隙 `<= max_gap` → 直接拼接（**不加空格**，中文折行）
- 间隙 `> max_gap` → 另起一段
- 空输入返回 `[]`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先 `rows = sorted(lines, key=lambda x: x["top"])`，用 `prev_bottom = row["top"] + row["height"]` 跟踪上一行底边。注意每轮都要更新 `prev_bottom`，包括合并的时候。""",
        "checker": OCR_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "OCR 返回的多行文本，判断「是否属于同一段」最可靠的依据是什么？",
                "options": [
                    "行号顺序",
                    "相邻两行的垂直间隙（下一行 top 减去上一行底边）",
                    "每行的字符数",
                    "置信度高低",
                ],
                "answer_index": 1,
                "explanation": "版面还原靠几何位置：间隙小说明是同一段被折行，间隙大说明是新段落。顺序和置信度都提供不了这个信息。",
            },
            {
                "type": "choice",
                "stem": "中文 OCR 的折行合并时，为什么通常不加空格？",
                "options": [
                    "加空格会超出字段长度",
                    "中文换行是排版折行，加空格会把词硬生生拆开，影响检索",
                    "OCR 不认识空格",
                    "加空格会导致编码错误",
                ],
                "answer_index": 1,
                "explanation": "中文词之间本来就没有空格。折行处加空格会造出「请 失主 到」这种断词，BM25 和向量检索都会失配。",
            },
            {
                "type": "judge",
                "stem": "所有 PDF 都应该先走 OCR 再入库，这样最保险。",
                "answer": False,
                "explanation": "电子版 PDF 的文字层可以直接抽取，又快又准、没有识别错误。只有扫描件（图片型 PDF）才需要 OCR。",
            },
            {
                "type": "blank",
                "stem": "OCR 结果里要过滤掉「第 1 页」这类每页重复的内容，它们统称为______。",
                "answer": "页眉页脚",
                "hint": "填四个字，指页面上下边缘那部分",
                "explanation": "页眉页脚在每页重复，入库后会变成高频噪声，拉低关键词的区分度。去重时按「多页同位置重复」识别最可靠。",
            },
        ],
    },
    {
        "code": "mm-docker",
        "subject": "多模态与部署",
        "stage": "部署与端",
        "runner": "python",
        "title": "Docker 镜像构建与 compose 编排",
        "summary": "depends_on 只管启动顺序，不管「准备好了没」",
        "definition": """**Docker 解决的是「在我机器上能跑」。**

**Dockerfile 的核心是分层缓存**。每条指令是一层，某层变了，它**后面所有层**的缓存都失效。所以顺序极其关键：

```dockerfile
COPY requirements.txt .        # ① 依赖清单先拷
RUN pip install -r requirements.txt   # ② 装依赖（最慢，但很少变）
COPY . .                       # ③ 再拷源码（天天变）
```

如果反过来先 `COPY . .` 再 `pip install`，你改一行代码，依赖就得重装一遍——构建时间从 30 秒变成 10 分钟。

**多阶段构建**用来瘦身：编译依赖（gcc、torch 的构建工具）只留在 builder 阶段，最终镜像只拷产物。

（顺带一个真实对照：项目的 `Dockerfile` 目前是**单阶段**，只有一个 `FROM python:3.10-slim`，并没有用多阶段；但它把 `COPY requirements.txt` 放在了 `COPY . .` 之前，**分层缓存这一点是做对的**。看别人代码时要分清哪些是最佳实践、哪些只是还没做。）

**docker-compose 编排多个服务**：

```yaml
services:
  app:
    depends_on: [milvus]
  milvus:
    depends_on: [etcd, minio]
```

**`depends_on` 只保证「启动顺序」，不保证「服务已就绪」**。容器起来 ≠ 服务能连。Milvus 启动要几十秒，`app` 一起床就去连必然失败。正确做法是配 `healthcheck` + `condition: service_healthy`：

```yaml
depends_on:
  milvus:
    condition: service_healthy
```

**启动顺序本质是拓扑排序**：把「A 依赖 B」看成一条有向边 B → A，排出所有服务的一个线性顺序。有环（A 依赖 B、B 又依赖 A）就永远排不出来，必须报错而不是死循环。

**项目落点**：`docker-compose.yml` 里 etcd + minio 是 Milvus 的依赖，Milvus 又是 app 的依赖；`Dockerfile` 用 `python:3.10-slim` 单阶段构建，先装系统库（`libgl1` / `libgomp1`，opencv 和 paddle 需要）再装 Python 依赖。""",
        "plain": """装修队进场：

- **depends_on** 只是「水电工先进场，木工后进场」——它不检查水电是不是真的通了
- 木工一进来就要用电钻，结果电还没通，当场停工

**healthcheck** 才是「水电工干完活，验收合格了，木工再进场」。

拓扑排序就是排工序：先看谁不依赖任何人（etcd、minio），再排依赖它们的（milvus），最后排依赖 milvus 的（app）。""",
        "example": """services = {"app": ["milvus"], "milvus": ["etcd", "minio"], "etcd": [], "minio": []}
print("按 dict 顺序启动:")
for name in services:
    print("  启动", name, "  依赖:", services[name])
print("app 在 milvus 之前就启动了，连接必然失败")""",
        "example_output": """按 dict 顺序启动:
  启动 app   依赖: ['milvus']
  启动 milvus   依赖: ['etcd', 'minio']
  启动 etcd   依赖: []
  启动 minio   依赖: []
app 在 milvus 之前就启动了，连接必然失败""",
        "pitfalls": [
            "先 `COPY . .` 再 `pip install`：改一行代码就重装全部依赖，构建从 30 秒变 10 分钟",
            "以为 depends_on 等于「等依赖就绪」：容器起了但服务没起来，app 一连接就崩",
            "拓扑排序不检测环：A↔B 互相依赖时死循环，容器编排器直接卡住",
            "最终镜像不做多阶段：把 gcc、构建缓存全打进生产镜像，体积从 500MB 涨到 3GB",
        ],
        "task": """请实现 `startup_order(services)`：按依赖关系排出启动顺序。

- `services`：`{服务名: [依赖的服务名, ...]}`
- 返回一个列表，保证**每个依赖都排在依赖它的服务之前**
- 同一个服务只出现一次
- 以下情况抛 `ValueError`：
  - 存在循环依赖（含服务依赖自己）
  - 依赖了 `services` 里不存在的服务
- 空字典返回 `[]`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """用 DFS + 三色标记：`state[name]` 为 0 未访问、1 访问中、2 已完成。遇到状态 1 说明有环，抛 `ValueError`；递归处理所有依赖后再把当前服务加入结果列表。""",
        "checker": DOCKER_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "Dockerfile 里为什么要把 `COPY requirements.txt` 放在 `COPY . .` 之前？",
                "options": [
                    "语法要求必须这个顺序",
                    "利用分层缓存：依赖没变时可以直接复用 pip install 那一层，不用重装",
                    "这样镜像体积更小",
                    "为了让 pip 能联网",
                ],
                "answer_index": 1,
                "explanation": "源码天天变、依赖很少变。把变化少的放前面，改代码时只需重跑 `COPY . .`，`pip install` 那层直接命中缓存。",
            },
            {
                "type": "choice",
                "stem": "`depends_on` 能保证什么？",
                "options": [
                    "保证依赖服务已经可以接受连接",
                    "只保证容器的启动顺序，不保证服务就绪",
                    "保证依赖服务不会崩溃",
                    "保证网络互通",
                ],
                "answer_index": 1,
                "explanation": "容器「启动了」和「服务能用了」是两件事。要等就绪必须配 `healthcheck` + `condition: service_healthy`。",
            },
            {
                "type": "judge",
                "stem": "如果服务之间存在循环依赖，拓扑排序仍然能给出一个合法的启动顺序。",
                "answer": False,
                "explanation": "有环就排不出线性顺序——A 要等 B、B 要等 A，永远启动不了。正确做法是检测到环就报错，让人去改依赖关系。",
            },
            {
                "type": "blank",
                "stem": "把「A 依赖 B」排成一个合法启动顺序，用到的经典算法是______排序。",
                "answer": "拓扑",
                "hint": "填两个字，图论里那个「按依赖先后排」的算法",
                "explanation": "拓扑排序把有向无环图排成线性序列，保证每条边的起点都在终点之前。DFS 三色标记或 Kahn 入度法都能实现。",
            },
        ],
    },
    {
        "code": "mm-miniprogram",
        "subject": "多模态与部署",
        "stage": "部署与端",
        "runner": "python",
        "title": "微信小程序：登录态与请求重试",
        "summary": "401 不能直接弹给用户，要静默重登一次",
        "definition": """**小程序的登录和 Web 不一样**：没有 Cookie，`wx.login()` 拿到的是一个**一次性 code**，必须由后端去换 `openid`。

完整链路：

```
小程序 wx.login() → code
        ↓
后端 POST /api/auth/wx  {code}
        ↓  调微信 code2session
拿到 openid + session_key
        ↓
后端签发自己的 token（JWT）返回给小程序
        ↓
小程序存 storage，之后每个请求带 Authorization
```

**为什么要换自己的 token**：`code` 只能用一次，`session_key` 绝不能下发到客户端（它是解密用户数据的密钥）。所以后端签发自己的凭证，前端只认这个。

**token 会过期，401 要静默处理**：

```
请求 → 401 → 调 login 换新 token → 用新 token 重放原请求 → 成功
```

三个细节：

1. **只重试一次**。重登后还是 401，说明不是登录态问题（可能是权限不足），继续重试就是死循环。
2. **并发的 401 要合并成一次登录**。页面同时发 5 个请求全部 401，不能触发 5 次 `wx.login()`——用一个「正在登录」的 Promise 让其它请求排队等它。
3. **区分 401 和 500**。500 是服务端错误，重登没有任何用，只会让用户多等几秒。

**项目落点**：`miniprogram/src/` 下 6 个页面（index / chat / login / mine / passes / recharge），请求封装在 `utils/request`，登录态存 storage；后端对应 `api/auth.py`。""",
        "plain": """进游乐园：

- `wx.login()` 给你一张**一次性的兑换券**（code）
- 你拿券去窗口换**手环**（token）
- 之后玩每个项目都刷手环，不再用券

手环会过期。过期时工作人员不会把你赶出去，而是让你**去窗口换一个新的，然后回来接着玩**——这就是「401 静默重登 + 重放原请求」。

但如果换了新臂环还是刷不开，说明不是臂环的问题（可能是这个项目你根本没买票），继续换就是无理取闹了。""",
        "example": """calls = []

def fake_api(token):
    calls.append(token)
    return (401, None) if token == "old" else (200, "数据")

def fake_login():
    return "new"

status, data = fake_api("old")
print("直接返回给页面:", status, data)
print("调用记录:", calls)""",
        "example_output": """直接返回给页面: 401 None
调用记录: ['old']""",
        "pitfalls": [
            "401 直接把错误弹给用户：明明可以静默续期，用户却被踢回登录页",
            "重登后还 401 却继续重试：死循环，请求量翻倍还可能被封",
            "并发 401 各自去登录：一次进页面触发 5 次 wx.login，code 互相覆盖",
            "把 500 也当成登录失效去重登：服务端错误跟 token 无关，白等几秒还是失败",
        ],
        "task": """请实现 `call_with_relogin(token, api, login, max_relogin=1)`：

- `api(token)` 返回 `(status, data)`
- `login()` 返回新的 token
- 流程：
  1. 先用传入的 token 调一次 `api`
  2. 如果状态码**不是 401**，原样返回 `(status, data)`
  3. 如果是 401，最多重登 `max_relogin` 次：每次调 `login()` 换 token，再用新 token 调 `api`
  4. 某次成功（非 401）立即返回；次数用尽仍 401 就返回最后一次的 `(401, data)`
- **只有 401 才触发重登**，500 等其它状态码直接返回""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先 `status, data = api(token)`；`if status != 401: return (status, data)`。然后 `for _ in range(max_relogin):` 里 `token = login()` 再调一次，非 401 就返回。循环结束后返回最后一次结果。""",
        "checker": MINI_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "小程序为什么不能把 `wx.login()` 拿到的 code 当长期凭证？",
                "options": [
                    "code 太长，存储不方便",
                    "code 是一次性的，且 session_key 绝不能下发到客户端",
                    "code 只能用于支付",
                    "code 不含用户信息",
                ],
                "answer_index": 1,
                "explanation": "code 用完即废，`session_key` 是解密敏感数据的密钥。后端必须用它换 openid，再签发自己的 token 给前端。",
            },
            {
                "type": "choice",
                "stem": "页面同时发出 5 个请求全部返回 401，正确的处理是？",
                "options": [
                    "5 个请求各自调用一次 wx.login",
                    "只发起一次登录，其余请求等这次登录完成后用新 token 重放",
                    "全部直接报错给用户",
                    "放弃其中 4 个请求",
                ],
                "answer_index": 1,
                "explanation": "并发重登会让多个 code 互相覆盖，还可能触发风控。正确做法是用一个「登录中」的 Promise 让其它请求排队复用结果。",
            },
            {
                "type": "judge",
                "stem": "接口返回 500 时，也应该像 401 一样触发重新登录再重试。",
                "answer": False,
                "explanation": "500 是服务端内部错误，跟登录态无关。重登只会多花几秒、多打两次接口，问题依旧。只有 401 才代表凭证失效。",
            },
            {
                "type": "blank",
                "stem": "HTTP 状态码______表示「未认证或凭证已失效」，是触发重新登录的信号。",
                "answer": "401",
                "hint": "填三位数字",
                "explanation": "401 Unauthorized 表示身份未验证；403 Forbidden 是「验证过了但没权限」，重登没用。两者要分清。",
            },
        ],
    },
]
