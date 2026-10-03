import React from 'react'
import { Skeleton } from '../ui/Skeleton'

export function ContentPageSkeleton() {
  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 pb-16 animate-in fade-in duration-200">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="w-28 h-6 rounded-full" />
          <Skeleton className="w-64 sm:w-80 h-8 sm:h-9 rounded-xl" />
          <Skeleton className="w-96 max-w-full h-4 rounded-md" />
        </div>
        <div className="flex items-center gap-3">
          <Skeleton className="w-32 h-10 rounded-full" />
        </div>
      </div>

      {/* Main Glass Content Card Skeleton */}
      <div className="rounded-[28px] bg-white/80 border border-white/95 p-8 sm:p-10 shadow-xs backdrop-blur-xl space-y-6">
        {/* Secondary Header or Tabs */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <Skeleton className="w-24 h-8 rounded-lg" />
            <Skeleton className="w-24 h-8 rounded-lg" />
          </div>
          <Skeleton className="w-28 h-6 rounded-md" />
        </div>

        {/* Content Placeholder Lines / Cards */}
        <div className="space-y-4 py-2">
          <Skeleton className="w-full h-12 rounded-xl" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-5 rounded-2xl bg-slate-50/80 border border-slate-100 space-y-3">
              <Skeleton className="w-10 h-10 rounded-xl" />
              <Skeleton className="w-36 h-5 rounded-md" />
              <Skeleton className="w-full h-3.5 rounded-md" />
              <Skeleton className="w-4/5 h-3.5 rounded-md" />
            </div>
            <div className="p-5 rounded-2xl bg-slate-50/80 border border-slate-100 space-y-3">
              <Skeleton className="w-10 h-10 rounded-xl" />
              <Skeleton className="w-40 h-5 rounded-md" />
              <Skeleton className="w-full h-3.5 rounded-md" />
              <Skeleton className="w-3/4 h-3.5 rounded-md" />
            </div>
          </div>
          <Skeleton className="w-full h-24 rounded-2xl mt-4" />
        </div>
      </div>
    </div>
  )
}

export default ContentPageSkeleton
