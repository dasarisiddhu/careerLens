import React, { useEffect, useState } from 'react'

export function ScoreRing({
  score = 98,
  max = 100,
  size = 72,
  strokeWidth = 6,
  showLabel = true,
  label = '',
  color = '#2563EB',
  trackColor = '#E2E8F0',
  className = '',
}) {
  const [animatedScore, setAnimatedScore] = useState(0)

  useEffect(() => {
    let start = 0
    const end = Math.min(Math.max(score, 0), max)
    if (end === 0) {
      setAnimatedScore(0)
      return
    }

    const duration = 800
    const stepTime = 16
    const steps = duration / stepTime
    const increment = end / steps

    const timer = setInterval(() => {
      start += increment
      if (start >= end) {
        setAnimatedScore(end)
        clearInterval(timer)
      } else {
        setAnimatedScore(Math.round(start))
      }
    }, stepTime)

    return () => clearInterval(timer)
  }, [score, max])

  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const normalizedScore = Math.min(Math.max(animatedScore, 0), max)
  const strokeDashoffset = circumference - (normalizedScore / max) * circumference

  return (
    <div
      role="img"
      aria-label={`Score ${score} out of ${max}${label ? ` - ${label}` : ''}`}
      className={`relative inline-flex items-center justify-center shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="rotate-[-90deg]">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={trackColor}
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Animated fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
        />
      </svg>

      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-sm font-extrabold text-[#0B0F19] leading-none tracking-tight">
            {animatedScore}
          </span>
          <span className="text-[9px] font-medium text-[#64748B] leading-none mt-0.5">
            /{max}
          </span>
        </div>
      )}
    </div>
  )
}

export default ScoreRing
