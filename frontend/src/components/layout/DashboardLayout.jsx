import React, { useEffect, useState } from 'react'
import {
  Star,
  LogOut,
  Menu,
  ChevronRight,
  ChevronDown,
  X,
  LayoutDashboard,
  FileText,
  Bot,
  Mic,
  Cpu,
  Briefcase,
  Rocket,
  Globe,
  Target,
  Flame,
  TrendingUp,
  Sparkles,
  Users,
  Brain,
} from 'lucide-react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import CompanionWidget from '../companion/CompanionWidget'

const NAV_PRIMARY = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/dashboard/optimizer', label: 'Resume Optimizer', icon: FileText, hero: true },
  { to: '/dashboard/job-match', label: 'Job Match', icon: Target },
  { to: '/dashboard/resume', label: 'GitHub Project Insights', icon: Flame },
]

const NAV_SECONDARY = [
  { to: '/dashboard/chatbot', label: 'Honest Career Coach', icon: Bot },
  { to: '/dashboard/interview', label: 'Mock Interview', icon: Mic },
  { to: '/dashboard/news/tech', label: 'Tech News', icon: Cpu },
  { to: '/dashboard/news/hiring', label: 'Hiring News', icon: Briefcase },
  { to: '/dashboard/career-switch', label: 'Career Switch', icon: Rocket },
  { to: '/dashboard/portfolio', label: 'Portfolio', icon: Globe },
  { to: '/dashboard/progress', label: 'Progress Tracker', icon: TrendingUp },
  { to: '/dashboard/recommendations', label: 'AI Recommendations', icon: Sparkles },
  { to: '/dashboard/community', label: 'Community', icon: Users },
  { to: '/dashboard/interview-predictor', label: 'Interview Predictor', icon: Brain },
]

const NAV = [...NAV_PRIMARY, ...NAV_SECONDARY]

function scrollDashboardToTop() {
  const lenis = window.__careerLensLenis
  if (lenis?.scrollTo) {
    lenis.scrollTo(0, { immediate: true, force: true })
    return
  }
  window.scrollTo(0, 0)
}

