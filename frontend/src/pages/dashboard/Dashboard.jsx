import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, useInView } from 'framer-motion'
import { api } from '../../services/api'
import {
  FileText,
  Mic,
  Bot,
  Star,
  ArrowRight,
  Zap,
  TrendingUp,
  CheckCircle,
  Upload,
  Sparkles,
  Target,
  Brain,
  Users,
} from 'lucide-react'
import SocialProof from './SocialProof'
import { useCountUp, staggerContainer, staggerItem, pageTransition } from '../../utils/animations'

const CARD_COLORS = {
  analyses: {
    border: '#FF3B3B',
    glow: 'rgba(255,59,59,0.28)',
    iconBg: 'linear-gradient(135deg,#FF3B3B,#CC1A1A)',
    iconColor: '#fff',
  },
  interviews: {
    border: '#e11d48',
    glow: 'rgba(225,29,72,0.25)',
    iconBg: 'linear-gradient(135deg,#e11d48,#be123c)',
    iconColor: '#fff',
  },
  messages: {
    border: '#10b981',
    glow: 'rgba(16,185,129,0.24)',
    iconBg: 'linear-gradient(135deg,#10b981,#0f9f6e)',
    iconColor: '#fff',
  },
  plan: {
    border: '#fb7185',
    glow: 'rgba(251,113,133,0.28)',
    iconBg: 'linear-gradient(135deg,#fb7185,#e11d48)',
    iconColor: '#fff',
  },
}

const ACTION_STYLES = {
  resume: 'linear-gradient(135deg,#FF3B3B,#CC1A1A)',
  optimizer: 'linear-gradient(135deg,#e11d48,#FF3B3B)',
  predictor: 'linear-gradient(135deg,#FF3B3B,#8B0000)',
  interview: 'linear-gradient(135deg,#10b981,#e11d48)',
  ats: 'linear-gradient(135deg,#8B0000,#FF3B3B)',
  community: 'linear-gradient(135deg,#e11d48,#fb7185)',
}

function StatCard({ label, value, icon: Icon, tone }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-12% 0px' })
  const isNumber = typeof value === 'number'
  const count = useCountUp(isNumber && inView ? value : 0, 1400)
  const colors = CARD_COLORS[tone]

  return (
    <motion.div
      ref={ref}
      variants={staggerItem}
      whileHover={{ y: -3, scale: 1.01 }}
      className="glass-glow p-5"
      style={{
        borderTop: `2px solid ${colors.border}`,
      }}
    >
      <div
        aria-hidden
        style={{
          position: 'absolute',
          top: -28,
          right: -12,
          width: 110,
          height: 110,
          borderRadius: '50%',
          background: colors.glow,
          filter: 'blur(30px)',
          pointerEvents: 'none',
        }}
      />

      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p
            className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8A8FA8]"
            style={{
              fontFamily: 'Cabinet Grotesk, sans-serif',
              fontWeight: 500,
              fontSize: 11,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            {label}
          </p>
          <p
            className="text-[32px] font-black leading-none text-white"
            style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 900, letterSpacing: '-0.04em' }}
          >
            {isNumber ? count : value}
          </p>
        </div>

        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 14,
            background: colors.iconBg,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 0 22px ${colors.glow}`,
          }}
        >
          <Icon size={18} color={colors.iconColor} />
        </div>
      </div>
    </motion.div>
  )
}

function ActionCard({ to, icon: Icon, title, desc, tone }) {
  return (
    <Link to={to}>
      <motion.div
        variants={staggerItem}
        whileHover={{ y: -3, x: 5, scale: 1.01 }}
        className="glass-glow flex items-center gap-4 p-5"
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 14,
            background: ACTION_STYLES[tone],
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 24px rgba(255,59,59,0.2)',
            flexShrink: 0,
          }}
        >
          <Icon size={20} className="text-white" />
        </div>

        <div className="min-w-0 flex-1">
          <p
            className="mb-1 text-sm font-semibold text-white"
            style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 700 }}
          >
            {title}
          </p>
          <p
            className="text-xs leading-relaxed text-[#8A8FA8]"
            style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 400 }}
          >
            {desc}
          </p>
        </div>

        <motion.div whileHover={{ x: 4 }} className="text-[#FF7070]">
          <ArrowRight size={16} />
        </motion.div>
      </motion.div>
    </Link>
  )
}

function FeatureCard({ icon: Icon, title, description, iconBg, iconGlow }) {
  return (
    <motion.div
      variants={staggerItem}
      whileHover={{ y: -3, scale: 1.01 }}
      className="glass-glow p-6"
    >
      <div
        aria-hidden
        style={{
          position: 'absolute',
          right: -12,
          bottom: -16,
          width: 94,
          height: 94,
          borderRadius: '50%',
          background: iconGlow,
          filter: 'blur(24px)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          width: 46,
          height: 46,
          borderRadius: 14,
          background: iconBg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 0 22px ${iconGlow}`,
          marginBottom: 18,
        }}
      >
        <Icon size={20} className="text-white" />
      </div>

      <h3
        className="mb-2 text-sm font-bold text-white"
        style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 700 }}
      >
        {title}
      </h3>
      <p className="text-xs leading-relaxed text-[#8A8FA8]">{description}</p>
    </motion.div>
  )
}

