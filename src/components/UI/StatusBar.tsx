import React, { useEffect, useState } from 'react'
import { useAppSelector } from '@/store'
import { Activity, Cpu, Database, AlertCircle, CheckCircle } from 'lucide-react'

interface StatusBarProps {
  backendStatus: 'connecting' | 'connected' | 'error'
}

export function StatusBar({ backendStatus }: StatusBarProps) {
  const { isEngineReady, isAnalyzing, current, backendConnected } = useAppSelector(
    (state) => state.analysis
  )
  const { moves, currentMoveIndex } = useAppSelector((state) => state.game)
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const statusColor = {
    connecting: 'text-yellow-400',
    connected:  'text-green-400',
    error:      'text-red-400',
  }[backendStatus]

  const statusLabel = {
    connecting: 'Connecting...',
    connected:  'Backend Connected',
    error:      'Backend Error',
  }[backendStatus]

  const StatusIcon = backendStatus === 'error'
    ? AlertCircle
    : backendStatus === 'connected'
    ? CheckCircle
    : Activity

  return (
    <div className="flex items-center justify-between px-4 h-6 bg-chess-panel border-t border-gray-700/50 text-[11px] text-gray-500 select-none">
      {/* Left: backend + engine status */}
      <div className="flex items-center gap-4">
        {/* Backend */}
        <div className={`flex items-center gap-1.5 ${statusColor}`}>
          <StatusIcon size={10} />
          <span>{statusLabel}</span>
        </div>

        {/* Engine */}
        <div className="flex items-center gap-1.5">
          <Cpu size={10} className={isEngineReady ? 'text-green-400' : 'text-gray-600'} />
          <span className={isEngineReady ? 'text-green-400' : 'text-gray-600'}>
            {isEngineReady ? 'Stockfish Ready' : 'Engine Offline'}
          </span>
        </div>

        {/* Analysis status */}
        {isAnalyzing && (
          <div className="flex items-center gap-1.5 text-blue-400">
            <Activity size={10} className="animate-pulse" />
            <span>
              Analyzing
              {current?.depth ? ` (depth ${current.depth})` : '...'}
            </span>
          </div>
        )}
      </div>

      {/* Center: move info */}
      <div className="flex items-center gap-4">
        {moves.length > 0 && (
          <div className="flex items-center gap-1.5">
            <Database size={10} />
            <span>
              Move {currentMoveIndex + 1} / {moves.length}
            </span>
          </div>
        )}

        {current && !isAnalyzing && (
          <span className="text-gray-600">
            {current.nodes
              ? `${(current.nodes / 1_000_000).toFixed(1)}M nodes`
              : null}
            {current.nps
              ? ` · ${(current.nps / 1_000_000).toFixed(1)}Mn/s`
              : null}
          </span>
        )}
      </div>

      {/* Right: time */}
      <div className="text-gray-600">
        {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  )
}