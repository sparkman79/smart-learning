@echo off
REM 启动飞书 Bot 适配器
cd /d "%~dp0"
set WORKSPACE=%~dp0..
python adapter.py
pause