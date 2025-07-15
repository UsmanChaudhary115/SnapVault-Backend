@echo off
setlocal enabledelayedexpansion

REM Default options
set INCLUDE_SUPABASE=false
set SUPABASE_ONLY=false

REM Parse command line arguments
:parse_args
if "%1"=="--with-supabase" (
    set INCLUDE_SUPABASE=true
    shift
    goto parse_args
)
if "%1"=="--supabase-only" (
    set SUPABASE_ONLY=true
    shift
    goto parse_args
)
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="/?" goto show_help
if not "%1"=="" (
    echo Unknown option: %1
    echo Use --help for usage information
    exit /b 1
)
goto start_setup

:show_help
echo SnapVault Backend Setup Script for Windows
echo.
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   --with-supabase     Include Supabase database setup
echo   --supabase-only     Only run Supabase database setup
echo   -h, --help, /?      Show this help message
echo.
echo Examples:
echo   %0                    # Basic setup
echo   %0 --with-supabase   # Setup with Supabase database
echo   %0 --supabase-only   # Only setup Supabase database
pause
exit /b 0

:start_setup
echo SnapVault Backend Setup for Windows
echo ========================================

REM Function to check environment variables
:check_env_vars
echo Checking environment variables...
set missing_vars=
if "%SUPABASE_URL%"=="" set missing_vars=!missing_vars! SUPABASE_URL
if "%SUPABASE_ANON_KEY%"=="" set missing_vars=!missing_vars! SUPABASE_ANON_KEY

if not "!missing_vars!"=="" (
    echo Missing environment variables:
    for %%v in (!missing_vars!) do echo    ❌ %%v
    echo.
    echo Please set these environment variables for Supabase integration:
    echo    set SUPABASE_URL=your-supabase-url
    echo    set SUPABASE_ANON_KEY=your-anon-key
    echo    set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  REM For admin operations
    exit /b 1
) else (
    echo All required environment variables are set
    exit /b 0
)

REM Function to setup Supabase database
:setup_supabase
echo.
echo Setting up Supabase database...
echo =========================================

REM Check environment variables
call :check_env_vars
if errorlevel 1 (
    echo Supabase setup skipped due to missing environment variables
    exit /b 1
)

REM Run Supabase setup
echo Setting up Supabase database tables...
call venv\Scripts\activate.bat
python -m utils.supabase_setup
if errorlevel 1 (
    echo Supabase database setup failed
    exit /b 1
)

echo Supabase database setup completed
exit /b 0

REM If supabase-only mode, skip basic setup
if "%SUPABASE_ONLY%"=="true" (
    echo Supabase-only setup mode
    echo.
    
    REM Check if virtual environment exists
    if not exist venv (
        echo Virtual environment not found. Please run basic setup first.
        echo    setup.bat
        pause
        exit /b 1
    )
    
    REM Setup Supabase
    call :setup_supabase
    if errorlevel 1 (
        echo.
        echo Supabase database setup failed
        pause
        exit /b 1
    ) else (
        echo.
        echo Supabase database setup completed successfully!
        pause
        exit /b 0
    )
)

REM Basic setup steps
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

REM Create uploads directories
echo Creating upload directories...
if not exist uploads mkdir uploads
if not exist uploads\photos mkdir uploads\photos
if not exist uploads\profile_pictures mkdir uploads\profile_pictures

echo Created uploads directory
echo Created uploads\photos directory
echo Created uploads\profile_pictures directory

REM Setup Supabase if requested
if "%INCLUDE_SUPABASE%"=="true" (
    call :setup_supabase
    if errorlevel 1 (
        echo Basic setup completed, but Supabase setup failed
        echo You can run Supabase setup later with: setup.bat --supabase-only
    )
)

echo.
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate

if "%INCLUDE_SUPABASE%"=="false" (
    echo 2. ^(Optional^) Setup Supabase database:
    echo    setup.bat --supabase-only
    echo 3. Run the application:
) else (
    echo 2. Run the application:
)

echo    uvicorn main:app --reload

if "%INCLUDE_SUPABASE%"=="false" (
    echo 4. Access the API documentation:
) else (
    echo 3. Access the API documentation:
)

echo    http://localhost:8000/docs
echo.
echo Documentation:
echo    • API_DOCUMENTATION.md - Local routes
echo    • SUPABASE_API_DOCUMENTATION.md - Supabase routes
echo    • SUPABASE_TEST_CASES.md - Test scenarios
echo.
pause 