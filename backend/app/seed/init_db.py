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
    # 学号 + 姓名（2026-10-26 注册改为学号制）
    "users": [
        ("student_id", "VARCHAR(16) NOT NULL DEFAULT ''"),
        ("real_name", "VARCHAR(32) NOT NULL DEFAULT ''"),
    ],
}

# 已下线的种子数据：签到任务、代码币/连续签到成就。
# 种子函数只负责「缺了补上」，不会删旧行，所以这里显式清理一次。
_REMOVED_SEEDS = {
    "daily_tasks": ["signin"],
    "achievements": ["coin_500", "streak_3", "streak_7"],
}


def prune_seed_rows() -> None:
    """删掉界面上已经下线的任务/成就，避免「签到」「代码币」还挂在成就墙里。"""
    from ..database import SessionLocal
    from ..models import Achievement, DailyTask, UserAchievement, UserDailyTask

    db = SessionLocal()
    try:
        for code in _REMOVED_SEEDS["daily_tasks"]:
            db.query(UserDailyTask).filter(UserDailyTask.task_code == code).delete()
            db.query(DailyTask).filter(DailyTask.code == code).delete()
        for code in _REMOVED_SEEDS["achievements"]:
            db.query(UserAchievement).filter(
                UserAchievement.achievement_code == code).delete()
            db.query(Achievement).filter(Achievement.code == code).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[migrate] 清理旧种子失败：{e}")
    finally:
        db.close()


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
    if own:
        prune_seed_rows()


if __name__ == "__main__":
    seed_all()
    print("种子数据初始化完成")
