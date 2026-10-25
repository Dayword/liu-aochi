"""科目：后端服务工程（第一批 · 3 课）。

AI 应用不是只有模型调用。「怎么把模型包成一个能上线、能鉴权、能流式返回的 HTTP 服务」
是另一条同样重要的能力线，而且面试里问得一点不少。

这批课对应项目 `api/` 与 `core/auth.py` 的真实实现。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）
"""

ROUTER_CHECKER = """
try:
    r = MiniRouter()
    r.add("GET", "/points/latest", lambda: "latest")
    r.add("GET", "/points/{code}", lambda code: "detail:" + code)
    r.add("POST", "/points", lambda: "created")

    assert r.dispatch("GET", "/points/py-var") == (200, "detail:py-var"), "路径参数要能捕获：/points/py-var 应命中 /points/{code}，并把 code='py-var' 传给 handler"
    assert r.dispatch("GET", "/points/latest") == (200, "latest"), "固定路由和通配路由都能匹配时，要按注册顺序取先注册的那个（固定路由在前就赢）"
    assert r.dispatch("POST", "/points") == (200, "created"), "没有参数的 handler 也要能调用"
    assert r.dispatch("GET", "/points") == (405, "method_not_allowed"), "路径存在但没有 GET 方法，必须是 405 而不是 404"
    assert r.dispatch("GET", "/nothing/here") == (404, "not_found"), "路径不存在返回 404"
    assert r.dispatch("GET", "/points/latest/") == (200, "latest"), "末尾多一个斜杠要能容忍"
    assert r.dispatch("GET", "/points/a/b") == (404, "not_found"), "路径段数不匹配不能命中（{code} 只吃一段，不跨斜杠）"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError, AttributeError) as e:
    print("__FAIL__ 返回结构不对（约定返回 (status, payload) 二元组）：" + str(e))
"""

AUTH_CHECKER = """
try:
    t = sign_token({"uid": 13, "role": "user"}, "s3cret", ttl=100, now=1000)
    assert isinstance(t, str) and t.count(".") == 2, "JWT 是三段式，必须用两个点分隔，现在是 %r" % (t,)

    v = verify_token(t, "s3cret", now=1050)
    assert v is not None, "自己签的 token 必须验得出来（检查 base64 补位和签名算法）"
    assert v["uid"] == 13 and v["role"] == "user", "payload 要原样还原，现在是 %r" % (v,)
    assert v["exp"] == 1100, "exp 应该等于 now + ttl = 1100，现在是 %r" % (v.get("exp"),)

    assert verify_token(t, "wrong-secret", now=1050) is None, "换个密钥必须验不过 —— 这是签名的全部意义"
    assert verify_token(t, "s3cret", now=1101) is None, "超过 exp 必须失效"
    assert verify_token(t, "s3cret", now=1100) is None, "正好到 exp 时刻也算过期（判定用 exp <= now）"
    assert verify_token("not-a-token", "s3cret", now=0) is None, "格式不对要返回 None，不能抛异常崩掉"
    assert verify_token("a.b.c", "s3cret", now=0) is None, "乱填的三段也要安全返回 None"

    import base64, json
    h, b, s = t.split(".")
    forged_body = base64.urlsafe_b64encode(
        json.dumps({"uid": 1, "role": "admin", "exp": 9999}).encode()
    ).rstrip(b"=").decode()
    forged = h + "." + forged_body + "." + s
    assert verify_token(forged, "s3cret", now=1050) is None, "改了 payload 却沿用旧签名，必须验不过 —— 否则任何人都能把自己改成 admin"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except Exception as e:
    print("__FAIL__ 签名/验签过程出错：" + str(e))
"""

