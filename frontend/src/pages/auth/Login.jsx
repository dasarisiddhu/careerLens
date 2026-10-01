import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { supabase } from '../../services/supabase'
import { Eye, EyeOff, Loader2, Github, Chrome, Mail, Lock, AlertCircle, ArrowLeft } from 'lucide-react'
import { Button, Input, GlassCard } from '../../components/ui'
import { Mascot } from '../../mascot/Mascot'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [oauthProvider, setOauthProvider] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password })
    if (signInError) {
      setError(signInError.message)
      setLoading(false)
      return
    }
    navigate('/dashboard')
  }

  const handleOAuth = async (provider) => {
    setOauthProvider(provider)
    setError('')
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/dashboard`,
      },
    })
    if (oauthError) {
      setError(oauthError.message)
      setOauthProvider('')
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-base overflow-hidden">
      {/* Background Soft Sky Bloom */}
      <div
        className="absolute top-1/4 -left-20 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-60"
        style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.7) 0%, transparent 70%)' }}
      />
      <div
        className="absolute bottom-1/4 -right-20 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-60"
        style={{ background: 'radial-gradient(circle, rgba(224, 242, 254, 0.7) 0%, transparent 70%)' }}
      />

      {/* Centered Glass Card */}
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
        className="relative w-full max-w-[440px] z-10"
      >
        {/* Mascot Peeking from Top-Right */}
        <div className="absolute -top-16 -right-6 z-20 pointer-events-none hidden sm:block">
          <Mascot size={110} showPodium={false} state="greeting" />
        </div>

        <GlassCard strong className="p-8 sm:p-10 rounded-[28px] shadow-glass-lg border-white/95">
          {/* Header */}
          <div className="mb-6">
            <Link to="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#64748B] hover:text-[#0B0F19] transition-colors mb-4">
              <ArrowLeft size={14} />
              <span>Back to home</span>
            </Link>

            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-xl bg-[#0B0F19] text-white flex items-center justify-center font-bold text-xs shadow-sm">
                CL
              </div>
              <span className="text-base font-bold text-[#0B0F19] tracking-tight">CareerLens</span>
            </div>

            <h1 className="text-2xl font-extrabold text-[#0B0F19] tracking-tight">
              Welcome back
            </h1>
            <p className="text-xs text-[#64748B] mt-1">
              Sign in to continue building your career system.
            </p>
          </div>

          {/* Error Alert */}
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

          {/* Form */}
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

            <div>
              <Input
                type={showPass ? 'text' : 'password'}
                required
                label="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                leadingIcon={Lock}
                trailingIcon={showPass ? EyeOff : Eye}
                onTrailingIconClick={() => setShowPass(!showPass)}
              />
              <div className="text-right mt-1.5">
                <Link
                  to="/forgot-password"
                  className="text-xs font-semibold text-[#2563EB] hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={loading || Boolean(oauthProvider)}
              loading={loading}
              className="w-full"
            >
              Sign In
            </Button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-200" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
              or continue with
            </span>
            <div className="h-px flex-1 bg-slate-200" />
          </div>

          {/* Social OAuth Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              icon={Chrome}
              onClick={() => handleOAuth('google')}
              disabled={loading || Boolean(oauthProvider)}
              loading={oauthProvider === 'google'}
              className="w-full"
            >
              Google
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              icon={Github}
              onClick={() => handleOAuth('github')}
              disabled={loading || Boolean(oauthProvider)}
              loading={oauthProvider === 'github'}
              className="w-full"
            >
              GitHub
            </Button>
          </div>

          <p className="mt-6 text-center text-xs text-[#64748B]">
            Don't have an account?{' '}
            <Link to="/signup" className="font-bold text-[#2563EB] hover:underline">
              Sign up
            </Link>
          </p>
        </GlassCard>
      </motion.div>
    </div>
  )
}
