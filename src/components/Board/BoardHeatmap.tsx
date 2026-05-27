import React, { useMemo } from 'react'
import { useAppSelector } from '@/store'
import { Chess } from 'chess.js'

const SQUARE_SIZE = 70
const FILES = ['a','b','c','d','e','f','g','h']
const RANKS = ['1','2','3','4','5','6','7','8']

function getSquareActivity(fen: string): Record<string, number> {
  const activity: Record<string, number> = {}

  try {
    const chess = new Chess(fen)
    const board = chess.board()

    board.forEach((row, rankIdx) => {
      row.forEach((piece, fileIdx) => {
        if (!piece) return
        const square = FILES[fileIdx] + RANKS[7 - rankIdx]

        // Get all moves from this square
        const moves = chess.moves({ square: square as any, verbose: true })
        activity[square] = (activity[square] ?? 0) + moves.length

        // Increment target squares
        moves.forEach((mv) => {
          const to = (mv as any).to as string
          activity[to] = (activity[to] ?? 0) + 0.5
        })
      })
    })
  } catch {
    // invalid fen
  }

  return activity
}

export function BoardHeatmap() {
  const { fen, orientation } = useAppSelector((state) => state.game)
  const showHeatmap = useAppSelector((state) => state.settings.app.showHeatmap)

  const activity = useMemo(() => getSquareActivity(fen), [fen])

  if (!showHeatmap) return null

  const maxActivity = Math.max(1, ...Object.values(activity))

  return (
    <svg
      className="absolute inset-0 pointer-events-none z-5"
      width={SQUARE_SIZE * 8}
      height={SQUARE_SIZE * 8}
    >
      {FILES.flatMap((file, fileIdx) =>
        RANKS.map((rank, rankIdx) => {
          const square = file + rank
          const val = activity[square] ?? 0
          const intensity = val / maxActivity

          const col = orientation === 'white' ? fileIdx : 7 - fileIdx
          const row = orientation === 'white' ? 7 - rankIdx : rankIdx

          const x = col * SQUARE_SIZE
          const y = row * SQUARE_SIZE

          return (
            <rect
              key={square}
              x={x}
              y={y}
              width={SQUARE_SIZE}
              height={SQUARE_SIZE}
              fill={`rgba(255, 100, 50, ${intensity * 0.55})`}
              rx={2}
            />
          )
        })
      )}
    </svg>
  )
}