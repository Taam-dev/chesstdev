import React, { useEffect, useState } from 'react'
import { Provider } from 'react-redux'
import { store } from './store'
import { Header } from './components/UI/Header'
import { MainLayout } from './components/UI/MainLayout'
import { StatusBar } from './components/UI/StatusBar'

function AppContent() {
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'connected' | 'error'>('connecting')

  useEffect(() => {
    // Listen for backend events from Electron
    if (window.electronAPI) {
      const cleanup = window.electronAPI.onBackendCrashed((code) => {
        console.error('Backend crashed with code:', code)
        setBackendStatus('error')
      })
      return cleanup
    }
  }, [])

  return (
    <div className="min-h-screen bg-chess-bg text-white flex flex-col overflow-hidden">
      <Header />
      <main className="flex-1 overflow-hidden">
        <MainLayout />
      </main>
      <StatusBar backendStatus={backendStatus} />
    </div>
  )
}

function App() {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  )
}

export default App