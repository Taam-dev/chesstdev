// ==UserScript==
// @name         Chess.com FEN Relay
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  Bypass CSP and CORS to send real-time FEN and draw best move highlights on Chess.com.
// @author       Antigravity
// @match        *://*.chess.com/*
// @match        *://chess.com/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// @run-at       document-end
// ==/UserScript==

console.log('[ChesstDev] Script matched and loaded.');

(function(){
    let lastFen = '';
    let count = 0;

    // Direct extraction via Chess.com internal state if available
    function getFenFromState() {
        const board = document.querySelector('wc-chess-board') || document.querySelector('chess-board');
        if (board && board.game) {
            try {
                for (const method of ['getFen', 'getFEN', 'fen']) {
                    if (typeof board.game[method] === 'function') {
                        const f = board.game[method]();
                        if (f && typeof f === 'string' && f.includes('/')) return f;
                    }
                }
                if (typeof board.game.fen === 'string' && board.game.fen.includes('/')) {
                    return board.game.fen;
                }
            } catch (e) {
                console.log('[ChesstDev] Internal game state extraction error:', e);
            }
        }
        return null;
    }

    // DOM pieces scraper fallback
    function getPieces(){
        const b = document.querySelector('wc-chess-board') || document.querySelector('chess-board');
        if(!b) return null;
        
        // Handle Shadow DOM if present
        const root = b.shadowRoot || b;
        const ps = root.querySelectorAll('.piece');
        if(!ps.length) return null;

        const g = Array.from({length:8}, ()=>Array(8).fill(''));
        const m = {
            'wp':'P','wn':'N','wb':'B','wr':'R','wq':'Q','wk':'K',
            'bp':'p','bn':'n','bb':'b','br':'r','bq':'q','bk':'k'
        };

        for(const el of ps){
            const cls = el.className.split(/\s+/);
            let pc = '';
            for(const c of cls){ if(m[c]){ pc=m[c]; break; } }
            for(const c of cls){
                const mt = c.match(/^square-(\d)(\d)$/);
                if(mt){
                    g[7-(parseInt(mt[2])-1)][parseInt(mt[1])-1] = pc;
                    break;
                }
            }
        }

        let rows = [];
        for(let r=0; r<8; r++){
            let row='', empty=0;
            for(let c=0; c<8; c++){
                if(!g[r][c]){ empty++; }
                else { if(empty){ row+=empty; empty=0; } row+=g[r][c]; }
            }
            if(empty) row+=empty;
            rows.push(row);
        }

        // Detect current turn from plies list
        let turn = 'w';
        const plies = document.querySelectorAll('.move-text-component, [data-ply], .move-node');
        if (plies.length > 0) {
            turn = (plies.length % 2 === 0) ? 'w' : 'b';
        }

        // Calculate castling rights based on starting positions
        let castling = '';
        if (g[7][4] === 'K') { // White King on e1
            if (g[7][7] === 'R') castling += 'K'; // White Rook on h1
            if (g[7][0] === 'R') castling += 'Q'; // White Rook on a1
        }
        if (g[0][4] === 'k') { // Black King on e8
            if (g[0][7] === 'r') castling += 'k'; // Black Rook on h8
            if (g[0][0] === 'r') castling += 'q'; // Black Rook on a8
        }
        if (!castling) castling = '-';

        const moveNum = Math.ceil((plies.length + 1) / 2);
        return rows.join('/') + ' ' + turn + ' ' + castling + ' - 0 ' + moveNum;
    }

    function getFen() {
        return getFenFromState() || getPieces();
    }

    function sendFen(fen){
        const url = 'http://127.0.0.1:5555/set?fen=' + encodeURIComponent(fen) + '&t=' + Date.now();
        
        // Priority 1: Use Tampermonkey privileged API to bypass CORS/CSP
        if (typeof GM_xmlhttpRequest !== 'undefined') {
            GM_xmlhttpRequest({
                method: "GET",
                url: url,
                onload: function(response) {
                    // Success
                },
                onerror: function(err) {
                    console.error('[ChesstDev] GM_xmlhttpRequest failed:', err);
                }
            });
        } else {
            // Priority 2: Use fetch (No-CORS) if pasted directly in Console
            fetch(url, { mode: 'no-cors' })
                .catch(err => {
                    // Priority 3: Image trick as ultimate fallback
                    const img = new Image();
                    img.src = url;
                });
        }
    }

    // Highlight the best move directly on Chess.com chessboard
    function highlightMove(moveUci) {
        const board = document.querySelector('wc-chess-board') || document.querySelector('chess-board');
        if (!board) return;
        const root = board.shadowRoot || board;
        
        // Remove previous custom highlights
        root.querySelectorAll('.chesstdev-highlight').forEach(el => el.remove());
        
        if (!moveUci || moveUci === '—' || moveUci === 'none' || moveUci.length < 4) return;
        
        const fromSquare = moveUci.substring(0, 2);
        const toSquare = moveUci.substring(2, 4);
        
        const files = { a:1, b:2, c:3, d:4, e:5, f:6, g:7, h:8 };
        const ranks = { '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8 };
        
        const fromX = files[fromSquare[0]];
        const fromY = ranks[fromSquare[1]];
        const toX = files[toSquare[0]];
        const toY = ranks[toSquare[1]];
        
        if (!fromX || !fromY || !toX || !toY) return;
        
        const fromClass = `square-${fromX}${fromY}`;
        const toClass = `square-${toX}${toY}`;
        
        // Create starting square highlight (Blue)
        const hlFrom = document.createElement('div');
        hlFrom.className = `highlight chesstdev-highlight ${fromClass}`;
        hlFrom.style.backgroundColor = 'rgba(255, 0, 0, 0.35)'; // Red transparency for starting square
        hlFrom.style.opacity = '0.85';
        hlFrom.style.pointerEvents = 'none';
        
        // Create ending square highlight (Green)
        const hlTo = document.createElement('div');
        hlTo.className = `highlight chesstdev-highlight ${toClass}`;
        hlTo.style.backgroundColor = 'rgba(0, 255, 0, 0.35)'; // Green transparency for target square
        hlTo.style.opacity = '0.85';
        hlTo.style.pointerEvents = 'none';
        
        root.appendChild(hlFrom);
        root.appendChild(hlTo);
    }

    // Poll the relay server to get the calculated best move from Stockfish
    function pollBestMove() {
        const url = 'http://127.0.0.1:5555/bestmove?t=' + Date.now();
        if (typeof GM_xmlhttpRequest !== 'undefined') {
            GM_xmlhttpRequest({
                method: "GET",
                url: url,
                onload: function(response) {
                    highlightMove(response.responseText.trim());
                }
            });
        } else {
            fetch(url)
                .then(resp => resp.text())
                .then(text => highlightMove(text.trim()))
                .catch(err => {});
        }
    }

    if(window._chesstdevInterval) clearInterval(window._chesstdevInterval);

    window._chesstdevInterval = setInterval(()=>{
        const fen = getFen();
        if(fen && fen !== lastFen){
            lastFen = fen;
            count++;
            console.log('[ChesstDev #' + count + '] FEN: ' + fen);
            sendFen(fen);
        }
        pollBestMove();
    }, 1000);

    console.log('[ChesstDev] INITIALIZED - Relay and highlight polling active.');
})();