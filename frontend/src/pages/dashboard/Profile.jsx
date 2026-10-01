// frontend/src/pages/dashboard/Profile.jsx
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import { supabase } from '../../services/supabase'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'
import { User, Github, Briefcase, Save, Loader2, Chrome } from 'lucide-react'
import { GlassCard, Badge } from '../../components/ui'

const GITHUB_LOCK_KEY = 'careerlens:locked_github_url'

const normalizeGithubUrl = (rawUrl = '') => {
  const url = String(rawUrl || '').trim()
  if (!url) return ''
  const m = url.match(/github\.com\/([^/?#]+)/i)
  return m ? `https://github.com/${m[1]}` : url
}

const resolveAuthGithubIdentity = (authUser) => {
  const providers = new Set()
  const identities = Array.isArray(authUser?.identities) ? authUser.identities : []
  for (const identity of identities) {
    const provider = identity?.provider || identity?.identity_data?.provider
    if (provider) providers.add(String(provider).toLowerCase())
  }

  const appProvider = authUser?.app_metadata?.provider
  if (appProvider) providers.add(String(appProvider).toLowerCase())
  const appProviders = Array.isArray(authUser?.app_metadata?.providers) ? authUser.app_metadata.providers : []
  for (const p of appProviders) {
    if (p) providers.add(String(p).toLowerCase())
  }

  const userMeta = authUser?.user_metadata || {}
  const identityMeta = identities.find((i) => (i?.provider || '').toLowerCase() === 'github')?.identity_data || {}
  const githubUsername = (
    userMeta.user_name
    || userMeta.preferred_username
    || userMeta.username
    || userMeta.login
    || identityMeta.user_name
    || identityMeta.preferred_username
    || identityMeta.username
    || identityMeta.login
    || ''
  ).trim()

  const githubUrl = githubUsername
    ? `https://github.com/${githubUsername}`
    : normalizeGithubUrl(userMeta.profile || userMeta.url || '')

  if (githubUsername) {
    providers.add('github')
  }

  return {
    providers: Array.from(providers),
    githubUsername,
    githubUrl: githubUsername ? githubUrl : (providers.has('github') ? githubUrl : ''),
  }
}

export default function Profile() {
  const { user: authUser } = useAuth()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({ name: '', github_url: '', desired_role: '' })
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [linkingProvider, setLinkingProvider] = useState('')
  const [linkError, setLinkError] = useState('')

  useEffect(() => {
    let active = true
    const load = async () => {
      setLoading(true)
      setLoadError('')
      try {
        const [meSettled, historySettled] = await Promise.allSettled([
          api.getMe(),
          api.getResumeHistory(),
        ])
        if (!active) return

        const meRes = meSettled.status === 'fulfilled' ? meSettled.value : null
        const historyRes = historySettled.status === 'fulfilled' ? historySettled.value : { analyses: [] }
        const authIdentity = resolveAuthGithubIdentity(authUser)
        const githubFromOAuth = meRes?.user?.github_username ? `https://github.com/${meRes.user.github_username}` : ''
        const historyGithub = Array.isArray(historyRes?.analyses)
          ? (historyRes.analyses.find((a) => a?.github_url)?.github_url || '')
          : ''
        const storedGithub = localStorage.getItem(GITHUB_LOCK_KEY) || ''
        const resolvedGithubUrl = normalizeGithubUrl(
          meRes?.user?.github_url || githubFromOAuth || authIdentity.githubUrl || historyGithub || storedGithub || ''
        )

        const userObj = meRes?.user || {
          email: authUser?.email || '',
          name: authUser?.user_metadata?.name || '',
          github_url: resolvedGithubUrl,
          desired_role: '',
          plan_type: 'free',
        }

        const effectiveUser = {
          ...userObj,
          github_url: resolvedGithubUrl,
        }

        setProfile(effectiveUser)
        setForm({
          name: effectiveUser.name || '',
          github_url: resolvedGithubUrl,
          desired_role: effectiveUser.desired_role || '',
        })
      } catch (err) {
        setLoadError(err?.message || 'Failed to load profile')
      }
      setLoading(false)
    }

    load()
    return () => {
      active = false
    }
  }, [authUser])

  const authIdentity = resolveAuthGithubIdentity(authUser)
  const authProviders = authIdentity.providers
  const githubLinked = authProviders.includes('github') || Boolean(profile?.github_username)
  const githubLocked = Boolean(profile?.github_url) || githubLinked

  const handle = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))

  const handleSave = async () => {
    setSaving(true)
    const toastId = toast.loading('Saving profile...')
    try {
      const res = await api.updateProfile(form)
      const updatedUser = { ...(profile || {}), ...(res?.user || {}), ...form }
      const githubFromOAuth = updatedUser.github_username ? `https://github.com/${updatedUser.github_username}` : ''
      const normalizedGithubUrl = normalizeGithubUrl(updatedUser.github_url || githubFromOAuth || '')
      const normalizedUser = { ...updatedUser, github_url: normalizedGithubUrl }
      if (normalizedGithubUrl) localStorage.setItem(GITHUB_LOCK_KEY, normalizedGithubUrl)
      setProfile(normalizedUser)
      setForm({
        name: normalizedUser.name || '',
        github_url: normalizedGithubUrl,
        desired_role: normalizedUser.desired_role || '',
      })
      setSaved(true)
      toast.success('Profile updated!', { id: toastId })
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      const msg = err.message || 'Failed to save profile.'
      toast.error(msg, { id: toastId })
    }
    setSaving(false)
  }

  const handleLinkProvider = async (provider) => {
    setLinkError('')
    setLinkingProvider(provider)
    const { data, error } = await supabase.auth.linkIdentity({
      provider,
      options: { redirectTo: `${window.location.origin}/dashboard/profile` },
    })
    if (error) {
      setLinkError(error.message || `Could not link ${provider}.`)
      setLinkingProvider('')
      return
    }
    if (data?.url) {
      window.location.href = data.url
      return
    }
    setLinkingProvider('')
  }

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 size={32} className="animate-spin text-[#2563EB]" />
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="max-w-xl mx-auto py-12">
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-[#E11D48] text-xs font-semibold">
          {loadError || 'Could not load profile.'}
        </div>
      </div>
    )
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
      <div className="max-w-xl mx-auto space-y-6 pb-16">
        <div>
          <Badge sparkle size="sm" className="mb-1">Account</Badge>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0B0F19] tracking-tight">Profile &amp; Settings</h1>
        </div>

        {loadError && (
          <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
            {loadError}
          </div>
        )}

        {/* User Card */}
        <GlassCard className="p-6 border-white/95 shadow-glass flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 text-[#2563EB] flex items-center justify-center text-xl font-black shrink-0">
            {profile.name?.[0]?.toUpperCase() || '?'}
          </div>
          <div className="space-y-0.5 min-w-0">
            <p className="text-base sm:text-lg font-bold text-[#0B0F19] truncate">{profile.name || 'User'}</p>
            <p className="text-xs text-[#64748B] truncate">{profile.email}</p>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full inline-block mt-1 ${
                profile.plan_type === 'premium'
                  ? 'bg-amber-50 text-amber-800 border border-amber-200'
                  : 'bg-slate-100 text-[#64748B]'
              }`}
            >
              {profile.plan_type === 'premium' ? '⭐ Pro Tier' : 'Free Tier'}
            </span>
          </div>
        </GlassCard>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {[
            ['Scans', profile.resume_analysis_count || 0],
            ['Interviews', profile.mock_interview_count || 0],
            ['Messages', profile.chatbot_message_count || 0],
            ['Portfolios', profile.portfolio_gen_count || 0],
          ].map(([l, v]) => (
            <GlassCard key={l} className="p-3.5 text-center border-white/90">
              <p className="text-xl font-black text-[#0B0F19]">{v}</p>
              <p className="text-[11px] text-[#64748B] font-semibold uppercase mt-0.5">{l}</p>
            </GlassCard>
          ))}
        </div>

        {/* Edit form */}
        <GlassCard className="p-6 border-white/95 shadow-glass-lg space-y-4">
          <h2 className="text-sm font-bold text-[#0B0F19] uppercase tracking-wider">Account Details</h2>
          {[
            { key: 'name', label: 'Full Name', icon: User, type: 'text', ph: 'Your name' },
            { key: 'github_url', label: 'GitHub Profile', icon: Github, type: 'url', ph: 'https://github.com/username' },
            { key: 'desired_role', label: 'Target Job Title', icon: Briefcase, type: 'text', ph: 'e.g. Senior Full Stack Engineer' },
          ].map(({ key, label, icon: Icon, type, ph }) => (
            <div key={key}>
              <label className="block text-xs font-bold text-[#0B0F19] uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Icon size={13} className="text-[#2563EB]" /> {label}
              </label>
              <input
                type={type}
                value={form[key]}
                onChange={handle(key)}
                placeholder={ph}
                disabled={key === 'github_url' && githubLocked}
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs sm:text-sm font-semibold text-[#0B0F19] shadow-xs focus:border-[#2563EB] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 disabled:bg-slate-50 disabled:text-[#64748B]"
              />
              {key === 'github_url' && (
                <p className="mt-1 text-[11px] text-[#64748B]">
                  {githubLocked
                    ? 'GitHub profile is verified and locked to this account.'
                    : 'Enter your GitHub username to link real code evidence.'}
                </p>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="w-full flex items-center justify-center gap-2 py-3.5 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50 mt-2"
          >
            {saving ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Saving...
              </>
            ) : saved ? (
              '✓ Saved!'
            ) : (
              <>
                <Save size={16} /> Save Changes
              </>
            )}
          </button>
        </GlassCard>

        {/* Connected accounts */}
        <GlassCard className="p-6 border-white/95 shadow-glass space-y-3">
          <h2 className="text-sm font-bold text-[#0B0F19] uppercase tracking-wider">Connected Accounts</h2>
          <p className="text-xs text-[#64748B]">Link identity providers for streamlined authentication.</p>
          {linkError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-[#E11D48] text-xs font-semibold">
              {linkError}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
            <button
              type="button"
              disabled={githubLinked || !!linkingProvider}
              onClick={() => handleLinkProvider('github')}
              className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-full border border-slate-200 bg-white text-xs font-bold text-[#0B0F19] hover:bg-slate-50 transition-colors disabled:opacity-50 shadow-xs"
            >
              {linkingProvider === 'github' ? <Loader2 size={14} className="animate-spin" /> : <Github size={14} />}
              <span>{githubLinked ? 'GitHub Linked' : 'Link GitHub'}</span>
            </button>
            <button
              type="button"
              disabled={authProviders.includes('google') || !!linkingProvider}
              onClick={() => handleLinkProvider('google')}
              className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-full border border-slate-200 bg-white text-xs font-bold text-[#0B0F19] hover:bg-slate-50 transition-colors disabled:opacity-50 shadow-xs"
            >
              {linkingProvider === 'google' ? <Loader2 size={14} className="animate-spin" /> : <Chrome size={14} />}
              <span>{authProviders.includes('google') ? 'Google Linked' : 'Link Google'}</span>
            </button>
          </div>
        </GlassCard>
      </div>
    </motion.div>
  )
}
