// frontend/src/pages/auth/ForgotPassword.jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { supabase } from '../../services/supabase'
import { Zap, Loader2, ArrowLeft } from 'lucide-react'

const buttonMotion = {
  whileHover: { scale: 1.03, y: -1 },
  whileTap: { scale: 0.97 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    const { error } = await supabase.auth.resetPasswordForEmail(email)
    if (error) { setError(error.message); setLoading(false) }
    else setSent(true)
  }

  return (
    <div className="min-h-screen bg-transparent flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-red-500/12 rounded-full blur-3xl pointer-events-none" />
      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md glass p-8 rounded-2xl relative z-10">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl border border-red-500/20 bg-[#151924] flex items-center justify-center">
            <Zap size={20} className="text-[#FF7070]" />
          </div>
          <span className="text-2xl font-bold gradient-text">CareerLens</span>
        </div>
        {sent ? (
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4 text-3xl">📧</div>
            <h2 className="text-2xl font-bold text-white mb-2">Email sent!</h2>
            <p className="text-[#d6d3d1] mb-6">Check your inbox for a password reset link.</p>
            <Link to="/login" className="btn-primary inline-block">Back to Login</Link>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-white mb-1">Reset password</h1>
            <p className="text-[#d6d3d1] text-sm mb-8">Enter your email and we'll send a reset link</p>
            {error && <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#d6d3d1] mb-1.5">Email</label>
                <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" className="input-field" />
              </div>
              <motion.button {...buttonMotion} type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                {loading ? <><Loader2 size={16} className="animate-spin" /> Sending...</> : 'Send Reset Link'}
              </motion.button>
            </form>
            <Link to="/login" className="mt-6 flex items-center gap-2 text-sm text-[#78716c] hover:text-white transition-colors">
              <ArrowLeft size={14} /> Back to Login
            </Link>
          </>
        )}
      </motion.div>
    </div>
  )
}




