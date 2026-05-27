import React, { useState } from 'react'
import { useAppSelector, useAppDispatch } from '@/store'
import { setAnalysisMode } from '@/store/analysisSlice'
import { AnalysisPanel } from '@/components/Analysis/AnalysisPanel'
import { MoveHistory } from '@/components/MoveHistory/MoveHistory'
import { TacticsDetector } from '@/components/Analysis/TacticsDetector'
import { AnalysisTimeline } from '@/components/MoveHistory/AnalysisTimeline'

type SidebarTab = 'analysis' | 'moves' | 'tactics'

const TABS: { id: SidebarTab; label: string; icon: string }[] = [
  { id: 'analysis', label: 'Analysis', icon: '⚡' },
  { id: 'moves', label: 'Moves', icon: '♟' },
  { id: 'tactics', label: 'Tactics', icon: '⚔️' },
]

export const Sidebar: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SidebarTab>('analysis')
  const dispatch = useAppDispatch()
  const { isEngineReady, backendConnected } = useAppSelector(
    (state) => state.analysis
  )
  const movesCount = useAppSelector((state) => state.game.moves.length)

  return (
    <div className="flex flex-col h-full bg-gray-900/50 border-l border-gray-800">
      {/* Connection status */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-800 bg-gray-900/80">
        <div
          className={`w-2 h-2 rounded-full ${
            backendConnected && isEngineReady
              ? 'bg-green-500 animate-pulse'
              : backendConnected
              ? 'bg-yellow-500'
              : 'bg-red-500'
          }`}
        />
        <span className="text-xs text-gray-400">
          {backendConnected && isEngineReady
            ? 'Engine Ready'
            : backendConnected
            ? 'Connecting Engine...'
            : 'Backend Offline'}
        </span>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-gray-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex-1 flex items-center justify-center gap-1.5
              py-2.5 text-xs font-medium transition-colors relative
              ${
                activeTab === tab.id
                  ? 'text-white bg-gray-800/50'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/30'
              }
            `}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.id === 'moves' && movesCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 text-[10px] bg-blue-600 rounded-full flex items-center justify-center">
                {movesCount > 99 ? '99+' : movesCount}
              </span>
            )}
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        {activeTab === 'analysis' && <AnalysisPanel />}
        {activeTab === 'moves' && (
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto">
              <MoveHistory />
            </div>
            <div className="border-t border-gray-800 flex-shrink-0">
              <AnalysisTimeline />
            </div>
          </div>
        )}
        {activeTab === 'tactics' && <TacticsDetector />}
      </div>
    </div>
  )
}