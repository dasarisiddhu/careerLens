import React, { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'

export const Button = forwardRef(function Button(
  {
    children,
    variant = 'primary', // 'primary' (dark black pill), 'blue' (solid blue pill), 'secondary' (white glass pill), 'ghost', 'destructive'
    size = 'md', // 'sm', 'md', 'lg'
    className = '',
    icon: Icon,
    trailingIcon: TrailingIcon,
    loading = false,
    disabled = false,
    type = 'button',
    onClick,
    ...props
  },
  ref
) {
  const baseStyles =
    'relative inline-flex items-center justify-center font-semibold rounded-pill transition-all duration-200 focus-ring select-none disabled:opacity-50 disabled:pointer-events-none'

  const sizeStyles = {
    sm: 'text-xs px-3.5 py-1.5 gap-1.5 h-8',
    md: 'text-sm px-5 py-2.5 gap-2 h-11',
    lg: 'text-base px-7 py-3.5 gap-2.5 h-[52px]',
  }

  const variantStyles = {
    primary:
      'bg-[#0B0F19] text-white hover:bg-[#1E293B] shadow-[0_4px_14px_rgba(11,15,25,0.18)] border border-black/10 active:bg-black',
    blue:
      'bg-[#2563EB] text-white hover:bg-[#1D4ED8] shadow-[0_4px_16px_rgba(37,99,235,0.25)] border border-blue-600/20 active:bg-blue-800',
    secondary:
      'bg-white/80 hover:bg-white text-[#0B0F19] border border-slate-200/80 shadow-[0_2px_8px_rgba(0,0,0,0.04)] backdrop-blur-md active:bg-slate-100',
    ghost:
      'bg-transparent text-[#475569] hover:text-[#0B0F19] hover:bg-slate-100/70',
    destructive:
      'bg-[#E11D48] text-white hover:bg-[#BE123C] shadow-[0_4px_14px_rgba(225,29,72,0.2)]',
  }

  return (
    <motion.button
      ref={ref}
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      whileHover={disabled || loading ? undefined : { y: -1 }}
      whileTap={disabled || loading ? undefined : { scale: 0.98 }}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 14 : 18} className="animate-spin text-current" />
      ) : (
        <>
          {Icon && <Icon size={size === 'sm' ? 14 : 18} className="shrink-0" />}
          <span>{children}</span>
          {TrailingIcon && <TrailingIcon size={size === 'sm' ? 14 : 18} className="shrink-0" />}
        </>
      )}
    </motion.button>
  )
})

export default Button
