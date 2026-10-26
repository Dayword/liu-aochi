"""代码运行路由（在线运行 Python）。"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import CodeRunIn, CodeRunOut
from ..security import get_current_user
from ..services.code_runner import run_python
from ..services.rate_limit import SlidingWindowLimiter, enforce

router = APIRouter(prefix="/api/code", tags=["code"])

# 公网环境下最需要限流的入口：每次执行都真占 CPU
_run_limiter = SlidingWindowLimiter(settings.CODE_RUN_PER_MINUTE, 60, "代码运行")


@router.post("/run", response_model=CodeRunOut)
def run(body: CodeRunIn, request: Request, db: Session = Depends(get_db),
        user: User = Depends(get_current_user)):
    if not settings.CODE_RUN_ENABLED:
        raise HTTPException(403, "当前部署已关闭在线运行，请在本地环境练习")
    if not user.character:
        raise HTTPException(400, "请先创建角色")
    if body.language != "python":
        raise HTTPException(400, "演示环境目前仅支持 Python，生产将接入 Judge0 多语言沙箱")
    if not body.code.strip():
        raise HTTPException(400, "代码不能为空")
    enforce(_run_limiter, request, user.id)
    return CodeRunOut(**run_python(body.code, body.stdin or ""))
