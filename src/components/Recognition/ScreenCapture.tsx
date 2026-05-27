import React, { useState, useCallback } from 'react'
import { useBoardRecognition } from '@/hooks/useBoardRecognition'
import { Monitor, Crosshair, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { CalibrationData } from '@/types'

export function ScreenCapture() {
  const {
    isCapturing,
    lastResult,
    confidence,
    error,
    captureScreen,
    applyPosition,
  } = useBoardRecognition()

  const [region, setRegion] = useState<CalibrationData | null>(null)
  const [screenSources, setScreenSources] = useState<
    Array<{ id: string; name: string; thumbnail: string }>
  >([])
  const [showSources, setShowSources] = useState(false)

  const handleLoadSources = async () => {
    if (window.electronAPI) {
      const sources = await window.electronAPI.getScreenSources()
      setScreenSources(sources)
      setShowSources(true)
    }
  }

  const handleCapture = useCallback(async () => {
    await captureScreen(region ?? undefined)
  }, [captureScreen, region])

  const confidencePct = Math.round(confidence * 100)
  const isGoodResult = confidence > 0.85

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Monitor size={16} className="text-chess-accent" />
        <h3 className="text-sm font-semibold text-white">Screen Capture</h3>
      </div>

      {/* Instructions */}
      <div className="text-xs text-gray-400 bg-white/5 rounded-lg p-3 border border-gray-700/30">
        <p>Capture a chess board from your screen. Works with Chess.com, Lichess, and other platforms.</p>
      </div>

      {/* Capture button */}
      <button
        onClick={handleCapture}
        disabled={isCapturing}
        className="w-full flex items-center justify-center gap-2 py-3 rounded-lg
          bg-chess-accent hover:bg-chess-accent/80 text-white font-medium
          transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isCapturing ? (
          <>
            <Loader size={16} className="animate-spin" />
            Capturing...
          </>
        ) : (
          <>
            <Crosshair size={16} />
            Capture Board
          </>
        )}
      </button>

      {/* Electron: screen source picker */}
      {window.electronAPI && (
        <button
          onClick={handleLoadSources}
          className="w-full py-2 rounded-lg border border-gray-700 text-gray-400
            hover:text-white hover:border-gray-600 text-xs transition-colors"
        >
          Select Window / Screen
        </button>
      )}

      {/* Source picker modal */}
      {showSources && screenSources.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-400">Select source:</p>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
            {screenSources.map((src) => (
              <button
                key={src.id}
                onClick={() => setShowSources(false)}
                className="flex flex-col items-center gap-1 p-2 rounded border
                  border-gray-700 hover:border-chess-accent text-xs text-gray-400
                  hover:text-white transition-colors"
              >
                <img
                  src={src.thumbnail}
                  alt={src.name}
                  className="w-full h-16 object-cover rounded opacity-80"
                />
                <span className="truncate w-full text-center">{src.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10
          border border-red-500/30 text-red-400 text-xs">
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Result */}
      {lastResult && (
        <div className={`p-3 rounded-lg border text-xs space-y-2 ${
          isGoodResult
            ? 'bg-green-500/10 border-green-500/30'
            : 'bg-yellow-500/10 border-yellow-500/30'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              {isGoodResult
                ? <CheckCircle size={14} className="text-green-400" />
                : <AlertCircle size={14} className="text-yellow-400" />
              }
              <span className={isGoodResult ? 'text-green-400' : 'text-yellow-400'}>
                {isGoodResult ? 'Board Detected' : 'Low Confidence'}
              </span>
            </div>
            <span className="font-mono text-gray-300">{confidencePct}%</span>
          </div>

          <div className="font-mono text-gray-400 break-all leading-relaxed">
            {lastResult.fen}
          </div>

          {!isGoodResult && (
            <button
              onClick={() => applyPosition(lastResult)}
              className="w-full py-1.5 rounded border border-yellow-500/30
                text-yellow-400 hover:bg-yellow-500/10 transition-colors"
            >
              Apply Anyway
            </button>
          )}
        </div>
      )}
    </div>
  )
}