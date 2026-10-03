import React from 'react'
import { Skeleton } from '../ui/Skeleton'
import { DashboardSkeleton } from './DashboardSkeleton'

export function DashboardLayoutSkeleton() {
  return (
    <div className="min-h-screen bg-[#F4F7FC] text-[#0B0F19] flex">
      {/* Sidebar Skeleton (hidden on mobile, fixed width on lg) */}
      <aside className="hidden lg:flex w-64 flex-col fixed inset-y-0 left-0 z-30 bg-white/80 border-r border-slate-200/80 backdrop-blur-xl p-5 justify-between">
        <div className="space-y-6">
          {/* Logo Skeleton */}
          <div className="flex items-center gap-3 px-2 py-1">
            <Skeleton className="w-8 h-8 rounded-xl" />
            <Skeleton className="w-28 h-6 rounded-md" />
          </div>

          {/* Section 1 Nav links */}
          <div className="space-y-1">
            <Skeleton className="w-20 h-3 rounded-md mb-3 ml-2" />
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl">
                <Skeleton className="w-4 h-4 rounded-md" />
                <Skeleton className="w-32 h-4 rounded-md" />
              </div>
            ))}
          </div>

          {/* Section 2 Nav links */}
          <div className="space-y-1 pt-2">
            <Skeleton className="w-24 h-3 rounded-md mb-3 ml-2" />
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl">
                <Skeleton className="w-4 h-4 rounded-md" />
                <Skeleton className="w-28 h-4 rounded-md" />
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Upgrade Pill Skeleton */}
        <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/60 space-y-2">
          <Skeleton className="w-24 h-4 rounded-md" />
          <Skeleton className="w-full h-8 rounded-xl" />
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Top Header Bar Skeleton */}
        <header className="sticky top-0 z-20 h-16 bg-white/70 border-b border-slate-200/60 backdrop-blur-xl px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton className="w-16 h-4 rounded-md hidden sm:block" />
            <Skeleton className="w-3 h-3 rounded-full hidden sm:block" />
            <Skeleton className="w-24 h-5 rounded-md" />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-slate-200/80 shadow-xs">
              <Skeleton className="w-6 h-6 rounded-full" />
              <Skeleton className="w-28 h-4 rounded-md hidden sm:block" />
            </div>
            <Skeleton className="w-18 h-8 rounded-full hidden sm:block" />
          </div>
        </header>

        {/* Inner Content Skeleton */}
        <main className="flex-1 p-6 sm:p-8">
          <DashboardSkeleton />
        </main>
      </div>
    </div>
  )
}

export default DashboardLayoutSkeleton
