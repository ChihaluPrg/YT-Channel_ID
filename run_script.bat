@echo off
cd /d "D:\Programming\PyCharm\YT-Channel_ID"
call .venv\Scripts\activate
python YT-Channel_ID.py
timeout /t 3 >nul