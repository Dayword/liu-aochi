"""专注（番茄钟）记录：只记时长，不发经验、不改学习进度。"""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FocusSession, User
from ..security import get_current_user

router = APIRouter(prefix="/api/focus", tags=["focus"])


class FocusLogIn(BaseModel):
    minutes: int = Field(ge=1, le=180)
    started_at: str | None = None


def _day_start(d: date) -> datetime:
    return datetime.combine(d, time.min)


@router.post("/log")
def log(body: FocusLogIn, db: Session = Depends(get_db),
        user: User = Depends(get_current_user)):
    """记一次专注。分钟数卡在 1~180：前端算错也不会写进一个负数或 10 小时。"""
    # 全站用的是本地时间（models.now = datetime.now()），这里必须一致：
    # 前端传的是 ISO/UTC，转成本地再去掉时区，否则凌晨 1 点会被算到前一天。
    started = datetime.now()
    if body.started_at:
        try:
            dt = datetime.fromisoformat(body.started_at.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone().replace(tzinfo=None)
            started = dt
        except ValueError:
            raise HTTPException(400, "started_at 格式不对")
    row = FocusSession(user_id=user.id, minutes=body.minutes, started_at=started)
    db.add(row)
    db.commit()
    return {"ok": True, "minutes": body.minutes}


@router.get("/stats")
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    week_start = today - timedelta(days=6)

    today_min = db.query(func.coalesce(func.sum(FocusSession.minutes), 0)).filter(
        FocusSession.user_id == user.id,
        FocusSession.started_at >= _day_start(today)).scalar() or 0

    week_min = db.query(func.coalesce(func.sum(FocusSession.minutes), 0)).filter(
        FocusSession.user_id == user.id,
        FocusSession.started_at >= _day_start(week_start)).scalar() or 0

    total_min = db.query(func.coalesce(func.sum(FocusSession.minutes), 0)).filter(
        FocusSession.user_id == user.id).scalar() or 0

    # 连续专注天数：从今天往回数，某天有记录就 +1，断一天就停
    day_rows = db.query(func.date(FocusSession.started_at)).filter(
        FocusSession.user_id == user.id).group_by(
        func.date(FocusSession.started_at)).all()
    days = {str(r[0]) for r in day_rows}
    streak = 0
    cursor = today
    if str(cursor) not in days:
        # 今天还没专注不算断：从昨天开始数，避免早上打开就显示 0
        cursor = today - timedelta(days=1)
    while str(cursor) in days:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "today": int(today_min),
        "week": int(week_min),
        "total": int(total_min),
        "streak": streak,
    }
