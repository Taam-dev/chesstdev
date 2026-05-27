import React from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { useAppDispatch } from '@/store'
import { MoveRecord } from '@/types'
import { MoveQualityBadge } from './MoveQuality'
import { useAnalysis } from '@/hooks/useAnalysis'
import { motion } from 'framer-motion'
import { RefreshCw, BookOpen } from 'lucide-react'

interface MoveExplanationProps {
  move?: MoveRecord
}

export function MoveExplanation({ move }: MoveExplanationProps) {
  const { currentExplanation } = useSelector((state: RootState) => state.analysis)
  const { currentMoveIndex } = useSelector((state: RootState) => state.game)
  const { explainMove } = useAnalysis()

  const explanation = move?.explanation ?? currentExplanation

  const handleExplain = () => {
    if (currentMoveIndex >= 0) {
      explainMove(currentMoveIndex)
    }
  }

  // ─── Empty state ──────────────────────────────────────────────────────────────
  if (!move && !explanation) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-gray-500 p-4">
        <BookOpen className="w-10 h-10 mb-2 opacity-30" />
        <p className="text-sm text-center">Navigate to a move to see coaching explanation</p>
      </div>
    )
  }

  // ─── No explanation yet ───────────────────────────────────────────────────────
  if (!explanation) {
    return (
      <div className="p-4 flex flex-col items-center gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-white font-mono mb-1">{move?.san}</div>
          <div className="text-sm text-gray-400">No explanation generated yet</div>
        </div>
        <button
          onClick={handleExplain}
          className="flex items-center gap-2 px-4 py-2 bg-chess-accent
            hover:bg-chess-accent/80 text-white rounded-lg text-sm font-medium
            transition-colors"
        >
          <BookOpen size={14} />
          Explain This Move
        </button>
      </div>
    )
  }

  // ─── Quality color ────────────────────────────────────────────────────────────
  const qualityColorMap: Record<string, string> = {
    brilliant:  '#00d4ff',
    great:      '#5c8bb0',
    best:       '#94c23c',
    good:       '#84cc16',
    inaccuracy: '#f6b740',
    mistake:    '#f97316',
    blunder:    '#ef4444',
    miss:       '#dc2626',
  }
  const qualityColor = qualityColorMap[explanation.quality?.label ?? ''] ?? '#888'

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-4 space-y-4"
    >
      {/* Move Header */}
      <div
        className="rounded-lg p-3 border"
        style={{
          backgroundColor: `${qualityColor}15`,
          borderColor: `${qualityColor}40`,
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white font-mono">{explanation.san}</span>
            {explanation.quality && (
              <MoveQualityBadge quality={explanation.quality} size="md" showLabel />
            )}
          </div>
        </div>
        <p className="text-sm mt-2 text-gray-200 leading-relaxed">{explanation.summary}</p>
      </div>

      {/* Sections */}
      <div className="space-y-3">
        <Section icon="🎯" title="Tactical Purpose"   content={explanation.tactical}   color="#e94560" />
        <Section icon="♟️" title="Strategic Idea"     content={explanation.strategic}  color="#6c5ce7" />
        <Section icon="🏰" title="Positional Impact"  content={explanation.positional} color="#00b894" />
        <Section icon="⚡" title="Threats Created"    content={explanation.threats}    color="#f5a623" />
        <Section icon="⚠️" title="If Ignored..."      content={explanation.risks}      color="#ca3431" />
      </div>

      {/* Tactics tags */}
      {explanation.tactics && explanation.tactics.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Tactics Detected
          </h3>
          <div className="flex flex-wrap gap-2">
            {explanation.tactics.map((tactic, idx) => (
              <span
                key={idx}
                className="px-2 py-1 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: '#e9456030',
                  color: '#e94560',
                  border: '1px solid #e9456040',
                }}
              >
                ⚡ {tactic.type.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Regenerate */}
      <button
        onClick={handleExplain}
        className="w-full flex items-center justify-center gap-2 py-2 border
          border-gray-700 hover:border-chess-accent text-gray-400
          hover:text-chess-accent rounded-lg text-xs transition-colors"
      >
        <RefreshCw size={12} />
        Regenerate Explanation
      </button>
    </motion.div>
  )
}

function Section({
  icon, title, content, color,
}: {
  icon: string; title: string; content: string; color: string
}) {
  if (!content) return null
  return (
    <div className="bg-white/5 rounded-lg p-3 border border-gray-700/20">
      <div className="flex items-center gap-2 mb-1.5">
        <span>{icon}</span>
        <h4 className="text-xs font-semibold uppercase tracking-wider" style={{ color }}>
          {title}
        </h4>
      </div>
      <p className="text-sm text-gray-300 leading-relaxed">{content}</p>
    </div>
  )
}