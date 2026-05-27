import React from 'react'
import { useSelector } from 'react-redux'
import { useAppDispatch } from '@/store'
import { RootState } from '@/store'
import { toggleAnnotationsMode } from '@/store/analysisSlice'
import { motion } from 'framer-motion'

export function PrincipalVariation() {
  const dispatch = useAppDispatch()
  const { current: analysis, showAnnotationsMode } = useSelector(
    (state: RootState) => state.analysis
  )

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-gray-500">
        <div className="text-4xl mb-2">♟</div>
        <p className="text-sm">Make a move to start analysis</p>
      </div>
    )
  }

  const isMate = analysis.mate !== undefined && analysis.mate !== null
  const evalAbs = Math.abs(analysis.evaluation / 100).toFixed(2)
  const evalSign = analysis.evaluation > 0 ? '+' : analysis.evaluation < 0 ? '-' : ''
  const evalDisplay = isMate ? `M${Math.abs(analysis.mate!)}` : `${evalSign}${evalAbs}`

  const evalColor =
    analysis.evaluation > 100 ? '#94c23c'
    : analysis.evaluation < -100 ? '#ca3431'
    : '#f5f5f5'

  return (
    <div className="p-4 space-y-4">
      {/* Main Evaluation */}
      <div className="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-gray-700/30">
        <div>
          <div className="text-2xl font-bold font-mono" style={{ color: evalColor }}>
            {evalDisplay}
          </div>
          <div className="text-xs text-gray-400 mt-0.5">
            Depth {analysis.depth}
            {analysis.nps > 0 && ` • ${(analysis.nps / 1_000_000).toFixed(1)}M nps`}
          </div>
        </div>

        {analysis.bestMoveSAN && (
          <div className="text-right">
            <div className="text-xs text-gray-400 mb-1">Best Move</div>
            <div className="bg-chess-accent/20 border border-chess-accent/50 rounded px-3 py-1">
              <span className="text-chess-accent font-bold font-mono">
                {analysis.bestMoveSAN}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Lines */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Top Lines
        </h3>

        {analysis.lines.map((line, idx) => {
          const lineIsMate = line.mate !== undefined && line.mate !== null
          const lineEvalAbs = Math.abs(line.evaluation / 100).toFixed(2)
          const lineSign = line.evaluation > 0 ? '+' : line.evaluation < 0 ? '-' : ''
          const lineEval = lineIsMate
            ? `M${Math.abs(line.mate!)}`
            : `${lineSign}${lineEvalAbs}`

          const lineColor =
            idx === 0 ? '#94c23c' : idx === 1 ? '#6c5ce7' : '#a0a0a0'

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="bg-white/5 rounded-lg p-3 border border-gray-700/30"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center
                    text-xs font-bold flex-shrink-0"
                  style={{
                    backgroundColor: `${lineColor}20`,
                    border: `1px solid ${lineColor}`,
                    color: lineColor,
                  }}
                >
                  {idx + 1}
                </div>

                <span
                  className="text-sm font-bold font-mono w-16 flex-shrink-0"
                  style={{ color: lineColor }}
                >
                  {lineEval}
                </span>

                <div className="flex-1 flex flex-wrap gap-1 overflow-hidden">
                  {line.moves.slice(0, 8).map((move, mIdx) => (
                    <span
                      key={mIdx}
                      className="text-xs font-mono px-1 py-0.5 rounded"
                      style={{
                        backgroundColor: mIdx === 0 ? `${lineColor}20` : 'transparent',
                        color: mIdx === 0 ? lineColor : '#aaa',
                        fontWeight: mIdx === 0 ? 'bold' : 'normal',
                      }}
                    >
                      {move}
                    </span>
                  ))}
                  {line.moves.length > 8 && (
                    <span className="text-xs text-gray-600">...</span>
                  )}
                </div>
              </div>
            </motion.div>
          )
        })}

        {analysis.lines.length === 0 && (
          <div className="text-center text-gray-600 text-sm py-4">
            Waiting for engine lines...
          </div>
        )}
      </div>

      {/* Annotations toggle */}
      <div className="pt-2 border-t border-gray-700/30">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-white font-medium">Move Annotations</div>
            <div className="text-xs text-gray-400">
              Show quality badges on moves
            </div>
          </div>
          <button
            onClick={() => dispatch(toggleAnnotationsMode())}
            className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
              showAnnotationsMode ? 'bg-chess-accent' : 'bg-gray-600'
            }`}
            role="switch"
            aria-checked={showAnnotationsMode}
          >
            <div
              className={`absolute w-4 h-4 rounded-full bg-white top-1 shadow
                transition-transform duration-200 ${
                showAnnotationsMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  )
}