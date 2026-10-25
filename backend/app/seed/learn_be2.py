"""科目：后端服务工程（第二批 · 3 课）。

这三课都围绕「线上真会出事的地方」：请求被打爆、任务跑超时、支付回调重复投递。
每一课的错误做法都能在真实事故里找到对应案例。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）
"""

RATE_CHECKER = """
try:
    assert rate_limit([], 0) == (True, [0]), "空历史当然放行，并且要把这次请求记进去"
    assert rate_limit([0, 10, 20], 30) == (False, [0, 10, 20]), "60 秒窗口内已有 3 次（limit=3），第 4 次必须拒绝，且历史不变"

    r = rate_limit([0, 10, 20], 60)
    assert r == (True, [10, 20, 60]), "now=60 时 t=0 刚好满 60 秒，要被清出窗口；剩下 2 次所以放行，现在是 %r" % (r,)

    r2 = rate_limit([0, 10], 100, limit=3, window=60)
    assert r2 == (True, [100]), "两条历史都已超过 60 秒，应全部清掉，只留本次，现在是 %r" % (r2,)

    assert rate_limit([], 5, limit=1, window=60) == (True, [5]), "limit=1 时第一次放行"
    assert rate_limit([5], 10, limit=1, window=60) == (False, [5]), "limit=1 时第二次必须拒绝"

    r3 = rate_limit([100], 150, limit=2, window=60)
    assert r3 == (True, [100, 150]), "limit=2 时留 1 条历史，本次可以放行，现在是 %r" % (r3,)

    assert rate_limit([59], 60, limit=2, window=1) == (True, [60]), "窗口设成 1 秒时，59 秒前的记录立刻失效"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, ValueError) as e:
    print("__FAIL__ 返回结构不对（约定返回 (是否放行, 保留的时间戳列表) 二元组）：" + str(e))
"""

QUEUE_CHECKER = """
try:
    tasks = [{"id": "a"}, {"id": "b"}, {"id": "c"}]

    def h(t):
        if t["id"] == "b":
            raise RuntimeError("boom")

    r = process_queue(tasks, h)
    assert r["done"] == ["a", "c"], "b 失败不能拖住后面的任务，a 和 c 都要完成，现在是 %r" % (r["done"],)
    assert r["failed"] == ["b"], "b 重试用尽后要进 failed，现在是 %r" % (r["failed"],)
    assert r["attempts"] == {"a": 1, "b": 3, "c": 1}, "默认 max_retry=2 表示最多试 3 次：a/c 各 1 次，b 试满 3 次，现在是 %r" % (r["attempts"],)

    def always_fail(t):
        raise ValueError("x")

    r2 = process_queue([{"id": "x"}], always_fail, max_retry=0)
    assert r2["failed"] == ["x"] and r2["attempts"]["x"] == 1, "max_retry=0 表示不重试，只尝试 1 次"

    r3 = process_queue([], h)
    assert r3 == {"done": [], "failed": [], "attempts": {}}, "空任务列表要返回空结果，现在是 %r" % (r3,)

    n = {"v": 0}

    def flaky(t):
        n["v"] += 1
        if n["v"] < 2:
            raise RuntimeError("第一次抖动")

    r4 = process_queue([{"id": "y"}], flaky, max_retry=2)
    assert r4["done"] == ["y"] and r4["attempts"]["y"] == 2, "第一次失败、第二次成功时，应记为完成且尝试次数为 2，现在是 %r" % (r4,)

    r5 = process_queue([{"id": "p"}, {"id": "q"}], always_fail, max_retry=1)
    assert r5["attempts"] == {"p": 2, "q": 2}, "每个任务的尝试次数要独立统计，不能串味"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, AttributeError) as e:
    print("__FAIL__ 返回结构不对（约定返回 done / failed / attempts 三个键）：" + str(e))
"""

