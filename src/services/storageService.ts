/**
 * Storage Service - Local persistence (electron-store / localStorage fallback)
 */

import { AppSettings, EngineSettings } from '@/types'

const KEYS = {
  APP_SETTINGS:    'app_settings',
  ENGINE_SETTINGS: 'engine_settings',
  RECENT_GAMES:    'recent_games',
  LAST_FEN:        'last_fen',
} as const

class StorageService {
  private isElectron = !!window.electronAPI

  // ─── Generic get/set ──────────────────────────────────────────────────────────

  private async get<T>(key: string, fallback: T): Promise<T> {
    try {
      if (this.isElectron) {
        const settings = await window.electronAPI.getSettings()
        const value = settings[key]
        return value !== undefined ? (value as T) : fallback
      } else {
        const raw = localStorage.getItem(key)
        return raw ? (JSON.parse(raw) as T) : fallback
      }
    } catch {
      return fallback
    }
  }

  private async set(key: string, value: unknown): Promise<void> {
    try {
      if (this.isElectron) {
        await window.electronAPI.setSetting(key, value)
      } else {
        localStorage.setItem(key, JSON.stringify(value))
      }
    } catch (err) {
      console.error(`StorageService.set(${key}) failed:`, err)
    }
  }

  // ─── App Settings ─────────────────────────────────────────────────────────────

  async getAppSettings(): Promise<Partial<AppSettings>> {
    return this.get<Partial<AppSettings>>(KEYS.APP_SETTINGS, {})
  }

  async saveAppSettings(settings: Partial<AppSettings>): Promise<void> {
    await this.set(KEYS.APP_SETTINGS, settings)
  }

  // ─── Engine Settings ──────────────────────────────────────────────────────────

  async getEngineSettings(): Promise<Partial<EngineSettings>> {
    return this.get<Partial<EngineSettings>>(KEYS.ENGINE_SETTINGS, {})
  }

  async saveEngineSettings(settings: Partial<EngineSettings>): Promise<void> {
    await this.set(KEYS.ENGINE_SETTINGS, settings)
  }

  // ─── Engine Path ──────────────────────────────────────────────────────────────

  async getEnginePath(): Promise<string> {
    if (this.isElectron) {
      return (await window.electronAPI.getEnginePath()) ?? ''
    }
    return this.get<string>('enginePath', '')
  }

  async saveEnginePath(path: string): Promise<void> {
    await this.set('enginePath', path)
  }

  // ─── Last FEN ─────────────────────────────────────────────────────────────────

  async getLastFen(): Promise<string> {
    return this.get<string>(KEYS.LAST_FEN, '')
  }

  async saveLastFen(fen: string): Promise<void> {
    await this.set(KEYS.LAST_FEN, fen)
  }

  // ─── Recent Games ─────────────────────────────────────────────────────────────

  async getRecentGames(): Promise<string[]> {
    return this.get<string[]>(KEYS.RECENT_GAMES, [])
  }

  async addRecentGame(pgn: string): Promise<void> {
    const recent = await this.getRecentGames()
    const updated = [pgn, ...recent.filter((g) => g !== pgn)].slice(0, 10)
    await this.set(KEYS.RECENT_GAMES, updated)
  }

  // ─── Clear ───────────────────────────────────────────────────────────────────

  async clearAll(): Promise<void> {
    if (!this.isElectron) {
      localStorage.clear()
    }
  }
}

export const storageService = new StorageService()