# ============================================================
# CareerLens - Mock Interview Router
# File: backend/routers/interview.py
# ============================================================

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from middleware.auth import get_authenticated_user, get_user_profile
from services.gemini_service import generate_interview_questions, evaluate_interview
from services.interview_question_bank import get_question_bank_for_role
from database import supabase
from config import settings
import logging
import random
import re
import uuid

logger = logging.getLogger("careerlens.interview")
router = APIRouter()

DEFAULT_QUESTION_COUNT = 8
MIN_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 10

# ============================================================
# Company DNA Profiles
# The AI uses these to generate questions that feel authentic
# to each company's real interview culture and patterns.
# ============================================================
COMPANY_PROFILES: dict[str, dict] = {
    "google": {
        "full_name": "Google",
        "focus_areas": [
            "system design at scale", "algorithms and data structures",
            "distributed systems", "Googleyness and culture fit",
            "why Google", "ambiguous problem solving",
        ],
        "interview_style": (
            "Open-ended questions with no single right answer. Interviewers expect "
            "candidates to think aloud, explore trade-offs, and drive the conversation. "
            "They push back to test depth — a good answer leads to a harder follow-up."
        ),
        "behavioral_framework": "no strict framework — prefer concrete examples with data",
        "known_rounds": ["coding x2", "system design", "behavioral/Googleyness", "hiring committee"],
        "signature_themes": [
            "design Gmail/Maps/YouTube from scratch",
            "scale to 1 billion users",
            "what happens when you type a URL",
            "why Google over other FAANG",
            "a time you disagreed with a manager",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "amazon": {
        "full_name": "Amazon",
        "focus_areas": [
            "all 16 Leadership Principles", "customer obsession", "ownership",
            "dive deep", "deliver results", "invent and simplify",
            "behavioral STAR stories", "bar-raiser round",
        ],
        "interview_style": (
            "Extremely behavioral-heavy. Every question maps to a Leadership Principle. "
            "Interviewers explicitly look for STAR-format answers with specific metrics and outcomes. "
            "Vague or hypothetical answers are penalized. The bar-raiser may probe aggressively."
        ),
        "behavioral_framework": "STAR (Situation, Task, Action, Result) — metrics required in Result",
        "known_rounds": ["behavioral x4 (each LP-mapped)", "coding x2", "bar raiser"],
        "signature_themes": [
            "Tell me about a time you failed and what you learned",
            "Describe a project where you had to make a decision with incomplete data",
            "A time you disagreed with your team and how it resolved",
            "How do you prioritize when everything is urgent",
            "Most complex technical problem you've owned end-to-end",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 16,
    },
    "microsoft": {
        "full_name": "Microsoft",
        "focus_areas": [
            "growth mindset", "problem solving approach", "collaboration and culture fit",
            "system design", "coding fundamentals", "why Microsoft",
        ],
        "interview_style": (
            "Collaborative tone — interviewers often hint when stuck rather than letting silence linger. "
            "They care about HOW you think as much as whether you get the answer. "
            "Culture questions focus on growth mindset and learning from failure."
        ),
        "behavioral_framework": "STAR encouraged but not as rigid as Amazon",
        "known_rounds": ["coding x3", "system design x1", "hiring manager culture fit"],
        "signature_themes": [
            "Design a feature for an existing Microsoft product",
            "How would you improve Microsoft Teams",
            "A time you had to learn something completely new fast",
            "Describe a project you are most proud of",
            "How do you handle feedback you disagree with",
        ],
        "difficulty": "medium-hard",
        "behavioral_lp_count": 0,
    },
    "meta": {
        "full_name": "Meta (Facebook)",
        "focus_areas": [
            "product sense", "move fast culture", "data structures at scale",
            "system design for social graphs", "impact and metrics",
            "cross-functional collaboration",
        ],
        "interview_style": (
            "Product and impact-focused. Even engineering roles get product sense questions. "
            "They want candidates who think in terms of user impact and business metrics. "
            "Coding is fast-paced — they expect clean code quickly."
        ),
        "behavioral_framework": "impact-driven — always tie answers back to measurable outcomes",
        "known_rounds": ["coding x2", "system design x1", "behavioral x1", "product sense x1"],
        "signature_themes": [
            "Design Facebook's news feed ranking algorithm",
            "How would you detect fake accounts at scale",
            "Design Instagram Stories",
            "A time you shipped something fast and broke something",
            "How do you measure the success of a feature",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "apple": {
        "full_name": "Apple",
        "focus_areas": [
            "deep technical expertise", "attention to detail", "product quality obsession",
            "system design for consumer hardware/software", "privacy by design",
            "why Apple specifically",
        ],
        "interview_style": (
            "Deeply technical — Apple interviewers go very deep on fundamentals. "
            "They value polish and precision over speed. Expect follow-ups that push you "
            "to the edge of your knowledge. Strong emphasis on past project ownership."
        ),
        "behavioral_framework": "no strict framework — focus on ownership and craft",
        "known_rounds": ["technical deep dives x3", "design x1", "hiring manager"],
        "signature_themes": [
            "Design a feature for iOS without mentioning existing ones",
            "How would you handle a privacy-sensitive data pipeline",
            "Your most technically challenging bug and how you fixed it",
            "Design a caching system for a low-latency mobile app",
            "Why Apple and not Google or Meta",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "netflix": {
        "full_name": "Netflix",
        "focus_areas": [
            "freedom and responsibility culture", "context not control",
            "highly aligned loosely coupled teams", "chaos engineering mindset",
            "senior ownership", "data-driven decisions",
        ],
        "interview_style": (
            "Netflix only hires senior people who need no hand-holding. "
            "They probe for radical candor, independent decision making, and "
            "whether you align with their 'keeper test' culture. "
            "Technical rounds go very deep into distributed systems and reliability."
        ),
        "behavioral_framework": "context-not-control — explain your decision framework, not just actions",
        "known_rounds": ["culture fit x2 (very important)", "system design x2", "coding x1"],
        "signature_themes": [
            "Design Netflix's recommendation system",
            "How would you handle a global CDN outage during a major show launch",
            "Tell me about a time you had to give or receive very direct feedback",
            "Design a system that handles 200 million concurrent streams",
            "Would you rather move fast and break things or move slow and be safe — why",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "uber": {
        "full_name": "Uber",
        "focus_areas": [
            "real-time systems", "geo-spatial problem solving", "marketplace dynamics",
            "backend scalability", "driver-rider matching algorithms", "reliability under load",
        ],
        "interview_style": (
            "Practical and product-aware. They expect candidates to reason about real-world "
            "constraints: latency, GPS accuracy, surge pricing logic. "
            "System design often revolves around marketplace or location-based scenarios."
        ),
        "behavioral_framework": "situation + outcome with emphasis on scale and speed",
        "known_rounds": ["coding x2", "system design x2", "hiring manager"],
        "signature_themes": [
            "Design Uber's surge pricing engine",
            "How do you match 500,000 ride requests to drivers in real time",
            "Design a real-time ETA prediction system",
            "A time you optimized a system under production pressure",
            "How would you detect fraudulent trips",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "stripe": {
        "full_name": "Stripe",
        "focus_areas": [
            "financial systems reliability", "API design", "payments infrastructure",
            "correctness over speed", "idempotency and consistency",
            "developer experience thinking",
        ],
        "interview_style": (
            "Writing-focused culture — Stripe values clear written communication. "
            "System design focuses heavily on correctness, idempotency, and financial safety. "
            "They probe deeply on edge cases. Expect 'what could go wrong' follow-ups constantly."
        ),
        "behavioral_framework": "clear decision rationale with trade-offs explicitly stated",
        "known_rounds": ["coding x2", "system design x2", "writing exercise", "culture fit"],
        "signature_themes": [
            "Design a payment processing system that never double-charges",
            "How do you handle idempotency in a distributed payments API",
            "Design Stripe's webhook delivery system",
            "How would you build fraud detection for online transactions",
            "A time you caught a critical bug before it reached production",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "flipkart": {
        "full_name": "Flipkart",
        "focus_areas": [
            "e-commerce systems at Indian scale", "supply chain optimization",
            "search and recommendation", "checkout and payments flow",
            "warehouse and logistics tech", "Big Billion Days scale",
        ],
        "interview_style": (
            "Mix of algorithmic coding and practical system design rooted in e-commerce. "
            "They value candidates who understand India-specific constraints: "
            "low-bandwidth users, COD payments, vernacular language support, tier-2/3 city logistics."
        ),
        "behavioral_framework": "STAR with India market context appreciated",
        "known_rounds": ["coding x2", "system design x1", "HM round"],
        "signature_themes": [
            "Design Flipkart's product search with filters at scale",
            "How would you handle 10 million concurrent users on Big Billion Days",
            "Design a delivery ETA system for India's last-mile delivery challenges",
            "How would you build a real-time inventory management system",
            "Optimize the checkout funnel for low-bandwidth mobile users",
        ],
        "difficulty": "medium-hard",
        "behavioral_lp_count": 0,
    },
    "swiggy": {
        "full_name": "Swiggy",
        "focus_areas": [
            "hyperlocal delivery systems", "real-time order tracking",
            "restaurant discovery and search", "dynamic pricing for delivery",
            "fleet management and route optimization", "dark store logistics",
        ],
        "interview_style": (
            "Product-aware engineering culture. Questions are grounded in food-tech "
            "and hyperlocal delivery realities. They value candidates who can reason "
            "about user experience alongside backend complexity."
        ),
        "behavioral_framework": "outcome + user impact framing",
        "known_rounds": ["coding x2", "system design x1", "product/behavioral x1"],
        "signature_themes": [
            "Design Swiggy's real-time order tracking system",
            "How do you assign delivery executives to orders optimally",
            "Design a restaurant recommendation engine using location + history",
            "Handle a sudden 10x spike in orders during IPL finals",
            "How would you design Swiggy Instamart's 10-minute delivery promise",
        ],
        "difficulty": "medium-hard",
        "behavioral_lp_count": 0,
    },
    "zomato": {
        "full_name": "Zomato",
        "focus_areas": [
            "food discovery and reviews", "restaurant partner tools",
            "delivery routing and ETA", "user retention and engagement",
            "multi-city expansion tech", "live order management",
        ],
        "interview_style": (
            "Startup-flavoured despite scale — they value hustle, pragmatism, and "
            "shipping fast. System design questions often include 'how fast can you ship an MVP.' "
            "Strong product sense is expected from engineers."
        ),
        "behavioral_framework": "impact + learning — what did you ship and what did you learn",
        "known_rounds": ["coding x1-2", "system design x1", "culture + product fit x1"],
        "signature_themes": [
            "Design Zomato's restaurant discovery feed",
            "How would you reduce food delivery cancellations",
            "Build a live order tracking system under 1 second latency",
            "Design the review and rating system to prevent fake reviews",
            "How would you help restaurants manage peak hour demand",
        ],
        "difficulty": "medium",
        "behavioral_lp_count": 0,
    },
    "infosys": {
        "full_name": "Infosys",
        "focus_areas": [
            "core programming fundamentals", "OOPS and design patterns",
            "database queries and optimization", "client communication skills",
            "agile methodology", "problem solving approach",
        ],
        "interview_style": (
            "Structured and process-oriented. Questions test breadth rather than depth. "
            "Behavioral questions focus on teamwork, client handling, and process adherence. "
            "Clear communication is valued over raw algorithmic brilliance."
        ),
        "behavioral_framework": "STAR with emphasis on teamwork and process",
        "known_rounds": ["aptitude/verbal", "coding test", "technical interview x1-2", "HR round"],
        "signature_themes": [
            "Explain OOPS concepts with real-world examples",
            "Write a SQL query for a complex join scenario",
            "How would you handle a difficult client situation",
            "Describe your approach when you receive unclear requirements",
            "Explain the software development lifecycle",
        ],
        "difficulty": "medium",
        "behavioral_lp_count": 0,
    },
    "tcs": {
        "full_name": "TCS (Tata Consultancy Services)",
        "focus_areas": [
            "programming basics in any language", "logical and aptitude reasoning",
            "database and SQL fundamentals", "verbal and communication skills",
            "adaptability and client-service mindset",
        ],
        "interview_style": (
            "Broad-based — designed to assess fresh graduates and lateral hires across "
            "many technologies. Less deep than product companies. Strong emphasis on "
            "attitude, learning agility, and communication over specific tech stack."
        ),
        "behavioral_framework": "situation + action + result — keep it simple and clear",
        "known_rounds": ["TCS NQT/written test", "technical interview", "managerial round", "HR round"],
        "signature_themes": [
            "Write a program to reverse a string without using built-in functions",
            "Explain normalization in databases",
            "How do you stay up-to-date with technology",
            "Where do you see yourself in 5 years at TCS",
            "Describe a group project and your specific contribution",
        ],
        "difficulty": "easy-medium",
        "behavioral_lp_count": 0,
    },
    "startup": {
        "full_name": "Early-Stage Startup",
        "focus_areas": [
            "full-stack ownership", "ship fast with minimal resources",
            "product thinking for engineers", "dealing with ambiguity",
            "wearing multiple hats", "customer empathy",
        ],
        "interview_style": (
            "Informal and conversational. They care more about whether you can own things "
            "end-to-end than passing algorithmic puzzles. Expect questions about past projects "
            "in detail, your opinions on product decisions, and how you handle chaos."
        ),
        "behavioral_framework": "storytelling — what you built, why, and what you would do differently",
        "known_rounds": ["take-home project", "technical discussion", "founder/culture fit"],
        "signature_themes": [
            "Walk me through the last thing you built from scratch",
            "How do you decide what to work on when everything is priority 1",
            "What is a product decision at a previous company you would have made differently",
            "How do you handle technical debt when moving fast",
            "What do you do when you disagree with a product decision",
        ],
        "difficulty": "medium",
        "behavioral_lp_count": 0,
    },
    "general": {
        "full_name": "General / No Specific Company",
        "focus_areas": [
            "core technical skills for the role", "problem solving",
            "communication and clarity", "past project experience",
            "team collaboration",
        ],
        "interview_style": "Standard industry interview covering technical depth, behavioral scenarios, and cultural fit.",
        "behavioral_framework": "STAR",
        "known_rounds": ["technical x2", "behavioral x1", "hiring manager"],
        "signature_themes": [],
        "difficulty": "medium",
        "behavioral_lp_count": 0,
    },
    # ── AI Companies ────────────────────────────────────────────────────────────
    "openai": {
        "full_name": "OpenAI",
        "focus_areas": [
            "LLM architecture and training", "RLHF and alignment techniques",
            "distributed training at scale", "AI safety and responsible deployment",
            "Python and PyTorch deep expertise", "research engineering",
        ],
        "interview_style": (
            "Research-heavy and deeply technical. They test both engineering rigour and "
            "conceptual ML understanding. Expect questions that blur the line between "
            "research and production. They care deeply about AI safety reasoning."
        ),
        "behavioral_framework": "impact + research contribution — what did you ship and what did it advance",
        "known_rounds": ["ML fundamentals x2", "coding x2", "system design for ML", "research discussion"],
        "signature_themes": [
            "Implement backpropagation from scratch",
            "How would you fine-tune GPT for a specific domain safely",
            "Design a scalable inference pipeline for a 70B parameter model",
            "How do you detect and mitigate hallucinations in production LLMs",
            "Explain RLHF — what are its failure modes",
            "Write a transformer attention mechanism in PyTorch",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "anthropic": {
        "full_name": "Anthropic",
        "focus_areas": [
            "AI safety and Constitutional AI", "interpretability research",
            "RLHF and alignment", "LLM evaluation and red-teaming",
            "Python and ML engineering", "responsible scaling policy",
        ],
        "interview_style": (
            "Mission-driven and safety-first. Anthropic probes whether you genuinely care "
            "about AI safety — not as a checkbox but philosophically. Technical rounds are "
            "rigorous: deep ML theory, alignment reasoning, and failure mode analysis."
        ),
        "behavioral_framework": "mission alignment + technical depth — why safety matters to you personally",
        "known_rounds": ["ML + coding x2", "system design", "alignment/safety discussion", "values interview"],
        "signature_themes": [
            "What are the biggest risks of deploying frontier AI models",
            "Implement a simple Constitutional AI training loop",
            "How would you evaluate whether a model is aligned with human values",
            "Design an evaluation suite to detect deceptive behaviour in LLMs",
            "Write code to implement a basic RLHF reward model training loop",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "xai": {
        "full_name": "xAI (Elon Musk)",
        "focus_areas": [
            "frontier model development", "maximum compute efficiency",
            "systems programming for ML", "real-time inference at scale",
            "first-principles reasoning", "move extremely fast",
        ],
        "interview_style": (
            "Extremely high bar, first-principles focused. xAI values raw intelligence and "
            "speed. Expect to reason from scratch on hard problems very fast. "
            "Interviews are intense and unstructured."
        ),
        "behavioral_framework": "first principles — explain WHY from scratch, not just WHAT",
        "known_rounds": ["hard algorithmic coding x2", "ML systems design", "founder interview"],
        "signature_themes": [
            "Implement a key attention optimization from scratch",
            "How would you build real-time inference for a 100B parameter model on limited hardware",
            "Design Grok's search-augmented LLM architecture",
            "What is the most important unsolved problem in AI right now",
            "Optimize a transformer inference kernel for speed",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "deepmind": {
        "full_name": "Google DeepMind",
        "focus_areas": [
            "reinforcement learning", "scientific AI applications",
            "ML theory and proofs", "Python and JAX",
            "research engineering at scale", "AlphaFold-style problems",
        ],
        "interview_style": (
            "Academically rigorous — DeepMind hires researchers who can also engineer. "
            "Deep RL theory, optimization, and scientific reasoning expected. "
            "Expect proofs, algorithm analysis, and paper discussions."
        ),
        "behavioral_framework": "research contribution — what novel insight did you produce",
        "known_rounds": ["ML theory x2", "coding x2", "research presentation", "system design"],
        "signature_themes": [
            "Implement Q-learning and explain its convergence guarantees",
            "Design a reward shaping strategy for a sparse-reward RL environment",
            "Prove why gradient descent converges for a convex loss function",
            "Write JAX code for a custom neural network layer with JIT compilation",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "mistral": {
        "full_name": "Mistral AI",
        "focus_areas": [
            "efficient LLM architectures", "sparse models and MoE",
            "open-source model development", "inference optimization",
            "Python and C++ for ML", "European AI compliance",
        ],
        "interview_style": (
            "Lean, fast-moving startup. They value engineers who do a lot with very little. "
            "Deep understanding of model architecture trade-offs is key."
        ),
        "behavioral_framework": "efficiency + impact — what did you build and how efficient was it",
        "known_rounds": ["ML coding x2", "architecture design", "technical discussion"],
        "signature_themes": [
            "Explain Mixture of Experts architecture and its training challenges",
            "How would you reduce KV cache memory for long-context inference",
            "Implement grouped-query attention in Python",
            "Design a model serving system handling 10k req/s at <100ms p99",
        ],
        "difficulty": "hard",
        "behavioral_lp_count": 0,
    },
    "cohere": {
        "full_name": "Cohere",
        "focus_areas": [
            "enterprise NLP and RAG systems", "embeddings and semantic search",
            "fine-tuning for business use cases", "production ML pipelines",
            "API product engineering", "multilingual models",
        ],
        "interview_style": (
            "Enterprise-focused and practical. Expect RAG, embeddings, evaluation pipelines, "
            "and production reliability questions — less theory, more applied engineering."
        ),
        "behavioral_framework": "customer value + reliability — what business problem did you solve",
        "known_rounds": ["coding x2", "ML system design", "product engineering discussion"],
        "signature_themes": [
            "Design a RAG pipeline for a Fortune 500 internal knowledge base",
            "How do you evaluate embedding quality for semantic search",
            "Build a fine-tuning pipeline that prevents catastrophic forgetting",
            "Design a reliable LLM API with rate limiting and fallbacks",
        ],
        "difficulty": "medium-hard",
        "behavioral_lp_count": 0,
    },
    "huggingface": {
        "full_name": "Hugging Face",
        "focus_areas": [
            "open-source ML tooling", "Transformers library internals",
            "model hub and dataset management", "developer experience",
            "Python", "democratising AI",
        ],
        "interview_style": (
            "Open-source culture — developer experience first. Collaborative and pragmatic. "
            "They care whether you'd be a good open-source citizen."
        ),
        "behavioral_framework": "community impact — how did you make AI more accessible",
        "known_rounds": ["coding x2", "technical discussion", "open-source contribution review"],
        "signature_themes": [
            "Design a Trainer class feature that does not break 10,000 existing users",
            "Implement a custom dataset class using the datasets library",
            "What are the hardest challenges in serializing ML models at scale",
            "Write a custom pipeline for a multimodal model",
        ],
        "difficulty": "medium-hard",
        "behavioral_lp_count": 0,
    },
}



class StartInterviewRequest(BaseModel):
    job_role: str
    company: str = "general"
    mode: str = "text"  # text | voice
    skills: list[str] = Field(default_factory=list)
    github_projects: list[str] = Field(default_factory=list)
    question_count: int = DEFAULT_QUESTION_COUNT


class EvaluateRequest(BaseModel):
    session_id: str
    transcript: list[dict]  # [{question, answer}, ...]


def _clamp_question_count(value: int) -> int:
    return max(MIN_QUESTION_COUNT, min(MAX_QUESTION_COUNT, int(value)))


def _question_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _clean_string_list(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = re.sub(r"\s+", " ", str(value or "").strip())
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned


VALID_CATEGORIES = {
    "technical", "behavioral", "situational",
    "code_fix", "code_write", "debugging", "error_handling",
}

CODING_CATEGORIES = {"code_fix", "code_write", "debugging", "error_handling"}


def _normalize_question(item: dict | str, fallback_id: int) -> dict | None:
    if isinstance(item, str):
        question_text = item.strip()
        if not question_text:
            return None
        return {
            "id": fallback_id,
            "question": question_text,
            "category": "technical",
            "difficulty": "medium",
            "expected_points": [],
            "code_snippet": None,
            "language": None,
        }

    if not isinstance(item, dict):
        return None

    question_text = str(item.get("question", "")).strip()
    if not question_text:
        return None

    category = str(item.get("category") or "technical").strip().lower()
    if category not in VALID_CATEGORIES:
        category = "technical"

    difficulty = str(item.get("difficulty") or "medium").strip().lower()
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"

    expected_points = item.get("expected_points") or []
    if not isinstance(expected_points, list):
        expected_points = []
    expected_points = [str(point).strip() for point in expected_points if str(point).strip()][:4]

    # Code fields — only present on coding question types
    code_snippet = None
    language = None
    if category in CODING_CATEGORIES:
        raw_snippet = item.get("code_snippet") or item.get("code") or ""
        code_snippet = str(raw_snippet).strip() or None
        raw_lang = item.get("language") or "python"
        language = str(raw_lang).strip().lower() or "python"

    return {
        "id": fallback_id,
        "question": question_text,
        "category": category,
        "difficulty": difficulty,
        "expected_points": expected_points,
        "code_snippet": code_snippet,
        "language": language,
    }


def _dedupe_questions(questions: list[dict | str]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()

    for i, item in enumerate(questions, start=1):
        question = _normalize_question(item, i)
        if not question:
            continue
        key = _question_key(question["question"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(question)

    return deduped


def _session_signature(questions: list[dict]) -> tuple[str, ...]:
    keys = sorted({_question_key(str(q.get("question", ""))) for q in questions if q.get("question")})
    return tuple(keys)


def _extract_github_username(github_url: str | None) -> str:
    if not github_url:
        return ""
    parts = [p for p in str(github_url).strip().rstrip("/").split("/") if p]
    return parts[-1] if parts else ""


def _build_company_context(company_key: str) -> str:
    """
    Builds a rich company context string injected into the AI prompt.
    This is what makes questions feel authentically company-specific.
    """
    profile = COMPANY_PROFILES.get(company_key.lower(), COMPANY_PROFILES["general"])

    lines = [
        f"TARGET COMPANY: {profile['full_name']}",
        f"INTERVIEW DIFFICULTY: {profile['difficulty']}",
        "",
        f"COMPANY INTERVIEW STYLE: {profile['interview_style']}",
        "",
        f"FOCUS AREAS THIS COMPANY TESTS: {', '.join(profile['focus_areas'])}",
        "",
        f"BEHAVIORAL FRAMEWORK EXPECTED: {profile['behavioral_framework']}",
        "",
        f"INTERVIEW ROUNDS AT THIS COMPANY: {', '.join(profile['known_rounds'])}",
    ]

    if profile.get("behavioral_lp_count"):
        lines += [
            "",
            f"NOTE: This company has {profile['behavioral_lp_count']} Leadership Principles. "
            "At least 2-3 questions must map to specific principles like Ownership, "
            "Customer Obsession, Invent and Simplify, Dive Deep, Deliver Results.",
        ]

    if profile.get("signature_themes"):
        lines += [
            "",
            "SIGNATURE QUESTION THEMES AT THIS COMPANY (generate questions inspired by these patterns):",
        ]
        for theme in profile["signature_themes"]:
            lines.append(f"  - {theme}")

    lines += [
        "",
        "CODING QUESTION REQUIREMENTS — include at least 2 of the following per session:",
        "Use one of these categories for each coding question:",
        "  code_fix       — provide a broken function with a real bug; ask candidate to fix it.",
        "  code_write     — describe a problem clearly; ask candidate to write a solution.",
        "  debugging      — show code with a runtime/logic error; ask candidate to find and fix it.",
        "  error_handling — show code that crashes on edge cases; ask candidate to add error handling.",
        "",
        "For code_fix, debugging, error_handling: include a 'code_snippet' field with 8-20 lines",
        "of realistic buggy/incomplete code in the most relevant language for the role.",
        "Also set 'language' field (python, javascript, typescript, java, etc).",
        "For code_write: code_snippet can be null — just provide a clear problem statement.",
        "",
        "CRITICAL: Return every question as a JSON object with these fields:",
        "  question (string), category (string), difficulty (easy|medium|hard),",
        "  expected_points (array of strings), code_snippet (string or null), language (string or null).",
        "",
        "CRITICAL INSTRUCTION: Generate questions that feel genuinely asked "
        f"by a {profile['full_name']} interviewer. Mirror their exact tone, depth, and focus. "
        f"Do NOT use generic questions — every question must feel specific to {profile['full_name']}.",
    ]

    return "\n".join(lines)


def _load_candidate_context(user_id: str, skills: list[str], github_projects: list[str]) -> tuple[list[str], list[str]]:
    merged_skills = list(skills or [])
    merged_projects = list(github_projects or [])

    try:
        latest_analysis = (
            supabase.table("resume_analyses")
            .select("results_json,github_url")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        logger.warning(f"Could not read latest resume analysis for interview context: {e}")
        latest_analysis = None

    analysis_row = latest_analysis.data[0] if latest_analysis and latest_analysis.data else {}
    results_json = analysis_row.get("results_json") or {}

    for key in ("strengths", "missing_skills", "top_keywords_missing"):
        values = results_json.get(key) or []
        if isinstance(values, list):
            merged_skills.extend([str(v) for v in values])

    suggested_projects = results_json.get("suggested_projects") or []
    if isinstance(suggested_projects, list):
        for project in suggested_projects[:5]:
            if isinstance(project, dict):
                title = str(project.get("title") or "").strip()
                if title:
                    merged_projects.append(title)

    github_username = _extract_github_username(analysis_row.get("github_url"))
    if github_username:
        try:
            github_cache = (
                supabase.table("github_cache")
                .select("repos_data,languages_data")
                .eq("github_username", github_username)
                .limit(1)
                .execute()
            )
            if github_cache.data:
                cached = github_cache.data[0]
                repos_data = cached.get("repos_data") or []
                if isinstance(repos_data, list):
                    for repo in repos_data[:6]:
                        if isinstance(repo, dict):
                            repo_name = str(repo.get("name") or "").strip()
                            if repo_name:
                                merged_projects.append(repo_name)

                languages_data = cached.get("languages_data") or {}
                if isinstance(languages_data, dict):
                    merged_skills.extend([str(lang) for lang in languages_data.keys()])
        except Exception as e:
            logger.warning(f"Could not read github_cache for interview context: {e}")

    return _clean_string_list(merged_skills), _clean_string_list(merged_projects)


async def _build_randomized_questions(
    user_id: str,
    job_role: str,
    company: str,
    skills: list[str],
    github_projects: list[str],
    question_count: int,
) -> list[dict]:
    pool: list[dict | str] = []
    company_context = _build_company_context(company)

    # Dynamic AI questions with company context injected; fallback to bank if AI fails.
    try:
        ai_questions = await generate_interview_questions(
            job_role=job_role,
            skills=skills,
            github_projects=github_projects,
            question_count=max(question_count, DEFAULT_QUESTION_COUNT),
            company_context=company_context,
        )
        pool.extend(ai_questions)
    except Exception as e:
        logger.warning(f"AI question generation failed, using question bank fallback: {e}")

    pool.extend(get_question_bank_for_role(job_role))
    deduped_pool = _dedupe_questions(pool)
    if not deduped_pool:
        raise HTTPException(status_code=500, detail="Could not generate interview questions.")

    previous_signature: tuple[str, ...] = tuple()
    try:
        previous = (
            supabase.table("interview_sessions")
            .select("questions")
            .eq("user_id", user_id)
            .eq("job_role", job_role)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if previous.data:
            previous_questions = _dedupe_questions(previous.data[0].get("questions") or [])
            previous_signature = _session_signature(previous_questions)
    except Exception as e:
        logger.warning(f"Could not read previous interview session for dedupe: {e}")

    selected: list[dict] = []
    for _ in range(5):
        random.shuffle(deduped_pool)
        candidate = deduped_pool[:question_count]
        if not previous_signature or _session_signature(candidate) != previous_signature:
            selected = candidate
            break

    if not selected:
        selected = deduped_pool[:question_count]

    # ── Guarantee at least 1 coding question ────────────────────────────────
    # If the selected set has no coding question, swap the last non-coding
    # question with a coding question from the remaining pool.
    has_coding = any(q.get("category") in CODING_CATEGORIES for q in selected)
    if not has_coding:
        selected_keys = {_question_key(q["question"]) for q in selected}
        coding_reserve = [
            q for q in deduped_pool
            if q.get("category") in CODING_CATEGORIES
            and _question_key(q["question"]) not in selected_keys
        ]
        if coding_reserve:
            swap_in = random.choice(coding_reserve)
            # Replace the last non-behavioral question so we don't gut soft-skills coverage
            for i in range(len(selected) - 1, -1, -1):
                if selected[i].get("category") not in {"behavioral", "situational"}:
                    selected[i] = swap_in
                    break
            else:
                selected[-1] = swap_in  # fallback: replace last question
        else:
            # No coding question in pool at all — build a generic one as a safety net
            fallback_coding: dict = {
                "question": (
                    f"Write a function in Python that takes a list of integers and returns "
                    f"all pairs that sum to a given target. Discuss time and space complexity."
                ),
                "category": "code_write",
                "difficulty": "medium",
                "expected_points": ["two-pointer or hash map approach", "O(n) time complexity", "edge cases: empty list, no pairs", "code correctness"],
                "code_snippet": None,
                "language": "python",
            }
            for i in range(len(selected) - 1, -1, -1):
                if selected[i].get("category") not in {"behavioral", "situational"}:
                    selected[i] = fallback_coding
                    break
            else:
                selected[-1] = fallback_coding
    # ────────────────────────────────────────────────────────────────────────

    for idx, question in enumerate(selected, start=1):
        question["id"] = idx
    return selected


@router.post("/start")
async def start_interview(body: StartInterviewRequest, profile=Depends(get_user_profile)):
    """Start a new mock interview session and return randomized, role-based questions."""
    user_id = profile["user_id"]

    if profile["plan_type"] == "freemium" and profile["mock_interview_count"] >= settings.FREEMIUM_MAX_INTERVIEWS:
        raise HTTPException(status_code=403, detail="Freemium limit reached. Upgrade to Premium for unlimited interviews.")

    # Normalise company key
    company_key = (body.company or "general").lower().strip().replace(" ", "_")
    if company_key not in COMPANY_PROFILES:
        company_key = "general"

    question_count = _clamp_question_count(body.question_count)
    skills, github_projects = _load_candidate_context(user_id, body.skills, body.github_projects)
    questions = await _build_randomized_questions(
        user_id=user_id,
        job_role=body.job_role,
        company=company_key,
        skills=skills,
        github_projects=github_projects,
        question_count=question_count,
    )

    session_id = str(uuid.uuid4())
    insert_payload = {
        "id": session_id,
        "user_id": user_id,
        "job_role": body.job_role,
        "company": company_key,
        "mode": body.mode,
        "status": "in_progress",
        "questions": questions,
        "answers": [],
        "transcript": [],
        "score": None,
    }

    try:
        supabase.table("interview_sessions").insert(insert_payload).execute()
    except Exception as e:
        # Backward-compatible fallback for older schemas without answers/score/company.
        logger.warning(f"Insert with extended interview schema failed, retrying legacy payload: {e}")
        legacy_payload = {k: v for k, v in insert_payload.items() if k not in {"answers", "score", "company"}}
        supabase.table("interview_sessions").insert(legacy_payload).execute()

    return {"success": True, "session_id": session_id, "questions": questions}



# ============================================================
# Honest Scoring Enforcement
# The AI evaluation prompt often inflates scores. These
# functions recalculate everything mathematically from
# per-question scores and enforce brutal honesty.
# ============================================================

# Curated resources keyed by weak area keyword
LEARNING_RESOURCES: dict[str, list[dict]] = {
    "system design": [
        {"title": "System Design Primer (GitHub)", "url": "https://github.com/donnemartin/system-design-primer"},
        {"title": "Designing Data-Intensive Applications — Martin Kleppmann", "url": "https://dataintensive.net/"},
        {"title": "ByteByteGo System Design Newsletter", "url": "https://bytebytego.com/"},
    ],
    "algorithms": [
        {"title": "LeetCode Top 150 Interview Questions", "url": "https://leetcode.com/studyplan/top-interview-150/"},
        {"title": "NeetCode 150 — Video solutions", "url": "https://neetcode.io/"},
        {"title": "The Algorithm Design Manual — Skiena", "url": "https://www.algorist.com/"},
    ],
    "data structures": [
        {"title": "LeetCode DSA Study Plan", "url": "https://leetcode.com/studyplan/leetcode-75/"},
        {"title": "Visualgo — Visualize Data Structures", "url": "https://visualgo.net/"},
        {"title": "NeetCode DSA course", "url": "https://neetcode.io/courses/dsa-for-beginners/0"},
    ],
    "behavioral": [
        {"title": "Amazon Leadership Principles Guide", "url": "https://www.amazon.jobs/content/en/our-workplace/leadership-principles"},
        {"title": "STAR Method — Indeed Guide", "url": "https://www.indeed.com/career-advice/interviewing/how-to-use-the-star-interview-response-technique"},
        {"title": "Grokking Behavioral Interviews — Educative", "url": "https://www.educative.io/courses/grokking-the-behavioral-interview"},
    ],
    "communication": [
        {"title": "Think Aloud — How to narrate your thought process", "url": "https://interviewing.io/guides/how-to-think-aloud"},
        {"title": "Pramp — Free peer mock interviews", "url": "https://www.pramp.com/"},
        {"title": "interviewing.io — Anonymous mock interviews", "url": "https://interviewing.io/"},
    ],
    "machine learning": [
        {"title": "fast.ai — Practical Deep Learning for Coders", "url": "https://www.fast.ai/"},
        {"title": "CS229 Machine Learning — Stanford (free)", "url": "https://cs229.stanford.edu/"},
        {"title": "Andrej Karpathy's Neural Networks Zero to Hero", "url": "https://karpathy.ai/zero-to-hero.html"},
    ],
    "python": [
        {"title": "Python for Algorithms — Interview Prep", "url": "https://www.educative.io/courses/python-for-programmers"},
        {"title": "Real Python — Advanced Python Concepts", "url": "https://realpython.com/"},
    ],
    "debugging": [
        {"title": "LeetCode Debugging Tag", "url": "https://leetcode.com/problemset/?topicSlugs=debugging"},
        {"title": "The Art of Debugging — Norman Matloff", "url": "https://nostarch.com/debugging.htm"},
    ],
    "problem solving": [
        {"title": "How to Solve It — George Pólya", "url": "https://www.amazon.com/How-Solve-Mathematical-Princeton-Science/dp/069116407X"},
        {"title": "Cracking the Coding Interview — Gayle McDowell", "url": "https://www.crackingthecodinginterview.com/"},
        {"title": "NeetCode Roadmap", "url": "https://neetcode.io/roadmap"},
    ],
    "object oriented": [
        {"title": "Head First Design Patterns", "url": "https://www.oreilly.com/library/view/head-first-design/0596007124/"},
        {"title": "Refactoring.Guru — Design Patterns", "url": "https://refactoring.guru/design-patterns"},
    ],
    "sql": [
        {"title": "SQLZoo — Interactive SQL Practice", "url": "https://sqlzoo.net/"},
        {"title": "LeetCode Database Problems", "url": "https://leetcode.com/problemset/?topicSlugs=database"},
        {"title": "Mode SQL Tutorial", "url": "https://mode.com/sql-tutorial/"},
    ],
    "confidence": [
        {"title": "Pramp — Free peer mock interviews", "url": "https://www.pramp.com/"},
        {"title": "Excelling at Behavioral Interviews — Exponent", "url": "https://www.tryexponent.com/courses/behavioral"},
        {"title": "r/cscareerquestions Mock Interview Thread", "url": "https://www.reddit.com/r/cscareerquestions/"},
    ],
    "default": [
        {"title": "Cracking the Coding Interview — Gayle McDowell", "url": "https://www.crackingthecodinginterview.com/"},
        {"title": "LeetCode Top Interview 150", "url": "https://leetcode.com/studyplan/top-interview-150/"},
        {"title": "Pramp — Free mock interviews", "url": "https://www.pramp.com/"},
        {"title": "interviewing.io — Anonymous practice", "url": "https://interviewing.io/"},
    ],
}


def _pick_resources(weak_areas: list[str], improvements: list[str]) -> list[dict]:
    """Map weak areas and improvement points to curated resources."""
    resources: list[dict] = []
    seen_titles: set[str] = set()

    combined_text = " ".join(weak_areas + improvements).lower()

    priority_keys = [
        "system design", "algorithms", "data structures", "behavioral",
        "communication", "machine learning", "python", "debugging",
        "problem solving", "object oriented", "sql", "confidence",
    ]

    for key in priority_keys:
        if key in combined_text:
            for r in LEARNING_RESOURCES[key]:
                if r["title"] not in seen_titles:
                    seen_titles.add(r["title"])
                    resources.append(r)
            if len(resources) >= 6:
                break

    # Always include defaults if we have fewer than 3 resources
    if len(resources) < 3:
        for r in LEARNING_RESOURCES["default"]:
            if r["title"] not in seen_titles:
                seen_titles.add(r["title"])
                resources.append(r)

    return resources[:6]


def _enforce_honest_scores(evaluation: dict, transcript: list[dict]) -> dict:
    """
    Recalculate all scores mathematically from per-question scores.
    If the AI inflated any score, this corrects it.

    Scoring rules:
    - overall_score   = weighted mean of per-question scores mapped to 0-100
    - technical_score = mean of technical/coding question scores → 0-100
    - communication_score = penalised if answers are short, vague, or missing
    - confidence_score = derived from answer length + variance in q scores
    - hire_recommendation = derived purely from overall_score thresholds
    """
    question_feedback: list[dict] = evaluation.get("question_feedback") or []
    n = len(question_feedback)

    # ── Per-question score extraction ──────────────────────────────────────────
    raw_scores: list[float] = []
    tech_scores: list[float] = []
    for i, fb in enumerate(question_feedback):
        score = float(fb.get("score") or 0)
        score = max(0.0, min(10.0, score))
        raw_scores.append(score)
        answer_text = ""
        if i < len(transcript):
            answer_text = str(transcript[i].get("answer") or "")
        if "CODE:" in answer_text or fb.get("category") in CODING_CATEGORIES:
            tech_scores.append(score)

    # ── Fallback: if AI gave no question_feedback, estimate from sub-scores ───
    if not raw_scores:
        ai_overall = float(evaluation.get("overall_score") or 0)
        substantial = sum(1 for t in transcript if len(str(t.get("answer") or "")) > 80)
        if n and substantial < n / 2:
            ai_overall = min(ai_overall, 55)
        return {**evaluation, "overall_score": int(ai_overall)}

    # ── Detect all-blank session ───────────────────────────────────────────────
    blank_count = sum(1 for t in transcript if len(str(t.get("answer") or "").strip()) < 10)
    all_blank = blank_count >= len(transcript) * 0.8  # 80%+ blank answers

    # ── Overall: weighted mean (scores out of 10 → out of 100) ────────────────
    mean_score = sum(raw_scores) / len(raw_scores)
    overall_score = round(mean_score * 10)

    # ── Penalty for very short / blank answers ─────────────────────────────────
    short_answer_count = sum(
        1 for t in transcript
        if len(str(t.get("answer") or "").strip()) < 40
    )
    if short_answer_count > 0:
        overall_score = max(0, overall_score - (short_answer_count * 4))

    # ── Technical score ────────────────────────────────────────────────────────
    if tech_scores:
        technical_score = round((sum(tech_scores) / len(tech_scores)) * 10)
    else:
        # No explicit coding questions detected — use top half of raw scores as proxy
        sorted_scores = sorted(raw_scores, reverse=True)
        top_half = sorted_scores[:max(1, len(sorted_scores) // 2)]
        technical_score = round((sum(top_half) / len(top_half)) * 10)

    # ── Communication score ────────────────────────────────────────────────────
    # Based on answer substance: length, structure keywords, completeness
    comm_scores: list[float] = []
    for t in transcript:
        answer = str(t.get("answer") or "").strip()
        word_count = len(answer.split())
        score = 0.0
        if word_count >= 100:  score += 4.0
        elif word_count >= 50: score += 2.5
        elif word_count >= 20: score += 1.0
        # Bonus for STAR/structure keywords
        lower = answer.lower()
        structure_words = ["because", "therefore", "first", "then", "finally",
                           "situation", "result", "decided", "approach", "solution"]
        score += min(3.0, sum(0.5 for w in structure_words if w in lower))
        # Bonus for specificity
        if any(c.isdigit() for c in answer): score += 1.0
        # Coding answers handled differently
        if "CODE:" in answer: score = min(7.0, score + 2.0)
        comm_scores.append(min(10.0, score))

    communication_score = round((sum(comm_scores) / len(comm_scores)) * 10) if comm_scores else 30

    # ── Confidence score ───────────────────────────────────────────────────────
    # High variance in scores = inconsistent = lower confidence reading
    if len(raw_scores) > 1:
        variance = sum((s - mean_score) ** 2 for s in raw_scores) / len(raw_scores)
        # Map variance 0→low → high confidence, variance 10→high → low confidence
        confidence_base = max(0.0, 10.0 - variance)
        confidence_score = round(confidence_base * 10)
        # Average with communication as a proxy
        confidence_score = round((confidence_score + communication_score) / 2)
    else:
        confidence_score = communication_score

    # ── Clamp all scores 0-100 ────────────────────────────────────────────────
    overall_score       = max(0, min(100, overall_score))
    technical_score     = max(0, min(100, technical_score))
    communication_score = max(0, min(100, communication_score))
    confidence_score    = max(0, min(100, confidence_score))

    # ── Hire recommendation — NO inflation allowed ─────────────────────────────
    if overall_score >= 80:
        hire = "Strong Yes — exceptional performance across all areas"
    elif overall_score >= 65:
        hire = "Yes — solid performance with minor gaps to work on"
    elif overall_score >= 50:
        hire = "Maybe — showed potential but significant gaps remain"
    elif overall_score >= 35:
        hire = "No — too many weak answers; needs more preparation"
    else:
        hire = "Strong No — fundamental gaps across most areas; start from basics"

    # ── Extract weak areas from improvements ───────────────────────────────────
    improvements: list[str] = evaluation.get("improvements") or []
    weak_area_text = " ".join(improvements).lower()

    # Collect topics from low-scoring questions
    weak_topics: list[str] = []
    for i, score in enumerate(raw_scores):
        if score < 5.0 and i < len(question_feedback):
            q_text = str(question_feedback[i].get("question") or "").lower()
            for kw in ["system design", "algorithm", "data structure", "behavioral",
                       "communication", "python", "sql", "debugging", "machine learning",
                       "object oriented", "problem solving", "confidence"]:
                if kw in q_text or kw in weak_area_text:
                    if kw not in weak_topics:
                        weak_topics.append(kw)

    # ── Resources ──────────────────────────────────────────────────────────────
    resources = _pick_resources(weak_topics, improvements)

    # ── Patch evaluation dict ──────────────────────────────────────────────────
    updated = {
        **evaluation,
        "overall_score":       overall_score,
        "technical_score":     technical_score,
        "communication_score": communication_score,
        "confidence_score":    confidence_score,
        "hire_recommendation": hire,
        "recommended_resources": [
            f"{r['title']} → {r['url']}" for r in resources
        ],
        "_score_method": "enforced",
    }

    # ── Patch summary ──────────────────────────────────────────────────────────
    if all_blank:
        updated["summary"] = (
            "No answers were provided for this session — all questions were left blank or empty. "
            "Scores of 0 are correct and reflect no submitted answers. "
            "Complete a full session with real answers to get a meaningful evaluation."
        )
        updated["strengths"] = []
        updated["hire_recommendation"] = "No — session was not completed (blank answers)"
        # Use default starter resources for blank sessions
        default_res = (
            LEARNING_RESOURCES.get("problem solving", []) +
            LEARNING_RESOURCES.get("communication", []) +
            LEARNING_RESOURCES.get("algorithms", [])
        )
        updated["recommended_resources"] = [
            f"{r['title']} → {r['url']}" for r in default_res[:6]
        ]
    elif overall_score < 50:
        weak_count = sum(1 for s in raw_scores if s < 5.0)
        strong_count = sum(1 for s in raw_scores if s >= 7.0)
        updated["summary"] = (
            f"{weak_count} out of {len(raw_scores)} answers were below the bar — "
            f"not enough to pass a real interview at this level. "
            f"{strong_count} answers showed genuine strength. "
            f"Focus on the resources below and practice at least 30 more problems "
            f"before your next attempt. This is fixable with targeted effort."
        )
    elif overall_score < 65:
        updated["summary"] = (
            (evaluation.get("summary") or "") +
            " Overall performance is below the typical hire bar — targeted practice on "
            "the weak areas listed will make a real difference."
        )

    return updated


@router.post("/evaluate")
async def evaluate_session(body: EvaluateRequest, user=Depends(get_authenticated_user)):
    """Submit full transcript and get AI evaluation scores."""
    session = (
        supabase.table("interview_sessions")
        .select("*")
        .eq("id", body.session_id)
        .eq("user_id", user["user_id"])
        .single()
        .execute()
    )
    if not session.data:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    evaluation = await evaluate_interview(
        job_role=session.data["job_role"],
        transcript=body.transcript,
    )

    # ── Override AI scores with mathematically honest values ──────────────────
    evaluation = _enforce_honest_scores(evaluation, body.transcript)
    # ─────────────────────────────────────────────────────────────────────────

    update_payload = {
        "answers": body.transcript,
        "transcript": body.transcript,
        "evaluation": evaluation,
        "score": evaluation.get("overall_score", 0),
        "communication_score": evaluation.get("communication_score", 0),
        "technical_score": evaluation.get("technical_score", 0),
        "overall_score": evaluation.get("overall_score", 0),
        "status": "completed",
    }

    try:
        supabase.table("interview_sessions").update(update_payload).eq("id", body.session_id).execute()
    except Exception as e:
        logger.warning(f"Update with extended interview schema failed, retrying legacy payload: {e}")
        legacy_update = {k: v for k, v in update_payload.items() if k not in {"answers", "score"}}
        supabase.table("interview_sessions").update(legacy_update).eq("id", body.session_id).execute()

    supabase.rpc("increment_interview_count", {"p_user_id": user["user_id"]}).execute()
    return {"success": True, "evaluation": evaluation}


@router.get("/history")
async def get_interview_history(user=Depends(get_authenticated_user)):
    result = (
        supabase.table("interview_sessions")
        .select("*")
        .eq("user_id", user["user_id"])
        .order("created_at", desc=True)
        .execute()
    )
    return {"success": True, "sessions": result.data}


@router.get("/{session_id}")
async def get_session(session_id: str, user=Depends(get_authenticated_user)):
    result = (
        supabase.table("interview_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user["user_id"])
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, "session": result.data}