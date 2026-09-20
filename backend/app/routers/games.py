"""消消乐闯关路由：关卡配置、失败后的知识问答、通关结算。

失败流程（前端驱动）：
    步数用尽且未达目标 → 拉一道该关卡学科的知识题
    答对 → 奖励步数继续；答错 → 扣一颗生命值
"""
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import client as ai
from ..database import get_db
from ..models import Level, Question, User, UserLevelProgress, now
from ..schemas import (Match3AnswerIn, Match3AnswerOut, Match3CompleteIn,
                       Match3CompleteOut, Match3QuestionOut, Match3StartIn,
                       Match3StartOut)
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/games/match3", tags=["games"])

ROWS, COLS, GEM_TYPES = 8, 8, 6


def _level_config(level: Level) -> tuple[int, int]:
    """按难度给出步数与目标分。

    步数与目标分是用模拟对局校准过的：8x8 盘面随机乱打时，
    30 步中位数约 2250 分、20 步约 1460 分，因此目标定在中位数附近偏上，
    随便点不易过、动点脑子能过。
    """
    d = max(1, min(5, level.difficulty))
    moves = 32 - 2 * d
    target = round((1300 + 240 * d) / 50) * 50
    return moves, target


def _get_level(db: Session, code: str) -> Level:
    level = db.query(Level).filter(Level.code == code).first()
    if not level:
        raise HTTPException(404, "关卡不存在")
    return level


@router.post("/start", response_model=Match3StartOut)
def start(body: Match3StartIn, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    if not user.character or not user.character.onboarding_done:
        raise HTTPException(400, "请先完成新手引导")
    level = _get_level(db, body.level_code)
    moves, target = _level_config(level)
    return Match3StartOut(level_code=level.code, name=level.name,
                          subject=level.subject, difficulty=level.difficulty,
                          rows=ROWS, cols=COLS, gem_types=GEM_TYPES,
                          moves=moves, target_score=target)


def _bank_question(db: Session, level: Level) -> Question | None:
    """题库兜底：按学科相关度取候选，再随机，避免每次都是同一道。"""
    pool = db.query(Question).filter(Question.type == "choice").all()
    if not pool:
        return None
    ranked = ai._rank_by_relevance(
        pool, f"{level.subject} {' '.join(level.tags or [])}", limit=10)
    return random.choice(ranked) if ranked else random.choice(pool)


@router.get("/question", response_model=Match3QuestionOut)
async def question(level_code: str, fast: bool = False,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """出一道与关卡学科相关的单选题。

    AI 实时生成优先（答题场景质量更高），生成失败则题库兜底。
    fast=true 时跳过 AI 直接走题库 —— 前端在「预取还没回来」时用它换即时响应，
    不让玩家盯着加载动画等模型思考。
    """
    level = _get_level(db, level_code)

    row = None
    if not fast:
        recent = [r[0] for r in db.query(Question.stem).filter(
            Question.source == "ai").order_by(Question.id.desc()).limit(8).all()]
        try:
            gen = await ai.ai_generate_question(
                db, level.tags or [level.subject or "软件工程"], level.difficulty, [],
                avoid=recent)
        except Exception:
            gen = None
        if gen and gen.get("stem") and len(gen.get("options") or []) >= 3:
            row = Question(type="choice", subject=level.subject or gen.get("subject", "综合"),
                           tags=gen.get("tags") or level.tags or [], difficulty=level.difficulty,
                           stem=gen["stem"], options=gen["options"], answer=gen["answer"],
                           explanation=gen.get("explanation", ""),
                           knowledge_point=gen.get("knowledge_point", ""), source="ai")
            db.add(row)
            db.commit()
            db.refresh(row)

    if row is None:
        row = _bank_question(db, level)
    if row is None:
        raise HTTPException(500, "题库暂不可用，请稍后再试")

    return Match3QuestionOut(question_id=row.id, stem=row.stem,
                             options=ai.strip_option_prefix(row.options or []),
                             subject=row.subject, source=row.source)


@router.post("/answer", response_model=Match3AnswerOut)
def answer(body: Match3AnswerIn, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    q = db.get(Question, body.question_id)
    if not q:
        raise HTTPException(404, "题目不存在")
    correct_index = (q.answer or {}).get("correct_index")
    if not isinstance(correct_index, int):
        raise HTTPException(500, "该题目缺少标准答案")
    return Match3AnswerOut(correct=body.answer_index == correct_index,
                           correct_index=correct_index,
                           explanation=q.explanation or "")


@router.post("/complete", response_model=Match3CompleteOut)
def complete(body: Match3CompleteIn, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    """结算：达标则标记通关、发奖励、解锁下一关。"""
    level = _get_level(db, body.level_code)
    _, target = _level_config(level)
    char = user.character
    if not char:
        raise HTTPException(400, "请先创建角色")

    progress = db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.level_code == level.code).first()
    if progress is None:
        progress = UserLevelProgress(user_id=user.id, level_code=level.code)
        db.add(progress)
    progress.attempts += 1

    exp_gain = coins_gain = 0
    unlocked_next = None
    completed = body.score >= target

    if completed:
        progress.status = "completed"
        progress.completed_at = now()
        # best_score 在关卡地图上按 x/10 展示，这里换算成同一量纲
        progress.best_score = max(progress.best_score,
                                  min(10, round(body.score / target * 10)))
        exp_gain = level.base_exp
        coins_gain = level.base_coins
        if body.score >= target * 1.5:      # 大幅超额额外奖励
            exp_gain += 30
            coins_gain += 10
        char.total_quests += 1
        growth.report_daily_event(db, user, "quest_pass")
        growth.unlock_levels(db, user)
        newly = db.query(UserLevelProgress).filter(
            UserLevelProgress.user_id == user.id,
            UserLevelProgress.status == "unlocked").order_by(
            UserLevelProgress.id.desc()).first()
        if newly and newly.level_code != level.code:
            unlocked_next = newly.level_code
    else:
        # 已经通关过的关卡，重玩失败不能把通关状态打回去
        if progress.status != "completed":
            progress.status = "unlocked"

    growth.add_exp(db, char, exp_gain)
    growth.add_coins(db, char, coins_gain)
    growth.check_achievements(db, user)
    db.commit()
    return Match3CompleteOut(completed=completed, exp_gained=exp_gain,
                             coins_gained=coins_gain, unlocked_next=unlocked_next)
