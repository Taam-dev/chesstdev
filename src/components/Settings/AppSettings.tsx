import React from 'react'
import { useAppDispatch, useAppSelector } from '@/store'
import {
  toggleShowAnnotations,
  toggleShowArrows,
  toggleShowHeatmap,
  toggleAutoAnalyze,
  toggleSound,
  setAnimationSpeed,
  setBoardTheme,
  setLanguage,
} from '@/store/settingsSlice'

export function AppSettings() {
  const dispatch = useAppDispatch()
  const { app } = useAppSelector((state) => state.settings)

  const boardThemes = [
    { id: 'green',  label: 'Classic Green',  light: '#f0d9b5', dark: '#b58863' },
    { id: 'blue',   label: 'Ocean Blue',     light: '#dee3e6', dark: '#8ca2ad' },
    { id: 'purple', label: 'Purple',         light: '#e8d0f0', dark: '#9c59b0' },
    { id: 'brown',  label: 'Walnut',         light: '#f0c98a', dark: '#9d6f40' },
  ]

  return (
    <div className="p-4 space-y-5">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
        Display
      </h3>

      <div className="space-y-3">
        <Toggle
          label="Move Annotations"
          description="Chess.com-style quality badges"
          checked={app.showAnnotations}
          onChange={() => dispatch(toggleShowAnnotations())}
        />
        <Toggle
          label="Best Move Arrows"
          description="Show engine suggestion arrows"
          checked={app.showArrows}
          onChange={() => dispatch(toggleShowArrows())}
        />
        <Toggle
          label="Position Heatmap"
          description="Piece activity visualization"
          checked={app.showHeatmap}
          onChange={() => dispatch(toggleShowHeatmap())}
        />
        <Toggle
          label="Auto-Analyze"
          description="Analyze each position automatically"
          checked={app.autoAnalyze}
          onChange={() => dispatch(toggleAutoAnalyze())}
        />
        <Toggle
          label="Sound Effects"
          description="Move and capture sounds"
          checked={app.soundEnabled}
          onChange={() => dispatch(toggleSound())}
        />
      </div>

      {/* Animation Speed */}
      <div className="pt-3 border-t border-gray-700/30 space-y-2">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Animation Speed
        </h3>
        <div className="flex gap-2">
          {(['slow', 'normal', 'fast'] as const).map((speed) => (
            <button
              key={speed}
              onClick={() => dispatch(setAnimationSpeed(speed))}
              className={`flex-1 py-1.5 rounded text-xs font-medium capitalize
                transition-colors ${
                app.animationSpeed === speed
                  ? 'bg-chess-accent text-white'
                  : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {speed}
            </button>
          ))}
        </div>
      </div>

      {/* Board Theme */}
      <div className="pt-3 border-t border-gray-700/30 space-y-2">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Board Theme
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {boardThemes.map((theme) => (
            <button
              key={theme.id}
              onClick={() => dispatch(setBoardTheme(theme.id))}
              className={`flex items-center gap-2 p-2 rounded-lg border transition-colors ${
                app.boardTheme === theme.id
                  ? 'border-chess-accent bg-chess-accent/10'
                  : 'border-gray-700/50 hover:border-gray-600 bg-white/5'
              }`}
            >
              {/* Color preview */}
              <div className="grid grid-cols-2 gap-0.5 w-6 h-6 rounded overflow-hidden flex-shrink-0">
                <div style={{ backgroundColor: theme.light }} />
                <div style={{ backgroundColor: theme.dark }} />
                <div style={{ backgroundColor: theme.dark }} />
                <div style={{ backgroundColor: theme.light }} />
              </div>
              <span className="text-xs text-gray-300 text-left leading-tight">
                {theme.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Language */}
      <div className="pt-3 border-t border-gray-700/30 space-y-2">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Language
        </h3>
        <div className="flex gap-2">
          {([
            { id: 'en', label: '🇬🇧 English' },
            { id: 'vi', label: '🇻🇳 Tiếng Việt' },
          ] as const).map(({ id, label }) => (
            <button
              key={id}
              onClick={() => dispatch(setLanguage(id))}
              className={`flex-1 py-1.5 rounded text-xs font-medium transition-colors ${
                app.language === id
                  ? 'bg-chess-accent text-white'
                  : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Toggle component ─────────────────────────────────────────────────────────

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  onChange: () => void
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex-1 min-w-0">
        <div className="text-sm text-white font-medium">{label}</div>
        <div className="text-xs text-gray-500 mt-0.5">{description}</div>
      </div>
      <button
        onClick={onChange}
        role="switch"
        aria-checked={checked}
        className={`relative w-10 h-5 rounded-full transition-colors duration-200
          flex-shrink-0 ${checked ? 'bg-chess-accent' : 'bg-gray-600'}`}
      >
        <div
          className={`absolute w-3.5 h-3.5 rounded-full bg-white top-[3px] shadow
            transition-transform duration-200 ${
            checked ? 'translate-x-[22px]' : 'translate-x-[3px]'
          }`}
        />
      </button>
    </div>
  )
}