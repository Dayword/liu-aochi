"""重置账号密码（迁移用）。

背景：早期版本没有登录页，前端靠 `/api/auth/guest` 静默以主账号进入，
那个账号的密码是一串随机数，没人知道。现在改成账号密码登录后，
需要先把主账号的密码设成你自己记得的，否则会以为「进度全丢了」。

用法：
    cd backend
    python reset_password.py --list            # 看看有哪些账号、进度如何
    python reset_password.py 如梦令 我的新密码   # 重置指定账号的密码

只改 password_hash，不动角色、金币、课程进度、面试记录。
"""
from __future__ import annotations

import sys

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

MIN_LEN = 8


def list_users() -> None:
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        if not users:
            print("数据库里还没有账号")
            return
        print(f"{'ID':>4}  {'用户名':<16} {'角色':<12} {'等级':>4} {'金币':>6}")
        print("-" * 50)
        for u in users:
            c = u.character
            print(f"{u.id:>4}  {u.username:<16} "
                  f"{(c.name if c else '—'):<12} "
                  f"{(c.level if c else 0):>4} {(c.coins if c else 0):>6}")
    finally:
        db.close()


def reset(username: str, password: str) -> int:
    if len(password) < MIN_LEN:
        print(f"密码至少 {MIN_LEN} 位")
        return 1
    if len(password.encode("utf-8")) > 72:
        print("密码过长（bcrypt 上限 72 字节）")
        return 1
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            print(f"账号不存在：{username}")
            print("用 --list 看看有哪些账号")
            return 1
        user.password_hash = hash_password(password)
        db.commit()
        c = user.character
        print(f"✅ 已重置「{username}」的密码")
        if c:
            print(f"   这个账号的角色：{c.name} · Lv.{c.level} · {c.coins} 金币（进度未受影响）")
    finally:
        db.close()
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--list":
        list_users()
        return 0
    if len(args) != 2:
        print("用法：python reset_password.py <用户名> <新密码>   或   python reset_password.py --list")
        return 1
    return reset(args[0], args[1])


if __name__ == "__main__":
    raise SystemExit(main())
