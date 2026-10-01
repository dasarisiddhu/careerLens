import React from 'react'
import { Sparkles } from 'lucide-react'

export function Badge({
  children,
  variant = 'blue', // 'blue', 'neutral', 'success', 'warning', 'danger'
  size = 'md', // 'sm', 'md'
  icon: Icon,
  className = '',
  sparkle = false,
  ...props
}) {
  const baseStyles =
    'inline-flex items-center font-medium rounded-pill border select-none transition-colors'

  const sizeStyles = {
    sm: 'text-[11px] px-2.5 py-0.5 gap-1.5',
    md: 'text-xs px-3.5 py-1 gap-2',
  }

  const variantStyles = {
    blue: 'bg-blue-50/90 text-[#2563EB] border-blue-200/70 shadow-sm',
    neutral: 'bg-white/80 text-[#475569] border-slate-200/80 shadow-sm',
    success: 'bg-emerald-50 text-[#16A34A] border-emerald-200/70',
    warning: 'bg-amber-50 text-[#D97706] border-amber-200/70',
    danger: 'bg-rose-50 text-[#E11D48] border-rose-200/70',
  }

  return (
    <span
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {sparkle && <Sparkles size={size === 'sm' ? 11 : 13} className="text-[#2563EB] shrink-0" />}
      {Icon && <Icon size={size === 'sm' ? 11 : 13} className="shrink-0" />}
      <span>{children}</span>
    </span>
  )
}

export default Badge
