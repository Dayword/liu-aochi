"""Bug 猎人路由：挑战列表、详情、提交判定、排行。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BugChallenge, BugRound, User
from ..schemas import BugSubmitIn, BugSubmitOut
from ..security import get_current_user
from ..services import code_runner, growth

router = APIRouter(prefix="/api/bugs", tags=["bugs"])


@router.get("/challenges")
def challenges(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(BugChallenge).order_by(BugChallenge.difficulty, BugChallenge.id).all()
    done = {r.bug_code for r in db.query(BugRound).filter(BugRound.user_id == user.id).all()}
    return [{"code": c.code, "title": c.title, "description": c.description,
             "bug_type": c.bug_type, "difficulty": c.difficulty,
             "hint": c.hint, "language": c.language, "done": c.code in done} for c in rows]


@router.get("/challenges/{code}")
def challenge(code: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    c = db.query(BugChallenge).filter(BugChallenge.code == code).first()
    if not c:
        raise HTTPException(404, "挑战不存在")
    return {"code": c.code, "title": c.title, "description": c.description,
            "bug_type": c.bug_type, "difficulty": c.difficulty, "language": c.language,
            "buggy_code": c.buggy_code, "hint": c.hint,
            "test_cases_preview": c.test_cases[:2]}


@router.post("/submit", response_model=BugSubmitOut)
def submit(body: BugSubmitIn, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    if not user.character:
        raise HTTPException(400, "请先创建角色")
    c = db.query(BugChallenge).filter(BugChallenge.code == body.bug_code).first()
    if not c:
        raise HTTPException(404, "挑战不存在")

    result = code_runner.judge_bug_fix(body.code, c.test_cases)
    if result.get("err"):
        raise HTTPException(400, result["err"])

    accuracy, speed_ms, quality = result["accuracy"], result["speed_ms"], result["quality"]
    score = int(accuracy * 2 + quality * 0.8 + max(0, 30 - speed_ms / 100))
    passed = accuracy >= 100
    exp_gain = c.base_exp if passed else int(c.base_exp * accuracy / 200)
    coin_gain = c.base_coins if passed else int(c.base_coins * accuracy / 200)

    char = user.character
    char.total_bugs += 1
    growth.add_exp(db, char, exp_gain)
    growth.add_coins(db, char, coin_gain)
    db.add(BugRound(user_id=user.id, bug_code=c.code, difficulty=c.difficulty,
                    submitted_code=body.code, accuracy=accuracy, speed_ms=speed_ms,
                    quality=quality, score=score, tests_passed=result["passed"],
                    tests_total=result["total"]))
    db.commit()
    new_ach = growth.check_achievements(db, user)
    growth.rebuild_leaderboard(db, user)

    explanation = (c.explanation if passed else
                   f"尚未完全修复：{result['passed']}/{result['total']} 组测试通过。"
                   f"提示：{c.hint}")
    return BugSubmitOut(score=score, accuracy=accuracy, speed_ms=speed_ms,
                        quality=quality, tests_passed=result["passed"],
                        tests_total=result["total"], passed=passed,
                        results=result["results"], explanation=explanation,
                        exp_gained=exp_gain, coins_gained=coin_gain,
                        new_achievements=[{"code": a.code, "name": a.name, "icon": a.icon}
                                          for a in new_ach])


@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(BugRound).order_by(BugRound.score.desc()).limit(20).all()
    out = []
    seen = set()
    for r in rows:
        u = db.get(User, r.user_id)
        if u and u.character and r.user_id not in seen:
            seen.add(r.user_id)
            out.append({"rank": len(out) + 1, "nickname": u.nickname or u.username,
                        "character_name": u.character.name,
                        "bug_code": r.bug_code, "score": r.score,
                        "accuracy": r.accuracy})
    return out
