"""「后端服务工程」「多模态与部署」「AI 工程质量」13 课在项目里的真实落点。

这批课有些地方项目做得比课程更细（例如小程序 401 的串号坑），
也有些地方项目还没做完（支付回调验签、图表 Top N 合并）——都如实标注。
"""

from .learn_project_base import absent, choice, judge, used

REFS: dict[str, dict] = {
    "be-fastapi": used(
        "core/auth.py", "60-73",
        '''def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """从请求中获取当前用户（FastAPI 依赖注入）"""
    token = credentials.credentials
    payload = decode_token(token)

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )''',
        "`core/auth.py::get_current_user`，被 `api/*.py` 里几乎所有接口用 `Depends(get_current_user)` 引用。",
        "这就是课程讲的**依赖注入**的标准形态：`HTTPBearer` 负责从 `Authorization: Bearer xxx` 里取 token，"
        "`Depends` 负责在每个接口执行前调用它。好处在测试时最明显 —— "
        "`app.dependency_overrides[get_current_user] = lambda: {...}` 一行就能跳过真实鉴权。"
        "注意它抛的是 **401**（凭证无效），而下游 `get_current_admin` 抛的是 **403**（权限不足）——"
        "课程里强调的「404/405 别搞混」在这里是同一类问题：状态码选错，排查方向就跑偏。"
        "还有一个细节：`headers={\"WWW-Authenticate\": \"Bearer\"}` 是 HTTP 规范要求的，"
        "漏了它有些客户端不会触发重新认证。",
        [
            choice("`get_current_user` 在 token 无效时返回 401，而 `get_current_admin` 在不是管理员时返回 403，为什么？",
                   ["随手写的，没有区别", "401 表示「没认证/凭证无效」，403 表示「认证过了但没权限」，语义不同", "403 比 401 更安全", "为了兼容旧版浏览器"],
                   1, "401 是身份问题（该重新登录），403 是权限问题（登录了也没用）。混用会让前端做出错误的重试行为。"),
            judge("FastAPI 的 `Depends` 只是语法糖，测试时没办法替换掉真实鉴权。", 0,
                  "错。`app.dependency_overrides` 可以整体替换依赖，这正是依赖注入相对「每个接口手写鉴权」的核心优势。"),
        ],
    ),
    "be-auth": used(
        "core/auth.py", "43-56",
        '''def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}''',
        "`core/auth.py` 的签发与校验，全项目登录态都走这两个函数。",
        "三件事和课程完全对得上：① `data.copy()` 而不是直接改传入的 dict —— 避免调用方拿到被偷偷塞了 exp 的对象；"
        "② `jwt.decode(..., algorithms=[ALGORITHM])` **显式指定算法**，这是防 `alg: none` 攻击的关键，"
        "很多漏洞就是因为让 token 自己声明用什么算法；③ 解码失败返回 `{}` 而不是抛异常，"
        "让调用方用 `payload.get(\"sub\")` 自然处理「没登进来」的情况。"
        "另外这个项目还做了个课程没展开的设计：员工端用**同一套账号密码**登录，"
        "但 `/auth/staff/login` 签发的 token 带 `scope=staff`，`get_current_admin` 里会把它挡掉（403）——"
        "这就是「降权令牌」，同一个人的两种身份用不同 scope 区分，比建两套账号表简单得多。",
        [
            choice("`jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])` 里为什么要显式传 algorithms？",
                   ["为了加快解码速度", "防止 token 自己声明算法（如 alg:none）被伪造通过", "支持多种编码格式", "这是 Python 语法要求"],
                   1, "不指定算法时，库可能按 header 里的 alg 去验，攻击者改成 none 或换算法就能绕过签名。必须由服务端写死。"),
            judge("同一个员工账号，用 admin 身份和管理员身份登录，应该签发完全相同的 token。", 0,
                  "错。项目用 scope=staff 签发降权令牌，get_current_admin 会拒绝 staff scope，从而限制员工端只能访问 /staff/api/*。"),
        ],
    ),
    "be-sse": used(
        "api/chat.py", "181-189",
        '''    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )''',
        "`api/chat.py` 的 `/chat/stream` 接口，把 Agent 的逐字输出包装成 SSE；`api/kb_agent.py` 里还有一层 `_sse()` 统一封装。",
        "三个响应头各管一件事，缺一个流式效果都可能打折："
        "`Cache-Control: no-cache` 防止中间层缓存整段响应；"
        "`Connection: keep-alive` 保持长连接；"
        "**`X-Accel-Buffering: no` 是给 Nginx 看的** —— 它明确告诉 Nginx 不要缓冲这个响应，"
        "否则会攒够一个 buffer 才下发，用户看到的是「等了 10 秒突然全出来」。"
        "这正是课程里「关掉 proxy_buffering」那句话在代码层的落地方式："
        "改 nginx.conf 是全局的，加响应头只影响这一个接口，更精准。"
        "顺带一提，`media_type` 必须是 `text/event-stream`，写成 `text/plain` 浏览器不会按 SSE 解析。",
        [
            choice("`X-Accel-Buffering: no` 这个响应头是给谁看的？",
                   ["浏览器", "Nginx（反向代理），让它不要缓冲流式响应", "FastAPI 框架", "Redis"],
                   1, "它是 Nginx 的私有头。不关缓冲的话，流式数据会被攒在代理层，用户感知不到逐字输出。"),
            judge("SSE 接口只要 `media_type` 写成 `text/event-stream` 就一定能流式输出。", 0,
                  "错。还要过得了中间代理这一关（缓冲）、服务端要 flush、客户端要按 SSE 解析。任何一环不配合，表现都是「一次性返回」。"),
        ],
    ),
    "be-ratelimit": used(
        "core/cache.py", "260-275",
        '''    def rate_limit_hit(self, scope: str, max_req: int, window: int = 60) -> bool:
        """计数窗口频控：scope 是调用方拼好的标识（桶名 + 身份），返回 True 表示放行。

        各接口的桶名由调用方决定（如 "write:user:12"、"vision:ip:1.2.3.4"），
        互不干扰；Redis 不可用时一律放行，不因为缓存挂掉而阻断业务。
        """
        if not self.available:
            return True
        try:
            key = f"rag:ratelimit:{scope}"
            current = self._client.incr(key)
            if current == 1:
                self._client.expire(key, window)
            return current <= max_req''',
        "`core/cache.py::rate_limit_hit`，各接口用不同 `scope` 前缀做多桶限流。",
        "**这里项目和课程讲的是两种算法，要分清**：项目用的是 `INCR + EXPIRE` 的**固定窗口**，"
        "课程讲的是 ZSET 滑动窗口。固定窗口实现最省（一个 key 一个计数），但有课程里说的"
        "「边界突刺」—— 第 59 秒打满、第 61 秒又打满，2 秒内放进 2 倍流量。"
        "项目注释也很坦诚：「Redis 不可用时一律放行，不因为缓存挂掉而阻断业务」——"
        "这是**限流器的降级策略**，宁可暂时不设防，也不能让限流组件成为新的故障点。"
        "另一个值得学的设计：`scope` 由调用方拼（`write:user:12` / `vision:ip:1.2.3.4`），"
        "一个函数支持任意多套桶，不用为每个接口写一遍限流代码。",
        [
            choice("项目用 `INCR + EXPIRE` 做限流，它属于哪种算法？有什么已知缺陷？",
                   ["滑动窗口，没有缺陷", "固定窗口，窗口边界处可能放进两倍流量", "令牌桶，无法限制突发", "漏桶，会丢弃所有请求"],
                   1, "INCR 计数到点时清零，是典型固定窗口。边界突刺是它的固有缺陷，滑动窗口（ZSET 记时间戳）才能解决。"),
            judge("限流器依赖的 Redis 挂了，应该直接拒绝所有请求，保证系统不被压垮。", 0,
                  "错。项目选择「Redis 不可用就放行」：限流是保护手段，不能因为保护组件自己挂了就把业务全部熔断。"),
        ],
    ),
    "be-async-task": used(
        "core/async_tasks.py", "46-70",
        '''class AsyncTaskProcessor:
    """异步任务处理器"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks = {}
                    cls._instance._queue = queue.Queue()
                    cls._instance._worker = None
                    cls._instance._running = False
        return cls._instance

    def start(self):
        if self._running:
            return
        self._running = True
        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()''',
        "`core/async_tasks.py`，文档入库异步化用的就是它；`AsyncTask` 保存 status/result/error。",
        "结构和课程讲的一致：**状态机**（`TaskStatus` 枚举 PENDING/PROCESSING/COMPLETED/FAILED）+ "
        "**队列**（`queue.Queue`）+ **单个 worker 线程**（`daemon=True`，主进程退出时自动结束）。"
        "几个工程细节值得注意：① 用 `daemon=True` 而不是普通线程，否则进程退出时会卡在等任务跑完；"
        "② `clean_old_tasks(max_age=3600)` 定期清理已完成的记录 —— 否则 `_tasks` 字典会无限增长，"
        "这是「内存版任务表」最常见的泄漏点；③ 单例用双重检查锁，和 `EmbeddingEngine` 同一套写法。"
        "**局限也要看清**：任务存在进程内存里，服务一重启，所有 PENDING 任务直接消失，"
        "也没有跨进程的重试。这就是课程里说的「线程池方案单机可用、要重试和持久化就得上 Celery/RQ」。",
        [
            choice("项目把任务存在 `AsyncTaskProcessor._tasks` 这个字典里，最大的风险是什么？",
                   ["字典查询太慢", "进程重启后任务全部丢失，无法恢复或重试", "字典不支持并发", "无法记录状态"],
                   1, "内存态任务表不持久化。重启即丢，也没有跨进程重试——这是单机线程方案的固有短板。"),
            judge("`daemon=True` 的 worker 线程会让主进程在退出时等待所有任务跑完。", 0,
                  "错。daemon 线程恰恰相反：主进程退出时它会被强行结束，不会阻塞退出。要保证任务跑完反而不能用 daemon。"),
        ],
    ),
    "be-payment": used(
        "api/pay.py", "268-284",
        '''    order = get_card_order_by_no(payload.get("out_trade_no", ""))
    if not order:
        return {"code": "FAIL", "message": "订单不存在"}
    if order["status"] == "paid":
        return {"code": "SUCCESS", "message": "重复通知忽略"}

    update_card_order_status(order["order_no"], "paid",
                             transaction_id=payload.get("transaction_id", ""))
    from database.db import get_card
    card = get_card(order["card_id"])
    add_user_card(order["user_id"], order["card_id"], order["card_name"], order["order_no"],
                  coins=_parse_coins(card["name"], card.get("description", "")) if card else 0,
                  kind=_card_kind(card) if card else "member")''',
        "`api/pay.py::pay_notify` —— 微信支付结果通知的处理入口。",
        "**幂等这一步项目做对了**：`if order[\"status\"] == \"paid\": return {\"code\": \"SUCCESS\", ...}` —— "
        "重复回调直接返回成功、**不再发卡**，这正是课程里最关键的第 4 步。"
        "返回 `SUCCESS` 而不是报错也很重要，否则微信会一直重试。"
        "但**验签这一环还没落地**：函数上方明确写着 `# TODO 商户号开通后联调：验签(Wechatpay-Signature) + "
        "平台证书 + AES-256-GCM 解密`，现在 `plaintext` 为空会直接抛错返回 FAIL —— 也就是说"
        "「伪造回调」这条攻击路径目前是靠「回调根本跑不通」来兜的，不是靠密码学。"
        "课程里强调的三道防线，项目落地了两道（金额以 cards 表为准、幂等发卡），验签待补。",
        [
            choice("`pay_notify` 里 `if order[\"status\"] == \"paid\": return {\"code\": \"SUCCESS\"}` 的作用是什么？",
                   ["跳过验签流程", "实现幂等：重复回调返回成功但不再发卡", "把订单标记为失败", "触发退款"],
                   1, "微信会重复投递同一笔回调。已支付就返回成功（避免它继续重试），但不重复执行发卡这个副作用。"),
            judge("项目当前的支付回调已经做了完整的签名验证，可以安全上线。", 0,
                  "错。代码里验签仍是 TODO（等商户号开通后联调），现在只是因为 plaintext 取不到而提前失败。这道防线不能算做了。"),
        ],
    ),
    "mm-vision": used(
        "services/vision_service.py", "117-139",
        '''def _extract_json(raw: str) -> Optional[dict]:
    """从模型输出里抠出 JSON 对象。推理/多模态模型爱加围栏或解释，必须容错。"""
    if not raw:
        return None
    text = raw.strip()
    # 去 ``` / ```json 围栏
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\\s*", "", text)
        text = re.sub(r"\\s*```$", "", text).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # 退化：取首个 { 到末个 }
    i, j = text.find("{"), text.rfind("}")''',
        "`services/vision_service.py::_extract_json`，失物招领的图片识别结果就靠它解析。",
        "项目的解析策略比课程写的**更稳一点**，顺序值得学："
        "① 先去 markdown 围栏；② **先试整体 `json.loads`**；③ 整体失败才退化成「首尾花括号切片」。"
        "课程里的写法是直接切片，遇到「两段 JSON 拼在一起」会切出一个非法字符串然后返回 None；"
        "项目先试整体解析，干净输出的场景下更快，脏输出才走兜底，行为更可预测。"
        "其余细节和课程一致：`isinstance(obj, dict)` 挡掉数组，异常一律吞掉返回 `None`。"
        "再往上看还能看到一个真实的性能设计：识别结果按**图片内容 md5** 缓存 5 分钟，"
        "因为「选图预识别」和「提交入库」会对同一张图调用两次。",
        [
            choice("项目 `_extract_json` 为什么先整体 `json.loads`，失败后才切片？",
                   ["整体解析更慢但更准", "干净输出时更快更准，脏输出才需要兜底，行为更可预测", "切片写法有 bug", "为了兼容 Python 2"],
                   1, "先试最严格的路径，失败再退化。直接切片在「两段 JSON 拼接」时会切出非法内容，虽然也返回 None，但先试整体能减少误判。"),
            judge("图片识别的结果不需要缓存，因为模型调用很快。", 0,
                  "错。视觉模型一次 2~4 秒，而同一张图在「选图预识别」和「提交入库」会被调用两次。项目按内容 md5 缓存 5 分钟，第二次直接命中。"),
        ],
    ),
    "mm-ocr": used(
        "data_pipeline.py", "10-21",
        '''def extract_text_from_pdf(file_path: str) -> str:
    """PDF扫描件/电子PDF OCR文字提取"""
    result = ocr.ocr(file_path, cls=True)
    text_lines = []
    for page in result:
        if page:
            for line in page:
                text_lines.append(line[1][0])
    raw_text = "\\n".join(text_lines)
    # 基础清洗
    clean_text = raw_text.replace(" ", "").replace("\\t", "").strip()
    return clean_text''',
        "`data_pipeline.py::extract_text_from_pdf`，入库流水线的第 1、2 步（抽取 + 清洗）。",
        "两层循环对应 PaddleOCR 的返回结构：**外层是页，内层是行**，`line[1][0]` 取的是"
        "「识别文本」（`line[0]` 是四个角点坐标、`line[1][1]` 是置信度）。"
        "这里**没有做课程讲的「按 y 坐标合并段落」**，而是直接用 `\"\\n\"` 把每行串起来 —— "
        "好处是简单、保留了原始换行；代价是同一段被折行的句子在文本里是断开的，"
        "后面 `split_text` 按 Markdown 标题切时拿不到完整语义边界。"
        "清洗那句 `replace(\" \", \"\")` 也值得注意：**中文场景删空格是对的**（OCR 常在汉字间插空格），"
        "但如果文档里有英文或数字，`10 元` 会变成 `10元`、`AI Agent` 会变成 `AIAgent` —— "
        "这是个典型的「为中文优化、牺牲了混排」的取舍。",
        [
            choice("`line[1][0]` 在 PaddleOCR 的返回里取的是什么？",
                   ["文本框的左上角坐标", "识别出的文本内容", "置信度", "页码"],
                   1, "PaddleOCR 每行是 `[四点坐标, (文本, 置信度)]`。`line[1][0]` 是文本，`line[1][1]` 才是置信度。"),
            judge("`replace(\" \", \"\")` 这种清洗方式对中英文混排文档完全没有副作用。", 0,
                  "错。它会把英文单词间、数字与单位间的空格也删掉（`AI Agent` → `AIAgent`），影响检索和阅读。"),
        ],
    ),
    "mm-docker": used(
        "Dockerfile", "24-27",
        '''COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \\
    -i https://pypi.tuna.tsinghua.edu.cn/simple \\
    && rm -rf /root/.cache/pip''',
        "`Dockerfile` 第 24~27 行：先拷依赖清单、装依赖；`COPY . .` 在它之后（第 33 行）。",
        "**分层缓存这一点做对了**：`COPY requirements.txt` 在 `COPY . .` 之前，"
        "改代码不会触发依赖重装 —— 这正是课程强调的顺序。`--no-cache-dir` 也是必须的，"
        "否则 pip 缓存会被打进镜像层，白白多几百 MB；加了国内镜像源 `-i pypi.tuna...` "
        "能让构建快很多（但镜像源不可用时也会让构建失败，属于可用性换速度）。"
        "往下第 42~43 行还有 `HEALTHCHECK ... CMD curl -f http://localhost:8000/health`，"
        "对应课程里说的「depends_on 不等于就绪」—— 有了它 compose 才能用 "
        "`condition: service_healthy` 等真正就绪。"
        "但要注意：**这个 Dockerfile 是单阶段的**，只有一个 `FROM python:3.10-slim`，"
        "没有用多阶段构建瘦身 —— 课程里讲的多阶段是「应该怎么做」，不是「项目已这么做」。"
        "另外 `EXPOSE 8000` 和 HEALTHCHECK 里的端口是硬编码的，改端口时两处都要一起改"
        "（这和本项目把 8001 散落在 5 个文件里是同一类问题）。",
        [
            choice("先把 `requirements.txt` 单独 COPY 再 `pip install`，主要收益是什么？",
                   ["镜像更小", "改源码时不会让依赖层缓存失效，构建快很多", "支持多阶段构建", "能自动升级依赖"],
                   1, "Docker 按层缓存。依赖清单没变时，pip install 那层直接复用；否则改一行代码就要重装全部依赖。"),
            judge("项目 Dockerfile 用了多阶段构建来减小镜像体积。", 0,
                  "错。它只有一个 FROM（python:3.10-slim），是单阶段。多阶段是课程讲的最佳实践，项目还没做。"),
        ],
    ),
    "mm-miniprogram": used(
        "miniprogram/src/utils/api.ts", "53-59",
        '''  // 401：只处理"本来就没登录"的情况 —— 用静默微信登录补一个 token 给公开页面用。
  // ⚠️ 绝不能对"已有 token 但过期/失效"的请求做强制静默登录：
  //    那会用微信身份换一个**另一个账号**的 token 覆盖当前会话，
  //    用户会突然变成"游客"、我的页数据全空（拿的是另一个账号的数据），且不会自愈。
  //    正确做法是把"登录已过期"如实抛给调用方，由页面引导重新登录。
  if (res.statusCode === 401 && auth && retryOn401) {
    if (getToken()) {
      throw new ApiError('登录已过期，请重新登录', 401)
    }''',
        "`miniprogram/src/utils/api.ts::request()` —— 所有小程序请求的统一入口。",
        "**这段注释直接推翻了课程里那个「401 就静默重登」的简化说法**，而且写的是真实事故："
        "小程序里 `wx.login()` 拿到的是**当前微信身份**的 code。如果用户原本是账号 A（已经绑了微信），"
        "token 过期后你偷偷用 `wx.login()` 换一个新 token，很可能换回来的是**账号 B（游客）**——"
        "于是用户的会话被静默顶替，进度、卡券全空，而且「换回去」没有任何入口，不会自愈。"
        "所以项目的正确做法是：**只在「本来就没登录」时才静默补 token**；"
        "「已有 token 但过期」如实抛 401，由页面引导用户重新登录。"
        "课程里 `call_with_relogin` 那个模式在 Web 端（refresh token 明确绑定同一账号）是成立的，"
        "但**搬到小程序就是坑**。这就是为什么「同一个技术模式在不同端不能照抄」。",
        [
            choice("小程序里对「已有 token 但过期」的请求做静默 `wx.login()` 重登，最大的风险是什么？",
                   ["登录接口会被限流", "可能换回另一个账号的 token，用户会话被静默顶替且无法自愈", "token 会变长", "页面会白屏 3 秒"],
                   1, "wx.login 绑定的是当前微信身份，不保证还是原来那个账号。一旦串号，用户的进度和数据都会「消失」。"),
            judge("Web 端的「401 → refresh token → 重放请求」模式，可以原样搬到小程序。", 0,
                  "错。Web 的 refresh token 明确绑定同一账号，重放是安全的；小程序的 wx.login 换取的是「当前微信身份」，可能是另一个账号。"),
        ],
    ),
    "ai-grounding": used(
        "agents/verification_agent.py", "45-48",
        '''【硬性要求】
1. ⚠️ 如果第三块（园区参考资料）**有内容但不足以**回答用户问题，
   **只输出这一行、不要写别的**：暂时没有查询到相关信息
   （这一行是给系统的信号，系统会换成更合适的引导话术，用户看不到它。）''',
        "`VerificationAgent.GENERATE_PROMPT` 里的【硬性要求】第 1 条（第 45~48 行；整段 prompt 从第 25 行开始）。",
        "课程讲的「四道防线」，这一段覆盖了第 2 道（prompt 约束），而且做得比课程更细："
        "① 把上下文**分成三块并规定各自用途**（画像可直答、历史只解指代、资料才是事实来源）——"
        "不分块的话模型会把「用户说过的话」当成「园区规则」，这是很隐蔽的一类幻觉；"
        "② 明确写出「这块没写到的，如实说没有」，也就是课程强调的「允许拒答」；"
        "③ **设计了一个机器可识别的信号行** `暂时没有查询到相关信息` ——"
        "模型只输出这一行时，系统识别到并换成更友好的引导话术，用户看不到这句生硬的原文。"
        "这个「信号行」设计非常实用：比让另一个模型去判断「它是不是在拒答」便宜得多，而且是确定性的。",
        [
            choice("prompt 里把上下文分成「用户画像 / 对话历史 / 园区资料」三块，主要防的是什么？",
                   ["prompt 太长超出上下文", "模型把「用户说过的话」当成「园区规则」这类隐蔽幻觉", "提高生成速度", "方便做多语言"],
                   1, "不分块时，模型会把三处信息一视同仁。用户随口说「听说票价十块」，模型可能当事实回答。分块 + 规定用途能显著降低这类错误。"),
            judge("让模型直接输出「暂时没有查询到相关信息」并展示给用户，是防幻觉的最佳做法。", 0,
                  "错。项目把它设计成**给系统看的信号行**，识别后替换成更友好的引导话术。直接展示会很生硬，用户体感差。"),
        ],
    ),
    "ai-router": used(
        "agents/router_agent.py", "137-168",
        '''    @staticmethod
    def _rule_route(query: str) -> Dict:
        """复用各 Agent 已有的关键词判定（0 LLM）。

        顺序与 orchestrator 现有分流顺序保持一致（map > business/account/service），
        保证"路由结果不改变既有行为"。
        """
        try:
            from agents.map_agent import map_agent
            if map_agent.is_map_question(query):
                return {"agent": "map", "intent": "位置与出行", "confidence": 1.0,
                        "source": "rule"}
        except Exception:
            pass''',
        "`agents/router_agent.py::RouterAgent._rule_route()` —— L1 规则快速通道；下面是 `_llm_route()` 做 L2。",
        "三级路由在项目里是完整落地的：L1 复用已有 Agent 的关键词判定（0 次 LLM），"
        "L2 用 `LLM_TEXT_MODEL` 单次分类并带 `ROUTER_TIMEOUT` 硬超时，失败一律返回 `agent=rag`。"
        "两个设计细节值得单独记：① **每个 Agent 的判定都包了 `try/except: pass`** ——"
        "某个 Agent 的模块导入失败不能连累整条路由，这比「一个 if 抛异常全挂」健壮得多；"
        "② 注释里写「顺序与 orchestrator 现有分流顺序保持一致，保证路由结果不改变既有行为」——"
        "**引入新路由时先保证行为不变**，再谈优化，这是很成熟的改造策略。"
        "课程里说的「规则优先于缓存」在项目里也是这么排的：`_rule_route` 在最前面，命中就返回。",
        [
            choice("`_rule_route` 里每个 Agent 的判定都包了 `try/except: pass`，目的是什么？",
                   ["为了少写代码", "某个 Agent 模块出问题时不影响整条路由，继续尝试下一个", "隐藏错误日志", "加快匹配速度"],
                   1, "路由是横切逻辑，任何一个分支抛异常都可能导致整个请求失败。逐个兜住，坏的跳过、好的照用。"),
            judge("引入三级路由时，应该顺便把原有分流逻辑一起改掉，一步到位。", 0,
                  "错。项目注释明确写了「保证路由结果不改变既有行为」——先让新机制等价替换，验证无回归后再改行为。"),
        ],
    ),
    "ai-chart": used(
        "services/chart_render.py", "58-64",
        '''def _render_hbars(items: List[Dict], title: str, subtitle: str,
                  value_of, label_of, color_field=None, filename: str = "") -> bool:
    """通用横向条形图。items 有序，value_of/d label 控制取值与文案"""
    if not items:
        return False
    top = min(len(items), 10)
    shown = items[:top]''',
        "`services/chart_render.py::_render_hbars()` —— 项目游玩排行、办卡统计都走这个函数，输出 PNG 到 static/charts/。",
        "**这里和课程讲的做法有实质差异，值得对照**：课程建议「Top N + 其他」，"
        "项目是 `top = min(len(items), 10)` 后直接 `items[:top]` —— **只截断、不合并「其他」**。"
        "后果是图上柱子总和小于真实总量，读者容易低估规模。"
        "在游乐园这个场景里影响可控（项目名有十几个，前 10 名基本覆盖大头），"
        "但如果做的是「消费构成」这类需要看总量的图，就必须补上「其他」那一根。"
        "另外注意 `if not items: return False` —— 返回布尔而不是抛异常，"
        "调用方可以「这张图没画出来就跳过」，符合课程说的「单图失败不阻塞整体回答」。"
        "函数签名里的 `value_of` / `label_of` 是**回调注入**：同一个绘图函数既能画「次数」也能画「金额」，"
        "不用为每种指标复制一份绘图代码。",
        [
            choice("项目 `_render_hbars` 直接 `items[:10]` 截断，没有合并「其他」，会带来什么问题？",
                   ["柱子颜色不够多", "图上总和小于真实总量，读者会低估规模", "渲染速度变慢", "中文会乱码"],
                   1, "只画前 10 名而不合并剩余项，视觉上的总量就失真了。类别多且要看构成时，必须补一根「其他」。"),
            judge("`_render_hbars` 在 items 为空时抛异常，让调用方必须处理。", 0,
                  "错。它 `return False`。图表是增强信息，失败应该被跳过而不是中断整条回答。"),
        ],
    ),
}
