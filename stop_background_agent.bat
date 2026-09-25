@echo off
title Autonomous AI Background Agent - Stop
cd /d "%~dp0"
python background_daemon.py stop
echo.
pause
