@echo off
title Autonomous AI Background Agent - Live Logs
cd /d "%~dp0"
python background_daemon.py logs 35
echo.
pause
