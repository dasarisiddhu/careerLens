import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { supabase } from '../../services/supabase'
import { Zap, Loader2, Github, Chrome, Mail, Lock, User, Eye, EyeOff } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'

function Particles() {
  const [particles, setParticles] = useState([])

  useEffect(() => {
    setParticles(
      Array.from({ length: 20 }).map((_, index) => ({
        id: index,
        left: Math.random() * 100,
        top: Math.random() * 100,
        size: Math.random() * 3 + 1,
        opacity: Math.random() * 0.28 + 0.08,
        duration: Math.random() * 6 + 4,
        delay: Math.random() * 2,
        color: index % 2 === 0 ? 'rgba(255,107,0,0.24)' : 'rgba(255,167,38,0.18)',
      })),
    )
  }, [])

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {particles.map((particle) => (
        <div
          key={particle.id}
          style={{
            position: 'absolute',
            left: `${particle.left}%`,
            top: `${particle.top}%`,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            borderRadius: '50%',
            background: particle.color,
            boxShadow: `0 0 ${particle.size * 8}px ${particle.color}`,
            animation: `float ${particle.duration}s ease-in-out ${particle.delay}s infinite alternate`,
          }}
        />
      ))}
    </div>
  )
}

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

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4 bg-[#0B0A10]">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-glow max-w-md rounded-3xl p-8 text-center"
        >
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 border border-primary/30 text-primary">
            <Mail size={28} />
          </div>
          <h2 className="font-display text-2xl font-bold text-white mb-2">Check your email</h2>
          <p className="text-sm text-slate-400 mb-6 leading-relaxed">
            We sent a confirmation link to <span className="text-white font-medium">{form.email}</span>. Click it to activate your account.
          </p>
          <Link to="/login">
            <Button variant="primary" className="w-full">
              Back to Sign In
            </Button>
          </Link>
        </motion.div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10 bg-[#0B0A10]"
    >
      <Particles />

      <motion.div
        initial={{ y: 28, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
        className="glass-glow relative z-[1] w-full max-w-[440px] overflow-hidden px-8 sm:px-10 py-10 rounded-3xl"
        style={{
          borderTop: '2px solid rgba(255,107,0,0.5)',
          boxShadow: '0 25px 60px rgba(0,0,0,0.5), 0 0 50px rgba(255,107,0,0.12)',
        }}
      >
        <div
          aria-hidden
          className="absolute right-0 top-0 h-40 w-40 rounded-full blur-3xl"
          style={{ background: 'radial-gradient(circle, rgba(255,107,0,0.16) 0%, transparent 72%)' }}
        />

        <div className="relative mb-8">
          <div className="mb-4 flex items-center gap-3">
            <div
              className="flex h-11 w-11 items-center justify-center rounded-xl"
              style={{
                background: 'linear-gradient(135deg, #FF6B00, #CC4E00)',
                boxShadow: '0 0 24px rgba(255,107,0,0.4)',
              }}
            >
              <Zap size={20} className="text-white fill-white" />
            </div>
            <div>
              <div className="gradient-text text-2xl font-bold font-display">CareerLens</div>
              <p className="text-[13px] text-[#9499B3]">Your AI career copilot</p>
            </div>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-white font-display">Create account</h1>
          <p className="text-sm text-[#9499B3]">Start your AI-powered career journey.</p>
        </div>

        {error && <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#F5F5F7]">Full Name</label>
            <div className="relative">
              <User size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[rgba(148,153,179,0.6)]" />
              <Input
                type="text"
                required
                value={form.name}
                onChange={handle('name')}
                placeholder="John Doe"
                className="pl-11"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#F5F5F7]">Email</label>
            <div className="relative">
              <Mail size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[rgba(148,153,179,0.6)]" />
              <Input
                type="email"
                required
                value={form.email}
                onChange={handle('email')}
                placeholder="you@example.com"
                className="pl-11"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#F5F5F7]">Password</label>
            <div className="relative">
              <Lock size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[rgba(148,153,179,0.6)]" />
              <Input
                type={showPass ? 'text' : 'password'}
                required
                value={form.password}
                onChange={handle('password')}
                placeholder="••••••••"
                className="pl-11 pr-11"
              />
              <button
                type="button"
                onClick={() => setShowPass((current) => !current)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#8A8FA8] transition hover:text-white"
              >
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            disabled={loading || cooldownSeconds > 0 || !!oauthProvider}
            className="w-full py-3 h-12 text-base"
          >
            {loading ? (
              <>
                <Loader2 size={17} className="animate-spin" />
                Creating account...
              </>
            ) : cooldownSeconds > 0 ? (
              `Try again in ${cooldownSeconds}s`
            ) : (
              'Create Account'
            )}
          </Button>
        </form>

        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(255,107,0,0.25)] to-transparent" />
          <span className="text-xs uppercase tracking-[0.18em] text-[#8A8FA8]">or continue with</span>
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(255,107,0,0.25)] to-transparent" />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <Button
            type="button"
            variant="ghost"
            onClick={() => handleOAuth('google')}
            disabled={loading || cooldownSeconds > 0 || !!oauthProvider}
            className="w-full h-11"
          >
            {oauthProvider === 'google' ? <Loader2 size={16} className="animate-spin" /> : <Chrome size={16} />}
            Google
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => handleOAuth('github')}
            disabled={loading || cooldownSeconds > 0 || !!oauthProvider}
            className="w-full h-11"
          >
            {oauthProvider === 'github' ? <Loader2 size={16} className="animate-spin" /> : <Github size={16} />}
            GitHub
          </Button>
        </div>

        <p className="mt-6 text-center text-sm text-[#8A8FA8]">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-primary-light transition hover:text-primary">
            Sign in
          </Link>
        </p>
      </motion.div>
    </motion.div>
  )
}
