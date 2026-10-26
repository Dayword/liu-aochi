@echo off
title 后端 FastAPI :8001
cd /d "%~dp0..\backend"

REM 由 start.bat 调用时会继承 PY；单独双击时自己找一遍
if not defined PY set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo   后端 FastAPI   http://localhost:8001    接口文档 /docs
echo   工作目录 %CD%
echo   解释器   %PY%
echo   ------------------------------------------------------------

"%PY%" run.py

echo.
echo   [后端已退出] 退出码 %errorlevel%  ／ 上面最后几行就是原因
echo   按任意键关闭本窗口
pause >nul
