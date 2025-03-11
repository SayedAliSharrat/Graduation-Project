@echo off
cd .venv2\Scripts
call activate
cd ..\..
start cmd.exe /k "python manage.py runserver"
start http://127.0.0.1:8000
