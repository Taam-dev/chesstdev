import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { EngineAnalysis, TacticPattern, MoveExplanation } from '@/types'

interface AnalysisState {
  current: EngineAnalysis | null
  isAnalyzing: boolean
  isEngineReady: boolean
  enginePath: string
  depth: number
  multiPV: number
  tactics: TacticPattern[]
  currentExplanation: MoveExplanation | null
  analysisMode: 'realtime' | 'manual' | 'game'
  showAnnotationsMode: boolean // Chess.com style
  backendConnected: boolean
  error: string | null
}

const initialState: AnalysisState = {
  current: null,
  isAnalyzing: false,
  isEngineReady: false,
  enginePath: '',
  depth: 20,
  multiPV: 3,
  tactics: [],
  currentExplanation: null,
  analysisMode: 'realtime',
  showAnnotationsMode: false,
  backendConnected: false,
  error: null,
}

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setAnalysis: (state, action: PayloadAction<EngineAnalysis>) => {
      state.current = action.payload
      state.isAnalyzing = action.payload.isAnalyzing
    },

    setIsAnalyzing: (state, action: PayloadAction<boolean>) => {
      state.isAnalyzing = action.payload
      if (state.current) {
        state.current.isAnalyzing = action.payload
      }
    },

    setEngineReady: (state, action: PayloadAction<boolean>) => {
      state.isEngineReady = action.payload
    },

    setEnginePath: (state, action: PayloadAction<string>) => {
      state.enginePath = action.payload
    },

    setDepth: (state, action: PayloadAction<number>) => {
      state.depth = action.payload
    },

    setMultiPV: (state, action: PayloadAction<number>) => {
      state.multiPV = action.payload
    },

    setTactics: (state, action: PayloadAction<TacticPattern[]>) => {
      state.tactics = action.payload
    },

    setCurrentExplanation: (state, action: PayloadAction<MoveExplanation | null>) => {
      state.currentExplanation = action.payload
    },

    setAnalysisMode: (state, action: PayloadAction<AnalysisState['analysisMode']>) => {
      state.analysisMode = action.payload
    },

    toggleAnnotationsMode: (state) => {
      state.showAnnotationsMode = !state.showAnnotationsMode
    },

    setAnnotationsMode: (state, action: PayloadAction<boolean>) => {
      state.showAnnotationsMode = action.payload
    },

    setBackendConnected: (state, action: PayloadAction<boolean>) => {
      state.backendConnected = action.payload
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },

    clearAnalysis: (state) => {
      state.current = null
      state.isAnalyzing = false
      state.tactics = []
      state.currentExplanation = null
    },
  },
})

export const {
  setAnalysis,
  setIsAnalyzing,
  setEngineReady,
  setEnginePath,
  setDepth,
  setMultiPV,
  setTactics,
  setCurrentExplanation,
  setAnalysisMode,
  toggleAnnotationsMode,
  setAnnotationsMode,
  setBackendConnected,
  setError,
  clearAnalysis,
} = analysisSlice.actions

export default analysisSlice.reducer