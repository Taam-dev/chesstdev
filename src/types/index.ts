// ─── Chess Types ──────────────────────────────────────────────────────────────

export interface ChessMove {
  from: string
  to: string
  promotion?: string
  san?: string
  lan?: string
}

export interface AnalysisLine {
  moves: string[]
  evaluation: number
  mate?: number
  depth: number
  multiPV: number
}

export interface MoveQualityType {
  label: 'brilliant' | 'great' | 'best' | 'good' | 'inaccuracy' | 'mistake' | 'blunder' | 'miss'
  symbol: string
  color: string
  description: string
  scoreDiff: number
}

export interface MoveExplanation {
  move: string
  san: string
  quality: MoveQualityType
  tactical: string
  strategic: string
  positional: string
  threats: string
  weaknesses: string
  risks: string
  summary: string
  tactics: TacticPattern[]
}

export interface TacticPattern {
  type: TacticType
  description: string
  squares: string[]
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export type TacticType =
  | 'fork'
  | 'pin'
  | 'skewer'
  | 'discovered_attack'
  | 'discovered_check'
  | 'double_check'
  | 'mating_net'
  | 'hanging_piece'
  | 'passed_pawn'
  | 'weak_square'
  | 'open_file'
  | 'back_rank'
  | 'zwischenzug'
  | 'zugzwang'

export interface EngineAnalysis {
  fen: string
  depth: number
  evaluation: number
  mate?: number
  bestMove: string
  bestMoveSAN: string
  principalVariation: string[]
  lines: AnalysisLine[]
  nodes: number
  nps: number
  time: number
  isAnalyzing: boolean
}

export interface GameState {
  fen: string
  pgn: string
  moves: MoveRecord[]
  currentMoveIndex: number
  orientation: 'white' | 'black'
  gameStatus: 'playing' | 'checkmate' | 'stalemate' | 'draw' | 'resigned'
  players: {
    white: { name: string; elo?: number }
    black: { name: string; elo?: number }
  }
}

export interface MoveRecord {
  index: number
  move: ChessMove
  san: string
  fen: string
  fenBefore: string
  analysis?: EngineAnalysis
  explanation?: MoveExplanation
  timestamp: number
  annotation?: string
  quality?: MoveQualityType
}

export interface EngineSettings {
  path: string
  depth: number
  threads: number
  hash: number
  multiPV: number
  skillLevel: number // 0-20 (20 = maximum strength)
  contempt: number
  useNNUE: boolean
  syzygyPath?: string
  moveOverhead: number
}

export interface AppSettings {
  showAnnotations: boolean // Chess.com style move badges
  showArrows: boolean
  showHeatmap: boolean
  autoAnalyze: boolean
  soundEnabled: boolean
  animationSpeed: 'slow' | 'normal' | 'fast'
  theme: 'dark' | 'light'
  boardTheme: string
  pieceSet: string
  language: 'en' | 'vi'
}

// ─── WebSocket Message Types ─────────────────────────────────────────────────

export type WSMessageType =
  | 'analysis_update'
  | 'analysis_complete'
  | 'engine_ready'
  | 'engine_error'
  | 'recognition_result'
  | 'explanation_ready'
  | 'tactics_detected'
  | 'error'
  | 'ping'
  | 'pong'

export interface WSMessage {
  type: WSMessageType
  data: unknown
  timestamp: number
  requestId?: string
}

// ─── Recognition Types ───────────────────────────────────────────────────────

export interface RecognitionResult {
  fen: string
  confidence: number
  squares: Record<string, string>
  turn: 'w' | 'b'
  mode: 'screen' | 'webcam'
  timestamp: number
}

export interface CalibrationData {
  x: number
  y: number
  width: number
  height: number
  screenId?: string
}

// ─── Database Types ──────────────────────────────────────────────────────────

export interface SavedGame {
  id: string
  pgn: string
  fen: string
  white: string
  black: string
  result: string
  event: string
  date: string
  analysisData?: string
  createdAt: number
  updatedAt: number
  tags: string[]
}