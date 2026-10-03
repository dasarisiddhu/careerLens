import React from 'react'
import { Skeleton } from '../ui/Skeleton'

export function LandingSkeleton() {
  return (
    <div className="min-h-screen bg-[#F4F7FC] relative overflow-hidden text-slate-800">
      {/* Background Soft Blobs */}
      <div
        className="absolute top-10 left-1/4 w-[480px] h-[480px] rounded-full pointer-events-none blur-3xl opacity-50"
        style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.8) 0%, transparent 70%)' }}
      />
      <div
        className="absolute top-60 right-10 w-[420px] h-[420px] rounded-full pointer-events-none blur-3xl opacity-40"
        style={{ background: 'radial-gradient(circle, rgba(224, 242, 254, 0.7) 0%, transparent 70%)' }}
      />

      {/* Navigation Bar Skeleton */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-slate-200/60 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <Skeleton className="w-9 h-9 rounded-xl" />
            <Skeleton className="w-28 h-6 rounded-md" />
          </div>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-7">
            <Skeleton className="w-16 h-4 rounded-md" />
            <Skeleton className="w-20 h-4 rounded-md" />
            <Skeleton className="w-24 h-4 rounded-md" />
            <Skeleton className="w-16 h-4 rounded-md" />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <Skeleton className="w-18 h-9 rounded-full hidden sm:block" />
            <Skeleton className="w-28 h-9 rounded-full" />
          </div>
        </div>
      </header>

      {/* Hero Section Skeleton */}
      <main className="max-w-7xl mx-auto px-6 pt-12 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Headlines & CTAs */}
          <div className="lg:col-span-7 space-y-6">
            {/* Sparkle Badge Pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 border border-slate-200/80 shadow-xs">
              <Skeleton className="w-4 h-4 rounded-full" />
              <Skeleton className="w-44 h-4 rounded-md" />
            </div>

            {/* Giant Title Bars */}
            <div className="space-y-3 pt-1">
              <Skeleton className="w-11/12 max-w-xl h-12 sm:h-14 rounded-2xl" />
              <Skeleton className="w-4/5 max-w-md h-12 sm:h-14 rounded-2xl" />
            </div>

            {/* Subtitle Lines */}
            <div className="space-y-2.5 max-w-lg pt-1">
              <Skeleton className="w-full h-4 rounded-md" />
              <Skeleton className="w-5/6 h-4 rounded-md" />
              <Skeleton className="w-3/4 h-4 rounded-md" />
            </div>

            {/* CTA Buttons Row */}
            <div className="flex flex-wrap items-center gap-3.5 pt-3">
              <Skeleton className="w-44 h-12 rounded-full" />
              <Skeleton className="w-36 h-12 rounded-full" />
            </div>

            {/* Trust Badges Bar */}
            <div className="pt-6 border-t border-slate-200/70 flex items-center gap-6">
              <div className="space-y-1">
                <Skeleton className="w-16 h-5 rounded-md" />
                <Skeleton className="w-24 h-3 rounded-md" />
              </div>
              <div className="w-px h-8 bg-slate-200" />
              <div className="space-y-1">
                <Skeleton className="w-16 h-5 rounded-md" />
                <Skeleton className="w-28 h-3 rounded-md" />
              </div>
              <div className="w-px h-8 bg-slate-200 hidden sm:block" />
              <div className="space-y-1 hidden sm:block">
                <Skeleton className="w-16 h-5 rounded-md" />
                <Skeleton className="w-24 h-3 rounded-md" />
              </div>
            </div>
          </div>

          {/* Right Column: Hero Preview Card Skeleton */}
          <div className="lg:col-span-5">
            <div className="relative rounded-[28px] bg-white/80 border border-white/95 p-6 sm:p-8 shadow-[0_24px_60px_-15px_rgba(37,99,235,0.12)] backdrop-blur-xl space-y-6">
              {/* Card Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Skeleton className="w-10 h-10 rounded-xl" />
                  <div className="space-y-1.5">
                    <Skeleton className="w-28 h-4 rounded-md" />
                    <Skeleton className="w-20 h-3 rounded-md" />
                  </div>
                </div>
                <Skeleton className="w-16 h-6 rounded-full" />
              </div>

              {/* Center Circular Score Visual */}
              <div className="flex flex-col items-center justify-center py-6 space-y-3">
                <Skeleton className="w-36 h-36 rounded-full" />
                <Skeleton className="w-32 h-4 rounded-md" />
              </div>

              {/* Metric Breakdown Bars */}
              <div className="space-y-3 pt-2">
                <div className="flex justify-between items-center">
                  <Skeleton className="w-24 h-3.5 rounded-md" />
                  <Skeleton className="w-10 h-3.5 rounded-md" />
                </div>
                <Skeleton className="w-full h-2 rounded-full" />
                <div className="flex justify-between items-center pt-1">
                  <Skeleton className="w-28 h-3.5 rounded-md" />
                  <Skeleton className="w-10 h-3.5 rounded-md" />
                </div>
                <Skeleton className="w-full h-2 rounded-full" />
              </div>
            </div>
          </div>
        </div>

        {/* Feature Cards Skeleton Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-2xl bg-white/70 border border-white/90 p-6 shadow-xs backdrop-blur-md space-y-4"
            >
              <Skeleton className="w-12 h-12 rounded-xl" />
              <Skeleton className="w-3/5 h-5 rounded-md" />
              <div className="space-y-2">
                <Skeleton className="w-full h-3.5 rounded-md" />
                <Skeleton className="w-4/5 h-3.5 rounded-md" />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

export default LandingSkeleton
