import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
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
  ChevronDown,
} from 'lucide-react'
import { staggerContainer } from '../utils/animations'

const NAV_LINKS = ['Features', 'How It Works', 'Pricing', 'Success Stories']

const FEATURES = [
  { icon: FileText, title: 'AI Resume Analysis', desc: 'Brutally honest scoring and specific improvements instead of generic advice.' },
  { icon: Target, title: 'Interview Probability', desc: 'See your odds before you apply so you can focus effort where it matters.' },
  { icon: BarChart3, title: 'ATS Checker', desc: 'Catch the wording and keyword issues that keep resumes invisible.' },
  { icon: Zap, title: 'Resume Optimizer', desc: 'Rewrite bullets for a real job description and export a cleaner version fast.' },
  { icon: Brain, title: 'Mock Interviews', desc: 'Practice with AI questions tailored to your role and current level.' },
  { icon: Github, title: 'GitHub Portfolio Analysis', desc: 'Get feedback that reflects your actual projects, not just your resume.' },
  { icon: TrendingUp, title: 'Career Roadmap', desc: 'Turn missing skills into a concrete plan with realistic next steps.' },
  { icon: Users, title: 'Community Feed', desc: 'Share progress, find collaborators, and discover career opportunities.' },
]

const STEPS = [
  { step: '01', title: 'Upload your resume', desc: 'Start with your current resume in a few seconds.', icon: FileText },
  { step: '02', title: 'Add your GitHub and target role', desc: 'CareerLens reads what you have actually built.', icon: Github },
  { step: '03', title: 'See your interview probability', desc: 'Get a blunt percentage, not vague encouragement.', icon: Target },
  { step: '04', title: 'Follow the action plan', desc: 'Use the roadmap, optimizer, and mock interview loop to improve.', icon: TrendingUp },
]

const PRICING = [
  {
    name: 'Free',
    price: '₹0',
    period: 'forever',
    features: ['Resume Analysis (3/month)', 'Basic ATS Score', 'Interview Probability (1/month)', 'Honest Career Coach (10 messages)', 'Community Feed'],
    cta: 'Get Started Free',
    ctaStyle: 'btn-ghost w-full',
    popular: false,
  },
  {
    name: 'Pro',
    price: '₹299',
    period: '/month',
    features: ['Unlimited Resume Analysis', 'Resume Optimizer', 'Unlimited Interview Probability', 'Mock Interviews (unlimited)', 'Job Match Engine', 'Portfolio Generator', 'Progress Tracker', 'Priority AI responses'],
    cta: 'Start Pro - ₹299/mo',
    ctaStyle: 'btn-primary w-full',
    popular: true,
  },
  {
    name: 'Lifetime',
    price: '₹1,999',
    period: 'one-time',
    features: ['Everything in Pro', 'Lifetime access', 'All future features', 'Early access to new tools', 'Community badge'],
    cta: 'Get Lifetime Access',
    ctaStyle: 'btn-ghost w-full',
    popular: false,
  },
]

const TESTIMONIALS = [
  { name: 'Rahul S.', role: 'Now at Amazon (ML Intern)', avatar: 'RS', color: 'linear-gradient(135deg,#FF3B3B,#8B0000)', quote: 'My interview probability moved from 35% to 72% in three weeks. I stopped guessing and finally knew what to fix.' },
  { name: 'Ananya K.', role: 'Frontend Dev at Startup', avatar: 'AK', color: 'linear-gradient(135deg,#FF8C42,#FF3B3B)', quote: 'The ATS checker showed me why my resume was being filtered out. I fixed those gaps and started getting calls immediately.' },
  { name: 'Siddharth M.', role: 'Data Analyst Intern', avatar: 'SM', color: 'linear-gradient(135deg,#1a1f2b,#ef4444)', quote: 'Seeing a low score was tough, but it gave me a real plan. Six weeks later, I was shortlisted at three companies.' },
]

const PROBLEMS = [
  'Sending 50+ applications with zero callbacks',
  'Not knowing which missing skills actually matter',
  'Resume filtered before any human reads it',
  'Wasting time preparing for the wrong roles',
  "Getting generic advice that doesn't apply to you",
]

