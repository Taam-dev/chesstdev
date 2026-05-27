/**
 * API Service - WebSocket communication with Python backend
 * Handles all real-time engine analysis updates
 */

import { WSMessage, WSMessageType, EngineAnalysis, MoveExplanation, TacticPattern, RecognitionResult } from '@/types'

type MessageHandler = (data: unknown) => void

class ApiService {
  private ws: WebSocket | null = null
  private handlers: Map<WSMessageType, Set<MessageHandler>> = new Map()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private isConnecting = false
  private messageQueue: WSMessage[] = []
  private readonly WS_URL = 'ws://localhost:8765'
  private readonly HTTP_URL = 'http://localhost:8765'
  private pingInterval: ReturnType<typeof setInterval> | null = null

  // ─── Connection Management ──────────────────────────────────────────────────

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.isConnecting) {
        // Wait for connection
        const checkInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            clearInterval(checkInterval)
            resolve()
          }
        }, 100)
        return
      }

      this.isConnecting = true
      console.log(`Connecting to backend at ${this.WS_URL}...`)

      this.ws = new WebSocket(this.WS_URL)

      this.ws.onopen = () => {
        console.log('✅ Backend connected')
        this.isConnecting = false
        this.flushMessageQueue()
        this.startPing()
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data)
          this.dispatchMessage(message)
        } catch (err) {
          console.error('Failed to parse WS message:', err)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...')
        this.isConnecting = false
        this.stopPing()
        this.scheduleReconnect()
      }

      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        this.isConnecting = false
        reject(new Error('Connection failed'))
      }

      // Timeout
      setTimeout(() => {
        if (this.isConnecting) {
          this.isConnecting = false
          reject(new Error('Connection timeout'))
        }
      }, 5000)
    })
  }

  disconnect(): void {
    this.reconnectTimer && clearTimeout(this.reconnectTimer)
    this.stopPing()
    this.ws?.close()
    this.ws = null
  }

  private scheduleReconnect(): void {
    this.reconnectTimer = setTimeout(() => {
      console.log('Attempting to reconnect...')
      this.connect().catch(console.error)
    }, 2000)
  }

  private startPing(): void {
    this.pingInterval = setInterval(() => {
      this.send('ping', {})
    }, 30000)
  }

  private stopPing(): void {
    this.pingInterval && clearInterval(this.pingInterval)
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  // ─── Message Handling ───────────────────────────────────────────────────────

  private send(type: string, data: unknown, requestId?: string): void {
    const message: WSMessage = {
      type: type as WSMessageType,
      data,
      timestamp: Date.now(),
      requestId,
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      this.messageQueue.push(message)
      this.connect().catch(console.error)
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()!
      this.ws?.send(JSON.stringify(message))
    }
  }

  private dispatchMessage(message: WSMessage): void {
    const handlers = this.handlers.get(message.type)
    handlers?.forEach((handler) => handler(message.data))
  }

  on(type: WSMessageType, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)

    // Return cleanup function
    return () => {
      this.handlers.get(type)?.delete(handler)
    }
  }

  // ─── Engine API ─────────────────────────────────────────────────────────────

  async analyzePosition(fen: string, depth: number, multiPV: number): Promise<void> {
    this.send('analyze', { fen, depth, multiPV })
  }

  async stopAnalysis(): Promise<void> {
    this.send('stop_analysis', {})
  }

  async explainMove(
    fen: string,
    move: string,
    analysis: EngineAnalysis
  ): Promise<MoveExplanation> {
    return this.httpPost('/explain-move', { fen, move, analysis })
  }

  async detectTactics(fen: string): Promise<TacticPattern[]> {
    return this.httpPost('/detect-tactics', { fen })
  }

  async setEngineOption(option: string, value: string | number): Promise<void> {
    this.send('set_option', { option, value })
  }

  async getEngineInfo(): Promise<Record<string, string>> {
    return this.httpGet('/engine-info')
  }

  async benchmarkEngine(): Promise<{ nps: number; time: number }> {
    return this.httpGet('/benchmark')
  }

  // ─── Recognition API ────────────────────────────────────────────────────────

  async captureScreen(region?: {
    x: number
    y: number
    width: number
    height: number
  }): Promise<RecognitionResult> {
    return this.httpPost('/capture-screen', { region })
  }

  async startWebcam(deviceIndex?: number): Promise<void> {
    this.send('start_webcam', { deviceIndex: deviceIndex ?? 0 })
  }

  async stopWebcam(): Promise<void> {
    this.send('stop_webcam', {})
  }

  async calibrateBoard(imageData: string): Promise<{ corners: number[][] }> {
    return this.httpPost('/calibrate-board', { imageData })
  }

  // ─── Game API ───────────────────────────────────────────────────────────────

  async saveGame(pgn: string, metadata: Record<string, string>): Promise<{ id: string }> {
    return this.httpPost('/save-game', { pgn, metadata })
  }

  async loadGames(): Promise<unknown[]> {
    return this.httpGet('/games')
  }

  async deleteGame(id: string): Promise<void> {
    return this.httpDelete(`/games/${id}`)
  }

  // ─── HTTP Helpers ───────────────────────────────────────────────────────────

  private async httpGet<T>(path: string): Promise<T> {
    const response = await fetch(`${this.HTTP_URL}${path}`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`)
    }
    return response.json()
  }

  private async httpPost<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.HTTP_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`)
    }
    return response.json()
  }

  private async httpDelete<T>(path: string): Promise<T> {
    const response = await fetch(`${this.HTTP_URL}${path}`, { method: 'DELETE' })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`)
    }
    return response.json()
  }
}

// Singleton export
export const apiService = new ApiService()