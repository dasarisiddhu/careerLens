import React from 'react'

export function NovaStaticFallback({ size = 'hero', expression = 'idle', className = '' }) {
  const isHero = size === 'hero'
  const width = isHero ? 340 : 80
  const height = isHero ? 380 : 90

  return (
    <div
      className={`relative flex items-center justify-center select-none ${className}`}
      style={{ width, height }}
      aria-label="Nova Assistant"
    >
      <svg
        viewBox="0 0 200 220"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full drop-shadow-[0_10px_30px_rgba(255,107,0,0.35)]"
      >
        <defs>
          <radialGradient id="novaEmberFloor" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#FF6B00" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#FF6B00" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="novaHead" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#EDE5D8" />
          </linearGradient>
          <filter id="novaGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Floor Glow */}
        <ellipse cx="100" cy="195" rx="75" ry="12" fill="url(#novaEmberFloor)" />
        <ellipse cx="100" cy="195" rx="65" ry="8" stroke="#FF6B00" strokeWidth="3" opacity="0.85" />

        {/* Torso */}
        <rect x="70" y="125" width="60" height="52" rx="20" fill="url(#novaHead)" stroke="#E0D6C5" strokeWidth="1.5" />
        {/* Chest Reactor Core */}
        <circle cx="100" cy="148" r="9" fill="#FFA726" filter="url(#novaGlow)" />
        <circle cx="100" cy="148" r="12" stroke="#FF6B00" strokeWidth="1.5" fill="none" opacity="0.8" />

        {/* Arms */}
        <rect x="52" y="132" width="14" height="38" rx="7" fill="url(#novaHead)" stroke="#E0D6C5" strokeWidth="1" />
        <rect x="134" y="132" width="14" height="38" rx="7" fill="url(#novaHead)" stroke="#E0D6C5" strokeWidth="1" />

        {/* Neck */}
        <rect x="85" y="116" width="30" height="12" rx="4" fill="#1A1824" />

        {/* Head Shell */}
        <rect x="42" y="32" width="116" height="90" rx="42" fill="url(#novaHead)" stroke="#E0D6C5" strokeWidth="2" />

        {/* Side Ear Cuffs */}
        <rect x="34" y="60" width="10" height="34" rx="5" fill="#FAF4EB" stroke="#FFA726" strokeWidth="1.5" />
        <rect x="156" y="60" width="10" height="34" rx="5" fill="#FAF4EB" stroke="#FFA726" strokeWidth="1.5" />

        {/* Visor */}
        <rect x="55" y="44" width="90" height="66" rx="28" fill="#0D0C14" />

        {/* Glowing Orange Eyes */}
        <ellipse cx="80" cy="74" rx="10" ry={expression === 'happy' ? 4 : 12} fill="#FFA726" filter="url(#novaGlow)" />
        <ellipse cx="120" cy="74" rx="10" ry={expression === 'happy' ? 4 : 12} fill="#FFA726" filter="url(#novaGlow)" />
      </svg>
    </div>
  )
}

export class NovaErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.warn('Nova 3D canvas failed, falling back to static visual:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <NovaStaticFallback
          size={this.props.size}
          expression={this.props.expression}
          className={this.props.className}
        />
      )
    }
    return this.props.children
  }
}
