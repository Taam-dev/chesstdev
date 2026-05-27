import { contextBridge, ipcRenderer } from 'electron'

// Expose safe APIs to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  setSetting: (key: string, value: unknown) => ipcRenderer.invoke('set-setting', key, value),

  // Engine
  getEnginePath: () => ipcRenderer.invoke('get-engine-path'),
  selectEnginePath: () => ipcRenderer.invoke('select-engine-path'),

  // Files
  openPgnFile: () => ipcRenderer.invoke('open-pgn-file'),
  savePgnFile: (content: string) => ipcRenderer.invoke('save-pgn-file', content),

  // Screen capture
  getScreenSources: () => ipcRenderer.invoke('get-screen-sources'),

  // Window controls
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  openExternal: (url: string) => ipcRenderer.invoke('open-external', url),
  restartBackend: () => ipcRenderer.invoke('restart-backend'),

  // Events (renderer receives)
  onBackendLog: (callback: (log: string) => void) => {
    ipcRenderer.on('backend-log', (_, log) => callback(log))
    return () => ipcRenderer.removeAllListeners('backend-log')
  },
  onBackendCrashed: (callback: (code: number) => void) => {
    ipcRenderer.on('backend-crashed', (_, code) => callback(code))
    return () => ipcRenderer.removeAllListeners('backend-crashed')
  },
})

// TypeScript declaration
declare global {
  interface Window {
    electronAPI: {
      getSettings: () => Promise<Record<string, unknown>>
      setSetting: (key: string, value: unknown) => Promise<boolean>
      getEnginePath: () => Promise<string>
      selectEnginePath: () => Promise<string | null>
      openPgnFile: () => Promise<string | null>
      savePgnFile: (content: string) => Promise<boolean>
      getScreenSources: () => Promise<Array<{ id: string; name: string; thumbnail: string }>>
      minimizeWindow: () => Promise<void>
      maximizeWindow: () => Promise<void>
      closeWindow: () => Promise<void>
      openExternal: (url: string) => Promise<void>
      restartBackend: () => Promise<void>
      onBackendLog: (callback: (log: string) => void) => () => void
      onBackendCrashed: (callback: (code: number) => void) => () => void
    }
  }
}