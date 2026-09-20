"""阶段三、四：工程基础 + AI Agent 应用开发。

这里的内容按「真的要做 AI Agent 会用到什么」来选：
调模型、写 Prompt、拿结构化输出、工具调用、Agent 循环、流式、RAG、记忆。

凡是需要在沙箱里手写的，都用**纯 Python 能模拟**的方式出题
（不联网、不需要密钥），比如「构造请求体」「解析模型返回」「实现余弦相似度」；
不适合手写的（如 os.environ 读密钥）就用习题考。
"""

JSON_CHECKER = """
try:
    assert isinstance(data, dict) and data["model"] == "glm-5.3", "data 应该是解析后的字典"
    assert data["usage"]["total_tokens"] == 150, "嵌套取值：data['usage']['total_tokens']"
    assert text.startswith("{") and "model" in text, "text 应该是完整的 JSON 文本，而不是只取某个字段"
    assert "你好" in text, "text 里应该能直接看到中文 —— 说明 json.dumps 少了 ensure_ascii=False"
    assert temp == 0.7, "temp 要用 .get 兜默认值 0.7"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

HTTP_CHECKER = """
try:
    payload, headers = build_request("你好", 0.3)
    assert isinstance(payload, dict) and isinstance(headers, dict), "函数要返回 (payload, headers) 两个字典"
    assert payload["model"] == "glm-5.3", "payload 里要有 model"
    assert payload["messages"][0]["role"] == "system", "第一条消息应该是 system"
    assert payload["messages"][-1]["content"] == "你好", "最后一条消息的 content 应该是传入的用户输入"
    assert payload["temperature"] == 0.3, "temperature 要能被参数覆盖"
    assert len(headers) == 2, "headers 应该正好两个键"
    assert headers["Content-Type"] == "application/json", "Content-Type 应该是 application/json"
    assert headers["Authorization"] == "Bearer sk-abc", "Authorization 格式是 Bearer + 一个空格 + key"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except KeyError as e:
    print("__FAIL__ 字典里缺少键：" + str(e))
except TypeError as e:
    print("__FAIL__ 参数写法不对：" + str(e))
"""

ASYNC_CHECKER = """
try:
    assert results == ["a", "b", "c"], "fetch 要用 asyncio.sleep(0.2) 后返回自己的名字，顺序按传入顺序"
    assert elapsed < 0.4, f"三个任务应该并发执行，总耗时约 0.2 秒；现在是 {elapsed:.2f} 秒（串行跑会是 0.6 秒左右）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

PYDANTIC_CHECKER = """
try:
    m = ChatRequest(model="glm-5.3")
    assert m.temperature == 0.7, "temperature 应该有默认值 0.7"
    assert m.max_tokens == 1024, "max_tokens 应该有默认值 1024"
    try:
        ChatRequest(model="x", temperature=5)
        ok = False
    except Exception:
        ok = True
    assert ok, "temperature=5 应该被校验拦住（限定在 0~2）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except Exception as e:
    print("__FAIL__ 模型定义有问题：" + str(e))
"""

LLM_CHECKER = """
try:
    assert isinstance(messages, list) and len(messages) == 2, "messages 应该是两条：system + user"
    assert messages[0]["role"] == "system", "第一条是 system"
    assert messages[1]["role"] == "user" and messages[1]["content"] == "什么是 RAG", "第二条是用户问题"
    assert reply == "RAG 是检索增强生成", "reply 要从返回结构里正确取出来"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

PROMPT_CHECKER = """
try:
    assert "检索增强生成" in prompt, "prompt 里要包含角色描述"
    assert "只输出 JSON" in prompt, "prompt 里要包含格式约束"
    assert "小王" in prompt and "退款" in prompt, "prompt 里要包含传入的用户名和问题"
    assert isinstance(prompt, str) and prompt.count("{") == 0, "不要把花括号原样留在最终字符串里"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有变量没有定义：" + str(e))
"""

PARSE_CHECKER = """
try:
    assert parse_json('{"a": 1}') == {"a": 1}, "正常 JSON 要能解析"
    assert parse_json('```json\\n{"a": 1}\\n```') == {"a": 1}, "要去掉代码块围栏"
    assert parse_json("这是解释\\n{\\"a\\": 2}\\n后面还有废话") == {"a": 2}, "要能从废话里把 JSON 抠出来"
    assert parse_json("完全不是 JSON") is None, "实在解析不出来就返回 None"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

TOOL_CHECKER = """
try:
    assert call_tool("get_weather", {"city": "北京"}) == "北京: 晴 25 度", "要按工具名调用对应函数"
    assert call_tool("search", {"query": "RAG"}) == "找到 1 条关于 RAG 的结果", "参数要传给对应函数"
    r = call_tool("no_such_tool", {})
    assert "未知工具" in r, "遇到不认识的工具名要返回可读的提示，而不是抛异常"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except TypeError as e:
    print("__FAIL__ 调用参数不匹配：" + str(e))
"""

AGENT_CHECKER = """
try:
    out = run_agent("北京天气怎么样", responses, 5)
    assert out == "北京今天晴，25 度", f"循环应该在最后一步把最终答复返回，现在是 {out!r}"
    assert len(calls) == 1, f"这一轮只有一次工具调用，实际记录了 {len(calls)} 次"
    assert calls[0][0] == "weather", "应该记录了 weather 这次调用"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

STREAM_CHECKER = """
try:
    assert chunks_out == ["你", "好", "，", "世界"], "chunks_out 应该按顺序收集非空片段（跳过空串，遇到结束标记就停）"
    assert text == "你好，世界", "拼接结果要正确"
    assert first_ms <= 100, "要记录首个片段到达的耗时（模拟数据里是 30）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

RAG_CHECKER = """
try:
    assert abs(cosine([1, 0], [1, 0]) - 1.0) < 1e-6, "同向向量余弦相似度是 1"
    assert abs(cosine([1, 0], [0, 1])) < 1e-6, "正交向量相似度是 0"
    assert abs(cosine([2, 0], [5, 0]) - 1.0) < 1e-6, "同方向但长度不同，结果仍是 1（余弦只看方向）"
    assert top1 == "b", "query 应该和 b 最相似"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

MEMORY_CHECKER = """
try:
    h = build_history(history, "新问题", 1)
    assert len(h) == 3, f"keep_rounds=1 时应该保留最近 1 轮（2 条）+ 新问题，共 3 条；现在是 {len(h)} 条"
    assert h[-1]["content"] == "新问题", "新问题必须保留在最后"
    assert h[0]["content"] == history[-2]["content"], "要从最近的消息往前保留，最旧的先丢掉"
    h2 = build_history(history, "另一个问题", 2)
    assert len(h2) == 5, f"keep_rounds=2 时应该是 4 + 1 = 5 条；现在是 {len(h2)} 条"
    assert all(m["role"] in ("user", "assistant") for m in h), "每条消息都要有 role"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
