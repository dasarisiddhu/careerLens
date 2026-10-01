import React, { useState, useEffect, lazy, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import {
  Zap,
  Target,
  FileText,
  Github,
  TrendingUp,
  CheckCircle,
  Star,
  ArrowRight,
  Users,
  BarChart3,
  Brain,
  ShieldCheck,
  Play,
  X,
  Compass,
  Sparkles,
} from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { NovaStaticFallback, NovaErrorBoundary } from '../components/companion/NovaFallback'

// Lazy load 3D Nova for the hero centerpiece
const Nova3D = lazy(() => import('../components/companion/Nova'))

const NAV_LINKS = [
  { label: 'Features', href: '#features' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'Success Stories', href: '#testimonials' },
]

const STAT_PILLS = [
  {
    title: 'Resume Analysis',
    value: '98/100',
    icon: ShieldCheck,
    color: 'from-amber-500/20 to-primary/20 border-primary/40 text-primary-light',
    badgeBg: 'bg-primary/20 text-primary-light',
  },
  {
    title: 'Skill Gap',
    value: '3 areas',
    icon: Target,
    color: 'from-orange-500/20 to-amber-500/20 border-accent/40 text-accent-light',
    badgeBg: 'bg-accent/20 text-accent-light',
  },
  {
    title: 'Job Match',
    value: '92%',
    icon: Sparkles,
    color: 'from-primary/20 to-orange-400/20 border-primary-light/40 text-amber-300',
    badgeBg: 'bg-amber-400/20 text-amber-300',
  },
]

const FEATURES = [
  {
    icon: FileText,
    title: 'AI Resume Analysis',
    desc: 'Brutally honest scoring and line-by-line improvements instead of vague generalities.',
  },
  {
    icon: Target,
    title: 'Interview Probability',
    desc: 'Know your odds before you apply so you can invest effort where it actually pays off.',
  },
  {
    icon: BarChart3,
    title: 'ATS Scanner & Checker',
    desc: 'Catch hidden formatting and keyword gaps that cause resumes to get silently rejected.',
  },
  {
    icon: Zap,
    title: 'Smart Resume Optimizer',
    desc: 'Rewrite bullet points tailored to target job descriptions with quantified impact.',
  },
  {
    icon: Brain,
    title: 'AI Mock Interviews',
    desc: 'Practice interactive role-specific technical and behavioral interviews anytime.',
  },
  {
    icon: Github,
    title: 'GitHub & Portfolio Insights',
    desc: 'Evaluate real public projects, commit quality, and codebase structure automatically.',
  },
  {
    icon: TrendingUp,
    title: 'Career Roadmap Engine',
    desc: 'Bridge missing skills into an actionable month-by-month sprint plan.',
  },
  {
    icon: Users,
    title: 'Peer Community',
    desc: 'Connect with driven engineers, compare milestone scores, and share interview experiences.',
  },
]

const STEPS = [
  {
    step: '01',
    title: 'Upload your resume',
    desc: 'Drop in your PDF resume for instant ATS breakdown and structural parsing.',
    icon: FileText,
  },
  {
    step: '02',
    title: 'Connect GitHub & target role',
    desc: 'CareerLens evaluates what you have actually built, not just what you claim.',
    icon: Github,
  },
  {
    step: '03',
    title: 'See your interview probability',
    desc: 'Get a blunt, data-backed percentage score before submitting your application.',
    icon: Target,
  },
  {
    step: '04',
    title: 'Follow the guided roadmap',
    desc: 'Use the optimizer, skill roadmaps, and mock interview drills to bridge every gap.',
    icon: TrendingUp,
  },
]

const PRICING = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    features: [
      'Resume Analysis (3/month)',
      'Basic ATS Score',
      'Interview Probability (3 checks)',
      'Honest Career Coach (20 messages)',
      'Community Feed Access',
    ],
    cta: 'Get Started Free',
    variant: 'ghost',
    popular: false,
  },
  {
    name: 'Premium',
    price: '$5.00',
    period: '/month',
    features: [
      'Unlimited Resume Analysis',
      'Unlimited Interview Probability',
      'Full ATS Keyword Scanner',
      'Interactive Mock Interviews',
      'Portfolio & Cover Letter Gen',
      'Job Match Engine',
      'Priority AI Mentor Response',
    ],
    cta: 'Upgrade to Premium',
    variant: 'glow',
    popular: true,
  },
]

