import React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold tracking-wide transition-colors uppercase font-display',
  {
    variants: {
      variant: {
        default:
          'bg-primary/15 text-primary-light border border-primary/30 shadow-[0_0_12px_rgba(255,107,0,0.18)]',
        accent:
          'bg-accent/15 text-accent-light border border-accent/30 shadow-[0_0_12px_rgba(255,167,38,0.2)]',
        glass:
          'bg-white/[0.05] text-slate-300 border border-white/[0.1] backdrop-blur-md',
        success:
          'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
        danger:
          'bg-rose-500/15 text-rose-400 border border-rose-500/30',
        outline:
          'border border-white/20 text-slate-300',
      },
      size: {
        sm: 'px-2 py-0.5 text-[10px]',
        md: 'px-3 py-1 text-xs',
        lg: 'px-4 py-1.5 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

function Badge({ className, variant, size, ...props }) {
  return (
    <span className={cn(badgeVariants({ variant, size }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
