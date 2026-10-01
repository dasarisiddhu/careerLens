# CareerLens — Routes & Service Dependency Audit

## Overview
This document catalogs every route in `frontend/src/App.jsx`, its page component, rendering responsibilities, API service dependencies, and auth/premium gating requirements.

| Route | Component | Purpose | Service Calls (`services/api.js`) | Auth / Access |
|---|---|---|---|---|
| `/` | `pages/Landing.jsx` | Landing page (Hero, features, demo, metrics, testimonials, FAQ, footer) | `supabase.auth.getSession()` | Public |
| `/login` | `pages/auth/Login.jsx` | User authentication | `supabase.auth.signInWithPassword`, `supabase.auth.signInWithOAuth` | Public (guest only) |
| `/signup` | `pages/auth/Signup.jsx` | User registration | `supabase.auth.signUp`, `supabase.auth.signInWithOAuth` | Public (guest only) |
| `/forgot-password` | `pages/auth/ForgotPassword.jsx` | Password reset request | `supabase.auth.resetPasswordForEmail` | Public (guest only) |
| `/dashboard` | `pages/dashboard/Dashboard.jsx` | Main dashboard overview, metrics, quick start | `api.getMe()` | Private |
| `/dashboard/optimizer` | `pages/dashboard/ResumeOptimizer.jsx` | Resume Optimizer (System B) — JD alignment, recruiter lens, bullet rewrites, ATS scoring, PDF download | `api.getMe()`, `api.extractResumeText()`, `api.analyseResume()`, `api.optimizeResume()`, `api.checkATS()`, `api.downloadProfessionalResumePdf()` | Private (Freemium quota gated) |
| `/dashboard/resume` | `pages/dashboard/ResumeAnalysis.jsx` | GitHub Project Insights & Repository analysis | `api.getMe()`, `api.getResumeHistory()`, `api.analyzeResume()` | Private |
| `/dashboard/resume/:id` | `pages/dashboard/AnalysisResult.jsx` | Analysis historical report view | `api.getAnalysis(id)` | Private |
| `/dashboard/job-match` | `pages/dashboard/JobMatch.jsx` | AI Job Match & Internship engine | `api.extractResumeText()`, `api.matchJobs()` | Private |
| `/dashboard/ats-checker` | `pages/dashboard/ATSChecker.jsx` | Direct ATS keyword & format checker | `api.extractResumeText()`, `api.checkATS()` | Private |
| `/dashboard/career-switch` | `pages/dashboard/CareerSwitch.jsx` | Career transition roadmaps & timeline | `api.generateBeginnerRoadmap()` | Private |
| `/dashboard/portfolio` | `pages/dashboard/Portfolio.jsx` | Portfolio generator for developers | `api.getMe()`, `api.generatePortfolio()` | Private |
| `/dashboard/chatbot` | `pages/dashboard/Chatbot.jsx` | Honest Career Coach AI chat | `api.sendMessage()`, `api.getChatHistory()`, `api.clearChatSession()` | Private |
| `/dashboard/interview` | `pages/dashboard/MockInterview.jsx` | AI Mock Interview stage (Web Speech API) | `api.startInterview()`, `api.evaluateInterview()`, `api.getInterviewHistory()`, `api.getInterviewResult()` | Private |
| `/dashboard/news/tech` | `pages/dashboard/TechNews.jsx` | Tech industry news feed | `api.getTechNews()` | Private |
| `/dashboard/news/hiring` | `pages/dashboard/HiringNews.jsx` | Hiring trends & companies actively hiring | `api.getHiringNews()` | Private |
| `/dashboard/progress` | `pages/dashboard/ProgressTracker.jsx` | Score history & career progression graphs | `api.getProgressHistory()` | Private |
| `/dashboard/recommendations` | `pages/dashboard/CareerRecommendations.jsx` | Skill recommendations & project roadmaps | `api.getCareerRecommendations()` | Private |
| `/dashboard/community` | `pages/dashboard/community.jsx` | Developer community posts, comments, likes | `api.getMe()`, `api.getPosts()`, `api.createPost()`, `api.deletePost()`, `api.likePost()`, `api.getUserLikes()`, `api.getComments()`, `api.addComment()`, `api.deleteComment()` | Private |
| `/dashboard/interview-predictor` | `pages/dashboard/interviewpredictor.jsx` | Probability score of landing interviews | `api.getMe()`, `api.getResumeHistory()`, `api.extractResumeText()`, `api.predictInterviewProbability()` | Private |
| `/dashboard/profile` | `pages/dashboard/Profile.jsx` | User account settings, skills, target roles | `api.getMe()`, `api.getResumeHistory()`, `api.updateProfile()` | Private |
| `/dashboard/upgrade` | `pages/dashboard/Upgrade.jsx` | Pro upgrade pricing & Stripe checkout | `api.getPlans()`, `api.initiatePayment()`, `api.upgradePlan()` | Private |
