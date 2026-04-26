import { createElement, useEffect, useState } from 'react'

const ease = [0.4, 0, 0.2, 1]

export const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease },
}

export const fadeInLeft = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  transition: { duration: 0.4, ease },
}

export const staggerContainer = {
  initial: {},
  hidden: {},
  animate: { transition: { staggerChildren: 0.08 } },
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
}

export const scaleIn = {
  initial: { opacity: 0, scale: 0.92 },
  animate: { opacity: 1, scale: 1 },
  transition: { duration: 0.35, ease },
}

export const cardHover = {
  whileHover: { y: -4, transition: { duration: 0.2 } },
}

export function useCountUp(target, duration = 1500) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!target) {
      setCount(0)
      return
    }

    let start = 0
    const step = target / (duration / 16)
    const timer = setInterval(() => {
      start += step
      if (start >= target) {
        setCount(target)
        clearInterval(timer)
      } else {
        setCount(Math.floor(start))
      }
    }, 16)

    return () => clearInterval(timer)
  }, [target, duration])

  return count
}

export function Particles({ count = 20 }) {
  return createElement(
    'div',
    {
      style: {
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
      },
    },
    Array.from({ length: count }).map((_, i) =>
      createElement('div', {
        key: i,
        style: {
          position: 'absolute',
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
          width: `${Math.random() * 2.5 + 1}px`,
          height: `${Math.random() * 2.5 + 1}px`,
          borderRadius: '50%',
          background:
            i % 3 === 0
              ? `rgba(255,59,59,${Math.random() * 0.35 + 0.1})`
              : i % 3 === 1
                ? `rgba(255,140,66,${Math.random() * 0.25 + 0.08})`
                : `rgba(255,255,255,${Math.random() * 0.08 + 0.02})`,
          animation: `float ${Math.random() * 5 + 3}s ease-in-out ${Math.random() * 2}s infinite alternate`,
        },
      })
    )
  )
}

export const fadeUp = {
  hidden: fadeInUp.initial,
  visible: {
    ...fadeInUp.animate,
    transition: { duration: 0.45, ease },
  },
  exit: { opacity: 0, y: -12, transition: { duration: 0.25, ease } },
}

export const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.35, ease } },
  exit: { opacity: 0, transition: { duration: 0.2, ease } },
}

export const staggerItem = {
  hidden: fadeInUp.initial,
  visible: {
    ...fadeInUp.animate,
    transition: { duration: 0.4, ease },
  },
}

export const slideInLeft = {
  hidden: fadeInLeft.initial,
  visible: {
    ...fadeInLeft.animate,
    transition: fadeInLeft.transition,
  },
}

export const slideInRight = {
  hidden: { opacity: 0, x: 20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4, ease },
  },
}

export const pageTransition = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.25, ease },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: { duration: 0.2, ease },
  },
}

export function useAnimatedCircle(score, maxScore = 100, size = 120, strokeWidth = 8) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const [offset, setOffset] = useState(circumference)

  useEffect(() => {
    const timer = setTimeout(() => {
      const progress = score / maxScore
      setOffset(circumference - progress * circumference)
    }, 300)

    return () => clearTimeout(timer)
  }, [score, circumference, maxScore])

  return { radius, circumference, offset, size, strokeWidth }
}
