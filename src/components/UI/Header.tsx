import React from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '@/store'
import { resetGame, setShowAnnotations } from '@/store/gameSlice'
import { toggleAnnotationsMode } from '@/store/analysisSlice'
import { apiService } from '@/services/apiService'
import {
  Minimize2,
  Maximize2,
  X,
  RefreshCw,
  Download,
  Upload,
  Settings,
  Camera,
  Video,
  RotateCcw,
} from 'lucide-react'
import { Chess } from 'chess.js'
import { addMove } from '@/store/gameSlice'

export function Header() {
  const dispatch = useDispatch()
  const { showAnnotationsMode } = useSelector((state: RootState) => state.analysis)
  const { fen, pgn, orientation } = useSelector((state: RootState) => state.game)

  const isElectron = !!window.electronAPI

  const handleOpenPGN = async () => {
    if (isElectron) {
      const content = await window.electronAPI.openPgnFile()
      if (content) loadPGN(content)
    } else {
      // Browser fallback
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.pgn'
      input.onchange = (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (file) {
          const reader = new FileReader()
          reader.onload = (e) => loadPGN(e.target?.result as string)
          reader.readAsText(file)
        }
      }
      input.click()
    }
  }

  const loadPGN = (content: string) => {
    const chess = new Chess()
    try {
      chess.loadPgn(content)
      const history = chess.history({ verbose: true })
      dispatch(resetGame())

      const chessReplay = new Chess()
      history.forEach((move, index) => {
        const fenBefore = chessReplay.fen()
        chessReplay.move(move)
        dispatch(addMove({
          index,
          move: { from: move.from, to: move.to },
          san: move.san,
          fen: chessReplay.fen(),
          fenBefore,
          timestamp: Date.now(),
        }))
      })
    } catch (err) {
      console.error('Failed to load PGN:', err)
    }
  }

  const handleSavePGN = async () => {
    if (isElectron) {
      await window.electronAPI.savePgnFile(pgn)
    } else {
      const blob = new Blob([pgn], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'game.pgn'
      a.click()
    }
  }

  const handleCopyFEN = () => {
    navigator.clipboard.writeText(fen)
  }

  return (
    <div
      className="flex items-center justify-between px-4 h-12 border-b border-gray-700/50 bg-chess-panel"
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
    >
      {/* Left: App Title */}
      <div
        className="flex items-center gap-3"
        style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
      >
        <div className="flex items-center gap-2">
          <span className="text-2xl">♟</span>
          <div>
            <span className="font-bold text-white text-sm">ChessCoach</span>
            <span className="text-chess-accent text-sm font-bold"> Local</span>
          </div>
        </div>
      </div>

      {/* Center: Toolbar */}
      <div
        className="flex items-center gap-1"
        style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
      >
        <ToolbarButton icon={<Upload size={14} />} label="Open PGN" onClick={handleOpenPGN} />
        <ToolbarButton icon={<Download size={14} />} label="Save PGN" onClick={handleSavePGN} />
        <ToolbarButton icon={<RefreshCw size={14} />} label="New Game" onClick={() => dispatch(resetGame())} />
        <div className="w-px h-5 bg-gray-600 mx-1" />
        <ToolbarButton icon={<RotateCcw size={14} />} label="Flip Board" onClick={() => {}} />

        {/* Annotations Toggle - Chess.com style */}
        <div className="w-px h-5 bg-gray-600 mx-1" />
        <button
          onClick={() => dispatch(toggleAnnotationsMode())}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
            showAnnotationsMode
              ? 'bg-chess-accent text-white'
              : 'text-gray-400 hover:text-white hover:bg-white/10'
          }`}
          title="Toggle Chess.com-style move annotations"
        >
          <span>{showAnnotationsMode ? '✨' : '⊙'}</span>
          <span>Annotations</span>
        </button>
      </div>

      {/* Right: Window Controls (Electron only) */}
      {isElectron && (
        <div
          className="flex items-center gap-1"
          style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
        >
          <button
            onClick={() => window.electronAPI.minimizeWindow()}
            className="p-1.5 hover:bg-white/10 rounded text-gray-400 hover:text-white transition-colors"
          >
            <Minimize2 size={12} />
          </button>
          <button
            onClick={() => window.electronAPI.maximizeWindow()}
            className="p-1.5 hover:bg-white/10 rounded text-gray-400 hover:text-white transition-colors"
          >
            <Maximize2 size={12} />
          </button>
          <button
            onClick={() => window.electronAPI.closeWindow()}
            className="p-1.5 hover:bg-red-500/20 rounded text-gray-400 hover:text-red-400 transition-colors"
          >
            <X size={12} />
          </button>
        </div>
      )}
    </div>
  )
}

function ToolbarButton({
  icon,
  label,
  onClick,
  active,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  active?: boolean
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={`flex items-center gap-1.5 px-2 py-1.5 rounded text-xs transition-colors ${
        active
          ? 'bg-chess-accent text-white'
          : 'text-gray-400 hover:text-white hover:bg-white/10'
      }`}
    >
      {icon}
      <span className="hidden lg:inline">{label}</span>
    </button>
  )
}