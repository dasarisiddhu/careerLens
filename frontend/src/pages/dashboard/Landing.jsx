// ============================================================
// CareerLens – Public Landing Page
// File: frontend/src/pages/Landing.jsx
// ============================================================

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { fadeUp, staggerContainer, pageTransition } from '../../utils/animations'
import {
  Zap, Target, FileText, Github, TrendingUp,
  CheckCircle, Star, ArrowRight, Users,
  BarChart3, Brain, ChevronDown
} from 'lucide-react'

// ------------------------------------------------------------
// Particles
// ------------------------------------------------------------
function Particles() {
  const [particles, setParticles] = useState([])

  useEffect(() => {
    const items = Array.from({ length: 20 }).map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.4 + 0.1,
      duration: Math.random() * 5 + 3,
      delay: Math.random() * 2,
      color: i % 2 === 0 ? '217,119,6' : '180,83,9',
    }))
    setParticles(items)
  }, [])

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.left}%`,
            top: `${p.top}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            borderRadius: '50%',
            background: `rgba(${p.color}, ${p.opacity})`,
            animation: `float ${p.duration}s ease-in-out ${p.delay}s infinite alternate`,
          }}
        />
      ))}
    </div>
  )
}

// ------------------------------------------------------------
// Helpers
// ------------------------------------------------------------
const NAV_LINKS = ['Features', 'How It Works', 'Pricing', 'Success Stories']

