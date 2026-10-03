import React from 'react'

export function Skeleton({
  className = '',
  variant = 'rounded', // 'rounded' | 'circular' | 'text' | 'card'
  ...props
}) {
  const variantStyles = {
    circular: 'rounded-full',
    text: 'rounded-md h-4',
    rounded: 'rounded-xl',
    card: 'rounded-2xl',
  }[variant] || 'rounded-xl'

  return (
    <div
      aria-hidden="true"
      className={`relative overflow-hidden bg-slate-200/70 ${variantStyles} ${className}`}
      {...props}
    >
      <div
        className="absolute inset-0 -translate-x-full animate-skeleton-shimmer bg-gradient-to-r from-transparent via-white/70 to-transparent"
        style={{ pointerEvents: 'none' }}
      />
    </div>
  )
}

export default Skeleton

