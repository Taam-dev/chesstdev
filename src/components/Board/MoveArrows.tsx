import React, { useMemo } from 'react'
import { useAppSelector } from '@/store'

interface Arrow {
  from: string
  to: string
  color: string
  opacity: number
}

/**
 * SVG overlay arrows rendered on top of the chess board.
 * Board is assumed to be 560×560px, 8×8 = 70px squares.
 */
const SQUARE_SIZE = 70
const BOARD_SIZE = 560

function squareToCoords(
  square: string,
  orientation: 'white' | 'black'
): { x: number; y: number } {
  const file = square.charCodeAt(0) - 'a'.charCodeAt(0) // 0-7
  const rank = parseInt(square[1]) - 1                   // 0-7

  const col = orientation === 'white' ? file : 7 - file
  const row = orientation === 'white' ? 7 - rank : rank

  return {
    x: col * SQUARE_SIZE + SQUARE_SIZE / 2,
    y: row * SQUARE_SIZE + SQUARE_SIZE / 2,
  }
}

interface ArrowSvgProps {
  arrow: Arrow
  orientation: 'white' | 'black'
}

function ArrowSvg({ arrow, orientation }: ArrowSvgProps) {
  const from = squareToCoords(arrow.from, orientation)
  const to   = squareToCoords(arrow.to,   orientation)

  // Shorten the line slightly so arrowhead sits on center of target square
  const dx = to.x - from.x
  const dy = to.y - from.y
  const len = Math.sqrt(dx * dx + dy * dy)
  const nx = dx / len
  const ny = dy / len
  const shortenBy = SQUARE_SIZE * 0.3

  const x2 = to.x - nx * shortenBy
  const y2 = to.y - ny * shortenBy

  const id = `arrow-${arrow.from}-${arrow.to}`

  return (
    <g opacity={arrow.opacity}>
      <defs>
        <marker
          id={id}
          markerWidth="6"
          markerHeight="6"
          refX="3"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L6,3 L0,6 Z" fill={arrow.color} />
        </marker>
      </defs>
      <line
        x1={from.x}
        y1={from.y}
        x2={x2}
        y2={y2}
        stroke={arrow.color}
        strokeWidth="8"
        strokeLinecap="round"
        markerEnd={`url(#${id})`}
      />
    </g>
  )
}

export function MoveArrows() {
  const { current: analysis } = useAppSelector((state) => state.analysis)
  const { orientation } = useAppSelector((state) => state.game)
  const showArrows = useAppSelector((state) => state.settings.app.showArrows)

  const arrows = useMemo<Arrow[]>(() => {
    if (!analysis?.lines || !showArrows) return []

    return analysis.lines.slice(0, 3).map((line, idx) => {
      const move = line.moves[0]
      if (!move || move.length < 4) return null

      const colors = ['#00b894', '#6c5ce7', '#0984e3']
      const opacities = [0.85, 0.55, 0.35]

      return {
        from:    move.slice(0, 2),
        to:      move.slice(2, 4),
        color:   colors[idx],
        opacity: opacities[idx],
      } satisfies Arrow
    }).filter(Boolean) as Arrow[]
  }, [analysis, showArrows])

  if (arrows.length === 0) return null

  return (
    <svg
      className="absolute inset-0 pointer-events-none z-10"
      width={BOARD_SIZE}
      height={BOARD_SIZE}
      viewBox={`0 0 ${BOARD_SIZE} ${BOARD_SIZE}`}
    >
      {arrows.map((arrow, idx) => (
        <ArrowSvg key={idx} arrow={arrow} orientation={orientation} />
      ))}
    </svg>
  )
}