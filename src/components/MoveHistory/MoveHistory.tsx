import React, { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '@/store'
import {
  goToMove,
  goToPreviousMove,
  goToNextMove,
  goToFirstMove,
  goToLastMove,
} from '@/store/gameSlice'
import { MoveQualityBadge } from '../Analysis/MoveQuality'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

export function MoveHistory() {
  const dispatch = useDispatch()
  const { moves, currentMoveIndex, showAnnotations } = useSelector(
    (state: RootState) => state.game
  )
  const { showAnnotationsMode } = useSelector((state: RootState) => state.analysis)
  const currentRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to current move
  useEffect(() => {
    currentRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [currentMoveIndex])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return
      if (e.key === 'ArrowLeft') dispatch(goToPreviousMove())
      if (e.key === 'ArrowRight') dispatch(goToNextMove())
      if (e.key === 'Home') dispatch(goToFirstMove())
      if (e.key === 'End') dispatch(goToLastMove())
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [dispatch])

  // Group moves into pairs (White/Black)
  const movePairs: Array<[typeof moves[0]?, typeof moves[0]?]> = []
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push([moves[i], moves[i + 1]])
  }

  return (
    <div className="flex flex-col h-full bg-chess-panel rounded-xl border border-gray-700/50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700/50">
        <h2 className="font-semibold text-white">Move History</h2>
        <p className="text-xs text-gray-400">{moves.length} moves played</p>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-center gap-2 px-4 py-2 border-b border-gray-700/30">
        <NavButton
          icon={<ChevronsLeft size={14} />}
          onClick={() => dispatch(goToFirstMove())}
          disabled={currentMoveIndex === -1}
          title="First move"
        />
        <NavButton
          icon={<ChevronLeft size={14} />}
          onClick={() => dispatch(goToPreviousMove())}
          disabled={currentMoveIndex === -1}
          title="Previous move (←)"
        />
        <span className="text-xs text-gray-400 w-16 text-center">
          {currentMoveIndex === -1 ? 'Start' : `Move ${currentMoveIndex + 1}`}
        </span>
        <NavButton
          icon={<ChevronRight size={14} />}
          onClick={() => dispatch(goToNextMove())}
          disabled={currentMoveIndex === moves.length - 1}
          title="Next move (→)"
        />
        <NavButton
          icon={<ChevronsRight size={14} />}
          onClick={() => dispatch(goToLastMove())}
          disabled={currentMoveIndex === moves.length - 1}
          title="Last move"
        />
      </div>

      {/* Move List */}
      <div className="flex-1 overflow-y-auto p-2">
        {moves.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <span className="text-2xl mb-1">♟</span>
            <p className="text-xs">No moves yet</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {movePairs.map((pair, pairIdx) => (
              <div key={pairIdx} className="flex items-center gap-1">
                {/* Move number */}
                <span className="text-xs text-gray-600 w-7 text-right flex-shrink-0">
                  {pairIdx + 1}.
                </span>

                {/* White move */}
                {pair[0] && (
                  <MoveButton
                    move={pair[0]}
                    index={pairIdx * 2}
                    isActive={currentMoveIndex === pairIdx * 2}
                    showAnnotation={showAnnotationsMode}
                    onClick={() => dispatch(goToMove(pairIdx * 2))}
                    ref={currentMoveIndex === pairIdx * 2 ? currentRef : undefined}
                  />
                )}

                {/* Black move */}
                {pair[1] && (
                  <MoveButton
                    move={pair[1]}
                    index={pairIdx * 2 + 1}
                    isActive={currentMoveIndex === pairIdx * 2 + 1}
                    showAnnotation={showAnnotationsMode}
                    onClick={() => dispatch(goToMove(pairIdx * 2 + 1))}
                    ref={currentMoveIndex === pairIdx * 2 + 1 ? currentRef : undefined}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Move Button ─────────────────────────────────────────────────────────────

interface MoveButtonProps {
  move: { san: string; quality?: any }
  index: number
  isActive: boolean
  showAnnotation: boolean
  onClick: () => void
}

const MoveButton = React.forwardRef<HTMLDivElement, MoveButtonProps>(
  ({ move, isActive, showAnnotation, onClick }, ref) => {
    return (
      <div ref={ref} className="flex-1 min-w-0">
        <button
          onClick={onClick}
          className={`w-full flex items-center justify-between px-2 py-1.5 rounded text-sm font-mono transition-colors ${
            isActive
              ? 'bg-chess-accent text-white font-bold'
              : 'text-gray-300 hover:bg-white/10 hover:text-white'
          }`}
        >
          <span className="truncate">{move.san}</span>
          {showAnnotation && move.quality && (
            <MoveQualityBadge quality={move.quality} size="sm" />
          )}
        </button>
      </div>
    )
  }
)
MoveButton.displayName = 'MoveButton'

// ─── Nav Button ──────────────────────────────────────────────────────────────

function NavButton({
  icon,
  onClick,
  disabled,
  title,
}: {
  icon: React.ReactNode
  onClick: () => void
  disabled: boolean
  title: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className="p-1.5 rounded hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-gray-400 hover:text-white transition-colors"
    >
      {icon}
    </button>
  )
}