"""

LESSONS: list[dict] = [
    # ---------------- 阶段三：工程基础 ----------------
    {
        "code": "eng-json",
        "stage": "工程基础",
        "title": "JSON 处理",
        "summary": "大模型的输入输出都是 JSON，这是最基础的搬运工",
        "definition": (
            "`json` 是 Python 标准库，负责「Python 对象 ↔ JSON 文本」互转：\n\n"
            "- `json.loads(text)` —— 把 **JSON 文本**解析成 Python 的 dict/list\n"
            "- `json.dumps(obj)` —— 把 Python 对象**转成** JSON 文本\n"
            "- `json.dumps(obj, ensure_ascii=False)` —— 中文不被转成 `\\uXXXX` 转义\n"
            "- `json.dumps(obj, indent=2)` —— 格式化输出，方便人看\n\n"
            "注意：`loads` 里带 s 的是处理**字符串**，`load` 处理的是**文件对象**。"
        ),
        "plain": (
            "JSON 长得**很像** Python 的字典，但它们是两回事：\n\n"
            "| JSON 文本 | Python 对象 |\n"
            "|---|---|\n"
            "| `'{\"a\": 1}'`（字符串） | `{\"a\": 1}`（字典） |\n\n"
            "这就是为什么老是记混：打印出来几乎一样，但**类型完全不同**。"
            "字典能直接 `d[\"a\"]`，JSON 文本必须先 `json.loads` 才能取值。"
            "反过来，要发给网络另一头（比如发 HTTP 请求）时，也必须先把字典 `dumps` 成字符串。\n\n"
            "**`ensure_ascii=False` 几乎每次都要加**，否则中文会变成 `\\u4f60\\u597d` 这种，"
            "日志里完全没法读。\n\n"
            "另外记住两个布尔值差异：JSON 里是 `true/false/null`，"
            "转成 Python 后是 `True/False/None`。"
        ),
        "example": (
            "import json\n"
            "\n"
            'raw = \'{"model": "glm-5.3", "usage": {"total_tokens": 150}}\'\n'
            "data = json.loads(raw)          # 字符串 -> 字典\n"
            "print(data[\"model\"])\n"
            "print(data[\"usage\"][\"total_tokens\"])   # 嵌套取值\n"
            "\n"
            'print(json.dumps(data, ensure_ascii=False))        # 中文不转义\n'
            'print(json.dumps({"q": "你好"}, ensure_ascii=True))  # 默认会转义'
        ),
        "example_output": (
            "glm-5.3\n150\n"
            '{"model": "glm-5.3", "usage": {"total_tokens": 150}}\n'
            '{"q": "\\u4f60\\u597d"}'
        ),
        "pitfalls": [
            "**`loads` / `dumps` 记混**：s = string。处理字符串用 loads，处理文件用 load。",
            "**忘了 `ensure_ascii=False`**：中文变成 `\\u4f60` 转义，日志没法看。",
            "**拿字典当字符串用**：`json.loads` 之后才能 `d[\"k\"]`；反过来发请求前必须 `dumps`。",
            "**JSON 不允许尾随逗号**：`{\"a\": 1,}` 会解析失败，Python 字典反而允许。",
            "**单引号不是合法 JSON**：`{'a': 1}` 用 `json.loads` 会报错，必须双引号。",
            "**嵌套取值容易崩**：`data[\"a\"][\"b\"]` 中间任一层缺失就 KeyError，深取值要用 `.get()` 层层兜底。",
        ],
        "task": (
            "题目已经给好了 JSON 字符串 `raw`（里面有中文）。\n\n"
            "1. 解析成字典存到 `data`\n"
            "2. 取出嵌套的 token 数存到 `total`（在 `usage.total_tokens` 里）\n"
            "3. 把 `data` 转回 JSON 文本存到 `text`，要求**中文保持中文**（不转义）\n"
            "4. 用 `.get()` 取出 `temperature`，取不到就用默认值 `0.7`，存到 `temp`"
        ),
        "setup": 'raw = \'{"model": "glm-5.3", "msg": "你好", "usage": {"total_tokens": 150}}\'\n',
        "starter": "import json\n\n# raw 已经给好了\n",
        "hint": (
            "`data = json.loads(raw)`\n"
            "`total = data[\"usage\"][\"total_tokens\"]`\n"
            "`text = json.dumps(data, ensure_ascii=False)`\n"
            "`temp = data.get(\"temperature\", 0.7)`"
        ),
        "checker": JSON_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "要把 Python 字典 `payload` 作为 HTTP 请求体发出去，需要先做什么？",
                "options": [
                    "json.dumps(payload) 转成 JSON 字符串",
                    "json.loads(payload) 解析一下",
                    "什么都不用做，直接传字典",
                    "str(payload) 转成字符串",
                ],
                "answer_index": 0,
                "explanation": "网络传的是文本，必须 `dumps` 成 JSON 字符串。`str(dict)` 出来的是 Python 字面量（单引号），不是合法 JSON。",
            },
            {
                "type": "judge",
                "stem": "`json.dumps({\"q\": \"你好\"})` 默认会把中文转义成 `\\u4f60\\u597d`，要输出中文得加 `ensure_ascii=False`。",
                "answer": True,
                "explanation": "默认 ensure_ascii=True。日志、调试输出、写文件时都建议关掉。",
            },
            {
                "type": "blank",
                "stem": "补全函数名，把 JSON 字符串解析成 Python 对象：\ndata = json.___('{\"a\": 1}')",
                "answer": "loads",
                "hint": "带 s 的那个",
                "explanation": "`loads` 处理字符串（s = string），`load` 处理文件对象。",
            },
        ],
    },
    {
        "code": "eng-env",
        "stage": "工程基础",
        "title": "环境变量与密钥管理",
        "summary": "API Key 绝对不能写进代码里",
        "definition": (
            "**环境变量**是操作系统层面的键值对，程序通过 `os.environ` 读取：\n"
            "```python\nimport os\nkey = os.environ.get(\"OPENAI_API_KEY\")\nif not key:\n    raise RuntimeError(\"缺少 OPENAI_API_KEY\")\n```\n\n"
            "**`.env` 文件**用来在本地保存这些变量，配合 `python-dotenv` 或 `pydantic-settings` 自动加载。\n"
            "`.env` **必须写进 `.gitignore`**，只提交 `.env.example`（里面是占位符）。\n\n"
            "读取用 `os.environ.get(\"名字\", 默认值)` 而不是 `os.environ[\"名字\"]`，"
            "这样缺变量时不会直接崩，可以给出更友好的提示。"
        ),
        "plain": (
            "**为什么密钥不能写在代码里？**\n\n"
            "因为代码会进 git、会被推到 GitHub、会被别人看到。"
            "密钥一旦进了仓库历史，**就算你后面删掉文件，历史记录里依然存在**——"
            "只能去平台**吊销并重新生成**。GitHub 上有专门的爬虫全天扫描新提交里的 `sk-` 开头的字符串，"
            "泄露的 Key 通常几分钟内就会被盗用。\n\n"
            "正确做法是「**代码和配置分离**」：\n"
            "- `.env`：本地真实密钥（**不入库**）\n"
            "- `.env.example`：只有键名和占位符（入库，给别人参考要配哪些变量）\n"
            "- 生产环境：在服务器/云平台的环境变量里配置，**不进代码仓库**\n\n"
            "在 Agent 项目里，除了模型 Key，还有向量库地址、数据库密码、第三方工具密钥，"
            "全都走这个机制。"
        ),
        "example": (
            "import os\n"
            "\n"
            "# 读取，缺了就给出友好提示\n"
            "api_key = os.environ.get(\"AI_API_KEY\")\n"
            "if not api_key:\n"
            "    print(\"⚠️ 没有配置 AI_API_KEY，将进入离线演示模式\")\n"
            "else:\n"
            "    print(\"已读取到密钥，长度\", len(api_key))\n"
            "\n"
            "base_url = os.environ.get(\"AI_BASE_URL\", \"https://api.example.com/v1\")\n"
            "print(\"接口地址:\", base_url)"
        ),
        "example_output": "⚠️ 没有配置 AI_API_KEY，将进入离线演示模式\n接口地址: https://api.example.com/v1",
        "pitfalls": [
            "**把 Key 写死在代码里然后提交**：这是最常见也最严重的错误，一旦推送就要立刻吊销。",
            "**`.env` 忘了加进 `.gitignore`**：`git add .` 会把密钥一起提交。",
            "**`.env.example` 里填了真 Key**：它是要入库的，必须只放占位符。",
            "**用 `os.environ[\"KEY\"]` 直接取**：没配置时直接 KeyError 崩掉，应该用 `.get()` 给友好提示。",
            "**以为删掉文件就没事了**：git 历史里还在，必须吊销密钥。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "checker": None,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "把 API Key 写进代码并推送到公开仓库后，第一时间应该做什么？",
                "options": [
                    "立刻去平台吊销这个 Key 并重新生成",
                    "把文件删掉再提交一次就好",
                    "把仓库改成私有",
                    "没关系，别人不会注意到",
                ],
                "answer_index": 0,
                "explanation": "**必须吊销**。git 历史里还留着明文，爬虫几分钟内就能扫到；改私有也不够，已经泄露了。",
            },
            {
                "type": "judge",
                "stem": "`.env.example` 里应该填上真实的 API Key，方便同事直接复制使用。",
                "answer": False,
                "explanation": "`.env.example` 是要提交到仓库的，只能放占位符（如 `你的Key`），真 Key 放在各自本地的 `.env` 里。",
            },
            {
                "type": "choice",
                "stem": "读取环境变量时，下面哪种写法对使用者最友好？",
                "options": [
                    "os.environ.get(\"AI_API_KEY\")，为空时给出提示并降级",
                    'os.environ["AI_API_KEY"]',
                    'open(".env").read()',
                    "把 Key 写成一个常量放在代码顶部",
                ],
                "answer_index": 0,
                "explanation": "`.get()` 不会因为缺变量直接崩，能给出「未配置，进入离线模式」这种可读提示。B 会 KeyError；D 就是硬编码密钥。",
            },
            {
                "type": "applied",
                "stem": "你要把一个本地跑通的 Agent 项目部署到服务器。请列出密钥和配置应该怎么放，"
                        "以及仓库里应该提交哪些文件、不提交哪些。",
                "keywords": [".env", ".gitignore", ".env.example", "环境变量", "吊销"],
                "reference": (
                    "仓库里**提交**：`.env.example`（占位符，列出需要哪些变量）、`.gitignore`（含 `.env`）。\n"
                    "仓库里**不提交**：`.env`（真实密钥）、任何含密钥的脚本。\n"
                    "服务器上：把真实密钥配到平台的环境变量里（或服务器上的 `.env`，权限收紧），"
                    "代码通过 `os.environ` 读取，本地和线上用同一套代码。\n"
                    "万一之前误提交过：**立刻去平台吊销并重新生成**，因为历史记录删不干净。"
                ),
                "explanation": "判断标准只有一条：这个文件会不会进入 git 历史。",
            },
        ],
    },
    {
        "code": "eng-log",
        "stage": "工程基础",
        "title": "日志与调试",
        "summary": "出了问题时，日志是你唯一的朋友",
        "definition": (
            "用标准库 `logging` 代替 `print`：\n"
            "```python\nimport logging\nlogging.basicConfig(level=logging.INFO,\n                    format=\"%(asctime)s %(levelname)s %(message)s\")\nlog = logging.getLogger(__name__)\n\nlog.info(\"开始处理: %s\", user_id)\nlog.warning(\"命中限流，等待重试\")\nlog.error(\"调用失败: %s\", err)\n```\n\n"
            "级别从低到高：`DEBUG` < `INFO` < `WARNING` < `ERROR` < `CRITICAL`。"
            "设置 `level` 后，低于该级别的日志不会输出。"
        ),
        "plain": (
            "**为什么不能只用 `print`？**\n\n"
            "1. `print` 没法分级——上线后你想只看「错误」，print 做不到\n"
            "2. `print` 没有时间戳，排查「什么时候开始出问题」时抓瞎\n"
            "3. 调试用的 print 很容易忘记删，混在正常输出里\n"
            "4. `print` 默认打到 stdout，而日志系统可以把错误写到文件、发到监控平台\n\n"
            "Agent 应用特别需要日志，因为**一次请求里发生了什么很难复现**："
            "模型返回了什么、调用了哪些工具、参数是什么、每步耗时多少——"
            "这些不记下来，线上出问题只能靠猜。\n\n"
            "**写日志的实用原则**：\n"
            "- 记**关键节点**和**异常**，不要什么都记（日志会爆炸）\n"
            "- **绝不记录密钥**和用户的敏感信息\n"
            "- 用参数化写法 `log.info(\"用户 %s\", uid)` 而不是 f-string——"
            "前者在日志级别不输出时不会白白拼接字符串"
        ),
        "example": (
            "import logging\n"
            "\n"
            "logging.basicConfig(level=logging.INFO,\n"
            "                    format=\"%(levelname)s: %(message)s\")\n"
            "log = logging.getLogger(\"agent\")\n"
            "\n"
            "log.debug(\"这条不会显示，因为级别是 INFO\")\n"
            "log.info(\"开始处理请求\")\n"
            "log.warning(\"响应较慢，耗时 3.2s\")\n"
            "log.error(\"工具调用失败\")"
        ),
        "example_output": "INFO: 开始处理请求\nWARNING: 响应较慢，耗时 3.2s\nERROR: 工具调用失败",
        "pitfalls": [
            "**在生产代码里留 `print` 调试**：忘记删就会污染正常输出，用日志级别控制更安全。",
            "**日志里打了密钥**：`log.info(f\"key={api_key}\")` 会把密钥写进日志文件，非常危险。",
            "**记了太多**：每一轮循环都打一堆日志，真出问题时反而被淹没。记关键节点。",
            "**只记「出错了」不记上下文**：`log.error(\"failed\")` 没有用，要带上入参、状态码、错误信息。",
            "**用 f-string 拼日志**：`log.debug(f\"{expensive()}\")` 即使不输出也会执行计算；用 `%s` 参数化。",
        ],
        "task": "",
        "setup": "",
        "starter": "",
        "hint": "",
        "checker": None,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "把日志级别设成 INFO 后，下面哪一行**不会**被输出？",
                "options": [
                    'log.debug("细节")',
                    'log.info("开始")',
                    'log.warning("慢")',
                    'log.error("失败")',
                ],
                "answer_index": 0,
                "explanation": "级别从低到高 DEBUG < INFO < WARNING < ERROR。设成 INFO 后，比它低的 DEBUG 不再输出。",
            },
            {
                "type": "judge",
                "stem": "排查问题时，日志里记下 API Key 方便对照，是推荐做法。",
                "answer": False,
                "explanation": "**绝对不要**把密钥写进日志。日志文件会流转、会被上传、会被很多人看到，等于二次泄露。",
            },
            {
                "type": "blank",
                "stem": "补全：设置日志级别为 INFO\nlogging.basicConfig(___=logging.INFO)",
                "answer": "level",
                "hint": "填参数名",
                "explanation": "`level` 决定哪些级别以上的日志会被输出。",
            },
            {
                "type": "short",
                "stem": "一次 Agent 请求要调用模型 3 次、工具 2 次。你会在哪些位置打日志、记录什么字段？",
                "keywords": ["耗时", "工具", "参数", "错误", "request id", "级别"],
                "reference": (
                    "关键节点 + 必要字段：\n"
                    "- 请求开始：用户 id、会话 id、请求 id（便于串联一次请求的全部日志）\n"
                    "- 每次模型调用：模型名、prompt 长度、耗时、token 用量（**不打完整 key**）\n"
                    "- 每次工具调用：工具名、参数（脱敏）、耗时、成功/失败\n"
                    "- 异常：错误类型、错误信息、重试次数\n"
                    "- 请求结束：总耗时、总 token、是否成功\n"
                    "用 INFO 记正常节点，ERROR 记异常；调试细节放 DEBUG。"
                ),
                "explanation": "核心是「通过 request id 能把一次请求的完整链路串起来」。",
            },
        ],
    },
    {
        "code": "eng-typing",
        "stage": "工程基础",
        "title": "类型注解与 dataclass",
        "summary": "让编辑器帮你查错，也让代码可读",
        "definition": (
            "**类型注解**是给变量/参数/返回值标注类型，Python 运行时**不强制检查**，"
            "但编辑器（VS Code/PyCharm）和 `mypy` 会帮你发现问题：\n"
            "```python\ndef greet(name: str, times: int = 1) -> str:\n    return name * times\n```\n"
            "常见写法：`list[str]`、`dict[str, int]`、`str | None`（可选）、`Optional[str]`。\n\n"
            "**`dataclass`** 自动生成 `__init__` / `__repr__`，很适合定义「一条数据结构」：\n"
            "```python\nfrom dataclasses import dataclass\n\n@dataclass\nclass Message:\n    role: str\n    content: str\n```"
        ),
        "plain": (
            "类型注解**不会让程序跑得更快、也不会在运行时报错**，那为什么还写？\n\n"
            "1. **编辑器会实时提示**：你把 `int` 传给了声明为 `str` 的参数，编辑器直接划黄线\n"
            "2. **可读性**：看函数签名就知道该传什么、返回什么，不用读实现\n"
            "3. **重构更安全**：改名、改结构时能全局查引用\n\n"
            "在 Agent 项目里类型注解几乎到处都有，因为要处理的数据结构很多："
            "消息、工具定义、模型响应……不标类型很容易传错。\n\n"
            "**`dataclass` 解决的是「一堆字段懒得写 __init__」**：\n"
            "```python\n@dataclass\nclass Message:\n    role: str\n    content: str\n\n"
            "m = Message(role=\"user\", content=\"hi\")   # __init__ 自动生成\n"
            "print(m)                                    # __repr__ 也自动生成\n```\n"
            "对比字典的好处：字段名写错会**立刻报错**（字典要等到运行时 KeyError）。"
        ),
        "example": (
            "from dataclasses import dataclass, field\n"
            "\n"
            "@dataclass\n"
            "class Message:\n"
            "    role: str\n"
            "    content: str\n"
            "    extra: dict = field(default_factory=dict)   # 可变默认值要这样写\n"
            "\n"
            "m = Message(role=\"user\", content=\"你好\")\n"
            "print(m)\n"
            "print(m.role)\n"
            "\n"
            "def total_len(messages: list[Message]) -> int:\n"
            "    return sum(len(x.content) for x in messages)\n"
            "\n"
            "print(total_len([m, Message(\"assistant\", \"在的\")]))"
        ),
        "example_output": (
            "Message(role='user', content='你好', extra={})\nuser\n5"
        ),
        "pitfalls": [
            "**以为注解会强制类型**：Python 运行时不管，传错类型照样跑；要强制校验用 Pydantic。",
            "**`dataclass` 里用可变默认值**：`extra: dict = {}` 会报错（也确实是坑），要用 `field(default_factory=dict)`。",
            "**`str | None` 和 `str` 不是一回事**：前者允许 None，写着 `str` 却传 None 是隐患。",
            "**注解写在注释里**：老代码常见 `# type: str` 写法，新代码直接用冒号注解。",
            "**`list[str]` 需要 Python 3.9+**：老版本要写 `from typing import List` 然后 `List[str]`。",
        ],
        "task": "请用 `@dataclass` 定义 `TokenUsage`：字段 `prompt_tokens: int`、`completion_tokens: int`，并写一个方法 `total(self)` 返回两者之和。",
        "setup": "",
        "starter": "from dataclasses import dataclass\n\n# 定义 TokenUsage\n",
        "hint": (
            "```\n@dataclass\nclass TokenUsage:\n    prompt_tokens: int\n    completion_tokens: int\n\n"
            "    def total(self):\n        return self.prompt_tokens + self.completion_tokens\n```"
        ),
        "checker": """