const FEATURES = [
  { icon: FileText,   color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20', glow: 'bg-amber-500/30', title: 'AI Resume Analysis',         desc: 'Brutally honest score with specific improvements — not generic tips.' },
  { icon: Target,     color: 'text-amber-400',   bg: 'bg-amber-500/10 border-amber-500/20',     glow: 'bg-amber-500/30',   title: 'Interview Probability',      desc: 'Know your exact % chance for any role before applying.' },
  { icon: BarChart3,  color: 'text-yellow-500', bg: 'bg-amber-500/10 border-amber-500/20', glow: 'bg-amber-500/30', title: 'ATS Checker',               desc: 'See if your resume survives applicant tracking systems.' },
  { icon: Zap,        color: 'text-amber-400',  bg: 'bg-amber-500/10 border-amber-500/20',   glow: 'bg-amber-500/30',  title: 'Resume Optimizer',          desc: 'AI rewrites your bullets to match any specific job description.' },
  { icon: Brain,      color: 'text-amber-300',  bg: 'bg-amber-500/10 border-amber-500/20',   glow: 'bg-amber-500/30',  title: 'Mock Interviews',           desc: 'Practice with AI questions tailored to your exact role and level.' },
  { icon: Github,     color: 'text-amber-200',  bg: 'bg-amber-500/10 border-amber-500/20',            glow: 'bg-amber-500/30',       title: 'GitHub Portfolio Analysis', desc: 'Get feedback on your actual projects and coding activity.' },
  { icon: TrendingUp, color: 'text-amber-400',   bg: 'bg-amber-500/10 border-amber-500/20',     glow: 'bg-amber-500/30',   title: 'Career Roadmap',            desc: 'Step-by-step plan from your current skills to your target job.' },
  { icon: Users,      color: 'text-amber-300',    bg: 'bg-amber-500/10 border-amber-500/20',       glow: 'bg-amber-500/30',    title: 'Community Feed',            desc: 'Share projects, find collaborators, discover opportunities.' },
]

const STEPS = [
  { step: '01', title: 'Upload your resume',       desc: 'PDF upload, takes 5 seconds.', icon: FileText },
  { step: '02', title: 'Add your GitHub & target role', desc: 'We analyze your actual projects.', icon: Github },
  { step: '03', title: 'Get your Interview Score', desc: 'See exactly where you stand.', icon: Target },
  { step: '04', title: 'Follow the action plan',   desc: 'Specific tasks to improve your score.', icon: TrendingUp },
]

const PRICING = [
  {
    name: 'Free',
    price: '₹0',
    period: 'forever',
    color: 'border-white/10',
    features: ['Resume Analysis (3/month)', 'Basic ATS Score', 'Interview Probability (1/month)', 'Honest Career Coach (10 messages)', 'Community Feed'],
    cta: 'Get Started Free',
    ctaStyle: 'btn-ghost w-full',
    popular: false,
  },
  {
    name: 'Pro',
    price: '₹299',
    period: '/month',
    color: 'border-amber-500',
    features: ['Unlimited Resume Analysis', 'Resume Optimizer', 'Unlimited Interview Probability', 'Mock Interviews (unlimited)', 'Job Match Engine', 'Portfolio Generator', 'Progress Tracker', 'Priority AI responses'],
    cta: 'Start Pro — ₹299/mo',
    ctaStyle: 'btn-primary w-full',
    popular: true,
  },
  {
    name: 'Lifetime',
    price: '₹1,999',
    period: 'one-time',
    color: 'border-amber-500/50',
    features: ['Everything in Pro', 'Lifetime access', 'All future features', 'Early access to new tools', 'Community badge'],
    cta: 'Get Lifetime Access',
    ctaStyle: 'w-full py-3 rounded-xl font-bold text-sm border border-amber-500/50 text-amber-300 hover:bg-amber-500/10 transition-all',
    popular: false,
  },
]

const TESTIMONIALS = [
  { name: 'Rahul S.',     role: 'Now at Amazon (ML Intern)', avatar: 'RS', color: 'bg-amber-500', quote: 'My interview probability went from 35% to 72% in 3 weeks following the roadmap. Got my first internship call the next day after optimizing my resume.' },
  { name: 'Ananya K.',    role: 'Frontend Dev at Startup',   avatar: 'AK', color: 'bg-yellow-600', quote: 'The ATS checker showed me my resume was getting filtered out before any human even saw it. Fixed it and got 4 calls in one week.' },
  { name: 'Siddharth M.', role: 'Data Analyst Intern',       avatar: 'SM', color: 'bg-amber-500',   quote: 'CareerLens told me I was a 28% match. Instead of being discouraged, I followed the plan. 6 weeks later I was at 61% and got shortlisted at 3 companies.' },
]

const PROBLEMS = [
  '❌  Sending 50+ applications with zero callbacks',
  '❌  Not knowing what skills are actually missing',
  '❌  Resume filtered before any human reads it',
  '❌  Wasting time on mock interviews for wrong roles',
  "❌  Generic advice that doesn't apply to you",
]
const SOLUTIONS = [
  '✅  Know your exact interview probability before applying',
  '✅  See specifically which skills to learn for your target role',
  '✅  ATS score tells you if your resume will be seen',
  '✅  Practice questions tailored to your role and level',
  '✅  Personalized roadmap based on your actual profile',
]

// ------------------------------------------------------------
// Stat counter
// ------------------------------------------------------------
function Stat({ value, label }) {
  return (
    <div className="text-center">
      <p className="text-4xl font-black text-white">{value}</p>
      <p className="text-[#d6d3d1] text-sm mt-1">{label}</p>
    </div>
  )
}

// ------------------------------------------------------------
// Main
// ------------------------------------------------------------
export default function Landing() {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="min-h-screen text-white relative">
      <Particles />

      {/* NAVBAR */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[rgba(10,10,10,0.9)] backdrop-blur-md border-b border-[rgba(217,119,6,0.12)]' : ''}`}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/90 shadow-[0_0_20px_rgba(245,158,11,0.35)] flex items-center justify-center">
              <Zap size={16} className="text-[#0a0a0a]" />
            </div>
            <span className="text-xl font-black gradient-text">CareerLens</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((l) => (
              <a
                key={l}
                href={`#${l.toLowerCase().replace(/ /g, '-')}`}
                className="text-sm text-[#d6d3d1] hover:text-white transition-colors"
              >
                {l}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm text-[#d6d3d1] hover:text-white transition-colors px-4 py-2">Login</Link>
            <Link to="/register" className="btn-primary text-sm px-5 py-2.5 flex items-center gap-1.5">
              Get Started <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <motion.section
        className="pt-32 pb-24 px-6 relative overflow-hidden"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
      >
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full opacity-15 blur-[60px]"
          style={{ background: 'radial-gradient(circle, rgba(245,158,11,0.5) 0%, transparent 70%)' }}
        />

        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-10 items-center relative z-10">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}
            className="space-y-6">
            <div className="badge badge-gold">
              <Zap size={13} /> AI-Powered Career Intelligence
            </div>
            <h1 className="text-[42px] md:text-[72px] font-black leading-[1.1]">
              Stop Applying Blindly.
              <motion.span
                className="block gradient-text"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3, duration: 0.6 }}
              >
                Know Your Chances.
              </motion.span>
            </h1>
            <p className="text-lg md:text-xl text-[#d6d3d1] max-w-xl leading-relaxed">
              CareerLens tells you your exact interview probability for any role,
              then gives you a specific action plan to improve it.
            </p>
            <div className="flex items-center gap-4 flex-wrap pt-2">
              <Link to="/register" className="btn-primary text-base px-8 py-4 flex items-center gap-2 font-bold">
                Analyze My Resume Free <ArrowRight size={17} />
              </Link>
              <a href="#how-it-works" className="btn-ghost text-sm px-6 py-3 flex items-center gap-2">
                See how it works <ChevronDown size={14} />
              </a>
            </div>
            <p className="text-xs text-[#44403c]">No credit card needed · Free plan available · 2,400+ resumes analyzed</p>
          </motion.div>

          {/* Mock score card */}
          <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.3 }}
            className="relative">
            <div
              className="glass-glow rounded-3xl p-6 border border-white/10 text-left space-y-4"
              style={{ animation: 'border-glow 3s ease-in-out infinite' }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[#d6d3d1] text-sm">Interview Probability</p>
                  <p className="text-white text-sm font-medium">ML Engineer @ Google</p>
                </div>
                <div className="text-right">
                  <p className="text-4xl font-black text-amber-400">62%</p>
                  <p className="text-xs text-[#78716c]">Competitive</p>
                </div>
              </div>
              {[{ label: 'Skill Match', val: 74, color: 'bg-amber-500' }, { label: 'ATS Score', val: 58, color: 'bg-amber-600' }, { label: 'Portfolio', val: 55, color: 'bg-amber-700' }].map((s, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-[#d6d3d1]">{s.label}</span>
                    <span className="text-white font-semibold">{s.val}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full ${s.color} rounded-full`}
                      initial={{ width: 0 }}
                      animate={{ width: `${s.val}%` }}
                      transition={{ delay: 1 + i * 0.2, duration: 0.8 }}
                    />
                  </div>
                </div>
              ))}
              <div className="pt-2 border-t border-white/5">
                <p className="text-xs text-red-400 font-semibold">Missing: Docker · Redis · System Design</p>
              </div>
            </div>
            <div className="absolute -top-3 -right-3 bg-green-500 text-white text-xs font-bold px-3 py-1.5 rounded-full">
              Live Preview
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* STATS */}
      <motion.section
        className="py-16 px-6 border-y border-white/5"
        style={{ background: 'rgba(255,255,255,0.02)' }}
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          <Stat value="2,400+" label="Resumes Analyzed" />
          <Stat value="580+" label="Interview Calls Reported" />
          <Stat value="+31%" label="Avg Score Improvement" />
          <Stat value="4.8★" label="User Rating" />
        </div>
      </motion.section>

      {/* PROBLEM / SOLUTION */}
      <motion.section
        className="py-24 px-6"
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black text-white">The Job Search is Broken</h2>
            <p className="text-[#d6d3d1] mt-3 text-lg">Most candidates fail not because they lack skills — but because they apply the wrong way.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="glass-glow p-6 rounded-2xl border border-red-500/10 space-y-3">
              <h3 className="text-lg font-bold text-white mb-4">Without CareerLens</h3>
              {PROBLEMS.map((p, i) => <p key={i} className="text-sm text-[#d6d3d1]">{p}</p>)}
            </div>
            <div className="glass-glow p-6 rounded-2xl border border-green-500/20 space-y-3">
              <h3 className="text-lg font-bold text-white mb-4">With CareerLens</h3>
              {SOLUTIONS.map((s, i) => <p key={i} className="text-sm text-[#d6d3d1]">{s}</p>)}
            </div>
          </div>
        </div>
      </motion.section>

      {/* FEATURES */}
      <motion.section
        id="features"
        className="py-24 px-6"
        style={{ background: 'rgba(255,255,255,0.01)' }}
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black text-white">Everything You Need to Get Hired</h2>
            <p className="text-[#d6d3d1] mt-3 text-lg">8 tools built for one goal — getting you interviews.</p>
          </div>
          <div className="relative">
            <svg className="absolute left-0 right-0 top-1/2 -translate-y-1/2 hidden lg:block" height="120">
              <defs>
                <linearGradient id="feature-line" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="rgba(245,158,11,0)" />
                  <stop offset="50%" stopColor="rgba(245,158,11,0.35)" />
                  <stop offset="100%" stopColor="rgba(180,83,9,0)" />
                </linearGradient>
              </defs>
              <line x1="0" y1="60" x2="100%" y2="60" stroke="url(#feature-line)" strokeWidth="2" />
            </svg>
            <motion.div
              className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 relative"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              {FEATURES.map((f, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.06 }}
                  className={`glass-glow p-5 rounded-2xl border ${f.bg} hover:scale-[1.02] transition-transform`}
                >
                  <div className="relative w-fit mb-3">
                    <span className={`absolute -inset-2 rounded-full ${f.glow} blur-[10px] opacity-60`} />
                    <f.icon size={22} className={`${f.color} relative`} />
                  </div>
                  <h3 className="font-bold text-white text-sm mb-1">{f.title}</h3>
                  <p className="text-[#d6d3d1] text-xs leading-relaxed">{f.desc}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* HOW IT WORKS */}
      <motion.section
        id="how-it-works"
        className="py-24 px-6"
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-4xl mx-auto relative">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black text-white">How It Works</h2>
            <p className="text-[#d6d3d1] mt-3">From upload to action plan in under 2 minutes.</p>
          </div>

          <motion.svg
            className="absolute left-0 right-0 top-20 hidden md:block"
            height="120"
            viewBox="0 0 1000 120"
            initial={{ pathLength: 0 }}
            whileInView={{ pathLength: 1 }}
            viewport={{ once: true }}
          >
            <motion.path
              d="M20 60 C 200 10, 400 10, 500 60 C 600 110, 800 110, 980 60"
              stroke="rgba(245,158,11,0.4)"
              strokeWidth="2"
              strokeDasharray="6 6"
              fill="none"
            />
          </motion.svg>

          <div className="grid md:grid-cols-4 gap-6 relative">
            {STEPS.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="text-center space-y-3"
              >
                <div className="relative mx-auto w-16 h-16">
                  <div className="w-16 h-16 rounded-full bg-[#151924] border border-red-500/20 flex items-center justify-center shadow-[0_0_20px_rgba(239,68,68,0.16)]">
                    <step.icon size={22} className="text-[#FF7070]" />
                  </div>
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-[#151924] border border-red-500/25 text-[#FF7070] text-xs font-bold flex items-center justify-center shadow-[0_0_12px_rgba(239,68,68,0.18)]">
                    {i + 1}
                  </span>
                </div>
                <h3 className="font-bold text-white text-sm">{step.title}</h3>
                <p className="text-[#78716c] text-xs">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* TESTIMONIALS */}
      <motion.section
        id="success-stories"
        className="py-24 px-6"
        style={{ background: 'rgba(255,255,255,0.01)' }}
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black text-white">Real Results</h2>
            <p className="text-[#d6d3d1] mt-3">Students and graduates who got interviews using CareerLens.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-glow p-6 rounded-2xl border border-white/5 space-y-4 relative overflow-hidden"
              >
                <div className="absolute inset-0 shimmer opacity-20 pointer-events-none" />
                <div className="flex gap-0.5">
                  {[...Array(5)].map((_, j) => (
                    <motion.span
                      key={j}
                      initial={{ opacity: 0, scale: 0.5 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.1 + j * 0.06 }}
                    >
                      <Star size={13} className="text-yellow-400 fill-yellow-400" />
                    </motion.span>
                  ))}
                </div>
                <p className="text-amber-200 text-sm leading-relaxed">"{t.quote}"</p>
                <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                  <div className={`w-9 h-9 rounded-xl ${t.color} flex items-center justify-center text-xs font-bold text-[#0a0a0a]`}>
                    {t.avatar}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{t.name}</p>
                    <p className="text-xs text-[#d6d3d1]">{t.role}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* PRICING */}
      <motion.section
        id="pricing"
        className="py-24 px-6"
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black text-white">Simple Pricing</h2>
            <p className="text-[#d6d3d1] mt-3">Start free. Upgrade when you're ready.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {PRICING.map((plan, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`glass-glow p-6 rounded-2xl border ${plan.color} relative space-y-5 ${plan.popular ? 'ring-2 ring-amber-500/50' : ''}`}
                style={plan.popular ? { animation: 'border-glow 3s ease-in-out infinite' } : undefined}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber-500 text-[#0a0a0a] text-xs font-bold px-4 py-1 rounded-full animate-pulse">
                    Most Popular
                  </div>
                )}
                <div>
                  <p className="text-[#d6d3d1] text-sm font-medium">{plan.name}</p>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-4xl font-black gradient-text">{plan.price}</span>
                    <span className="text-[#78716c] text-sm">{plan.period}</span>
                  </div>
                </div>
                <ul className="space-y-2">
                  {plan.features.map((f, j) => (
                    <li key={j} className="flex items-center gap-2 text-sm text-amber-200">
                      <CheckCircle size={14} className="text-amber-300 shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
                <Link to="/register" className={`${plan.ctaStyle} block text-center py-3 rounded-xl font-bold text-sm`}>
                  {plan.cta}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* CTA */}
      <motion.section
        className="py-24 px-6 text-center"
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-2xl mx-auto space-y-6 glass-glow p-10 rounded-3xl">
          <div className="w-16 h-16 rounded-2xl bg-amber-500 flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(245,158,11,0.4)]">
            <Zap size={28} className="text-[#0a0a0a]" />
          </div>
          <h2 className="text-4xl font-black text-white">Your next interview is closer than you think.</h2>
          <p className="text-[#d6d3d1] text-lg">Find out where you stand today. It takes 2 minutes.</p>
          <Link to="/register" className="btn-primary inline-flex items-center gap-2 px-10 py-4 text-base font-bold">
            Analyze My Resume — It's Free <ArrowRight size={17} />
          </Link>
        </div>
      </motion.section>

      {/* FOOTER */}
      <footer className="border-t border-white/5 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-amber-500 flex items-center justify-center">
              <Zap size={13} className="text-[#0a0a0a]" />
            </div>
            <span className="text-white font-bold">CareerLens</span>
          </div>
          <p className="text-[#44403c] text-sm">© 2025 CareerLens. Built to get you hired.</p>
          <div className="flex gap-6 text-sm text-[#78716c]">
            <Link to="/login" className="hover:text-white transition-colors">Login</Link>
            <Link to="/register" className="hover:text-white transition-colors">Sign Up</Link>
          </div>
        </div>
      </footer>
    </div>
    </motion.div>
  )
}








