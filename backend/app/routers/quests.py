"""闯关路由：开始、取题、答题、复活、结算、错题重刷。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Level, Question, User, WrongAnswer
from ..schemas import (AnswerIn, AnswerOut, QuestQuestionOut, QuestStartIn,
                       QuestStartOut, SettlementOut)
from ..security import get_current_user
from ..services import quest

router = APIRouter(prefix="/api/quests", tags=["quests"])


@router.post("/start", response_model=QuestStartOut)
def start(body: QuestStartIn, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    if not user.character or not user.character.onboarding_done:
        raise HTTPException(400, "请先完成新手引导")
    level = db.query(Level).filter(Level.code == body.level_code).first()
    if not level:
        raise HTTPException(404, "关卡不存在")
    if body.mode == "wrong_review":
        wrong_ids = [w.question_id for w in db.query(WrongAnswer).filter(
            WrongAnswer.user_id == user.id, WrongAnswer.resolved.is_(False)).all()]
        if not wrong_ids:
            raise HTTPException(400, "错题本是空的，先去闯关攒错题吧")
    else:
        wrong_ids = None
    try:
        run = quest.start_run(db, user, level, body.mode, wrong_ids)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return QuestStartOut(**run)


@router.get("/question/{run_id}", response_model=QuestQuestionOut)
def question(run_id: str, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    q = quest.current_question(db, run_id)
    if q is None:
        run = quest.RUNS.get(run_id)
        if run and run["user_id"] == user.id and run["index"] >= len(run["qids"]):
            raise HTTPException(409, "闯关已答完，请结算")
        raise HTTPException(404, "闯关会话不存在")
    return QuestQuestionOut(**q)


@router.post("/answer", response_model=AnswerOut)
async def answer(body: AnswerIn, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    try:
        result = quest.answer_question(db, user, body.run_id, body.question_id, body.answer)
    except ValueError as e:
        raise HTTPException(400, str(e))
    # 答错时异步补 AI 解析（失败静默，用内置解析）
    if not result["correct"] and result["explanation"]:
        try:
            from ..ai import client as ai
            q = db.get(Question, body.question_id)
            if q:
                result["ai_analysis"] = await ai.wrong_answer_analysis(
                    db, {"type": q.type, "stem": q.stem, "explanation": q.explanation,
                         "expected": (q.answer or {}).get("answer", "")}, body.answer)
        except Exception:
            pass
    return AnswerOut(**result)


@router.post("/settle", response_model=SettlementOut)
def settle(run_id: str, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    try:
        return SettlementOut(**quest.settle(db, user, run_id))
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/revive")
def revive(run_id: str, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    try:
        return quest.revive(db, user, run_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
