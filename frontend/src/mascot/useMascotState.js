import { useState, useEffect, useCallback, useRef } from 'react'

export function useMascotState({ initial = 'idle', autoNudge = false, nudgeDelayMs = 8000 } = {}) {
  const [state, setState] = useState(initial)
  const [bubbleOpen, setBubbleOpen] = useState(initial === 'greeting')
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 })
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)
  const idleTimerRef = useRef(null)

  // Media query for reduced motion
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mq.matches)
    const handler = (e) => setPrefersReducedMotion(e.matches)
    mq.addEventListener?.('change', handler)
    return () => mq.removeEventListener?.('change', handler)
  }, [])

  // Visibility change listener
  useEffect(() => {
    const handleVisibility = () => {
      setIsTabVisible(!document.hidden)
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [])

  // Parallax pointer tracking (desktop only, throttled via rAF)
  useEffect(() => {
    if (prefersReducedMotion) return

    let rAFId = null
    const handleMouseMove = (e) => {
      if (rAFId) return
      rAFId = requestAnimationFrame(() => {
        const { innerWidth, innerHeight } = window
        const normX = (e.clientX / innerWidth - 0.5) * 2 // -1 to 1
        const normY = (e.clientY / innerHeight - 0.5) * 2 // -1 to 1
        setMouseOffset({
          x: Math.max(-6, Math.min(6, normX * 6)),
          y: Math.max(-4, Math.min(4, normY * 4)),
        })
        rAFId = null
      })
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      if (rAFId) cancelAnimationFrame(rAFId)
    }
  }, [prefersReducedMotion])

  // Idle nudge trigger
  useEffect(() => {
    if (!autoNudge) return

    const resetIdleTimer = () => {
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current)
      idleTimerRef.current = setTimeout(() => {
        setBubbleOpen(true)
      }, nudgeDelayMs)
    }

    resetIdleTimer()
    window.addEventListener('pointerdown', resetIdleTimer, { passive: true })
    window.addEventListener('keydown', resetIdleTimer, { passive: true })

    return () => {
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current)
      window.removeEventListener('pointerdown', resetIdleTimer)
      window.removeEventListener('keydown', resetIdleTimer)
    }
  }, [autoNudge, nudgeDelayMs])

  const triggerState = useCallback((nextState, autoRevertMs = null) => {
    setState(nextState)
    if (nextState === 'greeting' || nextState === 'success') {
      setBubbleOpen(true)
    }
    if (autoRevertMs) {
      setTimeout(() => setState('idle'), autoRevertMs)
    }
  }, [])

  return {
    state,
    setState: triggerState,
    bubbleOpen,
    setBubbleOpen,
    mouseOffset,
    isTabVisible,
    prefersReducedMotion,
  }
}

export default useMascotState
