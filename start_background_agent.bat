@echo off
title Autonomous AI Background Agent - Launch
cd /d "%~dp0"
echo ======================================================================
echo   AUTONOMOUS AI BACKGROUND AGENT - USA TAKEOFF & ESTIMATION
echo ======================================================================
echo.
echo Starting Autonomous AI Agent silently in the background...
wscript.exe start_background_agent.vbs
timeout /t 2 /nobreak >nul
python background_daemon.py status
echo.
echo [INFO] Agent is now actively running in the background of your PC!
echo [INFO] You can safely close this window. The agent will continue running.
echo.
pause
