// frontend/src/pages/dashboard/Upgrade.jsx
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { CheckCircle, X, Zap, Star } from 'lucide-react'

const FEATURES = [
  { label: 'Resume Analyses', free: '1 only', premium: 'Unlimited' },
  { label: 'Mock Interviews', free: '1 only', premium: 'Unlimited' },
  { label: 'Honest Career Coach Messages', free: '20 messages', premium: 'Unlimited' },
  { label: 'ATS Compatibility Checker', free: false, premium: true },
  { label: 'AI Cover Letter Generator', free: false, premium: true },
  { label: 'Skill Gap Analyzer', free: false, premium: true },
  { label: 'Portfolio Website Generator', free: '4 generations', premium: 'Unlimited' },
  { label: 'Job Match Engine', free: false, premium: true },
  { label: 'GitHub Project Analyzer', free: false, premium: true },
  { label: 'Personalized AI Mentor', free: false, premium: true },
]

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap: { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

export default function Upgrade() {
  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden glass rounded-2xl p-10 text-center">
        <div className="absolute inset-0 bg-red-500/5" />
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl border border-red-500/20 bg-[#151924] flex items-center justify-center mx-auto mb-4">
            <Star size={28} className="text-[#FF7070]" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-3">Upgrade to Premium</h1>
          <p className="text-[#78716c] max-w-md mx-auto">Unlock unlimited AI analysis, interviews, and exclusive career tools to accelerate your job search.</p>
        </div>
      </motion.div>

      {/* Pricing cards */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Free */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
          className="glass p-6 rounded-2xl">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white mb-1">Free</h2>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-white">$0</span>
              <span className="text-[#78716c]">/month</span>
            </div>
          </div>
          <ul className="space-y-3 mb-8">
            {FEATURES.map((f, i) => (
              <li key={i} className="flex items-center gap-3 text-sm">
                {f.free === false
                  ? <X size={16} className="text-red-400 shrink-0" />
                  : <CheckCircle size={16} className="text-green-400 shrink-0" />}
                <span className={f.free === false ? 'text-[#44403c]' : 'text-[#d6d3d1]'}>
                  {f.label}{typeof f.free === 'string' ? ` – ${f.free}` : ''}
                </span>
              </li>
            ))}
          </ul>
          <motion.button {...buttonMotion} disabled className="btn-ghost w-full opacity-60 cursor-default">Current Plan</motion.button>
        </motion.div>

        {/* Premium */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}
          className="relative glass p-6 rounded-2xl border border-red-500/30 neon-glow">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
            <span className="border border-red-500/30 bg-[#151924] text-white text-xs font-bold px-4 py-1 rounded-full">MOST POPULAR</span>
          </div>
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white mb-1 flex items-center gap-2"><Star size={18} className="text-[#FF7070]" /> Premium</h2>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-white">$5.00</span>
              <span className="text-[#78716c]">/month</span>
            </div>
          </div>
          <ul className="space-y-3 mb-8">
            {FEATURES.map((f, i) => (
              <li key={i} className="flex items-center gap-3 text-sm">
                <CheckCircle size={16} className="text-green-400 shrink-0" />
                <span className="text-[#e7e5e4]">
                  {f.label}{f.premium === true ? '' : ` – ${f.premium}`}
                </span>
              </li>
            ))}
          </ul>
          <motion.button {...buttonMotion} className="btn-primary w-full flex items-center justify-center gap-2 py-4"
            onClick={() => alert('Payment integration coming soon! Connect Stripe or Razorpay.')}>
            <Zap size={16} /> Upgrade Now – $5.00/mo
          </motion.button>
          <p className="text-center text-xs text-[#44403c] mt-3">Cancel anytime · Secure payment via Stripe</p>
        </motion.div>
      </div>
    </div>
    </motion.div>
  )
}










