"""关卡地图路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Level, User, UserLevelProgress
from ..security import get_current_user
from ..services import growth

router = APIRouter(prefix="/api/levels", tags=["levels"])


@router.get("/map")
def level_map(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.character:
        return {"scenes": [], "levels": []}
    growth.unlock_levels(db, user)
    levels = db.query(Level).order_by(Level.order_no).all()
    progress = {p.level_code: p for p in db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id).all()}
    scenes: dict[str, dict] = {}
    out = []
    for lv in levels:
        prog = progress.get(lv.code)
        status = prog.status if prog else "locked"
        completed = status == "completed"
        out.append({"code": lv.code, "name": lv.name, "scene": lv.scene,
                    "description": lv.description, "difficulty": lv.difficulty,
                    "order_no": lv.order_no, "unlock_prev": lv.unlock_prev,
                    "subject": lv.subject, "tags": lv.tags or [],
                    "recommended_class": lv.recommended_class,
                    "base_exp": lv.base_exp, "base_coins": lv.base_coins,
                    "hp": lv.hp, "icon": lv.icon, "status": status,
                    "best_score": prog.best_score if prog else 0,
                    "attempts": prog.attempts if prog else 0,
                    "completed": completed})
        scenes.setdefault(lv.scene, {"name": lv.scene, "icon": lv.icon,
                                     "level_count": 0, "completed_count": 0})
        scenes[lv.scene]["level_count"] += 1
        if completed:
            scenes[lv.scene]["completed_count"] += 1
    return {"scenes": list(scenes.values()), "levels": out}
