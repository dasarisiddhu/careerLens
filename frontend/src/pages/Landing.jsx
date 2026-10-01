import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  Play,
  Sparkles,
  Briefcase,
  CheckCircle2,
  XCircle,
  TrendingUp,
  FileText,
  Compass,
  Layers,
  ChevronRight,
  ShieldCheck,
  Send,
  Star,
  Users,
  Award,
  Zap,
} from 'lucide-react'
import { Navbar } from '../components/layout/Navbar'
import { Footer } from '../components/layout/Footer'
import { Button, Badge, GlassCard, ScoreRing, StatCard, Dialog } from '../components/ui'
import { Mascot } from '../mascot/Mascot'
import { useMascotState } from '../mascot/useMascotState'
import { MARKETING_CONFIG } from '../config/marketing'

export default function Landing() {
  const navigate = useNavigate()
  const [demoOpen, setDemoOpen] = useState(false)
  const [askInput, setAskInput] = useState('')
  const [companionReply, setCompanionReply] = useState(null)
  const [dashboardTab, setDashboardTab] = useState('overview')

  const {
    state: mascotState,
    setState: setMascotState,
    bubbleOpen,
    setBubbleOpen,
    mouseOffset,
    prefersReducedMotion,
  } = useMascotState({ initial: 'greeting', autoNudge: true, nudgeDelayMs: 6000 })

  const handleAskSubmit = (e) => {
    e.preventDefault()
    if (!askInput.trim()) return
    setCompanionReply(
      `"I've tailored a custom roadmap for ${askInput.trim()}! Upload your resume and I'll highlight the highest-impact improvements for you."`
    )
    setAskInput('')
  }

  return (
    <div className="min-h-screen bg-base overflow-x-hidden selection:bg-blue-500 selection:text-white">
      {/* Top Sticky Navigation */}
      <Navbar />

      {/* ============================================================ */}
      {/* HERO SECTION (Faithful reproduction of REF-1) */}
      {/* ============================================================ */}
      <section className="relative pt-6 pb-20 px-4 sm:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Headline, sub-copy, CTAs, Social Proof */}
          <div className="lg:col-span-6 space-y-6 sm:space-y-8 z-10 text-left">
            {/* Pill Badge */}
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Badge sparkle size="md" className="cursor-pointer hover:bg-blue-100/80 transition-colors">
                AI Powered Career Guidance →
              </Badge>
            </motion.div>

            {/* Two-Tone H1 */}
            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.05 }}
              className="text-4xl sm:text-5xl lg:text-[56px] font-extrabold text-[#0B0F19] tracking-tight leading-[1.08]"
            >
              Your Resume Today. <br />
              <span className="text-[#0B0F19]">A Better Tomorrow.</span>
            </motion.h1>

            {/* Sub-copy */}
            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="text-base sm:text-lg text-[#475569] leading-relaxed max-w-lg"
            >
              Get personalized feedback, skill-gap analysis and a clear roadmap to land internships and your dream job — all in one place.
            </motion.p>

            {/* CTA Row */}
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.15 }}
              className="flex flex-wrap items-center gap-3.5 pt-2"
            >
              <Button
                variant="primary"
                size="lg"
                trailingIcon={ArrowRight}
                onClick={() => navigate('/dashboard/optimizer')}
              >
                Analyze My Resume
              </Button>

              <Button
                variant="secondary"
                size="lg"
                icon={Play}
                onClick={() => setDemoOpen(true)}
              >
                Watch Demo
              </Button>
            </motion.div>

            {/* Social Proof Row */}
            {MARKETING_CONFIG.SHOW_SOCIAL_PROOF && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4, delay: 0.2 }}
                className="flex items-center gap-3.5 pt-2"
              >
                <div className="flex -space-x-2.5 overflow-hidden">
                  {MARKETING_CONFIG.TESTIMONIALS.map((t, i) => (
                    <img
                      key={t.name}
                      src={t.avatar}
                      alt=""
                      width={34}
                      height={34}
                      className="inline-block h-8 w-8 sm:h-9 sm:w-9 rounded-full ring-2 ring-white object-cover shadow-sm"
                    />
                  ))}
                  <div className="inline-flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-full bg-[#0B0F19] text-[10px] font-bold text-white ring-2 ring-white">
                    +10k
                  </div>
                </div>
                <p className="text-xs sm:text-sm font-semibold text-[#475569]">
                  Trusted by{' '}
                  <span className="text-[#0B0F19] font-bold">
                    {MARKETING_CONFIG.STUDENT_COUNT_LABEL}
                  </span>
                </p>
              </motion.div>
            )}
          </div>

          {/* Right Column: 3D Centerpiece Mascot + Floating 3D Stat Cards */}
          <div className="lg:col-span-6 relative flex items-center justify-center min-h-[460px] sm:min-h-[520px]">
            {/* Soft Ambient Radial Bloom (Clean Sky Blue, NO PURPLE) */}
            <div
              className="absolute -top-10 -right-10 w-96 h-96 rounded-full pointer-events-none blur-3xl opacity-70"
              style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.75) 0%, transparent 70%)' }}
            />

            {/* Centerpiece 3D Mascot */}
            <div className="relative z-10">
              <Mascot
                state={mascotState}
                bubbleOpen={bubbleOpen}
                onBubbleClose={() => setBubbleOpen(false)}
                onMascotClick={() => setMascotState('wave', 1200)}
                mouseOffset={mouseOffset}
                prefersReducedMotion={prefersReducedMotion}
                size={440}
              />
            </div>

            {/* Floating Glass Stat Card 1: Resume Analysis (Top Right) */}
            <motion.div
              animate={
                prefersReducedMotion
                  ? {}
                  : {
                      y: [0, -8, 0],
                      transition: { duration: 5.4, repeat: Infinity, ease: 'easeInOut' },
                    }
              }
              className="absolute -top-2 right-2 sm:right-6 z-20"
            >
              <GlassCard className="p-3.5 sm:p-4 flex items-center gap-3.5 shadow-glass-lg border-white/95 backdrop-blur-md">
                <ScoreRing score={98} max={100} size={54} strokeWidth={5} color="#2563EB" />
                <div>
                  <p className="text-[11px] font-medium text-[#64748B]">Resume Analysis</p>
                  <p className="text-sm sm:text-base font-extrabold text-[#0B0F19] tracking-tight">
                    98/100
                  </p>
                  <p className="text-[10px] font-semibold text-[#2563EB]">Great Score!</p>
                </div>
              </GlassCard>
            </motion.div>

            {/* Floating Glass Stat Card 2: Skill Gap (Mid Left) */}
            <motion.div
              animate={
                prefersReducedMotion
                  ? {}
                  : {
                      y: [0, 8, 0],
                      transition: { duration: 6.2, repeat: Infinity, ease: 'easeInOut', delay: 0.8 },
                    }
              }
              className="absolute top-1/3 -left-2 sm:left-4 z-20"
            >
              <GlassCard className="p-3 sm:p-3.5 flex items-center gap-3 shadow-glass border-white/90">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2563EB] flex items-center justify-center shrink-0 border border-blue-100">
                  <Layers size={18} />
                </div>
                <div>
                  <p className="text-[11px] font-medium text-[#64748B]">Skill Gap</p>
                  <p className="text-sm font-bold text-[#0B0F19]">3 areas</p>
                </div>
              </GlassCard>
            </motion.div>

            {/* Floating Glass Stat Card 3: Job Match (Mid Right) */}
            <motion.div
              animate={
                prefersReducedMotion
                  ? {}
                  : {
                      y: [0, -6, 0],
                      transition: { duration: 5.8, repeat: Infinity, ease: 'easeInOut', delay: 1.4 },
                    }
              }
              className="absolute bottom-16 -right-2 sm:right-4 z-20"
            >
              <GlassCard className="p-3 sm:p-3.5 flex items-center gap-3 shadow-glass border-white/90">
                <div className="w-10 h-10 rounded-xl bg-orange-50 text-[#EA580C] flex items-center justify-center shrink-0 border border-orange-100">
                  <Briefcase size={18} />
                </div>
                <div>
                  <p className="text-[11px] font-medium text-[#64748B]">Job Match</p>
                  <p className="text-sm font-bold text-[#0B0F19]">92%</p>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION: WHY CAREERLENS? (More Than a Resume Checker) */}
      {/* ============================================================ */}
      <section id="features" className="py-20 px-4 sm:px-8 max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <p className="text-xs font-bold text-[#2563EB] uppercase tracking-wider mb-2">
              Why CareerLens?
            </p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight max-w-xl">
              More Than a Resume Checker. <br />
              <span className="text-[#0B0F19]">A Complete Career OS.</span>
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              aria-label="Previous"
              className="w-9 h-9 rounded-full bg-white border border-slate-200 text-[#475569] flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm"
            >
              ←
            </button>
            <button
              aria-label="Next"
              className="w-9 h-9 rounded-full bg-white border border-slate-200 text-[#475569] flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm"
            >
              →
            </button>
          </div>
        </div>

        {/* 4 Feature Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <GlassCard hoverable className="p-6 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 text-[#2563EB] flex items-center justify-center border border-blue-100 shadow-sm">
              <FileText size={22} />
            </div>
            <h3 className="text-lg font-bold text-[#0B0F19]">AI Resume Analysis</h3>
            <p className="text-xs text-[#64748B] leading-relaxed">
              Get detailed feedback with actionable suggestions, keyword density and recruiter diagnosis.
            </p>
          </GlassCard>

          <GlassCard hoverable className="p-6 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-[#4F46E5] flex items-center justify-center border border-indigo-100 shadow-sm">
              <Compass size={22} />
            </div>
            <h3 className="text-lg font-bold text-[#0B0F19]">Personalized Roadmap</h3>
            <p className="text-xs text-[#64748B] leading-relaxed">
              Step by step plan based on your skills, target roles, career switch goals and timeline.
            </p>
          </GlassCard>

          <GlassCard hoverable className="p-6 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-orange-50 text-[#EA580C] flex items-center justify-center border border-orange-100 shadow-sm">
              <Layers size={22} />
            </div>
            <h3 className="text-lg font-bold text-[#0B0F19]">Skill Gap Detection</h3>
            <p className="text-xs text-[#64748B] leading-relaxed">
              Know what to learn next to become job ready with curated open-source projects and topics.
            </p>
          </GlassCard>

          <GlassCard hoverable className="p-6 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-sky-50 text-[#0284C7] flex items-center justify-center border border-sky-100 shadow-sm">
              <Briefcase size={22} />
            </div>
            <h3 className="text-lg font-bold text-[#0B0F19]">Job & Internship Match</h3>
            <p className="text-xs text-[#64748B] leading-relaxed">
              Find the right opportunities tailored specifically to your verified skills and resume profile.
            </p>
          </GlassCard>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION: FROM CONFUSION TO CLARITY (Comparison) */}
      {/* ============================================================ */}
      <section className="py-20 px-4 sm:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-xl mx-auto mb-14">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight">
            From Confusion to Clarity.
          </h2>
          <p className="text-sm text-[#64748B] mt-2">
            See the transformative difference an AI career companion brings to your job search.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left: Before CareerLens */}
          <div className="lg:col-span-5 p-7 sm:p-8 rounded-[24px] bg-slate-100/80 border border-slate-200/90 shadow-sm space-y-5">
            <div className="flex items-center gap-3 pb-3 border-b border-slate-200">
              <div className="w-9 h-9 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center font-bold">
                :(
              </div>
              <h3 className="text-base font-bold text-[#0B0F19]">Before CareerLens</h3>
            </div>

            <ul className="space-y-3.5">
              {[
                'No idea what to do next',
                'Unclear resume feedback',
                'Random learning resources',
                'Missed opportunities',
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm text-[#64748B]">
                  <XCircle size={18} className="text-slate-400 shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Center Connector Arrow */}
          <div className="lg:col-span-2 flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-white border border-slate-200 shadow-sm flex items-center justify-center text-[#2563EB] font-bold">
              →
            </div>
          </div>

          {/* Right: After CareerLens */}
          <div className="lg:col-span-5 p-7 sm:p-8 rounded-[24px] bg-white border border-blue-200 shadow-glass-lg space-y-5">
            <div className="flex items-center gap-3 pb-3 border-b border-blue-100">
              <div className="w-9 h-9 rounded-full bg-[#0B0F19] text-white flex items-center justify-center font-bold">
                :)
              </div>
              <h3 className="text-base font-bold text-[#0B0F19]">After CareerLens</h3>
            </div>

            <ul className="space-y-3.5">
              {[
                'Clear career direction',
                'AI-powered resume improvements',
                'Personalized learning plan',
                'Relevant jobs & internships',
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm font-semibold text-[#0B0F19]">
                  <CheckCircle2 size={18} className="text-[#16A34A] shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION: HOW IT WORKS? (Get Started in Minutes) */}
      {/* ============================================================ */}
      <section id="how-it-works" className="py-20 px-4 sm:px-8 max-w-7xl mx-auto">
        <div className="mb-12">
          <p className="text-xs font-bold text-[#2563EB] uppercase tracking-wider mb-2">
            How It Works?
          </p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight">
            Get Started in Minutes.
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
          {[
            {
              step: '01',
              title: 'Upload Your Resume',
              desc: 'Upload your resume in PDF format with one click.',
              icon: FileText,
            },
            {
              step: '02',
              title: 'Get AI Analysis',
              desc: 'Receive detailed feedback, ATS checks and skill gap insights.',
              icon: Sparkles,
            },
            {
              step: '03',
              title: 'Explore Your Roadmap',
              desc: 'Get a personalized learning plan tailored to target roles.',
              icon: Compass,
            },
            {
              step: '04',
              title: 'Find Opportunities',
              desc: 'Discover jobs and internships that fit your validated profile.',
              icon: Briefcase,
            },
          ].map((item, idx) => {
            const Icon = item.icon
            return (
              <GlassCard key={item.step} className="p-6 relative space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#64748B] bg-slate-100 px-2.5 py-1 rounded-md">
                    {item.step}
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2563EB] flex items-center justify-center border border-blue-100 shadow-sm">
                    <Icon size={18} />
                  </div>
                </div>

                <h3 className="text-base font-bold text-[#0B0F19]">{item.title}</h3>
                <p className="text-xs text-[#64748B] leading-relaxed">{item.desc}</p>
              </GlassCard>
            )
          })}
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION: NOT JUST A TOOL. A CAREER COMPANION. */}
      {/* ============================================================ */}
      <section className="py-20 px-4 sm:px-8 max-w-7xl mx-auto">
        <GlassCard className="p-8 sm:p-12 lg:p-14 overflow-hidden relative">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left: Copy & Interactive Prompt Bar */}
            <div className="lg:col-span-7 space-y-6">
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight">
                Not Just a Tool. <br />
                <span className="text-[#0B0F19]">A Career Companion.</span>
              </h2>
              <p className="text-sm text-[#475569] leading-relaxed max-w-md">
                Get guidance, ask questions, explore roles and stay on track — anytime, anywhere.
              </p>

              {/* Search / Chat Input Box */}
              <form onSubmit={handleAskSubmit} className="relative max-w-md">
                <input
                  type="text"
                  value={askInput}
                  onChange={(e) => setAskInput(e.target.value)}
                  placeholder="Ask something... (e.g. How to break into AI engineering?)"
                  className="w-full h-13 pl-5 pr-14 py-3.5 bg-white border border-slate-300/80 rounded-pill text-sm text-[#0B0F19] placeholder:text-slate-400 focus-ring shadow-sm"
                />
                <button
                  type="submit"
                  aria-label="Send query"
                  className="absolute right-2 top-1.5 w-10 h-10 rounded-full bg-[#0B0F19] text-white flex items-center justify-center hover:bg-slate-800 transition-colors shadow-sm"
                >
                  <ArrowRight size={18} />
                </button>
              </form>

              {companionReply && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-2xl bg-blue-50/80 border border-blue-200 text-xs text-[#1E293B] leading-relaxed max-w-md shadow-sm"
                >
                  <p className="font-semibold text-[#2563EB] mb-1">Lens AI Companion:</p>
                  <p>{companionReply}</p>
                </motion.div>
              )}
            </div>

            {/* Right: Mascot with Speech Bubble */}
            <div className="lg:col-span-5 relative flex items-center justify-center">
              <Mascot
                state="greeting"
                bubbleText="Hey! 👋 Ask me anything about your career, skills or resume."
                bubbleOpen={true}
                size={340}
              />
            </div>
          </div>
        </GlassCard>
      </section>

      {/* ============================================================ */}
      {/* SECTION: DASHBOARD PREVIEW TABLET (REF-1 Bottom Left) */}
      {/* ============================================================ */}
      <section className="py-20 px-4 sm:px-8 max-w-7xl mx-auto text-center">
        <div className="max-w-2xl mx-auto mb-12">
          <Badge variant="blue" size="md">Interactive Dashboard</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight mt-3">
            Designed for Instant Impact.
          </h2>
          <p className="text-sm text-[#64748B] mt-2">
            Every analysis, metric, and bullet rewrite rendered in a high-clarity workspace.
          </p>
        </div>

        {/* 3D Glass Tablet Mockup */}
        <div className="max-w-5xl mx-auto p-4 sm:p-6 rounded-[32px] bg-slate-200/50 border border-white/90 shadow-2xl backdrop-blur-xl">
          <div className="rounded-[24px] bg-white border border-slate-200/90 shadow-lg overflow-hidden text-left p-6 sm:p-8 space-y-6">
            {/* Tablet Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#0B0F19] text-white flex items-center justify-center font-bold">
                  CL
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#0B0F19]">Resume Analysis</h3>
                  <p className="text-xs text-[#64748B]">Software Engineer • ATS Targeted</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button variant="secondary" size="sm">
                  Re-Analyze
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate('/dashboard/optimizer')}
                >
                  Open in App →
                </Button>
              </div>
            </div>

            {/* Score Ring Banner */}
            <div className="p-6 rounded-2xl bg-blue-50/50 border border-blue-100 flex flex-col sm:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-5">
                <ScoreRing score={98} max={100} size={74} strokeWidth={7} color="#2563EB" />
                <div>
                  <h4 className="text-lg font-extrabold text-[#0B0F19]">Excellent Resume!</h4>
                  <p className="text-xs text-[#64748B] max-w-sm mt-0.5">
                    Your resume is well structured and grounded in factual metrics.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <span className="text-xs font-semibold px-3 py-1.5 bg-emerald-50 text-[#16A34A] rounded-pill border border-emerald-200">
                  7 Strengths
                </span>
                <span className="text-xs font-semibold px-3 py-1.5 bg-amber-50 text-[#D97706] rounded-pill border border-amber-200">
                  3 Improvements
                </span>
              </div>
            </div>

            {/* Metric Tiles */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-xs font-medium text-[#64748B]">Work Experience</p>
                <p className="text-sm font-bold text-[#0B0F19] mt-1">Looks great!</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-xs font-medium text-[#64748B]">Skills</p>
                <p className="text-sm font-bold text-[#0B0F19] mt-1">3 new to add</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-xs font-medium text-[#64748B]">Projects</p>
                <p className="text-sm font-bold text-[#0B0F19] mt-1">Well presented!</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-xs font-medium text-[#64748B]">ATS Compliance</p>
                <p className="text-sm font-bold text-[#16A34A] mt-1">98% Passed</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SECTION: TRUSTED BY STUDENTS LIKE YOU (Testimonials) */}
      {/* ============================================================ */}
      <section className="py-20 px-4 sm:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-xl mx-auto mb-14">
          <p className="text-xs font-bold text-[#2563EB] uppercase tracking-wider mb-2">
            Real Experiences
          </p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight">
            Trusted by Students Like You.
          </h2>
        </div>

        {/* Metrics Banner */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-14">
          {MARKETING_CONFIG.METRICS.map((m) => (
            <GlassCard key={m.label} className="p-6 text-center space-y-1">
              <p className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19]">{m.value}</p>
              <p className="text-xs font-bold text-[#64748B]">{m.label}</p>
              <p className="text-[11px] text-[#94A3B8]">{m.detail}</p>
            </GlassCard>
          ))}
        </div>

        {/* Testimonials */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {MARKETING_CONFIG.TESTIMONIALS.map((t) => (
            <GlassCard key={t.name} className="p-6 space-y-4">
              <span className="text-3xl text-blue-300 font-serif leading-none">“</span>
              <p className="text-sm text-[#475569] leading-relaxed italic">
                "{t.quote}"
              </p>
              <div className="flex items-center gap-3 pt-3 border-t border-slate-100">
                <img
                  src={t.avatar}
                  alt={t.name}
                  width={38}
                  height={38}
                  className="w-9 h-9 rounded-full object-cover ring-2 ring-blue-100"
                />
                <div>
                  <p className="text-xs font-bold text-[#0B0F19]">{t.name}</p>
                  <p className="text-[11px] text-[#94A3B8]">{t.role}</p>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/* FINAL CTA BANNER */}
      {/* ============================================================ */}
      <section className="py-20 px-4 sm:px-8 max-w-7xl mx-auto">
        <GlassCard className="p-8 sm:p-14 bg-gradient-to-r from-blue-50/70 via-white/90 to-sky-50/70 text-center relative overflow-hidden">
          <div className="max-w-2xl mx-auto space-y-6 relative z-10">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight">
              Ready to Upgrade Your Career?
            </h2>
            <p className="text-sm sm:text-base text-[#475569]">
              Join 10,000+ students who are building a better future with CareerLens.
            </p>
            <div className="pt-2">
              <Button
                variant="primary"
                size="lg"
                trailingIcon={ArrowRight}
                onClick={() => navigate('/signup')}
              >
                Get Started Free
              </Button>
            </div>
          </div>
        </GlassCard>
      </section>

      {/* Footer */}
      <Footer />

      {/* Scripted "Watch Demo" Dialog (Section 5.1) */}
      <Dialog
        isOpen={demoOpen}
        onClose={() => setDemoOpen(false)}
        title="CareerLens Product Walkthrough"
        description="Scripted preview of resume analysis & ATS optimization"
        maxWidth="max-w-2xl"
      >
        <div className="space-y-6 py-4">
          <div className="p-6 rounded-2xl bg-blue-50/40 border border-blue-100 text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-blue-100/80 text-[#2563EB] mx-auto flex items-center justify-center">
              <FileText size={32} />
            </div>
            <div>
              <p className="text-sm font-bold text-[#0B0F19]">Demo Resume: Software_Engineer.pdf</p>
              <p className="text-xs text-[#64748B]">Simulating ATS scanning & LLM recruiter lens</p>
            </div>

            {/* Stepper simulation */}
            <div className="max-w-md mx-auto space-y-2 text-left pt-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600">
                <CheckCircle2 size={14} />
                <span>Extracted 1,480 characters</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600">
                <CheckCircle2 size={14} />
                <span>Compared keywords against Job Description</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-[#2563EB]">
                <ScoreRing score={98} max={100} size={28} showLabel={false} strokeWidth={4} />
                <span>Generated 98/100 ATS Score + 3 bullet improvements</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="secondary" size="sm" onClick={() => setDemoOpen(false)}>
              Close Demo
            </Button>
            <Button
              variant="primary"
              size="sm"
              trailingIcon={ArrowRight}
              onClick={() => {
                setDemoOpen(false)
                navigate('/dashboard/optimizer')
              }}
            >
              Try Optimizer Now
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
