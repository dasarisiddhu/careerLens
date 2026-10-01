import React, { useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Sparkles } from 'lucide-react'
import { MASCOT_CONFIG } from './mascot.config'
import { SPRINGS } from '../motion/tokens'

export function Mascot({
  state = 'idle', // 'idle' | 'greeting' | 'thinking' | 'success' | 'error' | 'pointing' | 'wave'
  bubbleText,
  bubbleOpen = false,
  onBubbleClose,
  onMascotClick,
  mouseOffset = { x: 0, y: 0 },
  prefersReducedMotion = false,
  size = 460, // default hero size in px
  showPodium = true,
  className = '',
}) {
  const containerRef = useRef(null)

  const activeBubbleText =
    bubbleText ||
    (state === 'thinking'
      ? MASCOT_CONFIG.speechBubble.thinkingText
      : state === 'success'
      ? MASCOT_CONFIG.speechBubble.successText
      : state === 'error'
      ? MASCOT_CONFIG.speechBubble.errorText
      : MASCOT_CONFIG.speechBubble.defaultText)

  // Motion variants based on state
  const getBodyMotion = () => {
    if (prefersReducedMotion) return {}
    switch (state) {
      case 'thinking':
        return {
          y: [0, -6, 0],
          rotate: [-1, 1, -1],
          transition: { duration: 1.6, repeat: Infinity, ease: 'easeInOut' },
        }
      case 'success':
        return {
          y: [0, -22, 0],
          scale: [1, 1.05, 1],
          transition: { duration: 0.8, times: [0, 0.4, 1], ease: 'easeOut' },
        }
      case 'error':
        return {
          x: [0, -8, 8, -6, 6, 0],
          transition: { duration: 0.5 },
        }
      case 'wave':
        return {
          rotate: [0, -3, 3, -3, 0],
          y: [0, -8, 0],
          transition: { duration: 0.8 },
        }
      case 'idle':
      default:
        return {
          y: [0, -12, 0],
          rotate: [0, 1.2, 0],
          transition: { duration: 4.2, repeat: Infinity, ease: 'easeInOut' },
        }
    }
  }

  return (
    <div
      ref={containerRef}
      className={`relative inline-flex flex-col items-center justify-center select-none ${className}`}
      style={{ width: size, height: size }}
    >
      {/* Speech Bubble (REF-1 / REF-2 Style) */}
      <AnimatePresence>
        {bubbleOpen && (
          <motion.div
            role="status"
            aria-live="polite"
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            transition={SPRINGS.snappy}
            className="absolute top-2 -right-4 sm:-right-8 z-30 max-w-[240px] sm:max-w-[270px] p-3.5 sm:p-4 rounded-[20px] bg-white/95 border border-slate-200/90 shadow-[0_16px_36px_rgba(37,99,235,0.12),0_2px_8px_rgba(0,0,0,0.04)] backdrop-blur-md"
          >
            {/* Pointer Caret anchored to robot */}
            <div
              className="absolute -bottom-2 left-6 w-3.5 h-3.5 bg-white border-b border-r border-slate-200/90 rotate-45"
              aria-hidden="true"
            />

            <div className="flex items-start justify-between gap-2">
              <p className="text-xs font-semibold text-[#0B0F19] leading-relaxed">
                {activeBubbleText}
              </p>
              {onBubbleClose && (
                <button
                  type="button"
                  onClick={onBubbleClose}
                  aria-label="Dismiss speech bubble"
                  className="text-slate-400 hover:text-slate-700 p-0.5 rounded-full transition-colors shrink-0"
                >
                  <X size={13} />
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Robot Body with Parallax */}
      <motion.div
        animate={getBodyMotion()}
        onClick={onMascotClick}
        style={{
          transform: `translate3d(${mouseOffset.x}px, ${mouseOffset.y}px, 0)`,
          cursor: onMascotClick ? 'pointer' : 'default',
        }}
        className="relative z-10 w-full h-full flex items-center justify-center"
      >
        <img
          src={MASCOT_CONFIG.assets.hero}
          alt=""
          aria-hidden="true"
          fetchPriority="high"
          width={size}
          height={size}
          className="w-full h-full object-contain pointer-events-none drop-shadow-[0_20px_40px_rgba(37,99,235,0.15)]"
        />

        {/* Orbiting Thinking Indicator when state === 'thinking' */}
        {state === 'thinking' && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2.4, repeat: Infinity, ease: 'linear' }}
            className="absolute top-1/4 w-32 h-32 rounded-full border border-dashed border-[#2563EB]/40 pointer-events-none"
          >
            <div className="w-2.5 h-2.5 rounded-full bg-[#2563EB] shadow-[0_0_8px_#2563EB]" />
          </motion.div>
        )}

        {/* Confetti sparkle burst on success */}
        {state === 'success' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1.2 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6 }}
            className="absolute -top-4 text-emerald-500 pointer-events-none"
          >
            <Sparkles size={28} />
          </motion.div>
        )}
      </motion.div>

      {/* Podium & Glow Base */}
      {showPodium && (
        <div
          className="absolute bottom-2 w-4/5 h-16 rounded-[50%] pointer-events-none z-0 flex items-center justify-center"
          aria-hidden="true"
        >
          {/* Outer glow ring */}
          <motion.div
            animate={
              prefersReducedMotion
                ? {}
                : {
                    scale: [1, 1.06, 1],
                    opacity: [0.6, 0.9, 0.6],
                  }
            }
            transition={{ duration: 3.2, repeat: Infinity, ease: 'easeInOut' }}
            className="absolute w-full h-full rounded-[50%] border-2 border-blue-400/40 shadow-[0_0_35px_rgba(37,99,235,0.25)]"
          />

          {/* Inner ring */}
          <div className="absolute w-3/4 h-3/4 rounded-[50%] border border-blue-300/50 shadow-[inset_0_0_15px_rgba(37,99,235,0.15)]" />

          {/* Soft shadow below robot */}
          <motion.div
            animate={
              prefersReducedMotion
                ? {}
                : {
                    scale: [1, 0.85, 1],
                    opacity: [0.35, 0.2, 0.35],
                  }
            }
            transition={{ duration: 4.2, repeat: Infinity, ease: 'easeInOut' }}
            className="w-1/2 h-4 rounded-[50%] bg-blue-950/20 blur-md"
          />
        </div>
      )}
    </div>
  )
}

export default Mascot