SSE_CHECKER = """
try:
    assert encode_sse({"data": "hi"}) == "data: hi\\n\\n", "最小事件就是一行 data 加一个空行，现在是 %r" % (encode_sse({"data": "hi"}),)
    r = encode_sse({"id": 7, "event": "delta", "data": "x"})
    assert r == "id: 7\\nevent: delta\\ndata: x\\n\\n", "字段顺序是 id -> event -> data，最后空行分帧，现在是 %r" % (r,)

    r2 = encode_sse({"data": "第一行\\n第二行"})
    assert r2 == "data: 第一行\\ndata: 第二行\\n\\n", "多行 data 必须每行都加 'data: ' 前缀，否则客户端会把它拆成两个事件、第二个还缺 data —— 现在是 %r" % (r2,)

    r3 = encode_sse({"data": {"a": 1}})
    assert r3 == 'data: {"a": 1}\\n\\n', "非字符串 data 要先 json.dumps，现在是 %r" % (r3,)

    r4 = encode_sse({"data": "中文"})
    assert r4 == "data: 中文\\n\\n", "json 序列化要 ensure_ascii=False，中文不能被转成 \\\\uXXXX，现在是 %r" % (r4,)

    try:
        encode_sse({"event": "x"})
        assert False, "没有 data 的事件是非法 SSE，应该抛 ValueError"
    except ValueError:
        pass
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, AttributeError) as e:
    print("__FAIL__ 参数或返回类型不对：" + str(e))
"""

