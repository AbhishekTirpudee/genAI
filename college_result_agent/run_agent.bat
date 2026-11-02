@echo off
title College Result Analysis Agent
echo ==========================================================
echo        COLLEGE RESULT ANALYSIS AGENT (AI + SQL)
echo ==========================================================
echo.
echo Starting Flask Web Application on http://localhost:5050 ...
echo.

cd /d "%~dp0"
py app.py

pause