function Sidebar({ mobile = false, onClose }) {
  const [moreToolsOpen, setMoreToolsOpen] = useState(true)

  const renderNavItem = ({ to, label, icon: Icon, end, hero }) => (
    <NavLink
      key={to}
      to={to}
      end={end}
      onClick={onClose}
      className={({ isActive }) =>
        `group relative flex items-center gap-3 overflow-hidden rounded-xl px-3 py-2.5 text-xs font-semibold transition-all duration-200 ${
          isActive
            ? 'text-[#0B0F19] font-bold'
            : hero
            ? 'text-[#2563EB] hover:text-[#1D4ED8] hover:bg-blue-50/50'
            : 'text-[#64748B] hover:text-[#0B0F19] hover:bg-slate-100/70'
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
                background: 'rgba(37, 99, 235, 0.08)',
                borderRadius: 12,
                border: '1px solid rgba(37, 99, 235, 0.2)',
                borderLeft: '3px solid #2563EB',
                boxShadow: 'inset 3px 0 10px rgba(37, 99, 235, 0.06)',
              }}
              transition={{ type: 'spring', bounce: 0.18, duration: 0.38 }}
            />
          )}

          <div className="absolute inset-0 rounded-xl bg-transparent transition group-hover:bg-slate-100/50" />
          <Icon
            size={17}
            className={`relative shrink-0 transition-colors ${
              isActive
                ? 'text-[#2563EB]'
                : hero
                ? 'text-[#2563EB]'
                : 'text-[#94A3B8] group-hover:text-[#475569]'
            }`}
          />
          <span className="relative flex-1 truncate">
            {label}
          </span>
          {isActive && (
            <motion.div initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} className="relative">
              <ChevronRight size={13} className="text-[#2563EB]" />
            </motion.div>
          )}
        </>
      )}
    </NavLink>
  )

  return (
    <aside
      style={{
        background: 'rgba(255, 255, 255, 0.88)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(226, 232, 240, 0.85)',
      }}
      className="relative flex h-screen flex-col overflow-hidden shadow-[2px_0_16px_rgba(0,0,0,0.02)]"
    >
      <div className="relative flex h-full min-h-0 flex-col p-4 sm:p-5">
        {/* Brand Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#0B0F19] text-white flex items-center justify-center shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M3 9a2 2 0 0 1 2-2h1.5a2 2 0 0 0 1.6-.8L9.3 4.8A2 2 0 0 1 10.9 4h2.2a2 2 0 0 1 1.6.8l1.2 1.4a2 2 0 0 0 1.6.8H19a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" />
              </svg>
            </div>
            <span className="text-base font-bold text-[#0B0F19] tracking-tight">
              CareerLens
            </span>
          </div>

          {mobile && (
            <button
              onClick={onClose}
              className="rounded-xl p-1.5 text-[#64748B] transition hover:bg-slate-100 hover:text-[#0B0F19]"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Navigation list */}
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
          <p className="mb-2 pl-3 text-[10px] font-bold uppercase tracking-[0.14em] text-[#94A3B8]">
            Resume Intelligence
          </p>

          <div className="space-y-[2px]">
            {NAV_PRIMARY.map(renderNavItem)}
          </div>

          <div className="my-3 mx-2 border-t border-slate-200/80" />

          <button
            type="button"
            onClick={() => setMoreToolsOpen((prev) => !prev)}
            className="mb-2 flex w-full items-center justify-between pl-3 pr-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#94A3B8] transition hover:text-[#475569]"
          >
            <span>More Tools</span>
            <ChevronDown
              size={12}
              className={`transition-transform duration-200 ${moreToolsOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {moreToolsOpen && (
            <div className="space-y-[2px]">
              {NAV_SECONDARY.map(renderNavItem)}
            </div>
          )}
        </nav>

        <div className="my-3 border-t border-slate-200/80" />

        {/* Upgrade Card */}
        <NavLink to="/dashboard/upgrade" onClick={onClose}>
          <motion.div
            whileHover={{ scale: 1.01, y: -1 }}
            whileTap={{ scale: 0.98 }}
            className="rounded-2xl p-3.5 bg-gradient-to-br from-blue-50/80 to-sky-50/60 border border-blue-200/70 shadow-sm transition-all"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-blue-100 text-[#2563EB] flex items-center justify-center shrink-0 shadow-sm">
                <Star size={16} />
              </div>
              <div>
                <p className="text-xs font-bold text-[#0B0F19]">Upgrade to Pro</p>
                <p className="text-[11px] text-[#64748B]">Unlimited AI analyses</p>
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
    <div style={{ display: 'flex', minHeight: '100vh', background: '#F4F7FC' }}>
      {/* Desktop Sticky Sidebar */}
      <div
        className="hidden lg:block"
        style={{
          width: 240,
          flexShrink: 0,
          zIndex: 2,
          position: 'sticky',
          top: 0,
          height: '100vh',
          alignSelf: 'flex-start',
          overflow: 'hidden',
        }}
      >
        <Sidebar />
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
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

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, position: 'relative', zIndex: 2 }}>
        {/* Sticky Glass Topbar */}
        <header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            height: 64,
            background: 'rgba(255, 255, 255, 0.85)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(226, 232, 240, 0.8)',
            position: 'sticky',
            top: 0,
            zIndex: 10,
            flexShrink: 0,
          }}
        >
          <div className="flex items-center gap-4">
            <button
              onClick={() => setOpen(true)}
              className="rounded-xl p-2 text-[#64748B] transition hover:bg-slate-100 hover:text-[#0B0F19] lg:hidden"
            >
              <Menu size={20} />
            </button>

            <div className="hidden items-center gap-2 lg:flex">
              <span className="text-xs font-medium text-[#94A3B8]">CareerLens</span>
              <ChevronRight size={12} className="text-[#CBD5E1]" />
              <span className="text-xs font-bold text-[#0B0F19]">
                {currentPage?.label || 'Dashboard'}
              </span>
            </div>

            <span className="text-base font-bold text-[#0B0F19] lg:hidden">
              CareerLens
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleOpenProfile}
              className="flex items-center gap-2.5 rounded-pill bg-white px-3 py-1.5 border border-slate-200/80 shadow-sm hover:bg-slate-50 transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-[#0B0F19] text-white flex items-center justify-center text-[10px] font-bold">
                {user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <span className="hidden sm:inline text-xs font-semibold text-[#0B0F19] max-w-[140px] truncate">
                {user?.email}
              </span>
            </button>

            <button
              onClick={handleSignOut}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[#64748B] hover:text-[#0B0F19] hover:bg-slate-100 rounded-pill transition-colors"
            >
              <LogOut size={14} />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </header>

        {/* Page Outlet */}
        <main style={{ flex: 1, padding: '24px sm:32px' }}>
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
          >
            <Outlet />
          </motion.div>
        </main>

        {/* Persistent Mascot Companion Widget */}
        <CompanionWidget />
      </div>
    </div>
  )
}
