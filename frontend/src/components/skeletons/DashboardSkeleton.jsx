import React from 'react'
import { Skeleton } from '../ui/Skeleton'

export function DashboardSkeleton() {
  return (
    <div className="w-full max-w-6xl mx-auto space-y-8 pb-16 animate-in fade-in duration-300">
      {/* Hero Greeting Glass Banner Skeleton */}
      <div className="rounded-[24px] bg-white/80 border border-white/95 p-8 sm:p-10 shadow-[0_20px_50px_-15px_rgba(37,99,235,0.08)] backdrop-blur-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-2xl space-y-3.5">
            {/* Badge & Tier Pill */}
            <div className="flex items-center gap-2">
              <Skeleton className="w-36 h-6 rounded-full" />
              <Skeleton className="w-20 h-5 rounded-full" />
            </div>

            {/* Greeting Headline */}
            <Skeleton className="w-80 sm:w-96 h-9 sm:h-10 rounded-xl" />

            {/* Subtitle */}
            <div className="space-y-2 pt-1 max-w-lg">
              <Skeleton className="w-full h-4 rounded-md" />
              <Skeleton className="w-3/4 h-4 rounded-md" />
            </div>
          </div>

          {/* Right Action Button */}
          <div className="shrink-0">
            <Skeleton className="w-44 h-11 rounded-full" />
          </div>
        </div>
      </div>

      {/* 4 Stat Cards Grid Skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-[20px] bg-white/80 border border-white/95 p-5 sm:p-6 shadow-xs backdrop-blur-xl space-y-3"
          >
            <div className="flex items-center justify-between">
              <Skeleton className="w-10 h-10 rounded-xl" />
              <Skeleton className="w-12 h-4 rounded-md" />
            </div>
            <div className="space-y-1.5 pt-1">
              <Skeleton className="w-24 h-7 rounded-lg" />
              <Skeleton className="w-28 h-3.5 rounded-md" />
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions Section Skeleton */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="w-36 h-6 rounded-md" />
            <Skeleton className="w-64 h-3.5 rounded-md" />
          </div>
          <Skeleton className="w-24 h-4 rounded-md" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="rounded-[20px] bg-white/80 border border-white/95 p-6 shadow-xs backdrop-blur-xl space-y-4"
            >
              <div className="flex items-center justify-between">
                <Skeleton className="w-10 h-10 rounded-xl" />
                <Skeleton className="w-14 h-5 rounded-full" />
              </div>
              <div className="space-y-2 pt-1">
                <Skeleton className="w-40 h-5 rounded-md" />
                <Skeleton className="w-full h-3.5 rounded-md" />
                <Skeleton className="w-4/5 h-3.5 rounded-md" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Insights Glass Container Skeleton */}
      <div className="rounded-[24px] bg-white/80 border border-white/95 p-6 sm:p-8 shadow-xs backdrop-blur-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <Skeleton className="w-48 h-6 rounded-md" />
          <Skeleton className="w-20 h-4 rounded-md" />
        </div>
        <div className="space-y-3 pt-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50/70 border border-slate-100"
            >
              <div className="flex items-center gap-3">
                <Skeleton className="w-8 h-8 rounded-lg" />
                <div className="space-y-1">
                  <Skeleton className="w-48 h-4 rounded-md" />
                  <Skeleton className="w-24 h-3 rounded-md" />
                </div>
              </div>
              <Skeleton className="w-16 h-7 rounded-lg" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default DashboardSkeleton
