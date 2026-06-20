@echo off
chcp 65001 >nul
title Work Log 工作记录系统
cd /d D:\work-log

echo ================================
echo   Work Log 工作记录系统 启动中...
echo ================================
echo.

call venv\Scripts\activate.bat
python -m app.main

pause
