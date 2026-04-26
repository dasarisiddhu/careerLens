import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { supabase } from '../../services/supabase'
import { Zap, Eye, EyeOff, Loader2, Github, Chrome, Mail, Lock } from 'lucide-react'

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
        color: index % 2 === 0 ? 'rgba(255,59,59,0.24)' : 'rgba(200,30,30,0.18)',
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
    } else {
      navigate('/dashboard')
    }
  }

  const handleOAuth = async (provider) => {
    setError('')
    setOauthProvider(provider)
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/dashboard` },
    })
    if (oauthError) {
      setError(oauthError.message || 'OAuth sign-in failed.')
      setOauthProvider('')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10"
    >
      <Particles />

      <motion.div
        initial={{ y: 28, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
        className="glass-glow relative z-[1] w-full max-w-[420px] overflow-hidden px-10 py-11"
        style={{
          borderTop: '2px solid rgba(255,59,59,0.5)',
          boxShadow: '0 25px 60px rgba(0,0,0,0.5), 0 0 40px rgba(255,59,59,0.06)',
        }}
      >
        <div
          aria-hidden
          className="absolute right-0 top-0 h-40 w-40 rounded-full blur-3xl"
          style={{ background: 'radial-gradient(circle, rgba(255,59,59,0.14) 0%, transparent 72%)' }}
        />

        <div className="relative mb-8">
          <div className="mb-4 flex items-center gap-3">
            <div
              className="flex h-11 w-11 items-center justify-center rounded-xl"
              style={{
                background: 'linear-gradient(135deg,#FF3B3B,#CC1A1A)',
                boxShadow: '0 0 24px rgba(255,59,59,0.35)',
              }}
            >
              <Zap size={20} className="text-white" />
            </div>
            <div>
              <div className="gradient-text text-2xl font-bold">CareerLens</div>
              <p className="text-[13px] text-[#8A8FA8]">Your AI career copilot</p>
            </div>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-white">Welcome back</h1>
          <p className="text-sm text-[#8A8FA8]">Sign in to continue building your career system.</p>
        </div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#F5F5F7]">Email address</label>
            <div className="relative">
              <Mail size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[rgba(138,143,168,0.5)]" />
              <input
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                className="input-field pl-11"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#F5F5F7]">Password</label>
            <div className="relative">
              <Lock size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[rgba(138,143,168,0.5)]" />
              <input
                type={showPass ? 'text' : 'password'}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                className="input-field pl-11 pr-11"
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

          <div className="text-right">
            <Link to="/forgot-password" className="text-sm text-[#FF7070] transition hover:text-[#FF3B3B]">
              Forgot password?
            </Link>
          </div>

          <button type="submit" disabled={loading || !!oauthProvider} className="btn-primary w-full py-3">
            {loading ? (
              <>
                <Loader2 size={17} className="animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(255,59,59,0.2)] to-transparent" />
          <span className="text-xs uppercase tracking-[0.18em] text-[#8A8FA8]">or continue with</span>
          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(255,59,59,0.2)] to-transparent" />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => handleOAuth('google')}
            disabled={loading || !!oauthProvider}
            className="btn-ghost w-full"
          >
            {oauthProvider === 'google' ? <Loader2 size={16} className="animate-spin" /> : <Chrome size={16} />}
            Google
          </button>
          <button
            type="button"
            onClick={() => handleOAuth('github')}
            disabled={loading || !!oauthProvider}
            className="btn-ghost w-full"
          >
            {oauthProvider === 'github' ? <Loader2 size={16} className="animate-spin" /> : <Github size={16} />}
            GitHub
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-[#8A8FA8]">
          Don&apos;t have an account?{' '}
          <Link to="/signup" className="font-medium text-[#FF7070] transition hover:text-[#FF3B3B]">
            Sign up
          </Link>
        </p>
      </motion.div>
    </motion.div>
  )
}
