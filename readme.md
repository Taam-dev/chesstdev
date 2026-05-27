# ♟ ChesstDev — Chess.com Practice Assistant

A lightweight desktop tool that suggests the best moves while practicing chess on Chess.com, powered by **Stockfish**.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Stockfish](https://img.shields.io/badge/Engine-Stockfish-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 Features

- 🔍 **Real-time FEN detection** from your Chess.com browser window
- 🧠 **Stockfish analysis** with configurable depth
- 🏆 **Top 3 moves** with evaluation scores and principal variation
- 🖥️ **Always-on-top GUI overlay** (Tkinter)
- ⌨️ **CLI mode** for quick analysis
- 🔁 **Auto-refresh** — automatically analyzes new positions
- 🌐 **Browser integration** via Tampermonkey userscript
- 📡 **Local relay server** for secure FEN transfer

---

## 📸 How It Works
Chess.com (Browser)
│
│ Tampermonkey reads board position
│
▼
POST http://127.0.0.1:5555/fen
│
▼
FEN Relay Server (fen_relay_server.py)
│
│ GET /fen
│
▼
Chess Assistant GUI (main.py)
│
▼
Stockfish Engine Analysis
│
▼
Best Move + Evaluation Display ✅

text


---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** — [Download](https://www.python.org/downloads/)
- **Stockfish** — [Download](https://stockfishchess.org/download/)
- **Tampermonkey** browser extension — [Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) | [Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/) | [Edge](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd)

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/chesstdev.git
cd chesstdev

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
Configure Stockfish
The tool auto-detects Stockfish in common locations. If not found:

Bash

# Option 1: Specify path when running
python main.py --stockfish "C:\path\to\stockfish.exe"

# Option 2: Edit config.py
# Change STOCKFISH_PATH to your Stockfish location
🎮 Usage
Method 1: GUI Mode (Recommended)
Open 3 terminals:

Terminal 1 — Start relay server:

Bash

python fen_relay_server.py
Terminal 2 — Start GUI:

Bash

python main.py
Browser — Install the Tampermonkey userscript (see below), then play on Chess.com.

In the GUI:

Click 🔄 Lấy FEN to fetch the current position
Click ▶ Analyze to get the best move
Click 📊 Top 3 to see top 3 candidate moves
Enable 🔁 Auto for automatic analysis
Method 2: CLI Mode
Bash

# Analyze a specific position
python main.py --fen "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

# Top 3 moves at depth 20
python main.py --fen "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3" --top 3 --depth 20

# Custom Stockfish path
python main.py --stockfish "/path/to/stockfish" --fen "..."
🌐 Tampermonkey Userscript Setup
Install Tampermonkey in your browser
Click the Tampermonkey icon → Create a new script
Delete all default code
Copy and paste the contents of the userscript from the Tampermonkey Userscript section below
Press Ctrl+S to save
Go to Chess.com and start a game
You should see a small panel at the bottom-right showing the current FEN
<details> <summary>📋 Click to expand the Tampermonkey Userscript</summary>
JavaScript

// ==UserScript==
// @name         Chess.com FEN Extractor v4
// @namespace    chesstdev
// @version      4.0
// @description  Extract FEN from Chess.com and send to local relay server
// @match        https://www.chess.com/*
// @grant        GM_xmlhttpRequest
// @grant        unsafeWindow
// @connect      127.0.0.1
// @connect      localhost
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    let lastFen = '';
    let sendCount = 0;
    let serverOK = false;

    const panel = document.createElement('div');
    panel.style.cssText = `
        position: fixed; bottom: 10px; right: 10px; z-index: 999999;
        background: #1a1a2e; color: #e0e0e0; padding: 10px 14px;
        font-family: 'Courier New', monospace; font-size: 11px;
        border-radius: 8px; max-width: 460px; word-break: break-all;
        border: 2px solid #333; cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    `;
    panel.innerHTML = 'Finding board...';
    document.body.appendChild(panel);

    panel.addEventListener('click', () => {
        const fen = panel.getAttribute('data-fen');
        if (fen) navigator.clipboard.writeText(fen);
    });

    function updatePanel(fen, method) {
        const srv = serverOK ? 'Server OK' : 'Server OFF';
        panel.setAttribute('data-fen', fen || '');
        if (fen) {
            panel.innerHTML = `FEN: ${fen}<br><small>${srv} | ${method} | #${sendCount}</small>`;
            panel.style.borderColor = serverOK ? '#4CAF50' : '#f44336';
        } else {
            panel.innerHTML = `No board found<br><small>${srv}</small>`;
            panel.style.borderColor = '#ff9800';
        }
    }

    function sendFEN(fen) {
        GM_xmlhttpRequest({
            method: 'POST',
            url: 'http://127.0.0.1:5555/fen',
            headers: { 'Content-Type': 'text/plain' },
            data: fen,
            timeout: 3000,
            onload: () => { sendCount++; serverOK = true; },
            onerror: () => { serverOK = false; },
            ontimeout: () => { serverOK = false; }
        });
    }

    function method_piecesFromDOM() {
        const board = document.querySelector('wc-chess-board');
        if (!board) return null;
        const pieces = board.querySelectorAll('.piece');
        if (pieces.length === 0) return null;
        const grid = Array.from({length: 8}, () => Array(8).fill(''));
        const map = {
            'wp':'P','wn':'N','wb':'B','wr':'R','wq':'Q','wk':'K',
            'bp':'p','bn':'n','bb':'b','br':'r','bq':'q','bk':'k'
        };
        for (const el of pieces) {
            const classes = el.className.split(/\s+/);
            let pc = '';
            for (const c of classes) { if (map[c]) { pc = map[c]; break; } }
            for (const c of classes) {
                const m = c.match(/^square-(\d)(\d)$/);
                if (m) {
                    grid[7 - (parseInt(m[2]) - 1)][parseInt(m[1]) - 1] = pc;
                    break;
                }
            }
        }
        let rows = [];
        for (let r = 0; r < 8; r++) {
            let row = '', empty = 0;
            for (let c = 0; c < 8; c++) {
                if (!grid[r][c]) { empty++; }
                else { if (empty) { row += empty; empty = 0; } row += grid[r][c]; }
            }
            if (empty) row += empty;
            rows.push(row);
        }
        const mn = document.querySelectorAll('.move-text-component, [data-ply]');
        const turn = (mn.length % 2 === 0) ? 'w' : 'b';
        return rows.join('/') + ' ' + turn + ' KQkq - 0 ' + Math.ceil((mn.length+1)/2);
    }

    setInterval(() => {
        const fen = method_piecesFromDOM();
        if (fen) {
            if (fen !== lastFen) { lastFen = fen; sendFEN(fen); }
            updatePanel(fen, 'DOM');
        } else {
            updatePanel(null, '');
        }
    }, 800);

    console.log('[FEN Extractor v4] Loaded');
})();
</details>
📁 Project Structure
text

chesstdev/
├── main.py                 # Entry point (GUI + CLI)
├── config.py               # Configuration (Stockfish path, settings)
├── engine_manager.py       # Stockfish UCI wrapper
├── fen_parser.py           # FEN provider (relay server, file, manual)
├── fen_relay_server.py     # Local HTTP server for browser communication
├── overlay_gui.py          # Tkinter always-on-top GUI
├── send_test.py            # Test script for relay server
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
⚙️ Configuration
Edit config.py to customize:

Setting	Default	Description
STOCKFISH_PATH	Auto-detect	Path to Stockfish binary
ENGINE_DEPTH	18	Analysis depth
ENGINE_TIME_LIMIT	2.0s	Max analysis time
ENGINE_THREADS	2	CPU threads for Stockfish
ENGINE_HASH_MB	128	Hash table size (MB)
RELAY_PORT	5555	Relay server port
🔧 Troubleshooting
Stockfish not found
Bash

# Specify path manually
python main.py --stockfish "C:\stockfish\stockfish-windows-x86-64-avx2.exe"
Relay server: "Address already in use"
Another instance is running. Close it or change the port in config.py.

Browser not sending FEN
Check Tampermonkey is enabled
Press F12 → Console on Chess.com, look for [FEN Extractor v4] Loaded
Make sure fen_relay_server.py is running
CORS errors
The relay server includes CORS headers. If issues persist, the Tampermonkey script uses GM_xmlhttpRequest which bypasses CORS entirely.

⚠️ Disclaimer
This tool is intended for learning and practice purposes only. Using it in rated games or tournaments on Chess.com violates their Fair Play Policy. Use responsibly.

📄 License
MIT License — see LICENSE file.

🤝 Contributing