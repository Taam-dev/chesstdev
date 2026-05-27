import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { GameState, MoveRecord, ChessMove, MoveExplanation, EngineAnalysis } from '@/types'

interface GameStoreState extends GameState {
  isLoading: boolean
  error: string | null
  showAnnotations: boolean
}

const initialState: GameStoreState = {
  fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
  pgn: '',
  moves: [],
  currentMoveIndex: -1,
  orientation: 'white',
  gameStatus: 'playing',
  players: {
    white: { name: 'White', elo: undefined },
    black: { name: 'Black', elo: undefined },
  },
  isLoading: false,
  error: null,
  showAnnotations: true,
}

const gameSlice = createSlice({
  name: 'game',
  initialState,
  reducers: {
    setFen: (state, action: PayloadAction<string>) => {
      state.fen = action.payload
    },

    setPgn: (state, action: PayloadAction<string>) => {
      state.pgn = action.payload
    },

    addMove: (state, action: PayloadAction<MoveRecord>) => {
      // Remove future moves if we're not at the end
      if (state.currentMoveIndex < state.moves.length - 1) {
        state.moves = state.moves.slice(0, state.currentMoveIndex + 1)
      }
      state.moves.push(action.payload)
      state.currentMoveIndex = state.moves.length - 1
      state.fen = action.payload.fen
    },

    goToMove: (state, action: PayloadAction<number>) => {
      const index = action.payload
      if (index >= -1 && index < state.moves.length) {
        state.currentMoveIndex = index
        if (index === -1) {
          state.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        } else {
          state.fen = state.moves[index].fen
        }
      }
    },

    goToPreviousMove: (state) => {
      if (state.currentMoveIndex > -1) {
        state.currentMoveIndex -= 1
        if (state.currentMoveIndex === -1) {
          state.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        } else {
          state.fen = state.moves[state.currentMoveIndex].fen
        }
      }
    },

    goToNextMove: (state) => {
      if (state.currentMoveIndex < state.moves.length - 1) {
        state.currentMoveIndex += 1
        state.fen = state.moves[state.currentMoveIndex].fen
      }
    },

    goToFirstMove: (state) => {
      state.currentMoveIndex = -1
      state.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    },

    goToLastMove: (state) => {
      if (state.moves.length > 0) {
        state.currentMoveIndex = state.moves.length - 1
        state.fen = state.moves[state.currentMoveIndex].fen
      }
    },

    resetGame: (state) => {
      state.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
      state.pgn = ''
      state.moves = []
      state.currentMoveIndex = -1
      state.gameStatus = 'playing'
    },

    updateMoveExplanation: (
      state,
      action: PayloadAction<{ index: number; explanation: MoveExplanation }>
    ) => {
      const { index, explanation } = action.payload
      if (state.moves[index]) {
        state.moves[index].explanation = explanation
      }
    },

    updateMoveAnalysis: (
      state,
      action: PayloadAction<{ index: number; analysis: EngineAnalysis }>
    ) => {
      const { index, analysis } = action.payload
      if (state.moves[index]) {
        state.moves[index].analysis = analysis
        state.moves[index].quality = classifyMoveQuality(analysis)
      }
    },

    setOrientation: (state, action: PayloadAction<'white' | 'black'>) => {
      state.orientation = action.payload
    },

    setPlayers: (state, action: PayloadAction<GameState['players']>) => {
      state.players = action.payload
    },

    setShowAnnotations: (state, action: PayloadAction<boolean>) => {
      state.showAnnotations = action.payload
    },

    loadGame: (state, action: PayloadAction<Partial<GameStoreState>>) => {
      return { ...state, ...action.payload }
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
  },
})

// Helper function to classify move quality
function classifyMoveQuality(analysis: EngineAnalysis) {
  const { evaluation } = analysis
  // This is simplified - real classification compares with best move eval
  return undefined // Will be set by analysis pipeline
}

export const {
  setFen,
  setPgn,
  addMove,
  goToMove,
  goToPreviousMove,
  goToNextMove,
  goToFirstMove,
  goToLastMove,
  resetGame,
  updateMoveExplanation,
  updateMoveAnalysis,
  setOrientation,
  setPlayers,
  setShowAnnotations,
  loadGame,
  setError,
} = gameSlice.actions

export default gameSlice.reducer