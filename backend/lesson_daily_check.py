"""每日学习进度检查（口径：引导式学习里带绿色对勾的课 = 已完成）。

判定依据是 `learn_progress.completed_at` —— 也就是界面上打勾那一节真正被判定通过的
时刻，不是"我打算写几课"，也不看 git 提交。

用法：
    cd backend
    python lesson_daily_check.py            # 输出今天的结算
    python lesson_daily_check.py --days 7   # 顺便打印最近 7 天明细

脚本**只读数据库，不写任何状态文件**，所以重复运行不会污染数据，也不会出现
"重跑一次就算 0 课" 这类假数据。
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import date, datetime, time, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import LearnProgress, User  # noqa: E402
from app.routers.learn import _statuses  # noqa: E402
from app.seed.learn import CURRICULUM  # noqa: E402

GOAL_MIN = 10
GOAL_MAX = 15


def day_range(d: date) -> tuple[datetime, datetime]:
    return datetime.combine(d, time.min), datetime.combine(d + timedelta(days=1), time.min)


def main() -> int:
    show_days = 7
    if "--days" in sys.argv:
        try:
            show_days = max(1, int(sys.argv[sys.argv.index("--days") + 1]))
        except (IndexError, ValueError):
            pass

    today = date.today()
    yesterday = today - timedelta(days=1)

    # 身份以**学号**为准（登录早改成学号了），username 列里的旧名只作老账号兜底。
    keys = [settings.AUTO_LOGIN_STUDENT_ID, settings.AUTO_LOGIN_USERNAME]
    for i, a in enumerate(sys.argv):
        if a in ("--student", "--user") and i + 1 < len(sys.argv):
            keys.insert(0, sys.argv[i + 1])

    db = SessionLocal()
    try:
        user = None
        for k in keys:
            if not k:
                continue
            user = (db.query(User).filter(User.student_id == k).first()
                    or db.query(User).filter(User.username == k).first())
            if user is not None:
                break
        if user is None:
            print(f"❌ 找不到主账号（学号 {settings.AUTO_LOGIN_STUDENT_ID}"
                  f" / 用户名 {settings.AUTO_LOGIN_USERNAME}），无法统计。")
            print("   检查 .env / app/config.py 的 AUTO_LOGIN_STUDENT_ID 是否被改过。")
            return 2

        rows = db.query(LearnProgress).filter(LearnProgress.user_id == user.id).all()
        statuses = _statuses(db, user)
    except Exception as exc:  # noqa: BLE001 - 数据库连不上要报警，绝不能当成 0 课
        print(f"❌ 读取学习进度失败：{type(exc).__name__}: {exc}")
        print("   数据库没起 / 连不上时不能当作「今天 0 课」，请先确认 MySQL 在运行。")
        return 2
    finally:
        db.close()

    total_lessons = len(CURRICULUM)
    done = {r.point_code: r for r in rows if r.status == "completed"}
    completed_total = len(done)

    # 每天完成了几节
    per_day: Counter[str] = Counter()
    for r in done.values():
        if r.completed_at:
            per_day[r.completed_at.date().isoformat()] += 1

    today_n = per_day.get(today.isoformat(), 0)
    yest_n = per_day.get(yesterday.isoformat(), 0)

    # 连续达标：今天达标就从今天往前数，否则从昨天往前数
    streak = 0
    cursor = today if today_n >= GOAL_MIN else yesterday
    while per_day.get(cursor.isoformat(), 0) >= GOAL_MIN:
        streak += 1
        cursor -= timedelta(days=1)

    if today_n >= GOAL_MAX:
        verdict, label = "over", "超额达标"
    elif today_n >= GOAL_MIN:
        verdict, label = "ok", "达标"
    elif today_n > 0:
        verdict, label = "short", "未达标"
    else:
        verdict, label = "zero", "没有进展"

    # ---------- 输出 ----------
    who = f"学号 {user.student_id}" if user.student_id else f"用户名 {user.username}"
    name = user.real_name or user.nickname or user.username
    print(f"【引导式学习 · 每日结算】{today.isoformat()}（{name} · {who}）")
    print(f"数据源：{settings.DB_URL.split('@')[-1].split('?')[0]}")
    print(f"今天完成：{today_n} 节   昨天完成：{yest_n} 节")
    if not today_n:
        last_at = max((r.completed_at for r in done.values() if r.completed_at), default=None)
        if last_at:
            print(f"（该账号最近一次完成：{last_at:%Y-%m-%d %H:%M}）")
    print(f"目标：每天 {GOAL_MIN}-{GOAL_MAX} 节   →   {label}")
    print(
        f"累计进度：{completed_total} / {total_lessons} 节"
        f"（{completed_total / total_lessons * 100:.1f}%），还剩 {total_lessons - completed_total} 节"
    )
    if streak:
        print(f"连续达标：{streak} 天")

    todays = sorted(
        (r for r in done.values() if r.completed_at and r.completed_at.date() == today),
        key=lambda r: r.completed_at,
    )
    by_code = {p["code"]: p for p in CURRICULUM}
    if todays:
        print("今天打勾的课：")
        for r in todays:
            p = by_code.get(r.point_code) or {}
            print(f"  ✓ [{p.get('subject', '?')}] {r.point_code} · {p.get('title', '?')}"
                  f"  ({r.completed_at:%H:%M})")

    if verdict in ("short", "zero"):
        print(f"差距：还差 {max(0, GOAL_MIN - today_n)} 节才算完成今天的最低目标。")

    # 接下来能做的（已解锁）
    available = [p for p, st in statuses if st == "unlocked"]
    if available:
        print(f"现在可继续学的：{len(available)} 节已解锁，例如：")
        for p in available[:4]:
            print(f"  · [{p['subject']}] {p['code']} · {p['title']}")
    elif completed_total:
        print("所有已解锁的课都做完了（后面还锁着，需要先过前一节）。")

    if show_days > 1:
        print(f"最近 {show_days} 天明细：")
        for i in range(show_days):
            d = today - timedelta(days=i)
            n = per_day.get(d.isoformat(), 0)
            mark = "✓" if n >= GOAL_MIN else ("·" if n else "—")
            print(f"  {d.isoformat()}  {mark}  {n} 节")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
