import { app, BrowserWindow, ipcMain, dialog, shell, screen } from 'electron'
import * as path from 'path'
import * as fs from 'fs'
import { spawn, ChildProcess } from 'child_process'
import Store from 'electron-store'

// ─── App Store ─────────────────────────────────────────────────────────────────
const store = new Store({
  defaults: {
    enginePath: '',
    engineDepth: 20,
    engineThreads: 2,
    engineHash: 256,
    multiPV: 3,
    windowBounds: { width: 1400, height: 900 },
    showAnnotations: true,
  },
})

let mainWindow: BrowserWindow | null = null
let backendProcess: ChildProcess | null = null
const isDev = process.env.NODE_ENV === 'development'

// ─── Create Main Window ─────────────────────────────────────────────────────────
function createWindow(): void {
  const { width, height } = store.get('windowBounds') as { width: number; height: number }

  mainWindow = new BrowserWindow({
    width,
    height,
    minWidth: 1200,
    minHeight: 700,
    backgroundColor: '#1a1a2e',
    titleBarStyle: 'hiddenInset',
    frame: process.platform !== 'win32',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
    },
    icon: path.join(__dirname, '../assets/icons/icon.png'),
    show: false, // Don't show until ready
  })

  // Load URL
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }

  // Show when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show()
    mainWindow?.focus()
  })

  // Save window size on close
  mainWindow.on('close', () => {
    const bounds = mainWindow?.getBounds()
    if (bounds) {
      store.set('windowBounds', { width: bounds.width, height: bounds.height })
    }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ─── Start Python Backend ────────────────────────────────────────────────────────
function startBackend(): void {
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3'
  const backendScript = isDev
    ? path.join(__dirname, '../backend/main.py')
    : path.join(process.resourcesPath, 'backend/main.py')

  console.log(`Starting backend: ${pythonPath} ${backendScript}`)

  backendProcess = spawn(pythonPath, [backendScript], {
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      ENGINE_PATH: getEnginePath(),
    },
    stdio: ['pipe', 'pipe', 'pipe'],
  })

  backendProcess.stdout?.on('data', (data: Buffer) => {
    console.log('[Backend]', data.toString())
    // Forward backend logs to renderer
    mainWindow?.webContents.send('backend-log', data.toString())
  })

  backendProcess.stderr?.on('data', (data: Buffer) => {
    console.error('[Backend Error]', data.toString())
  })

  backendProcess.on('close', (code) => {
    console.log(`Backend exited with code ${code}`)
    if (code !== 0 && mainWindow) {
      mainWindow.webContents.send('backend-crashed', code)
    }
  })

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err)
    dialog.showErrorBox(
      'Backend Error',
      `Failed to start Python backend: ${err.message}\n\nMake sure Python is installed.`
    )
  })
}

// ─── Engine Path Detection ───────────────────────────────────────────────────────
function getEnginePath(): string {
  const stored = store.get('enginePath') as string
  if (stored && fs.existsSync(stored)) return stored

  // Auto-detect common locations
  const candidates = [
    // App bundled
    path.join(isDev ? 'assets' : process.resourcesPath, 'engines', 'stockfish'),
    path.join(isDev ? 'assets' : process.resourcesPath, 'engines', 'stockfish.exe'),
    // System installed
    '/usr/bin/stockfish',
    '/usr/local/bin/stockfish',
    '/opt/homebrew/bin/stockfish',
    // Windows common
    'C:\\Program Files\\Stockfish\\stockfish.exe',
    path.join(process.env.USERPROFILE || '', 'stockfish', 'stockfish.exe'),
  ]

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      store.set('enginePath', candidate)
      return candidate
    }
  }

  return ''
}

// ─── IPC Handlers ───────────────────────────────────────────────────────────────
function setupIpcHandlers(): void {
  // Settings
  ipcMain.handle('get-settings', () => store.store)
  ipcMain.handle('set-setting', (_, key: string, value: unknown) => {
    store.set(key, value)
    return true
  })

  // Engine path
  ipcMain.handle('get-engine-path', () => getEnginePath())
  ipcMain.handle('select-engine-path', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      title: 'Select Stockfish Engine',
      filters: [
        { name: 'Executables', extensions: ['exe', ''] },
        { name: 'All Files', extensions: ['*'] },
      ],
      properties: ['openFile'],
    })
    if (!result.canceled && result.filePaths[0]) {
      store.set('enginePath', result.filePaths[0])
      return result.filePaths[0]
    }
    return null
  })

  // File operations
  ipcMain.handle('open-pgn-file', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      title: 'Open PGN File',
      filters: [{ name: 'PGN Files', extensions: ['pgn'] }],
      properties: ['openFile'],
    })
    if (!result.canceled && result.filePaths[0]) {
      return fs.readFileSync(result.filePaths[0], 'utf-8')
    }
    return null
  })

  ipcMain.handle('save-pgn-file', async (_, content: string) => {
    const result = await dialog.showSaveDialog(mainWindow!, {
      title: 'Save PGN File',
      filters: [{ name: 'PGN Files', extensions: ['pgn'] }],
    })
    if (!result.canceled && result.filePath) {
      fs.writeFileSync(result.filePath, content, 'utf-8')
      return true
    }
    return false
  })

  // Screen capture
  ipcMain.handle('get-screen-sources', async () => {
    const { desktopCapturer } = require('electron')
    const sources = await desktopCapturer.getSources({
      types: ['window', 'screen'],
      thumbnailSize: { width: 1920, height: 1080 },
    })
    return sources.map((s: Electron.DesktopCapturerSource) => ({
      id: s.id,
      name: s.name,
      thumbnail: s.thumbnail.toDataURL(),
    }))
  })

  // App control
  ipcMain.handle('minimize-window', () => mainWindow?.minimize())
  ipcMain.handle('maximize-window', () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize()
    else mainWindow?.maximize()
  })
  ipcMain.handle('close-window', () => mainWindow?.close())
  ipcMain.handle('open-external', (_, url: string) => shell.openExternal(url))
  ipcMain.handle('restart-backend', () => {
    backendProcess?.kill()
    setTimeout(startBackend, 1000)
  })
}

// ─── App Events ──────────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  startBackend()

  // Wait a moment for backend to start
  setTimeout(() => {
    createWindow()
    setupIpcHandlers()
  }, 2000)
})

app.on('window-all-closed', () => {
  backendProcess?.kill()
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

app.on('before-quit', () => {
  backendProcess?.kill()
})

// Handle unhandled errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error)
  dialog.showErrorBox('Unexpected Error', error.message)
})