#!/usr/bin/env bash
set -e

echo "🚀 Setting up ChessCoach Local..."

# ─── Node.js dependencies ────────────────────────────────────────────────────
echo "📦 Installing Node.js dependencies..."
npm install

# ─── Python virtual environment ──────────────────────────────────────────────
echo "🐍 Setting up Python environment..."
if ! command -v python3 &>/dev/null; then
  echo "❌ Python3 not found. Please install Python 3.9+"
  exit 1
fi

cd backend
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# ─── Assets folders ──────────────────────────────────────────────────────────
mkdir -p assets/engines assets/icons assets/sounds

# ─── Download Stockfish ──────────────────────────────────────────────────────
echo "♟ Downloading Stockfish..."
python3 scripts/download-stockfish.py

# ─── Copy env ────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Created .env from .env.example"
fi

echo ""
echo "✅ Setup complete!"
echo "   Run: npm run dev"