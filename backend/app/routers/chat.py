"""AI 导师对话路由（SSE 流式：把模型思考过程与正文实时推给前端）。"""
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal, get_db
from ..models import ChatMessage, ChatSession, User
from ..schemas import ChatIn
from ..security import get_current_user
from ..services import growth
from ..services.rate_limit import SlidingWindowLimiter, enforce

router = APIRouter(prefix="/api/chat", tags=["chat"])

_chat_limiter = SlidingWindowLimiter(settings.AI_CALL_PER_MINUTE, 60, "AI 对话")

# 后台摘要任务：必须留强引用，否则 asyncio 只持有弱引用时任务可能被 GC 掉
_BG_TASKS: set[asyncio.Task] = set()

MENTORS = ["老架构师", "大厂面试官", "学霸学长", "Python 全栈导师", "测试大师", "运维骑士长"]


@router.get("/mentors")
def mentors():
    return MENTORS


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def stream(body: ChatIn, request: Request, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    """流式对话。事件类型：
    - {"type":"reasoning","text":...}  模型思考过程增量
    - {"type":"reply","text":...}      正文增量（题目 JSON 之前的部分）
    - {"type":"done", ...}             收尾：题目、知识点总结、经验值
    - {"type":"error","message":...}   异常
    """
    if not user.character:
        raise HTTPException(400, "请先创建角色")
    if body.mentor not in MENTORS:
        raise HTTPException(400, "未知导师")
    if not body.message.strip():
        raise HTTPException(400, "消息不能为空")
    # 公网开放后 AI 调用是唯一的持续花钱入口，必须限流
    enforce(_chat_limiter, request, user.id)

    history: list[dict] = []
    if body.session_id:
        session = db.get(ChatSession, body.session_id)
        if session is None or session.user_id != user.id:
            raise HTTPException(404, "会话不存在")
        # 带上 id：摘要要记住「压到哪一条了」，只靠内容比对会在重复提问时错位
        history = [{"id": m.id, "role": m.role, "content": m.content}
                   for m in db.query(ChatMessage).filter(
                       ChatMessage.session_id == session.id).order_by(ChatMessage.id).all()]
    else:
        session = ChatSession(user_id=user.id, mentor=body.mentor)
        db.add(session)
        db.commit()

    return StreamingResponse(
        _chat_events(user.id, session.id, body.mentor, history, body.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive",
                 "X-Accel-Buffering": "no"},
    )


async def _refresh_summary(session_id: int, fresh: list[dict]) -> None:
    """把滑出窗口的旧轮次压进 session.summary（后台任务）。

    放在首字之前会把「首响 ~6s」拖成 ~10s，所以一律丢后台：
    这一次对话用不上它没关系，下一轮读到的就是新摘要。
    自己开 Session、自己 commit，失败只回滚自己，绝不影响主对话。
    """
    from ..ai import client as ai

    db = SessionLocal()
    try:
        sess = db.get(ChatSession, session_id)
        if sess is None:
            return
        text = await ai.summarize_history(sess.summary or "", fresh)
        if not text:
            return
        sess.summary = text
        sess.summary_upto_id = max(m.get("id", 0) for m in fresh)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


async def _chat_events(user_id: int, session_id: int, mentor: str,
                       history: list[dict], message: str):
    """流式生成器。这里单独开一个 Session：StreamingResponse 的生成器在依赖清理之后才跑。"""
    from ..ai import client as ai

    mark = ai.QUIZ_MARK
    db = SessionLocal()
    reply_text, quiz, summary = "", [], ""
    try:
        # 历史按 token 预算成轮取舍：窗口内的原样发，窗口外的进摘要
        sess = db.get(ChatSession, session_id)
        kept, dropped = ai.split_history(history)
        long_summary = (sess.summary or "") if sess else ""
        if dropped:
            upto = (sess.summary_upto_id or 0) if sess else 0
            fresh = [m for m in dropped if m.get("id", 0) > upto]
            if len(fresh) >= settings.CHAT_SUMMARY_MIN_MSGS:
                task = asyncio.create_task(_refresh_summary(session_id, fresh))
                # 必须留引用：局部变量一丢，任务可能被 GC 掉
                _BG_TASKS.add(task)
                task.add_done_callback(_BG_TASKS.discard)

        buf, emitted, sep_seen = "", 0, False
        messages: list[dict] = []
        try:
            messages = ai.build_chat_messages(
                db, mentor, message, kept,
                avoid=ai.recent_quiz_stems(db, user_id, 12), summary=long_summary,
                gap=bool(dropped) and not long_summary)
            async for kind, text in ai.stream_llm(messages):
                if kind == "reasoning":
                    yield _sse({"type": "reasoning", "text": text})
                    continue
                buf += text
                if sep_seen:
                    continue
                idx = buf.find(mark)
                if idx >= 0:
                    sep_seen = True
                    if idx > emitted:
                        yield _sse({"type": "reply", "text": buf[emitted:idx]})
                        emitted = idx
                else:
                    # 留出分隔符长度，避免分隔符被切在两个 chunk 中间时被误当成正文发出去
                    safe = max(emitted, len(buf) - (len(mark) - 1))
                    if safe > emitted:
                        yield _sse({"type": "reply", "text": buf[emitted:safe]})
                        emitted = safe
            if not sep_seen and emitted < len(buf):
                yield _sse({"type": "reply", "text": buf[emitted:]})
        except Exception as e:
            # 必须打日志：这个 except 一旦静默，线上就成了「模型挂了但用户看到一段
            # 跑题的内置讲解」，冒烟全绿也发现不了（踩过，问「我叫什么」答「TCP 三次握手」）。
            print(f"[chat] 模型调用失败 user={user_id} session={session_id} "
                  f"prompt={sum(len(m.get('content') or '') for m in messages)}字 "
                  f"{type(e).__name__}: {str(e)[:200]}", flush=True)
            if not buf:
                # 模型不可用/超时 → 整体降级为内置讲解
                reply_text = ai.fallback_reply(db, mentor, message)
                buf = reply_text
                yield _sse({"type": "reply", "text": reply_text})

        reply_text, quiz, summary = ai.split_reply(buf)
        if not reply_text:
            # 另一条静默兜底路径：模型只吐了题目 JSON、没吐正文。同样要留痕。
            print(f"[chat] 正文为空，改用内置讲解 user={user_id} session={session_id} "
                  f"buf={len(buf)}字", flush=True)
            reply_text = ai.fallback_reply(db, mentor, message)
            yield _sse({"type": "reply", "text": reply_text})
        if len(quiz) < 2:
            quiz = ai.pick_bank_quiz(db, reply_text, user_id)

        # 落库 + 成长
        db.add(ChatMessage(session_id=session_id, role="user", content=message))
        db.add(ChatMessage(session_id=session_id, role="assistant", content=reply_text))
        user = db.get(User, user_id)
        exp_gained = 0
        if user and user.character:
            user.character.total_chats += 1
            # 经验只来自完成课时（services/growth.py 文件头），对话不发经验
            growth.report_daily_event(db, user, "chat")
            new_ach = growth.check_achievements(db, user)
            exp_gained = 0
        ai.remember_quiz(db, user_id, quiz)
        db.commit()
        if user:
            growth.rebuild_leaderboard(db, user)
        yield _sse({"type": "done", "session_id": session_id, "summary": summary,
                    "quiz": quiz, "exp_gained": exp_gained})
    except Exception as e:  # 兜底，别让流静默断掉
        yield _sse({"type": "error", "message": str(e)[:120]})
    finally:
        db.close()


@router.get("/history/{session_id}")
def history(session_id: int, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "会话不存在")
    return {"session_id": session.id, "mentor": session.mentor,
            "messages": [{"role": m.role, "content": m.content} for m in db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id).order_by(ChatMessage.id).all()]}


@router.get("/sessions")
def sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(
        ChatSession.id.desc()).limit(20).all()
    return [{"id": s.id, "mentor": s.mentor,
             "created_at": s.created_at.strftime("%m-%d %H:%M")} for s in rows]
