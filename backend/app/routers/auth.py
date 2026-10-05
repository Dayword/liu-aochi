"""认证路由：注册、登录、访客直通、当前用户。"""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Character, User
from ..schemas import LoginIn, RegisterIn, TokenOut
from ..security import create_token, get_current_user, hash_password, verify_password
from ..services import growth

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 访客直通账号：前端已移除登录页，启动时用它静默换 Token。
GUEST_USERNAME = "guest"


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, "用户名已存在")
    user = User(username=body.username, nickname=body.nickname or body.username,
                password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(400, "用户名或密码错误")
    return TokenOut(access_token=create_token(user.id))


@router.post("/guest", response_model=TokenOut)
def guest(db: Session = Depends(get_db)):
    """访客直通：页面无需登录，自动复用/创建访客账号并签发 Token。"""
    user = db.query(User).filter(User.username == GUEST_USERNAME).first()
    if user is None:
        user = User(username=GUEST_USERNAME, nickname="冒险者",
                    password_hash=hash_password(secrets.token_hex(16)))
        db.add(user)
        db.commit()
        db.refresh(user)
    if user.character is None:
        # 默认角色直接置为「已完成新手引导」，跳过引导页直接进首页。
        char = Character(user_id=user.id, name="代码冒险者", identity="在校学生",
                         class_key="backend", class_name=growth.class_info("backend")["name"],
                         level=1, exp=0, coins=100, hp=3, max_hp=3, onboarding_done=True)
        db.add(char)
        db.commit()
        db.refresh(user)
        growth.unlock_levels(db, user)
    return TokenOut(access_token=create_token(user.id))


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "nickname": user.nickname,
            "onboarding_done": user.character.onboarding_done if user.character else False}