try:
    u = TokenUsage(prompt_tokens=100, completion_tokens=50)
    assert u.total() == 150, "total() 应该返回两个字段之和"
    assert TokenUsage(1, 2).total() == 3, "按位置传参也要能用（dataclass 会自动生成 __init__）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except TypeError as e:
    print("__FAIL__ 构造或调用参数不对：" + str(e))
""",
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "关于 Python 的类型注解，下面说法正确的是？",
                "options": [
                    "运行时不会强制检查，主要靠编辑器和静态检查工具发现问题",
                    "运行时会在类型不匹配时抛异常",
                    "加了注解程序会变快",
                    "注解只能用在函数参数上",
                ],
                "answer_index": 0,
                "explanation": "注解主要是给人和工具看的。要**运行时**校验（比如校验外部传入的 JSON）得用 Pydantic。",
            },
            {
                "type": "judge",
                "stem": "在 dataclass 里写 `extra: list = []` 作为字段默认值是安全的写法。",
                "answer": False,
                "explanation": "可变默认值会让所有实例共享同一个列表，dataclass 会直接报错提示你用 `field(default_factory=list)`。",
            },
            {
                "type": "blank",
                "stem": "补全装饰器，让下面的类自动生成 __init__ 和 __repr__：\n@___\nclass Message:\n    role: str\n    content: str",
                "answer": "dataclass",
                "hint": "填装饰器名",
                "explanation": "`@dataclass` 会按类里声明的字段自动生成构造方法和打印格式。",
            },
        ],
    },
    {
        "code": "eng-http",
        "stage": "工程基础",
        "title": "HTTP 请求与外部 API",
        "summary": "Agent 调模型、调工具，本质都是在发 HTTP 请求",
        "definition": (
            "调用 HTTP 接口需要三样东西：**URL、请求头（headers）、请求体（body）**。\n\n"
            "```python\nimport httpx\n\nheaders = {\n    \"Authorization\": f\"Bearer {api_key}\",   # 认证：Bearer + 空格 + key\n    \"Content-Type\": \"application/json\",     # 告诉对方我发的是 JSON\n}\nresp = httpx.post(url, json=payload, headers=headers, timeout=30)\nresp.raise_for_status()                      # 4xx/5xx 直接抛异常\nprint(resp.status_code)\ndata = resp.json()\n```\n\n"
            "常见状态码：`200` 成功、`400` 参数错、`401` 密钥无效、`403` 无权限、"
            "`429` 限流、`500` 服务端错误。"
        ),
        "plain": (
            "**Agent 调用大模型，本质上就是发一个 HTTP POST 请求**。"
            "把这件事想成「寄快递」会很清晰：\n"
            "- URL 是**地址**\n"
            "- headers 是**快递单上的信息**（其中 Authorization 相当于你的身份凭证）\n"
            "- body 是**包裹内容**（JSON 字符串）\n"
            "- 状态码是**签收回执**\n\n"
            "**几个必须养成的习惯**：\n"
            "1. **一定设超时**。不设的话网络卡住会一直挂着，整个服务被拖死。"
            "大模型请求通常给 30~90 秒。\n"
            "2. **区分「该重试」和「不该重试」**：`429` 和 `5xx` 可以等一会儿重试；"
            "`400`/`401` 重试一百次也没用，是参数或密钥的问题。\n"
            "3. **`raise_for_status()`**：不检查状态码的话，错误响应也会被当成正常结果往解析，"
            "然后报一个莫名其妙的 KeyError。"
        ),
        "example": (
            "import json\n"
            "\n"
            "def build_request(user_text, temperature=0.7):\n"
            "    payload = {\n"
            "        \"model\": \"glm-5.3\",\n"
            "        \"messages\": [\n"
            "            {\"role\": \"system\", \"content\": \"你是一个助手\"},\n"
            "            {\"role\": \"user\", \"content\": user_text},\n"
            "        ],\n"
            "        \"temperature\": temperature,\n"
            "    }\n"
            "    headers = {\n"
            "        \"Authorization\": \"Bearer 你的Key\",\n"
            "        \"Content-Type\": \"application/json\",\n"
            "    }\n"
            "    return payload, headers\n"
            "\n"
            "p, h = build_request(\"你好\", 0.3)\n"
            "print(json.dumps(p, ensure_ascii=False))\n"
            "print(h[\"Content-Type\"])"
        ),
        "example_output": (
            '{"model": "glm-5.3", "messages": [{"role": "system", "content": "你是一个助手"}, '
            '{"role": "user", "content": "你好"}], "temperature": 0.3}\napplication/json'
        ),
        "pitfalls": [
            "**不设超时**：请求挂住不返回，线程被占满，服务雪崩。",
            "**`Authorization` 格式写错**：是 `Bearer sk-xxx`，中间一个空格，不能少也不能多。",
            "**忘了 `Content-Type: application/json`**：对方可能不解析你的 body。",
            "**不看状态码就解析**：401 返回的是错误信息，你去取 `data[\"choices\"]` 只会 KeyError。",
            "**把 429 当普通错误不重试**：限流是正常的，要按 Retry-After 等待后重试。",
            "**密钥写进代码**：应该从环境变量读。",
        ],
        "task": (
            "请实现 `build_request(user_text, temperature=0.7)`，返回 `(payload, headers)`：\n\n"
            "- `payload` 是字典：`model` 固定 `\"glm-5.3\"`，`messages` 是两条（system + user），"
            "`temperature` 用传入值\n"
            "- `headers` 是字典：`Authorization` 为 `\"Bearer sk-abc\"`，`Content-Type` 为 `\"application/json\"`"
        ),
        "setup": "",
        "starter": "def build_request(user_text, temperature=0.7):\n    payload = {}\n    headers = {}\n    return payload, headers\n",
        "hint": (
            "messages 里 system 那条固定写「你是一个助手」，user 那条 `content` 用传入的 `user_text`；\n"
            "headers 两个键都用字符串字面量。"
        ),
        "checker": HTTP_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "调用大模型接口返回了 429，下面哪种处理最合适？",
                "options": [
                    "等待一小段时间后重试，并限制最大重试次数",
                    "立刻原样重试，越快越好",
                    "当成致命错误，直接让程序退出",
                    "把 temperature 调小再试",
                ],
                "answer_index": 0,
                "explanation": "429 是限流，说明你请求太快了，应该退避等待（最好读 Retry-After）再试，并设上限避免无限循环。A 里的「等待」是关键。",
            },
            {
                "type": "judge",
                "stem": "发 HTTP 请求时应该始终设置超时时间，否则网络卡住会把服务拖死。",
                "answer": True,
                "explanation": "这是生产环境的硬性要求。调大模型通常给 30~90 秒。",
            },
            {
                "type": "blank",
                "stem": "补全认证头的格式（key 变量名是 api_key）：\nheaders = {\"Authorization\": f\"Bearer ___\"}",
                "answer": "{api_key}",
                "accept": ["{api_key}", " {api_key}"],
                "hint": "f-string 里引用变量",
                "explanation": "`f\"Bearer {api_key}\"` —— Bearer 和 key 之间是一个空格。",
            },
            {
                "type": "short",
                "stem": "哪些 HTTP 状态码适合自动重试，哪些不适合？分别说明理由。",
                "keywords": ["429", "5", "400", "401", "重试", "退避"],
                "reference": (
                    "**适合重试**：`429`（限流，等一会儿就好）、`500/502/503/504`（服务端临时故障）。"
                    "重试要用**退避**（等待时间递增），并设最大次数。\n"
                    "**不适合重试**：`400`（参数错误）、`401`（密钥无效）、`403`（无权限）、`404`（地址错）"
                    "—— 这些都是「你发的东西有问题」，重试多少次结果都一样，只会浪费时间。"
                ),
                "explanation": "判断依据：**问题在服务端且可能是暂时的 → 重试；问题在你的请求本身 → 别重试**。",
            },
        ],
    },
    {
        "code": "eng-async",
        "stage": "工程基础",
        "title": "异步编程 asyncio",
        "summary": "等网络的时候别干等，Agent 提速的关键",
        "definition": (
            "`async def` 定义**协程函数**，调用它得到协程对象，要放进事件循环执行：\n"
            "```python\nimport asyncio\n\nasync def fetch(name):\n    await asyncio.sleep(0.2)    # await 表示「这里会让出控制权」\n    return name\n\nasync def main():\n    r = await asyncio.gather(fetch(\"a\"), fetch(\"b\"), fetch(\"c\"))  # 并发\n    print(r)\n\nasyncio.run(main())\n```\n\n"
            "`await` 只能写在 `async def` 里；`asyncio.gather` 把多个协程**并发**跑，"
            "总耗时约等于最慢的那个，而不是相加。"
        ),
        "plain": (
            "**为什么要异步？** 因为调用大模型是「等网络」——大部分时间都在傻等。\n\n"
            "假设一次模型调用要 5 秒，你要问 3 个独立的问题：\n"
            "- **串行**：5 + 5 + 5 = **15 秒**，用户等到不耐烦\n"
            "- **并发**：同时发出去，约 **5 秒**后就都有结果了\n\n"
            "异步不是「多开线程」，而是**单线程遇到等待就先切去干别的**，"
            "等结果回来了再切回来。所以才叫「协作式」——需要你在等待的地方写 `await`，"
            "主动让出控制权。\n\n"
            "在 Agent 里的典型用法：**并行调用多个工具**，或者**并行生成多个候选答案**。\n\n"
            "⚠️ 两个坑：\n"
            "1. **忘了 await**：`fetch(\"a\")` 不写 await 只会得到一个协程对象，不会执行，还会警告。\n"
            "2. **在异步函数里写同步阻塞代码**（如 `time.sleep`、`requests.get`）——"
            "会把整个事件循环卡住，异步就没意义了。"
        ),
        "example": (
            "import asyncio\n"
            "import time\n"
            "\n"
            "async def fetch(name):\n"
            "    await asyncio.sleep(0.2)     # 模拟网络等待\n"
            "    return name\n"
            "\n"
            "async def main():\n"
            "    start = time.time()\n"
            "    result = await asyncio.gather(fetch(\"a\"), fetch(\"b\"), fetch(\"c\"))\n"
            "    print(result)\n"
            "    print(f\"耗时 {time.time() - start:.2f}s\")   # 约 0.1s 而不是 0.3s\n"
            "\n"
            "asyncio.run(main())"
        ),
        "example_output": "['a', 'b', 'c']\n耗时 0.10s",
        "pitfalls": [
            "**忘了 `await`**：协程不会执行，只拿到一个对象，运行时报 `coroutine was never awaited`。",
            "**在 async 里用同步阻塞函数**：`time.sleep()` / `requests.get()` 会卡住整个事件循环，要用 `asyncio.sleep()` / `httpx.AsyncClient`。",
            "**在没有事件循环的地方 `await`**：普通函数里直接 await 会语法错误，要么改成 async，要么用 `asyncio.run()`。",
            "**`asyncio.gather` 里某个任务抛异常**：默认会中断整体，需要 `return_exceptions=True` 来逐个处理。",
            "**以为加了 async 就变快**：没有并发（没有同时发起多个 await）时，速度和不加一样。",
        ],
        "task": (
            "请实现并发调用：\n"
            "1. 写一个 `async def fetch(name)`，内部 `await asyncio.sleep(0.2)`，返回 `name`\n"
            "2. 写一个 `async def main()`，用 `asyncio.gather` **并发**跑 `fetch(\"a\")`、`fetch(\"b\")`、`fetch(\"c\")`，"
            "把结果存到 `results`\n"
            "3. 记录总耗时到 `elapsed`（用 `time.time()` 前后相减）"
        ),
        "setup": "",
        "starter": "import asyncio\nimport time\n\nasync def fetch(name):\n    pass\n\nasync def main():\n    global results, elapsed\n    pass\n\nasyncio.run(main())\n",
        "hint": (
            "```\nasync def fetch(name):\n    await asyncio.sleep(0.2)\n    return name\n\n"
            "async def main():\n    global results, elapsed\n    start = time.time()\n"
            "    results = await asyncio.gather(fetch(\"a\"), fetch(\"b\"), fetch(\"c\"))\n"
            "    elapsed = time.time() - start\n```"
        ),
        "checker": ASYNC_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "3 个互不依赖的模型调用，每个耗时 5 秒。用 `asyncio.gather` 并发执行，总耗时大约是？",
                "options": ["5 秒", "15 秒", "10 秒", "2.5 秒"],
                "answer_index": 0,
                "explanation": "并发时都在等各自的网络，总耗时约等于最慢的那个。串行才是 15 秒。",
            },
            {
                "type": "judge",
                "stem": "在 `async def` 函数里调用 `time.sleep(5)` 不会影响其他并发任务的执行。",
                "answer": False,
                "explanation": "`time.sleep` 是同步阻塞，会把整个事件循环卡住 5 秒，其他任务全都动不了。异步里要用 `await asyncio.sleep(5)`。",
            },
            {
                "type": "blank",
                "stem": "补全，让三个协程并发执行：\nresults = await asyncio.___(task1(), task2(), task3())",
                "answer": "gather",
                "hint": "填函数名",
                "explanation": "`asyncio.gather` 并发收集多个协程的结果，顺序与传入顺序一致。",
            },
        ],
    },
    {
        "code": "eng-pydantic",
        "stage": "工程基础",
        "title": "Pydantic 数据校验",
        "summary": "外部进来的数据不可信，先校验再用",
        "definition": (
            "```python\nfrom pydantic import BaseModel, Field\n\nclass ChatRequest(BaseModel):\n    model: str\n    temperature: float = Field(default=0.7, ge=0, le=2)\n    max_tokens: int = 1024\n\nreq = ChatRequest(model=\"glm-5.3\", temperature=0.5)\nprint(req.temperature)          # 0.5\nChatRequest(model=\"x\", temperature=5)   # 抛 ValidationError\n```\n\n"
            "特点：**运行时真的会校验**（和类型注解不同）、**自动类型转换**"
            "（`\"0.5\"` 会转成 `0.5`）、字段缺失且有默认值时用默认值、"
            "还能用 `req.model_dump()` 转成字典。"
        ),
        "plain": (
            "**Pydantic 解决的核心问题：外面来的数据不可信。**\n\n"
            "模型返回的 JSON、工具传来的参数、前端发来的请求——"
            "这些数据你不能假设它一定正确。手写校验是这样的：\n"
            "```python\ntemp = data.get(\"temperature\", 0.7)\nif not isinstance(temp, (int, float)):\n    raise ValueError(\"temperature 必须是数字\")\nif temp < 0 or temp > 2:\n    raise ValueError(\"temperature 超出范围\")\n```\n"
            "用 Pydantic 只要声明：`temperature: float = Field(default=0.7, ge=0, le=2)`。\n\n"
            "**这是 Agent 项目里使用频率最高的库之一**——"
            "用「模型 + 校验规则」一次性定义好数据结构，"
            "既当文档，又当校验器，还能直接序列化成 JSON Schema 交给大模型"
            "（Function Calling 的参数定义就是这么来的）。"
        ),
        "example": (
            "from pydantic import BaseModel, Field, ValidationError\n"
            "\n"
            "class ToolArg(BaseModel):\n"
            "    city: str\n"
            "    days: int = Field(default=1, ge=1, le=7)\n"
            "\n"
            "a = ToolArg(city=\"北京\")\n"
            'print(a.model_dump())          # {\'city\': \'北京\', \'days\': 1}\n'
            "\n"
            "b = ToolArg(city=\"上海\", days=\"3\")   # 字符串会自动转成整数\n"
            "print(b.days)\n"
            "\n"
            "try:\n"
            "    ToolArg(city=\"广州\", days=99)\n"
            "except ValidationError:\n"
            "    print(\"days 超出范围，已被拦截\")"
        ),
        "example_output": "{'city': '北京', 'days': 1}\n3\ndays 超出范围，已被拦截",
        "pitfalls": [
            "**以为类型注解就够了**：普通注解运行时不检查，要真校验必须用 Pydantic。",
            "**用 `Field(ge=..., le=...)` 做范围校验**：`ge` 是 ≥、`le` 是 ≤（注意别和 `gt`/`lt` 混）。",
            "**默认值也要参加校验**：`temperature: float = 5` 这种写法在部分版本会被拦，建议统一用 `Field(default=...)`。",
            "**嵌套模型要标类型**：`messages: list[Message]` 才会逐条校验，只写 `list` 不会。",
            "**别把密钥字段放进响应模型**：Pydantic 会原样序列化出来，容易泄露。",
        ],
        "task": (
            "请用 Pydantic 定义 `ChatRequest`：\n"
            "- `model: str`（必填）\n"
            "- `temperature: float`，默认 0.7，范围 0~2\n"
            "- `max_tokens: int`，默认 1024"
        ),
        "setup": "",
        "starter": "from pydantic import BaseModel, Field\n\n# 定义 ChatRequest\n",
        "hint": "`temperature: float = Field(default=0.7, ge=0, le=2)`",
        "checker": PYDANTIC_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "Pydantic 的模型相比普通类型注解，最关键的区别是？",
                "options": [
                    "Pydantic 在运行时真的会校验并转换类型，不合法会抛异常",
                    "Pydantic 运行更快",
                    "普通注解也能在运行时强制校验",
                    "Pydantic 只能用于 FastAPI",
                ],
                "answer_index": 0,
                "explanation": "普通注解运行时完全不检查；Pydantic 会真校验、能自动转换（\"3\" → 3）、还能给出具体错误位置。",
            },
            {
                "type": "judge",
                "stem": "定义 `days: int` 后传入字符串 `\"3\"`，Pydantic 会把它自动转成整数 3。",
                "answer": True,
                "explanation": "这是 Pydantic 的便利之处；但传 `\"abc\"` 这种无法转换的值会抛 ValidationError。",
            },
            {
                "type": "blank",
                "stem": "补全范围校验，要求 temperature 在 0 到 2 之间：\ntemperature: float = Field(default=0.7, __=0, le=2)",
                "answer": "ge",
                "hint": "大于等于的参数名",
                "explanation": "`ge` = greater or equal（≥），`le` = less or equal（≤）。",
            },
        ],
    },
    # ---------------- 阶段四：AI Agent 应用开发 ----------------
    {
        "code": "ai-llm-api",
        "stage": "AI Agent 开发",
        "title": "调用大模型 API",
        "summary": "messages 结构、system 与 user 的分工",
        "definition": (
            "主流大模型接口都是 OpenAI 兼容格式：**POST /chat/completions**，请求体形如\n"
            "```python\n{\n  \"model\": \"glm-5.3\",\n  \"messages\": [\n    {\"role\": \"system\", \"content\": \"你是一个严谨的助手\"},\n    {\"role\": \"user\", \"content\": \"什么是 RAG？\"},\n  ],\n  \"temperature\": 0.7,\n  \"max_tokens\": 1024,\n}\n```\n\n"
            "`messages` 是一个**有序列表**，每条消息有 `role` 和 `content`：\n"
            "- `system`：设定身份、规则、输出格式（最高优先级）\n"
            "- `user`：用户输入\n"
            "- `assistant`：模型之前的回复（多轮对话时要把历史带上）\n\n"
            "返回结构：`data[\"choices\"][0][\"message\"][\"content\"]` 才是回复文本；"
            "token 用量在 `data[\"usage\"]`。"
        ),
        "plain": (
            "**`messages` 是「对话记录」，不是一个 prompt 字符串。** 这是最容易理解错的地方。\n\n"
            "每条消息带 role，模型看到的是**谁说了什么**。所以：\n"
            "- 想设定人设和行为规则 → 放在 **system** 里\n"
            "- 用户这一轮说的话 → **user**\n"
            "- 上一轮模型说了什么 → 要作为 **assistant** 消息放回列表里，模型才「记得」\n\n"
            "**多轮对话的本质就是「每轮把完整历史重新发一遍」**。"
            "模型本身没有记忆，是你在每次请求里把上下文带过去的——"
            "这也解释了为什么对话越长越贵：每次都重发全部历史。\n\n"
            "**为什么用 `system` 做规则约束？** 因为模型被训练成更重视 system 内容。"
            "像「只输出 JSON」「不要编造」这类要求写进 system 比写在 user 里更稳。\n\n"
            "⚠️ **推理模型的坑**：有些模型（如 glm-5.3、DeepSeek-R 系列）的「思考过程」也计入 `max_tokens`。"
            "预算给小了，`content` 会是空字符串而不是报错——看起来就像「模型没反应」。"
        ),
        "example": (
            "import json\n"
            "\n"
            "# 模拟一个模型返回\n"
            'response = {\n'
            '    "choices": [{"message": {"role": "assistant", "content": "RAG 是检索增强生成"}}],\n'
            '    "usage": {"prompt_tokens": 30, "completion_tokens": 12},\n'
            "}\n"
            "\n"
            "reply = response[\"choices\"][0][\"message\"][\"content\"]\n"
            "print(reply)\n"
            "print(response[\"usage\"][\"completion_tokens\"])\n"
            "\n"
            "messages = [\n"
            "    {\"role\": \"system\", \"content\": \"你是一个严谨的助手\"},\n"
            "    {\"role\": \"user\", \"content\": \"什么是 RAG\"},\n"
            "]\n"
            "print(json.dumps(messages, ensure_ascii=False))"
        ),
        "example_output": (
            "RAG 是检索增强生成\n12\n"
            '[{"role": "system", "content": "你是一个严谨的助手"}, {"role": "user", "content": "什么是 RAG"}]'
        ),
        "pitfalls": [
            "**把 messages 写成一个大字符串**：必须是「消息对象的列表」，不是拼好的文本。",
            "**忘了带历史**：模型没有记忆，不多轮传历史它就完全不记得之前说了什么。",
            "**推理模型的 `max_tokens` 给小了**：思考过程占预算，`content` 会直接是空串，看起来像没反应。",
            "**取值路径写错**：`choices[0].message.content`，少一层就 KeyError。",
            "**把密钥写在代码里**：从环境变量读。",
            "**以为返回一定是 JSON**：流式返回、或者模型抽风时可能不是，解析要 try 包住。",
        ],
        "task": (
            "题目已经给好了 `question = \"什么是 RAG\"` 和模拟返回 `response`。\n\n"
            "1. 构造 `messages`：一条 system（内容 `\"你是一个严谨的助手\"`）+ 一条 user（内容用 `question`）\n"
            "2. 从 `response` 里取出模型回复文本，存到 `reply`"
        ),
        "setup": (
            'question = "什么是 RAG"\n'
            'response = {"choices": [{"message": {"role": "assistant", "content": "RAG 是检索增强生成"}}], '
            '"usage": {"total_tokens": 42}}\n'
        ),
        "starter": "# question 和 response 已经给好了\n\n",
        "hint": (
            "`messages = [{\"role\": \"system\", \"content\": \"你是一个严谨的助手\"}, {\"role\": \"user\", \"content\": question}]`\n"
            "`reply = response[\"choices\"][0][\"message\"][\"content\"]`"
        ),
        "checker": LLM_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "多轮对话中，模型是怎么「记住」前面聊过什么的？",
                "options": [
                    "每次请求都把之前的对话历史放进 messages 一起发过去",
                    "模型服务端会保存会话状态，只要传会话 id",
                    "模型有长期记忆，会自动记住",
                    "把之前的回复拼接成一个长字符串放在 system 里",
                ],
                "answer_index": 0,
                "explanation": "大模型 API 是无状态的，记忆靠每次请求携带历史实现。这也是对话越长越贵的原因。",
            },
            {
                "type": "judge",
                "stem": "使用推理模型时，如果 `max_tokens` 设置过小，可能出现 `content` 是空字符串的情况。",
                "answer": True,
                "explanation": "推理模型的思考过程也占用 token 预算，预算被思考用光后就没有内容输出了。遇到「模型没反应」先查这里。",
            },
            {
                "type": "blank",
                "stem": "补全取值路径，从返回结果里拿到回复文本：\nreply = data[\"choices\"][0][\"message\"][\"___\"]",
                "answer": "content",
                "hint": "填字段名",
                "explanation": "`choices[0].message.content` 是回复正文；同层的 `role` 是角色。",
            },
        ],
    },
    {
        "code": "ai-prompt",
        "stage": "AI Agent 开发",
        "title": "Prompt 工程",
        "summary": "把规则、角色、格式约束写清楚",
        "definition": (
            "好的 Prompt 通常包含四部分：\n"
            "1. **角色**：你是谁 —— 「你是一位资深 Python 讲师」\n"
            "2. **任务**：要做什么 —— 「解释这个概念」\n"
            "3. **约束**：怎么做 —— 「用生活化比喻，不超过 200 字，代码只用 Python」\n"
            "4. **格式**：输出长什么样 —— 「只输出 JSON，不要任何多余文字」\n\n"
            "在代码里通常用 **f-string 模板**把变量填进去：\n"
            "```python\nPROMPT = \"\"\"你是客服助手。\n用户：{name}\n问题：{question}\n请用 3 句话回答，语气亲切。\"\"\"\n\nprompt = PROMPT.format(name=name, question=q)\n```"
        ),
        "plain": (
            "**Prompt 就是给模型的需求文档。** 你写需求文档时会写清楚交付物、格式、限制条件吧？"
            "对模型也一样——写得越具体，结果越可控。\n\n"
            "**为什么格式约束要单独强调？** 因为模型有「自由发挥」的倾向。"
            "你只说「输出结果」，它可能回一段解释、也可能加句「好的，以下是结果：」。"
            "明确说「**只输出 JSON，不要任何多余文字，不要用代码块包裹**」，"
            "下游解析就稳得多。\n\n"
            "**几个实用技巧**：\n"
            "- 用**分隔符**把数据括起来，避免和指令混在一起：`<document>...</document>`\n"
            "- 给**一两个示例**（few-shot），比长篇描述更有效\n"
            "- 规则多的时候**编号列出**，模型更容易逐条遵守\n"
            "- 把 prompt **模板放在代码里用变量填充**，不要手写拼字符串\n\n"
            "⚠️ **不要把用户输入直接拼进 prompt 指令部分**。"
            "用户可能输入「忽略上面的指令」之类的注入内容，要放进明确的数据区里。"
        ),
        "example": (
            "SYSTEM = \"\"\"你是一位面向初学者的 Python 讲师。\n"
            "要求：\n"
            "1. 用生活化比喻解释\n"
            "2. 举一个 Python 例子\n"
            "3. 控制在 200 字以内\n"
            "\"\"\"\n"
            "\n"
            "TEMPLATE = \"\"\"请解释下面这个概念，面向 {level} 学习者：\n"
            "<concept>{concept}</concept>\n\"\"\"\n"
            "\n"
            "print(SYSTEM)\n"
            "print(TEMPLATE.format(level=\"入门\", concept=\"闭包\"))"
        ),
        "example_output": (
            "你是一位面向初学者的 Python 讲师。\n要求：\n1. 用生活化比喻解释\n2. 举一个 Python 例子\n3. 控制在 200 字以内\n\n"
            "请解释下面这个概念，面向 入门 学习者：\n<concept>闭包</concept>"
        ),
        "pitfalls": [
            "**只说「输出 JSON」但没说「不要加代码块」**：模型常会包一层 ```json，解析就失败。",
            "**约束写得太长太散**：要编号分条，模型才容易逐条遵守。",
            "**用户输入直接拼进指令**：有 prompt 注入风险，应该放进明确的数据区。",
            "**忘了给「不知道怎么办」的出口**：模型会硬编。要加一句「如果资料中没有答案，就回答不知道」。",
            "**以为 prompt 能保证 100% 遵守**：模型仍有概率不听话，代码里必须做**兜底解析**。",
        ],
        "task": (
            "题目已经给好了 `user_name = \"小王\"`、`question = \"我要退款\"`。\n\n"
            "请拼出 `prompt`（一个字符串），要求同时包含：\n"
            "1. 角色描述里要有「检索增强生成」这几个字\n"
            "2. 格式约束里要有「只输出 JSON」\n"
            "3. 把 `user_name` 和 `question` 的值填进去\n\n"
            "最终 `prompt` 里**不能残留花括号占位符**。"
        ),
        "setup": 'user_name = "小王"\nquestion = "我要退款"\n',
        "starter": "# 用 f-string 或 .format 把变量填进去\nprompt = \"\"\n",
        "hint": (
            "用 f-string 最直接：\n"
            '`prompt = f\"你是检索增强生成的客服助手。用户 {user_name} 问：{question}。只输出 JSON。\"`'
        ),
        "checker": PROMPT_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "你要求模型「输出 JSON」，但它总是回复 ```` ```json {...} ``` ```` 这样的代码块，最有效的改法是？",
                "options": [
                    "在 prompt 里明确写「不要用代码块包裹，只输出纯 JSON」",
                    "把 temperature 调成 0",
                    "换一个更大的模型",
                    "每次手动删掉代码块",
                ],
                "answer_index": 0,
                "explanation": "约束要写具体。同时**代码里仍要做兜底**：解析前先把 ``` 去掉，因为约束不能保证 100% 遵守。",
            },
            {
                "type": "judge",
                "stem": "把用户输入直接拼接到 prompt 的指令部分，是安全且推荐的做法。",
                "answer": False,
                "explanation": "有 prompt 注入风险（用户可输入「忽略以上指令」）。应该把用户内容放进明确的数据区（如 `<user_input>` 标签内），与指令分开。",
            },
            {
                "type": "applied",
                "stem": "你要让模型从用户评论里抽取「情绪」和「涉及的产品」。请写出你的 prompt 设计（要有角色、任务、约束、格式四部分）。",
                "keywords": ["角色", "JSON", "格式", "不要", "情绪", "产品"],
                "reference": (
                    "```\n你是文本信息抽取助手。\n任务：从用户评论中抽取「情绪」和「涉及产品」。\n"
                    "约束：\n1. 情绪只能是 正面/负面/中性 三者之一\n"
                    "2. 如果没有提到具体产品，product 填 null\n"
                    "3. 无法判断时 emotion 填 \"未知\"，不要编造\n"
                    "格式：只输出 JSON，不要代码块，不要任何解释文字\n"
                    '{"emotion": "...", "product": "..."}\n\n'
                    "评论：<review>...</review>\n```\n"
                    "要点：四部分齐全；用标签把数据括起来；给出「不知道怎么办」的出口；明确禁止代码块。"
                ),
                "explanation": "这四段式结构适用于绝大多数抽取类任务。",
            },
        ],
    },
    {
        "code": "ai-structured",
        "stage": "AI Agent 开发",
        "title": "结构化输出与 JSON 解析",
        "summary": "模型不总会乖乖给纯 JSON，你得能兜住",
        "definition": (
            "让模型输出结构化数据的常见做法：在 prompt 里给出**目标 JSON 结构**，"
            "并要求「只输出 JSON」。\n\n"
            "但实际返回经常带杂质，所以解析要**层层兜底**：\n"
            "```python\ndef parse_json(text):\n"
            "    if not text:\n        return None\n"
            "    t = text.strip()\n"
            "    if t.startswith(\"```\"):                  # 去掉代码块围栏\n"
            "        t = t.strip(\"`\")\n        if t.startswith(\"json\"):\n            t = t[4:].strip()\n"
            "    try:\n        return json.loads(t)\n"
            "    except Exception:\n        pass\n"
            "    start, end = t.find(\"{\"), t.rfind(\"}\")   # 从废话里抠出 JSON\n"
            "    if 0 <= start < end:\n        try:\n            return json.loads(t[start:end+1])\n"
            "        except Exception:\n            return None\n"
            "    return None\n"
            "```"
        ),
        "plain": (
            "**别假设模型会给你干净的 JSON。** 真实情况里你会遇到：\n"
            "- 前面加一句「好的，以下是结果：」\n"
            "- 用 ```` ```json ```` 代码块包起来\n"
            "- 末尾多一句解释\n"
            "- 字符串里出现没转义的换行、或者用了 Python 的单引号\n"
            "- 输出被 max_tokens 截断，JSON 不完整\n\n"
            "所以解析函数要**一层层降级**：先直接解析；不行就去掉围栏再试；"
            "再不行就用「第一个 `{` 到最后一个 `}`」把 JSON 抠出来；最后兜底返回 `None` "
            "让上层走默认值，而不是让整个流程崩掉。\n\n"
            "**更稳的做法**：如果模型平台支持 **JSON Schema / 结构化输出模式**，优先用它，"
            "由服务端保证格式。但即便如此，代码里还是要有兜底——"
            "网络中断导致截断时，任何模式都救不了你。"
        ),
        "example": (
            "import json\n"
            "\n"
            "def parse_json(text):\n"
            "    if not text:\n"
            "        return None\n"
            "    t = text.strip()\n"
            "    if t.startswith(\"```\"):\n"
            "        t = t.strip(\"`\")\n"
            "        if t.startswith(\"json\"):\n"
            "            t = t[4:].strip()\n"
            "    try:\n"
            "        return json.loads(t)\n"
            "    except Exception:\n"
            "        pass\n"
            "    start, end = t.find(\"{\"), t.rfind(\"}\")\n"
            "    if 0 <= start < end:\n"
            "        try:\n"
            "            return json.loads(t[start:end + 1])\n"
            "        except Exception:\n"
            "            return None\n"
            "    return None\n"
            "\n"
            'print(parse_json(\'```json\\n{"a": 1}\\n```\'))\n'
            'print(parse_json(\'好的：{"a": 2}——以上\'))\n'
            'print(parse_json("完全不是 JSON"))'
        ),
        "example_output": "{'a': 1}\n{'a': 2}\nNone",
        "pitfalls": [
            "**直接 `json.loads(model_output)`**：一旦带围栏或前缀就崩，必须兜底。",
            "**只 strip 反引号不够**：还要处理紧跟的 `json` 字样和换行。",
            "**忽略「截断」这种情况**：被 max_tokens 截断的 JSON 无法修复，只能返回 None 并重试或降级。",
            "**解析失败直接抛异常**：会让整个 Agent 流程中断，应该返回 None 并让上层决定怎么办。",
            "**没校验字段**：解析成功不代表字段齐全，取值时要用 `.get()` 或 Pydantic 校验。",
        ],
        "task": (
            "请实现 `parse_json(text)`，要求能处理这四种情况：\n"
            "1. 正常 JSON 字符串 → 返回字典\n"
            "2. 被 ```` ``` ```` 代码块包着的 JSON → 去掉围栏后返回字典\n"
            "3. 前面有解释文字、后面有废话 → 从里面把 JSON 抠出来\n"
            "4. 完全不是 JSON → 返回 `None`"
        ),
        "setup": "",
        "starter": "import json\n\ndef parse_json(text):\n    pass\n",
        "hint": "按「先直接解析 → 去围栏 → 抠 `{...}` → 返回 None」的顺序层层降级。",
        "checker": PARSE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "模型返回的 JSON 被 max_tokens 截断了（少了一半），最好的处理方式是什么？",
                "options": [
                    "返回 None，让上层决定重试或降级",
                    "用 try 包裹后忽略异常继续",
                    "手动补上缺失的括号",
                    "把 max_tokens 改小再试一次",
                ],
                "answer_index": 0,
                "explanation": "截断的 JSON 无法可靠修复。正确做法是识别出失败、返回 None，上层可以选择重试（调大 max_tokens）或用兜底回复。",
            },
            {
                "type": "judge",
                "stem": "即使模型平台支持「结构化输出」模式，代码里仍然需要保留解析失败的兜底逻辑。",
                "answer": True,
                "explanation": "网络中断、超时、截断都可能让返回不完整，任何模式都救不了。兜底是工程必需。",
            },
            {
                "type": "blank",
                "stem": "补全：从字符串里抠出 JSON 时，通常取第一个 `{` 到最后一个 `}`，用哪个方法找最后一个？\nt.find(\"{\"), t.___(\"}\")",
                "answer": "rfind",
                "hint": "从右边找的方法",
                "explanation": "`rfind` 从右侧查找，正好配对 `find`。用 `find` 找最后一个 `}` 会取到第一个，截断 JSON。",
            },
        ],
    },
    {
        "code": "ai-tools",
        "stage": "AI Agent 开发",
        "title": "Function Calling 工具调用",
        "summary": "让模型能「用工具」，Agent 的起点",
        "definition": (
            "**Function Calling 的流程**：\n"
            "1. 你把**可用工具的定义**（名字、说明、参数结构）随请求发给模型\n"
            "2. 模型判断需要哪个工具，返回 `tool_calls`（**它只是想调，不会真的执行**）\n"
            "3. **你的程序**根据工具名找到对应的本地函数，执行它\n"
            "4. 把执行结果作为 `role=\"tool\"` 的消息再发回给模型\n"
            "5. 模型用结果继续推理，给出最终回答\n\n"
            "模型返回的结构形如：\n"
            "```python\n{\"name\": \"get_weather\", \"arguments\": {\"city\": \"北京\"}}\n```"
        ),
        "plain": (
            "**关键认知：模型不会执行任何代码。** 它只会返回「我想调用 get_weather，参数是 city=北京」这样一个**意图**。"
            "真正的执行是你的程序做的。这也是安全边界所在——"
            "你可以决定哪些工具允许调用、参数要不要校验。\n\n"
            "**为什么需要「工具」？** 因为模型只会「生成文字」：\n"
            "- 不知道今天的天气（训练数据里没有）\n"
            "- 算不准大数乘法\n"
            "- 读不到你的数据库\n"
            "工具就是给它接上这些能力的手。\n\n"
            "**实现工具调度器的最小形态就是一个字典映射**：\n"
            "```python\nTOOLS = {\"get_weather\": get_weather, \"search\": search}\n\n"
            "def call_tool(name, args):\n    fn = TOOLS.get(name)\n"
            "    if fn is None:\n        return f\"未知工具: {name}\"      # 返回字符串而不是抛异常\n"
            "    return fn(**args)\n```\n"
            "注意最后那行注释：**遇到不认识的工具名要返回可读文本**，"
            "因为这条结果要回传给模型，模型看到「未知工具」才知道换个方式。"
            "如果直接抛异常，整个循环就断了。"
        ),
        "example": (
            "def get_weather(city):\n"
            '    return f"{city}: 晴 25 度"\n'
            "\n"
            "def search(query):\n"
            '    return f"找到 1 条关于 {query} 的结果"\n'
            "\n"
            "TOOLS = {\"get_weather\": get_weather, \"search\": search}\n"
            "\n"
            "def call_tool(name, args):\n"
            "    fn = TOOLS.get(name)\n"
            "    if fn is None:\n"
            '        return f"未知工具: {name}"\n'
            "    return fn(**args)\n"
            "\n"
            "# 模拟模型返回的 tool_call\n"
            'tool_call = {"name": "get_weather", "arguments": {"city": "北京"}}\n'
            "print(call_tool(tool_call[\"name\"], tool_call[\"arguments\"]))\n"
            'print(call_tool("search", {"query": "RAG"}))\n'
            'print(call_tool("not_exist", {}))'
        ),
        "example_output": "北京: 晴 25 度\n找到 1 条关于 RAG 的结果\n未知工具: not_exist",
        "pitfalls": [
            "**以为模型会自己执行工具**：它只返回调用意图，执行必须你来写。",
            "**工具名对不上**：定义里叫 `get_weather`，实现里写成 `getWeather`，就永远调不到。",
            "**参数直接 `**args` 展开不做校验**：模型可能给多余参数或类型不对，应该用 Pydantic 校验。",
            "**遇到未知工具就抛异常**：应该返回可读文本，让模型有机会纠正。",
            "**忘了把结果回传给模型**：执行完就不管了，模型拿不到结果，只能凭空编。",
            "**不设调用次数上限**：模型可能反复调用同一个工具，要有最大轮数保护。",
        ],
        "task": (
            "题目已经给好了两个工具函数 `get_weather(city)` 和 `search(query)`。\n\n"
            "请实现 `call_tool(name, args)`：\n"
            "- `args` 是参数字典，要能正确传给对应函数\n"
            "- 遇到不认识的工具名，**返回以「未知工具」开头的字符串**（不要抛异常）"
        ),
        "setup": (
            "def get_weather(city):\n"
            '    return f"{city}: 晴 25 度"\n\n'
            "def search(query):\n"
            '    return f"找到 1 条关于 {query} 的结果"\n'
        ),
        "starter": "def call_tool(name, args):\n    pass\n",
        "hint": (
            "用一个字典把工具名映射到函数：`{\"get_weather\": get_weather, \"search\": search}`，"
            "取不到就返回 `f\"未知工具: {name}\"`，取到了就 `return fn(**args)`。"
        ),
        "checker": TOOL_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "模型返回了一个 `tool_calls`，接下来应该由谁执行这个工具？",
                "options": [
                    "你的程序根据工具名找到本地函数并执行",
                    "模型自己会在服务端执行",
                    "平台会自动执行并返回结果",
                    "不需要执行，直接把工具名告诉用户",
                ],
                "answer_index": 0,
                "explanation": "模型只输出「想调用什么、参数是什么」，执行是你的程序的职责——这也是安全边界。",
            },
            {
                "type": "judge",
                "stem": "工具执行失败时，应该把错误信息作为工具结果返回给模型，而不是直接让程序崩溃。",
                "answer": True,
                "explanation": "模型看到「执行失败：超时」还能换个思路继续；直接崩溃则整个对话中断。",
            },
            {
                "type": "blank",
                "stem": "补全工具调度：按名字从字典里取函数\nfn = TOOLS.___(name)",
                "answer": "get",
                "hint": "填方法名",
                "explanation": "`TOOLS.get(name)` 取不到时返回 None，再据此返回「未知工具」提示。",
            },
            {
                "type": "applied",
                "stem": "请按顺序描述 Function Calling 的完整一轮流程（从发请求到拿到最终回答）。",
                "keywords": ["工具定义", "tool_calls", "执行", "tool", "回传", "最终"],
                "reference": (
                    "1. 请求时把**工具定义**（名称、用途、参数 schema）一起发给模型\n"
                    "2. 模型判断需要工具，返回 `tool_calls`（意图，不执行）\n"
                    "3. 程序解析出工具名和参数，做校验\n"
                    "4. **本地执行**对应函数\n"
                    "5. 把执行结果作为 `role=\"tool\"` 的消息（带 tool_call_id）**回传**给模型\n"
                    "6. 模型基于结果继续推理：要么再调工具（回到第 2 步），要么给出最终回答\n"
                    "7. 全程要有**最大轮数**限制，防止无限循环"
                ),
                "explanation": "第 5 步是最容易漏的——不回传结果，模型就无从继续。",
            },
        ],
    },
    {
        "code": "ai-agent-loop",
        "stage": "AI Agent 开发",
        "title": "Agent 循环（ReAct）",
        "summary": "想 → 做 → 看，循环到给出答案",
        "definition": (
            "Agent 的核心就是一个循环：\n"
            "```\nwhile 还没给出最终答案 and 步数 < 上限:\n"
            "    让模型看当前上下文，决定下一步\n"
            "    if 模型要调工具:\n"
            "        执行工具，把结果加入上下文\n"
            "    else:\n"
            "        它就是最终回答，结束\n"
            "```\n\n"
            "这个模式叫 **ReAct**（Reason + Act）：模型先推理（要不要用工具、用哪个），"
            "再行动（调用工具），然后观察结果，继续推理。"
        ),
        "plain": (
            "**Agent 和普通问答的区别就在这个循环。**\n\n"
            "普通问答：问一次 → 答一次。\n"
            "Agent：**问 → 想 → 用工具 → 看结果 → 再想 → 可能再用工具 → 直到能回答**。\n\n"
            "举个例子，用户问「北京今天适合跑步吗」：\n"
            "1. 模型想：我得先知道天气 → 调 `get_weather(\"北京\")`\n"
            "2. 工具返回：晴，25 度\n"
            "3. 模型想：温度合适、没下雨 → 可以给出答案\n"
            "4. 输出：「今天晴 25 度，很适合跑步」\n\n"
            "**两个必须有的保护**：\n"
            "- **最大步数**：否则模型可能反复调同一个工具，无限循环烧钱\n"
            "- **异常兜底**：工具失败也要把失败信息喂回去，让模型自己决定换路\n\n"
            "写这个循环时最容易犯的错是「**工具结果没加回上下文**」——"
            "那样模型下一轮看不到结果，会重复调用同一个工具，直到步数耗尽。"
        ),
        "example": (
            "def run_agent(question, responses, max_steps=5):\n"
            "    context = [question]\n"
            "    for step in range(max_steps):\n"
            "        action = responses[step]         # 模拟模型这一步的决定\n"
            "        if action[\"type\"] == \"tool\":\n"
            "            result = TOOLS[action[\"name\"]](**action[\"args\"])\n"
            "            context.append(result)       # 关键：结果加回上下文\n"
            "        else:\n"
            "            return action[\"text\"]        # 最终答复，结束循环\n"
            "    return \"达到最大步数，未能完成\"\n"
            "\n"
            "def weather(city):\n"
            "    return f\"{city}今天晴，25 度\"\n"
            "\n"
            "TOOLS = {\"weather\": weather}\n"
            "\n"
            "steps = [\n"
            "    {\"type\": \"tool\", \"name\": \"weather\", \"args\": {\"city\": \"北京\"}},\n"
            "    {\"type\": \"final\", \"text\": \"北京今天晴，25 度\"},\n"
            "]\n"
            "print(run_agent(\"北京天气怎么样\", steps))"
        ),
        "example_output": "北京今天晴，25 度",
        "pitfalls": [
            "**工具结果没加回上下文**：模型下一轮看不到结果，会重复调同一个工具直到步数用尽。",
            "**没有最大步数**：无限循环，API 费用失控。这是上线前必须检查的一条。",
            "**工具异常直接抛出**：应该把错误信息作为结果喂回去，让模型自己换策略。",
            "**每轮都重发全部历史**：上下文会越来越长，token 费用快速增长，要有裁剪策略。",
            "**把「模型说要调工具」当成「工具已执行」**：前者只是意图，必须真的去执行。",
        ],
        "task": (
            "题目已经给好了：模拟的模型决策序列 `responses`、工具表 `TOOLS`、以及 `calls` 列表"
            "（每次调用工具要把 `(工具名, 参数)` 追加进去）。\n\n"
            "请实现 `run_agent(question, responses, max_steps)`：\n"
            "- 逐个处理 `responses`：`type == \"tool\"` 就执行对应工具并把结果连同**已产生的所有结果**"
            "一起保留；`type == \"final\"` 就返回 `text`\n"
            "- 达到 `max_steps` 仍未结束，返回 `\"达到最大步数\"`"
        ),
        "setup": (
            "calls = []\n\n"
            "def weather(city):\n"
            '    return f"{city}今天晴，25 度"\n\n'
            "TOOLS = {\"weather\": weather}\n\n"
            "responses = [\n"
            '    {"type": "tool", "name": "weather", "args": {"city": "北京"}},\n'
            '    {"type": "final", "text": "北京今天晴，25 度"},\n'
            "]\n"
        ),
        "starter": "def run_agent(question, responses, max_steps=5):\n    pass\n",
        "hint": (
            "循环里只做两件事：`type == \"tool\"` 就按名字查 `TOOLS` 表、记录调用、执行；"
            "否则说明是最终答复，直接返回。\n\n"
            "```\ndef run_agent(question, responses, max_steps=5):\n"
            "    for step in range(max_steps):\n        a = responses[step]\n"
            "        if a[\"type\"] == \"tool\":\n"
            "            calls.append((a[\"name\"], a[\"args\"]))\n"
            "            TOOLS[a[\"name\"]](**a[\"args\"])\n"
            "        else:\n            return a[\"text\"]\n    return \"达到最大步数\"\n```"
        ),
        "checker": AGENT_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "在 Agent 循环里，把工具执行结果加回上下文的作用是什么？",
                "options": [
                    "让模型看到执行结果，从而决定是继续用工具还是给出最终答案",
                    "方便打印日志",
                    "让上下文更长一些",
                    "没什么作用，只是习惯",
                ],
                "answer_index": 0,
                "explanation": "不加回去，模型下一轮看不到结果，会重复调同一个工具，直到步数耗尽——这是最典型的 Agent bug。",
            },
            {
                "type": "judge",
                "stem": "Agent 循环必须设置最大步数限制，否则可能出现无限循环、费用失控。",
                "answer": True,
                "explanation": "这是生产环境的硬性要求。可以按步数限制，也可以按 token/费用限制。",
            },
            {
                "type": "blank",
                "stem": "补全循环的最大步数保护：\nfor step in ___ (max_steps):",
                "answer": "range",
                "hint": "填内置函数",
                "explanation": "`range(max_steps)` 保证循环最多跑 max_steps 次。",
            },
            {
                "type": "applied",
                "stem": "用户问「我们上季度华东区的销售额是多少」。请描述你的 Agent 会怎么一步步完成（要有工具调用和观察结果的过程）。",
                "keywords": ["工具", "查询", "结果", "推理", "失败", "回答"],
                "reference": (
                    "1. **推理**：这个问题需要内部数据，我只有查询工具，先确认要什么参数（指标=销售额、区域=华东、时间=上季度）\n"
                    "2. **行动**：调用 `query_sales(metric=\"revenue\", region=\"华东\", period=\"Q_last\")`\n"
                    "3. **观察**：工具返回数据（或「无权限」「参数不对」等错误）\n"
                    "4. **继续推理**：如果失败 → 根据错误调整参数重试一次；如果成功 → 检查数据是否完整\n"
                    "5. **收尾**：用自然语言总结结果，并说明数据口径/时间范围\n"
                    "全程有最大步数限制，避免反复重试。"
                ),
                "explanation": "关键点：先想清楚要什么参数，再调工具，然后**看结果决定下一步**。",
            },
        ],
    },
    {
        "code": "ai-stream",
        "stage": "AI Agent 开发",
        "title": "流式输出",
        "summary": "让用户看到字在往外冒，而不是干等",
        "definition": (
            "非流式：等模型全部生成完，一次返回 → 用户干等 10 秒。\n"
            "流式：模型每生成一小段就推给前端 → 0.5 秒就开始出字。\n\n"
            "接口层面通常是 **SSE（Server-Sent Events）**，每个事件形如：\n"
            "```\ndata: {\"type\": \"delta\", \"text\": \"你\"}\n\nsignature\n\n"
            "data: {\"type\": \"done\"}\n\n"
            "```\n\n"
            "客户端要**按块读取**，并且处理「一个块里可能包含半条消息」的情况——"
            "这就是所谓的**粘包/半包**问题。"
        ),
        "plain": (
            "**为什么要流式？** 纯粹是体验问题。\n\n"
            "大模型生成一段 500 字的回答要 8 秒。非流式就是白屏 8 秒然后一次性出现；"
            "流式是 0.5 秒后开始一个字一个字往外冒。**总耗时一样，但感受完全不同**——"
            "用户知道它在干活，不会以为卡死了。\n\n"
            "**实现时的关键细节**：\n"
            "1. 网络返回的数据是**字节流**，你需要解码 + 按分隔符（`\\n\\n`）切分\n"
            "2. **一次读到的可能不是完整事件**，要先缓存起来，等下一个 chunk 补齐再解析\n"
            "3. 收到 `done` 才能认为结束\n\n"
            "在 Agent 里还有额外好处：**工具调用的过程也能实时展示**"
            "（「正在检索…」「正在查询数据库…」），用户的等待感会大幅降低。"
        ),
        "example": (
            "# 模拟服务端按小块推送\n"
            "chunks = [\"你\", \"好\", \"，\", \"世界\", None]\n"
            "\n"
            "collected = []\n"
            "text = \"\"\n"
            "for c in chunks:\n"
            "    if c is None:          # None 表示流结束\n"
            "        break\n"
            "    if not c:              # 空块跳过\n"
            "        continue\n"
            "    collected.append(c)\n"
            "    text = text + c\n"
            "    print(f\"收到 {c!r}，当前：{text}\")"
        ),
        "example_output": (
            "收到 '你'，当前：你\n收到 '好'，当前：你好\n"
            "收到 '，'，当前：你好，\n收到 '世界'，当前：你好，世界"
        ),
        "pitfalls": [
            "**把每个 chunk 当成完整消息**：网络层可能把两条消息合在一个块里，也可能把一条拆开，必须先缓冲再按分隔符切。",
            "**忘了处理空块和结束标记**：空 `data:` 是心跳，收到 `[DONE]` 才能收尾。",
            "**前端用 EventSource 发 POST**：浏览器原生 EventSource 只支持 GET，要发 POST 得用 `fetch` + 读取 stream。",
            "**流式下也按整段算 token**：token 计数要累加，不能只看最后一次。",
            "**没做异常处理**：流到一半断了，要能提示并保留已收到的内容。",
        ],
        "task": (
            "题目已经给好了模拟的分块数据 `chunks`（其中 `None` 表示结束，空字符串表示心跳要跳过）。\n\n"
            "请按顺序处理，要求：\n"
            "1. 把非空片段收集到列表 `chunks_out`（按顺序）\n"
            "2. 全部拼起来存到 `text`\n"
            "3. 记录**第一个片段**的到达耗时存到 `first_ms`（题目已给好每个块的耗时 `times`，取第一个的）"
        ),
        "setup": (
            'chunks = ["你", "好", "", "，", "世界", None]\n'
            "times = [30, 60, 70, 90, 120, 150]\n"
            'chunks_out = []\nfirst_ms = 0\ntext = ""\n'
        ),
        "starter": "# chunks / times 已经给好了，遍历处理\n",
        "hint": (
            "遍历时用下标能同时拿到 times：\n"
            "```\nfor i, c in enumerate(chunks):\n    if c is None:\n        break\n    if not c:\n        continue\n"
            "    if not chunks_out:\n        first_ms = times[i]\n    chunks_out.append(c)\n    text = text + c\n```"
        ),
        "checker": STREAM_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "流式返回时，客户端一次 `read()` 拿到的数据最可能是？",
                "options": [
                    "可能是半条消息，也可能是好几条消息拼在一起",
                    "一定正好是一条完整消息",
                    "一定是完整的一段文字",
                    "一定是一个字节",
                ],
                "answer_index": 0,
                "explanation": "网络传输是按块来的，和业务消息边界无关。所以必须先缓冲，再按分隔符切分——这就是「粘包/半包」问题。",
            },
            {
                "type": "judge",
                "stem": "流式输出能让模型生成得更快，所以总耗时也会明显缩短。",
                "answer": False,
                "explanation": "生成总耗时基本一样，流式改善的是**首字延迟和等待体验**（用户 0.5 秒就能看到内容），不是总时长。",
            },
            {
                "type": "blank",
                "stem": "补全：收到结束标记后退出循环\nif chunk == \"[DONE]\":\n    ___",
                "answer": "break",
                "hint": "填一个关键字",
                "explanation": "收到结束标记就跳出循环，结束读取。",
            },
        ],
    },
    {
        "code": "ai-rag",
        "stage": "AI Agent 开发",
        "title": "RAG 与向量检索",
        "summary": "先检索再回答，让模型会说你的资料",
        "definition": (
            "**RAG = 检索增强生成**，流程是：\n"
            "1. **切分**：把文档切成小段（chunk）\n"
            "2. **向量化**：把每段文本转成向量（embedding），存进向量库\n"
            "3. **检索**：用户提问也转成向量，找出最相似的 Top-K 段\n"
            "4. **生成**：把检索到的原文拼进 prompt，让模型「看着资料回答」\n\n"
            "相似度最常用的是**余弦相似度**（只看方向不看长度）：\n"
            "```python\ncos(A, B) = (A·B) / (|A| × |B|)\n```"
        ),
        "plain": (
            "**为什么需要 RAG？** 因为模型只知道训练时见过的东西：\n"
            "- 不知道你公司内部的文档\n"
            "- 不知道上周刚发布的产品\n"
            "- 硬问它会**编**（幻觉）\n\n"
            "RAG 的做法是：**先去你的资料库里找出相关段落，再把它们塞进 prompt 让模型照着实说**。"
            "这样既用上了私有知识，又不用重新训练模型。\n\n"
            "**为什么用「向量」检索而不是关键词？** 因为用户问「怎么退款」和文档里写的「申请售后返款」"
            "一个共同词都没有，但意思相近。向量能把「语义相近」变成「距离近」。\n\n"
            "**余弦相似度只看方向不看长度**，这点很关键：\n"
            "`[2, 0]` 和 `[5, 0]` 方向完全一样，相似度就是 **1**，"
            "哪怕长度差很多。这样长短文档之间也能公平比较。\n\n"
            "⚠️ 提高检索质量的两个实用手段：**重排（rerank）** 和 **混合检索**"
            "（关键词 + 向量各取一部分再合并）。"
        ),
        "example": (
            "import math\n"
            "\n"
            "def cosine(a, b):\n"
            "    dot = sum(x * y for x, y in zip(a, b))\n"
            "    na = math.sqrt(sum(x * x for x in a))\n"
            "    nb = math.sqrt(sum(y * y for y in b))\n"
            "    if na == 0 or nb == 0:\n"
            "        return 0.0\n"
            "    return dot / (na * nb)\n"
            "\n"
            "print(cosine([1, 0], [1, 0]))   # 1.0  完全相同\n"
            "print(cosine([1, 0], [0, 1]))   # 0.0  正交，毫不相关\n"
            "print(cosine([2, 0], [5, 0]))   # 1.0  长度不同但方向一样\n"
            "\n"
            "query = [1, 0]\n"
            "docs = {\"a\": [0, 1], \"b\": [0.9, 0.1], \"c\": [0, 0.5]}\n"
            "ranked = sorted(docs, key=lambda k: cosine(query, docs[k]), reverse=True)\n"
            "print(ranked)                    # 最相关的排前面"
        ),
        "example_output": "1.0\n0.0\n1.0\n['b', 'c', 'a']",
        "pitfalls": [
            "**忘了除以长度**：只算点积的话，长文档分数天然更高，排序就不公平了。",
            "**除零**：零向量（比如空文本转出来的）会导致除零错误，要先判断。",
            "**切片太大或太小**：太大噪音多、超 token 限制；太小语义不完整。一般 200~500 字一段，并留重叠。",
            "**只检索不校验**：检索结果不相关时模型会硬答，prompt 里要加「如果资料里没有，就说不知道」。",
            "**只做向量检索**：专有名词（型号、错误码）用关键词更准，混合检索效果更好。",
        ],
        "task": (
            "题目已经给好了 `query` 和一组文档向量 `docs`。\n\n"
            "1. 实现 `cosine(a, b)`：返回余弦相似度，遇到零向量返回 `0.0`\n"
            "2. 用它把 `docs` 按相似度从高到低排序，最相似的那个键存到 `top1`"
        ),
        "setup": (
            "query = [1, 0]\n"
            'docs = {"a": [0, 1], "b": [0.9, 0.1], "c": [0, 0.5]}\n'
        ),
        "starter": "import math\n\ndef cosine(a, b):\n    pass\n\n",
        "hint": (
            "点积用 `sum(x * y for x, y in zip(a, b))`；\n"
            "模长用 `math.sqrt(sum(x * x for x in a))`；\n"
            "排序：`max(docs, key=lambda k: cosine(query, docs[k]))`"
        ),
        "checker": RAG_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "向量 `[2, 0]` 和 `[5, 0]` 的余弦相似度是多少？",
                "options": ["1（方向相同，长度不影响）", "0.4（长度比）", "10（点积）", "0（不同向量）"],
                "answer_index": 0,
                "explanation": "余弦只看夹角。两者方向完全一致，夹角为 0，cos(0) = 1。这正是它比点积更适合检索的原因。",
            },
            {
                "type": "judge",
                "stem": "RAG 能让模型回答训练数据里没有的、你私有文档里的内容。",
                "answer": True,
                "explanation": "这就是 RAG 的核心价值：把检索到的原文放进 prompt，模型照着实说，不必重新训练。",
            },
            {
                "type": "blank",
                "stem": "补全余弦相似度的分母（模长相乘）：\nreturn dot / (na * ___)",
                "answer": "nb",
                "hint": "另一个向量的模长变量名",
                "explanation": "分母是两个向量模长的乘积，这样结果一定落在 -1 到 1 之间。",
            },
            {
                "type": "applied",
                "stem": "用户问「怎么申请退款」，检索只找到一段关于「物流延迟」的文档。"
                        "如果不做处理，模型很可能答错。你会在 prompt 和流程里做什么防护？",
                "keywords": ["不知道", "没有", "阈值", "相关度", "兜底", "提示"],
                "reference": (
                    "两层防护：\n"
                    "1. **检索层**：设相似度阈值，分数太低就不注入（避免塞无关内容）；"
                    "或用 rerank 重排、混合检索提高召回质量\n"
                    "2. **生成层**：prompt 里明确写「**只能依据下面提供的资料回答；"
                    "如果资料中没有相关信息，就回答「资料中没有找到答案」，不要自行推测**」，"
                    "并把资料放进明确的标签里（如 `<context>`）\n"
                    "3. 兜底：如果检索结果为空或分数过低，**直接走固定话术/转人工**，不调模型。"
                ),
                "explanation": "「允许模型说不知道」是抑制幻觉最有效的一招。",
            },
        ],
    },
    {
        "code": "ai-memory",
        "stage": "AI Agent 开发",
        "title": "多轮对话与记忆",
        "summary": "上下文会越来越长，得学会裁剪",
        "definition": (
            "多轮对话就是把**历史消息**一起发过去。但历史会无限增长，所以必须管理：\n\n"
            "- **滑动窗口**：只保留最近 N 轮（最简单，最常用）\n"
            "- **摘要压缩**：把早期对话用模型总结成一段话，替代原文\n"
            "- **按 token 预算裁剪**：从最近往前取，直到接近预算上限\n\n"
            "**原则：system 消息必须始终保留**（规则不能丢），从最旧的历史开始丢。"
        ),
        "plain": (
            "**为什么不能一直把全部历史发过去？**\n\n"
            "1. **贵**：每次都重发全部历史，token 费用随轮数线性增长（实际上是平方级增长）\n"
            "2. **装不下**：模型有上下文长度上限，超了直接报错\n"
            "3. **变笨**：上下文里塞太多无关内容，模型注意力会被分散\n\n"
            "**滑动窗口是最实用的做法**：只留最近 10 轮。绝大多数场景够用，因为"
            "「刚才说了什么」比「50 轮前说了什么」重要得多。\n\n"
            "**更讲究的做法是「摘要 + 窗口」**：把很久以前的内容压缩成一段「之前聊过：用户在做 RAG 项目…」，"
            "再拼上最近的原文。这样既有长期记忆，又不爆上下文。\n\n"
            "⚠️ 裁剪时有个硬规则：**system 消息永远不能删**。它是行为约束，丢了模型就开始乱来。\n\n"
            "还有个容易忽略的点：**裁剪要按「轮」而不是按「条」**。"
            "如果一刀切下去把 user 和 assistant 拆开（只留了问题没留回答），模型会看不懂。"
        ),
        "example": (
            "def build_history(history, new_question, keep_rounds=2):\n"
            "    # 每条历史消息算半轮，一轮 = user + assistant\n"
            "    keep = keep_rounds * 2\n"
            "    recent = history[-keep:] if keep else []\n"
            "    return recent + [{\"role\": \"user\", \"content\": new_question}]\n"
            "\n"
            "history = [\n"
            "    {\"role\": \"user\", \"content\": \"第1轮问题\"},\n"
            "    {\"role\": \"assistant\", \"content\": \"第1轮回答\"},\n"
            "    {\"role\": \"user\", \"content\": \"第2轮问题\"},\n"
            "    {\"role\": \"assistant\", \"content\": \"第2轮回答\"},\n"
            "]\n"
            "print(len(build_history(history, \"新问题\", 1)))   # 2 条历史 + 1 条新问题\n"
            "print(build_history(history, \"新问题\", 1)[-1])"
        ),
        "example_output": "3\n{'role': 'user', 'content': '新问题'}",
        "pitfalls": [
            "**把 system 消息一起裁掉**：行为约束丢失，模型开始不守格式。",
            "**按条裁剪拆散了轮次**：只留了 user 没留 assistant，模型看不懂上下文。",
            "**忘了把新问题加进去**：裁剪完历史却漏了当前这句，模型不知道该答什么。",
            "**只截断字符数**：按字符估 token 在中文上误差很大，应该用平台给的 tokenizer 或留足余量。",
            "**从不做摘要**：长对话场景下，只靠滑动窗口会丢失早期关键信息（比如用户的偏好、已确认的需求）。",
        ],
        "task": (
            "题目已经给好了历史 `history`（4 条，即 2 轮）、新问题 `\"新问题\"`。\n\n"
            "请实现 `build_history(history, new_question, keep_rounds)`：\n"
            "- 保留**最近 `keep_rounds` 轮**（一轮 = user + assistant 共 2 条）\n"
            "- 把 `new_question` 作为最后一条 user 消息加上\n\n"
            "判定会检查：返回条数、新问题在最后、以及保留的是**最近**的消息。"
        ),
        "setup": (
            "history = [\n"
            '    {"role": "user", "content": "问题1"},\n'
            '    {"role": "assistant", "content": "回答1"},\n'
            '    {"role": "user", "content": "问题2"},\n'
            '    {"role": "assistant", "content": "回答2"},\n'
            '    {"role": "user", "content": "问题3"},\n'
            '    {"role": "assistant", "content": "回答3"},\n'
            "]\n"
        ),
        "starter": "def build_history(history, new_question, keep_rounds=2):\n    pass\n",
        "hint": (
            "```\ndef build_history(history, new_question, keep_rounds=2):\n"
            "    keep = keep_rounds * 2\n    recent = history[-keep:] if keep else []\n"
            "    return recent + [{\"role\": \"user\", \"content\": new_question}]\n```"
        ),
        "checker": MEMORY_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "裁剪对话历史时，哪条消息绝对不能删？",
                "options": [
                    "system 消息",
                    "最早的一条 user 消息",
                    "最后一条 assistant 消息",
                    "可以随便删",
                ],
                "answer_index": 0,
                "explanation": "system 里是行为规则和格式约束，删了模型就会不守规矩。裁剪应从最旧的历史开始。",
            },
            {
                "type": "judge",
                "stem": "直接把全部对话历史一直发给模型，除了贵之外，还可能让模型表现变差。",
                "answer": True,
                "explanation": "上下文里无关内容太多会分散模型注意力；而且可能超出上下文长度上限直接报错。",
            },
            {
                "type": "blank",
                "stem": "补全：取最近的 4 条消息\nrecent = history[___:]",
                "answer": "-4",
                "hint": "用负数下标",
                "explanation": "`history[-4:]` 取末尾 4 条，是最常用的滑动窗口写法。",
            },
            {
                "type": "short",
                "stem": "长对话（几百轮）场景下，只用「滑动窗口保留最近 10 轮」会有什么问题？你会怎么改进？",
                "keywords": ["摘要", "丢失", "偏好", "长期", "压缩"],
                "reference": (
                    "问题：早期的重要信息会丢，比如用户一开始说的「我在做 RAG 项目」「回答要简洁」"
                    "这些跨轮次的设定会被裁掉，模型后面就忘了，体验很差。\n\n"
                    "改进：**摘要 + 滑动窗口**的组合。把超出窗口的早期对话用模型压缩成一段摘要"
                    "（用户背景、已确认的需求、关键结论），作为一条 system 或 assistant 消息保留，"
                    "再拼上最近几轮的原文。另外也可以把稳定信息（用户偏好、项目背景）抽成结构化字段长期保存。"
                ),
                "explanation": "核心思路：**长期信息做压缩，短期信息保原文**。",
            },
        ],
    },
]
