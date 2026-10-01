import React, { forwardRef } from 'react'
import { motion } from 'framer-motion'

export const GlassCard = forwardRef(function GlassCard(
  {
    children,
    className = '',
    strong = false,
    hoverable = false,
    onClick,
    ...props
  },
  ref
) {
  const cardClass = strong ? 'glass-strong' : 'glass'
  const hoverClass = hoverable
    ? 'hover:-translate-y-1 hover:shadow-glass-lg hover:border-blue-200/60 cursor-pointer'
    : ''

  if (hoverable) {
    return (
      <motion.div
        ref={ref}
        onClick={onClick}
        whileHover={{ y: -2 }}
        transition={{ duration: 0.2, ease: [0.2, 0.8, 0.2, 1] }}
        className={`${cardClass} ${hoverClass} ${className}`}
        {...props}
      >
        {children}
      </motion.div>
    )
  }

  return (
    <div
      ref={ref}
      onClick={onClick}
      className={`${cardClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
})

export default GlassCard
