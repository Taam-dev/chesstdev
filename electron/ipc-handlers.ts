/**
 * IPC Handlers - Extracted from main.ts for modularity
 * Handles all renderer <-> main process communication
 */

import { ipcMain, dialog, shell, BrowserWindow, desktopCapturer } from 'electron'
import * as fs from 'fs'
import * as path from 'path'
import Store from 'electron-store'

export function registerIpcHandlers(
  mainWindow: BrowserWindow,
  store: Store,
  getEnginePath: () => string
): void {
  // ─── Settings ─────────────────────────────────────────────────────────────────

  ipcMain.handle('get-settings', () => store.store)

  ipcMain.handle('set-setting', (_event, key: string, value: unknown) => {
    store.set(key, value)
    return true
  })

  ipcMain.handle('get-all-settings', () => ({
    engineSettings: store.get('engineSettings'),
    appSettings: store.get('appSettings'),
    enginePath: store.get('enginePath'),
    windowBounds: store.get('windowBounds'),
  }))

  // ─── Engine ───────────────────────────────────────────────────────────────────

  ipcMain.handle('get-engine-path', () => getEnginePath())

  ipcMain.handle('select-engine-path', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Select Stockfish Executable',
      filters: [
        { name: 'Executables', extensions: ['exe', ''] },
        { name: 'All Files', extensions: ['*'] },
      ],
      properties: ['openFile'],
    })

    if (!result.canceled && result.filePaths[0]) {
      const selectedPath = result.filePaths[0]
      // Verify it's executable
      if (!fs.existsSync(selectedPath)) {
        return { error: 'File not found', path: null }
      }
      store.set('enginePath', selectedPath)
      return { error: null, path: selectedPath }
    }
    return { error: null, path: null }
  })

  // ─── File Operations ──────────────────────────────────────────────────────────

  ipcMain.handle('open-pgn-file', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Open PGN File',
      filters: [
        { name: 'PGN Files', extensions: ['pgn'] },
        { name: 'All Files', extensions: ['*'] },
      ],
      properties: ['openFile'],
    })

    if (!result.canceled && result.filePaths[0]) {
      try {
        return {
          content: fs.readFileSync(result.filePaths[0], 'utf-8'),
          path: result.filePaths[0],
          error: null,
        }
      } catch (err) {
        return {
          content: null,
          path: null,
          error: (err as Error).message,
        }
      }
    }
    return { content: null, path: null, error: null }
  })

  ipcMain.handle('save-pgn-file', async (_event, content: string, suggestedName?: string) => {
    const result = await dialog.showSaveDialog(mainWindow, {
      title: 'Save PGN File',
      defaultPath: suggestedName ?? `game_${Date.now()}.pgn`,
      filters: [{ name: 'PGN Files', extensions: ['pgn'] }],
    })

    if (!result.canceled && result.filePath) {
      try {
        fs.writeFileSync(result.filePath, content, 'utf-8')
        return { success: true, path: result.filePath }
      } catch (err) {
        return { success: false, error: (err as Error).message }
      }
    }
    return { success: false, error: null }
  })

  ipcMain.handle('read-file', (_event, filePath: string) => {
    try {
      return fs.readFileSync(filePath, 'utf-8')
    } catch {
      return null
    }
  })

  // ─── Screen Capture ───────────────────────────────────────────────────────────

  ipcMain.handle('get-screen-sources', async () => {
    try {
      const sources = await desktopCapturer.getSources({
        types: ['window', 'screen'],
        thumbnailSize: { width: 320, height: 180 },
      })
      return sources.map((s) => ({
        id: s.id,
        name: s.name,
        thumbnail: s.thumbnail.toDataURL(),
        display_id: s.display_id,
      }))
    } catch (err) {
      console.error('Failed to get screen sources:', err)
      return []
    }
  })

  // ─── Window Controls ─────────────────────────────────────────────────────────

  ipcMain.handle('minimize-window', () => {
    mainWindow.minimize()
  })

  ipcMain.handle('maximize-window', () => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow.maximize()
    }
    return mainWindow.isMaximized()
  })

  ipcMain.handle('close-window', () => {
    mainWindow.close()
  })

  ipcMain.handle('toggle-fullscreen', () => {
    mainWindow.setFullScreen(!mainWindow.isFullScreen())
    return mainWindow.isFullScreen()
  })

  ipcMain.handle('is-maximized', () => mainWindow.isMaximized())

  // ─── System ──────────────────────────────────────────────────────────────────

  ipcMain.handle('open-external', (_event, url: string) => {
    // Validate URL before opening
    try {
      const parsed = new URL(url)
      if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
        shell.openExternal(url)
      }
    } catch {
      console.warn('Invalid URL:', url)
    }
  })

  ipcMain.handle('open-path', (_event, filePath: string) => {
    shell.openPath(filePath)
  })

  ipcMain.handle('show-item-in-folder', (_event, filePath: string) => {
    shell.showItemInFolder(filePath)
  })

  ipcMain.handle('get-app-version', () => {
    return process.env.npm_package_version ?? '1.0.0'
  })

  ipcMain.handle('get-platform', () => process.platform)
}