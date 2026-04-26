import { useEffect, useState } from 'react'
import { Star, LogOut, Menu, ChevronRight, Zap, X } from 'lucide-react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', emoji: '🏠', end: true },
  { to: '/dashboard/resume', label: 'Resume Analysis', emoji: '📄' },
  { to: '/dashboard/chatbot', label: 'Honest Career Coach', emoji: '🤖' },
  { to: '/dashboard/interview', label: 'Mock Interview', emoji: '🎤' },
  { to: '/dashboard/news/tech', label: 'Tech News', emoji: '🧠' },
  { to: '/dashboard/news/hiring', label: 'Hiring News', emoji: '💼' },
  { to: '/dashboard/career-switch', label: 'Career Switch', emoji: '🚀' },
  { to: '/dashboard/portfolio', label: 'Portfolio', emoji: '🌐' },
  { to: '/dashboard/job-match', label: 'Job Match', emoji: '🎯' },
  { to: '/dashboard/ats-checker', label: 'ATS Checker', emoji: '🎯' },
  { to: '/dashboard/optimizer', label: 'Resume Optimizer', emoji: '🔥' },
  { to: '/dashboard/progress', label: 'Progress Tracker', emoji: '📈' },
  { to: '/dashboard/recommendations', label: 'AI Recommendations', emoji: '✨' },
  { to: '/dashboard/community', label: 'Community', emoji: '👥' },
  { to: '/dashboard/interview-predictor', label: 'Interview Predictor', emoji: '🧠' },
]

function useMouseSpotlight() {
  useEffect(() => {
    const handler = (event) => {
      document.documentElement.style.setProperty('--mouse-x', `${event.clientX}px`)
      document.documentElement.style.setProperty('--mouse-y', `${event.clientY}px`)
    }

    window.addEventListener('mousemove', handler, { passive: true })
    return () => window.removeEventListener('mousemove', handler)
  }, [])
}

function MouseSpotlight() {
  return (
    <div
      aria-hidden
      style={{
        position: 'fixed',
        pointerEvents: 'none',
        zIndex: 1,
        width: '700px',
        height: '700px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(255,59,59,0.03) 0%, transparent 68%)',
        transform: 'translate(-50%, -50%)',
        left: 'var(--mouse-x, 50vw)',
        top: 'var(--mouse-y, 50vh)',
        transition: 'left 0.12s ease, top 0.12s ease',
      }}
    />
  )
}

function scrollDashboardToTop() {
  const lenis = window.__careerLensLenis
  if (lenis?.scrollTo) {
    lenis.scrollTo(0, { immediate: true, force: true })
    return
  }
  window.scrollTo(0, 0)
}

function Sidebar({ mobile = false, onClose }) {
  return (
    <aside
      style={{
        background: 'rgba(14, 16, 22, 0.96)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        borderRight: '1px solid rgba(255, 59, 59, 0.08)',
      }}
      className="relative flex h-screen flex-col overflow-hidden"
    >
      <div
        aria-hidden
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '180px',
          background: 'linear-gradient(180deg, rgba(255,59,59,0.08) 0%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      <div className="relative flex h-full min-h-0 flex-col p-5">
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div
              whileHover={{ scale: 1.08, rotate: 5 }}
              transition={{ type: 'spring', stiffness: 400, damping: 18 }}
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #FF3B3B, #CC1A1A)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(255,59,59,0.45)',
              }}
            >
              <Zap size={18} className="text-white" />
            </motion.div>
            <div className="flex items-center gap-2">
              <span
                className="gradient-text text-lg font-bold"
                style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 700, letterSpacing: '-0.03em' }}
              >
                CareerLens
              </span>
              <span
                className="animate-pulse"
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: '#10b981',
                  boxShadow: '0 0 8px rgba(16,185,129,0.8)',
                  display: 'inline-block',
                }}
              />
            </div>
          </div>

          {mobile && (
            <button onClick={onClose} className="rounded-xl p-2 text-[#8A8FA8] transition hover:bg-white/5 hover:text-white">
              <X size={18} />
            </button>
          )}
        </div>

        <p
          className="mb-2 pl-3 text-[10px] font-bold uppercase tracking-[0.18em] text-[#8A8FA8]/45"
          style={{ fontFamily: 'Clash Display, sans-serif', letterSpacing: '0.12em' }}
        >
          Navigation
        </p>

        <nav
          data-lenis-prevent
          className="sidebar-nav min-h-0 flex-1 space-y-[2px] overflow-y-auto pr-1"
          style={{
            overflowY: 'auto',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            overscrollBehavior: 'contain',
          }}
          onWheelCapture={(event) => event.stopPropagation()}
        >
          {NAV.map(({ to, label, emoji, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onClose}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 overflow-hidden rounded-xl px-3 py-2 text-sm font-medium transition ${
                  isActive ? 'text-white' : 'text-[rgba(138,143,168,0.7)] hover:text-[#F5F5F7]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="activeNav"
                      style={{
                        position: 'absolute',
                        inset: 0,
                        background: 'rgba(255,59,59,0.1)',
                        borderRadius: 12,
                        border: '1px solid rgba(255,59,59,0.22)',
                        borderLeft: '2px solid #FF3B3B',
                        boxShadow: 'inset 3px 0 12px rgba(255,59,59,0.12)',
                      }}
                      transition={{ type: 'spring', bounce: 0.18, duration: 0.38 }}
                    />
                  )}

                  <div className="absolute inset-0 rounded-xl bg-transparent transition group-hover:bg-white/[0.03]" />
                  <span className="relative text-base leading-none">{emoji}</span>
                  <span
                    className="relative flex-1 truncate"
                    style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 500 }}
                  >
                    {label}
                  </span>
                  {isActive && (
                    <motion.div initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} className="relative">
                      <ChevronRight size={13} style={{ color: '#FF3B3B' }} />
                    </motion.div>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="divider my-4" />

        <NavLink to="/dashboard/upgrade" onClick={onClose}>
          <motion.div
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98 }}
            className="glass-glow rounded-2xl p-4"
            style={{
              background: 'linear-gradient(135deg, rgba(255,59,59,0.12) 0%, rgba(180,20,20,0.12) 100%)',
              border: '1px solid rgba(255,59,59,0.22)',
            }}
          >
            <div className="flex items-center gap-3">
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 12,
                  background: 'rgba(255,59,59,0.12)',
                  border: '1px solid rgba(255,59,59,0.24)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Star size={16} style={{ color: '#FF3B3B' }} />
              </div>
              <div>
                <p
                  className="text-sm font-semibold text-white"
                  style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 700 }}
                >
                  Upgrade to Pro
                </p>
                <p
                  className="text-[11px] text-[#8A8FA8]"
                  style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 400 }}
                >
                  Unlimited everything
                </p>
              </div>
            </div>
          </motion.div>
        </NavLink>
      </div>
    </aside>
  )
}

