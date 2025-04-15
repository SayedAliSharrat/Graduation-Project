@echo off
cd .venv2\Scripts
call activate
cd ..\..
start cmd.exe /k "python live_cam.py"