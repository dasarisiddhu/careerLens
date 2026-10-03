# 🔍 CareerLens – AI-Powered Career Guidance & Resume Intelligence Platform

[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.2-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-1.5_Flash-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL_%26_Auth-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose_Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **CareerLens** is a production-ready, full-stack career platform engineered to empower job seekers, students, and career switchers. Combining state-of-the-art **Google Gemini AI**, real-time **voice-assisted mock interviews**, targeted **ATS resume optimization**, **interview probability forecasting**, and an **interactive animated career coach**, CareerLens provides end-to-end guidance from resume preparation to job offer negotiation.

---

## 🌟 Key Features

### 📄 1. Targeted ATS Resume Scanner & Optimizer
- **Deep Document Extraction**: High-precision text parsing with `PyMuPDF`, `pdfplumber`, and OCR fallback via `pytesseract` for image-based PDFs.
- **Semantic ATS Match Score**: Quantified alignment against target job descriptions with detailed scoring across formatting, impact metrics, keyword density, and structural clarity.
- **Interactive Diff & Bullet Optimizer**: One-click AI rewriting converting weak bullet points into high-impact, quantified STAR-format accomplishments.
- **Export Options**: Download optimized resumes directly to PDF, DOCX, or clean TXT.

### 🎙️ 2. Voice-Assisted AI Mock Interviewer
- **Bi-Directional Voice Interaction**: Full speech-to-text input and natural text-to-speech voice playback using the Web Speech API.
- **Dynamic Role Simulation**: Generates custom technical, behavioral, and situational questions tailored to specific job titles and difficulty levels.
- **Comprehensive Rubric Evaluation**: Instant scoring across communication, technical depth, problem-solving, and relevance with actionable feedback reports.

### 📊 3. Interview Probability & Offer Predictor
- **Predictive Scoring Engine**: Multi-dimensional scoring assessing candidate competitiveness against real-world hiring criteria.
- **Hiring Persona Insights**: Visual breakdown of recruiter, hiring manager, and technical lead expectations with interactive radar charts.

### 🧭 4. Career Switcher & Skill Gap Planner
- **Target Role Roadmaps**: Step-by-step transition pathways calculating estimated time-to-hire, transferable skills, and critical skill deficits.
- **Structured Learning Milestones**: Actionable project recommendations and certification checkpoints to bridge identified gaps.

### 🤖 5. Interactive Career Coach Mascot
- **Dynamic State Machine**: Autonomous animated companion featuring distinct visual and behavioral states: `idle`, `listening`, `thinking`, `speaking`, and `celebration`.
- **Context-Aware AI Chatbot**: Real-time advice on salary negotiation, interview strategy, resume inquiries, and career dilemmas.

### 🐙 6. GitHub Portfolio & Developer Identity Analyzer
- **Codebase Evaluation**: Connects with public GitHub profiles to analyze repository quality, technology stack distribution, commit cadence, and architectural complexity.
- **Portfolio Generator**: Automatically highlights top projects with recruiter-ready summaries.

### 💼 7. Live Job Match Engine & Market Intelligence
- **Intelligent Job Matching**: Scans candidate profile attributes against active openings for accurate relevance matching.
- **Hiring & Tech News Radar**: Real-time RSS feeds monitoring tech industry expansions, layoffs, and hiring momentum.

### 📈 8. Goal Tracking & Community
- **Progress & Streaks**: Goal setting with milestone trackers, daily application logs, and visual streaks.
- **Community Hub**: Peer discussions, resume feedback boards, and shared career insights.

### ⚡ 9. Premium UX & Skeleton Loading Screens
- **Zero Layout Shift (CLS)**: Custom shimmer skeletons across all routes ensure lightning-fast perceived performance upon initial loads and state transitions.
- **Modern Dark Aesthetic**: Slate/obsidian backgrounds, subtle glassmorphism, fluid micro-interactions via Framer Motion & GSAP, and typography powered by Plus Jakarta Sans.

---

## 🧱 Tech Stack

### Frontend
| Component | Technology | Description |
|-----------|------------|-------------|
| **Framework** | [React 18](https://react.dev/) + [Vite 5](https://vitejs.dev/) | High-performance SPA with fast HMR |
| **Styling** | [TailwindCSS 3.4](https://tailwindcss.com/) | Curated dark-mode design system |
| **UI Primitives** | [Radix UI](https://www.radix-ui.com/) | Accessible dialogs, dropdowns, tabs, toasts |
| **Animations** | [Framer Motion 11](https://www.framer.com/motion/) + [GSAP 3](https://greensock.com/) | Page transitions and physics-based interactions |
| **Data Viz** | [Recharts](https://recharts.org/) | Radar, area, and bar charts for career analytics |
| **Voice** | Web Speech API | Native speech synthesis and voice recognition |
| **Icons** | [Lucide React](https://lucide.dev/) | Clean, consistent SVG icon set |

### Backend
| Component | Technology | Description |
|-----------|------------|-------------|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Asynchronous, high-throughput Python API |
| **Language** | Python 3.11+ | Modern type annotations and async execution |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Strict data schemas and request validation |
| **AI Engine** | [Google Gemini Pro / Flash](https://deepmind.google/technologies/gemini/) | Large language model for analysis, optimization & coaching |
| **PDF Parsing** | `PyMuPDF`, `pdfplumber`, `pytesseract` | Multi-engine PDF and OCR extraction |
| **Rate Limiting** | [SlowAPI](https://github.com/laurentS/slowapi) | IP-based endpoint throttling and abuse prevention |
| **Payments** | [Stripe](https://stripe.com/) | Subscription tier management and secure checkout |

### Database & Authentication
| Component | Technology | Description |
|-----------|------------|-------------|
| **Database** | [Supabase](https://supabase.com/) | Cloud-hosted PostgreSQL with Row Level Security (RLS) |
| **Auth** | Supabase Auth & JWT | Secure email/password and OAuth authentication |

---

## 📁 Project Architecture

```
career-lens/
├── frontend/                          # React 18 + Vite Frontend Application
│   ├── public/                        # Static assets, mascots, favicon
│   ├── src/
│   │   ├── components/                # Reusable UI widgets, modals, layout elements
│   │   │   ├── common/                # Buttons, Cards, Inputs, Shimmer Skeletons
│   │   │   ├── layout/                # Sidebar, Navbar, PageShell
│   │   │   └── ui/                    # Radix UI wrapped primitives
│   │   ├── context/                   # Global state (Auth, Theme, Notification)
│   │   ├── mascot/                    # Interactive Career Mascot state machine & UI
│   │   │   ├── Mascot.jsx             # Visual canvas & robot animations
│   │   │   └── useMascotState.js      # Behavioral state machine hook
│   │   ├── motion/                    # Framer Motion transition variants
│   │   ├── pages/                     # Application route views
│   │   │   ├── auth/                  # Login, Register, Forgot Password
│   │   │   ├── dashboard/             # Dashboard modules:
│   │   │   │   ├── ATSChecker.jsx           # Resume score & issues
│   │   │   │   ├── ResumeOptimizer.jsx      # Job-targeted AI optimizer
│   │   │   │   ├── MockInterview.jsx        # Voice AI interview room
│   │   │   │   ├── InterviewPredictor.jsx   # Odds & persona radar
│   │   │   │   ├── CareerSwitch.jsx         # Transition roadmaps
│   │   │   │   ├── CareerRecommendations.jsx# Targeted roles & paths
│   │   │   │   ├── JobMatchEngine.jsx       # Job matching engine
│   │   │   │   ├── Portfolio.jsx            # GitHub analysis
│   │   │   │   ├── TechNews.jsx             # Industry & hiring radar
│   │   │   │   ├── GoalTracker.jsx          # Milestones & streaks
│   │   │   │   ├── Community.jsx            # Discussion forums
│   │   │   │   ├── Chatbot.jsx              # AI assistant panel
│   │   │   │   └── Profile.jsx              # User settings & profile
│   │   │   └── Landing.jsx            # High-conversion glassmorphism landing page
│   │   ├── services/                  # Axios/Fetch API clients & interceptors
│   │   ├── styles/                    # Global CSS variables & Tailwind config
│   │   ├── App.jsx                    # Root router with Skeleton fallbacks
│   │   └── main.jsx                   # React DOM root & providers
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── backend/                           # FastAPI Python Backend
│   ├── routers/                       # Modular API router endpoints
│   │   ├── auth.py                    # Session validation & user context
│   │   ├── resume.py                  # Resume parsing & ATS analysis
│   │   ├── optimizer.py               # Job-description targeted rewrites & diffs
│   │   ├── interview.py               # Mock interview generation & audio evaluation
│   │   ├── interviewprobability.py    # Offer prediction & competency radar
│   │   ├── chatbot.py                 # Multi-turn conversational AI coach
│   │   ├── recommendations.py         # Career path recommendations
│   │   ├── github_identity.py         # GitHub API integration & repo parsing
│   │   ├── news.py                    # Real-time tech & hiring RSS aggregation
│   │   ├── community.py               # Forum posts, comments, likes
│   │   └── premium.py                 # Stripe checkout sessions & webhooks
│   ├── services/                      # Core business logic & AI prompts
│   │   ├── gemini_service.py          # Google Generative AI interface
│   │   ├── pdf_service.py             # PyMuPDF / pdfplumber parser
│   │   └── github_service.py          # GitHub user data extraction
│   ├── models/                        # Pydantic schemas for request/response typing
│   ├── middleware/                    # CORS, trusted hosts, rate limiting
│   ├── config.py                      # Environment configuration via Pydantic Settings
│   ├── main.py                        # FastAPI application entry point
│   ├── requirements.txt               # Backend dependencies
│   └── .env.example                   # Backend environment template
│
├── database/
│   ├── schema.sql                     # Supabase PostgreSQL schema with RLS policies
│   └── seed.sql                       # Sample seed data for development
│
├── docker/
│   ├── Dockerfile.frontend            # Multi-stage production build (Node + Nginx)
│   ├── Dockerfile.backend             # Lightweight Python 3.11 container
│   └── nginx.conf                     # Reverse proxy & gzip configuration
│
├── docker-compose.yml                 # Orchestration for frontend & backend services
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.11 or higher
- **Supabase Account**: (free tier works)
- **Google Gemini API Key**: [Get one here](https://aistudio.google.com/)
- **Docker & Docker Compose**: (Optional, for containerized run)

---

### Option A: Running with Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/career-lens.git
   cd career-lens
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` in both directories and provide your keys:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

3. **Launch Containers**:
   ```bash
   docker compose up --build
   ```
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **Interactive API Docs (Swagger)**: http://localhost:8000/docs

---

### Option B: Local Manual Setup (Development Mode)

#### 1. Database Setup (Supabase)
1. Create a project at [supabase.com](https://supabase.com).
2. Navigate to **SQL Editor** in your Supabase dashboard.
3. Open `database/schema.sql`, paste its content, and click **Run**.
4. Enable **Email / Password** under **Authentication > Providers**.
5. Retrieve your `Project URL`, `anon key`, and `service_role key` from **Project Settings > API**.

#### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload --port 8000
```

#### 3. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Start development server
npm run dev
```
Access the application at `http://localhost:3000`.

---

## 🔑 Environment Variables Reference

### Backend (`backend/.env`)
| Variable | Required | Description |
|----------|----------|-------------|
| `ENVIRONMENT` | Yes | `development` or `production` |
| `GEMINI_API_KEY` | Yes | Google Gemini API key from AI Studio |
| `SUPABASE_URL` | Yes | Your Supabase project URL (`https://xyz.supabase.co`) |
| `SUPABASE_KEY` | Yes | Supabase Service Role key (for backend admin operations) |
| `SECRET_KEY` | Yes | Random 32+ character string for JWT signature verification |
| `ALLOWED_ORIGINS` | Yes | Comma-separated CORS origins (e.g. `http://localhost:3000`) |
| `STRIPE_SECRET_KEY` | Optional | Stripe secret key for payment processing |
| `STRIPE_WEBHOOK_SECRET` | Optional | Stripe webhook secret for checkout verification |

### Frontend (`frontend/.env`)
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_SUPABASE_URL` | Yes | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Yes | Supabase Anonymous (public) key |
| `VITE_API_BASE_URL` | Yes | FastAPI backend URL (`http://localhost:8000`) |
| `VITE_STRIPE_PUBLISHABLE_KEY`| Optional | Stripe public key for checkout UI |

---

## 📡 Core API Endpoints

| Category | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| **Resume & ATS** | `POST` | `/api/resume/analyze` | Parse PDF/DOCX resume & calculate baseline score |
| | `GET` | `/api/resume/history` | Fetch historical resume analysis runs |
| **Optimizer** | `POST` | `/api/optimizer/tailor` | Generate JD-tailored resume with diffs & STAR rewrites |
| | `POST` | `/api/optimizer/export` | Export tailored resume as PDF/DOCX |
| **Mock Interview**| `POST` | `/api/interview/start` | Start interview session tailored to role & level |
| | `POST` | `/api/interview/evaluate` | Evaluate transcribed user response with scoring rubric |
| **Predictor** | `POST` | `/api/interview-probability/predict` | Compute offer probability & persona alignment radar |
| **Career Coach** | `POST` | `/api/chatbot/message` | Conversational query response from AI mentor |
| **GitHub** | `GET` | `/api/github/profile` | Analyze public repositories & developer skill tags |
| **News** | `GET` | `/api/news/tech` | Aggregated technology sector news |
| | `GET` | `/api/news/hiring` | Hiring surges, trends, and layoff reports |
| **Community** | `GET` | `/api/community/posts` | Retrieve community discussion posts & threads |
| | `POST` | `/api/community/posts` | Create a new community discussion post |

---

## 🎨 Design System & Aesthetics

- **Color Palette**: Dark obsidian (`#0b0f17`), slate card layers (`#111827`, `#1f2937`), highlighted with emerald accents (`#10b981`), cyber cyan (`#06b6d4`), and electric indigo.
- **Glassmorphism**: Backdrop blur with border stroke accents (`border-white/10`).
- **Typography**: Clean hierarchy with `@fontsource-variable/plus-jakarta-sans`.
- **Skeleton Loaders**: Integrated animated shimmer cards to eliminate Cumulative Layout Shift (CLS) and deliver instant tactile feedback during asynchronous operations.

---

## 🧪 Testing & Code Quality

```bash
# Frontend Linting
cd frontend
npm run lint

# Frontend Unit Tests
npm run test

# Backend Health Check
curl http://localhost:8000/health
```

---

## 🔒 Security & Best Practices

- **Zero-Storage of Sensitive Resumes**: Raw resume files are parsed in-memory and processed securely via Google Gemini without public data persistence.
- **Row Level Security (RLS)**: PostgreSQL tables enforce database-level access controls so users can only view their own resumes, analyses, and history.
- **Rate Limiting**: Critical AI endpoints use SlowAPI rate-limiting middleware to prevent quota exhaustion and DDoS attacks.
- **Defensive Headers**: Production headers include `nosniff`, `X-Frame-Options: DENY`, and strict CORS origin validation.

---

## 🤝 Contributing

Contributions are welcomed! Follow these steps:
1. **Fork** the repository.
2. Create a feature branch: `git checkout -b feature/amazing-feature`.
3. Commit your changes: `git commit -m 'feat: Add amazing feature'`.
4. Push to branch: `git push origin feature/amazing-feature`.
5. Open a **Pull Request**.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgements

- [Google DeepMind / Gemini](https://deepmind.google/technologies/gemini/) for high-speed generative intelligence.
- [Supabase](https://supabase.com/) for PostgreSQL database & authentication infrastructure.
- [FastAPI](https://fastapi.tiangolo.com/) & [Pydantic](https://docs.pydantic.dev/) for robust backend development.
- [TailwindCSS](https://tailwindcss.com/) & [Radix UI](https://www.radix-ui.com/) for modern UI components.
