@echo off
echo 🚀 Starting SnapVault Backend...
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ❌ Virtual environment not found!
    echo Please run setup.bat first to set up the project.
    pause
    exit /b 1
)

REM Activate virtual environment and start the server
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

echo 🚀 Starting FastAPI server...
echo 📍 Server will be available at: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000 