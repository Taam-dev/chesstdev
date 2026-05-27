import React from 'react'
import { useAppSelector } from '@/store'

interface EvaluationBadgeProps {
  /** Override value (centipawns). If omitted, reads from Redux store. */
  value?: number
  mate?: number | null
  className?: string
}

export function EvaluationBadge({ value, mate, className = '' }: EvaluationBadgeProps) {
  const analysis = useAppSelector((state) => state.analysis.current)

  const eval_ = value ?? analysis?.evaluation ?? 0
  const mate_ = mate !== undefined ? mate : analysis?.mate

  const isMate = mate_ !== undefined && mate_ !== null

  const pawns   = Math.abs(eval_ / 100)
  const sign    = eval_ > 0 ? '+' : eval_ < 0 ? '-' : ''
  const display = isMate ? `M${Math.abs(mate_!)}` : `${sign}${pawns.toFixed(1)}`

  const bgColor =
    isMate && mate_! > 0 ? 'bg-white text-gray-900'
    : isMate && mate_! < 0 ? 'bg-gray-900 text-white border border-gray-600'
    : eval_ > 50  ? 'bg-white text-gray-900'
    : eval_ < -50 ? 'bg-gray-900 text-white border border-gray-600'
    : 'bg-gray-500 text-white'

  return (
    <div
      className={`inline-flex items-center justify-center px-2 py-0.5 rounded
        text-xs font-bold font-mono min-w-[52px] ${bgColor} ${className}`}
    >
      {display}
    </div>
  )
}