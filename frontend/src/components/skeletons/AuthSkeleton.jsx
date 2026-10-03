import React from 'react'
import { Skeleton } from '../ui/Skeleton'

export function AuthSkeleton() {
  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-[#F4F7FC] overflow-hidden">
      {/* Background Blobs */}
      <div
        className="absolute top-1/4 -left-20 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-60"
        style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.7) 0%, transparent 70%)' }}
      />
      <div
        className="absolute bottom-1/4 -right-20 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-60"
        style={{ background: 'radial-gradient(circle, rgba(224, 242, 254, 0.7) 0%, transparent 70%)' }}
      />

      <div className="relative w-full max-w-[440px] z-10">
        <div className="p-8 sm:p-10 rounded-[28px] bg-white/85 border border-white/95 shadow-[0_28px_64px_-16px_rgba(37,99,235,0.12)] backdrop-blur-2xl space-y-6">
          {/* Back to Home Link Placeholder */}
          <div className="flex items-center gap-2 mb-4">
            <Skeleton className="w-4 h-4 rounded-full" />
            <Skeleton className="w-24 h-3.5 rounded-md" />
          </div>

          {/* Logo & Headline */}
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <Skeleton className="w-8 h-8 rounded-xl" />
              <Skeleton className="w-28 h-6 rounded-md" />
            </div>
            <Skeleton className="w-48 h-7 rounded-lg pt-1" />
            <Skeleton className="w-56 h-3.5 rounded-md" />
          </div>

          {/* Inputs Skeleton */}
          <div className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <Skeleton className="w-16 h-3.5 rounded-md" />
              <Skeleton className="w-full h-11 rounded-xl" />
            </div>
            <div className="space-y-1.5">
              <Skeleton className="w-18 h-3.5 rounded-md" />
              <Skeleton className="w-full h-11 rounded-xl" />
            </div>
          </div>

          {/* Action Button Skeleton */}
          <Skeleton className="w-full h-12 rounded-xl mt-2" />

          {/* Divider */}
          <div className="flex items-center gap-3 pt-1">
            <div className="flex-1 h-px bg-slate-200" />
            <Skeleton className="w-24 h-3 rounded-md" />
            <div className="flex-1 h-px bg-slate-200" />
          </div>

          {/* OAuth Buttons Skeleton */}
          <div className="grid grid-cols-2 gap-3">
            <Skeleton className="w-full h-10 rounded-xl" />
            <Skeleton className="w-full h-10 rounded-xl" />
          </div>

          {/* Footer Link */}
          <div className="flex justify-center pt-2">
            <Skeleton className="w-44 h-3.5 rounded-md" />
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthSkeleton
