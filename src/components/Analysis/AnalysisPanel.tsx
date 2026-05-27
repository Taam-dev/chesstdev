import React, { useState } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { MoveExplanation } from './MoveExplanation'
import { PrincipalVariation } from './PrincipalVariation'
import { TacticsDetector } from './TacticsDetector'
import { EngineSettings } from '../Settings/EngineSettings'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Settings, Target, ChevronDown } from 'lucide-react'

type PanelTab = 'lines' | 'explanation' | 'tactics' | 'settings'

export function AnalysisPanel() {
  const [activeTab, setActiveTab] = useState<PanelTab>('lines')
  const { current: analysis, isAnalyzing, isEngineReady, backendConnected } = useSelector(
    (state: RootState) => state.analysis
  )
  const { moves, currentMoveIndex } = useSelector((state: RootState) => state.game)

  const currentMove = moves[currentMoveIndex]

  const tabs = [
    { id: 'lines' as PanelTab, label: 'Lines', icon: '📊' },
    { id: 'explanation' as PanelTab, label: 'Coach', icon: '🎓' },
    { id: 'tactics' as PanelTab, label: 'Tactics', icon: '⚡' },
    { id: 'settings' as PanelTab, label: 'Engine', icon: '⚙️' },
  ]

  return (
    <div className="flex flex-col h-full bg-chess-panel rounded-xl border border-gray-700/50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-chess-accent" />
            <h2 className="font-semibold text-white">Analysis</h2>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                !backendConnected
                  ? 'bg-red-500'
                  : !isEngineReady
                  ? 'bg-yellow-500 animate-pulse'
                  : isAnalyzing
                  ? 'bg-chess-green animate-pulse'
                  : 'bg-chess-green'
              }`}
            />
            <span className="text-xs text-gray-400">
              {!backendConnected
                ? 'Offline'
                : !isEngineReady
                ? 'Starting...'
                : isAnalyzing
                ? 'Analyzing...'
                : 'Ready'}
            </span>
          </div>
        </div>

        {/* Depth progress */}
        {isAnalyzing && analysis && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Depth {analysis.depth}</span>
              <span>{(analysis.nps / 1000).toFixed(0)}k nps</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1">
              <motion.div
                className="bg-chess-accent h-1 rounded-full"
                animate={{ width: `${Math.min((analysis.depth / 30) * 100, 100)}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-700/50">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-1 py-2 text-xs font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-chess-accent border-b-2 border-chess-accent bg-chess-accent/5'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="h-full"
          >
            {activeTab === 'lines' && <PrincipalVariation />}
            {activeTab === 'explanation' && (
              <MoveExplanation move={currentMove} />
            )}
            {activeTab === 'tactics' && <TacticsDetector />}
            {activeTab === 'settings' && <EngineSettings />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}