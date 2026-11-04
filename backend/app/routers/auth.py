"""认证路由：注册、登录、直通登录、当前用户。"""
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Character, User
from ..schemas import ChangePasswordIn, LoginIn, RegisterIn, TokenOut
from ..security import create_token, get_current_user, hash_password, verify_password
from ..services import growth
from ..services.rate_limit import SlidingWindowLimiter, enforce

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 防密码爆破：同一 IP 每分钟最多 30 次登录尝试。
# 不能更紧 —— 校园网/宿舍 WiFi 下几十个学生共用一个出口 IP，30 人才刚好够一个班同时登录。
# 对爆破而言 30 次/分钟仍无实际威胁（8 位复杂密码的空间远超单日 4.3 万次）。
_login_limiter = SlidingWindowLimiter(30, 60, "登录尝试")
# 防批量注册：同一 IP 每小时最多 50 个账号。
# 开学第一节课全班同时注册是真实场景，原来的 10 个会让后排的人干等一小时。
_register_limiter = SlidingWindowLimiter(50, 3600, "注册")
# 改密码要验旧密码，本质也是一次密码校验，同样可能被拿来爆破：
# 每 IP 每分钟 10 次（正常用户不会连改十次，爆破也过不了这一关）
_change_pwd_limiter = SlidingWindowLimiter(10, 60, "修改密码")


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    enforce(_register_limiter, request)
    if db.query(User).filter(User.student_id == body.student_id).first():
        raise HTTPException(400, "该学号已注册，请直接登录")
    if db.query(User).filter(User.username == body.student_id).first():
        raise HTTPException(400, "该学号已注册，请直接登录")
    # 新账号：登录名直接用学号，昵称取姓名（排行榜展示用姓名）
    user = User(username=body.student_id, student_id=body.student_id,
                real_name=body.real_name, nickname=body.real_name,
                password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    # 注册即建角色：新手引导已下线，登录后直接进首页
    growth.ensure_character(db, user)
    return TokenOut(access_token=create_token(user.id))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    enforce(_login_limiter, request)
    # 优先按学号查；查不到再按 username 查，兼容 2026-10-26 之前注册的老账号
    user = (db.query(User).filter(User.student_id == body.student_id).first()
            or db.query(User).filter(User.username == body.student_id).first())
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(400, "学号或密码错误")
    return TokenOut(access_token=create_token(user.id))


@router.post("/guest", response_model=TokenOut)
def guest(db: Session = Depends(get_db)):
    """直通登录：页面无需登录，直接以「主账号」身份进入。

    ⚠️ 只有在 `ALLOW_GUEST_LOGIN=True` 时可用（本地开发默认开）。
    **公网部署必须设成 false**，否则任何人打开网页都是同一个账号，
    所有人的进度、金币、面试记录会互相覆盖。

    主账号由 `settings.AUTO_LOGIN_USERNAME` 指定。这里**只补缺、绝不覆盖**：
    账号已存在就原样使用（进度、成就、记录全都在），只有确实不存在时才新建。

    ⚠️ 主账号名写错时，这里会静默新建一个空白账号，学生看到的就是
    「我上次解锁的课全没了」—— 所以账号不存在时一定要打日志。
    """
    if not settings.ALLOW_GUEST_LOGIN:
        raise HTTPException(403, "本站已启用账号登录，请使用用户名和密码登录")
    username = settings.AUTO_LOGIN_USERNAME
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        print(f"[auth] ⚠️ 主账号 {username!r} 不存在，已新建空白账号。"
              f"若你是在找回旧进度，请检查 .env / config.py 里的 AUTO_LOGIN_USERNAME")
        user = User(username=username, nickname=username,
                    password_hash=hash_password(secrets.token_hex(16)))
        db.add(user)
        db.commit()
        db.refresh(user)
    if user.character is None:
        # 只注册过、没走完引导的账号：补一个默认角色，直接进首页。
        char = Character(user_id=user.id, name="冒险者", identity="在校学生",
                         class_key="backend", class_name=growth.class_info("backend")["name"],
                         level=1, exp=0, coins=100, hp=3, max_hp=3, onboarding_done=True)
        db.add(char)
        db.commit()
        db.refresh(user)
        growth.unlock_levels(db, user)
    return TokenOut(access_token=create_token(user.id))


@router.post("/change-password")
def change_password(body: ChangePasswordIn, request: Request,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    """改密码：先验旧密码，再写新哈希。

    只换 password_hash，不动角色、经验、课程进度、收藏、错题。
    已经发出去的 JWT 仍然有效（有效期 7 天）——
    这是刻意的：学生在机房改完密码，不该被踢回登录页重新输一遍。
    """
    enforce(_change_pwd_limiter, request)
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(400, "当前密码不正确")
    if verify_password(body.new_password, user.password_hash):
        raise HTTPException(400, "新密码不能和当前密码相同")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    print(f"[auth] 用户 {user.id}（{user.student_id or user.username}）修改了密码")
    return {"ok": True}


@router.get("/me")
def me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 存量账号（注册于引导下线之前、没建过角色）在这里补齐，避免任何页面 400
    growth.ensure_character(db, user)
    return {"id": user.id, "username": user.username, "nickname": user.nickname,
            "student_id": user.student_id, "real_name": user.real_name or user.nickname,
            "grade": user.grade, "class_code": user.class_code,
            "onboarding_done": True}
