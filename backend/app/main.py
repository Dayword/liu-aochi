"""FastAPI 应用入口。"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import (auth, bug_hunter, chat, code, games, growth, interview,
                      interview_guide, learn, levels, quests, user)


def _warnings() -> list[str]:
    """生产环境配置自检：只告警不阻塞启动，避免一个疏忽让整站起不来。"""
    if settings.ENV.lower() != "prod":
        return []
    problems: list[str] = []
    if settings.SECRET_KEY in settings.INSECURE_SECRETS or len(settings.SECRET_KEY) < 32:
        problems.append("SECRET_KEY 仍是默认值或过短，任何人都能伪造登录态，请改成 32 位以上随机串")
    if settings.ALLOW_GUEST_LOGIN:
        problems.append("ALLOW_GUEST_LOGIN 仍为 true，所有人会共享同一账号，请设为 false")
    if settings.CORS_ORIGINS.strip() == "*":
        problems.append("CORS_ORIGINS 为 *，建议改成实际域名")
    return problems


async def _warm_up_ai() -> None:
    """启动时预热 AI 连接：否则首个用户请求要额外付 DNS + TLS 握手的时间。"""
    try:
        from .ai.client import llm_chat
        await llm_chat([{"role": "user", "content": "hi"}], temperature=0, max_tokens=1)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        from .seed.init_db import seed_all
        seed_all()
    except Exception as e:  # 种子失败不阻塞启动
        print(f"[seed] warning: {e}")
    for w in _warnings():
        print(f"[config] ⚠️ 生产配置风险：{w}")
    asyncio.create_task(_warm_up_ai())
    yield


app = FastAPI(title="码境 CodeRealm · 软件工程游戏化 AI 问答系统", version="0.2.0",
              lifespan=lifespan)

_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    # 用通配符时浏览器禁止携带 cookie（这里认证走 Bearer Token，不受影响）
    allow_credentials="*" not in _origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(levels.router)
app.include_router(quests.router)
app.include_router(chat.router)
app.include_router(interview.router)
app.include_router(interview_guide.router)
app.include_router(bug_hunter.router)
app.include_router(code.router)
app.include_router(growth.router)
app.include_router(games.router)
app.include_router(learn.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "code-adventurer", "env": settings.ENV,
            "ai_enabled": _ai_flag(),
            "guest_login": settings.ALLOW_GUEST_LOGIN,
            "code_run": settings.CODE_RUN_ENABLED,
            "config_warnings": _warnings()}


def _ai_flag():
    try:
        from .ai.client import ai_enabled
        return ai_enabled()
    except Exception:
        return False


@app.get("/")
def root():
    return {"name": "码境 CodeRealm API", "docs": "/docs"}
