# ============================================================
# CareerLens – FastAPI Backend Entry Point
# File: backend/main.py
# ============================================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from config import settings
from routers import auth, resume, interview, chatbot, news, github, premium, beginner, portfolio

# ============================================================
# Logging Setup
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("careerlens")


# ============================================================
# Lifespan: Startup & Shutdown Events
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown logic."""
    logger.info("🚀 CareerLens API starting up...")
    logger.info(f"   Environment : {settings.ENVIRONMENT}")
    logger.info(f"   Allowed origins: {settings.ALLOWED_ORIGINS}")
    yield
    logger.info("🛑 CareerLens API shutting down...")


# ============================================================
# FastAPI App Initialization
# ============================================================

app = FastAPI(
    title="CareerLens API",
    description=(
        "AI-powered Resume Analyzer & Career Guidance Platform. "
        "Analyze resumes, run mock interviews, get AI career coaching."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================
# Middleware
# ============================================================

# CORS – allow frontend origin(s)
dev_origin_regex = (
    r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+)(:\d+)?$"
    if settings.ENVIRONMENT != "production"
    else None
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=dev_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host protection (disable in dev if needed)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )


# ============================================================
# Request Timing Middleware
# Logs every request with method, path, status, and duration
# ============================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} [{duration}ms]"
    )
    return response


# ============================================================
# Global Exception Handler
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error. Please try again later.",
        },
    )


# ============================================================
# Routers – all prefixed under /api
# ============================================================

app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(resume.router,    prefix="/api/resume",    tags=["Resume Analysis"])
app.include_router(interview.router, prefix="/api/interview", tags=["Mock Interview"])
app.include_router(chatbot.router,   prefix="/api/chatbot",   tags=["Honest Career Coach"])
app.include_router(news.router,      prefix="/api/news",      tags=["News"])
app.include_router(github.router,    prefix="/api/github",    tags=["GitHub"])
app.include_router(premium.router,   prefix="/api/premium",   tags=["Premium / Payments"])
app.include_router(beginner.router, prefix="/api/beginner", tags=["Beginner"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])

# ============================================================
# Root & Health Check Endpoints
# ============================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint – confirms API is live."""
    return {
        "success": True,
        "message": "CareerLens API is running 🚀",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Used by Docker, load balancers, and monitoring tools.
    """
    return {
        "success": True,
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api", tags=["Health"])
async def api_index():
    """Lists all available API route groups."""
    return {
        "success": True,
        "available_routes": [
            "/api/auth      – Authentication (login, signup, profile)",
            "/api/resume    – Resume upload & AI analysis",
            "/api/interview – Mock interview sessions",
            "/api/chatbot   – Honest Career Coach",
            "/api/news      – Tech & hiring news",
            "/api/github    – GitHub profile analysis",
            "/api/premium   – Upgrade & payment",
            "/api/beginner  – Beginner learning roadmap",
            "/api/portfolio – Portfolio generator",
        ],
    }

from routers import recommendations
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])

from routers import community
app.include_router(community.router, prefix="/api/community", tags=["Community"])

from routers import interview_probability
app.include_router(interview_probability.router, prefix="/api/interview-probability", tags=["Interview Probability"])
#=====================================================
from routers import optimizer, job_match
app.include_router(optimizer.router,  prefix="/api/optimizer",  tags=["Optimizer"])
app.include_router(job_match.router,  prefix="/api/job-match",  tags=["Job Match"])
