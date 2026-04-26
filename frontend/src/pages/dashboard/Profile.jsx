// frontend/src/pages/dashboard/Profile.jsx
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { pageTransition } from '../../utils/animations'
import { api } from '../../services/api'
import { supabase } from '../../services/supabase'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'
import { User, Github, Briefcase, Save, Loader2, Chrome } from 'lucide-react'

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
  const buttonMotion = {
    whileHover: { scale: 1.03, y: -1 },
    whileTap: { scale: 0.97 },
    transition: { duration: 0.15, ease: 'easeOut' },
  }

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
          meRes?.user?.github_url
          || githubFromOAuth
          || authIdentity.githubUrl
          || historyGithub
          || storedGithub
          || '',
        )

        if (resolvedGithubUrl) localStorage.setItem(GITHUB_LOCK_KEY, resolvedGithubUrl)

        if (meRes?.user) {
          const resolvedUser = {
            ...meRes.user,
            github_url: resolvedGithubUrl,
            github_username: meRes.user.github_username || authIdentity.githubUsername || '',
            auth_providers: Array.isArray(meRes.user.auth_providers) && meRes.user.auth_providers.length > 0
              ? meRes.user.auth_providers
              : authIdentity.providers,
          }
          setProfile(resolvedUser)
          setForm({
            name: resolvedUser.name || '',
            github_url: resolvedGithubUrl,
            desired_role: resolvedUser.desired_role || '',
          })
          return
        }

        if (authUser) {
          const fallbackUser = {
            name: authUser.user_metadata?.name || authUser.email?.split('@')[0] || 'User',
            email: authUser.email || '',
            plan_type: 'freemium',
            resume_analysis_count: 0,
            mock_interview_count: 0,
            chatbot_message_count: 0,
            portfolio_gen_count: 0,
            auth_providers: authIdentity.providers,
            github_username: authIdentity.githubUsername,
            github_url: resolvedGithubUrl,
            desired_role: '',
          }
          setProfile(fallbackUser)
          setForm({
            name: fallbackUser.name,
            github_url: fallbackUser.github_url || '',
            desired_role: fallbackUser.desired_role || '',
          })
          setLoadError('Profile details could not be fully loaded. Showing basic account info.')
          return
        }

        setLoadError('Could not load profile. Please refresh the page.')
      } catch (err) {
        if (!active) return
        if (authUser) {
          const authIdentity = resolveAuthGithubIdentity(authUser)
          const fallbackUser = {
            name: authUser.user_metadata?.name || authUser.email?.split('@')[0] || 'User',
            email: authUser.email || '',
            plan_type: 'freemium',
            resume_analysis_count: 0,
            mock_interview_count: 0,
            chatbot_message_count: 0,
            portfolio_gen_count: 0,
            auth_providers: authIdentity.providers,
            github_username: authIdentity.githubUsername,
            github_url: normalizeGithubUrl(authIdentity.githubUrl || localStorage.getItem(GITHUB_LOCK_KEY) || ''),
            desired_role: '',
          }
          setProfile(fallbackUser)
          setForm({
            name: fallbackUser.name,
            github_url: fallbackUser.github_url || '',
            desired_role: fallbackUser.desired_role || '',
          })
        }
        setLoadError(err?.message || 'Could not load profile. Please refresh the page.')
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [authUser])

  const handle = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const authProviders = Array.isArray(profile?.auth_providers) ? profile.auth_providers : []
  const githubLinked = authProviders.includes('github')
  const resolvedGithubUrl = (
    profile?.github_url
    || (profile?.github_username ? `https://github.com/${profile.github_username}` : '')
    || ''
  ).trim()
  const githubLocked = githubLinked || !!resolvedGithubUrl

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
    }
    catch (err) {
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
      <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
        <div className="flex justify-center py-16"><Loader2 size={28} className="animate-spin text-amber-400" /></div>
      </motion.div>
    )
  }

  if (!profile) {
    return (
      <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
        <div className="max-w-xl mx-auto">
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {loadError || 'Could not load profile.'}
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div variants={pageTransition} initial="hidden" animate="visible" exit="exit" style={{ width: '100%' }}>
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-white">Profile</h1>
      {loadError && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm">
          {loadError}
        </div>
      )}

      {/* Avatar */}
      <div className="glass p-6 rounded-2xl flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl border border-red-500/20 bg-[#151924] flex items-center justify-center text-2xl font-bold">
          {profile.name?.[0]?.toUpperCase() || '?'}
        </div>
        <div>
          <p className="text-xl font-bold text-white">{profile.name}</p>
          <p className="text-[#78716c] text-sm">{profile.email}</p>
          <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${profile.plan_type === 'premium' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-[#1c1917] text-[#78716c]'}`}>
            {profile.plan_type === 'premium' ? '⭐ Premium' : 'Free Plan'}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[['Analyses', profile.resume_analysis_count], ['Interviews', profile.mock_interview_count], ['Messages', profile.chatbot_message_count], ['Portfolios', profile.portfolio_gen_count || 0]].map(([l, v]) => (
          <div key={l} className="glass p-4 rounded-xl text-center">
            <p className="text-2xl font-bold text-white">{v}</p>
            <p className="text-xs text-[#78716c]">{l}</p>
          </div>
        ))}
      </div>

      {/* Edit form */}
      <div className="glass p-6 rounded-2xl space-y-4">
        <h2 className="text-lg font-bold text-white">Edit Profile</h2>
        {[
          { key: 'name', label: 'Full Name', icon: User, type: 'text', ph: 'Your name' },
          { key: 'github_url', label: 'GitHub URL', icon: Github, type: 'url', ph: 'https://github.com/username' },
          { key: 'desired_role', label: 'Desired Role', icon: Briefcase, type: 'text', ph: 'e.g. Full Stack Developer' },
        ].map(({ key, label, icon: Icon, type, ph }) => (
          <div key={key}>
            <label className="block text-sm font-medium text-[#d6d3d1] mb-1.5 flex items-center gap-2">
              <Icon size={13} /> {label}
            </label>
            <input
              type={type}
              value={form[key]}
              onChange={handle(key)}
              placeholder={ph}
              disabled={key === 'github_url' && githubLocked}
              className={`input-field ${key === 'github_url' && githubLocked ? 'opacity-70 cursor-not-allowed' : ''}`}
            />
            {key === 'github_url' && (
              <p className="mt-1 text-xs text-[#78716c]">
                {githubLocked
                  ? 'GitHub URL is locked for this account and cannot be changed.'
                  : githubLinked
                    ? `Linked GitHub account detected${profile?.github_username ? `: ${profile.github_username}` : ''}.`
                    : 'Set this once to lock your analysis profile.'}
              </p>
            )}
          </div>
        ))}
        <motion.button {...buttonMotion} onClick={handleSave} disabled={saving}
          className="btn-primary w-full flex items-center justify-center gap-2">
          {saving ? <><Loader2 size={16} className="animate-spin" /> Saving...</>
            : saved ? '✓ Saved!'
            : <><Save size={16} /> Save Changes</>}
        </motion.button>
      </div>

      <div className="glass p-6 rounded-2xl space-y-4">
        <h2 className="text-lg font-bold text-white">Connected Accounts</h2>
        <p className="text-xs text-[#78716c]">Link providers to secure identity verification for analysis.</p>
        {linkError && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {linkError}
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <motion.button {...buttonMotion}
            type="button"
            disabled={githubLinked || !!linkingProvider}
            onClick={() => handleLinkProvider('github')}
            className="btn-ghost w-full flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {linkingProvider === 'github' ? <Loader2 size={16} className="animate-spin" /> : <Github size={16} />}
            {githubLinked ? 'GitHub Linked' : 'Link GitHub'}
          </motion.button>
          <motion.button {...buttonMotion}
            type="button"
            disabled={authProviders.includes('google') || !!linkingProvider}
            onClick={() => handleLinkProvider('google')}
            className="btn-ghost w-full flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {linkingProvider === 'google' ? <Loader2 size={16} className="animate-spin" /> : <Chrome size={16} />}
            {authProviders.includes('google') ? 'Google Linked' : 'Link Google'}
          </motion.button>
        </div>
      </div>
    </div>
    </motion.div>
  )
}









