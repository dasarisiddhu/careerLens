import React from 'react'
import { Skeleton } from '../ui/Skeleton'

export function CardsGridSkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-in fade-in duration-300">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-[24px] bg-white/80 border border-white/95 p-6 shadow-xs backdrop-blur-xl flex flex-col justify-between space-y-4"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="w-20 h-5 rounded-full" />
              <Skeleton className="w-16 h-3.5 rounded-md" />
            </div>
            <Skeleton className="w-4/5 h-5 rounded-md" />
            <div className="space-y-2 pt-1">
              <Skeleton className="w-full h-3.5 rounded-md" />
              <Skeleton className="w-11/12 h-3.5 rounded-md" />
              <Skeleton className="w-3/4 h-3.5 rounded-md" />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Skeleton className="w-6 h-6 rounded-full" />
              <Skeleton className="w-20 h-3.5 rounded-md" />
            </div>
            <Skeleton className="w-16 h-4 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  )
}

export default CardsGridSkeleton