PAY_CHECKER = """
try:
    import hashlib
    import hmac

    def sign(oid, amt, secret="s"):
        msg = ("%s:%s" % (oid, amt)).encode()
        return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

    orders = {"ORD-1": {"amount": 10, "paid": False}}

    assert handle_payment(orders, "ORD-X", {"amount": 10, "sign": sign("ORD-X", 10)}, "s") == "not_found", "订单不存在时先返回 not_found，不要去校验签名"

    assert handle_payment(orders, "ORD-1", {"amount": 10, "sign": "deadbeef"}, "s") == "bad_sign", "签名对不上必须拒绝 —— 这是回调防伪造的唯一防线"

    assert handle_payment(orders, "ORD-1", {"amount": 999, "sign": sign("ORD-1", 999)}, "s") == "amount_mismatch", "签名合法但金额与订单不一致，必须拒绝（金额不能信回调）"

    assert orders["ORD-1"]["paid"] is False, "以上三种失败都不能把订单改成已支付"

    assert handle_payment(orders, "ORD-1", {"amount": 10, "sign": sign("ORD-1", 10)}, "s") == "ok", "签名和金额都对，应当支付成功"
    assert orders["ORD-1"]["paid"] is True, "成功后订单状态要落库"

    assert handle_payment(orders, "ORD-1", {"amount": 10, "sign": sign("ORD-1", 10)}, "s") == "already_paid", "微信可能重复投递同一笔回调，第二次必须幂等返回 already_paid"
    assert orders["ORD-1"]["paid"] is True, "重复回调不能把状态改回去"

    orders2 = {"ORD-2": {"amount": 100, "paid": True}}
    assert handle_payment(orders2, "ORD-2", {"amount": 100, "sign": sign("ORD-2", 100)}, "s") == "already_paid", "已支付订单的任何回调都不应该再发一次卡"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, AttributeError) as e:
    print("__FAIL__ 返回结构不对（约定返回字符串状态码）：" + str(e))
"""

