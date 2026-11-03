"""全局配置：环境变量优先，未设置则使用默认值。"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # dev = 本机开发；prod = 公网部署（会启用更严格的安全校验）
    ENV: str = "dev"

    DB_URL: str = "mysql+pymysql://root:root@127.0.0.1:3306/code_adventurer?charset=utf8mb4"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    SECRET_KEY: str = "code-adventurer-dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # 允许跨域的前端来源，逗号分隔；`*` 表示不限制（仅开发用）。
    # 生产必须写成实际域名，例如 https://learn.example.com
    CORS_ORIGINS: str = "*"

    # 是否允许「直通登录」（无需账号直接进入主账号）。
    # 本地开发方便；**公网部署必须关掉**，否则所有人共享同一个账号。
    ALLOW_GUEST_LOGIN: bool = True

    # 直通登录使用的主账号（仅 ALLOW_GUEST_LOGIN=True 时生效）。
    # 换身份就改这里，或在 .env 里覆盖 AUTO_LOGIN_USERNAME（.env 不入库）。
    # ⚠️ 改错名字不会报错，只会新建一个空白账号 —— 看起来就像「进度全没了」。
    AUTO_LOGIN_USERNAME: str = "如梦令"

    # 每日学习结算（lesson_daily_check.py）按**学号**认人。
    # 登录已经改成学号，username 列的旧名（如梦令）只是历史残留，不能当身份用。
    AUTO_LOGIN_STUDENT_ID: str = "20230614224"

    # AI（留空 = 离线演示模式）
    AI_BASE_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = ""
    AI_TIMEOUT: int = 30

    # 导师对话的历史记忆（滑动窗口 + 摘要压缩）
    # 只把「最近若干轮」原样发给模型，滑出窗口的旧轮次压成一段摘要拼进 system。
    # 预算按估算 token 算，不是按条数：一条贴了长代码的提问可能顶十轮闲聊。
    # 实测：提示词每多 1000 字，首字延迟约 +0.9s（2773 字→4.2s，6513 字→7.5s）。
    # 4000 已是「首响 < 10s」这条线内的上限：真实对话消息 50~150 字，够放十几轮。
    CHAT_HISTORY_TOKENS: int = 4000   # 原样发送的历史预算（中文 1 字≈1 token）
    CHAT_MAX_TURNS: int = 20          # 条数上限，防止一堆「嗯」「好的」把预算耗光
    CHAT_SUMMARY_CHARS: int = 400     # 摘要长度上限（汉字），太长会挤占 system
    CHAT_SUMMARY_MIN_MSGS: int = 4    # 滑出窗口不足这么多条就先不压，省调用

    # 代码沙箱
    # 公网长期运行时若担心沙箱逃逸，可设为 false 直接关闭「自由运行」入口
    # （课程判定用的内部 run_python 不受影响）。
    CODE_RUN_ENABLED: bool = True
    CODE_RUN_TIMEOUT: int = 5
    CODE_MAX_SIZE: int = 64 * 1024
    # 子进程内存上限（MB）。仅 Linux/macOS 生效，Windows 无 resource 模块。
    CODE_MAX_MEMORY_MB: int = 512
    # 单次执行允许写入磁盘的最大字节数（学生可能要练文件读写）
    CODE_MAX_FILE_BYTES: int = 8 * 1024 * 1024
    # 返回给前端的 stdout / stderr 截断长度，防止 print 炸弹撑爆响应
    CODE_MAX_OUTPUT: int = 20_000
    # 同时执行的沙箱子进程数上限。2C2G 机器上 MySQL 已占 ~400MB、uvicorn ~200MB，
    # 单个子进程最坏能吃满 CODE_MAX_MEMORY_MB，不限并发会被 OOM Killer 连 MySQL 一起杀掉。
    # 2 核下取 3：留 1 核给 Web 与数据库，内存峰值约 1.5GB，留出余量。
    CODE_MAX_CONCURRENCY: int = 3

    # 限流（公网部署的关键成本闸门，单位为「次 / 窗口」）
    CODE_RUN_PER_MINUTE: int = 12          # 同一用户每分钟可运行代码次数
    AI_CALL_PER_MINUTE: int = 15           # 同一用户每分钟可调用 AI 次数

    # 生产环境校验用：被判定为「未修改的默认密钥」
    INSECURE_SECRETS: tuple[str, ...] = (
        "code-adventurer-dev-secret-change-me",
        "change-me",
        "secret",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
