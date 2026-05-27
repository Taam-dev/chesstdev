import { useState, useCallback, useRef } from 'react'
import { useAppDispatch } from '@/store'
import { setFen } from '@/store/gameSlice'
import { apiService } from '@/services/apiService'
import { RecognitionResult, CalibrationData } from '@/types'

interface UseBoardRecognitionReturn {
  isCapturing: boolean
  isWebcamActive: boolean
  lastResult: RecognitionResult | null
  confidence: number
  error: string | null
  captureScreen: (region?: CalibrationData) => Promise<void>
  startWebcam: (deviceIndex?: number) => Promise<void>
  stopWebcam: () => Promise<void>
  calibrate: (imageData: string) => Promise<{ corners: number[][] } | null>
  applyPosition: (result: RecognitionResult) => void
}

export function useBoardRecognition(): UseBoardRecognitionReturn {
  const dispatch = useAppDispatch()
  const [isCapturing, setIsCapturing] = useState(false)
  const [isWebcamActive, setIsWebcamActive] = useState(false)
  const [lastResult, setLastResult] = useState<RecognitionResult | null>(null)
  const [confidence, setConfidence] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  const applyPosition = useCallback(
    (result: RecognitionResult) => {
      dispatch(setFen(result.fen))
    },
    [dispatch]
  )

  const captureScreen = useCallback(
    async (region?: CalibrationData) => {
      setIsCapturing(true)
      setError(null)
      try {
        const result = await apiService.captureScreen(region)
        setLastResult(result)
        setConfidence(result.confidence)
        if (result.confidence > 0.85) {
          applyPosition(result)
        }
      } catch (err) {
        setError(`Screen capture failed: ${err}`)
      } finally {
        setIsCapturing(false)
      }
    },
    [applyPosition]
  )

  const startWebcam = useCallback(
    async (deviceIndex = 0) => {
      setError(null)
      try {
        // Subscribe to recognition results
        const cleanup = apiService.on('recognition_result', (data) => {
          const result = data as RecognitionResult
          setLastResult(result)
          setConfidence(result.confidence)
          if (result.confidence > 0.85) {
            applyPosition(result)
          }
        })
        cleanupRef.current = cleanup

        await apiService.startWebcam(deviceIndex)
        setIsWebcamActive(true)
      } catch (err) {
        setError(`Failed to start webcam: ${err}`)
      }
    },
    [applyPosition]
  )

  const stopWebcam = useCallback(async () => {
    await apiService.stopWebcam()
    cleanupRef.current?.()
    cleanupRef.current = null
    setIsWebcamActive(false)
  }, [])

  const calibrate = useCallback(async (imageData: string) => {
    setError(null)
    try {
      return await apiService.calibrateBoard(imageData)
    } catch (err) {
      setError(`Calibration failed: ${err}`)
      return null
    }
  }, [])

  return {
    isCapturing,
    isWebcamActive,
    lastResult,
    confidence,
    error,
    captureScreen,
    startWebcam,
    stopWebcam,
    calibrate,
    applyPosition,
  }
}