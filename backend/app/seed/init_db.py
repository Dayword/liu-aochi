"""种子数据初始化入口。"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import SessionLocal, engine
from . import bank, bugs_interviews, data, questions

# 新增字段时在这里登记：create_all 只会「建表」，不会给已存在的表加列。
_ADDED_COLUMNS = {
    "learn_progress": [
        ("code_passed", "TINYINT(1) NOT NULL DEFAULT 0"),
        ("quiz_json", "JSON NULL"),
    ],
}


def ensure_columns() -> None:
    """轻量补列，避免新增字段后旧库报 Unknown column。"""
    if engine.dialect.name != "mysql":
        return
    with engine.begin() as conn:
        for table, cols in _ADDED_COLUMNS.items():
            exists = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = :t"), {"t": table}).scalar()
            if not exists:
                continue  # 表还不存在，交给 create_all
            have = {r[0] for r in conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = :t"), {"t": table})}
            for name, ddl in cols:
                if name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    print(f"[migrate] 已补充字段 {table}.{name}")


def seed_all(db: Session | None = None) -> None:
    try:
        ensure_columns()
    except Exception as e:  # 补列失败不阻塞启动
        print(f"[migrate] warning: {e}")
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
