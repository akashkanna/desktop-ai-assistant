@echo off
title Starting Jarvis...
cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Jarvis in the background...
start pythonw main.py

exit
