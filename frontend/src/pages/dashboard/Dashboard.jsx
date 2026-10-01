import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../../services/api'
import {
  FileText,
  Mic,
  Bot,
  Star,
  ArrowRight,
  Zap,
  TrendingUp,
  Sparkles,
  Target,
  Briefcase,
  CheckCircle2,
  Lock,
} from 'lucide-react'
import { GlassCard, Button, Badge } from '../../components/ui'
import { Mascot } from '../../mascot/Mascot'

const STAT_CONFIGS = [
  {
    key: 'resume_analysis_count',
    label: 'Analyses Done',
    icon: FileText,
    tileBg: 'bg-blue-50 text-[#2563EB] border border-blue-100',
  },
  {
    key: 'mock_interview_count',
    label: 'Mock Interviews',
    icon: Mic,
    tileBg: 'bg-indigo-50 text-[#4F46E5] border border-indigo-100',
  },
  {
    key: 'chatbot_message_count',
    label: 'AI Coach Chats',
    icon: Bot,
    tileBg: 'bg-emerald-50 text-[#16A34A] border border-emerald-100',
  },
  {
    key: 'plan_type',
    label: 'Current Plan',
    icon: Zap,
    tileBg: 'bg-amber-50 text-[#D97706] border border-amber-100',
  },
]

const QUICK_ACTIONS = [
  {
    to: '/dashboard/optimizer',
    title: 'Resume Optimizer',
    desc: 'Targeted resume tailoring with grounded keywords and ATS scoring.',
    icon: Sparkles,
    highlight: true,
    tag: 'Hero Flow',
  },
  {
    to: '/dashboard/resume',
    title: 'Resume & GitHub Analysis',
    desc: 'Comprehensive multi-factor review of your CV and repositories.',
    icon: FileText,
  },
  {
    to: '/dashboard/job-match',
    title: 'Job & Internship Match',
    desc: 'Find live open roles matching your verified skills and level.',
    icon: Briefcase,
  },
  {
    to: '/dashboard/interview-predictor',
    title: 'Interview Predictor',
    desc: 'Estimate interview invitation odds before submitting applications.',
    icon: Target,
  },
  {
    to: '/dashboard/interview',
    title: 'Mock Interview',
    desc: 'Practice voice-enabled behavioral and technical questions.',
    icon: Mic,
  },
  {
    to: '/dashboard/chatbot',
    title: 'Honest Career Coach',
    desc: 'Unfiltered, strategic career guidance tailored to your situation.',
    icon: Bot,
  },
]

export default function Dashboard() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    api.getMe()
      .then((res) => {
        if (active) {
          setProfile(res.user)
          setLoading(false)
        }
      })
      .catch(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const firstName = profile?.name?.split(' ')[0] || 'there'
  const isPremium = profile?.plan_type === 'premium'

  return (
    <div className="w-full max-w-6xl mx-auto space-y-8 pb-16">
      {/* Hero Greeting Glass Banner */}
      <GlassCard className="relative overflow-hidden p-8 sm:p-10 border-white/95 shadow-glass-lg">
        {/* Soft Background Sky Bloom */}
        <div
          className="absolute -top-20 -right-20 w-80 h-80 rounded-full pointer-events-none blur-3xl opacity-60"
          style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.7) 0%, transparent 70%)' }}
        />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-2xl space-y-3">
            <div className="flex items-center gap-2">
              <Badge sparkle size="sm">
                AI Career Workspace
              </Badge>
              {isPremium ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold text-amber-700 border border-amber-200">
                  <Star size={12} className="fill-amber-500 text-amber-500" />
                  Pro Member
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
                  Free Tier
                </span>
              )}
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight">
              Hello, {firstName}!
            </h1>

            <p className="text-sm text-[#475569] leading-relaxed max-w-xl">
              Your career intelligence operating system is active. Upload your resume to optimize for specific roles, test your interview readiness, or explore your personalized roadmap.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link to="/dashboard/optimizer">
                <Button variant="primary" size="md" trailingIcon={ArrowRight}>
                  Optimize Resume
                </Button>
              </Link>
              <Link to="/dashboard/resume">
                <Button variant="secondary" size="md">
                  Upload PDF
                </Button>
              </Link>
              {!isPremium && (
                <Link to="/dashboard/upgrade">
                  <Button variant="ghost" size="md" icon={Star} className="text-amber-600 hover:text-amber-700">
                    Upgrade to Pro
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Mini Mascot Centerpiece */}
          <div className="hidden lg:flex items-center justify-center shrink-0 pr-4">
            <div className="relative">
              <Mascot size={150} showPodium={false} state="greeting" />
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Activity Stats Strip */}
      <div className="space-y-3">
        <h2 className="text-base font-bold text-[#0B0F19] tracking-tight">
          Your Activity & Limits
        </h2>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {STAT_CONFIGS.map(({ key, label, icon: Icon, tileBg }) => {
            let val = profile ? profile[key] : '—'
            if (key === 'plan_type') {
              val = isPremium ? 'Pro' : 'Free'
            }

            return (
              <GlassCard key={key} hoverable className="p-4 sm:p-5 flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] font-medium text-[#64748B] uppercase tracking-wider">
                    {label}
                  </p>
                  <p className="text-2xl font-extrabold text-[#0B0F19] tracking-tight mt-1">
                    {loading ? '...' : val}
                  </p>
                </div>
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${tileBg}`}>
                  <Icon size={20} />
                </div>
              </GlassCard>
            )
          })}
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-[#0B0F19] tracking-tight">
              Recommended Tools
            </h2>
            <p className="text-xs text-[#64748B]">
              Direct access to CareerLens intelligence modules.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {QUICK_ACTIONS.map(({ to, title, desc, icon: Icon, highlight, tag }) => (
            <Link key={to} to={to} className="group">
              <GlassCard
                hoverable
                className={`p-5 h-full flex flex-col justify-between transition-all duration-200 ${
                  highlight
                    ? 'border-blue-200/90 bg-gradient-to-br from-white via-white to-blue-50/40 shadow-[0_12px_32px_rgba(37,99,235,0.08)]'
                    : ''
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-105 shadow-sm ${
                        highlight
                          ? 'bg-[#2563EB] text-white shadow-blue-500/20'
                          : 'bg-slate-100 text-[#0B0F19]'
                      }`}
                    >
                      <Icon size={18} />
                    </div>
                    {tag && (
                      <span className="text-[10px] font-bold text-[#2563EB] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                        {tag}
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-[#0B0F19] group-hover:text-[#2563EB] transition-colors">
                    {title}
                  </h3>
                  <p className="text-xs text-[#64748B] mt-1.5 leading-relaxed">
                    {desc}
                  </p>
                </div>

                <div className="flex items-center gap-1 text-xs font-semibold text-[#2563EB] mt-4 pt-3 border-t border-slate-100 group-hover:gap-2 transition-all">
                  <span>Open Tool</span>
                  <ArrowRight size={13} />
                </div>
              </GlassCard>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
