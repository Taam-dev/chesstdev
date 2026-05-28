@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   ♟ Chess Assistant — Build ^& Package Script 
echo =======================================================
echo.

:: Step 1: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system.
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

:: Step 2: Check or create virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
) else (
    echo [INFO] Existing virtual environment found.
)

:: Step 3: Upgrade pip and install dependencies
echo [INFO] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

echo [INFO] Installing required dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed successfully.
echo.

:: Step 4: Ask the user if they want to build the standalone EXE using PyInstaller
echo =======================================================
set /p BUILD_EXE="Do you want to compile to a standalone EXE? (y/n): "
if /i "%BUILD_EXE%" neq "y" (
    echo [INFO] Build script completed successfully, environment is set up.
    echo To run the application, run:
    echo   venv\Scripts\python.exe main.py
    echo.
    pause
    exit /b 0
)

echo.
echo [INFO] Installing PyInstaller...
venv\Scripts\python.exe -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

echo [INFO] Compiling Chess Assistant into a standalone executable...
set "ICON_ARG="
if exist "icon.ico" (
    set "ICON_ARG=--icon="icon.ico""
)
venv\Scripts\pyinstaller --onefile --noconsole !ICON_ARG! --name="ChessAssistant" main.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed to package the application.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo   🎉 SUCCESS! The standalone executable has been built!
echo =======================================================
echo  You can find the executable at:
echo    dist\ChessAssistant.exe
echo.
pause
exit /b 0
