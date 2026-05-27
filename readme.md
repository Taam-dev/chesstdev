# ♟️ ChessCoach Local

> A fully offline AI-powered chess analysis desktop application powered by Stockfish NNUE.
> Acts as your personal chess coach — not just an engine wrapper.

![ChessCoach Local Banner](docs/screenshots/banner.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)]()
[![Engine](https://img.shields.io/badge/Engine-Stockfish%2016%20NNUE-green)]()
[![Offline](https://img.shields.io/badge/Mode-100%25%20Offline-brightgreen)]()

---

## 🎯 What is ChessCoach Local?

ChessCoach Local is a **production-quality desktop chess analysis tool** that runs
**entirely on your computer** — no internet required, no cloud APIs, no telemetry.

It uses **Stockfish 16 NNUE** (the world's strongest open-source chess engine) combined
with a human-friendly coaching layer that explains every move in plain language.

---

## ✨ Features

### 🧠 AI Chess Coaching
- Real-time position analysis
- Best move suggestions with **human language explanations**
- Tactical pattern detection (forks, pins, skewers, mating nets...)
- Move quality classification (Brilliant ✨ → Blunder ???)
- **Chess.com-style move annotations** (toggle on/off)

### 📊 Analysis Dashboard
- Live evaluation bar
- Principal variation display
- MultiPV lines (up to 5 lines simultaneously)
- Analysis timeline with move-by-move review
- Adjustable engine depth (1-30+)

### 🎮 Board Interaction
- Drag-and-drop pieces
- PGN import/export
- FEN editor
- Arrow overlays for best moves
- Position heatmaps

### 🖥️ Board Recognition
- **Screen Capture Mode**: Detect Chess.com/Lichess boards automatically
- **Webcam Mode**: Analyze physical chessboard via camera

### 💾 Fully Offline
- 100% local processing
- SQLite database for game storage
- No internet required after setup
- No telemetry or tracking

---

## 🖼️ Screenshots

[SCREENSHOT: Main analysis dashboard]
![Main Dashboard](docs/screenshots/main-dashboard.png)

[SCREENSHOT: Move explanations panel]
![Move Explanations](docs/screenshots/move-explanations.png)

[SCREENSHOT: Tactics detection]
![Tactics](docs/screenshots/tactics.png)

[SCREENSHOT: Screen capture mode]
![Screen Capture](docs/screenshots/screen-capture.png)

---

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 (primary), Linux, macOS
- Node.js 18+
- Python 3.10+
- 4GB RAM minimum (8GB recommended)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/chess-coach-local.git
cd chess-coach-local

# 2. Run setup script (Windows)
scripts\setup.bat

# OR Linux/macOS
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Start application
npm run dev
Full installation guide: See INSTALLATION GUIDE below.

📖 Installation Guide
Windows Installation
Step 1: Install Node.js
Go to https://nodejs.org
Download LTS version (18.x or higher)
Run installer, check "Add to PATH"
Verify: Open Command Prompt → node --version
Step 2: Install Python
Go to https://python.org/downloads
Download Python 3.10 or higher
IMPORTANT: Check "Add Python to PATH" during installation
Verify: python --version
Step 3: Clone and Setup
batch

git clone https://github.com/yourusername/chess-coach-local.git
cd chess-coach-local
scripts\setup.bat
Step 4: Download Stockfish
batch

python scripts\download-stockfish.py
Or manually download from https://stockfishchess.org/download/ and place
in assets/engines/stockfish.exe

Step 5: Run the Application
batch

npm run dev
Linux Installation
Bash

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip nodejs npm git \
    libopencv-dev python3-opencv libsqlite3-dev \
    libx11-dev libxext-dev libxrender-dev

# Install Stockfish
sudo apt-get install -y stockfish

# Clone and setup
git clone https://github.com/yourusername/chess-coach-local.git
cd chess-coach-local
chmod +x scripts/setup.sh
./scripts/setup.sh

# Run
npm run dev
macOS Installation
Bash

# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install node python stockfish opencv

# Clone and setup
git clone https://github.com/yourusername/chess-coach-local.git
cd chess-coach-local
./scripts/setup.sh

# Allow app through Gatekeeper if needed
xattr -cr dist/ChessCoachLocal.app

# Run
npm run dev
📚 Usage Guide
Starting Analysis
Launch ChessCoach Local
The main board appears in the center
Click "Start Analysis" button or press Ctrl+A
Stockfish begins analyzing the current position
[SCREENSHOT: Start analysis button highlighted]

Loading a PGN Game
Click File → Open PGN or press Ctrl+O
Select your .pgn file
The game loads in the move history panel
Navigate moves with arrow keys ← →
Using the Engine Settings
Depth: Higher = stronger analysis (10-15 for quick, 20+ for deep)
MultiPV: Number of alternative lines (1-5)
Threads: CPU cores to use (auto-detected)
Hash: Memory for engine (256MB-2GB recommended)
Activating Chess.com-Style Move Annotations
Toggle "Show Move Evaluations" in toolbar
After analysis, each move shows a badge:
✨ Brilliant
!! Great
! Best
✓ Good
⊙ Inaccuracy
? Mistake
?? Blunder
[SCREENSHOT: Move annotations visible on board]

Understanding Move Explanations
The coaching panel explains every move:

text

Knight f5 !! Great Move
━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Tactical: Attacks both the queen on d6 and rook on h6 (fork!)
♟️ Strategic: Centralizes knight on dominant outpost
🏰 Positional: Controls key squares d4, g7, h4
⚡ Threats: Forces queen movement, winning the exchange
⚠️  If ignored: Black loses material immediately
Screen Capture Mode (Chess.com / Lichess)
Open Chess.com or Lichess in your browser
In ChessCoach, click "Screen Capture" button
Click "Calibrate" and draw a rectangle around the chessboard
Analysis updates automatically as moves are made
Webcam Mode (Physical Board)
Connect/enable webcam
Click "Webcam Mode"
Position camera directly above board
Click "Calibrate" - follow on-screen guide
Analysis tracks physical game in real-time
Interpreting the Evaluation Bar
text

+5.0  White is winning decisively
+2.0  White has significant advantage  
+0.5  White is slightly better
 0.0  Equal position
-0.5  Black is slightly better
-2.0  Black has significant advantage
-5.0  Black is winning decisively
 M5   Checkmate in 5 moves
⌨️ Keyboard Shortcuts
Key	Action
Ctrl+A	Start/Stop analysis
Ctrl+O	Open PGN
Ctrl+S	Save game
← / →	Navigate moves
Ctrl+F	Open FEN editor
Ctrl+R	Reset board
Ctrl+,	Open settings
Space	Pause/Resume engine
Ctrl+C	Copy FEN
Ctrl+V	Paste FEN
🔧 Troubleshooting
Stockfish not found
text

Error: Engine not found at assets/engines/stockfish
Solution: Run python scripts/download-stockfish.py
Python backend won't start
text

Error: Connection refused on port 8765
Solution: 
1. Check Python is installed: python --version
2. Reinstall deps: pip install -r backend/requirements.txt
3. Run manually: python backend/main.py
Screen capture not detecting board
text

Solution:
1. Make sure board is fully visible on screen
2. Increase browser zoom to 100%
3. Recalibrate using the calibration tool
4. Try "Manual FEN input" instead
Analysis is slow
text

Solution:
1. Reduce engine depth to 15
2. Reduce MultiPV to 1
3. Increase thread count in settings
4. Close other applications
OpenCV errors on Windows
text

pip uninstall opencv-python opencv-python-headless
pip install opencv-python==4.8.0.76
🏗️ Architecture
text

┌─────────────────────────────────────────┐
│           Electron Shell                │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │   React UI  │  │  IPC Bridge     │  │
│  │  + Board    │  │  (Main↔Renderer)│  │
│  └──────┬──────┘  └────────┬────────┘  │
│         │                  │           │
│         └────────┬─────────┘           │
│                  │                     │
│         ┌────────▼────────┐            │
│         │  WebSocket      │            │
│         │  Client         │            │
│         └────────┬────────┘            │
└──────────────────┼──────────────────────┘
                   │ ws://localhost:8765
┌──────────────────▼──────────────────────┐
│         Python FastAPI Backend          │
│  ┌──────────────┐  ┌──────────────────┐ │
│  │  Stockfish   │  │  Chess Coach     │ │
│  │  Manager     │  │  (Explainer)     │ │
│  └──────┬───────┘  └──────────────────┘ │
│         │                               │
│  ┌──────▼───────┐  ┌──────────────────┐ │
│  │  UCI Protocol│  │  Board Vision    │ │
│  │  Manager     │  │  (OpenCV)        │ │
│  └──────────────┘  └──────────────────┘ │
│  ┌──────────────────────────────────────┤
│  │        SQLite Database               │
│  └──────────────────────────────────────┤
└─────────────────────────────────────────┘
📄 License
MIT License - see LICENSE file

🤝 Contributing
Pull requests welcome! See CONTRIBUTING.md

⭐ Star this repo if it helps you improve your chess!