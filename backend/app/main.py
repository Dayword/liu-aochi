"""FastAPI 应用入口。"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import (auth, bug_hunter, chat, code, games, growth, interview,
                      learn, levels, quests, user)


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
    asyncio.create_task(_warm_up_ai())
    yield


app = FastAPI(title="代码冒险者 · 软件工程游戏化 AI 问答系统", version="0.1.0",
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(levels.router)
app.include_router(quests.router)
app.include_router(chat.router)
app.include_router(interview.router)
app.include_router(bug_hunter.router)
app.include_router(code.router)
app.include_router(growth.router)
app.include_router(games.router)
app.include_router(learn.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "code-adventurer", "ai_enabled": _ai_flag()}


def _ai_flag():
    try:
        from .ai.client import ai_enabled
        return ai_enabled()
    except Exception:
        return False


@app.get("/")
def root():
    return {"name": "代码冒险者 API", "docs": "/docs"}
