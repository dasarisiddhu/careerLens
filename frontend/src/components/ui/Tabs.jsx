import React from 'react'
import { motion } from 'framer-motion'

export function Tabs({
  tabs = [], // [{ id, label, icon: Icon }]
  activeTab,
  onChange,
  className = '',
}) {
  return (
    <div
      role="tablist"
      className={`inline-flex items-center p-1 bg-slate-100/90 rounded-pill border border-slate-200/80 backdrop-blur-sm ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id
        const Icon = tab.icon

        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onChange?.(tab.id)}
            className={`relative px-4 py-1.5 text-xs font-semibold rounded-pill transition-colors duration-200 select-none focus-ring flex items-center gap-2 ${
              isActive ? 'text-[#0B0F19]' : 'text-[#64748B] hover:text-[#0B0F19]'
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="activeTabPill"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                className="absolute inset-0 bg-white rounded-pill shadow-sm border border-slate-200/60"
              />
            )}
            {Icon && <Icon size={14} className="relative z-10 shrink-0" />}
            <span className="relative z-10">{tab.label}</span>
          </button>
        )
      })}
    </div>
  )
}

export default Tabs
