@echo off
echo Building Chat API for deployment...

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run tests
echo Running tests...
cd endpoint
python test_api.py
cd ..

REM Create .env file if it doesn't exist
if not exist endpoint\.env (
    echo Creating .env file...
    copy endpoint\.env.example endpoint\.env
    echo Please update the .env file with your Supabase credentials
)

echo Build complete! You can now deploy to Render using the render.yaml file.
echo For more information, see README_RENDER_CHAT_API.md

pause
