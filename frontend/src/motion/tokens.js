// ============================================================
// CareerLens — Motion System Tokens (Section 7)
// ============================================================

export const DURATION = {
  fast: 0.15,
  base: 0.25,
  slow: 0.45,
  hero: 0.9,
}

export const EASING = {
  standard: [0.2, 0.8, 0.2, 1],
  emphasized: [0.3, 0.0, 0.0, 1],
  smooth: [0.4, 0.0, 0.2, 1],
}

export const SPRINGS = {
  snappy: { type: 'spring', stiffness: 350, damping: 25 },
  gentle: { type: 'spring', stiffness: 120, damping: 16 },
  bouncy: { type: 'spring', stiffness: 260, damping: 18 },
  floating: { type: 'spring', stiffness: 80, damping: 12 },
}

export const FADE_UP = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: DURATION.base, ease: EASING.standard } },
  exit: { opacity: 0, y: -8, transition: { duration: DURATION.fast, ease: EASING.standard } },
}

export const SCALE_IN = {
  initial: { opacity: 0, scale: 0.94 },
  animate: { opacity: 1, scale: 1, transition: SPRINGS.snappy },
  exit: { opacity: 0, scale: 0.94, transition: { duration: DURATION.fast } },
}
