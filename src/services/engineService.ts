/**
 * Engine Service - Wraps apiService với typed callbacks
 * Quản lý analysis state và subscriptions
 */

import { apiService } from './apiService'
import { EngineAnalysis, TacticPattern, MoveExplanation } from '@/types'

type AnalysisCallback = (analysis: EngineAnalysis) => void
type TacticsCallback = (tactics: TacticPattern[]) => void
type ExplanationCallback = (explanation: MoveExplanation) => void
type StatusCallback = (ready: boolean) => void
type ErrorCallback = (error: string) => void

class EngineService {
  private analysisCallbacks: Set<AnalysisCallback> = new Set()
  private tacticsCallbacks: Set<TacticsCallback> = new Set()
  private explanationCallbacks: Set<ExplanationCallback> = new Set()
  private statusCallbacks: Set<StatusCallback> = new Set()
  private errorCallbacks: Set<ErrorCallback> = new Set()

  private currentFen: string = ''
  private isAnalyzing: boolean = false
  private cleanupFns: Array<() => void> = []

  // ─── Initialization ─────────────────────────────────────────────────────────

  async initialize(): Promise<void> {
    // Connect to backend
    try {
      await apiService.connect()
    } catch (err) {
      console.error('Failed to connect to backend:', err)
    }

    // Register WebSocket handlers
    const unsubAnalysis = apiService.on('analysis_update', (data) => {
      const analysis = data as EngineAnalysis
      this.isAnalyzing = analysis.isAnalyzing
      this.analysisCallbacks.forEach((cb) => cb(analysis))
    })

    const unsubComplete = apiService.on('analysis_complete', (data) => {
      const analysis = data as EngineAnalysis
      analysis.isAnalyzing = false
      this.isAnalyzing = false
      this.analysisCallbacks.forEach((cb) => cb(analysis))
    })

    const unsubTactics = apiService.on('tactics_detected', (data) => {
      const tactics = data as TacticPattern[]
      this.tacticsCallbacks.forEach((cb) => cb(tactics))
    })

    const unsubExplanation = apiService.on('explanation_ready', (data) => {
      const explanation = data as MoveExplanation
      this.explanationCallbacks.forEach((cb) => cb(explanation))
    })

    const unsubReady = apiService.on('engine_ready', (data) => {
      const { ready } = data as { ready: boolean }
      this.statusCallbacks.forEach((cb) => cb(ready))
    })

    const unsubError = apiService.on('engine_error', (data) => {
      const { message } = data as { message: string }
      this.errorCallbacks.forEach((cb) => cb(message))
    })

    this.cleanupFns = [
      unsubAnalysis,
      unsubComplete,
      unsubTactics,
      unsubExplanation,
      unsubReady,
      unsubError,
    ]
  }

  // ─── Analysis Control ────────────────────────────────────────────────────────

  async analyzePosition(
    fen: string,
    depth: number = 20,
    multiPV: number = 3
  ): Promise<void> {
    if (!apiService.isConnected) {
      try {
        await apiService.connect()
      } catch {
        this.errorCallbacks.forEach((cb) =>
          cb('Cannot connect to analysis engine. Is the backend running?')
        )
        return
      }
    }

    this.currentFen = fen
    this.isAnalyzing = true
    await apiService.analyzePosition(fen, depth, multiPV)
  }

  async stopAnalysis(): Promise<void> {
    this.isAnalyzing = false
    await apiService.stopAnalysis()
  }

  // ─── Engine Options ──────────────────────────────────────────────────────────

  async setDepth(depth: number): Promise<void> {
    await apiService.setEngineOption('depth', depth)
  }

  async setThreads(threads: number): Promise<void> {
    await apiService.setEngineOption('Threads', threads)
  }

  async setHash(hash: number): Promise<void> {
    await apiService.setEngineOption('Hash', hash)
  }

  async setMultiPV(multiPV: number): Promise<void> {
    await apiService.setEngineOption('MultiPV', multiPV)
  }

  async setSkillLevel(level: number): Promise<void> {
    await apiService.setEngineOption('Skill Level', level)
  }

  // ─── Coach Features ──────────────────────────────────────────────────────────

  async explainMove(
    fen: string,
    move: string,
    analysis: EngineAnalysis
  ): Promise<MoveExplanation | null> {
    try {
      return await apiService.explainMove(fen, move, analysis)
    } catch (err) {
      console.error('Explain move failed:', err)
      return null
    }
  }

  async detectTactics(fen: string): Promise<TacticPattern[]> {
    try {
      return await apiService.detectTactics(fen)
    } catch (err) {
      console.error('Tactics detection failed:', err)
      return []
    }
  }

  async getEngineInfo(): Promise<Record<string, string>> {
    try {
      return await apiService.getEngineInfo()
    } catch {
      return {}
    }
  }

  async benchmark(): Promise<{ nps: number; time: number }> {
    try {
      return await apiService.benchmarkEngine()
    } catch {
      return { nps: 0, time: 0 }
    }
  }

  // ─── Event Subscriptions ────────────────────────────────────────────────────

  onAnalysis(cb: AnalysisCallback): () => void {
    this.analysisCallbacks.add(cb)
    return () => this.analysisCallbacks.delete(cb)
  }

  onTactics(cb: TacticsCallback): () => void {
    this.tacticsCallbacks.add(cb)
    return () => this.tacticsCallbacks.delete(cb)
  }

  onExplanation(cb: ExplanationCallback): () => void {
    this.explanationCallbacks.add(cb)
    return () => this.explanationCallbacks.delete(cb)
  }

  onStatusChange(cb: StatusCallback): () => void {
    this.statusCallbacks.add(cb)
    return () => this.statusCallbacks.delete(cb)
  }

  onError(cb: ErrorCallback): () => void {
    this.errorCallbacks.add(cb)
    return () => this.errorCallbacks.delete(cb)
  }

  // ─── Getters ─────────────────────────────────────────────────────────────────

  get analyzing(): boolean {
    return this.isAnalyzing
  }

  get connected(): boolean {
    return apiService.isConnected
  }

  // ─── Cleanup ─────────────────────────────────────────────────────────────────

  destroy(): void {
    this.cleanupFns.forEach((fn) => fn())
    this.cleanupFns = []
    this.analysisCallbacks.clear()
    this.tacticsCallbacks.clear()
    this.explanationCallbacks.clear()
    this.statusCallbacks.clear()
    this.errorCallbacks.clear()
  }
}

export const engineService = new EngineService()