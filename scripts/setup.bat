@echo off
echo Setting up ChessCoach Local...

REM Node dependencies
echo Installing Node.js dependencies...
npm install
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Node dependencies
    exit /b 1
)

REM Python venv
echo Setting up Python environment...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found. Please install Python 3.9+
    exit /b 1
)

cd backend
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
cd ..

REM Assets
if not exist "assets\engines" mkdir assets\engines
if not exist "assets\icons"   mkdir assets\icons
if not exist "assets\sounds"  mkdir assets\sounds

REM Download Stockfish
echo Downloading Stockfish...
python scripts\download-stockfish.py

REM Copy env
if not exist ".env" (
    copy .env.example .env
    echo Created .env from .env.example
)

echo.
echo Setup complete! Run: npm run dev
pause