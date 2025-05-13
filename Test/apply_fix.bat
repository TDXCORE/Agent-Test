@echo off
REM Script to automatically apply the fix to the Messages API on Windows

echo ===== MESSAGES API FIX SCRIPT =====
echo This script will automatically fix the order() method issue in App\Api\messages.py
echo.

REM Check if the file exists
if not exist "App\Api\messages.py" (
    echo Error: App\Api\messages.py not found
    echo Make sure you're running this script from the root directory of your project
    pause
    exit /b 1
)

REM Check if the file contains the problematic line
findstr /C:".order(\"created_at\", {\"ascending\": True}).execute()" "App\Api\messages.py" >nul
if errorlevel 1 (
    echo Warning: Could not find the problematic line in App\Api\messages.py
    echo The file may have already been fixed or the line might be different
    echo Would you like to continue anyway? (y/n)
    set /p response=
    if not "%response%"=="y" (
        echo Aborting
        pause
        exit /b 0
    )
)

REM Create a backup of the original file
echo Creating backup of original file...
copy "App\Api\messages.py" "App\Api\messages.py.bak" >nul
echo Backup created at App\Api\messages.py.bak

REM Apply the fix
echo Applying fix...
powershell -Command "(Get-Content 'App\Api\messages.py') -replace '\.order\(""created_at"", \{""ascending"": True\}\)\.execute\(\)', '.order(""created_at"").execute()' | Set-Content 'App\Api\messages.py'"

REM Check if the fix was applied
findstr /C:".order(\"created_at\").execute()" "App\Api\messages.py" >nul
if errorlevel 1 (
    echo Failed to apply fix
    echo Restoring backup...
    copy "App\Api\messages.py.bak" "App\Api\messages.py" >nul
    echo Backup restored
    pause
    exit /b 1
) else (
    echo Fix successfully applied!
)

echo.
echo ===== NEXT STEPS =====
echo 1. Restart your API server
echo 2. Test the Messages API to verify the fix
echo    You can use one of the test scripts:
echo    - node Test\comprehensive_api_test.js
echo    - node Test\fix_messages_api_test.js
echo    - node Test\api_fix_solution.js
echo.
echo Done!
pause