LESSONS = [
    {
        "code": "be-ratelimit",
        "subject": "后端服务工程",
        "stage": "接口与流式",
        "runner": "python",
        "title": "Redis 滑动窗口限流",
        "summary": "固定窗口会在边界处放进来两倍流量",
        "definition": """**限流 = 限制单位时间内的请求次数。** 目的有三个：防刷（恶意脚本）、保护下游（模型 API 有配额）、保证公平（一个用户不能占满全部并发）。

**三种常见算法**：

| 算法 | 思路 | 问题 |
|---|---|---|
| 固定窗口 | 每分钟一个计数器，到点清零 | **边界突刺**：第 59 秒打满，第 61 秒又打满，2 秒内进来 2 倍流量 |
| 滑动窗口 | 始终看「最近 60 秒」 | 需要记录每个请求的时间戳，内存稍高 |
| 令牌桶 | 按速率往桶里放令牌，请求取令牌 | 允许短时突发，最平滑 |

**滑动窗口的 Redis 实现**（ZSET）：

```
ZREMRANGEBYSCORE key 0 (now-window    # ① 删掉窗口外的旧记录
ZCARD key                             # ② 数一数窗口内还有几次
# 如果 < limit：
ZADD key now now                      # ③ 记录本次请求
EXPIRE key window                     # ④ 给 key 设过期，避免僵尸 key
```

四步必须放在一个 Lua 脚本或事务里，否则并发时「数完再写」中间会插进别的请求，限流就漏了。

**key 怎么设计**：按维度组合——`rl:ip:1.2.3.4`、`rl:user:13`、`rl:api:chat`。只按 IP 限流会误伤 NAT 后的整栋楼，只按用户限流挡不住未登录刷接口。通常是「IP 粗粒度 + 用户细粒度」两层。

**被限流要好好说话**：返回 `429 Too Many Requests`，并带上 `Retry-After: 30` 告诉客户端多久后重试。返回 200 加一句「请求太频繁」是错的——客户端和监控都识别不出来。

**项目落点**：`core/cache.py` 的 `rate_limit_hit(scope, max_req, window)` / `rate_limit_check(ip, ...)`，用 Redis 做计数，scope 传 `ip:xxx` 这样的前缀。""",
        "plain": """固定窗口像「每分钟发 60 张票，整点重新发」：

23:59:59 你抢了 60 张，00:00:01 又抢了 60 张 —— 两秒钟内你用了 120 张票，但每一分钟都没超限。这就是边界突刺。

滑动窗口像「任何时候回头看 60 秒，这 60 秒内不能超过 60 张」：

00:00:01 的时候，它会把 23:59:59 的那 60 张也算进去，所以第二波直接被拦。""",
        "example": """def fixed_window(times, now, limit=3, window=60):
    start = now - now % window
    return sum(1 for t in times if t >= start) < limit

times = [59, 59, 59]
print("59 秒时还能进吗:", fixed_window(times, 59))
print("61 秒时还能进吗:", fixed_window(times, 61))
print("只隔 2 秒，新窗口却已经把计数清零了")""",
        "example_output": """59 秒时还能进吗: False
61 秒时还能进吗: True
只隔 2 秒，新窗口却已经把计数清零了""",
        "pitfalls": [
            "用固定窗口限流：窗口边界处能在 2 秒内放进 2 倍流量，等于限流形同虚设",
            "「先查数量再写入」不加原子保护：高并发下两个请求同时通过检查，实际放行数超限",
            "只按 IP 限流：公司/校园 NAT 后面几百人共用一个出口 IP，一个人刷就把整栋楼封了",
            "被限流返回 200：客户端以为成功、监控看不到异常，实际请求全被丢弃",
        ],
        "task": """请实现 `rate_limit(timestamps, now, limit=3, window=60)`：

- `timestamps`：这个 key 过去的请求时间戳列表（升序，int）
- `now`：本次请求时间
- `window`：窗口长度（秒）
- **先清理**：只保留 `now - t < window` 的记录（正好等于 window 的算过期）
- 如果剩余条数 `< limit`：本次放行，把 `now` 追加进列表，返回 `(True, 新列表)`
- 否则：拒绝，返回 `(False, 清理后的列表)`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """列表推导 `[t for t in timestamps if now - t < window]` 就是滑动窗口的「清理」；再判 `len(kept) < limit`。返回的是清理后的列表，不是原列表。""",
        "checker": RATE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "固定窗口限流最主要的问题是什么？",
                "options": [
                    "实现太复杂，容易出 bug",
                    "窗口边界处可能放进两倍于限额的流量",
                    "会永久封禁用户",
                    "无法用 Redis 实现",
                ],
                "answer_index": 1,
                "explanation": "第 59 秒打满、第 61 秒又打满，两秒内就是 2 倍流量。滑动窗口通过「始终看最近一段」解决这个问题。",
            },
            {
                "type": "choice",
                "stem": "限流命中时，HTTP 响应应该返回什么？",
                "options": [
                    "200 + 一段友好文案",
                    "429 Too Many Requests + Retry-After",
                    "404 Not Found",
                    "500 Internal Server Error",
                ],
                "answer_index": 1,
                "explanation": "429 是限流的标准语义，`Retry-After` 告诉客户端多久后重试。返回 200 会让客户端和监控都误判成功。",
            },
            {
                "type": "judge",
                "stem": "用 Redis 做滑动窗口限流时，「先查数量再写入」这两步可以分开执行，不需要保证原子性。",
                "answer": False,
                "explanation": "并发下两个请求可能同时读到「还没超限」，然后都写入，实际放行数超过 limit。必须用 Lua 脚本或事务把检查与写入绑在一起。",
            },
            {
                "type": "blank",
                "stem": "Redis 里做滑动窗口限流最常用的数据结构是______（支持按分数范围删除成员）。",
                "answer": "ZSet",
                "hint": "填 Redis 五种基本类型之一，中文或英文均可",
                "explanation": "ZSET 用时间戳当 score，`ZREMRANGEBYSCORE` 删旧记录、`ZCARD` 数数量，天然契合滑动窗口。",
            },
        ],
    },
    {
        "code": "be-async-task",
        "subject": "后端服务工程",
        "stage": "任务与交易",
        "runner": "python",
        "title": "后台异步任务队列与重试",
        "summary": "一个任务失败，不能拖死整批",
        "definition": """**有些活不能放在 HTTP 请求里做**：文档入库、批量重编码、报表导出、给几百个用户群发消息。它们动辄几十秒到几分钟，同步做必然超时。

**方案怎么选**：

| 方案 | 适用 | 代价 |
|---|---|---|
| `BackgroundTasks`（FastAPI 内置） | 请求结束后顺手做一件小事 | 进程重启就丢，没有重试 |
| 线程池 + 队列 | 单机、中等量级、能容忍丢任务 | 要自己做状态和重试 |
| Celery / RQ + Redis | 多机、需要重试和定时 | 多一套 broker 要运维 |
| Kafka / RabbitMQ | 高吞吐、要削峰、要回放 | 最重 |

**任务状态机**（前端轮询进度就靠它）：

```
PENDING → PROCESSING → COMPLETED
              ↓
           FAILED → （重试）→ PENDING
```

**重试的三个原则**：

1. **有上限**：`max_retry` 必须有限，否则一个坏任务能无限占着队列
2. **退避**：失败后等一会儿再试（1s → 2s → 4s），立刻重试只会把下游打得更惨
3. **幂等**：重试必须安全。入库要「先删后插」，发消息要带去重键，否则重试就变成重复副作用

**失败隔离**：一个任务失败不能中断整批。用 `for` 循环逐个处理，每个任务自己 `try/except`，而不是让异常冒到最外层——那样后面的任务一个都跑不了。

**可观测性**：至少记录「任务 id、尝试次数、最后一次错误」。没有这些，线上出问题你只能猜。

**项目落点**：`core/async_tasks.py` 用线程 + `queue.Queue` + 状态机（`PENDING / PROCESSING / COMPLETED / FAILED`）实现文档入库异步化；接口立即返回任务 id，前端轮询状态。""",
        "plain": """寄快递：

- 同步 = 你抱着包裹坐火车送到对方手里，再回来接待下一位顾客。一个人卡住，整条队都停。
- 异步 = 你把包裹交给快递员，拿一张单号就走。之后用单号查「已揽收 / 运输中 / 已签收」。

**重试**就像快递送不到时再送一次 —— 但必须规定「最多送三次」，而且不能立刻再送（人家可能只是暂时不在家）。""",
        "example": """def call_with_retry(fn, max_retry=2):
    for i in range(max_retry + 1):
        try:
            return fn(), i + 1
        except Exception:
            if i == max_retry:
                return None, i + 1

tries = {"n": 0}

def flaky():
    tries["n"] += 1
    if tries["n"] < 3:
        raise RuntimeError("网络抖动")
    return "成功"

print("结果:", call_with_retry(flaky))""",
        "example_output": "结果: ('成功', 3)",
        "pitfalls": [
            "重试不设上限：一个必然失败的任务永远占着队列，后面的任务全被饿死",
            "失败后立刻重试、不做退避：下游只是短暂抖动，被重试打得更惨",
            "一个任务抛异常就中断整批：本可以完成的其它任务全被放弃",
            "重试不保证幂等：入库重试一次就多一整套重复 chunk，发消息就重复发一遍",
        ],
        "task": """请实现 `process_queue(tasks, handler, max_retry=2)`：

- `tasks`：`[{"id": ...}, ...]`
- `handler(task)`：处理函数，可能抛异常
- 每个任务最多尝试 `max_retry + 1` 次（首次 + 重试次数）
- **某个任务失败不能影响后面的任务**
- 返回字典：`{"done": [完成的 id], "failed": [失败的 id], "attempts": {id: 实际尝试次数}}`
- `done` / `failed` 都按任务原顺序；空输入返回三个空结构""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """外层 `for task in tasks`，内层 `for _ in range(max_retry + 1)` 里 `try: handler(task); ok = True; break` / `except Exception: continue`。计数用 `attempts[tid] = attempts.get(tid, 0) + 1`。""",
        "checker": QUEUE_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "文档入库为什么要做成异步任务？",
                "options": [
                    "异步能让分块质量更高",
                    "入库耗时长，同步执行会让请求超时、服务不可用",
                    "因为 Python 没有多线程",
                    "异步可以不做清洗",
                ],
                "answer_index": 1,
                "explanation": "抽取 + 分块 + 批量编码可能几分钟。放在请求里必然超时，异步化后立即返回任务 id，前端轮询进度。",
            },
            {
                "type": "choice",
                "stem": "任务重试时为什么要做「退避」（等一会儿再试）？",
                "options": [
                    "为了让日志更好看",
                    "下游可能只是短暂抖动，立刻重试会把它打得更惨",
                    "退避能减少存储占用",
                    "退避能提高单次成功率",
                ],
                "answer_index": 1,
                "explanation": "立刻重试等于把瞬时故障放大成持续压力。指数退避（1s/2s/4s）给下游恢复时间，也避免重试风暴。",
            },
            {
                "type": "judge",
                "stem": "批处理任务里，只要有一个任务抛异常，就应该让整批任务中断，避免产生不一致。",
                "answer": False,
                "explanation": "单个任务失败应该被隔离，记录后继续处理后面的任务。中断整批会让本可成功的任务全部放弃，而且重跑成本更高。",
            },
            {
                "type": "blank",
                "stem": "任务状态机里，`PROCESSING` 失败后应该进入______状态。",
                "answer": "FAILED",
                "hint": "填英文状态名，全大写",
                "explanation": "`PROCESSING → FAILED`，之后可以重试回 `PENDING`。状态机让前端能准确展示「排队中/处理中/已完成/失败」。",
            },
        ],
    },
    {
        "code": "be-payment",
        "subject": "后端服务工程",
        "stage": "任务与交易",
        "runner": "python",
        "title": "支付订单：金额锁定、幂等与回调验签",
        "summary": "回调会重复投递，重复发卡就是资金损失",
        "definition": """支付是「AI 应用里唯一直接亏钱的地方」，三条铁律：

**① 金额绝不来自客户端，更不来自 LLM**

前端传 `amount: 0.01`、模型说「这张卡 1 块钱」，都不能信。下单时必须用**服务端数据库里的权威价格**（`cards` 表）重新算一遍。否则改个请求体就能一分钱买年卡。

**② 订单号服务端生成 + 幂等键**

用户连点两下「立即支付」，不能生成两个订单发两张卡。做法是：客户端带一个 `idempotency_key`（或同一次会话 + 商品），服务端先查这个 key 有没有已存在的订单，有就返回原订单。

**③ 回调必须验签，且必须幂等**

第三方支付（微信/支付宝）是**异步回调**通知你「这笔钱到账了」。回调有两个特点：

- **可能是伪造的**：任何人只要能访问你的回调地址，就能伪造一个「支付成功」请求。所以必须验签（HMAC / 证书），签名对不上直接拒。
- **会重复投递**：网络抖动、你返回超时，支付平台都会重试。同一笔订单的回调来 3 次是正常的。

处理顺序（顺序错了就有漏洞）：

```
1. 订单存在吗？           → not_found
2. 验签通过吗？           → bad_sign
3. 回调金额 == 订单金额？  → amount_mismatch
4. 订单已经是已支付？      → already_paid（幂等返回成功，但不重复发卡）
5. 标记已支付 + 发卡
```

**第 4 步特别重要**：如果重复回调时又发一次卡，用户就会凭空多一张——这是真金白银的损失。注意「已支付」要返回**成功语义**，否则支付平台会一直重试。

**项目落点**：`api/pay.py` 的下单接口从 `cards` 表读权威价格，订单号服务端生成；正式模式回调走微信 APIv3 验签；模拟模式（`WECHAT_PAY_ENABLED=false`）直接标记支付完成，方便联调全流程。""",
        "plain": """你开了个小卖部，支付宝给你打电话：「有人给你转了 10 块，订单 A123」。

你要做的检查：

1. **这单真的存在吗**（不是骗子瞎报的订单号）
2. **电话真的是支付宝打的吗**（验签，防伪造）
3. **他说 10 块，订单上写的是 10 块吗**（金额核对）
4. **我已经给过货了吗**（幂等 —— 支付宝可能打三次电话说同一件事）

第 4 步最容易被忽略：你接三次电话就发三次货，亏的是自己。""",
        "example": """orders = {"ORD-1": {"amount": 10, "paid": False}}

def settle(order_id, callback_amount, callback_paid):
    o = orders[order_id]
    if o["paid"]:
        return "already_paid"
    if callback_amount != o["amount"]:
        return "amount_mismatch"
    o["paid"] = True
    return "ok"

print(settle("ORD-1", 10, True))
print(settle("ORD-1", 10, True))
print("已支付订单:", orders["ORD-1"])""",
        "example_output": """ok
already_paid
已支付订单: {'amount': 10, 'paid': True}""",
        "pitfalls": [
            "用前端传来的金额下单：改个请求体就能一分钱买年卡，这是最典型的资损漏洞",
            "回调不验签：任何人构造一个 POST 就能白嫖，签名是唯一防线",
            "重复回调时又发一次卡：支付平台重试 3 次，用户就多 3 张卡，直接资金损失",
            "只校验签名不校验金额：签名合法但金额被改成 0.01 也放行（签名和金额要一起校验）",
        ],
        "task": """请实现 `handle_payment(orders, order_id, callback, secret)`：

- `orders`：`{order_id: {"amount": int, "paid": bool}}`（会被原地修改）
- `callback`：`{"amount": int, "sign": str}`，签名算法为
  `HMAC-SHA256(secret, f"{order_id}:{amount}")` 的十六进制字符串
- 按顺序判断并返回状态字符串：
  1. 订单不存在 → `"not_found"`
  2. 验签失败 → `"bad_sign"`（用 `hmac.compare_digest` 做常量时间比较）
  3. 回调金额 ≠ 订单金额 → `"amount_mismatch"`
  4. 订单已支付 → `"already_paid"`（幂等，**不再修改状态**）
  5. 否则标记 `paid = True`，返回 `"ok"`""",
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": """先 `order = orders.get(order_id)`，为 None 直接 `return "not_found"`。签名用 `hmac.new(secret.encode(), f"{order_id}:{amount}".encode(), hashlib.sha256).hexdigest()`，比较用 `hmac.compare_digest`。注意「已支付」的判断要放在金额校验之后。""",
        "checker": PAY_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "下单时商品金额应该从哪里取？",
                "options": [
                    "前端请求体里传的值",
                    "大模型根据对话推断的值",
                    "服务端数据库里的权威价格",
                    "URL 查询参数",
                ],
                "answer_index": 2,
                "explanation": "前两种都能被篡改或产生幻觉。金额必须由服务端按商品 id 查库确定，客户端只传「买什么」，不传「多少钱」。",
            },
            {
                "type": "choice",
                "stem": "支付平台的回调可能重复投递，服务端应该怎么处理？",
                "options": [
                    "第二次回调直接返回 500",
                    "检测到已支付就幂等返回成功，但不重复发货/发卡",
                    "每次都发一次货，反正钱已经收了",
                    "把订单删掉重建",
                ],
                "answer_index": 1,
                "explanation": "幂等是必须的：重复回调要返回成功语义（否则平台一直重试），但业务副作用只能发生一次。",
            },
            {
                "type": "judge",
                "stem": "只要回调请求的签名校验通过，就可以信任其中的金额直接发卡。",
                "answer": False,
                "explanation": "还要校验回调金额与订单金额一致。签名只证明「消息没被篡改」，不证明「金额是对的」——下单价格和实付价格必须对账。",
            },
            {
                "type": "blank",
                "stem": "同一操作重复执行与执行一次结果相同，这种性质叫______（支付回调必须靠它防止重复发卡）。",
                "answer": "幂等",
                "hint": "填两个字，英文 idempotent",
                "explanation": "重复回调 → 检测到已支付 → 返回 already_paid，不重复发卡。这就是幂等的业务价值。",
            },
        ],
    },
]
