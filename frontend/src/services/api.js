import { supabase } from './supabase'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function getToken() {
  try {
    const { data } = await supabase.auth.getSession()
    const sessionToken = data?.session?.access_token
    if (sessionToken) return sessionToken
  } catch {
    // fall back to storage lookup below
  }

  try {
    const projectRef = import.meta.env.VITE_SUPABASE_URL
      ?.replace('https://', '')
      ?.split('.')[0]
    const raw = localStorage.getItem(`sb-${projectRef}-auth-token`)
      || localStorage.getItem('supabase.auth.token')
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.access_token
      || parsed?.currentSession?.access_token
      || parsed?.session?.access_token
      || null
  } catch {
    return null
  }
}

async function request(method, url, data, isBlob = false) {
  const token = await getToken()
  const isFormData = typeof FormData !== 'undefined' && data instanceof FormData
  const headers = {}

  if (!isFormData) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${API_BASE}${url}`, {
      method,
      headers,
      body: data ? (isFormData ? data : JSON.stringify(data)) : undefined,
    })
  } catch {
    throw new Error('Network error: cannot reach API server')
  }

  if (!res.ok) {
    let detail = `Request failed: ${res.status}`
    try {
      const err = await res.json()
      detail = err.detail || err.message || detail
    } catch {
      try {
        const text = await res.text()
        if (text) detail = text
      } catch {
        // ignore body parse failures
      }
    }
    throw new Error(detail)
  }

  if (isBlob) return res.blob()
  return res.json()
}

export const api = {
  // Auth
  getMe: () => request('GET', '/api/auth/me'),
  updateProfile: (body) => request('PUT', '/api/auth/me', body),

  // Resume
  analyzeResume: (body) => request('POST', '/api/resume/analyze', body),
  getAnalysisHistory: () => request('GET', '/api/resume/history'),
  getResumeHistory: () => request('GET', '/api/resume/history'),
  getAnalysis: (id) => request('GET', `/api/resume/${id}`),
  extractResumeText: (body) => request('POST', '/api/resume/extract-text', body),
  getProgressHistory: () => request('GET', '/api/resume/progress'),

  // ATS
  checkATS: (body) => request('POST', '/api/resume/ats-check', body),

  // Interview
  startInterview: (body) => request('POST', '/api/interview/start', body),
  evaluateInterview: (body) => request('POST', '/api/interview/evaluate', body),
  getInterviewHistory: () => request('GET', '/api/interview/history'),
  getInterviewResult: (id) => request('GET', `/api/interview/${id}`),

  // Chatbot
  sendMessage: (body) => request('POST', '/api/chatbot/message', body),
  getChatHistory: (sessionId) =>
    request('GET', `/api/chatbot/history${sessionId ? `?session_id=${sessionId}` : ''}`),
  clearChatSession: (sessionId) => request('DELETE', `/api/chatbot/history/${sessionId}`),

  // News
  getTechNews: () => request('GET', '/api/news/tech'),
  getHiringNews: () => request('GET', '/api/news/hiring'),

  // GitHub
  getGithubProfile: (username) => request('GET', `/api/github/profile?username=${username}`),

  // Optimizer
  optimizeResume: (body) => request('POST', '/api/optimizer/', body),

  // Job Match
  matchJobs: (body) => request('POST', '/api/job-match/', body),

  // Interview Probability
  predictInterviewProbability: (body) => request('POST', '/api/interview-probability/', body),
  getPredictionHistory: () => request('GET', '/api/interview-probability/history'),

  // Recommendations
  getCareerRecommendations: (body) => request('POST', '/api/recommendations/', body),

  // Community
  getPosts: (type) => request('GET', `/api/community/posts?post_type=${type || 'all'}`),
  createPost: (body) => request('POST', '/api/community/posts', body),
  deletePost: (id) => request('DELETE', `/api/community/posts/${id}`),
  likePost: (id) => request('POST', `/api/community/posts/${id}/like`),
  getUserLikes: () => request('GET', '/api/community/likes'),
  getComments: (postId) => request('GET', `/api/community/posts/${postId}/comments`),
  addComment: (body) => request('POST', '/api/community/comments', body),
  deleteComment: (id) => request('DELETE', `/api/community/comments/${id}`),

  // Portfolio
  generatePortfolio: (body) => request('POST', '/api/portfolio/generate', body),

  // Beginner
  generateBeginnerRoadmap: (body) => request('POST', '/api/beginner/roadmap', body),

  // Premium
  getPlans: () => request('GET', '/api/premium/plans'),
  initiatePayment: (body) => request('POST', '/api/premium/initiate', body),
  upgradePlan: (body) => request('POST', '/api/premium/upgrade', body),
}
