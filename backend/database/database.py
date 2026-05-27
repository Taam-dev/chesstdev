"""
Database - SQLite async database for saving games and analysis
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Optional
import time

logger = logging.getLogger(__name__)

try:
    import aiosqlite

    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False
    logger.warning("aiosqlite not installed - database unavailable")


class Database:
    """
    Async SQLite database for ChessCoach.
    Stores saved games, analysis data, and settings.
    """

    DB_PATH = Path.home() / ".chesstdev" / "games.db"

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DB_PATH
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Create database and tables"""
        if not HAS_AIOSQLITE:
            logger.warning("Database unavailable - aiosqlite not installed")
            return

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = aiosqlite.Row

        # Enable WAL mode for better performance
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA synchronous=NORMAL")

        await self._create_tables()
        logger.info(f"Database initialized: {self.db_path}")

    async def _create_tables(self) -> None:
        """Create all required tables"""
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                id          TEXT PRIMARY KEY,
                pgn         TEXT NOT NULL,
                fen         TEXT,
                white       TEXT DEFAULT 'White',
                black       TEXT DEFAULT 'Black',
                white_elo   INTEGER,
                black_elo   INTEGER,
                result      TEXT DEFAULT '*',
                event       TEXT DEFAULT 'ChessCoach',
                date        TEXT,
                analysis    TEXT,
                tags        TEXT DEFAULT '[]',
                created_at  INTEGER NOT NULL,
                updated_at  INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_games_created
                ON games (created_at DESC);

            CREATE TABLE IF NOT EXISTS positions (
                id          TEXT PRIMARY KEY,
                fen         TEXT NOT NULL UNIQUE,
                analysis    TEXT,
                depth       INTEGER DEFAULT 0,
                created_at  INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_positions_fen
                ON positions (fen);

            CREATE TABLE IF NOT EXISTS settings (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                updated_at  INTEGER NOT NULL
            );
        """)
        await self._db.commit()

    # ─── Games ───────────────────────────────────────────────────────────────────

    async def save_game(self, pgn: str, metadata: Optional[dict] = None) -> str:
        """Save a game to the database"""
        if not self._db:
            raise RuntimeError("Database not initialized")

        game_id = str(uuid.uuid4())
        now = int(time.time() * 1000)
        meta = metadata or {}

        await self._db.execute(
            """
            INSERT INTO games
                (id, pgn, fen, white, black, white_elo, black_elo,
                 result, event, date, tags, created_at, updated_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_id,
                pgn,
                meta.get("fen", ""),
                meta.get("white", "White"),
                meta.get("black", "Black"),
                meta.get("whiteElo"),
                meta.get("blackElo"),
                meta.get("result", "*"),
                meta.get("event", "ChessCoach"),
                meta.get("date", ""),
                json.dumps(meta.get("tags", [])),
                now,
                now,
            ),
        )
        await self._db.commit()
        logger.info(f"Saved game: {game_id}")
        return game_id

    async def get_games(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get list of saved games"""
        if not self._db:
            return []

        async with self._db.execute(
            """
            SELECT id, pgn, fen, white, black, white_elo, black_elo,
                   result, event, date, tags, created_at, updated_at
            FROM games
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            {
                "id": row["id"],
                "pgn": row["pgn"],
                "fen": row["fen"] or "",
                "white": row["white"],
                "black": row["black"],
                "whiteElo": row["white_elo"],
                "blackElo": row["black_elo"],
                "result": row["result"],
                "event": row["event"],
                "date": row["date"] or "",
                "tags": json.loads(row["tags"] or "[]"),
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]

    async def get_game(self, game_id: str) -> Optional[dict]:
        """Get a specific game by ID"""
        if not self._db:
            return None

        async with self._db.execute(
            "SELECT * FROM games WHERE id = ?", (game_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        return dict(row)

    async def delete_game(self, game_id: str) -> bool:
        """Delete a game"""
        if not self._db:
            return False

        await self._db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        await self._db.commit()
        return True

    async def update_game_analysis(self, game_id: str, analysis: dict) -> bool:
        """Update analysis data for a game"""
        if not self._db:
            return False

        now = int(time.time() * 1000)
        await self._db.execute(
            "UPDATE games SET analysis = ?, updated_at = ? WHERE id = ?",
            (json.dumps(analysis), now, game_id),
        )
        await self._db.commit()
        return True

    # ─── Position Cache ───────────────────────────────────────────────────────────

    async def cache_position(self, fen: str, analysis: dict, depth: int) -> None:
        """Cache analysis result for a position"""
        if not self._db:
            return

        pos_id = str(uuid.uuid4())
        now = int(time.time() * 1000)

        await self._db.execute(
            """
            INSERT INTO positions (id, fen, analysis, depth, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fen) DO UPDATE SET
                analysis = excluded.analysis,
                depth = excluded.depth
            WHERE excluded.depth > positions.depth
            """,
            (pos_id, fen, json.dumps(analysis), depth, now),
        )
        await self._db.commit()

    async def get_cached_position(self, fen: str, min_depth: int = 0) -> Optional[dict]:
        """Get cached analysis for a position"""
        if not self._db:
            return None

        async with self._db.execute(
            "SELECT analysis, depth FROM positions WHERE fen = ? AND depth >= ?",
            (fen, min_depth),
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            return json.loads(row["analysis"])
        return None

    # ─── Settings ─────────────────────────────────────────────────────────────────

    async def save_setting(self, key: str, value) -> None:
        """Save a setting value"""
        if not self._db:
            return

        now = int(time.time() * 1000)
        await self._db.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, json.dumps(value), now),
        )
        await self._db.commit()

    async def get_setting(self, key: str, default=None):
        """Get a setting value"""
        if not self._db:
            return default

        async with self._db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            return json.loads(row["value"])
        return default

    # ─── Cleanup ──────────────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close database connection"""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Database closed")
