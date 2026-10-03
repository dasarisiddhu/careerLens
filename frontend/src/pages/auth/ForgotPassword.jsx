import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { supabase } from '../../services/supabase'
import { ArrowLeft, Mail, AlertCircle, CheckCircle2 } from 'lucide-react'
import { Button, Input, GlassCard } from '../../components/ui'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email)
    if (resetError) {
      setError(resetError.message)
      setLoading(false)
    } else {
      setSent(true)
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-base overflow-hidden">
      <div
        className="absolute top-1/4 -left-20 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-60"
        style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.7) 0%, transparent 70%)' }}
      />
      <div
        className="absolute bottom-1/4 -right-20 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-60"
        style={{ background: 'radial-gradient(circle, rgba(224, 242, 254, 0.7) 0%, transparent 70%)' }}
      />

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
        className="relative w-full max-w-[440px] z-10"
      >
        <GlassCard strong className="p-8 sm:p-10 rounded-[28px] shadow-glass-lg border-white/95">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#64748B] hover:text-[#0B0F19] transition-colors mb-6"
          >
            <ArrowLeft size={14} />
            <span>Back to Login</span>
          </Link>

          {sent ? (
            <div className="text-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-[#16A34A] flex items-center justify-center mx-auto border border-emerald-200 shadow-sm">
                <CheckCircle2 size={28} />
              </div>
              <h2 className="text-2xl font-extrabold text-[#0B0F19]">Email sent!</h2>
              <p className="text-xs text-[#64748B] leading-relaxed">
                Check your inbox for a password reset link sent to <span className="font-semibold text-[#0B0F19]">{email}</span>.
              </p>
              <div className="pt-4">
                <Link to="/login">
                  <Button variant="primary" size="md" className="w-full">
                    Return to Sign In
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h1 className="text-2xl font-extrabold text-[#0B0F19] tracking-tight">
                  Reset password
                </h1>
                <p className="text-xs text-[#64748B] mt-1">
                  Enter your email and we'll send you a link to reset your password.
                </p>
              </div>

              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200/80 text-xs text-[#E11D48] flex items-center gap-2"
                  >
                    <AlertCircle size={15} className="shrink-0" />
                    <span>{error}</span>
                  </motion.div>
                )}
              </AnimatePresence>

              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  type="email"
                  required
                  label="Email Address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  leadingIcon={Mail}
                />

                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  disabled={loading}
                  loading={loading}
                  className="w-full"
                >
                  Send Reset Link
                </Button>
              </form>
            </>
          )}
        </GlassCard>
      </motion.div>
    </div>
  )
}
