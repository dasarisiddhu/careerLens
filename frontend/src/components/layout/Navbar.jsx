import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ArrowRight, LayoutDashboard, LogOut } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Button from '../ui/Button'

const NAV_LINKS = [
  { label: 'Home', href: '/' },
  { label: 'Features', href: '/#features' },
  { label: 'Pricing', href: '/#pricing' },
  { label: 'Resources', href: '/#resources' },
  { label: 'About', href: '/#about' },
]

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 12)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header className="sticky top-4 z-50 w-full px-4 sm:px-8 max-w-7xl mx-auto">
      <nav
        aria-label="Main Navigation"
        className={`h-[72px] px-6 rounded-[22px] flex items-center justify-between transition-all duration-300 ${
          isScrolled
            ? 'glass-strong bg-white/95 shadow-glass-lg border-white/95'
            : 'glass bg-white/80 border-white/90 shadow-glass'
        }`}
      >
        {/* Left: Brand Logo & Wordmark */}
        <Link to="/" className="flex items-center gap-2.5 group select-none">
          <div className="w-9 h-9 rounded-xl bg-[#0B0F19] text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform duration-200">
            {/* Minimalist Camera/Lens Glyph */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M3 9a2 2 0 0 1 2-2h1.5a2 2 0 0 0 1.6-.8L9.3 4.8A2 2 0 0 1 10.9 4h2.2a2 2 0 0 1 1.6.8l1.2 1.4a2 2 0 0 0 1.6.8H19a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" />
            </svg>
          </div>
          <span className="text-lg font-bold text-[#0B0F19] tracking-tight">
            CareerLens
          </span>
        </Link>

        {/* Center: Desktop Nav Links with animated active pill indicator */}
        <div className="hidden md:flex items-center gap-1.5 p-1 rounded-pill bg-slate-100/60 border border-slate-200/50 backdrop-blur-sm">
          {NAV_LINKS.map((link) => {
            const isActive = location.pathname === link.href || (link.href === '/' && location.pathname === '/')
            return (
              <a
                key={link.label}
                href={link.href}
                className={`relative px-4 py-1.5 text-xs font-semibold rounded-pill transition-colors duration-200 ${
                  isActive ? 'text-[#0B0F19]' : 'text-[#64748B] hover:text-[#0B0F19]'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNavPill"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    className="absolute inset-0 bg-white rounded-pill shadow-sm border border-slate-200/60"
                  />
                )}
                <span className="relative z-10">{link.label}</span>
              </a>
            )
          })}
        </div>

        {/* Right: Actions */}
        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                icon={LayoutDashboard}
                onClick={() => navigate('/dashboard')}
              >
                Dashboard
              </Button>
              <Button
                variant="ghost"
                size="sm"
                icon={LogOut}
                onClick={async () => {
                  await signOut()
                  navigate('/')
                }}
              >
                Sign out
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2.5">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate('/login')}
              >
                Login
              </Button>
              <Button
                variant="primary"
                size="sm"
                trailingIcon={ArrowRight}
                onClick={() => navigate('/signup')}
              >
                Get Started
              </Button>
            </div>
          )}
        </div>

        {/* Mobile Hamburger Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle mobile menu"
          className="md:hidden p-2 rounded-xl text-[#0B0F19] hover:bg-slate-100 transition-colors"
        >
          {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="md:hidden mt-2 p-5 glass-strong rounded-[20px] shadow-xl border border-white/90 space-y-3"
          >
            <div className="flex flex-col space-y-1">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2 text-sm font-semibold text-[#0B0F19] hover:bg-blue-50/60 rounded-xl transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </div>

            <div className="pt-3 border-t border-slate-200/80 flex flex-col gap-2">
              {user ? (
                <>
                  <Button
                    variant="primary"
                    size="sm"
                    className="w-full"
                    onClick={() => {
                      setMobileMenuOpen(false)
                      navigate('/dashboard')
                    }}
                  >
                    Go to Dashboard
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full"
                    onClick={async () => {
                      setMobileMenuOpen(false)
                      await signOut()
                      navigate('/')
                    }}
                  >
                    Sign out
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="w-full"
                    onClick={() => {
                      setMobileMenuOpen(false)
                      navigate('/login')
                    }}
                  >
                    Login
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    className="w-full"
                    trailingIcon={ArrowRight}
                    onClick={() => {
                      setMobileMenuOpen(false)
                      navigate('/signup')
                    }}
                  >
                    Get Started
                  </Button>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

export default Navbar
