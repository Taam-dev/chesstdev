import React, { useCallback, useState, useMemo } from 'react'
import { Chessboard } from 'react-chessboard'
import { Chess } from 'chess.js'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '@/store'
import { addMove } from '@/store/gameSlice'
import { EvaluationBar } from './EvaluationBar'
import { MoveArrows } from './MoveArrows'
import { BoardHeatmap } from './BoardHeatmap'
import { MoveQualityBadge } from '../Analysis/MoveQuality'
import { motion, AnimatePresence } from 'framer-motion'
import { MoveRecord } from '@/types'

export function ChessBoard() {
  const dispatch = useDispatch()
  const { fen, orientation, moves, currentMoveIndex } = useSelector(
    (state: RootState) => state.game
  )
  const { current: analysis, showAnnotationsMode } = useSelector(
    (state: RootState) => state.analysis
  )

  const [isDragging, setIsDragging] = useState(false)
  const [hoverSquare, setHoverSquare] = useState<string | null>(null)
  const [lastMove, setLastMove] = useState<{ from: string; to: string } | null>(null)

  // ─── Square styles ────────────────────────────────────────────────────────────

  const customSquareStyles = useMemo(() => {
    const styles: Record<string, React.CSSProperties> = {}

    if (lastMove) {
      styles[lastMove.from] = { background: 'rgba(255,255,0,0.25)' }
      styles[lastMove.to]   = { background: 'rgba(255,255,0,0.35)' }
    }

    if (analysis?.bestMove) {
      const from = analysis.bestMove.slice(0, 2)
      const to   = analysis.bestMove.slice(2, 4)
      styles[from] = { background: 'rgba(0,184,148,0.35)' }
      styles[to]   = { background: 'rgba(0,184,148,0.50)' }
    }

    if (hoverSquare && isDragging) {
      styles[hoverSquare] = { background: 'rgba(255,255,255,0.2)' }
    }

    return styles
  }, [lastMove, analysis, hoverSquare, isDragging])

  // ─── Move handler ─────────────────────────────────────────────────────────────

  const onDrop = useCallback(
    (sourceSquare: string, targetSquare: string, piece: string): boolean => {
      const chess = new Chess(fen)
      try {
        const moveResult = chess.move({
          from: sourceSquare,
          to:   targetSquare,
          promotion:
            piece[1]?.toLowerCase() === 'p' &&
            (targetSquare[1] === '8' || targetSquare[1] === '1')
              ? 'q'
              : undefined,
        })
        if (!moveResult) return false

        const record: MoveRecord = {
          index:     moves.length,
          move:      { from: sourceSquare, to: targetSquare },
          san:       moveResult.san,
          fen:       chess.fen(),
          fenBefore: fen,
          timestamp: Date.now(),
        }
        dispatch(addMove(record))
        setLastMove({ from: sourceSquare, to: targetSquare })
        return true
      } catch {
        return false
      }
    },
    [fen, moves.length, dispatch]
  )

  const currentMove = moves[currentMoveIndex]

  return (
    <div className="flex gap-4 items-center">
      <EvaluationBar />

      <div className="relative">
        {/* Heatmap + Arrows overlays */}
        <BoardHeatmap />
        <MoveArrows />

        {/* Move quality badge */}
        <AnimatePresence>
          {showAnnotationsMode && currentMove?.quality && (
            <motion.div
              key={currentMoveIndex}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              className="absolute -top-3 -right-3 z-20"
            >
              <MoveQualityBadge quality={currentMove.quality} size="lg" />
            </motion.div>
          )}
        </AnimatePresence>

        <Chessboard
          position={fen}
          onPieceDrop={onDrop}
          onPieceDragBegin={() => setIsDragging(true)}
          onPieceDragEnd={() => { setIsDragging(false); setHoverSquare(null) }}
          onSquareClick={(sq) => setHoverSquare(sq)}
          boardOrientation={orientation}
          customSquareStyles={customSquareStyles}
          animationDuration={200}
          boardWidth={560}
          customBoardStyle={{
            borderRadius: '8px',
            boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          }}
          customDarkSquareStyle={{ backgroundColor: '#b58863' }}
          customLightSquareStyle={{ backgroundColor: '#f0d9b5' }}
        />
      </div>
    </div>
  )
}