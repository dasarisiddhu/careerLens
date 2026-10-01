import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { supabase } from '../../services/supabase'
import { Eye, EyeOff, Loader2, Github, Chrome, Mail, Lock, User, AlertCircle, CheckCircle2, ArrowLeft } from 'lucide-react'
import { Button, Input, GlassCard } from '../../components/ui'
import { Mascot } from '../../mascot/Mascot'

export default function Signup() {
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [oauthProvider, setOauthProvider] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [cooldownSeconds, setCooldownSeconds] = useState(0)
  const [showPass, setShowPass] = useState(false)

  const handle = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }))

  useEffect(() => {
    if (cooldownSeconds <= 0) return
    const timer = setInterval(() => {
      setCooldownSeconds((seconds) => {
        if (seconds <= 1) {
          clearInterval(timer)
          return 0
        }
        return seconds - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [cooldownSeconds])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (cooldownSeconds > 0) return
    setLoading(true)
    setError('')
    try {
      const { error: signUpError } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
        options: {
          data: { name: form.name },
          emailRedirectTo: `${window.location.origin}/dashboard`,
        },
      })
      if (signUpError) {
        if (signUpError.status === 429) {
          setCooldownSeconds(60)
          setError('Rate limit exceeded. Please wait 60 seconds.')
        } else {
          setError(signUpError.message)
        }
        setLoading(false)
        return
      }
      setSuccess(true)
    } catch {
      setError('An unexpected error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
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
        className="relative w-full max-w-[460px] z-10"
      >
        <div className="absolute -top-16 -right-6 z-20 pointer-events-none hidden sm:block">
          <Mascot size={110} showPodium={false} state="wave" />
        </div>

        <GlassCard strong className="p-8 sm:p-10 rounded-[28px] shadow-glass-lg border-white/95">
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
              Create your account
            </h1>
            <p className="text-xs text-[#64748B] mt-1">
              Start analyzing resumes and unlocking career roadmaps.
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

            {success && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-[#16A34A] space-y-1"
              >
                <div className="flex items-center gap-2 font-bold">
                  <CheckCircle2 size={16} />
                  <span>Check your email to confirm registration!</span>
                </div>
                <p className="text-[#64748B]">
                  We sent a confirmation link to <span className="font-semibold">{form.email}</span>. Click it to activate your account.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {!success && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                type="text"
                required
                label="Full Name"
                value={form.name}
                onChange={handle('name')}
                placeholder="Jane Doe"
                leadingIcon={User}
              />

              <Input
                type="email"
                required
                label="Email Address"
                value={form.email}
                onChange={handle('email')}
                placeholder="you@example.com"
                leadingIcon={Mail}
              />

              <div>
                <Input
                  type={showPass ? 'text' : 'password'}
                  required
                  label="Password"
                  value={form.password}
                  onChange={handle('password')}
                  placeholder="Min 6 characters"
                  leadingIcon={Lock}
                  trailingIcon={showPass ? EyeOff : Eye}
                  onTrailingIconClick={() => setShowPass(!showPass)}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                disabled={loading || Boolean(oauthProvider) || cooldownSeconds > 0}
                loading={loading}
                className="w-full mt-2"
              >
                {cooldownSeconds > 0 ? `Wait ${cooldownSeconds}s` : 'Create Account'}
              </Button>
            </form>
          )}

          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-200" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
              or continue with
            </span>
            <div className="h-px flex-1 bg-slate-200" />
          </div>

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
            Already have an account?{' '}
            <Link to="/login" className="font-bold text-[#2563EB] hover:underline">
              Sign in
            </Link>
          </p>
        </GlassCard>
      </motion.div>
    </div>
  )
}