function SectionHeading({ children, sub }) {
  return (
    <div className="mb-5">
      <h2
        className="mb-1 text-2xl font-black text-white"
        style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 700, letterSpacing: '-0.03em' }}
      >
        {children}
      </h2>
      {sub && <p className="text-sm text-[#8A8FA8]">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    api.getMe().then((response) => setProfile(response.user)).catch(() => {})
  }, [])

  const firstName = profile?.name?.split(' ')[0] || 'there'

  return (
    <motion.div
      variants={pageTransition}
      initial="hidden"
      animate="visible"
      exit="exit"
      style={{ width: '100%' }}
    >
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
          className="glass-glow relative overflow-hidden p-10 md:p-12"
          style={{
            background: 'rgba(24,27,37,0.6)',
            backdropFilter: 'blur(20px)',
            borderRadius: 24,
            border: '1px solid rgba(255,255,255,0.07)',
          }}
        >
          <div
            aria-hidden
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 2,
              background: 'linear-gradient(90deg, transparent, #FF3B3B, #FF7070, transparent)',
            }}
          />
          <div
            aria-hidden
            style={{
              position: 'absolute',
              left: -60,
              top: -40,
              width: 500,
              height: 300,
              background: 'radial-gradient(circle, rgba(255,59,59,0.1) 0%, transparent 70%)',
              filter: 'blur(60px)',
              pointerEvents: 'none',
            }}
          />
          <div
            aria-hidden
            style={{
              position: 'absolute',
              right: 30,
              bottom: -20,
              fontSize: 140,
              lineHeight: 1,
              fontWeight: 900,
              color: 'rgba(255,255,255,0.025)',
              userSelect: 'none',
            }}
          >
            AI
          </div>

          <div className="relative z-[1] max-w-3xl">
            <div
              className="badge badge-red mb-5"
              style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 600, letterSpacing: '0.1em' }}
            >
              <Sparkles size={12} />
              AI CAREER PLATFORM
            </div>
            <h1
              className="gradient-text mb-4 text-[36px] font-black leading-tight md:text-[44px]"
              style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 900, letterSpacing: '-0.04em' }}
            >
              Hello, {firstName}!
            </h1>
            <p
              className="mb-8 max-w-2xl text-[15px] leading-7 text-[#8A8FA8]"
              style={{ fontFamily: 'Cabinet Grotesk, sans-serif', fontWeight: 400 }}
            >
              Your AI-powered career workspace is ready. Analyze your resume, sharpen your interview readiness,
              and move through every next step with clearer signal.
            </p>

            <div className="flex flex-wrap gap-3">
              <Link to="/dashboard/resume" className="btn-primary">
                <FileText size={16} />
                Analyze Resume
              </Link>
              <Link to="/dashboard/interview-predictor" className="btn-ghost">
                <Target size={16} />
                Interview Predictor
              </Link>
              {profile?.plan_type === 'freemium' && (
                <Link to="/dashboard/upgrade" className="btn-ghost">
                  <Star size={15} />
                  Upgrade to Pro
                </Link>
              )}
            </div>
          </div>
        </motion.div>

        <div>
          <SectionHeading>Your Activity</SectionHeading>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
          >
            <StatCard label="Analyses Done" value={profile?.resume_analysis_count ?? 0} icon={FileText} tone="analyses" />
            <StatCard label="Mock Interviews" value={profile?.mock_interview_count ?? 0} icon={Mic} tone="interviews" />
            <StatCard label="AI Messages" value={profile?.chatbot_message_count ?? 0} icon={Bot} tone="messages" />
            <StatCard
              label="Current Plan"
              value={profile?.plan_type === 'premium' ? 'Pro' : 'Free'}
              icon={Zap}
              tone="plan"
            />
          </motion.div>
        </div>

        <div>
          <SectionHeading sub="Jump straight into your highest-leverage actions">Quick Actions</SectionHeading>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid gap-3 md:grid-cols-2 xl:grid-cols-3"
          >
            <ActionCard
              to="/dashboard/resume"
              icon={FileText}
              title="Analyze My Resume"
              desc="Upload your PDF for a sharper read on fit, gaps, and next steps."
              tone="resume"
            />
            <ActionCard
              to="/dashboard/optimizer"
              icon={Sparkles}
              title="Optimize for a Job"
              desc="Rewrite resume bullets to match a specific role and ATS language."
              tone="optimizer"
            />
            <ActionCard
              to="/dashboard/interview-predictor"
              icon={Target}
              title="Interview Predictor"
              desc="Estimate your interview odds before you spend time applying."
              tone="predictor"
            />
            <ActionCard
              to="/dashboard/interview"
              icon={Mic}
              title="Mock Interview"
              desc="Practice role-specific questions with immediate AI feedback."
              tone="interview"
            />
            <ActionCard
              to="/dashboard/ats-checker"
              icon={CheckCircle}
              title="ATS Checker"
              desc="See if your resume language survives applicant tracking filters."
              tone="ats"
            />
            <ActionCard
              to="/dashboard/community"
              icon={Users}
              title="Community Feed"
              desc="Share wins, projects, and opportunities with the builder network."
              tone="community"
            />
          </motion.div>
        </div>

        <div>
          <SectionHeading sub="What makes CareerLens feel more tactical than generic career tools">
            Why CareerLens
          </SectionHeading>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
          >
            <FeatureCard
              icon={FileText}
              title="Multi-Profile Analysis"
              description="Resume, GitHub, and job intent get read together so the advice feels grounded."
              iconBg="linear-gradient(135deg,#FF3B3B,#CC1A1A)"
              iconGlow="rgba(255,59,59,0.26)"
            />
            <FeatureCard
              icon={TrendingUp}
              title="Skill Gap Detection"
              description="See what is missing, how much it matters, and what to learn next."
              iconBg="linear-gradient(135deg,#e11d48,#FF3B3B)"
              iconGlow="rgba(225,29,72,0.22)"
            />
            <FeatureCard
              icon={Mic}
              title="AI Mock Interviews"
              description="Rehearse with targeted prompts and tighter feedback loops before the real call."
              iconBg="linear-gradient(135deg,#10b981,#0f9f6e)"
              iconGlow="rgba(16,185,129,0.22)"
            />
            <FeatureCard
              icon={Brain}
              title="Personalized Roadmap"
              description="Turn vague improvement ideas into a concrete plan you can actually execute."
              iconBg="linear-gradient(135deg,#fb7185,#e11d48)"
              iconGlow="rgba(251,113,133,0.24)"
            />
          </motion.div>
        </div>

        <div>
          <SectionHeading sub="From profile upload to job-ready momentum">How It Works</SectionHeading>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid gap-4 md:grid-cols-3"
          >
            {[
              {
                step: '01',
                title: 'Upload Your Profile',
                desc: 'Start with your resume, GitHub, and target role.',
                icon: Upload,
              },
              {
                step: '02',
                title: 'Get AI Career Analysis',
                desc: 'CareerLens reads your materials and exposes the real gaps.',
                icon: Bot,
              },
              {
                step: '03',
                title: 'Improve & Prepare',
                desc: 'Use the roadmap, optimizer, and interview tools to raise your odds.',
                icon: TrendingUp,
              },
            ].map(({ step, title, desc, icon: Icon }) => (
              <motion.div key={step} variants={staggerItem} whileHover={{ y: -3 }} className="glass-glow p-6">
                <div
                  className="absolute right-5 top-4 text-[68px] font-black leading-none text-white/[0.025]"
                  style={{ fontFamily: 'Clash Display, sans-serif', fontWeight: 900 }}
                >
                  {step}
                </div>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 14,
                    background: 'rgba(255,59,59,0.1)',
                    border: '1px solid rgba(255,59,59,0.22)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 0 20px rgba(255,59,59,0.16)',
                    marginBottom: 18,
                  }}
                >
                  <Icon size={18} className="text-[#FF7070]" />
                </div>
                <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.18em] text-[#FF3B3B]">Step {step}</p>
                <h3 className="mb-2 text-base font-bold text-white">{title}</h3>
                <p className="text-sm leading-6 text-[#8A8FA8]">{desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>

        <div>
          <SectionHeading sub="Real results from real users">Community Wins</SectionHeading>
          <SocialProof />
        </div>
      </div>
    </motion.div>
  )
}
