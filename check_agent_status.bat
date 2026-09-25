@echo off
title Autonomous AI Background Agent - Status
cd /d "%~dp0"
python background_daemon.py status
echo.
pause
