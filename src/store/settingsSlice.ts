import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { EngineSettings, AppSettings } from '@/types'

interface SettingsState {
  engine: EngineSettings
  app: AppSettings
  isLoaded: boolean
}

const initialState: SettingsState = {
  engine: {
    path: '',
    depth: 20,
    threads: 2,
    hash: 256,
    multiPV: 3,
    skillLevel: 20,
    contempt: 0,
    useNNUE: true,
    syzygyPath: undefined,
    moveOverhead: 10,
  },
  app: {
    showAnnotations: true,
    showArrows: true,
    showHeatmap: false,
    autoAnalyze: true,
    soundEnabled: true,
    animationSpeed: 'normal',
    theme: 'dark',
    boardTheme: 'green',
    pieceSet: 'cburnett',
    language: 'en',
  },
  isLoaded: false,
}

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setEngineSettings: (state, action: PayloadAction<Partial<EngineSettings>>) => {
      state.engine = { ...state.engine, ...action.payload }
    },

    setAppSettings: (state, action: PayloadAction<Partial<AppSettings>>) => {
      state.app = { ...state.app, ...action.payload }
    },

    setEnginePath: (state, action: PayloadAction<string>) => {
      state.engine.path = action.payload
    },

    setEngineDepth: (state, action: PayloadAction<number>) => {
      state.engine.depth = Math.min(Math.max(action.payload, 1), 30)
    },

    setEngineThreads: (state, action: PayloadAction<number>) => {
      state.engine.threads = Math.min(Math.max(action.payload, 1), 32)
    },

    setEngineHash: (state, action: PayloadAction<number>) => {
      state.engine.hash = action.payload
    },

    setMultiPV: (state, action: PayloadAction<number>) => {
      state.engine.multiPV = Math.min(Math.max(action.payload, 1), 5)
    },

    setSkillLevel: (state, action: PayloadAction<number>) => {
      state.engine.skillLevel = Math.min(Math.max(action.payload, 0), 20)
    },

    toggleShowAnnotations: (state) => {
      state.app.showAnnotations = !state.app.showAnnotations
    },

    toggleShowArrows: (state) => {
      state.app.showArrows = !state.app.showArrows
    },

    toggleShowHeatmap: (state) => {
      state.app.showHeatmap = !state.app.showHeatmap
    },

    toggleAutoAnalyze: (state) => {
      state.app.autoAnalyze = !state.app.autoAnalyze
    },

    toggleSound: (state) => {
      state.app.soundEnabled = !state.app.soundEnabled
    },

    setTheme: (state, action: PayloadAction<'dark' | 'light'>) => {
      state.app.theme = action.payload
    },

    setBoardTheme: (state, action: PayloadAction<string>) => {
      state.app.boardTheme = action.payload
    },

    setPieceSet: (state, action: PayloadAction<string>) => {
      state.app.pieceSet = action.payload
    },

    setLanguage: (state, action: PayloadAction<'en' | 'vi'>) => {
      state.app.language = action.payload
    },

    setAnimationSpeed: (state, action: PayloadAction<AppSettings['animationSpeed']>) => {
      state.app.animationSpeed = action.payload
    },

    loadSettings: (state, action: PayloadAction<Partial<SettingsState>>) => {
      return { ...state, ...action.payload, isLoaded: true }
    },

    markLoaded: (state) => {
      state.isLoaded = true
    },
  },
})

export const {
  setEngineSettings,
  setAppSettings,
  setEnginePath,
  setEngineDepth,
  setEngineThreads,
  setEngineHash,
  setMultiPV,
  setSkillLevel,
  toggleShowAnnotations,
  toggleShowArrows,
  toggleShowHeatmap,
  toggleAutoAnalyze,
  toggleSound,
  setTheme,
  setBoardTheme,
  setPieceSet,
  setLanguage,
  setAnimationSpeed,
  loadSettings,
  markLoaded,
} = settingsSlice.actions

export default settingsSlice.reducer