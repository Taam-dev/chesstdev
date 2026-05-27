import React, { useRef, useEffect, useState } from 'react'
import { useBoardRecognition } from '@/hooks/useBoardRecognition'
import { Camera, CameraOff, CheckCircle, AlertCircle } from 'lucide-react'

export function WebcamCapture() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([])
  const [selectedDevice, setSelectedDevice] = useState(0)

  const {
    isWebcamActive,
    lastResult,
    confidence,
    error,
    startWebcam,
    stopWebcam,
  } = useBoardRecognition()

  // Load webcam devices
  useEffect(() => {
    navigator.mediaDevices
      .enumerateDevices()
      .then((devs) => setDevices(devs.filter((d) => d.kind === 'videoinput')))
      .catch(() => {})
  }, [])

  // Show local webcam preview
  useEffect(() => {
    let stream: MediaStream | null = null

    if (isWebcamActive && videoRef.current) {
      navigator.mediaDevices
        .getUserMedia({ video: { deviceId: devices[selectedDevice]?.deviceId } })
        .then((s) => {
          stream = s
          if (videoRef.current) videoRef.current.srcObject = s
        })
        .catch(console.error)
    }

    return () => {
      stream?.getTracks().forEach((t) => t.stop())
      if (videoRef.current) videoRef.current.srcObject = null
    }
  }, [isWebcamActive, selectedDevice, devices])

  const handleToggle = async () => {
    if (isWebcamActive) {
      await stopWebcam()
    } else {
      await startWebcam(selectedDevice)
    }
  }

  const confidencePct = Math.round(confidence * 100)

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Camera size={16} className="text-chess-accent" />
        <h3 className="text-sm font-semibold text-white">Webcam Detection</h3>
      </div>

      {/* Device selector */}
      {devices.length > 1 && (
        <select
          value={selectedDevice}
          onChange={(e) => setSelectedDevice(Number(e.target.value))}
          disabled={isWebcamActive}
          className="w-full bg-white/5 border border-gray-700 rounded px-2 py-1.5
            text-sm text-gray-300 outline-none focus:border-chess-accent
            disabled:opacity-50"
        >
          {devices.map((dev, idx) => (
            <option key={dev.deviceId} value={idx}>
              {dev.label || `Camera ${idx + 1}`}
            </option>
          ))}
        </select>
      )}

      {/* Video preview */}
      <div className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden
        border border-gray-700">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover ${isWebcamActive ? '' : 'hidden'}`}
        />
        {!isWebcamActive && (
          <div className="absolute inset-0 flex flex-col items-center justify-center
            text-gray-600">
            <CameraOff size={32} />
            <p className="text-xs mt-2">Camera off</p>
          </div>
        )}

        {/* Confidence overlay */}
        {isWebcamActive && confidence > 0 && (
          <div className="absolute top-2 right-2 bg-black/60 rounded px-2 py-1
            text-xs font-mono text-white">
            {confidencePct}%
          </div>
        )}
      </div>

      {/* Toggle button */}
      <button
        onClick={handleToggle}
        className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-lg
          font-medium text-sm transition-colors ${
          isWebcamActive
            ? 'bg-red-500/20 border border-red-500/50 text-red-400 hover:bg-red-500/30'
            : 'bg-chess-accent hover:bg-chess-accent/80 text-white'
        }`}
      >
        {isWebcamActive ? (
          <><CameraOff size={16} /> Stop Webcam</>
        ) : (
          <><Camera size={16} /> Start Webcam</>
        )}
      </button>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10
          border border-red-500/30 text-red-400 text-xs">
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Last result */}
      {lastResult && (
        <div className={`p-3 rounded-lg border text-xs ${
          confidence > 0.85
            ? 'bg-green-500/10 border-green-500/30'
            : 'bg-yellow-500/10 border-yellow-500/30'
        }`}>
          <div className="flex items-center gap-1.5 mb-1">
            {confidence > 0.85
              ? <CheckCircle size={12} className="text-green-400" />
              : <AlertCircle size={12} className="text-yellow-400" />
            }
            <span className={confidence > 0.85 ? 'text-green-400' : 'text-yellow-400'}>
              {confidence > 0.85 ? 'Board detected & applied' : 'Detecting...'}
            </span>
          </div>
          <div className="font-mono text-gray-500 truncate">{lastResult.fen}</div>
        </div>
      )}
    </div>
  )
}