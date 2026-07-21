@echo off
title Khoi dong MatchEngine
echo ==========================================================
echo   Dang khoi dong He thong Doi sanh Mentor-Student...
echo ==========================================================
echo.
echo [1/2] Dang kiem tra va cai dat cac thu vien (requirements)...
pip install -r requirements.txt
echo.
echo [2/2] Dang khoi chay server backend va mo Dashboard...
python main.py
pause
