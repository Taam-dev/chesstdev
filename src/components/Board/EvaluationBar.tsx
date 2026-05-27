import React, { useMemo } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { motion } from 'framer-motion'

export function EvaluationBar() {
  const { current: analysis } = useSelector((state: RootState) => state.analysis)

  const { whitePercent, displayText, isMate } = useMemo(() => {
    if (!analysis) {
      return { whitePercent: 50, displayText: '0.0', isMate: false }
    }

    if (analysis.mate !== undefined && analysis.mate !== null) {
      const isWhiteMating = analysis.mate > 0
      return {
        whitePercent: isWhiteMating ? 95 : 5,
        displayText: `M${Math.abs(analysis.mate)}`,
        isMate: true,
      }
    }

    const eval_ = analysis.evaluation
    // Convert centipawns to percentage (sigmoid-like function)
    const evalInPawns = eval_ / 100
    const percent = 50 + (50 * Math.tanh(evalInPawns / 3))

    const displayEval = Math.abs(evalInPawns).toFixed(1)
    const sign = evalInPawns > 0 ? '+' : evalInPawns < 0 ? '-' : ''

    return {
      whitePercent: Math.max(5, Math.min(95, percent)),
      displayText: `${sign}${displayEval}`,
      isMate: false,
    }
  }, [analysis])

  return (
    <div className="flex flex-col items-center h-[560px] w-10 relative">
      {/* Black percentage */}
      <div
        className="absolute top-0 text-xs font-bold text-center w-full py-1"
        style={{ fontSize: '10px', color: analysis?.evaluation && analysis.evaluation < 0 ? '#f5f5f5' : '#888' }}
      >
        {analysis?.evaluation && analysis.evaluation < 0 ? displayText : ''}
      </div>

      {/* Bar */}
      <div className="relative flex-1 w-10 bg-gray-900 rounded-lg overflow-hidden shadow-xl border border-gray-700">
        {/* White portion (bottom) */}
        <motion.div
          className="absolute bottom-0 w-full bg-white"
          animate={{ height: `${whitePercent}%` }}
          transition={{ type: 'spring', stiffness: 200, damping: 30 }}
        />

        {/* Black portion (top) */}
        <div
          className="absolute top-0 w-full bg-gray-800"
          style={{ height: `${100 - whitePercent}%` }}
        />

        {/* Center line */}
        <div className="absolute w-full h-px bg-gray-500" style={{ top: '50%' }} />

        {/* Evaluation text on bar */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span
            className="text-xs font-mono font-bold transform -rotate-90 whitespace-nowrap"
            style={{
              color: whitePercent > 50 ? '#1a1a2e' : '#f5f5f5',
              fontSize: '10px',
              textShadow: '0 1px 2px rgba(0,0,0,0.5)',
            }}
          >
            {displayText}
          </span>
        </div>

        {/* Mate indicator */}
        {isMate && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{ background: whitePercent > 50 ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
          >
            <span className="text-xs font-bold animate-pulse"
              style={{ color: whitePercent > 50 ? '#1a1a2e' : '#fff' }}>
              ♚
            </span>
          </div>
        )}
      </div>

      {/* White percentage */}
      <div
        className="absolute bottom-0 text-xs font-bold text-center w-full py-1"
        style={{ fontSize: '10px', color: analysis?.evaluation && analysis.evaluation > 0 ? '#1a1a2e' : '#888' }}
      >
        {analysis?.evaluation && analysis.evaluation > 0 ? displayText : ''}
      </div>
    </div>
  )
}