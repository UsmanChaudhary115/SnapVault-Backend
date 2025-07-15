@echo off
echo SnapVault Backend Setup for Windows
echo ======================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found

REM Create virtual environment
if exist venv (
    echo Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
)

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed

REM Create uploads directory
if not exist uploads (
    mkdir uploads
    echo Created uploads directory
) else (
    echo Uploads directory already exists
)

echo.
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate
echo 2. Run the application:
echo    uvicorn main:app --reload
echo 3. Access the API documentation:
echo    http://localhost:8000/docs
echo.
echo For more information, see API_DOCUMENTATION.md
echo.
pause 