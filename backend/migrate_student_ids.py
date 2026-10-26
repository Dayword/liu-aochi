"""把老账号迁到学号体系（幂等，可重复执行）。

2026-10-26 起注册/登录改成 11 位学号：前 4 位=年级，5~9 位=班级，后 2 位=班内座号。
历史账号没有学号，用这个脚本补上，补完即可参与排行榜。

用法（在 backend 目录、用装了依赖的 Python 执行）：

    python migrate_student_ids.py --list
    python migrate_student_ids.py 如梦令 20230614224 刘澳驰

脚本只改 `users.student_id / users.real_name / users.nickname`，
**不动密码、不动任何学习进度**。username 保持原样，所以两种登录名都能进。
"""
from __future__ import annotations

import re
import sys

from sqlalchemy import text

from app.database import SessionLocal, engine
from app.models import User


def ensure_columns() -> None:
    """老库缺列时先补上（和启动时的轻量迁移同一套逻辑）。"""
    if engine.dialect.name != "mysql":
        return
    with engine.begin() as conn:
        have = {r[0] for r in conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'users'"))}
        for name, ddl in (("student_id", "VARCHAR(16) NOT NULL DEFAULT ''"),
                          ("real_name", "VARCHAR(32) NOT NULL DEFAULT ''")):
            if name not in have:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                print(f"[migrate] 已补充字段 users.{name}")


def list_users() -> None:
    db = SessionLocal()
    try:
        rows = db.query(User).order_by(User.id).all()
        print(f"{'id':>3}  {'username':<20} {'student_id':<13} {'real_name':<10} nickname")
        for u in rows:
            print(f"{u.id:>3}  {u.username:<20} {u.student_id or '-':<13} "
                  f"{u.real_name or '-':<10} {u.nickname}")
        print(f"\n共 {len(rows)} 个账号；只有带 11 位学号的会进入排行榜。")
    finally:
        db.close()


def migrate(username: str, student_id: str, real_name: str) -> None:
    if not re.fullmatch(r"\d{11}", student_id):
        sys.exit("学号必须是 11 位数字，例如 20230614224")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = db.query(User).filter(User.student_id == username).first()
        if user is None:
            sys.exit(f"找不到账号：{username}（先用 --list 看有哪些）")
        clash = (db.query(User)
                 .filter(User.student_id == student_id, User.id != user.id).first())
        if clash:
            sys.exit(f"学号 {student_id} 已被 {clash.username} 占用")
        old = (user.student_id, user.real_name, user.nickname)
        user.student_id = student_id
        user.real_name = real_name
        user.nickname = real_name      # 站内展示统一用真实姓名
        db.commit()
        print(f"✅ 已迁移账号 id={user.id}")
        print(f"   学号   {old[0] or '(空)'} → {student_id}")
        print(f"   姓名   {old[1] or '(空)'} → {real_name}")
        print(f"   年级 {student_id[:4]} / 班级 {student_id[4:9]} / 座号 {student_id[-2:]}")
        print("   密码与学习进度未改动。")
    finally:
        db.close()


if __name__ == "__main__":
    ensure_columns()
    if len(sys.argv) == 1 or sys.argv[1] in ("-l", "--list"):
        list_users()
    elif len(sys.argv) == 4:
        migrate(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
