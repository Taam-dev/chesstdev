import React from 'react'
import { useAppSelector } from '@/store'
import { TacticPattern } from '@/types'

const TACTIC_ICONS: Record<string, string> = {
  fork: '⑂',
  pin: '📌',
  skewer: '⚔️',
  discovered_attack: '💥',
  discovered_check: '👁️',
  double_check: '‼️',
  mating_net: '♚',
  hanging_piece: '⚠️',
  passed_pawn: '♟️',
  weak_square: '◻️',
  open_file: '|',
  back_rank: '🔒',
  zwischenzug: '↩️',
  zugzwang: '🔄',
}

const SEVERITY_COLORS: Record<string, string> = {
  low: 'text-blue-400 border-blue-400/30 bg-blue-400/10',
  medium: 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10',
  high: 'text-orange-400 border-orange-400/30 bg-orange-400/10',
  critical: 'text-red-400 border-red-400/30 bg-red-400/10',
}

interface TacticCardProps {
  tactic: TacticPattern
}

const TacticCard: React.FC<TacticCardProps> = ({ tactic }) => {
  const colorClass = SEVERITY_COLORS[tactic.severity] ?? SEVERITY_COLORS.low
  const icon = TACTIC_ICONS[tactic.type] ?? '⚡'

  const formattedType = tactic.type
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <div className={`border rounded-lg p-3 ${colorClass}`}>
      <div className="flex items-start gap-2">
        <span className="text-lg flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="font-semibold text-sm">{formattedType}</span>
            <span
              className={`text-xs px-1.5 py-0.5 rounded-full border capitalize
                ${colorClass}`}
            >
              {tactic.severity}
            </span>
          </div>
          <p className="text-xs mt-1 text-gray-300 leading-relaxed">
            {tactic.description}
          </p>
          {tactic.squares.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {tactic.squares.map((sq) => (
                <span
                  key={sq}
                  className="text-xs font-mono px-1.5 py-0.5 rounded bg-black/30 border border-white/10"
                >
                  {sq}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export const TacticsDetector: React.FC = () => {
  const tactics = useAppSelector((state) => state.analysis.tactics)
  const isAnalyzing = useAppSelector((state) => state.analysis.isAnalyzing)

  if (isAnalyzing && tactics.length === 0) {
    return (
      <div className="p-4">
        <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">
          Tactics
        </h3>
        <div className="flex items-center gap-2 text-gray-500">
          <div className="w-3 h-3 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Scanning for tactics...</span>
        </div>
      </div>
    )
  }

  if (tactics.length === 0) {
    return (
      <div className="p-4">
        <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">
          Tactics
        </h3>
        <p className="text-sm text-gray-500 italic">No tactical patterns detected</p>
      </div>
    )
  }

  // Sort by severity
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
  const sorted = [...tactics].sort(
    (a, b) =>
      (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3)
  )

  return (
    <div className="p-4">
      <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider flex items-center gap-2">
        Tactics
        <span className="text-xs bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded-full">
          {tactics.length}
        </span>
      </h3>
      <div className="space-y-2">
        {sorted.map((tactic, idx) => (
          <TacticCard key={idx} tactic={tactic} />
        ))}
      </div>
    </div>
  )
}