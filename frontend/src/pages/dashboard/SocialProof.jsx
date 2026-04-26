// ============================================================
// CareerLens – Social Proof Widget
// File: frontend/src/components/dashboard/SocialProof.jsx
// ============================================================

import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { TrendingUp, Star, Users } from 'lucide-react'

const STORIES = [
  { name: 'Rahul S.',    role: 'ML Engineer',          improvement: '35% → 72%', action: 'Landed Amazon internship',        avatar: 'RS', color: 'bg-rose-600' },
  { name: 'Ananya K.',   role: 'Frontend Developer',   improvement: '41% → 68%', action: 'Hired at a funded startup',       avatar: 'AK', color: 'bg-rose-500' },
  { name: 'Siddharth M.',role: 'Data Analyst',         improvement: '28% → 61%', action: 'Got 3 interview calls in a week', avatar: 'SM', color: 'bg-rose-600' },
  { name: 'Priya R.',    role: 'Backend Developer',    improvement: '52% → 79%', action: 'Cleared Google online assessment', avatar: 'PR', color: 'bg-green-500' },
  { name: 'Arjun T.',    role: 'Full Stack Dev',       improvement: '19% → 55%', action: 'Resume shortlisted at 5 companies', avatar: 'AT', color: 'bg-rose-600' },
]

const STATS = [
  { label: 'Resumes analyzed',    value: '2,400+' },
  { label: 'Avg score improvement', value: '+31%' },
  { label: 'Interview calls reported', value: '580+' },
]

export default function SocialProof() {
  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="glass-glow rounded-2xl overflow-hidden">
      <div className="p-5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users size={17} className="text-rose-400" />
          <h2 className="font-bold text-white">Users Improving With CareerLens</h2>
        </div>
        <div className="flex gap-0.5">
          {[...Array(5)].map((_, i) => <Star key={i} size={12} className="text-rose-400 fill-rose-400" />)}
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 divide-x divide-white/5 border-b border-white/5">
        {STATS.map((s, i) => (
          <div key={i} className="p-4 text-center">
            <p className="text-xl font-black text-white">{s.value}</p>
            <p className="text-xs text-[#78716c] mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Stories */}
      <div className="p-4 space-y-3">
        {STORIES.map((story, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            className="relative flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5"
          >
            <div className="absolute left-0 top-2 bottom-2 w-1 rounded-full bg-gradient-to-b from-rose-600/70 via-rose-500/50 to-rose-600/40" />
            <div className={`w-9 h-9 rounded-xl ${story.color} flex items-center justify-center text-xs font-bold text-white shrink-0 ml-2`}>
              {story.avatar}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">{story.name}</span>
                <span className="text-xs text-[#44403c]">• {story.role}</span>
              </div>
              <p className="text-xs text-[#78716c] truncate">{story.action}</p>
            </div>
            <div className="shrink-0 text-right">
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-green-500/10 border border-green-500/20">
                <TrendingUp size={11} className="text-green-400" />
                <span className="text-xs font-bold text-green-400">{story.improvement}</span>
              </div>
              <span className="text-[10px] text-[#44403c] mt-1 block">Just now</span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="px-5 pb-4">
        <p className="text-xs text-[#44403c] text-center">
          * Results based on user-reported improvements. Individual results may vary.
        </p>
      </div>
    </div>
    </motion.div>
  )
}






