"""代码运行路由（在线运行 Python）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import CodeRunIn, CodeRunOut
from ..security import get_current_user
from ..services.code_runner import run_python

router = APIRouter(prefix="/api/code", tags=["code"])


@router.post("/run", response_model=CodeRunOut)
def run(body: CodeRunIn, db: Session = Depends(get_db),
        user: User = Depends(get_current_user)):
    if not user.character:
        raise HTTPException(400, "请先创建角色")
    if body.language != "python":
        raise HTTPException(400, "演示环境目前仅支持 Python，生产将接入 Judge0 多语言沙箱")
    if not body.code.strip():
        raise HTTPException(400, "代码不能为空")
    return CodeRunOut(**run_python(body.code, body.stdin or ""))