const SOLUTIONS = [
  'Know your exact interview probability before applying',
  'See which skills to learn for the target role',
  'Use ATS scoring to improve visibility',
  'Practice role-specific interview questions',
  'Follow a roadmap tied to your real profile',
]

function Particles() {
  const [particles, setParticles] = useState([])

  useEffect(() => {
    const items = Array.from({ length: 20 }).map((_, index) => ({
      id: index,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.28 + 0.08,
      duration: Math.random() * 6 + 4,
      delay: Math.random() * 2,
      color: index % 2 === 0 ? 'rgba(255,59,59,0.28)' : 'rgba(200,30,30,0.2)',
    }))
    setParticles(items)
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
            boxShadow: `0 0 ${particle.size * 7}px ${particle.color}`,
            animation: `float ${particle.duration}s ease-in-out ${particle.delay}s infinite alternate`,
          }}
        />
      ))}
    </div>
  )
}

function Stat({ value, label }) {
  return (
    <div className="text-center">
      <p className="gradient-text text-4xl font-black">{value}</p>
      <p className="mt-2 text-sm text-[#8A8FA8]">{label}</p>
    </div>
  )
}

export default function Landing() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="relative min-h-screen overflow-x-hidden text-white"
    >
      <Particles />

      <nav
        className={`fixed left-0 right-0 top-0 z-50 transition-all duration-300 ${
          scrolled ? 'border-b border-white/5' : ''
        }`}
        style={scrolled ? { background: 'rgba(14,16,22,0.8)', backdropFilter: 'blur(20px)' } : undefined}
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div
              className="flex h-9 w-9 items-center justify-center rounded-xl"
              style={{
                background: 'linear-gradient(135deg,#FF3B3B,#CC1A1A)',
                boxShadow: '0 0 20px rgba(255,59,59,0.35)',
              }}
            >
              <Zap size={17} className="text-white" />
            </div>
            <span className="gradient-text text-xl font-black">CareerLens</span>
          </div>

          <div className="hidden items-center gap-8 md:flex">
            {NAV_LINKS.map((link) => (
              <a
                key={link}
                href={`#${link.toLowerCase().replace(/ /g, '-')}`}
                className="text-sm text-[#8A8FA8] transition hover:text-white"
              >
                {link}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Link to="/login" className="px-4 py-2 text-sm text-[#8A8FA8] transition hover:text-white">
              Login
            </Link>
            <Link to="/signup" className="btn-primary text-sm">
              Get Started
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </nav>

      <section className="relative overflow-hidden px-6 pb-24 pt-32">
        <div
          aria-hidden
          className="absolute left-1/2 top-0 h-[340px] w-[760px] -translate-x-1/2 rounded-full blur-[80px]"
          style={{ background: 'radial-gradient(circle, rgba(255,59,59,0.16) 0%, transparent 70%)' }}
        />

        <div className="relative z-[1] mx-auto grid max-w-6xl items-center gap-14 md:grid-cols-2">
          <div>
            <div className="badge badge-red mb-6">
              <Zap size={12} />
              AI-Powered Career Intelligence
            </div>
            <h1 className="mb-6 text-[46px] font-black leading-[1.02] text-white md:text-[72px]">
              Stop Applying Blindly.
              <span className="gradient-text block">Know Your Chances.</span>
            </h1>
            <p className="mb-8 max-w-xl text-lg leading-8 text-[#8A8FA8]">
              CareerLens tells you your interview probability for any role, then gives you the exact actions
              to improve it before you spend weeks guessing.
            </p>
            <div className="hero-cta flex flex-wrap items-center gap-4">
              <Link to="/signup" className="btn-primary px-8 py-4 text-base font-bold">
                Analyze My Resume Free
                <ArrowRight size={16} />
              </Link>
              <a href="#how-it-works" className="btn-ghost px-6 py-3 text-sm">
                See how it works
                <ChevronDown size={14} />
              </a>
            </div>
            <p className="mt-4 text-xs text-[#8A8FA8]/70">No credit card needed. Free plan available. 2,400+ resumes analyzed.</p>
          </div>

          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
            <div className="glass-glow rounded-[28px] p-6" style={{ animation: 'border-glow-red 3s infinite' }}>
              <div className="mb-5 flex items-start justify-between">
                <div>
                  <p className="text-sm text-[#8A8FA8]">Interview Probability</p>
                  <p className="mt-1 text-sm font-medium text-white">ML Engineer @ Google</p>
                </div>
                <div className="text-right">
                  <p className="text-5xl font-black text-[#FF3B3B]">62%</p>
                  <p className="text-xs text-[#8A8FA8]">Competitive</p>
                </div>
              </div>

              {[
                { label: 'Skill Match', val: 74 },
                { label: 'ATS Score', val: 58 },
                { label: 'Portfolio', val: 55 },
              ].map((item, index) => (
                <div key={item.label} className="mb-4 last:mb-0">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="text-[#8A8FA8]">{item.label}</span>
                    <span className="font-semibold text-white">{item.val}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${item.val}%` }}
                      transition={{ delay: 0.25 + index * 0.12, duration: 0.8 }}
                      className="h-full rounded-full bg-[#FF3B3B]"
                    />
                  </div>
                </div>
              ))}

              <div className="mt-5 border-t border-white/5 pt-4 text-xs font-semibold text-[#FF7070]">
                Missing: Docker, Redis, System Design
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="border-y border-[rgba(255,59,59,0.1)] bg-[rgba(255,59,59,0.04)] px-6 py-16">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 md:grid-cols-4">
          <Stat value="2,400+" label="Resumes Analyzed" />
          <Stat value="580+" label="Interview Calls Reported" />
          <Stat value="+31%" label="Avg Score Improvement" />
          <Stat value="4.8/5" label="User Rating" />
        </div>
      </section>

      <section className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <h2 className="text-4xl font-black text-white">The Job Search is Broken</h2>
            <p className="mt-3 text-lg text-[#8A8FA8]">Most candidates fail because they are navigating without signal.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="glass-glow rounded-3xl p-6">
              <h3 className="mb-4 text-lg font-bold text-white">Without CareerLens</h3>
              <div className="space-y-3">
                {PROBLEMS.map((problem) => (
                  <p key={problem} className="text-sm text-[#8A8FA8]">
                    {problem}
                  </p>
                ))}
              </div>
            </div>
            <div className="glass-glow rounded-3xl p-6">
              <h3 className="mb-4 text-lg font-bold text-white">With CareerLens</h3>
              <div className="space-y-3">
                {SOLUTIONS.map((solution) => (
                  <p key={solution} className="text-sm text-[#8A8FA8]">
                    {solution}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="bg-white/[0.01] px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="text-4xl font-black text-white">Everything You Need to Get Hired</h2>
            <p className="mt-3 text-lg text-[#8A8FA8]">Eight focused tools built for a single outcome: more interviews.</p>
          </div>

          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
          >
            {FEATURES.map((feature) => (
              <motion.div
                key={feature.title}
                whileHover={{ y: -3, scale: 1.01 }}
                className="glass-glow feature-card rounded-3xl p-5"
              >
                <div className="relative mb-4 w-fit">
                  <span className="absolute -inset-2 rounded-full bg-[rgba(255,59,59,0.18)] blur-[10px]" />
                  <div className="relative rounded-2xl border border-[rgba(255,59,59,0.2)] bg-[rgba(255,59,59,0.12)] p-3">
                    <feature.icon size={20} className="text-[#FF3B3B]" />
                  </div>
                </div>
                <h3 className="mb-2 text-sm font-bold text-white">{feature.title}</h3>
                <p className="text-xs leading-relaxed text-[#8A8FA8]">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      <section id="how-it-works" className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <h2 className="text-4xl font-black text-white">How It Works</h2>
            <p className="mt-3 text-[#8A8FA8]">From upload to action plan in under two minutes.</p>
          </div>

          <div className="grid gap-6 md:grid-cols-4">
            {STEPS.map((step, index) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                className="text-center"
              >
                <div className="relative mx-auto mb-4 h-16 w-16">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full border border-[rgba(255,59,59,0.25)] bg-[rgba(255,59,59,0.12)] shadow-[0_0_20px_rgba(255,59,59,0.2)]">
                    <step.icon size={22} className="text-[#FF3B3B]" />
                  </div>
                  <span className="absolute -right-1 -top-1 flex h-6 w-6 items-center justify-center rounded-full bg-[#11131A] text-xs font-bold text-[#FF3B3B] ring-1 ring-[rgba(255,59,59,0.25)]">
                    {step.step}
                  </span>
                </div>
                <h3 className="mb-2 text-sm font-bold text-white">{step.title}</h3>
                <p className="text-xs text-[#8A8FA8]">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="success-stories" className="bg-white/[0.01] px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <h2 className="text-4xl font-black text-white">Real Results</h2>
            <p className="mt-3 text-[#8A8FA8]">Students and graduates who turned career guesswork into momentum.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {TESTIMONIALS.map((testimonial, index) => (
              <motion.div
                key={testimonial.name}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                whileHover={{ y: -3 }}
                className="glass-glow rounded-3xl p-6"
              >
                <div className="mb-4 flex gap-1">
                  {Array.from({ length: 5 }).map((_, starIndex) => (
                    <Star key={starIndex} size={14} className="fill-[#FF3B3B] text-[#FF3B3B]" />
                  ))}
                </div>
                <p className="mb-5 text-sm leading-7 text-[#F5F5F7]">"{testimonial.quote}"</p>
                <div className="flex items-center gap-3 border-t border-white/5 pt-4">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-2xl text-xs font-bold text-white"
                    style={{ background: testimonial.color }}
                  >
                    {testimonial.avatar}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{testimonial.name}</p>
                    <p className="text-xs text-[#8A8FA8]">{testimonial.role}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <h2 className="text-4xl font-black text-white">Simple Pricing</h2>
            <p className="mt-3 text-[#8A8FA8]">Start free. Upgrade when you want the full loop.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {PRICING.map((plan) => (
              <motion.div
                key={plan.name}
                whileHover={{ y: -3, scale: 1.01 }}
                className="glass-glow relative rounded-3xl p-6"
                style={plan.popular ? { animation: 'border-glow-red 3s infinite' } : undefined}
              >
                {plan.popular && <div className="badge badge-red absolute -top-3 left-1/2 -translate-x-1/2">Most Popular</div>}
                <p className="text-sm font-medium text-[#8A8FA8]">{plan.name}</p>
                <div className="mt-2 flex items-end gap-1">
                  <span className="gradient-text text-4xl font-black">{plan.price}</span>
                  <span className="pb-1 text-sm text-[#8A8FA8]">{plan.period}</span>
                </div>
                <ul className="my-6 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm text-[#F5F5F7]">
                      <CheckCircle size={15} className="mt-0.5 shrink-0 text-[#FF7070]" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link to="/signup" className={`${plan.ctaStyle} block py-3 text-center text-sm font-bold`}>
                  {plan.cta}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 py-24 text-center">
        <div className="glass-glow mx-auto max-w-2xl rounded-[32px] p-10">
          <div
            className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl"
            style={{
              background: 'linear-gradient(135deg,#FF3B3B,#CC1A1A)',
              boxShadow: '0 0 20px rgba(255,59,59,0.35)',
            }}
          >
            <Zap size={28} className="text-white" />
          </div>
          <h2 className="mb-4 text-4xl font-black text-white">Your next interview is closer than you think.</h2>
          <p className="mb-8 text-lg text-[#8A8FA8]">Find out where you stand today. It only takes two minutes.</p>
          <Link to="/signup" className="btn-primary px-10 py-4 text-base font-bold">
            Analyze My Resume - It's Free
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/5 px-6 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 md:flex-row">
          <div className="flex items-center gap-3">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-xl"
              style={{ background: 'linear-gradient(135deg,#FF3B3B,#CC1A1A)' }}
            >
              <Zap size={14} className="text-white" />
            </div>
            <span className="font-bold text-white">CareerLens</span>
          </div>
          <p className="text-sm text-[#8A8FA8]">© 2025 CareerLens. Built to get you hired.</p>
          <div className="flex gap-6 text-sm text-[#8A8FA8]">
            <Link to="/login" className="transition hover:text-white">
              Login
            </Link>
            <Link to="/signup" className="transition hover:text-white">
              Sign Up
            </Link>
          </div>
        </div>
      </footer>
    </motion.div>
  )
}
