@echo off
chcp 65001 >nul
title 停止 WebHosting 服务
color 0C
cd /d "%~dp0"

echo ====================================
echo WebHosting 守护进程停止脚本
echo ====================================
echo.
echo 正在检查 psutil 模块...
python -c "import psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装 psutil 模块...
    pip install psutil
)

echo.
echo 正在查找并停止进程...
echo.

python stop_service.py

pause
