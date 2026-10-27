"""按新经验规则重算全站经验（2026-10-27）。

规则：**每完成一个课时 = 10 点经验，其它来源一律不计**。
（闯关答题、关卡通关、成就、每日任务、Bug 猎人、面试在改动后都已不再发经验，
 这个脚本负责把改动之前攒下的经验也拉回同一口径。）

顺带做一次老数据归一：
- `user_level_progress.best_score` 从「10 分制得分」改成「星级 0~3」；
- `characters.weekly_exp` 不超过 total_exp，避免周榜出现比总经验还大的数；
- **成就补发**：成就种子换成 8 家族 × 铜/银/金 之后，老用户早就满足条件，
  但 `check_achievements` 只在答题/学习事件里触发，不补一次会一直显示「目标 N」。

用法：
    cd backend
    python migrate_exp.py --dry-run     # 只看会改成什么样，不落库
    python migrate_exp.py               # 真正执行
"""
import sys

from sqlalchemy import func

from app.database import SessionLocal
from app.models import (Achievement, Character, LearnProgress, User,
                        UserAchievement, UserLevelProgress)
from app.services import growth


def _pending_achievements(db, user) -> list[Achievement]:
    """该用户已经达标但还没发记录的成就（check_achievements 的只读版）。"""
    got = {ua.achievement_code for ua in db.query(UserAchievement).filter(
        UserAchievement.user_id == user.id).all()}
    triggers = growth._ach_trigger_type(db, user)  # noqa: SLF001
    out = []
    for ach in db.query(Achievement).all():
        if ach.code in got:
            continue
        value = triggers.get(ach.condition_type)
        if value is not None and value >= ach.condition_value:
            out.append(ach)
    return out


def main(dry_run: bool = False) -> None:
    db = SessionLocal()
    try:
        done = dict(db.query(LearnProgress.user_id,
                             func.count(LearnProgress.id))
                    .filter(LearnProgress.status == "completed")
                    .group_by(LearnProgress.user_id).all())

        changed = 0
        print(f"{'学号/账号':<16}{'课时':>5}{'旧等级':>7}{'新等级':>7}{'旧总经验':>9}{'新总经验':>9}")
        for char in db.query(Character).all():
            user = db.query(User).filter(User.id == char.user_id).first()
            if user is None:
                continue
            lessons = int(done.get(user.id, 0))
            total = lessons * growth.LESSON_EXP
            level, exp = growth.level_of_total_exp(total)
            if (char.total_exp, char.level, char.exp) == (total, level, exp):
                continue
            changed += 1
            who = user.student_id or user.username
            print(f"{who:<16}{lessons:>5}{char.level:>7}{level:>7}"
                  f"{char.total_exp:>9}{total:>9}")
            char.total_exp = total
            char.level = level
            char.exp = exp
            char.weekly_exp = min(char.weekly_exp or 0, total)

        # 星级归一：旧数据里 best_score 是 10 分制得分
        fixed = 0
        for prog in db.query(UserLevelProgress).all():
            if (prog.best_score or 0) > 3:
                old = prog.best_score
                if prog.status == "completed":
                    prog.best_score = max(1, min(3, round(old / 10 * 3)))
                else:
                    prog.best_score = 0
                fixed += 1
                if fixed <= 5:
                    print(f"  星级归一 {prog.level_code}: {old} → {prog.best_score}")

        # 成就补发（只补不删；已发出的不会重复发）
        granted = 0
        for user in db.query(User).all():
            if user.character is None:
                continue
            pending = _pending_achievements(db, user)
            if not pending:
                continue
            if granted < 8:
                names = "、".join(a.name for a in pending[:4])
                print(f"  成就补发 {user.student_id or user.username}: {names}")
            granted += len(pending)
            if not dry_run:
                for ach in pending:
                    db.add(UserAchievement(user_id=user.id,
                                           achievement_code=ach.code))

        if dry_run:
            db.rollback()
            print(f"\n[dry-run] 将调整 {changed} 个账号、{fixed} 条关卡星级、"
                  f"补发 {granted} 个成就，未写库")
        else:
            db.commit()
            print(f"\n✅ 已调整 {changed} 个账号、{fixed} 条关卡星级、"
                  f"补发 {granted} 个成就")
    finally:
        db.close()


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
