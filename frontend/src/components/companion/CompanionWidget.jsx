import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, X, FileText, Compass, Briefcase, HelpCircle } from 'lucide-react'
import { MASCOT_CONFIG } from '../../mascot/mascot.config'

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
            initial={{ opacity: 0, y: 10, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.94 }}
            transition={{ type: 'spring', stiffness: 350, damping: 25 }}
            className="mb-3 w-72 sm:w-80 rounded-[22px] border border-white/90 bg-white/95 p-4 shadow-[0_16px_40px_rgba(37,99,235,0.12),0_4px_16px_rgba(15,23,42,0.06)] backdrop-blur-2xl"
          >
            {/* Speech bubble pointer / caret */}
            <div
              className="absolute -bottom-2 right-8 h-4 w-4 rotate-45 border-b border-r border-slate-200 bg-white"
              aria-hidden="true"
            />

            <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2563EB] opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#2563EB]" />
                </span>
                <span className="text-xs font-bold uppercase tracking-wider text-[#0B0F19]">
                  Lens • AI Career Companion
                </span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-full p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                aria-label="Minimize companion bubble"
              >
                <X size={14} />
              </button>
            </div>

            <p className="text-xs leading-relaxed text-[#475569] mb-3 font-medium">
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
                    className="flex items-center gap-2 rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-2 text-left text-xs font-semibold text-[#1E293B] transition-all duration-200 hover:border-blue-300 hover:bg-blue-50/60 hover:text-[#2563EB] active:scale-[0.98]"
                  >
                    <Icon size={14} className="text-[#2563EB] shrink-0" />
                    <span className="truncate">{action.label}</span>
                  </button>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Lightweight Mascot Launcher */}
      <div className="relative flex items-center justify-center">
        <motion.div
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(!isOpen)}
          className="relative cursor-pointer p-1 rounded-full bg-white/90 shadow-glass-lg border border-white/95 backdrop-blur-md"
          title="Toggle Lens AI Assistant"
        >
          {/* Subtle glow underneath */}
          <div className="absolute inset-0 rounded-full bg-blue-400/20 blur-lg pointer-events-none" />

          {/* 3D Mascot Avatar Launcher */}
          <div className="w-14 h-14 sm:w-16 sm:h-16 flex items-center justify-center overflow-hidden rounded-full">
            <img
              src={MASCOT_CONFIG.assets.hero}
              alt="Lens Assistant"
              width={64}
              height={64}
              className="w-full h-full object-contain pointer-events-none scale-125"
            />
          </div>

          {/* Notification ping badge when bubble is closed */}
          {!isOpen && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-[#2563EB] text-white shadow-sm"
            >
              <Sparkles size={11} />
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
