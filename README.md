# 🔍 CareerLens – AI Resume Analyzer & Career Guidance Platform

> A production-ready full-stack web app that helps students and job seekers analyze their resumes and receive AI-driven career guidance.

---

## 🧱 Tech Stack

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| Frontend     | React (Vite), TailwindCSS, Framer Motion, ShadCN UI |
| Backend      | Python FastAPI                                  |
| Database     | Supabase (PostgreSQL + Supabase Auth)           |
| AI           | Google Gemini API                               |
| Voice        | Web Speech API                                  |
| APIs         | GitHub Public API, RSS/News APIs                |
| Deployment   | Docker, Docker Compose                          |

---

## 📁 Project Structure

```
career-lens/
├── frontend/                  # React + Vite app
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Route-based page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── context/           # Auth & global state
│   │   ├── services/          # API call helpers
│   │   ├── utils/             # Utility functions
│   │   └── styles/            # Global CSS / Tailwind config
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/                   # FastAPI app
│   ├── routers/               # API route modules
│   │   ├── auth.py
│   │   ├── resume.py
│   │   ├── interview.py
│   │   ├── chatbot.py
│   │   └── news.py
│   ├── services/              # Business logic & external APIs
│   │   ├── gemini_service.py
│   │   ├── github_service.py
│   │   └── pdf_service.py
│   ├── models/                # Pydantic models / DB schemas
│   ├── middleware/            # Auth middleware, CORS
│   ├── main.py                # FastAPI entry point
│   ├── config.py              # Settings & env vars
│   ├── requirements.txt
│   └── .env.example
│
├── database/
│   ├── schema.sql             # Supabase PostgreSQL schema
│   └── seed.sql               # Optional seed data
│
├── docker/
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   └── nginx.conf
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Supabase account
- Google Gemini API key
- GitHub account (for OAuth optional)

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourname/career-lens.git
cd career-lens
```

---

### 2. Configure Environment Variables

#### Backend
```bash
cp backend/.env.example backend/.env
# Fill in your keys in backend/.env
```

#### Frontend
```bash
cp frontend/.env.example frontend/.env
# Fill in your Supabase URL and anon key
```

---

### 3. Set Up Supabase

1. Create a new Supabase project at https://supabase.com
2. Go to **SQL Editor** and run `database/schema.sql`
3. Enable **Email Auth** under Authentication > Providers
4. Copy your **Project URL** and **anon key** into env files

---

### 4. Run with Docker (Recommended)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### 5. Run Locally (Dev Mode)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable              | Description                          |
|-----------------------|--------------------------------------|
| `SUPABASE_URL`        | Your Supabase project URL            |
| `SUPABASE_KEY`        | Supabase service role key            |
| `GEMINI_API_KEY`      | Google Gemini API key                |
| `SECRET_KEY`          | JWT secret for session tokens        |
| `ALLOWED_ORIGINS`     | CORS origins (e.g. http://localhost:3000) |

### Frontend (`frontend/.env`)

| Variable                    | Description                    |
|-----------------------------|--------------------------------|
| `VITE_SUPABASE_URL`         | Supabase project URL           |
| `VITE_SUPABASE_ANON_KEY`    | Supabase anon (public) key     |
| `VITE_API_BASE_URL`         | Backend FastAPI URL            |

---

## 🧠 Core Features

| Feature                  | Freemium | Premium |
|--------------------------|----------|---------|
| Resume Analysis          | 1x       | ∞       |
| Mock Interviews          | 1x       | ∞       |
| AI Chatbot               | Limited  | ∞       |
| ATS Checker              | ❌       | ✅      |
| Cover Letter Generator   | ❌       | ✅      |
| Skill Gap Analyzer       | ❌       | ✅      |
| Portfolio Generator      | ❌       | ✅      |
| Job Match Engine         | ❌       | ✅      |
| GitHub Project Analyzer  | ❌       | ✅      |
| AI Mentor (Weekly Plan)  | ❌       | ✅      |

---

## 🧪 API Endpoints

| Method | Endpoint                        | Description                     |
|--------|---------------------------------|---------------------------------|
| POST   | `/api/resume/analyze`           | Run full resume analysis        |
| GET    | `/api/resume/history`           | Get user's past analyses        |
| POST   | `/api/interview/start`          | Start mock interview session    |
| POST   | `/api/interview/evaluate`       | Evaluate interview transcript   |
| POST   | `/api/chatbot/message`          | Send message to AI chatbot      |
| GET    | `/api/news/tech`                | Get latest tech news            |
| GET    | `/api/news/hiring`              | Get hiring/layoff news          |
| GET    | `/api/github/profile`           | Fetch GitHub profile data       |

---

## 🎨 Design System

- **Theme**: Dark mode default
- **Primary**: Indigo → Purple gradient (`#6366f1` → `#9333ea`)
- **Accent**: Neon blue (`#22d3ee`)
- **Background**: Dark slate (`#0f172a`)
- **Cards**: Glassmorphism with backdrop blur
- **Animations**: Framer Motion page transitions + micro-interactions

---

## 🐳 Docker

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down
```

---

## 📦 Deployment

### Recommended Platforms
- **Frontend**: Vercel / Netlify
- **Backend**: Railway / Render / AWS EC2
- **Database**: Supabase (managed)

### Vercel (Frontend)
```bash
cd frontend
vercel deploy
```

### Railway (Backend)
```bash
cd backend
railway up
```

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙌 Acknowledgements

- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [Supabase](https://supabase.com)
- [FastAPI](https://fastapi.tiangolo.com)
- [ShadCN UI](https://ui.shadcn.com)
- [Framer Motion](https://www.framer.com/motion/)
