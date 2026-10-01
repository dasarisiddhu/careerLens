import React, { useState, lazy, Suspense } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, Sparkles, X, ChevronUp, FileText, Compass, Briefcase, HelpCircle } from 'lucide-react'
import { NovaStaticFallback, NovaErrorBoundary } from './NovaFallback'

// Lazy load the 3D canvas so three.js + drei are chunked separately
const Nova3D = lazy(() => import('./Nova'))

const QUICK_ACTIONS = [
  {
    label: 'Analyze Resume',
    path: '/dashboard/optimizer',
    icon: FileText,
  },
  {
    label: 'Suggest Projects',
    path: '/dashboard/recommendations',
    icon: Compass,
  },
  {
    label: 'Find Jobs',
    path: '/dashboard/job-match',
    icon: Briefcase,
  },
  {
    label: 'Ask Anything',
    path: '/dashboard/chatbot',
    icon: HelpCircle,
  },
]

export default function CompanionWidget() {
  const [isOpen, setIsOpen] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()

  // Infer expression from active route/activity if applicable
  const getExpression = () => {
    if (location.pathname.includes('/chatbot')) return 'thinking'
    if (location.pathname.includes('/resume')) return 'analyzing'
    return 'idle'
  }

  const handleAction = (path) => {
    navigate(path)
  }

  return (
    <div
      className="fixed bottom-5 right-5 z-40 flex flex-col items-end pointer-events-auto select-none"
      style={{ isolation: 'isolate' }}
      data-lenis-prevent
    >
      {/* Speech bubble & Quick Action Chips */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 12, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.94 }}
            transition={{ type: 'spring', stiffness: 350, damping: 25 }}
            className="mb-2 w-72 sm:w-80 rounded-2xl border border-primary/30 bg-[#13121C]/92 p-4 shadow-[0_12px_40px_rgba(0,0,0,0.65),0_0_30px_rgba(255,107,0,0.15)] backdrop-blur-2xl"
          >
            {/* Speech bubble pointer / caret */}
            <div
              className="absolute -bottom-2 right-12 h-4 w-4 rotate-45 border-b border-r border-primary/30 bg-[#13121C]/92"
              aria-hidden
            />

            <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
                </span>
                <span className="font-display text-xs font-bold uppercase tracking-wider text-white">
                  Nova • AI Companion
                </span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
                aria-label="Minimize companion bubble"
              >
                <X size={14} />
              </button>
            </div>

            <p className="text-xs leading-relaxed text-slate-300 mb-3">
              Ready to accelerate your career? Pick an action or ask me anything:
            </p>

            {/* Quick Action Chips */}
            <div className="grid grid-cols-2 gap-2">
              {QUICK_ACTIONS.map((action) => {
                const Icon = action.icon
                return (
                  <button
                    key={action.label}
                    onClick={() => handleAction(action.path)}
                    className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-left text-xs font-medium text-slate-200 transition-all duration-200 hover:border-primary/40 hover:bg-primary/10 hover:text-white hover:shadow-[0_0_15px_rgba(255,107,0,0.2)] active:scale-[0.98]"
                  >
                    <Icon size={13} className="text-primary shrink-0" />
                    <span className="truncate">{action.label}</span>
                  </button>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating 3D Nova Character & Toggle Button */}
      <div className="relative flex items-center justify-center">
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(!isOpen)}
          className="relative cursor-pointer"
          title="Toggle Nova AI Assistant"
        >
          {/* Subtle glow underneath */}
          <div className="absolute inset-0 rounded-full bg-primary/20 blur-xl pointer-events-none" />

          {/* 3D Nova Avatar */}
          <div className="w-24 h-24 sm:w-28 sm:h-28 flex items-center justify-center">
            <NovaErrorBoundary size="widget" expression={getExpression()}>
              <Suspense fallback={<NovaStaticFallback size="widget" expression={getExpression()} />}>
                <Nova3D size="widget" expression={getExpression()} />
              </Suspense>
            </NovaErrorBoundary>
          </div>

          {/* Collapsed badge notification when bubble is closed */}
          {!isOpen && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-tr from-primary to-accent text-white shadow-[0_0_12px_rgba(255,107,0,0.6)]"
            >
              <Sparkles size={11} />
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
