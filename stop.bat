@echo off
setlocal
cd /d "%~dp0"
title 停止服务

echo.
echo   停止 代码冒险者 的前后端服务
echo   ----------------------------------------------------------
call :kill_port 8001 后端
call :kill_port 5173 前端
echo   ----------------------------------------------------------
echo   按任意键关闭
pause >nul
exit /b 0

:kill_port
set "HIT="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":%~1 " ^| findstr /C:"LISTENING"') do call :kill_one %~1 %%p
if defined HIT goto :eof
echo   [--] 端口 %~1  没有进程在跑
goto :eof

:kill_one
echo   [停] 端口 %~1  PID %~2
taskkill /F /T /PID %~2 >nul 2>&1
set "HIT=1"
goto :eof
