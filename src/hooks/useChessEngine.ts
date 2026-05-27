import { useEffect, useCallback, useRef } from 'react'
import { useAppDispatch, useAppSelector } from '@/store'
import {
  setAnalysis,
  setIsAnalyzing,
  setEngineReady,
  setTactics,
  setCurrentExplanation,
  setBackendConnected,
  setError,
} from '@/store/analysisSlice'
import { engineService } from '@/services/engineService'
import { EngineAnalysis } from '@/types'

export function useChessEngine() {
  const dispatch = useAppDispatch()
  const { depth, multiPV, isEngineReady, isAnalyzing, backendConnected } =
    useAppSelector((state) => state.analysis)
  const { engine: engineSettings } = useAppSelector((state) => state.settings)
  const initializedRef = useRef(false)

  // ─── Initialize engine service ──────────────────────────────────────────────

  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    const init = async () => {
      await engineService.initialize()
      dispatch(setBackendConnected(engineService.connected))
    }

    init()

    // Subscribe to engine events
    const unsubAnalysis = engineService.onAnalysis((analysis: EngineAnalysis) => {
      dispatch(setAnalysis(analysis))
      dispatch(setIsAnalyzing(analysis.isAnalyzing))
    })

    const unsubStatus = engineService.onStatusChange((ready: boolean) => {
      dispatch(setEngineReady(ready))
      dispatch(setBackendConnected(true))
    })

    const unsubTactics = engineService.onTactics((tactics) => {
      dispatch(setTactics(tactics))
    })

    const unsubExplanation = engineService.onExplanation((explanation) => {
      dispatch(setCurrentExplanation(explanation))
    })

    const unsubError = engineService.onError((error: string) => {
      dispatch(setError(error))
      dispatch(setIsAnalyzing(false))
    })

    return () => {
      unsubAnalysis()
      unsubStatus()
      unsubTactics()
      unsubExplanation()
      unsubError()
    }
  }, [dispatch])

  // ─── Analyze position ────────────────────────────────────────────────────────

  const analyzePosition = useCallback(
    async (fen: string) => {
      if (!fen) return
      dispatch(setIsAnalyzing(true))
      dispatch(setError(null))
      await engineService.analyzePosition(fen, depth, multiPV)
    },
    [depth, multiPV, dispatch]
  )

  const stopAnalysis = useCallback(async () => {
    await engineService.stopAnalysis()
    dispatch(setIsAnalyzing(false))
  }, [dispatch])

  // ─── Apply settings to engine ────────────────────────────────────────────────

  const applyEngineSettings = useCallback(async () => {
    await engineService.setThreads(engineSettings.threads)
    await engineService.setHash(engineSettings.hash)
    await engineService.setMultiPV(engineSettings.multiPV)
    await engineService.setSkillLevel(engineSettings.skillLevel)
  }, [engineSettings])

  // ─── Coach features ──────────────────────────────────────────────────────────

  const explainMove = useCallback(
    async (fen: string, move: string, analysis: EngineAnalysis) => {
      const explanation = await engineService.explainMove(fen, move, analysis)
      if (explanation) {
        dispatch(setCurrentExplanation(explanation))
      }
      return explanation
    },
    [dispatch]
  )

  const detectTactics = useCallback(
    async (fen: string) => {
      const tactics = await engineService.detectTactics(fen)
      dispatch(setTactics(tactics))
      return tactics
    },
    [dispatch]
  )

  return {
    // State
    isEngineReady,
    isAnalyzing,
    backendConnected,
    // Actions
    analyzePosition,
    stopAnalysis,
    applyEngineSettings,
    explainMove,
    detectTactics,
  }
}