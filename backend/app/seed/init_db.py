"""种子数据初始化入口。"""
from sqlalchemy.orm import Session

from ..database import SessionLocal
from . import bank, bugs_interviews, data, questions


def seed_all(db: Session | None = None) -> None:
    own = db is None
    if own:
        db = SessionLocal()
    try:
        data.seed_levels(db)
        data.seed_achievements(db)
        data.seed_daily_tasks(db)
        data.seed_knowledge(db)
        questions.seed_questions(db)
        bugs_interviews.seed_bugs(db)
        bugs_interviews.seed_interviews(db)
        bank.seed_bank(db)
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    seed_all()
    print("种子数据初始化完成")
