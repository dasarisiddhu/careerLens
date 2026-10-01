import React from 'react'

export function Skeleton({ className = '', ...props }) {
  return (
    <div
      aria-hidden="true"
      className={`relative overflow-hidden bg-slate-200/60 rounded-xl ${className}`}
      {...props}
    >
      <div
        className="absolute inset-0 -translate-x-full animate-[shimmer_1.8s_infinite] bg-gradient-to-r from-transparent via-white/50 to-transparent"
        style={{
          animationName: 'shimmer',
          animationDuration: '1.8s',
          animationIterationCount: 'infinite',
        }}
      />
      <style>{`
        @keyframes shimmer {
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  )
}

export default Skeleton
