import React from 'react'
import { MoveQualityType } from '@/types'
import { motion } from 'framer-motion'

// ─── Quality Config ───────────────────────────────────────────────────────────

export const QUALITY_CONFIG: Record<
  MoveQualityType['label'],
  { color: string; bg: string; symbol: string; label: string }
> = {
  brilliant:  { color: '#00d4ff', bg: '#00d4ff20', symbol: '✨', label: 'Brilliant' },
  great:      { color: '#5c8bb0', bg: '#5c8bb020', symbol: '!!',  label: 'Great'     },
  best:       { color: '#94c23c', bg: '#94c23c20', symbol: '!',   label: 'Best'      },
  good:       { color: '#84cc16', bg: '#84cc1620', symbol: '✓',   label: 'Good'      },
  inaccuracy: { color: '#f6b740', bg: '#f6b74020', symbol: '⊙',   label: 'Inaccuracy'},
  mistake:    { color: '#f97316', bg: '#f9731620', symbol: '?',   label: 'Mistake'   },
  blunder:    { color: '#ef4444', bg: '#ef444420', symbol: '??',  label: 'Blunder'   },
  miss:       { color: '#dc2626', bg: '#dc262620', symbol: '??',  label: 'Miss'      },
}

// ─── MoveQualityBadge ─────────────────────────────────────────────────────────

interface MoveQualityBadgeProps {
  quality: MoveQualityType
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export function MoveQualityBadge({
  quality,
  size = 'md',
  showLabel = false,
}: MoveQualityBadgeProps) {
  const config = QUALITY_CONFIG[quality.label]
  if (!config) return null

  const sizeClasses = {
    sm: 'w-4 h-4 text-[9px]',
    md: 'w-5 h-5 text-[10px]',
    lg: 'w-7 h-7 text-xs',
  }[size]

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      className="flex items-center gap-1"
    >
      <div
        className={`${sizeClasses} rounded-full flex items-center justify-center font-bold
          border-2 border-white/20 shadow-lg flex-shrink-0`}
        style={{ backgroundColor: config.color }}
        title={config.label}
      >
        <span style={{ fontSize: size === 'sm' ? 7 : size === 'md' ? 9 : 11 }}>
          {config.symbol}
        </span>
      </div>
      {showLabel && (
        <span className="text-xs font-medium" style={{ color: config.color }}>
          {config.label}
        </span>
      )}
    </motion.div>
  )
}

// ─── MoveQualityBar (stats summary) ──────────────────────────────────────────

interface QualitySummary {
  brilliant: number
  great: number
  best: number
  good: number
  inaccuracy: number
  mistake: number
  blunder: number
  miss: number
}

interface MoveQualityBarProps {
  summary: QualitySummary
  total: number
}

export function MoveQualityBar({ summary, total }: MoveQualityBarProps) {
  if (total === 0) return null

  const labels = Object.keys(QUALITY_CONFIG) as MoveQualityType['label'][]

  return (
    <div className="space-y-1.5">
      {labels.map((label) => {
        const count = summary[label] ?? 0
        if (count === 0) return null
        const pct = (count / total) * 100
        const cfg = QUALITY_CONFIG[label]

        return (
          <div key={label} className="flex items-center gap-2 text-xs">
            <span className="w-20 text-gray-400 capitalize">{cfg.label}</span>
            <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, backgroundColor: cfg.color }}
              />
            </div>
            <span className="w-6 text-right text-gray-400">{count}</span>
          </div>
        )
      })}
    </div>
  )
}