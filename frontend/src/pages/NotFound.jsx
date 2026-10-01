import React from 'react'
import { Link } from 'react-router-dom'
import { GlassCard, Button } from '../components/ui'
import { Mascot } from '../mascot/Mascot'
import { ArrowLeft, Home, Compass } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-base overflow-hidden relative">
      {/* Soft Background Sky Bloom */}
      <div
        className="absolute top-1/3 left-1/4 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-60"
        style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.7) 0%, transparent 70%)' }}
      />

      <GlassCard strong className="p-8 sm:p-12 max-w-md w-full text-center space-y-6 border-white/95 shadow-glass-lg relative z-10 rounded-[28px]">
        <div className="flex justify-center">
          <Mascot size={180} showPodium={false} state="error" />
        </div>

        <div className="space-y-2">
          <span className="text-xs font-bold text-[#2563EB] uppercase tracking-wider">
            Error 404
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight">
            Page Not Found
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] leading-relaxed">
            The page you're looking for doesn't exist, has been moved, or is temporarily unavailable.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link to="/dashboard" className="w-full sm:w-auto">
            <Button variant="primary" size="md" trailingIcon={ArrowLeft} className="w-full sm:w-auto">
              Back to Dashboard
            </Button>
          </Link>
          <Link to="/" className="w-full sm:w-auto">
            <Button variant="secondary" size="md" icon={Home} className="w-full sm:w-auto">
              Home
            </Button>
          </Link>
        </div>
      </GlassCard>
    </div>
  )
}
