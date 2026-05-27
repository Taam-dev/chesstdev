"""
Database Models - Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GameSaveRequest(BaseModel):
    pgn: str
    metadata: dict = Field(default_factory=dict)


class GameResponse(BaseModel):
    id: str
    pgn: str
    fen: str = ""
    white: str = "White"
    black: str = "Black"
    white_elo: Optional[int] = None
    black_elo: Optional[int] = None
    result: str = "*"
    event: str = "ChessCoach"
    date: str = ""
    tags: List[str] = Field(default_factory=list)
    created_at: int
    updated_at: int


class AnalyzeRequest(BaseModel):
    fen: str
    depth: int = Field(default=20, ge=1, le=30)
    multi_pv: int = Field(default=3, ge=1, le=5)


class ExplainMoveRequest(BaseModel):
    fen: str
    move: str
    analysis: dict = Field(default_factory=dict)


class CaptureRequest(BaseModel):
    region: Optional[dict] = None


class CalibrationRequest(BaseModel):
    image_data: str  # base64 encoded


class EngineOptionRequest(BaseModel):
    option: str
    value: str | int | bool
