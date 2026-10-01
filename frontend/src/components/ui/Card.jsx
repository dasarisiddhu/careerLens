import React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const cardVariants = cva(
  'rounded-2xl transition-all duration-300 relative overflow-hidden',
  {
    variants: {
      variant: {
        default:
          'bg-surface-card/80 backdrop-blur-xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.45)] hover:border-primary/20 hover:shadow-[0_8px_36px_rgba(255,107,0,0.08)]',
        glass:
          'bg-surface-card/70 backdrop-blur-2xl border border-white/[0.07] shadow-[0_8px_32px_rgba(0,0,0,0.4)] hover:border-primary/25 hover:shadow-[0_0_30px_rgba(255,107,0,0.1)]',
        'elevated-glow':
          'bg-gradient-to-b from-surface-elevated/90 to-surface-card/95 backdrop-blur-2xl border border-primary/25 shadow-[0_16px_48px_rgba(0,0,0,0.65),0_0_35px_rgba(255,107,0,0.15)] ring-1 ring-primary/20 hover:border-primary/40 hover:shadow-[0_18px_56px_rgba(0,0,0,0.7),0_0_45px_rgba(255,107,0,0.25)]',
        subtle:
          'bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

const Card = React.forwardRef(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(cardVariants({ variant, className }))}
    {...props}
  />
))
Card.displayName = 'Card'

const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
))
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('font-display text-xl font-bold tracking-tight text-white', className)}
    {...props}
  />
))
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-slate-400', className)}
    {...props}
  />
))
CardDescription.displayName = 'CardDescription'

const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
))
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
))
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent, cardVariants }
