import React, { Suspense, lazy } from 'react'
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import DashboardLayout from './components/layout/DashboardLayout'
// Auth Pages
import Login from './pages/auth/Login'
import Signup from './pages/auth/Signup'
import ForgotPassword from './pages/auth/ForgotPassword'
import Landing from './pages/Landing'

// Lazy load all dashboard pages (loaded only when visited)
const Dashboard = lazy(() => import('./pages/dashboard/Dashboard'))
const ResumeAnalysis = lazy(() => import('./pages/dashboard/ResumeAnalysis'))
const AnalysisResult = lazy(() => import('./pages/dashboard/AnalysisResult'))
const Chatbot = lazy(() => import('./pages/dashboard/Chatbot'))
const MockInterview = lazy(() => import('./pages/dashboard/MockInterview'))
const TechNews = lazy(() => import('./pages/dashboard/TechNews'))
const HiringNews = lazy(() => import('./pages/dashboard/HiringNews'))
const Upgrade = lazy(() => import('./pages/dashboard/Upgrade'))
const Profile = lazy(() => import('./pages/dashboard/Profile'))
const CareerSwitch = lazy(() => import('./pages/dashboard/CareerSwitch'))
const ATSChecker = lazy(() => import('./pages/dashboard/ATSChecker'))
const ProgressTracker = lazy(() => import('./pages/dashboard/ProgressTracker'))
const CareerRecommendations = lazy(() => import('./pages/dashboard/CareerRecommendations'))
const Community = lazy(() => import('./pages/dashboard/community'))
const InterviewPredictor = lazy(() => import('./pages/dashboard/interviewpredictor.jsx'))
const ResumeOptimizer = lazy(() => import('./pages/dashboard/ResumeOptimizer'))
const JobMatch = lazy(() => import('./pages/dashboard/JobMatch'))
const Portfolio = lazy(() => import('./pages/dashboard/Portfolio'))

const PageLoader = () => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
    flexDirection: 'column',
    gap: 16,
  }}>
    <div style={{
      width: 40, height: 40,
      borderRadius: '50%',
      border: '3px solid rgba(225,29,72,0.15)',
      borderTop: '3px solid #e11d48',
      animation: 'spin 0.8s linear infinite',
    }} />
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
)

function DashboardRouteSuspense() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Outlet />
    </Suspense>
  )
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-transparent">
      <div className="w-8 h-8 border-2 border-[#FF3B3B] border-t-transparent rounded-full animate-spin shadow-[0_0_20px_rgba(255,59,59,0.35)]" />
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return !user ? children : <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/signup" element={<PublicRoute><Signup /></PublicRoute>} />
      <Route path="/forgot-password" element={<PublicRoute><ForgotPassword /></PublicRoute>} />

      <Route path="/dashboard" element={<PrivateRoute><DashboardLayout /></PrivateRoute>}>
        <Route element={<DashboardRouteSuspense />}>
          <Route index element={<Dashboard />} />
          <Route path="career-switch" element={<CareerSwitch />} />
          <Route path="ats-checker" element={<ATSChecker />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="resume" element={<ResumeAnalysis />} />
          <Route path="resume/:id" element={<AnalysisResult />} />
          <Route path="chatbot" element={<Chatbot />} />
          <Route path="interview" element={<MockInterview />} />
          <Route path="news/tech" element={<TechNews />} />
          <Route path="news/hiring" element={<HiringNews />} />
          <Route path="upgrade" element={<Upgrade />} />
          <Route path="profile" element={<Profile />} />
          <Route path="progress" element={<ProgressTracker />} />
          <Route path="recommendations" element={<CareerRecommendations />} />
          <Route path="community" element={<Community />} />
          <Route path="interview-predictor" element={<InterviewPredictor />} />
          <Route path="job-match" element={<JobMatch />} />
          <Route path="optimizer" element={<ResumeOptimizer />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
