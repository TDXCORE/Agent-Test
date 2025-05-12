@echo off
echo Running FastAPI Chat API Tests...
echo.
cd %~dp0
python test_api.py
pause
