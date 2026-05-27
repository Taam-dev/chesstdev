import React, { useEffect, useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/store'
import {
  setEngineDepth,
  setEngineThreads,
  setEngineHash,
  setMultiPV,
  setSkillLevel,
  setEnginePath,
} from '@/store/settingsSlice'
import { setDepth, setMultiPV as setAnalysisMultiPV } from '@/store/analysisSlice'
import { apiService } from '@/services/apiService'
import { storageService } from '@/services/storageService'
import { Cpu, Zap, Database, Target, FolderOpen, Info } from 'lucide-react'

export function EngineSettings() {
  const dispatch = useAppDispatch()
  const { engine } = useAppSelector((state) => state.settings)
  const { isEngineReady } = useAppSelector((state) => state.analysis)
  const [engineInfo, setEngineInfo] = useState<Record<string, string>>({})
  const [isBenchmarking, setIsBenchmarking] = useState(false)
  const [benchmarkResult, setBenchmarkResult] = useState<{
    nps: number; time: number
  } | null>(null)

  useEffect(() => {
    apiService.getEngineInfo().then(setEngineInfo).catch(() => {})
  }, [isEngineReady])

  const handleSelectEngine = async () => {
    if (window.electronAPI) {
      const path = await window.electronAPI.selectEnginePath()
      if (path) {
        dispatch(setEnginePath(path))
        await storageService.saveEnginePath(path)
      }
    }
  }

  const handleDepthChange = (val: number) => {
    dispatch(setEngineDepth(val))
    dispatch(setDepth(val))
  }

  const handleMultiPVChange = (val: number) => {
    dispatch(setMultiPV(val))
    dispatch(setAnalysisMultiPV(val))
    apiService.setEngineOption('MultiPV', val)
  }

  const handleThreadsChange = (val: number) => {
    dispatch(setEngineThreads(val))
    apiService.setEngineOption('Threads', val)
  }

  const handleHashChange = (val: number) => {
    dispatch(setEngineHash(val))
    apiService.setEngineOption('Hash', val)
  }

  const handleSkillLevelChange = (val: number) => {
    dispatch(setSkillLevel(val))
    apiService.setEngineOption('Skill Level', val)
  }

  const handleBenchmark = async () => {
    setIsBenchmarking(true)
    setBenchmarkResult(null)
    try {
      const result = await apiService.benchmarkEngine()
      setBenchmarkResult(result)
    } finally {
      setIsBenchmarking(false)
    }
  }

  const maxThreads = navigator.hardwareConcurrency ?? 4

  return (
    <div className="p-4 space-y-5">
      {/* Engine Status */}
      <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-gray-700/30">
        <div
          className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
            isEngineReady ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`}
        />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-white truncate">
            {engineInfo.version ?? (isEngineReady ? 'Stockfish' : 'Engine Offline')}
          </div>
          <div className="text-xs text-gray-400 truncate">
            {engine.path || 'Auto-detected'}
          </div>
        </div>
        {window.electronAPI && (
          <button
            onClick={handleSelectEngine}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs
              text-gray-400 hover:text-white hover:bg-white/10 transition-colors
              flex-shrink-0"
            title="Select engine binary"
          >
            <FolderOpen size={12} />
            Browse
          </button>
        )}
      </div>

      {/* Depth */}
      <SliderSetting
        icon={<Target size={14} />}
        label="Analysis Depth"
        value={engine.depth}
        min={5}
        max={30}
        step={1}
        display={`${engine.depth}`}
        onChange={handleDepthChange}
        color="#e94560"
      />

      {/* Threads */}
      <SliderSetting
        icon={<Cpu size={14} />}
        label="CPU Threads"
        value={engine.threads}
        min={1}
        max={maxThreads}
        step={1}
        display={`${engine.threads} / ${maxThreads}`}
        onChange={handleThreadsChange}
        color="#6c5ce7"
      />

      {/* Hash */}
      <SliderSetting
        icon={<Database size={14} />}
        label="Hash Table"
        value={engine.hash}
        min={16}
        max={2048}
        step={16}
        display={`${engine.hash} MB`}
        onChange={handleHashChange}
        color="#00b894"
      />

      {/* MultiPV */}
      <SliderSetting
        icon={<Zap size={14} />}
        label="Analysis Lines"
        value={engine.multiPV}
        min={1}
        max={5}
        step={1}
        display={`${engine.multiPV} lines`}
        onChange={handleMultiPVChange}
        color="#f5a623"
      />

      {/* Skill Level */}
      <SliderSetting
        icon={<span className="text-sm">♟</span>}
        label="Skill Level"
        value={engine.skillLevel}
        min={0}
        max={20}
        step={1}
        display={engine.skillLevel === 20 ? 'Maximum' : `${engine.skillLevel} / 20`}
        onChange={handleSkillLevelChange}
        color="#0984e3"
      />

      {/* Benchmark */}
      <div className="pt-2 border-t border-gray-700/30 space-y-2">
        <button
          onClick={handleBenchmark}
          disabled={isBenchmarking || !isEngineReady}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg
            border border-gray-700 hover:border-chess-accent text-gray-400
            hover:text-chess-accent transition-colors disabled:opacity-40
            disabled:cursor-not-allowed text-sm"
        >
          {isBenchmarking ? (
            <>
              <div className="w-3 h-3 border-2 border-current border-t-transparent
                rounded-full animate-spin" />
              Benchmarking...
            </>
          ) : (
            <>⚡ Run Benchmark</>
          )}
        </button>

        {benchmarkResult && (
          <div className="flex justify-between text-xs text-gray-400 px-1">
            <span>Speed: <span className="text-white font-mono">
              {(benchmarkResult.nps / 1_000_000).toFixed(1)}M nps
            </span></span>
            <span>Time: <span className="text-white font-mono">
              {benchmarkResult.time.toFixed(1)}s
            </span></span>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Slider Setting ───────────────────────────────────────────────────────────

interface SliderSettingProps {
  icon: React.ReactNode
  label: string
  value: number
  min: number
  max: number
  step: number
  display: string
  onChange: (val: number) => void
  color: string
}

function SliderSetting({
  icon, label, value, min, max, step, display, onChange, color,
}: SliderSettingProps) {
  const pct = ((value - min) / (max - min)) * 100

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-400">
          {icon}
          <span className="text-xs font-medium">{label}</span>
        </div>
        <span className="text-xs font-mono text-white">{display}</span>
      </div>
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-1.5 rounded-full appearance-none cursor-pointer
            bg-gray-700 outline-none"
          style={{
            background: `linear-gradient(to right, ${color} ${pct}%, #374151 ${pct}%)`,
          }}
        />
      </div>
    </div>
  )
}