LESSONS = [
    {
        "code": "be-fastapi",
        "subject": "后端服务工程",
        "stage": "Web 框架与鉴权",
        "runner": "python",
        "title": "FastAPI 路由注册与依赖注入",
        "summary": "404 和 405 是两件事，路由顺序也能埋坑",
        "definition": """**Web 框架要干的第一件事：把「HTTP 请求」映射到「一个 Python 函数」。**

FastAPI 的三段式：

```python
@app.get("/learn/points/{code}")          # ① 装饰器 = 方法 + 路径
def get_point(code: str, limit: int = 10): # ② 参数 = 路径参数 + 查询参数
    return {"code": code, "limit": limit}  # ③ 返回值自动转 JSON
```

**参数来源由声明决定，不是靠猜**：

- 出现在路径里的 `{code}` → 路径参数
- 普通标量参数（`limit: int = 10`）→ 查询参数 `?limit=20`
- Pydantic 模型参数 → 请求体 JSON
- `Depends(...)` → 依赖注入

**依赖注入（Depends）解决什么**：把「每个接口都要做的事」抽出来复用——取数据库 session、校验 JWT、拿当前用户。

```python
def current_user(cred = Depends(bearer)):
    ...  # 解析 token，失败抛 401
    return user

@app.get("/me")
def me(user = Depends(current_user)):   # 声明即注入，测试时可以直接替换依赖
    return user
```

好处不只是少写代码：**依赖可以被 override**，测试时一行 `app.dependency_overrides[current_user] = fake` 就能跳过真实鉴权。

**三个状态码别搞混**：

| 码 | 含义 | 例子 |
|---|---|---|
| 404 | 路径不存在 | `/nope` |
| 405 | 路径存在，方法不对 | 对只有 POST 的 `/points` 发 GET |
| 422 | 参数校验失败 | `limit=abc` |

**路由匹配顺序有坑**：Starlette 按**注册顺序**逐个匹配。如果先注册 `/points/{code}` 再注册 `/points/latest`，那 `/points/latest` 永远会先被通配吃掉，固定路由变成死代码。所以固定路径要注册在通配路径之前。

**项目落点**：`api/` 下每个文件是一个业务域的路由模块（`chat.py` / `pay.py` / `knowledge.py` …），`core/auth.py` 用 `HTTPBearer` + `Depends` 提供 `get_current_user`，全项目共用。""",
        "plain": """前台接待：

- 你说「我找 302 房间」，前台按楼层索引查（路径匹配）
- 你说「我要投诉」，但投诉窗口只在下午开（方法不对 → 405，不是「没这个窗口」）
- 你说「我找 9999 房间」，压根没这间（404）

**注册顺序的坑**像这样：前台先贴了一张「找任何人 → 都带去 1 号会议室」，后面又贴了「找张总 → 带去总裁办」。结果所有人（包括张总）都被带去 1 号会议室，第二张告示永远不会被看到。""",
        "example": """def match(pattern, path):
    ps = pattern.strip("/").split("/")
    xs = path.strip("/").split("/")
    if len(ps) != len(xs):
        return None
    out = {}
    for p, x in zip(ps, xs):
        if p.startswith("{") and p.endswith("}"):
            out[p[1:-1]] = x
        elif p != x:
            return None
    return out

routes = ["/points/{code}", "/points/latest"]
for r in routes:
    m = match(r, "/points/latest")
    if m is not None:
        print("命中:", r, "参数:", m)
        break""",
        "example_output": """命中: /points/{code} 参数: {'code': 'latest'}""",
        "pitfalls": [
            "把通配路由注册在固定路由之前：`/points/latest` 被 `/points/{code}` 抢先匹配，固定路由成为死代码",
            "路径存在但方法不对却返回 404：客户端以为是路径写错，排查半天，实际是 405",
            "鉴权逻辑抄在每个接口开头：漏写一个就是越权漏洞，而且测试时没法替换",
            "在 handler 里直接 `return` 一个 ORM 对象：没配响应模型时会带出密码哈希等不该返回的字段",
        ],
        "task": """请实现一个极简路由器 `MiniRouter`：

1. `add(method, pattern, handler)`
   - `method` 是大写字符串（`"GET"` / `"POST"`）
   - `pattern` 形如 `"/points/{code}"`，`{name}` 表示路径参数
   - 按**注册顺序**保存

2. `dispatch(method, path)`
   - 返回 `(status, payload)` 二元组
   - 路径匹配成功 → `(200, handler(**路径参数))`
   - 路径匹配但方法不对 → `(405, "method_not_allowed")`
   - 路径不匹配 → `(404, "not_found")`
   - 忽略首尾多余的 `/`；`{code}` 只匹配一段，不跨 `/`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """`pattern.strip("/").split("/")` 和 `path` 同样处理，段数不等直接不匹配。逐段比对时，段形如 `"{code}"` 就记进参数字典。**注意先判路径是否匹配，再判方法**——否则路径不存在时会错报 405。""",
        "checker": ROUTER_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "一个路径只注册了 POST，客户端用 GET 请求它，应该返回什么？",
                "options": ["404", "405", "422", "500"],
                "answer_index": 1,
                "explanation": "路径存在、方法不允许，语义上就是 405 Method Not Allowed。404 是「这个路径根本没有」，会让排查方向完全跑偏。",
            },
            {
                "type": "choice",
                "stem": "FastAPI 的 `Depends` 最主要的价值是什么？",
                "options": [
                    "让接口自动变快",
                    "把鉴权、数据库 session 这类公共逻辑抽出来复用，并且能在测试里替换",
                    "自动生成数据库表",
                    "把同步函数变成异步",
                ],
                "answer_index": 1,
                "explanation": "依赖注入的核心是解耦与可替换。`app.dependency_overrides` 让你在测试里换个假依赖就能跳过真实鉴权。",
            },
            {
                "type": "judge",
                "stem": "路由匹配时，固定路径和带 `{参数}` 的通配路径谁生效，取决于注册顺序。",
                "answer": True,
                "explanation": "Starlette 按注册顺序逐个匹配，第一个匹配上的就赢。所以固定路径必须注册在通配路径之前，否则永远轮不到它。",
            },
            {
                "type": "blank",
                "stem": "补全 FastAPI 的鉴权依赖（用 ___ 表示要填的部分）：\\nuser = Depends(___current_user)",
                "answer": "get_",
                "hint": "填一个英文前缀，表示「获取」",
                "explanation": "项目里依赖函数名是 `get_current_user`。命名上 `get_` 前缀是 FastAPI 社区的惯例。",
            },
        ],
    },
    {
        "code": "be-auth",
        "subject": "后端服务工程",
        "stage": "Web 框架与鉴权",
        "runner": "python",
        "title": "JWT 认证与密码哈希",
        "summary": "JWT 是签名不是加密，密码要用慢哈希",
        "definition": """**认证（你是谁）和授权（你能干什么）是两件事**。JWT 通常负责前者。

**密码存储的三代做法**：

1. 明文 —— 脱库即全泄露。绝对不行。
2. MD5 / SHA256 —— 可逆推（彩虹表），而且太快，每秒能试几十亿次。不行。
3. **bcrypt / argon2** —— 自带随机盐（同样的密码每次哈希结果都不同）+ 故意慢（可调 cost）。正确做法。

`passlib` 的 `CryptContext(schemes=["bcrypt"])` 就是干这个的：`hash()` 生成带盐的串，`verify()` 用常量时间比较。

**JWT 的结构**：

```
header.payload.signature
  ↑        ↑         ↑
算法     数据      HMAC(前两段, 密钥)
```

三段都是 **base64url 编码，不是加密**。任何人拿到 token 都能解出 payload——所以**绝不能把密码、身份证号放进 payload**。

**签名保证的是「没被篡改」**，不是「看不见」。把 payload 里的 `role: user` 改成 `admin`，签名立刻对不上，服务端验签就会拒绝。这就是 JWT 的全部安全性所在。

**四个必须做对的点**：

- **一定要验签**，而且用常量时间比较（`hmac.compare_digest`），防时序攻击
- **一定要验过期**：`exp <= now` 就拒绝
- **别信 `alg` 字段**：历史上出过 `alg: none` 漏洞，服务端必须写死自己支持的算法
- **别把 JWT 当 session**：JWT 无状态，签发后无法单独撤销。要「强制下线」就得配黑名单或短过期 + refresh token

**项目落点**：`core/auth.py` 用 `python-jose` 签发/校验 JWT、`passlib` 的 `CryptContext` 存密码，`HTTPBearer` 从 `Authorization: Bearer xxx` 取 token。`SECRET_KEY` 强制从环境变量注入，没配置就随机生成并告警——随机密钥重启后所有 token 失效，但这比「写死一个默认密钥」安全得多。""",
        "plain": """JWT 像一张**盖了钢印的介绍信**：

- 内容是用明文写的（base64 不是加密），谁都能看
- 但钢印（签名）只有发信机关能盖。你改一个字，钢印就对不上

所以：**能放的是「不怕被看见」的信息**（用户 id、角色），不能放密码。

密码哈希则像把纸条塞进碎纸机再搅匀——而且故意搅得很慢。慢不是缺点，是特性：攻击者想暴力试密码，每秒只能试几千次而不是几十亿次。""",
        "example": """import base64, json

token = "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoidXNlciIsInVpZCI6MTN9.abc"
head, body, sig = token.split(".")

def dec(s):
    return json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))

