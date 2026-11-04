@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Stable ASCII Video Generator (Windows Runner)
echo ========================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your PATH!
    echo.
    echo Please install Python (version 3.10 or newer) from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Make sure to check the box
    echo   "Add python.exe to PATH"
    echo at the bottom of the first installer screen.
    echo.
    pause
    exit /b 1
)

:: 2. Create virtual environment if it does not exist
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Activate virtual environment
call .venv\Scripts\activate.bat

:: 4. Install / verify dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Encountered an issue installing requirements. Retrying without quiet...
    pip install -r requirements.txt
)

:: 5. Run the generator
echo.
echo Starting video conversion...
echo.

if "%~1"=="" (
    python main.py
) else (
    python main.py %*
)

echo.
pause
