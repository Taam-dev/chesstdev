import { useCallback, useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/store'
import { loadGame, resetGame, addMove } from '@/store/gameSlice'
import { apiService } from '@/services/apiService'
import { Chess } from 'chess.js'
import { SavedGame } from '@/types'

export function useGameStorage() {
  const dispatch = useAppDispatch()
  const { pgn, fen, moves, players } = useAppSelector((state) => state.game)
  const [savedGames, setSavedGames] = useState<SavedGame[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const saveGame = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const metadata: Record<string, string> = {
        white: players.white.name,
        black: players.black.name,
        date: new Date().toISOString().split('T')[0],
        fen,
      }
      const result = await apiService.saveGame(pgn, metadata)
      return result.id
    } catch (err) {
      setError(`Failed to save game: ${err}`)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [pgn, fen, players])

  const loadGames = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const games = (await apiService.loadGames()) as SavedGame[]
      setSavedGames(games)
      return games
    } catch (err) {
      setError(`Failed to load games: ${err}`)
      return []
    } finally {
      setIsLoading(false)
    }
  }, [])

  const deleteGame = useCallback(async (id: string) => {
    try {
      await apiService.deleteGame(id)
      setSavedGames((prev) => prev.filter((g) => g.id !== id))
    } catch (err) {
      setError(`Failed to delete game: ${err}`)
    }
  }, [])

  const loadPgnString = useCallback(
    (content: string) => {
      const chess = new Chess()
      try {
        chess.loadPgn(content)
        const history = chess.history({ verbose: true })
        dispatch(resetGame())

        const replay = new Chess()
        history.forEach((move, index) => {
          const fenBefore = replay.fen()
          replay.move(move)
          dispatch(
            addMove({
              index,
              move: { from: move.from, to: move.to },
              san: move.san,
              fen: replay.fen(),
              fenBefore,
              timestamp: Date.now(),
            })
          )
        })
        return true
      } catch (err) {
        setError(`Failed to load PGN: ${err}`)
        return false
      }
    },
    [dispatch]
  )

  const exportPgn = useCallback(async () => {
    if (window.electronAPI) {
      await window.electronAPI.savePgnFile(pgn)
    } else {
      const blob = new Blob([pgn], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `game_${Date.now()}.pgn`
      a.click()
      URL.revokeObjectURL(url)
    }
  }, [pgn])

  const importPgn = useCallback(async () => {
    if (window.electronAPI) {
      const content = await window.electronAPI.openPgnFile()
      if (content) return loadPgnString(content)
      return false
    } else {
      return new Promise<boolean>((resolve) => {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = '.pgn'
        input.onchange = (e) => {
          const file = (e.target as HTMLInputElement).files?.[0]
          if (!file) { resolve(false); return }
          const reader = new FileReader()
          reader.onload = (ev) => {
            resolve(loadPgnString(ev.target?.result as string))
          }
          reader.readAsText(file)
        }
        input.click()
      })
    }
  }, [loadPgnString])

  return {
    savedGames,
    isLoading,
    error,
    saveGame,
    loadGames,
    deleteGame,
    loadPgnString,
    exportPgn,
    importPgn,
  }
}