const TESTIMONIALS = [
  {
    name: 'Rahul S.',
    role: 'Now at Amazon (ML Intern)',
    avatar: 'RS',
    quote:
      'My interview probability moved from 35% to 72% in three weeks. Nova and CareerLens showed me the exact gaps in my GitHub repos.',
  },
  {
    name: 'Ananya K.',
    role: 'Frontend Dev at Unicorn Startup',
    avatar: 'AK',
    quote:
      'The ATS checker showed me why my resume was being silently filtered out. I revised my bullets and received recruiter calls within a week.',
  },
  {
    name: 'Siddharth M.',
    role: 'Full Stack Engineer',
    avatar: 'SM',
    quote:
      'Seeing an honest, unvarnished score gave me a real action plan. Practiced the mock interview questions and landed my target offer.',
  },
]

export default function Landing() {
  const [demoModalOpen, setDemoModalOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <div className="relative min-h-screen bg-[#0B0A10] text-[#F5F5F7] overflow-x-hidden selection:bg-primary/30 selection:text-white">
      {/* Background glow ambiance */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-40"
        style={{
          backgroundImage:
            'radial-gradient(circle at 50% 0%, rgba(255,107,0,0.18) 0%, transparent 60%), radial-gradient(circle at 85% 35%, rgba(255,167,38,0.08) 0%, transparent 50%)',
        }}
      />

      {/* ============================================================
          TOP NAVIGATION BAR
      ============================================================ */}
      <header className="sticky top-0 z-50 w-full border-b border-white/[0.06] bg-[#0B0A10]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-6 lg:px-12">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-primary to-accent shadow-[0_0_20px_rgba(255,107,0,0.45)] group-hover:scale-105 transition-transform duration-300">
              <Zap size={20} className="text-white fill-white" />
            </div>
            <span className="font-display text-2xl font-bold tracking-tight text-white">
              Career<span className="gradient-text">Lens</span>
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm font-medium text-slate-300 transition-colors hover:text-white hover:text-primary"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" size="md" className="rounded-full px-5">
                Login
              </Button>
            </Link>
            <Link to="/signup">
              <Button variant="primary" size="md" className="rounded-full px-6 shadow-glow">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ============================================================
          HERO SECTION (Image 1 Option 1 + Nova Mascot Centerpiece)
      ============================================================ */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pt-12 pb-24 lg:px-12 lg:pt-16">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
          {/* Left Column: Benefit-driven headline & CTA */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-6 flex flex-col items-start"
          >
            {/* Pill Tag */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 backdrop-blur-md">
              <Sparkles size={14} className="text-primary" />
              <span className="text-xs font-semibold uppercase tracking-wider text-primary-light font-display">
                AI Powered Career Guidance
              </span>
            </div>

            {/* Headline */}
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.08] text-white mb-6">
              Turn Your <br />
              Resume into <br />
              <span className="gradient-text">Real Opportunities</span>
            </h1>

            {/* Subtitle */}
            <p className="max-w-xl text-base sm:text-lg text-slate-300 leading-relaxed mb-8">
              Get AI-powered feedback, personalized roadmaps, and job-ready guidance — all in one
              place.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 mb-10">
              <Link to="/signup">
                <Button
                  variant="primary"
                  size="lg"
                  className="rounded-full px-8 py-4 text-base font-bold shadow-[0_0_30px_rgba(255,107,0,0.5)] hover:shadow-[0_0_45px_rgba(255,107,0,0.7)] group"
                >
                  Analyze My Resume
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>

              <Button
                variant="ghost"
                size="lg"
                onClick={() => setDemoModalOpen(true)}
                className="rounded-full px-7 py-4 text-base font-medium border border-white/10 hover:border-primary/40 bg-white/[0.03]"
              >
                <Play size={16} className="text-primary fill-primary mr-1" />
                Watch Demo
              </Button>
            </div>

            {/* Social Proof */}
            <div className="flex items-center gap-4 pt-2 border-t border-white/[0.08] w-full max-w-md">
              <div className="flex -space-x-2 overflow-hidden">
                {['RS', 'AK', 'SM', 'DP', 'NK'].map((initials, i) => (
                  <div
                    key={i}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border-2 border-[#0B0A10] bg-gradient-to-tr from-surface-elevated to-primary/40 text-xs font-bold text-white shadow"
                  >
                    {initials}
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 font-medium">
                Trusted by <span className="font-bold text-white">10,000+</span> students & engineers
              </p>
            </div>
          </motion.div>

          {/* Right Column: Nova 3D Centerpiece + Floating Stat Pills */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-6 relative flex items-center justify-center"
          >
            {/* Center Background Orbit Glow */}
            <div
              className="absolute h-[380px] w-[380px] sm:h-[460px] sm:w-[460px] rounded-full border border-primary/20 bg-gradient-to-b from-primary/10 via-transparent to-transparent pointer-events-none"
              style={{
                boxShadow: '0 0 80px rgba(255,107,0,0.18), inset 0 0 60px rgba(255,107,0,0.08)',
              }}
            />

            {/* 3D Nova Hero Character */}
            <div className="relative z-10 w-full flex items-center justify-center">
              <NovaErrorBoundary size="hero" expression="idle">
                <Suspense fallback={<NovaStaticFallback size="hero" expression="idle" />}>
                  <Nova3D size="hero" expression="idle" />
                </Suspense>
              </NovaErrorBoundary>
            </div>

            {/* Floating Stat Pills (Stacked on the right, matching Image 1 Option 1) */}
            <div className="absolute right-0 sm:right-4 top-1/2 -translate-y-1/2 z-20 flex flex-col gap-3 pointer-events-auto">
              {STAT_PILLS.map((pill, idx) => {
                const Icon = pill.icon
                return (
                  <motion.div
                    key={pill.title}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + idx * 0.15, duration: 0.5 }}
                    whileHover={{ scale: 1.04, x: -4 }}
                    className="flex items-center gap-3 rounded-2xl border border-white/10 bg-[#13121C]/85 px-4 py-3 shadow-[0_10px_30px_rgba(0,0,0,0.65),0_0_20px_rgba(255,107,0,0.12)] backdrop-blur-xl"
                  >
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-xl border ${pill.color} bg-gradient-to-br shadow-inner`}
                    >
                      <Icon size={18} />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-display">
                        {pill.title}
                      </p>
                      <p className="text-base font-bold text-white tracking-tight">{pill.value}</p>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ============================================================
          FEATURES GRID (Using Phase 0 Card Primitives)
      ============================================================ */}
      <section id="features" className="relative z-10 border-t border-white/[0.06] bg-[#0E0D14]/60 py-24 px-6 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <Badge variant="default" className="mb-4">
              Comprehensive Toolkit
            </Badge>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
              Everything You Need to Get Hired
            </h2>
            <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
              Designed from real industry feedback to eliminate blind spots in your resume, GitHub,
              and interview prep.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feature, i) => {
              const Icon = feature.icon
              return (
                <Card
                  key={feature.title}
                  variant="glass"
                  className="group hover:-translate-y-1 transition-all duration-300"
                >
                  <CardHeader className="p-6">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 text-primary shadow-[0_0_20px_rgba(255,107,0,0.15)] group-hover:scale-110 group-hover:bg-primary group-hover:text-white transition-all duration-300">
                      <Icon size={22} />
                    </div>
                    <CardTitle className="text-lg mb-2 group-hover:text-primary-light transition-colors">
                      {feature.title}
                    </CardTitle>
                    <CardDescription className="text-xs leading-relaxed text-slate-400">
                      {feature.desc}
                    </CardDescription>
                  </CardHeader>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* ============================================================
          HOW IT WORKS
      ============================================================ */}
      <section id="how-it-works" className="relative z-10 py-24 px-6 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <Badge variant="accent" className="mb-4">
              Step-by-Step Flow
            </Badge>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
              How CareerLens Works
            </h2>
            <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
              From an unoptimized resume to confident interview readiness in 4 simple steps.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {STEPS.map((s, index) => {
              const Icon = s.icon
              return (
                <div
                  key={s.step}
                  className="relative rounded-2xl border border-white/[0.08] bg-surface-card/60 p-6 backdrop-blur-xl"
                >
                  <div className="flex items-center justify-between mb-6">
                    <span className="font-display text-3xl font-extrabold text-primary/40">
                      {s.step}
                    </span>
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.05] border border-white/10 text-primary">
                      <Icon size={18} />
                    </div>
                  </div>
                  <h3 className="font-display text-base font-bold text-white mb-2">{s.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ============================================================
          PRICING SECTION (Using Phase 0 Card Primitives)
      ============================================================ */}
      <section id="pricing" className="relative z-10 border-t border-white/[0.06] bg-[#0E0D14]/70 py-24 px-6 lg:px-12">
        <div className="mx-auto max-w-5xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <Badge variant="default" className="mb-4">
              Simple Pricing
            </Badge>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
              Invest in Your Career
            </h2>
            <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
              Start free with no credit card required. Upgrade when you are ready to accelerate.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
            {PRICING.map((plan) => (
              <Card
                key={plan.name}
                variant={plan.popular ? 'elevated-glow' : 'glass'}
                className="relative flex flex-col justify-between p-8"
              >
                {plan.popular && (
                  <div className="absolute top-0 right-0 rounded-bl-xl bg-gradient-to-l from-primary to-accent px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-white shadow-md">
                    Most Popular
                  </div>
                )}
                <div>
                  <h3 className="font-display text-2xl font-bold text-white mb-2">{plan.name}</h3>
                  <div className="flex items-baseline gap-2 mb-6">
                    <span className="font-display text-4xl font-extrabold text-white">{plan.price}</span>
                    <span className="text-sm text-slate-400 font-medium">{plan.period}</span>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-center gap-2.5 text-xs text-slate-300">
                        <CheckCircle size={15} className="text-primary shrink-0" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <Link to={plan.popular ? '/dashboard/upgrade' : '/signup'} className="w-full">
                  <Button
                    variant={plan.variant}
                    size="lg"
                    className="w-full rounded-xl font-bold"
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================
          TESTIMONIALS
      ============================================================ */}
      <section id="testimonials" className="relative z-10 py-24 px-6 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <Badge variant="accent" className="mb-4">
              Student Results
            </Badge>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
              Real Offers. Real Feedback.
            </h2>
            <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
              See how developers turned low initial match scores into top-tier tech offers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t) => (
              <Card key={t.name} variant="glass" className="p-6 flex flex-col justify-between">
                <div className="flex items-center gap-1 text-primary mb-4">
                  {[...Array(5)].map((_, idx) => (
                    <Star key={idx} size={14} className="fill-primary" />
                  ))}
                </div>
                <p className="text-xs sm:text-sm text-slate-200 leading-relaxed mb-6 italic">
                  "{t.quote}"
                </p>
                <div className="flex items-center gap-3 pt-4 border-t border-white/[0.08]">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-tr from-primary to-accent font-bold text-xs text-white">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="font-display text-sm font-bold text-white">{t.name}</p>
                    <p className="text-[11px] text-slate-400">{t.role}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================
          BOTTOM CTA BANNER
      ============================================================ */}
      <section className="relative z-10 py-20 px-6 lg:px-12">
        <div className="mx-auto max-w-5xl rounded-3xl border border-primary/30 bg-gradient-to-b from-[#181724] to-[#0B0A10] p-10 sm:p-14 text-center shadow-[0_20px_60px_rgba(0,0,0,0.8),0_0_40px_rgba(255,107,0,0.18)]">
          <Badge variant="default" className="mb-4">
            Instant Access
          </Badge>
          <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
            Stop Guessing. <span className="gradient-text">Start Getting Interviews.</span>
          </h2>
          <p className="max-w-xl mx-auto text-slate-300 text-sm sm:text-base leading-relaxed mb-8">
            Upload your resume now to see your match score, fix hidden ATS filters, and follow a
            concrete improvement plan.
          </p>
          <Link to="/signup">
            <Button
              variant="glow"
              size="lg"
              className="rounded-full px-10 py-4 text-base font-bold shadow-[0_0_35px_rgba(255,107,0,0.6)]"
            >
              Analyze Your Resume Now →
            </Button>
          </Link>
        </div>
      </section>

      {/* ============================================================
          FOOTER
      ============================================================ */}
      <footer className="relative z-10 border-t border-white/[0.06] bg-[#07060A] py-12 px-6 lg:px-12 text-slate-500 text-xs">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-primary fill-primary" />
            <span className="font-display text-sm font-bold text-white">CareerLens</span>
            <span>— Dark 3D AI Career Guidance</span>
          </div>
          <p>© {new Date().getFullYear()} CareerLens. All rights reserved.</p>
        </div>
      </footer>

      {/* ============================================================
          DEMO MODAL
      ============================================================ */}
      <AnimatePresence>
        {demoModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.92 }}
              className="relative w-full max-w-2xl rounded-2xl border border-primary/30 bg-[#13121C] p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
                <h3 className="font-display text-lg font-bold text-white">CareerLens Walkthrough Demo</h3>
                <button
                  onClick={() => setDemoModalOpen(false)}
                  className="rounded-lg p-1.5 text-slate-400 hover:text-white hover:bg-white/10"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="aspect-video w-full rounded-xl bg-black/60 border border-white/[0.08] flex flex-col items-center justify-center p-6 text-center">
                <Play size={44} className="text-primary fill-primary mb-3" />
                <p className="text-sm font-semibold text-white mb-1">CareerLens Interactive Demo</p>
                <p className="text-xs text-slate-400 max-w-md">
                  Experience full end-to-end ATS score breakdown, interview probability prediction,
                  and resume bullet rewrites directly inside the dashboard.
                </p>
                <Link to="/signup" className="mt-5">
                  <Button variant="primary" size="sm" className="rounded-full">
                    Try Dashboard Free
                  </Button>
                </Link>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
