import { useEffect, useCallback, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '@/store'
import {
  setAnalysis,
  setIsAnalyzing,
  setEngineReady,
  setTactics,
  setCurrentExplanation,
  setBackendConnected,
  setError,
} from '@/store/analysisSlice'
import { updateMoveExplanation, updateMoveAnalysis } from '@/store/gameSlice'
import { apiService } from '@/services/apiService'
import { EngineAnalysis, TacticPattern, MoveExplanation } from '@/types'

export function useAnalysis() {
  const dispatch = useDispatch()
  const {
    current,
    isAnalyzing,
    isEngineReady,
    depth,
    multiPV,
    backendConnected,
  } = useSelector((state: RootState) => state.analysis)
  const { fen, moves, currentMoveIndex } = useSelector(
    (state: RootState) => state.game
  )
  const analysisTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const currentFenRef = useRef(fen)

  // ─── Backend Connection ─────────────────────────────────────────────────────

  useEffect(() => {
    let retries = 0
    const maxRetries = 10
    let cancelled = false

    const connectWithRetry = async () => {
      if (cancelled) return
      try {
        await apiService.connect()
        if (!cancelled) {
          dispatch(setBackendConnected(true))
          dispatch(setError(null))
        }
      } catch {
        retries++
        if (!cancelled && retries < maxRetries) {
          setTimeout(connectWithRetry, 2000)
        } else if (!cancelled) {
          dispatch(
            setError('Cannot connect to analysis engine. Is the backend running?')
          )
        }
      }
    }

    connectWithRetry()

    return () => {
      cancelled = true
      apiService.disconnect()
    }
  }, [dispatch])

  // ─── Subscribe to Engine Events ─────────────────────────────────────────────

  useEffect(() => {
    const cleanups = [
      apiService.on('analysis_update', (data) => {
        dispatch(setAnalysis(data as EngineAnalysis))
      }),
      apiService.on('analysis_complete', (data) => {
        const analysis = data as EngineAnalysis
        analysis.isAnalyzing = false
        dispatch(setAnalysis(analysis))
        dispatch(setIsAnalyzing(false))
      }),
      apiService.on('engine_ready', (data) => {
        const { ready } = data as { ready: boolean }
        dispatch(setEngineReady(ready))
      }),
      apiService.on('engine_error', (data) => {
        const { message } = data as { message: string }
        dispatch(setError(message))
        dispatch(setEngineReady(false))
        dispatch(setIsAnalyzing(false))
      }),
      apiService.on('tactics_detected', (data) => {
        dispatch(setTactics(data as TacticPattern[]))
      }),
      apiService.on('explanation_ready', (data) => {
        dispatch(setCurrentExplanation(data as MoveExplanation))
      }),
    ]

    return () => cleanups.forEach((fn) => fn())
  }, [dispatch])

  // ─── Auto-analyze on Position Change ────────────────────────────────────────

  useEffect(() => {
    currentFenRef.current = fen
    if (!backendConnected || !isEngineReady) return

    if (analysisTimeoutRef.current) {
      clearTimeout(analysisTimeoutRef.current)
    }

    analysisTimeoutRef.current = setTimeout(() => {
      if (currentFenRef.current === fen) {
        analyzePosition(fen)
      }
    }, 300)

    return () => {
      if (analysisTimeoutRef.current) {
        clearTimeout(analysisTimeoutRef.current)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fen, backendConnected, isEngineReady, depth, multiPV])

  // ─── Actions ────────────────────────────────────────────────────────────────

  const analyzePosition = useCallback(
    async (fenToAnalyze?: string) => {
      const targetFen = fenToAnalyze ?? fen
      if (!backendConnected) return
      dispatch(setIsAnalyzing(true))
      try {
        await apiService.analyzePosition(targetFen, depth, multiPV)
      } catch (err) {
        dispatch(setError(`Analysis failed: ${err}`))
        dispatch(setIsAnalyzing(false))
      }
    },
    [fen, depth, multiPV, backendConnected, dispatch]
  )

  const stopAnalysis = useCallback(async () => {
    await apiService.stopAnalysis()
    dispatch(setIsAnalyzing(false))
  }, [dispatch])

  const explainMove = useCallback(
    async (moveIndex: number) => {
      if (moveIndex < 0 || moveIndex >= moves.length) return
      if (!current) return

      const move = moves[moveIndex]
      try {
        const explanation = await apiService.explainMove(
          move.fenBefore,
          move.san,
          current
        )
        dispatch(updateMoveExplanation({ index: moveIndex, explanation }))
        dispatch(setCurrentExplanation(explanation))
      } catch (err) {
        console.error('Failed to get explanation:', err)
      }
    },
    [moves, current, dispatch]
  )

  const detectTactics = useCallback(async () => {
    try {
      const tactics = await apiService.detectTactics(fen)
      dispatch(setTactics(tactics))
    } catch (err) {
      console.error('Tactics detection failed:', err)
    }
  }, [fen, dispatch])

  const runGameAnalysis = useCallback(async () => {
    for (let i = 0; i < moves.length; i++) {
      await new Promise<void>((resolve) => {
        const cleanup = apiService.on('analysis_complete', (data) => {
          const analysis = data as EngineAnalysis
          dispatch(updateMoveAnalysis({ index: i, analysis }))
          cleanup()
          resolve()
        })
        apiService.analyzePosition(moves[i].fenBefore, depth, 1)
      })
    }
  }, [moves, depth, dispatch])

  return {
    analysis: current,
    isAnalyzing,
    isEngineReady,
    backendConnected,
    analyzePosition,
    stopAnalysis,
    explainMove,
    detectTactics,
    runGameAnalysis,
  }
}