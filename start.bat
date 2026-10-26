@echo off
setlocal
cd /d "%~dp0"
title 代码冒险者 · 一键启动

echo.
echo   ==========================================================
echo     代码冒险者   一键启动
echo   ----------------------------------------------------------
echo     后端  FastAPI    http://localhost:8001/docs
echo     前端  Vite       http://localhost:5173
echo   ==========================================================
echo.

REM ---------- 1. 定位 Python（必须装过 fastapi / uvicorn）----------
set "PY="
if defined PYTHON if exist "%PYTHON%" set "PY=%PYTHON%"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY set "PY=python"

"%PY%" -c "import fastapi, uvicorn" >nul 2>&1
if not errorlevel 1 goto :py_ok

echo   [X] 没找到装了 fastapi / uvicorn 的 Python
echo.
echo       刚才试的解释器 : %PY%
echo       推荐使用这个   : %LOCALAPPDATA%\Programs\Python\Python312\python.exe
echo       它已经有依赖就不用改；缺依赖装一下:
echo         pip install -r backend\requirements.txt
echo       换解释器: 先 set PYTHON=你的python.exe 再运行本脚本
echo.
pause
exit /b 1

:py_ok
echo   [OK] 解释器 %PY%
"%PY%" --version
echo.

REM ---------- 2. 端口占用检查（同一时间只应有一个后端实例）--------
set "BE_PID="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":8001 " ^| findstr /C:"LISTENING"') do set "BE_PID=%%p"
set "FE_PID="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":5173 " ^| findstr /C:"LISTENING"') do set "FE_PID=%%p"

if not defined BE_PID goto :start_be
echo   [!] 8001 已有进程在跑（PID %BE_PID%），后端不重复启动
goto :be_done

:start_be
start "后端 FastAPI :8001" "%~dp0scripts\run-backend.bat"
echo   [^>] 后端窗口已弹出
:be_done

if not defined FE_PID goto :start_fe
echo   [!] 5173 已有进程在跑（PID %FE_PID%），前端不重复启动
goto :fe_done

:start_fe
start "前端 Vite :5173" "%~dp0scripts\run-frontend.bat"
echo   [^>] 前端窗口已弹出
:fe_done

REM ---------- 3. 等后端和前端都就绪，再开浏览器 ----------
echo.
echo   等待后端和前端就绪...
set /a TRY=0
set "BE_UP="
set "FE_UP="

:wait_both
set /a TRY+=1
netstat -ano | findstr /C:":8001 " | findstr /C:"LISTENING" >nul && set "BE_UP=1"
netstat -ano | findstr /C:":5173 " | findstr /C:"LISTENING" >nul && set "FE_UP=1"
if defined BE_UP if defined FE_UP goto :all_ready
if %TRY% GEQ 90 goto :too_slow
ping -n 2 127.0.0.1 >nul 2>&1
goto :wait_both

:all_ready
echo   [OK] 后端 8001 已就绪
echo   [OK] 前端 5173 已就绪
start "" http://localhost:5173
echo   [OK] 浏览器已打开 http://localhost:5173
goto :done

:too_slow
if defined BE_UP echo   [OK] 后端 8001 已就绪
if not defined BE_UP echo   [X]  后端 8001 没起来，去看「后端 FastAPI」窗口的报错
if defined FE_UP echo   [OK] 前端 5173 已就绪
if not defined FE_UP echo   [X]  前端 5173 没起来，去看「前端 Vite」窗口的报错
echo        首次运行要先装依赖，慢一点是正常的

:done
echo.
echo   ----------------------------------------------------------
echo   两个黑窗口开着就是服务在跑，关掉任何一个即停对应服务
echo   一键停止：双击 stop.bat
echo   ----------------------------------------------------------
echo.
pause
exit /b 0
