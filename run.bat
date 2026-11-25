@echo off
setlocal
title AI Maze Solver
cd /d "%~dp0"

REM Check for virtual environment, create if missing
if not exist ".venv\Scripts\python.exe" (
    echo [Setup] Virtual environment not found. Creating .venv...
    where python >nul 2>nul
    if errorlevel 1 (
        echo [Error] Python is not installed or not available in PATH.
        echo Please install Python 3.10+ and add it to your system PATH.
        pause
        exit /b 1
    )
    python -m venv .venv
    if errorlevel 1 (
        echo [Error] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [Setup] Installing required dependencies from requirements.txt...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [Error] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [Setup] Environment ready.
    echo.
)

echo Starting AI Maze Solver...
.venv\Scripts\python.exe main.py %*
if errorlevel 1 (
    echo.
    echo [Error] Application terminated with an error.
    pause
    exit /b %errorlevel%
)
