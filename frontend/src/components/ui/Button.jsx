import React from 'react'
import { cva } from 'class-variance-authority'
import { Slot } from '@radix-ui/react-slot'
import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 disabled:pointer-events-none disabled:opacity-40 select-none active:scale-[0.98]',
  {
    variants: {
      variant: {
        primary:
          'bg-gradient-to-r from-primary to-primary-dark text-white shadow-[0_4px_20px_rgba(255,107,0,0.38)] hover:shadow-[0_6px_28px_rgba(255,107,0,0.55)] hover:-translate-y-0.5 border border-primary-light/20',
        ghost:
          'bg-white/[0.04] text-slate-300 hover:text-white hover:bg-primary/10 hover:border-primary/30 border border-white/[0.08]',
        glow:
          'bg-gradient-to-r from-primary via-accent to-primary text-white shadow-[0_0_28px_rgba(255,107,0,0.5)] hover:shadow-[0_0_45px_rgba(255,107,0,0.75)] hover:scale-[1.02] border border-amber-300/30',
        outline:
          'border border-primary/40 bg-transparent text-primary hover:bg-primary/10 hover:border-primary',
        secondary:
          'bg-surface-elevated text-slate-200 hover:bg-surface-elevated/80 border border-white/10 hover:text-white',
        danger:
          'bg-rose-600/80 text-white hover:bg-rose-600 border border-rose-500/30 shadow-[0_4px_16px_rgba(225,29,72,0.3)]',
      },
      size: {
        sm: 'h-8 px-3 text-xs rounded-lg',
        md: 'h-10 px-4 py-2',
        lg: 'h-12 px-6 text-base rounded-2xl',
        icon: 'h-9 w-9 p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
)

const Button = React.forwardRef(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
