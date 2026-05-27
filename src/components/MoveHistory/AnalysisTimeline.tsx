import React, { useRef, useEffect } from 'react'
import { useAppSelector, useAppDispatch } from '@/store'
import { goToMove } from '@/store/gameSlice'
import { MoveRecord } from '@/types'

const QUALITY_COLORS: Record<string, string> = {
  brilliant: '#00d4ff',
  great: '#50fa7b',
  best: '#50fa7b',
  good: '#6272a4',
  inaccuracy: '#ffb86c',
  mistake: '#ff9800',
  blunder: '#ff5555',
  miss: '#ff5555',
}

const QUALITY_HEIGHT: Record<string, number> = {
  brilliant: 100,
  great: 85,
  best: 85,
  good: 70,
  inaccuracy: 50,
  mistake: 30,
  blunder: 10,
  miss: 10,
}

interface TimelineBarProps {
  move: MoveRecord
  index: number
  isActive: boolean
  onClick: () => void
}

const TimelineBar: React.FC<TimelineBarProps> = ({
  move,
  index,
  isActive,
  onClick,
}) => {
  const quality = move.quality?.label
  const color = quality ? QUALITY_COLORS[quality] : '#6272a4'
  const height = quality ? QUALITY_HEIGHT[quality] : 50

  // Eval bar based on analysis
  const evalValue = move.analysis?.evaluation ?? 0
  const clampedEval = Math.max(-10, Math.min(10, evalValue / 100))
  const evalHeight = ((clampedEval + 10) / 20) * 100

  return (
    <div
      className="relative flex flex-col items-center cursor-pointer group"
      onClick={onClick}
      title={`${move.san} — ${quality ?? 'unknown'}`}
    >
      {/* Eval bar background */}
      <div className="w-4 h-16 bg-gray-700/50 rounded-sm relative overflow-hidden">
        <div
          className="absolute bottom-0 left-0 right-0 transition-all duration-300"
          style={{
            height: `${evalHeight}%`,
            backgroundColor: evalValue >= 0 ? '#f8f8f8' : '#1a1a1a',
          }}
        />
        {/* Quality indicator */}
        {quality && (
          <div
            className="absolute bottom-0 left-0 right-0 rounded-sm transition-all duration-300"
            style={{
              height: `${height}%`,
              backgroundColor: color,
              opacity: 0.6,
            }}
          />
        )}
      </div>

      {/* Active indicator */}
      {isActive && (
        <div className="w-1.5 h-1.5 rounded-full bg-white mt-0.5" />
      )}

      {/* Tooltip on hover */}
      <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden group-hover:block z-20 pointer-events-none">
        <div className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs whitespace-nowrap">
          <span className="font-mono">{move.san}</span>
          {quality && (
            <span className="ml-1" style={{ color }}>
              {move.quality?.symbol}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export const AnalysisTimeline: React.FC = () => {
  const dispatch = useAppDispatch()
  const { moves, currentMoveIndex } = useAppSelector((state) => state.game)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to current move
  useEffect(() => {
    if (scrollRef.current && currentMoveIndex >= 0) {
      const bar = scrollRef.current.children[currentMoveIndex] as HTMLElement
      bar?.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
    }
  }, [currentMoveIndex])

  if (moves.length === 0) {
    return (
      <div className="h-20 flex items-center justify-center">
        <p className="text-xs text-gray-600">No moves yet</p>
      </div>
    )
  }

  return (
    <div className="px-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-500">Analysis Timeline</span>
        <span className="text-xs text-gray-600">{moves.length} moves</span>
      </div>

      {/* Timeline graph */}
      <div
        ref={scrollRef}
        className="flex gap-0.5 overflow-x-auto scrollbar-thin scrollbar-track-transparent
          scrollbar-thumb-gray-700 pb-2 items-end h-20"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {moves.map((move, idx) => (
          <div key={idx} style={{ scrollSnapAlign: 'start' }}>
            <TimelineBar
              move={move}
              index={idx}
              isActive={idx === currentMoveIndex}
              onClick={() => dispatch(goToMove(idx))}
            />
          </div>
        ))}
      </div>
    </div>
  )
}