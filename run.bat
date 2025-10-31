@echo off
setlocal enabledelayedexpansion

REM Vehicle Painter Launcher Script
REM Creates a virtual environment, installs dependencies, and runs the application

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

echo Vehicle Painter for Cataclysm: Bright Nights
echo ==============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo Error: python is not installed or not in PATH
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    set "PYTHON_CMD=python"
)

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
if exist "%SCRIPT_DIR%requirements.txt" (
    echo Installing requirements...
    python -m pip install -r "%SCRIPT_DIR%requirements.txt" --quiet
) else (
    echo Warning: requirements.txt not found, skipping dependency installation.
)

echo.
echo Starting Vehicle Painter...
echo.

REM Run the application
python "%SCRIPT_DIR%main.py"

REM Deactivate virtual environment when done
call deactivate
