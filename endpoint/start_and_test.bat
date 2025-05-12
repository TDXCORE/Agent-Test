@echo off
echo Starting FastAPI Chat API Server and Tests...
echo.

REM Start the server in a new window
start cmd /k "cd %~dp0 && python run.py"

REM Wait for the server to start
echo Waiting for server to start...
timeout /t 5 /nobreak

REM Run the tests
echo Running tests...
cd %~dp0
python test_api.py

echo.
echo Press any key to exit...
pause > nul