export default function DashboardLayout() {
  const [open, setOpen] = useState(false)
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  useMouseSpotlight()

  useEffect(() => {
    scrollDashboardToTop()
  }, [location.pathname])

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  const handleOpenProfile = () => {
    setOpen(false)
    navigate('/dashboard/profile')
  }

  const currentPage = NAV.find((item) => {
    if (item.end) return location.pathname === item.to
    return location.pathname.startsWith(item.to)
  })

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#11131A' }}>
      <MouseSpotlight />

      <div className="hidden lg:block" style={{ width: 240, flexShrink: 0, zIndex: 2, position: 'sticky', top: 0, height: '100vh', alignSelf: 'flex-start', overflow: 'hidden' }}>
        <Sidebar />
      </div>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/70 backdrop-blur-[4px] lg:hidden"
              onClick={() => setOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed inset-y-0 left-0 z-50 w-[260px] lg:hidden"
            >
              <Sidebar mobile onClose={() => setOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, position: 'relative', zIndex: 2 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            height: 64,
            background: 'rgba(14,16,22,0.85)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            position: 'sticky',
            top: 0,
            zIndex: 10,
            flexShrink: 0,
          }}
        >
          <div className="flex items-center gap-4">
            <button onClick={() => setOpen(true)} className="rounded-xl p-2 text-[#8A8FA8] transition hover:bg-white/5 hover:text-white lg:hidden">
              <Menu size={20} />
            </button>

            <div className="hidden items-center gap-2 lg:flex">
              <span className="text-xs text-[#8A8FA8]/50">CareerLens</span>
              <ChevronRight size={12} className="text-[#8A8FA8]/30" />
              <span
                className="text-sm font-semibold text-[#F5F5F7]"
                style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 600 }}
              >
                {currentPage?.label || 'Dashboard'}
              </span>
            </div>

            <span
              className="gradient-text text-lg font-bold lg:hidden"
              style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 700, letterSpacing: '-0.03em' }}
            >
              CareerLens
            </span>
          </div>

          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleOpenProfile}
              className="glass flex items-center gap-3 rounded-xl px-3 py-2"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
            >
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg,#FF3B3B,#8B0000)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 11,
                  fontWeight: 800,
                  color: 'white',
                  boxShadow: '0 0 12px rgba(255,59,59,0.4)',
                  flexShrink: 0,
                }}
              >
                {user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <span
                className="hidden max-w-[170px] truncate text-xs text-[#8A8FA8] sm:block"
                style={{ fontFamily: 'Cabinet Grotesk, sans-serif' }}
              >
                {user?.email}
              </span>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSignOut}
              className="btn-ghost"
            >
              <LogOut size={14} />
              <span
                className="hidden sm:inline"
                style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 500 }}
              >
                Sign out
              </span>
            </motion.button>
          </div>
        </div>

        <main style={{ flex: 1, padding: '32px' }}>
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  )
}
