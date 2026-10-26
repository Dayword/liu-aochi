@echo off
title 前端 Vite :5173
cd /d "%~dp0..\frontend"

if exist "node_modules" goto :run

echo.
echo   首次运行，正在安装前端依赖，大约 1-3 分钟...
call npm install --registry=https://registry.npmmirror.com
if errorlevel 1 goto :install_failed

:run
echo.
echo   前端 Vite   http://localhost:5173
echo   工作目录 %CD%
echo   接口 /api 自动代理到 8001
echo   ------------------------------------------------------------
call npm run dev

echo.
echo   [前端已退出] 退出码 %errorlevel%
echo   按任意键关闭本窗口
pause >nul
exit /b 0

:install_failed
echo.
echo   [X] 依赖安装失败，请看上面的报错
echo       常见原因：网络不通，或没装 Node.js
pause
exit /b 1
