@echo off
rem Start de Hyped-bot en herstart hem automatisch als hij stopt.
cd /d "%~dp0"
:loop
python hyped_bot.py
echo Bot gestopt, herstart over 10 seconden...
timeout /t 10 /nobreak >nul
goto loop
