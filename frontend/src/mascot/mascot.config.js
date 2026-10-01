// ============================================================
// CareerLens — Mascot Configuration (Section 6.1)
// Centralized theme, assets, and animation timings
// ============================================================

export const MASCOT_CONFIG = {
  name: 'Lens',
  assets: {
    hero: '/mascot/mascot-hero.webp',
    flat: '/mascot/mascot-flat.webp',
  },
  colors: {
    eyeGlow: '#00F0FF',
    coreGlow: '#2563EB',
    podiumRing: 'rgba(37, 99, 235, 0.45)',
  },
  speechBubble: {
    defaultText: "Hi! I'm your AI career companion. Let's build your future together! 🚀",
    idleNudgeText: "Ready to analyze your resume? Let's go! 📄",
    thinkingText: "Reading your resume & calculating ATS keywords...",
    successText: "Great job! Your resume analysis is ready! 🎉",
    errorText: "Oops, something went wrong. Let's try that again.",
  },
}