print("header:", dec(head))
print("payload:", dec(body))
print("签名:", sig)""",
        "example_output": """header: {'alg': 'HS256'}
payload: {'role': 'user', 'uid': 13}
签名: abc""",
        "pitfalls": [
            "把密码或手机号放进 JWT payload：base64 一解就全露，等于明文传输",
            "只解 payload 不验签名：攻击者把 role 改成 admin 直接越权",
            "用 MD5 存密码：彩虹表秒破，而且不加盐时相同密码哈希值完全一样",
            "只验签名不验 exp：token 泄露后永久有效，没有任何补救手段",
        ],
        "task": """请实现两个函数（都用 HS256 = HMAC-SHA256）：

1. `sign_token(payload, secret, ttl=3600, now=0)`
   - 在 payload 基础上加 `exp = now + ttl`
   - header 固定 `{"alg": "HS256", "typ": "JWT"}`
   - 两段 JSON 都要 `sort_keys=True`、`separators=(",", ":")`，再 base64url 编码并**去掉结尾的 `=`**
   - 签名 = `HMAC-SHA256(header段 + "." + payload段, secret)`，同样 base64url 去 `=`
   - 返回 `header.payload.signature`

2. `verify_token(token, secret, now=0)`
   - 签名不符、格式不对、已过期（`exp <= now`）都返回 `None`
   - 全部通过则返回 payload 字典（含 `exp`）
   - 任何异常都不能往外抛""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """编码用 `base64.urlsafe_b64encode(b).rstrip(b"=").decode()`；解码要先补 `"=" * (-len(s) % 4)`。签名用 `hmac.new(secret.encode(), seg.encode(), hashlib.sha256).digest()`，比较用 `hmac.compare_digest`。整个 `verify_token` 包在 `try/except Exception: return None` 里。""",
        "checker": AUTH_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "JWT 的 payload 是什么保护级别？",
                "options": [
                    "加密的，没有密钥解不开",
                    "base64url 编码，任何人都能解开看内容",
                    "只有服务端能读",
                    "用 bcrypt 哈希过",
                ],
                "answer_index": 1,
                "explanation": "base64 是编码不是加密。JWT 的安全性只来自签名（防篡改），不来自保密性。所以不能放敏感信息。",
            },
            {
                "type": "choice",
                "stem": "存用户密码应该用哪种方式？",
                "options": [
                    "MD5，快且不可逆",
                    "AES 加密，需要时能解回来",
                    "bcrypt / argon2 这类带随机盐的慢哈希",
                    "base64 编码",
                ],
                "answer_index": 2,
                "explanation": "密码永远不需要「解回来」，所以用不可逆哈希。必须是慢哈希 + 随机盐：抗彩虹表、抗暴力枚举。MD5 太快且不加盐。",
            },
            {
                "type": "judge",
                "stem": "JWT 是无状态的，所以服务端可以随时让某一个已签发的 token 立刻失效。",
                "answer": False,
                "explanation": "无状态意味着服务端不保存 token 记录，签发后只能等它过期。要强制下线必须额外引入黑名单或缩短有效期配 refresh token。",
            },
            {
                "type": "blank",
                "stem": "补全 JWT 的三段结构（用 ___ 表示要填的部分）：\\nheader.___signature",
                "answer": "payload.",
                "hint": "填两段之间的内容，注意带上分隔点",
                "explanation": "完整结构是 `header.payload.signature`，三段用两个点分隔。",
            },
        ],
    },
    {
        "code": "be-sse",
        "subject": "后端服务工程",
        "stage": "接口与流式",
        "runner": "python",
        "title": "SSE 服务端流式输出",
        "summary": "多行 data 不加前缀，客户端直接断包",
        "definition": """**SSE（Server-Sent Events）= 服务端单向、持续往客户端推文本。**

三种「实时」方案怎么选：

| 方案 | 方向 | 复杂度 | 适用 |
|---|---|---|---|
| 轮询 | 客户端反复问 | 最低 | 状态变化慢、能容忍延迟 |
| SSE | 服务端 → 客户端单向 | 低（就是 HTTP） | **大模型流式输出**、进度推送 |
| WebSocket | 双向 | 高（要握手升级、心跳、重连） | 聊天室、协同编辑 |

大模型流式几乎都用 SSE：它只要一个普通 HTTP 连接，浏览器原生 `EventSource` 就能收，断线还自动重连。

**报文格式（每条消息用空行分隔）**：

```
id: 12
event: delta
data: 你

data: 好

: 这是注释，常用来做心跳
```

三个必须记住的细节：

1. **每个字段后面必须跟一个空格**：`data: hello`，不是 `data:hello`（少空格时部分客户端会把整行当数据）。
2. **多行数据要每行都加 `data: ` 前缀**。这是最常见的 bug：把一段带换行的文本直接拼在 `data: ` 后面，客户端会把它当成两条消息，第二条还没有 data 字段。
3. **帧与帧之间用一个空行分隔**（即结尾是 `\\n\\n`）。

**工程上的四个注意点**：

- **心跳**：中间代理或负载均衡器通常 60 秒无数据就断连接。每隔 15~30 秒发一个注释行 `: ping` 保活。
- **关掉 Nginx 缓冲**：`proxy_buffering off;`。否则 Nginx 会攒够一个 buffer 才下发，流式变成「一次性」。
- **断线重连**：浏览器会自动重连，并把最后收到的 `id` 放进 `Last-Event-ID` 请求头。服务端可以据此续传。
- **客户端主动断开要能感知**：FastAPI 里监听 `await request.is_disconnected()`，不然模型还在傻跑，白烧 token。

**项目落点**：`api/chat.py` 用 `StreamingResponse(gen(), media_type="text/event-stream")` 把 Agent 的逐字输出推给前端；`api/kb_agent.py` 的 `_sse()` 把同步生成器统一包装成 SSE 响应。""",
        "plain": """SSE 就是「服务端给客户端发微信，一条一条发」。

格式规定得很死：每条消息的每个字段都要写成 `字段名: 内容`，消息之间空一行。

**多行的坑**：你想发一段两行的文字，直接写

```
data: 第一行
第二行
```

客户端看到的是：第一条消息 `data: 第一行`，然后遇到一个**没有 data 前缀的 `第二行`** —— 这条直接解析失败，可能被丢弃，也可能让整个流断掉。

正确写法是每行都盖章：

```
data: 第一行
data: 第二行
```""",
        "example": """text = "第一行\\n第二行"
print("错误写法:")
print("data: " + text)
print()
print("正确写法:")
for line in text.split("\\n"):
    print("data: " + line)
print()""",
        "example_output": """错误写法:
data: 第一行
第二行

正确写法:
data: 第一行
data: 第二行
""",
        "pitfalls": [
            "多行文本只给第一行加 `data: ` 前缀：客户端把它拆成两个事件，第二个缺 data 直接报错",
            "忘了 `data: ` 里那个空格：`data:hello` 在部分客户端会被当成字段名 `data:hello`",
            "不发心跳：经过负载均衡器时 60 秒无数据被判定空闲，连接直接被掐",
            "Nginx 开着 proxy_buffering：服务端一条条发，客户端攒一大坨才收到，流式效果全没了",
        ],
        "task": """请实现 `encode_sse(event)`：把一个事件字典编码成 SSE 文本块。

- `event` 是 dict，可能包含 `id`、`event`、`data`
- 输出顺序固定：`id` → `event` → `data`，最后跟一个空行（即结尾是 `\\n\\n`）
- `data` 是字符串时按行拆分，**每一行**都输出成 `data: 行内容`
- `data` 是其它类型时先 `json.dumps(data, ensure_ascii=False)` 再按上面的规则处理
- **没有 `data` 键时抛 `ValueError`**""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先判 `if "data" not in event: raise ValueError(...)`。`isinstance(data, str)` 决定要不要 `json.dumps`。拼行用列表 + `"\\n".join(lines) + "\\n\\n"`。""",
        "checker": SSE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "大模型逐字输出为什么普遍用 SSE 而不是 WebSocket？",
                "options": [
                    "SSE 支持双向通信，WebSocket 只能单向",
                    "SSE 是单向推送、基于普通 HTTP，实现和部署都更简单，浏览器还自带重连",
                    "WebSocket 不能传中文",
                    "SSE 的带宽一定更低",
                ],
                "answer_index": 1,
                "explanation": "模型输出本来就是单向的，不需要 WebSocket 的双向能力。SSE 走普通 HTTP，代理、鉴权、部署都更省事，浏览器 `EventSource` 还自带断线重连。",
            },
            {
                "type": "choice",
                "stem": "SSE 里一段带换行的文本应该怎么发？",
                "options": [
                    "直接拼在 `data: ` 后面",
                    "每一行都加上 `data: ` 前缀",
                    "把换行替换成 `\\n` 字面量",
                    "拆成多个 HTTP 请求",
                ],
                "answer_index": 1,
                "explanation": "SSE 协议规定 data 字段按行累积，每行都必须有前缀。只给第一行加前缀会让后续行变成非法字段。",
            },
            {
                "type": "judge",
                "stem": "SSE 连接长时间没有数据时，中间代理可能会把它当成空闲连接断开，所以需要定期发心跳。",
                "answer": True,
                "explanation": "Nginx、负载均衡器通常有 60 秒空闲超时。发 `: ping` 这样的注释行既不产生业务数据，又能保活。",
            },
            {
                "type": "blank",
                "stem": "补全 FastAPI 的流式响应（用 ___ 表示要填的部分）：\\nreturn StreamingResponse(gen(), media_type=\"text/___-stream\")",
                "answer": "event",
                "hint": "填一个英文单词，SSE 的英文首字母缩写里就有它",
                "explanation": "SSE 的 MIME 类型是 `text/event-stream`。写成 `text/stream` 或 `application/json` 浏览器都不会按 SSE 解析。",
            },
        ],
    },
]
