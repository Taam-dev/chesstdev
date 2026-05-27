"""
ChessCoach Local - Python FastAPI Backend
Main entry point - starts WebSocket server + HTTP API
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.stockfish_manager import StockfishManager
from engine.analysis_pipeline import AnalysisPipeline
from coach.move_explainer import MoveExplainer
from coach.tactics_detector import TacticsDetector
from coach.move_classifier import MoveClassifier
from database.database import Database
from recognition.screen_capture import ScreenCapture
from utils.helpers import setup_logging

# ─── Logging Setup ──────────────────────────────────────────────────────────

setup_logging()
logger = logging.getLogger(__name__)

# ─── Global State ────────────────────────────────────────────────────────────

stockfish: StockfishManager = None
analysis_pipeline: AnalysisPipeline = None
move_explainer: MoveExplainer = None
tactics_detector: TacticsDetector = None
move_classifier: MoveClassifier = None
database: Database = None
screen_capture: ScreenCapture = None

# Connected WebSocket clients
ws_clients: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    global stockfish, analysis_pipeline, move_explainer
    global tactics_detector, move_classifier, database, screen_capture

    logger.info("🚀 Starting ChessCoach Local backend...")

    # Initialize database
    database = Database()
    await database.initialize()
    logger.info("✅ Database initialized")

    # Initialize Stockfish
    engine_path = os.environ.get("ENGINE_PATH", "")
    stockfish = StockfishManager(engine_path=engine_path)
    if await stockfish.initialize():
        logger.info(f"✅ Stockfish initialized: {stockfish.engine_path}")
    else:
        logger.warning("⚠️ Stockfish not found - analysis unavailable")

    # Initialize analysis pipeline
    analysis_pipeline = AnalysisPipeline(stockfish)

    # Initialize coach components
    move_explainer = MoveExplainer()
    tactics_detector = TacticsDetector()
    move_classifier = MoveClassifier()

    # Initialize screen capture
    screen_capture = ScreenCapture()

    logger.info("✅ All systems ready!")

    yield

    # Cleanup
    logger.info("Shutting down...")
    if stockfish:
        await stockfish.shutdown()
    if database:
        await database.close()


# ─── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="ChessCoach Local API",
    description="Local chess analysis backend powered by Stockfish NNUE",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helper: Broadcast to all WebSocket clients ───────────────────────────────

async def broadcast(message: dict):
    """Send message to all connected WebSocket clients"""
    if not ws_clients:
        return
    data = json.dumps(message)
    disconnected = set()
    for client in ws_clients:
        try:
            await client.send_text(data)
        except Exception:
            disconnected.add(client)
    ws_clients -= disconnected


async def send_to_client(ws: WebSocket, msg_type: str, data: dict):
    """Send message to specific client"""
    await ws.send_text(json.dumps({
        "type": msg_type,
        "data": data,
        "timestamp": asyncio.get_event_loop().time(),
    }))


# ─── WebSocket Endpoint ────────────────────────────────────────────────────────

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    logger.info(f"Client connected. Total: {len(ws_clients)}")

    # Send initial status
    await send_to_client(websocket, "engine_ready", {
        "ready": stockfish.is_ready if stockfish else False,
        "engine_path": stockfish.engine_path if stockfish else "",
        "version": stockfish.version if stockfish else "Unknown",
    })

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            await handle_ws_message(websocket, message)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_clients.discard(websocket)


async def handle_ws_message(ws: WebSocket, message: dict):
    """Route WebSocket messages to handlers"""
    msg_type = message.get("type")
    data = message.get("data", {})
    request_id = message.get("requestId")

    logger.debug(f"WS message: {msg_type}")

    if msg_type == "ping":
        await send_to_client(ws, "pong", {"timestamp": asyncio.get_event_loop().time()})

    elif msg_type == "analyze":
        await handle_analyze(ws, data, request_id)

    elif msg_type == "stop_analysis":
        if analysis_pipeline:
            await analysis_pipeline.stop()
        await send_to_client(ws, "analysis_update", {"isAnalyzing": False})

    elif msg_type == "set_option":
        if stockfish:
            option = data.get("option")
            value = data.get("value")
            await stockfish.set_option(option, value)

    elif msg_type == "start_webcam":
        await handle_start_webcam(ws, data)

    elif msg_type == "stop_webcam":
        if screen_capture:
            screen_capture.stop_webcam()

    else:
        logger.warning(f"Unknown message type: {msg_type}")


async def handle_analyze(ws: WebSocket, data: dict, request_id: str = None):
    """Handle position analysis request"""
    fen = data.get("fen", "")
    depth = min(data.get("depth", 20), 30)  # Cap at depth 30
    multi_pv = min(data.get("multiPV", 3), 5)

    if not stockfish or not stockfish.is_ready:
        await send_to_client(ws, "engine_error", {
            "message": "Engine not available. Check Stockfish installation."
        })
        return

    if not analysis_pipeline:
        return

    async def on_update(analysis_data: dict):
        """Callback for each engine update"""
        await send_to_client(ws, "analysis_update", analysis_data)

    try:
        result = await analysis_pipeline.analyze(
            fen=fen,
            depth=depth,
            multi_pv=multi_pv,
            callback=on_update,
        )

        if result:
            await send_to_client(ws, "analysis_complete", result)

            # Auto-detect tactics
            if tactics_detector:
                tactics = await tactics_detector.detect(fen, result)
                if tactics:
                    await send_to_client(ws, "tactics_detected", tactics)

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await send_to_client(ws, "engine_error", {"message": str(e)})


async def handle_start_webcam(ws: WebSocket, data: dict):
    """Start webcam board detection"""
    if not screen_capture:
        return

    device_index = data.get("deviceIndex", 0)

    async def on_recognition(result: dict):
        await send_to_client(ws, "recognition_result", result)

    await screen_capture.start_webcam(device_index, callback=on_recognition)


# ─── HTTP Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "engine": stockfish.is_ready if stockfish else False,
        "version": "1.0.0",
    }


@app.get("/engine-info")
async def get_engine_info():
    if not stockfish:
        return {"error": "Engine not initialized"}
    return {
        "path": stockfish.engine_path,
        "version": stockfish.version,
        "ready": stockfish.is_ready,
        "options": stockfish.get_options(),
    }


@app.get("/benchmark")
async def run_benchmark():
    if not stockfish:
        return {"error": "Engine not available"}
    result = await stockfish.benchmark()
    return result


@app.post("/explain-move")
async def explain_move(request: dict):
    """Generate human-language move explanation"""
    fen = request.get("fen", "")
    move = request.get("move", "")
    analysis = request.get("analysis", {})

    if not move_explainer:
        return {"error": "Move explainer not initialized"}

    try:
        explanation = await move_explainer.explain(fen, move, analysis)
        return explanation
    except Exception as e:
        logger.error(f"Explanation error: {e}")
        return {"error": str(e)}


@app.post("/detect-tactics")
async def detect_tactics(request: dict):
    """Detect tactical patterns in position"""
    fen = request.get("fen", "")
    analysis = request.get("analysis", {})

    if not tactics_detector:
        return []

    try:
        tactics = await tactics_detector.detect(fen, analysis)
        return tactics
    except Exception as e:
        logger.error(f"Tactics detection error: {e}")
        return []


@app.post("/capture-screen")
async def capture_screen(request: dict):
    """Capture and analyze screen for chess board"""
    region = request.get("region")

    if not screen_capture:
        return {"error": "Screen capture not available"}

    try:
        result = await screen_capture.capture_and_analyze(region)
        return result
    except Exception as e:
        logger.error(f"Screen capture error: {e}")
        return {"error": str(e)}


@app.post("/calibrate-board")
async def calibrate_board(request: dict):
    """Calibrate board detection"""
    image_data = request.get("imageData", "")

    if not screen_capture:
        return {"error": "Screen capture not available"}

    corners = await screen_capture.calibrate(image_data)
    return {"corners": corners}


@app.post("/save-game")
async def save_game(request: dict):
    """Save game to database"""
    if not database:
        return {"error": "Database not available"}

    game_id = await database.save_game(
        pgn=request.get("pgn", ""),
        metadata=request.get("metadata", {}),
    )
    return {"id": game_id}


@app.get("/games")
async def get_games():
    """List saved games"""
    if not database:
        return []
    return await database.get_games()


@app.delete("/games/{game_id}")
async def delete_game(game_id: str):
    """Delete a saved game"""
    if not database:
        return {"error": "Database not available"}
    await database.delete_game(game_id)
    return {"success": True}


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    logger.info(f"Starting server on port {port}")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        ws_ping_interval=30,
        ws_ping_timeout=10,
    )