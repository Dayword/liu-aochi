"""AI 导师对话路由（SSE 流式：把模型思考过程与正文实时推给前端）。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import ChatMessage, ChatSession, User
from ..schemas import ChatIn
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/chat", tags=["chat"])

MENTORS = ["老架构师", "大厂面试官", "学霸学长", "Python 全栈导师", "测试大师", "运维骑士长"]


@router.get("/mentors")
def mentors():
    return MENTORS


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def stream(body: ChatIn, db: Session = Depends(get_db),
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

    history: list[dict] = []
    if body.session_id:
        session = db.get(ChatSession, body.session_id)
        if session is None or session.user_id != user.id:
            raise HTTPException(404, "会话不存在")
        history = [{"role": m.role, "content": m.content} for m in db.query(ChatMessage).filter(
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


async def _chat_events(user_id: int, session_id: int, mentor: str,
                       history: list[dict], message: str):
    """流式生成器。这里单独开一个 Session：StreamingResponse 的生成器在依赖清理之后才跑。"""
    from ..ai import client as ai

    mark = ai.QUIZ_MARK
    db = SessionLocal()
    reply_text, quiz, summary = "", [], ""
    try:
        buf, emitted, sep_seen = "", 0, False
        try:
            messages = ai.build_chat_messages(
                db, mentor, message, history,
                avoid=ai.recent_quiz_stems(db, user_id, 12))
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
        except Exception:
            if not buf:
                # 模型不可用/超时 → 整体降级为内置讲解
                reply_text = ai.fallback_reply(db, mentor, message)
                buf = reply_text
                yield _sse({"type": "reply", "text": reply_text})

        reply_text, quiz, summary = ai.split_reply(buf)
        if not reply_text:
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
            growth.add_exp(db, user.character, 5)
            growth.add_coins(db, user.character, 2)
            growth.report_daily_event(db, user, "chat")
            new_ach = growth.check_achievements(db, user)
            exp_gained = 5 + sum(a.exp_reward for a in new_ach)
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
