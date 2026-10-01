import React from 'react'
import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="w-full border-t border-slate-200/80 bg-white/70 backdrop-blur-md mt-24 py-12 px-6 sm:px-12">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-[#0B0F19] text-white flex items-center justify-center shadow-sm">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M3 9a2 2 0 0 1 2-2h1.5a2 2 0 0 0 1.6-.8L9.3 4.8A2 2 0 0 1 10.9 4h2.2a2 2 0 0 1 1.6.8l1.2 1.4a2 2 0 0 0 1.6.8H19a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" />
            </svg>
          </div>
          <span className="text-base font-bold text-[#0B0F19] tracking-tight">CareerLens</span>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-semibold text-[#64748B]">
          <a href="#features" className="hover:text-[#0B0F19] transition-colors">Features</a>
          <a href="#pricing" className="hover:text-[#0B0F19] transition-colors">Pricing</a>
          <a href="#how-it-works" className="hover:text-[#0B0F19] transition-colors">How It Works</a>
          <Link to="/login" className="hover:text-[#0B0F19] transition-colors">Login</Link>
          <Link to="/signup" className="hover:text-[#0B0F19] transition-colors">Get Started</Link>
        </div>

        <p className="text-xs text-[#94A3B8]">
          &copy; {new Date().getFullYear()} CareerLens. All rights reserved.
        </p>
      </div>
    </footer>
  )
}

export default Footer
