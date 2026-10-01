import React from 'react'
import GlassCard from './GlassCard'

export function StatCard({
  icon: Icon,
  iconColor = 'blue', // 'blue', 'violet', 'coral', 'emerald'
  label,
  value,
  subtitle,
  tag,
  className = '',
  ...props
}) {
  const iconTileStyles = {
    blue: 'bg-blue-50 text-[#2563EB] border border-blue-200/60 shadow-sm',
    violet: 'bg-indigo-50 text-[#4F46E5] border border-indigo-200/60 shadow-sm',
    coral: 'bg-orange-50 text-[#EA580C] border border-orange-200/60 shadow-sm',
    emerald: 'bg-emerald-50 text-[#16A34A] border border-emerald-200/60 shadow-sm',
  }

  return (
    <GlassCard className={`p-4 flex items-center gap-3.5 ${className}`} {...props}>
      {Icon && (
        <div
          className={`w-11 h-11 rounded-icon flex items-center justify-center shrink-0 ${iconTileStyles[iconColor] || iconTileStyles.blue}`}
        >
          <Icon size={20} strokeWidth={2} />
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1 mb-0.5">
          <p className="text-xs font-medium text-[#64748B] truncate">{label}</p>
          {tag && (
            <span className="text-[10px] font-semibold text-[#2563EB] bg-blue-50 px-1.5 py-0.5 rounded-md">
              {tag}
            </span>
          )}
        </div>
        <p className="text-xl font-bold text-[#0B0F19] tracking-tight">{value}</p>
        {subtitle && <p className="text-[11px] text-[#94A3B8] truncate">{subtitle}</p>}
      </div>
    </GlassCard>
  )
}

export default StatCard
