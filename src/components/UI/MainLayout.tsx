import React from 'react'
import { ChessBoard } from '../Board/ChessBoard'
import { Sidebar } from './Sidebar'
import { useAnalysis } from '@/hooks/useAnalysis'

export function MainLayout() {
  useAnalysis() // Initialize analysis hook - WebSocket connection, auto-analyze

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main Content: Board */}
      <div className="flex flex-col items-center justify-center flex-1 min-w-0 p-4">
        <ChessBoard />
      </div>

      {/* Right Sidebar: Analysis / Moves / Tactics */}
      <div className="w-80 xl:w-96 flex-shrink-0 border-l border-gray-800 overflow-hidden">
        <Sidebar />
      </div>
    </div>
  )
}