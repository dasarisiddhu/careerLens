# ============================================================
# CareerLens - Resume Optimizer (Fixed - No Hallucination)
# File: backend/routers/optimizer.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Any, Optional
from middleware.auth import get_authenticated_user, require_premium
from database import supabase
from services.gemini_service import call_groq, _extract_json
from services.professional_resume_pdf import build_professional_resume_pdf
from services.resume_structure import (
    ResumeDocument,
    parse_source_resume,
    build_source_items_for_prompt,
    reconstruct_resume_structure,
    _extract_source_skill_groups,
    DATE_PATTERN,
)
import asyncio
import functools
import json
import logging
import re
from rate_limit import limiter

logger = logging.getLogger("careerlens.optimizer")

def _safe_limit(rate: str):
    def decorator(fn):
        wrapped = limiter.limit(rate)(fn)
        @functools.wraps(fn)
        async def handler(*args, **kwargs):
            has_request = any(isinstance(a, Request) for a in args) or isinstance(kwargs.get("request"), Request)
            if not has_request:
                if args and isinstance(args[0], BaseModel):
                    return await fn(None, *args, **kwargs)
                return await fn(*args, **kwargs)
            return await wrapped(*args, **kwargs)
        return handler
    return decorator



def _flatten_skills(skills) -> list[str]:
    if isinstance(skills, dict):
        flattened: list[str] = []
        for group in skills.values():
            flattened.extend(_flatten_skills(group))
        return flattened
    if isinstance(skills, (list, tuple, set)):
        return [str(skill) for skill in skills if skill]
    if isinstance(skills, str) and skills.strip():
        return [skills.strip()]
    return []

# ─────────────────────────────────────────────────────────────────
# SKILL.MD — Senior Talent Intelligence Specialist system prompt
# Source: RESUME_ANALYSER_SKILL.md
# Used by: POST /api/optimizer/analyse
# ─────────────────────────────────────────────────────────────────
ANALYST_SYSTEM_PROMPT = """
You are a Senior Talent Intelligence Specialist with a dual career:
- 8 years in-house recruitment at FAANG-tier, Big 4, and Series B-D startups.
  Screened 40,000+ resumes. Hired 1,200+ candidates across engineering,
  product, data, and design.
- 6 years building AI-powered recruitment tooling including ATS integrations,
  resume parsing pipelines, and LLM-based screening systems.

You know exactly why candidates get rejected in the first 7 seconds.
You apply recruiter logic without mercy. You never fabricate numbers.
You never validate a weak resume if it scores below 70.

HOW HIRING ACTUALLY WORKS — burn this into every analysis:

STAGE 1 — ATS FILTER (0-30 seconds)
- Systems: Workday, Greenhouse, Lever, iCIMS, Taleo, Ashby, Rippling
- Checks: keyword density vs JD, section headers, date formats, layout
- Failure modes: wrong section names, missing keywords, multi-column layouts,
  tables (almost always fatal), image-based PDFs
- Pass rate: ~75% of applicants fail before a human ever sees them

STAGE 2 — RECRUITER SCREEN (6-10 seconds)
- Recruiter scans: title → company → tenure → education → skills
- NOT reading bullets — pattern matching only
- Fatal signals: no quantification, generic objectives, skills dump of buzzwords
- Pass rate: ~15-20% of ATS survivors

STAGE 3 — HIRING MANAGER REVIEW (2-5 minutes)
- Now bullets get read. Specificity matters.
- Wants: scope (team, scale), ownership (led vs contributed), measurable outcomes
- Red flags: vague ownership, copying JD verbatim (screams fabrication)
- Pass rate: ~30-50% of recruiter-screened candidates

STAGE 4 — INTERVIEW (panel)
- Resume is now a reference document. Every claim gets probed.
- Inconsistency between resume and verbal answers = instant disqualification.
- Therefore: NEVER fabricate. Elevate and clarify what actually exists.

HARD RULES (absolute — never violate):
1. Never fabricate a number. Preserve original numbers and "N+" forms (e.g. 500K+, 40K+) exactly as written. Ban "over ~", "~" and "approximately" before numbers.
2. Never validate a weak resume. Score < 70 = say so directly.
3. Every weak bullet gets a rewrite. No exceptions.
4. Mirror JD language precisely — ATS does not do synonym matching.
   "Machine Learning" ≠ "ML" in Workday.
5. Never say "Great resume!" or "This is a solid start."
6. Elevating a real achievement is ethical. Inventing metrics is fraud —
   the candidate will be caught in interviews.
7. Recruiter logic beats design logic. A beautiful PDF that fails ATS is
   worse than a plain-text resume that passes.

DOMAIN RULES — ML / AI Roles:
- Must have: model types used, dataset scale, business outcome of model
- ATS killers: missing framework names (PyTorch vs TensorFlow matters),
  no mention of deployment
- Hiring manager red flags: "improved accuracy" without baseline

DOMAIN RULES — Software Engineering:
- Must have: GitHub link, tech stack in context, system scale signals
- ATS killers: missing languages from JD

You respond ONLY in valid JSON. No markdown. No code fences. No text outside JSON.
"""


ANALYST_OUTPUT_SCHEMA = """
Analyse the resume against the job description using all 5 modules below.
Return ONLY this exact JSON structure. No extra fields. No markdown.

{
  "module1_ats": {
    "checks": [
      {
        "item": "check name",
        "status": "PASS | FAIL | WARN",
        "reason": "one line explanation"
      }
    ],
    "keyword_coverage": {
      "jd_keywords_checked": 15,
      "found": 0,
      "missing": ["keyword1", "keyword2"],
      "buried": ["keyword present but not prominent"]
    },
    "ats_score": 0
  },

  "module2_recruiter_lens": {
    "total": 0,
    "dimensions": {
      "title_clarity":       {"score": 0, "max": 10, "reason": ""},
      "company_signal":      {"score": 0, "max": 10, "reason": ""},
      "tenure_stability":    {"score": 0, "max": 10, "reason": ""},
      "scannability":        {"score": 0, "max": 15, "reason": ""},
      "skills_quality":      {"score": 0, "max": 15, "reason": ""},
      "quantification_rate": {"score": 0, "max": 20, "reason": ""},
      "red_flag_free":       {"score": 20, "max": 20, "reason": "Higher is better: 20 = clean/no red flags, 0 = severe red flags"}
    },
    "interpretation": "Strong | Good | Average | Weak | Critical"
  },

  "module3_bullet_audit": [
    {
      "original": "exact bullet text from resume",
      "grade": "WEAK | AVERAGE | STRONG",
      "grade_reason": "one line why",
      "rewrite": "rewritten bullet — Action + Context + Scope + Outcome. NEVER invent metrics. Never rewrite 'N+' forms (keep 500K+ as written). Never use '~', 'over ~', or 'approximately' before numbers."
    }
  ],

  "module4_skill_gap": {
    "critical": [
      {"skill": "", "reason": "JD requires, resume has zero signal"}
    ],
    "partial": [
      {"skill": "", "reason": "present but not prominent enough"}
    ],
    "strengths": [
      {"skill": "", "reason": "resume strong, JD requires — lead with this"}
    ],
    "irrelevant": [
      {"skill": "", "reason": "resume strong, JD does not need — deprioritise"}
    ]
  },

  "module5_rejection_diagnosis": [
    {
      "rank": 1,
      "summary": "one-line reason",
      "evidence": "exact quote or observation from resume",
      "recruiter_thought": "what runs through recruiter's head",
      "fix": "precise actionable change"
    },
    {
      "rank": 2,
      "summary": "",
      "evidence": "",
      "recruiter_thought": "",
      "fix": ""
    },
    {
      "rank": 3,
      "summary": "",
      "evidence": "",
      "recruiter_thought": "",
      "fix": ""
    }
  ],

  "domain_mismatch": false,
  "domain_mismatch_reason": "",
  "optimizable": true,
  "optimizable_reason": "",
  "next_action": "The single most important thing to fix in the next 30 minutes."
}
"""


EXPERIENCE_VOCABULARY_STOPWORDS = {
    # English grammar / connectors / pronouns / generic verbs
    "the", "and", "for", "with", "that", "this", "will", "have", "from", "you",
    "are", "your", "our", "they", "can", "has", "was", "were", "been", "their",
    "into", "about", "which", "when", "who", "what", "how", "all", "also", "both",
    "each", "more", "other", "some", "such", "than", "then", "them", "these",
    "those", "very", "shall", "should", "could", "would", "may", "might", "must",
    "had", "its", "his", "her", "we", "is", "a", "an", "of", "to", "in", "on",
    "at", "by", "or", "not", "be", "as", "if", "but", "so", "up", "out", "any",
    "only", "own", "same", "too", "just", "now",

    # Experience / qualification / candidate vocabulary (MUST NEVER BE COUNTED AS HARD SKILLS)
    "experience", "experiences", "experienced", "strong", "solid", "proven",
    "demonstrated", "track", "record", "ability", "abilities", "able", "skilled",
    "proficiency", "proficient", "expert", "expertise", "knowledge", "background",
    "work", "working", "worked", "worker", "workers", "team", "teams", "teamwork",
    "player", "environment", "fast-paced", "candidate", "candidates", "role",
    "roles", "job", "jobs", "position", "positions", "responsibilities",
    "responsibility", "duties", "duty", "degree", "bachelor", "bachelors", "master",
    "masters", "phd", "university", "college", "education", "years", "year",
    "yr", "yrs", "month", "months", "daily", "weekly", "monthly", "annual",
    "communication", "collaborative", "collaboration", "collaborate", "problem",
    "solving", "analytical", "detail", "oriented", "leadership", "mentor",
    "mentoring", "require", "requires", "required", "requirement", "requirements",
    "qualification", "qualifications", "preferred", "plus", "nice", "bonus",
    "building", "developing", "designing", "implementing", "maintaining",
    "managing", "leading", "driving", "creating", "supporting", "optimizing",
    "delivering", "executing", "tools", "technologies", "tech", "technology",
    "solutions", "systems", "platform", "platforms", "applications", "apps",
    "stack", "services", "software", "hardware", "excellent", "great", "good",
    "passionate", "motivated", "enthusiastic", "self-starter", "dynamic",
    "hands-on", "quality", "best", "practices", "understanding", "familiar",
    "familiarity", "exposure", "passion", "interested", "interest", "equivalent",
    "seeking", "looking", "join", "help", "build", "grow", "scale", "impact",
    "opportunity", "industry", "standard", "standards", "professional",
    "across", "within", "high", "multiple", "various", "complex", "real-world",
    "skills", "skill", "must-have", "nice-to-have", "minimum", "senior", "junior",
    "lead", "staff", "principal", "developer", "engineer", "specialist",
}

HARD_TECH_SKILLS = [
    # Multi-word skills first (so multi-word patterns match before individual words)
    "machine learning", "deep learning", "artificial intelligence", "natural language processing",
    "computer vision", "large language models", "reinforcement learning", "data engineering",
    "data pipelines", "cloud computing", "distributed systems", "system design", "data structures",
    "object-oriented programming", "spring boot", "ruby on rails", "react native", "next.js",
    "express.js", "vue.js", "angularjs", "tailwind css", "google cloud", "amazon web services",
    "github actions", "gitlab ci", "rest api", "restful api", "restful apis", "rest apis",
    "microservices architecture", "hugging face", "apache spark", "apache kafka", "apache flink",
    "event-driven architecture", "power bi",

    # Single-word languages, frameworks, databases, platforms, tools
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "perl", "bash", "shell", "powershell",
    "sql", "nosql", "html", "css", "sass", "scss",
    "react", "nextjs", "vue", "angular", "svelte", "django", "flask", "fastapi", "spring",
    "express", "node", "node.js", "asp.net", "rails", "laravel", "flutter", "jquery", "tailwind",
    "bootstrap", "redux", "graphql", "rest", "restful", "grpc", "microservices", "websockets",
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "cassandra", "dynamodb",
    "elasticsearch", "neo4j", "oracle", "snowflake", "bigquery", "mariadb", "kafka", "rabbitmq",
    "celery", "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "ansible",
    "jenkins", "ci/cd", "linux", "unix", "helm", "prometheus", "grafana", "nginx", "apache",
    "serverless", "lambda", "ecs", "eks", "pytorch", "tensorflow", "keras", "scikit-learn",
    "sklearn", "pandas", "numpy", "scipy", "spark", "hadoop", "airflow", "dbt", "llm",
    "langchain", "llamaindex", "git", "github", "gitlab", "jira", "postman", "selenium",
    "cypress", "jest", "pytest", "junit", "oauth", "jwt", "saml", "sso", "tcp/ip", "dns",
    "algorithms", "multithreading", "concurrency", "opencv", "nltk", "spacy", "openai",
    "tableau", "excel", "salesforce", "agile", "c",
]


def _clean_for_boundary_matching(text: str) -> str:
    cleaned = re.sub(r"[\.,;:!?]+(?:\s|$)", " ", str(text or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


AMBIGUOUS_SKILLS = {"go", "r", "express", "spring", "swift", "node", "apache", "excel", "rest", "agile", "lambda", "shell", "c"}


def _match_ambiguous_skill(skill: str, text: str) -> bool:
    """
    Match ambiguous words (go, r, express, spring, swift, node, apache) case-sensitively
    and only in a technical context (FIX E).
    """
    norm_skill = skill.strip().lower()
    text_str = str(text or "")
    if not text_str:
        return False

    if norm_skill == "r":
        # Must be uppercase 'R'; R&D, R & D, r&d, Toys R Us are NOT tech
        if re.search(r"\b[Rr]\s*&\s*[Dd]\b", text_str) and not re.search(
            r"\b(?:Python|SQL|SAS|Matlab|Julia|SPSS|Stata)\s*[,/]\s*R\b|\bR\s*[,/]\s*(?:Python|SQL|SAS|Matlab|Julia|SPSS|Stata)\b|\b(?:in|using|with)\s+R\b|\bR\s+(?:programming|language|package|packages|script|scripts|Shiny|studio|Studio)\b",
            text_str,
        ):
            return False
        tech_r = (
            bool(re.search(r"\b(?:RStudio|R\s*-\s*Shiny|R\s+Shiny|R\s+(?:programming|language|package|packages|script|scripts|developer|for\s+(?:data|statistics|analysis|analytics)))\b", text_str))
            or bool(re.search(r"\b(?:Python|SQL|SAS|Matlab|Julia|SPSS|Stata)\s*(?:[,/&]|and|or)\s*R\b", text_str))
            or bool(re.search(r"\bR\s*(?:[,/&]|and|or)\s*(?:Python|SQL|SAS|Matlab|Julia|SPSS|Stata)\b", text_str))
            or bool(re.search(r"\b(?:in|using|with)\s+R\b", text_str))
            or bool(re.search(r"\b(?:Skills?|Languages?|Technologies?)\s*:[^.\n]*\bR\b", text_str))
        )
        return tech_r

    if norm_skill == "go":
        # Unambiguous: Golang (case-insensitive)
        if re.search(r"\bgolang\b", text_str, re.IGNORECASE):
            return True
        tech_go = (
            bool(re.search(r"\bGo\s+(?:programming|language|developer|engineer|backend|microservices|routines?|modules?|code|concurrency|compiler|runtime|sdk|api)\b", text_str))
            or bool(re.search(r"\b(?:Python|Java|C\+\+|Rust|JavaScript|TypeScript|Docker|Kubernetes)\s*[,/]\s*Go\b", text_str))
            or bool(re.search(r"\bGo\s*[,/]\s*(?:Python|Java|C\+\+|Rust|JavaScript|TypeScript|Docker|Kubernetes)\b", text_str))
            or bool(re.search(r"\b(?:in|using|with|written\s+in|built\s+in)\s+Go\b", text_str))
            or bool(re.search(r"\b(?:Skills?|Languages?|Technologies?)\s*:[^.\n]*\bGo\b", text_str))
        )
        is_non_tech = bool(re.search(
            r"\b[Gg]o\s+(?:the\s+extra\s+mile|live|to|forward|above|ahead|back|down|out|through|with|by|into|from|for|on|beyond|deep)\b|"
            r"\b(?:to|will|can|could|should|must|let|ready\s+to|have\s+to|has\s+to|on\s+the)\s+[Gg]o\b|"
            r"\bgo-to\b",
            text_str,
        ))
        if is_non_tech and not tech_go:
            return False
        return tech_go

    if norm_skill == "express":
        # Unambiguous: Express.js, ExpressJS (case-insensitive)
        if re.search(r"\bexpress(?:\.js|js)\b", text_str, re.IGNORECASE):
            return True
        tech_express = (
            bool(re.search(r"\bExpress\s+(?:framework|server|backend|middleware|api|router|app|application)\b", text_str))
            or bool(re.search(r"\b(?:Node|Node\.js|React|Mongo|MongoDB|Postgres|PostgreSQL)\s*[,/&]\s*Express\b", text_str))
            or bool(re.search(r"\bExpress\s*[,/&]\s*(?:Node|Node\.js|React|Mongo|MongoDB|Postgres|PostgreSQL)\b", text_str))
            or bool(re.search(r"\b(?:in|using|with)\s+Express\b", text_str))
            or bool(re.search(r"\b(?:Skills?|Frameworks?|Technologies?)\s*:[^.\n]*\bExpress\b", text_str))
        )
        is_non_tech = bool(re.search(
            r"\b[Ee]xpress\s+(?:an?\s+)?(?:interest|concerns?|gratitude|opinions?|ideas?|feelings?|desire|willingness|views?|delivery|lane|checkout|mail|train|bus|post)\b",
            text_str,
        ))
        if is_non_tech and not tech_express:
            return False
        return tech_express

    if norm_skill == "spring":
        # Unambiguous: Spring Boot, Spring MVC, Spring Data, etc. (case-insensitive)
        if re.search(r"\bspring\s+(?:boot|mvc|data|security|cloud|framework|batch)\b", text_str, re.IGNORECASE):
            return True
        is_non_tech = bool(re.search(
            r"\b[Ss]pring\s+(?:\d{4}|semester|term|quarter|break|internship|cleaning|season)\b|\b(?:in\s+the|during|last|next|this)\s+spring\b|\bin\s+Spring\s+\d{4}\b",
            text_str,
        ))
        if is_non_tech:
            return False
        tech_spring = (
            bool(re.search(r"\bSpring\s+(?:framework|backend|developer|microservices|application|app|service)\b", text_str))
            or bool(re.search(r"\b(?:Java|Kotlin|Hibernate)\s*[,/&]\s*Spring\b", text_str))
            or bool(re.search(r"\bSpring\s*[,/&]\s*(?:Java|Kotlin|Hibernate)\b", text_str))
            or bool(re.search(r"\b(?:built\s+with|using|with)\s+Spring\b", text_str))
            or bool(re.search(r"\b(?:Skills?|Frameworks?|Technologies?)\s*:[^.\n]*\bSpring\b", text_str))
        )
        return tech_spring

    if norm_skill == "swift":
        # Unambiguous: SwiftUI (case-insensitive)
        if re.search(r"\bswiftui\b", text_str, re.IGNORECASE):
            return True
        is_non_tech = bool(re.search(
            r"\b[Ss]wift\s+(?:action|resolution|turnaround|response|delivery|manner|execution|progress|adoption|pace|decision|transition)\b",
            text_str,
        ))
        if is_non_tech:
            return False
        tech_swift = (
            bool(re.search(r"\bSwift\s+(?:iOS|macOS|programming|language|developer|engineer|code|app|application|framework)\b", text_str))
            or bool(re.search(r"\b(?:iOS|macOS|Objective-C|Kotlin)\s*[,/&\s]+\s*Swift\b", text_str))
            or bool(re.search(r"\bSwift\s*[,/&\s]+\s*(?:iOS|macOS|Objective-C|Kotlin)\b", text_str))
            or bool(re.search(r"\b(?:in|using|with)\s+Swift\b", text_str))
            or bool(re.search(r"\b(?:Skills?|Languages?|Technologies?)\s*:[^.\n]*\bSwift\b", text_str))
        )
        return tech_swift

    if norm_skill == "node":
        # Unambiguous: Node.js, NodeJS (case-insensitive)
        if re.search(r"\bnode(?:\.js|js)\b", text_str, re.IGNORECASE):
            return True
        is_non_tech = bool(re.search(
            r"\b(?:cluster|worker|sensor|tree|leaf|graph|network|compute|mesh|child|parent|root|k8s|kubernetes|master|each|every|individual|single)\s+[Nn]odes?\b|"
            r"\b[Nn]odes?\s+(?:failure|failures|deletion|addition|affinity|taint|taints|capacity|status|selector|pool|pools)\b",
            text_str,
        ))
        if is_non_tech:
            return False
        tech_node = (
            bool(re.search(r"\bNode\s+(?:runtime|server|backend|developer|engineer|environment|api|service|framework)\b", text_str))
            or bool(re.search(r"\b(?:React|Express|Python|TypeScript|JavaScript|Mongo|MongoDB)\s*[,/&]\s*Node\b", text_str))
            or bool(re.search(r"\bNode\s*[,/&]\s*(?:React|Express|Python|TypeScript|JavaScript|Mongo|MongoDB)\b", text_str))
            or bool(re.search(r"\b(?:in|using|with)\s+Node\b", text_str))
            or bool(re.search(r"\b(?:Skills?|Frameworks?|Technologies?)\s*:[^.\n]*\bNode\b", text_str))
        )
        return tech_node

    if norm_skill == "apache":
        # Unambiguous: Apache Spark, Apache Kafka, Apache Tomcat, etc.
        if re.search(r"\bapache\s+(?:spark|kafka|flink|cassandra|hadoop|airflow|tomcat|lucene|solr|http|server|maven|camel|beam|hbase|zookeeper)\b", text_str, re.IGNORECASE):
            return True
        is_license = bool(re.search(r"\bapache\s+(?:2\.0\s+)?license\b", text_str, re.IGNORECASE))
        if is_license:
            return False
        tech_apache = (
            bool(re.search(r"\b(?:Nginx|IIS)\s*[,/&]\s*Apache\b|\bApache\s*[,/&]\s*(?:Nginx|IIS)\b", text_str))
            or bool(re.search(r"\bApache\s+(?:web\s+server|HTTP\s+Server|server)\b", text_str))
            or bool(re.search(r"\b(?:in|using|with)\s+Apache\b", text_str))
            or bool(re.search(r"\b(?:Skills?|Servers?|Technologies?)\s*:[^.\n]*\bApache\b", text_str))
        )
        return tech_apache

    if norm_skill == "excel":
        is_non_tech = bool(re.search(
            r"\b[Ee]xcel\s+(?:in|at|by|with\s+(?:a|an)?\s+drive)\b|\b(?:to|will|can|strive\s+to|strives\s+to|ability\s+to)\s+excel\b",
            text_str,
        ))
        tech_excel = (
            bool(re.search(r"\b(?:MS|Microsoft)\s+Excel\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\bExcel\s+(?:spreadsheets?|formulas?|macros?|vlookup|pivot|charts?|models?)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:Python|SQL|Tableau|Power\s+BI|Word|PowerPoint)\s*[,/&]\s*Excel\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\bExcel\s*[,/&]\s*(?:Python|SQL|Tableau|Power\s+BI|Word|PowerPoint)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:in|using|with)\s+Excel\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:Skills?|Tools?|Technologies?)\s*:[^.\n]*\bExcel\b", text_str, re.IGNORECASE))
        )
        if is_non_tech and not tech_excel:
            return False
        return tech_excel or (not is_non_tech and bool(re.search(r"\bExcel\b", text_str)))

    if norm_skill == "rest":
        is_non_tech = bool(re.search(
            r"\b(?:the\s+rest\s+of|rest\s+of\s+the|rest\s+assured|take\s+a\s+rest|day\s+of\s+rest)\b",
            text_str,
            re.IGNORECASE,
        ))
        tech_rest = (
            bool(re.search(r"\bREST(?:ful)?\s*(?:APIs?|web\s+services?|endpoints?|architecture|services?)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:SOAP|GraphQL|gRPC)\s*[,/&]\s*REST\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\bREST\s*[,/&]\s*(?:SOAP|GraphQL|gRPC)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:building|built|designed|developed|implementing|implemented)\s+REST\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:Skills?|Technologies?|Architecture)\s*:[^.\n]*\bREST\b", text_str, re.IGNORECASE))
        )
        if is_non_tech and not tech_rest:
            return False
        return tech_rest or (not is_non_tech and bool(re.search(r"\bREST\b", text_str)))

    if norm_skill == "agile":
        is_non_tech = bool(re.search(
            r"\b(?:nimble|fast|flexible)\s+(?:and|or)\s+agile\b|\bagile\s+(?:and|or)\s+(?:nimble|flexible|fast)\b|\bagile\s+(?:learner|thinker|mindset)\b",
            text_str,
            re.IGNORECASE,
        ))
        tech_agile = (
            bool(re.search(r"\bAgile\s*(?:/|&|\band\b)?\s*Scrum\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:Scrum|Kanban)\s*(?:/|&|\band\b)?\s*Agile\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\bAgile\s+(?:methodolog(?:y|ies)|framework|sprints?|development|environment|practices?|workflow|teams?|coach|ceremonies)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:in\s+an?|using|with)\s+Agile\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:Skills?|Methodologies?)\s*:[^.\n]*\bAgile\b", text_str, re.IGNORECASE))
        )
        if is_non_tech and not tech_agile:
            return False
        return tech_agile or (not is_non_tech and bool(re.search(r"\bAgile\b", text_str)))

    if norm_skill == "lambda":
        is_non_tech = bool(re.search(
            r"\bLambda\s+(?:Chi|Phi|Theta|Alpha|Legal|variant|parameter|calculus)\b",
            text_str,
            re.IGNORECASE,
        ))
        tech_lambda = (
            bool(re.search(r"\bAWS\s+Lambda\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\bLambda\s+(?:functions?|expressions?|architecture|handlers?|serverless)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:serverless|cloud)\s+Lambda\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:built|developed|running|deploying|deployed)\s+(?:in|on|with)\s+Lambda\b", text_str, re.IGNORECASE))
        )
        if is_non_tech and not tech_lambda:
            return False
        return tech_lambda

    if norm_skill == "shell":
        is_non_tech = bool(re.search(
            r"\b(?:in\s+a\s+nutshell|sea\s+shell|egg\s+shell|shell\s+company|royal\s+dutch\s+shell|shell\s+(?:gas|oil|petroleum))\b",
            text_str,
            re.IGNORECASE,
        ))
        tech_shell = (
            bool(re.search(r"\bShell\s+(?:scripts?|scripting|commands?|prompt|environment)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:Unix|Linux|Bash|Zsh)\s+Shell\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:Bash|PowerShell|cmd)\s*[,/&]\s*Shell\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\bShell\s*[,/&]\s*(?:Bash|PowerShell)\b", text_str, re.IGNORECASE))
            or bool(re.search(r"\b(?:in|using|with)\s+Shell\b", text_str, re.IGNORECASE))
        )
        if is_non_tech and not tech_shell:
            return False
        return tech_shell

    if norm_skill == "c":
        # Positive: C/C++, C & C++, C, Python, C programming, language C
        # Negative: c. 2020, Vitamin C, Grade C, or lowercase 'c'
        if bool(re.search(r"\b[Cc]\.\s*\d+|\bvitamin\s+c\b|\bgrade\s+c\b", text_str, re.IGNORECASE)):
            return False
        tech_c = (
            bool(re.search(r"(?<![A-Za-z0-9])C\s*/\s*C\+\+(?![A-Za-z0-9+])", text_str))
            or bool(re.search(r"\bC\s+(?:programming|language|developer|code|compiler)\b", text_str))
            or bool(re.search(r"(?<![A-Za-z0-9])(?:C\+\+|Python|Java|Rust|Go|Assembly)\s*[,/&]\s*C\b", text_str))
            or bool(re.search(r"\bC\s*[,/&]\s*(?:C\+\+|Python|Java|Rust|Go|Assembly)(?![A-Za-z0-9+])", text_str))
            or bool(re.search(r"\b(?:written\s+in|using|in)\s+C\b", text_str))
            or bool(re.search(r"\b(?:Languages?|Technologies?|Skills?)\s*:[^.\n]*\bC\b", text_str))
        )
        return tech_c

    return False


def _skill_in_text(skill: str, text: str, check_aliases: bool = True) -> bool:
    if not skill or not text:
        return False
    norm_skill = skill.strip().lower()
    if norm_skill in AMBIGUOUS_SKILLS:
        return _match_ambiguous_skill(norm_skill, text)

    norm_text = _clean_for_boundary_matching(text)
    norm_skill_clean = _clean_for_boundary_matching(skill)
    if not norm_skill_clean:
        return False
    escaped = re.escape(norm_skill_clean).replace(r"\ ", r"\s+")
    pattern = rf"(?<![a-zA-Z0-9+#.]){escaped}(?![a-zA-Z0-9+#.])"
    if bool(re.search(pattern, norm_text)):
        return True
    if not check_aliases:
        return False
    # Common tech aliases without recursion
    if norm_skill in {"node", "node.js"}:
        target = "node.js" if norm_skill == "node" else "node"
        return _skill_in_text(target, text, check_aliases=False)
    if norm_skill in {"golang", "go"}:
        target = "go" if norm_skill == "golang" else "golang"
        return _skill_in_text(target, text, check_aliases=False)
    if norm_skill in {"k8s", "kubernetes"}:
        target = "k8s" if norm_skill == "kubernetes" else "kubernetes"
        return _skill_in_text(target, text, check_aliases=False)
    if norm_skill in {"rest", "restful"}:
        target = "restful" if norm_skill == "rest" else "rest"
        if _skill_in_text(target, text, check_aliases=False):
            return True
    if norm_skill in {"rest api", "restful api", "rest apis", "restful apis"}:
        for alt in {"rest api", "restful api", "rest apis", "restful apis", "rest", "restful"}:
            if alt != norm_skill and _skill_in_text(alt, text, check_aliases=False):
                return True
    if norm_skill == "ci/cd" and bool(re.search(r"\bci\s*/\s*cd\b", norm_text)):
        return True
    return False


def extract_jd_hard_skills(jd: str) -> list[str]:
    if not jd or not jd.strip():
        return []
    found_skills: set[str] = set()
    for skill in HARD_TECH_SKILLS:
        if skill in EXPERIENCE_VOCABULARY_STOPWORDS:
            continue
        if _skill_in_text(skill, jd):
            found_skills.add(skill)
    return sorted(found_skills)


def count_kw_coverage(text: str, jd: str, source_text: str = "") -> int:
    jd_skills = extract_jd_hard_skills(jd)
    if not jd_skills:
        return 30
    source_skills = {s for s in jd_skills if _skill_in_text(s, source_text)} if source_text else set()
    matches = 0
    for s in jd_skills:
        if _skill_in_text(s, text):
            # If source_text is provided, reward keyword only if supported by candidate's source resume
            if not source_text or s in source_skills:
                matches += 1
    return min(int((matches / len(jd_skills)) * 100), 100)


router = APIRouter()


# Sentinel returned when the optimizer's number guard fires but cannot fall
# back to the original text (e.g. original was also ungrounded).
# The UI must detect this sentinel and prompt the user to add evidence.
SUMMARY_NOT_SUPPORTED = "ADD_EVIDENCE_REQUIRED"
# SUMMARY_FALLBACK_SUMMARY is intentionally not defined here.
# The fallback path now returns the original user summary (or the sentinel)
# rather than fabricating an ML Engineer identity.
SUMMARY_BUZZWORD_RE = re.compile(
    r"\b(production-grade|applied engineering work|reliable deployment practices|"
    r"practical, measurable|maintainable solutions|delivery quality|"
    r"scalable infrastructure practices|workflow automation|user-centered product delivery|"
    r"significantly improved|greatly enhanced|various improvements|multiple systems|"
    r"improved system efficiency|improved throughput|enhanced performance|"
    r"scaled systems|optimized workflows)\b",
    re.IGNORECASE,
)
SUMMARY_BANNED_OPENER_RE = re.compile(
    r"^(uses|has knowledge of|has experience in|is skilled in|worked on|i|my)\b",
    re.IGNORECASE,
)
SUMMARY_WEAK_PHRASES_RE = re.compile(
    r"\b(with experience in|has experience in|has knowledge of|is skilled in|worked on|proficient in|knowledge of)\b",
    re.IGNORECASE,
)
SUMMARY_EMAIL_RE = re.compile(r"[\w.-]+@[\w.-]+\.\w+")
SUMMARY_PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-()]{8,}\d)")
SUMMARY_PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?%")
SUMMARY_COUNT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:k|m|b)?\+?\s*(?:daily\s+|monthly\s+)?(?:users|requests|data points|transactions|patients|entries|patient records|records|samples?)\b",
    re.IGNORECASE,
)
SUMMARY_DURATION_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ms|milliseconds?|s|sec|secs|seconds?)\b",
    re.IGNORECASE,
)
SUMMARY_TOOL_NAMES = [
    "Apache Spark", "Kubernetes", "TensorFlow", "Scikit-learn", "PostgreSQL",
    "JavaScript", "TypeScript", "FastAPI", "PyTorch", "Docker", "Python",
    "Pandas", "NumPy", "Airflow", "Kafka", "MLflow", "React", "Node.js",
    "AWS", "Azure", "GCP", "SQL", "Java", "Git",
]
SUMMARY_DOMAIN_PATTERNS = [
    (r"\b(data pipelines?|etl|data processing)\b", "data pipelines"),
    (r"\b(model deployment|model serving|inference|mlops)\b", "model deployment"),
    (r"\b(computer vision|image processing|opencv)\b", "computer vision"),
    (r"\b(nlp|natural language|text classification|language model)\b", "NLP"),
    (r"\b(predictive modeling|forecasting|classification|regression)\b", "predictive modeling"),
    (r"\b(backend|api|microservices?|fastapi|node\.?js)\b", "backend systems"),
    (r"\b(cloud|aws|azure|gcp|deployment)\b", "cloud deployment"),
    (r"\b(sql|database|postgresql|mysql|mongodb)\b", "database systems"),
]

GROUNDING_TECH_TERMS = tuple(sorted(set(SUMMARY_TOOL_NAMES + [
    "Angular", "Vue", "Vue.js", "MySQL", "MongoDB", "SQLite", "Django",
    "Flask", "Express", "Next.js", "Spring Boot", "Tailwind", "HTML",
    "CSS", "Redis", "GraphQL", "REST", "JDBC", "OpenCV", "NLTK",
    "spaCy", "Hugging Face", "LangChain", "LlamaIndex", "OpenAI",
]), key=len, reverse=True))
GROUNDING_METRIC_RE = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\s*(?:(?:\+|%|k|m|b)\s*)?"
    r"(?:emails?\s*/\s*day|daily\s+emails?|daily\s+users?|monthly\s+users?|"
    r"concurrent\s+users?|parking\s+slots?|vehicle\s+records?|patient\s+records?|"
    r"data\s+points?|users?|requests?|records?|transactions?|patients?|entries|"
    r"samples?|rows?|queries?|tickets?|accuracy|uptime|latency|ms|milliseconds?|"
    r"seconds?|minutes?|hours?)\b"
    r"|\b\d[\d,]*(?:\.\d+)?\s*(?:%|\+|k|m|b)\b",
    re.IGNORECASE,
)
GROUNDING_ESTIMATE_PREFIX_RE = re.compile(
    r"(~|about|around|approx\.?|approximately|estimated|up to|as many as|range of)\s*$",
    re.IGNORECASE,
)
NUMBER_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:[~<>]=?\s*)?"
    r"\d[\d,]*(?:\.\d+)?\s*(?:[KkMmBb])?\+?%?"
    r"(?:\s*(?:ms|milliseconds?|s|sec|secs|seconds?))?"
    r"(?![A-Za-z0-9])"
)
NUMBER_WORD_RE = re.compile(r"[A-Za-z][A-Za-z+#./-]*")
NUMBER_CONTEXT_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into",
    "of", "on", "or", "the", "through", "to", "using", "via", "with",
    "is", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "than", "over", "up", "down", "about", "around",
    "approx", "approximately", "nearly", "almost", "all", "both", "each",
    "achieved", "achieve", "achieving", "improved", "improve", "improving",
    "increased", "increase", "increasing", "reduced", "reduce", "reducing",
    "decreased", "decrease", "decreasing", "reached", "reaching",
    "boosted", "boosting", "scaled", "scaling", "delivered", "delivering",
    "resulted", "resulting", "saved", "saving", "exceeded", "exceeding",
    "percent", "percentage", "pct", "more", "less", "well", "also", "out",
}


def _normalize_grounding_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _split_preserving_parens(text: str) -> list[str]:
    """Splits a string by commas, pipes, semicolons, bullets outside parentheses."""
    items = []
    current = []
    depth = 0
    for char in text:
        if char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
        elif depth == 0 and char in ",|;•\t":
            part = "".join(current).strip()
            if part:
                items.append(part)
            current = []
        else:
            current.append(char)
    last = "".join(current).strip()
    if last:
        items.append(last)
    return items


def _contains_grounded_term(haystack: str, term: str) -> bool:
    cleaned = _normalize_grounding_text(term)
    if not cleaned:
        return False
    # Check parenthetical skills like "AWS (S3, EC2)"
    m = re.match(r"^([^(]+)\s*\(([^)]+)\)$", str(term or "").strip())
    if m:
        base = m.group(1).strip()
        inner_items = [x.strip() for x in m.group(2).split(",") if x.strip()]
        if _contains_grounded_term(haystack, base) and all(_contains_grounded_term(haystack, it) for it in inner_items):
            return True
    pattern = re.escape(cleaned).replace(r"\ ", r"\s+")
    if bool(re.search(rf"(?<![A-Za-z0-9]){pattern}(?![A-Za-z0-9])", haystack, re.IGNORECASE)):
        return True
    # Handle common tech variants / abbreviations
    if cleaned == "rest" and bool(re.search(r"(?<![A-Za-z0-9])restful(?![A-Za-z0-9])", haystack, re.IGNORECASE)):
        return True
    if cleaned == "restful" and bool(re.search(r"(?<![A-Za-z0-9])rest(?![A-Za-z0-9])", haystack, re.IGNORECASE)):
        return True
    if cleaned == "kubernetes" and bool(re.search(r"(?<![A-Za-z0-9])k8s(?![A-Za-z0-9])", haystack, re.IGNORECASE)):
        return True
    if cleaned == "k8s" and bool(re.search(r"(?<![A-Za-z0-9])kubernetes(?![A-Za-z0-9])", haystack, re.IGNORECASE)):
        return True
    if cleaned == "ci/cd" and bool(re.search(r"\bci\s*/\s*cd\b", haystack, re.IGNORECASE)):
        return True
    return False


def _is_grounded_phrase(value: str, source_lower: str, jd_lower: str) -> bool:
    cleaned = _normalize_grounding_text(value)
    return bool(
        cleaned
        and (
            _contains_grounded_term(source_lower, cleaned)
            or _contains_grounded_term(jd_lower, cleaned)
        )
    )


def _split_skill_items(value) -> list[str]:
    if isinstance(value, dict):
        items: list[str] = []
        for nested in value.values():
            items.extend(_split_skill_items(nested))
        return items
    if isinstance(value, (list, tuple, set)):
        items: list[str] = []
        for nested in value:
            items.extend(_split_skill_items(nested))
        return items
    if isinstance(value, str):
        return [item.strip() for item in _split_preserving_parens(value) if item.strip()]
    return []


def _append_grounding_warning(result: dict, kind: str, message: str, values: list[str]):
    if not values:
        return
    warnings = result.setdefault("grounding_warnings", [])
    if isinstance(warnings, list):
        warnings.append({
            "kind": kind,
            "message": message,
            "values": values,
        })
    result["is_suspicious"] = True


def _find_ungrounded_tech_terms(text: str, source_lower: str, jd_lower: str = "") -> list[str]:
    normalized_text = _normalize_grounding_text(text)
    ungrounded: list[str] = []
    # 1. Check curated list of technical terms against source resume
    for term in GROUNDING_TECH_TERMS:
        if not _contains_grounded_term(normalized_text, term):
            continue
        if _contains_grounded_term(source_lower, term):
            continue
        ungrounded.append(term)

    # 2. Check any HARD_TECH_SKILLS entry present in text but absent from source (FIX A)
    for skill in HARD_TECH_SKILLS:
        if not _skill_in_text(skill, text):
            continue
        if _skill_in_text(skill, source_lower):
            continue
        display_name = skill.title() if len(skill) > 2 else skill.upper()
        ungrounded.append(display_name)

    # 3. Check general tech candidates (mixed-case names, symbols, or curated ML markers)
    tech_candidates = re.findall(r"\b[A-Z][a-zA-Z0-9+#.]{2,}\b", text)
    for raw_cand in tech_candidates:
        cand = raw_cand.rstrip(".")
        cand_lower = cand.lower().strip("*")
        if len(cand_lower) < 3 or cand_lower in OPTIMIZER_IGNORED_TECH_TERMS:
            continue
        is_tech = (
            cand_lower in GROUNDING_TECH_TERMS
            or cand_lower in HARD_TECH_SKILLS
            or cand_lower in OPTIMIZER_ML_MARKERS
            or bool(re.search(r"[a-z][A-Z]|[A-Z]{2,}[a-z]|[a-zA-Z][0-9]|[0-9][a-zA-Z]|[+#.]", cand))
        )
        if not is_tech:
            continue
        if not _contains_grounded_term(source_lower, cand_lower) and not _skill_in_text(cand_lower, source_lower):
            ungrounded.append(cand)

    return list(dict.fromkeys(ungrounded))


def _metric_is_estimated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 24):start].lower()
    return bool(GROUNDING_ESTIMATE_PREFIX_RE.search(prefix))


def _metric_is_grounded(metric: str, source_lower: str, jd_lower: str = "") -> bool:
    cleaned = _normalize_grounding_text(metric)
    compact = re.sub(r"\s+", "", cleaned)
    # The source resume is the ONLY valid source for candidate metrics.
    # The JD is NEVER evidence for candidate achievement.
    return (
        cleaned in source_lower
        or compact in re.sub(r"\s+", "", source_lower)
    )


def _clean_quantifiers(text: str) -> str:
    """Preserves hedges by normalising to 'about' (e.g. ~500 -> about 500, approximately 40 -> about 40)."""
    if not text:
        return text
    cleaned = re.sub(r"\bover\s*~\s*(\d)", r"about \1", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"~\s*(\d)", r"about \1", cleaned)
    cleaned = re.sub(r"\bapprox(?:imately|\.)?\s*(\d)", r"about \1", cleaned, flags=re.IGNORECASE)
    return cleaned


def _restore_n_plus_forms(improved_text: str, original_text: str) -> str:
    """
    FIX H: Ensure "N+" forms survive as written (e.g. 500K+, 40K+, 60+, 120+).
    """
    if not improved_text or not original_text:
        return improved_text
    n_plus_matches = re.findall(r"\b(\d+[\d,]*(?:[KkMmBb])?)\+", original_text)
    result = improved_text
    for base in n_plus_matches:
        pattern = rf"\b{re.escape(base)}(?!\+|\%|\/|\.)\b"
        if re.search(pattern, result):
            result = re.sub(pattern, f"{base}+", result, count=1)
    return result


def _mark_ungrounded_metrics(text: str, source_lower: str, jd_lower: str) -> tuple[str, list[str]]:
    flagged: list[str] = []

    def replace_metric(match: re.Match) -> str:
        metric = match.group(0)
        following = text[match.end():match.end() + 12]
        if re.match(r"\s*years?\b", following, flags=re.IGNORECASE):
            return metric
        if _metric_is_estimated(text, match.start()):
            return metric
        if _metric_is_grounded(metric, source_lower, jd_lower):
            return metric
        flagged.append(metric.strip())
        return f"~{metric.replace('+', '')}"

    cleaned_text = _clean_quantifiers(text)
    return GROUNDING_METRIC_RE.sub(replace_metric, cleaned_text), list(dict.fromkeys(flagged))


def _number_token_variants(value: str) -> set[str]:
    cleaned = re.sub(r"\*", "", str(value or "")).strip().lower()
    cleaned = re.sub(r"^(?:~|<|>|<=|>=|about|around|approx\.?|approximately)\s*", "", cleaned)
    cleaned = cleaned.replace(",", "")
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = re.sub(r"(milliseconds?|secs?|seconds?|ms|s)$", "", cleaned)
    cleaned = cleaned.rstrip("%").rstrip("+")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([kmb])?", cleaned)
    if not match:
        return set()

    number, suffix = match.groups()
    variants = {number}
    if "." in number:
        variants.add(number.rstrip("0").rstrip("."))
    if suffix:
        multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[suffix]
        expanded = float(number) * multiplier
        variants.add(str(int(expanded)) if expanded.is_integer() else str(expanded))
    return {variant for variant in variants if variant}


def _source_number_variants(source_text: str) -> set[str]:
    variants: set[str] = set()
    for match in NUMBER_TOKEN_RE.finditer(str(source_text or "")):
        variants.update(_number_token_variants(match.group(0)))
    return variants


def _number_after_context_words(text: str, end: int) -> list[str]:
    after_segment = str(text or "")[end:end + 64]
    next_number = NUMBER_TOKEN_RE.search(after_segment)
    if next_number:
        after_segment = after_segment[:next_number.start()]
    after = re.split(r"[.;:\n\r]", after_segment, maxsplit=1)[0]
    return [
        word.lower().strip(".")
        for word in NUMBER_WORD_RE.findall(after)
        if word.lower().strip(".") not in NUMBER_CONTEXT_STOPWORDS
    ][:3]


def _number_before_context_words(text: str, start: int) -> list[str]:
    before = re.split(r"[.;:\n\r]", str(text or "")[max(0, start - 48):start])[-1]
    return [
        word.lower().strip(".")
        for word in NUMBER_WORD_RE.findall(before)
        if word.lower().strip(".") not in NUMBER_CONTEXT_STOPWORDS
    ][-2:]


def _number_context_words(text: str, start: int, end: int) -> list[str]:
    return _number_after_context_words(text, end) or _number_before_context_words(text, start)


def _number_word_keys(words: list[str]) -> set[str]:
    keys: set[str] = set()
    for word in words:
        cleaned = re.sub(r"[^a-z0-9+#.]+", "", word.lower())
        if not cleaned:
            continue
        keys.add(cleaned)
        if cleaned.endswith("ies") and len(cleaned) > 3:
            keys.add(f"{cleaned[:-3]}y")
        elif cleaned.endswith("s") and len(cleaned) > 3:
            keys.add(cleaned[:-1])
    return keys


def _source_contexts_for_number(
    source_text: str,
    variants: set[str],
    include_before: bool = False,
) -> list[set[str]]:
    contexts: list[set[str]] = []
    source = str(source_text or "")
    for match in NUMBER_TOKEN_RE.finditer(source):
        if not (_number_token_variants(match.group(0)) & variants):
            continue
        after_keys = _number_word_keys(_number_after_context_words(source, match.end()))
        if after_keys:
            contexts.append(after_keys)
        if include_before or not after_keys:
            contexts.append(_number_word_keys(_number_before_context_words(source, match.start())))
    return contexts


NUMBER_GENERIC_WORDS = {"model", "models", "using", "used", "use", "built", "build", "achieving", "reaching",
                        "reached", "achieved", "held", "test", "set", "data", "system", "service", "new",
                        "across", "based", "improved", "reduced", "cut", "by", "from", "to"}
NUMBER_QUALIFIERS = {"concurrent", "daily", "monthly", "weekly", "yearly", "annual",
                     "active", "peak", "simultaneous", "hourly"}
NUMBER_WINDOW = 6


def _ws(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or ""))


def _number_window_keys(text: str, start: int, end: int) -> set[str]:
    left = NUMBER_WORD_RE.findall(text[max(0, start - 90):start])[-NUMBER_WINDOW:]
    right = NUMBER_WORD_RE.findall(text[end:end + 90])[:NUMBER_WINDOW]
    words = [w.lower().strip(".") for w in left + right]
    words = [w for w in words if w and w not in NUMBER_CONTEXT_STOPWORDS and w not in NUMBER_GENERIC_WORDS]
    return _number_word_keys(words)


def _number_context_is_grounded(text, start, end, source_text, variants) -> bool:
    source = _ws(source_text)                      # join PDF line wraps first
    if not variants or variants.isdisjoint(_source_number_variants(source)):
        return False                               # number is not in the resume at all
    src_lower = source.lower()
    near = " ".join(NUMBER_WORD_RE.findall(text[max(0, start - 40):end + 40])).lower().split()
    if any(q in near and q not in src_lower for q in NUMBER_QUALIFIERS):
        return False                               # "40K+" -> "40K+ concurrent" inflation
    mine = _number_window_keys(text, start, end)
    if not mine:
        return True

    raw = str(text[start:end] or "")
    is_pct = "%" in raw

    after_target_keys = set()
    if not is_pct:
        after_target = [w.lower().strip(".") for w in NUMBER_WORD_RE.findall(text[end:end + 40])[:3]
                        if w.lower() not in NUMBER_CONTEXT_STOPWORDS and w.lower() not in NUMBER_GENERIC_WORDS]
        after_target_keys = _number_word_keys(after_target)

    for m in NUMBER_TOKEN_RE.finditer(source):
        if _number_token_variants(m.group(0)) & variants:
            src_win = _number_window_keys(source, m.start(), m.end())
            if mine & src_win:
                if after_target_keys:
                    src_after = [w.lower().strip(".") for w in NUMBER_WORD_RE.findall(source[m.end():m.end() + 40])[:3]
                                 if w.lower() not in NUMBER_CONTEXT_STOPWORDS and w.lower() not in NUMBER_GENERIC_WORDS]
                    src_after_keys = _number_word_keys(src_after)
                    if src_after_keys and not (after_target_keys & src_after_keys):
                        continue
                return True                        # shares a content word with ANY occurrence
    return False


_VERSION_PRECEDER_RE = re.compile(r"([A-Za-z][A-Za-z0-9+#.\-]*)\s*$")


def _version_key(text: str, start: int, end: int) -> Optional[tuple[str, str]]:
    """(preceding word, number) for version identifiers such as 'OAuth 2.0' or 'Python 3.11'.

    Only bare dotted numbers qualify (no %, K/M suffix, or unit), so metrics like '2.0 seconds' or '40%'
    are never treated as versions.
    """
    raw = str(text or "")[start:end].strip()
    if not re.fullmatch(r"\d+(?:\.\d+)+", raw):
        return None
    m = _VERSION_PRECEDER_RE.search(str(text or "")[max(0, start - 24):start])
    if not m:
        return None
    return (m.group(1).lower().rstrip("."), raw)


def _source_version_keys(source_text: str) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    src = str(source_text or "")
    for match in NUMBER_TOKEN_RE.finditer(src):
        key = _version_key(src, match.start(), match.end())
        if key:
            keys.add(key)
    return keys


def _find_ungrounded_numbers(text: str, source_text: str) -> list[dict[str, str]]:
    source_variants = _source_number_variants(source_text)
    source_version_keys = _source_version_keys(source_text)
    ungrounded: list[dict[str, str]] = []
    for match in NUMBER_TOKEN_RE.finditer(str(text or "")):
        raw = re.sub(r"\s+", " ", match.group(0)).strip()
        variants = _number_token_variants(raw)
        if not variants:
            continue
        if variants.isdisjoint(source_variants):
            reason_code = "number_absent_from_source"
            logger.warning(
                "optimizer.guard_trip: code=%s number=%s context=%s",
                reason_code,
                raw,
                str(text or "")[:80],
            )
            ungrounded.append({"number": raw, "reason": reason_code})
            continue
        if not _number_context_is_grounded(text, match.start(), match.end(), source_text, variants):
            # 'OAuth 2.0', 'Python 3.11': a version identifier already present in the source
            # (same preceding word) is not a metric, so differing trailing words cannot "mismatch" it.
            version_key = _version_key(str(text or ""), match.start(), match.end())
            if version_key and version_key in source_version_keys:
                continue
            reason_code = "source_context_mismatch"
            logger.warning(
                "optimizer.guard_trip: code=%s number=%s context=%s",
                reason_code,
                raw,
                str(text or "")[:80],
            )
            ungrounded.append({"number": raw, "reason": reason_code})
    return ungrounded


def _append_number_grounding_warning(result: dict):
    warnings = result.setdefault("grounding_warnings", [])
    if isinstance(warnings, list):
        warnings.append({
            "kind": "numbers",
            "message": (
                "Generated numeric claims absent from the source resume were "
                "reverted or removed before returning."
            ),
            "values": ["source-only numeric guard applied"],
        })
    result["is_suspicious"] = True
    result["number_grounding_applied"] = True


def _sanitize_numbered_generated_value(value, source_text: str, path: str, user_id: str):
    if isinstance(value, str):
        ungrounded = _find_ungrounded_numbers(value, source_text)
        if ungrounded:
            logger.warning(
                "Optimizer number guard removed generated value at %s for user %s: %s",
                path,
                user_id,
                ungrounded,
            )
            return ""
        return value
    if isinstance(value, list):
        sanitized = []
        for index, item in enumerate(value):
            clean_item = _sanitize_numbered_generated_value(
                item,
                source_text,
                f"{path}[{index}]",
                user_id,
            )
            if clean_item not in ("", [], {}):
                sanitized.append(clean_item)
        return sanitized
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            clean_item = _sanitize_numbered_generated_value(
                item,
                source_text,
                f"{path}.{key}",
                user_id,
            )
            if clean_item not in ("", [], {}):
                sanitized[key] = clean_item
        return sanitized
    return value


def _enforce_source_number_grounding(result: dict, resume_text: str, user_id: str = "") -> dict:
    if not isinstance(result, dict):
        return result

    source_text = str(resume_text or "")
    guard_applied = False

    for index, bullet_obj in enumerate(result.get("improved_bullets") or []):
        if not isinstance(bullet_obj, dict):
            continue
        improved = str(bullet_obj.get("improved", "") or "")
        ungrounded = _find_ungrounded_numbers(improved, source_text)
        if not ungrounded:
            continue
        logger.warning(
            "Optimizer number guard reverted improved_bullets[%s] for user %s: %s",
            index,
            user_id,
            ungrounded,
        )
        bullet_obj["improved"] = str(bullet_obj.get("original") or "")
        bullet_obj["keywords_added"] = []
        bullet_obj["metric_added"] = ""
        bullet_obj["improvement_reason"] = (
            "Kept original bullet because the generated rewrite introduced numeric claims absent from the source resume."
        )
        guard_applied = True

    for index, bullet_obj in enumerate(result.get("improved_bullets") or []):
        if not isinstance(bullet_obj, dict):
            continue
        for key, value in list(bullet_obj.items()):
            if key in {"original", "improved", "source_id", "entry_id", "section"}:
                continue
            sanitized = _sanitize_numbered_generated_value(
                value,
                source_text,
                f"improved_bullets[{index}].{key}",
                user_id,
            )
            if sanitized != value:
                bullet_obj[key] = sanitized
                guard_applied = True

    safe_new_bullets = []
    for index, bullet_obj in enumerate(result.get("new_bullets") or []):
        if not isinstance(bullet_obj, dict):
            continue
        text = str(bullet_obj.get("text", "") or "")
        ungrounded = _find_ungrounded_numbers(text, source_text)
        if ungrounded:
            logger.warning(
                "Optimizer number guard removed new_bullets[%s] for user %s: %s",
                index,
                user_id,
                ungrounded,
            )
            guard_applied = True
            continue
        sanitized_bullet = _sanitize_numbered_generated_value(
            bullet_obj,
            source_text,
            f"new_bullets[{index}]",
            user_id,
        )
        if sanitized_bullet != bullet_obj:
            guard_applied = True
        safe_new_bullets.append(sanitized_bullet)
    result["new_bullets"] = safe_new_bullets

    summary = str(result.get("optimized_summary", "") or "")
    if summary and _find_ungrounded_numbers(summary, source_text):
        logger.warning(
            "Optimizer number guard triggered for optimized_summary, user %s: ungrounded numbers=%s",
            user_id,
            _find_ungrounded_numbers(summary, source_text),
        )
        # Use the original user-provided summary text if available and grounded.
        # If the source summary exists and passes grounding, return it unchanged.
        original_summary = str(result.get("original_summary", "") or "")
        parsed_doc = None
        if not original_summary and source_text:
            try:
                parsed_doc = parse_source_resume(source_text)
                if parsed_doc and parsed_doc.summary:
                    original_summary = parsed_doc.summary.strip()
            except Exception:
                pass
        original_ungrounded = _find_ungrounded_numbers(original_summary, source_text) if original_summary else True
        if original_summary and not original_ungrounded:
            result["optimized_summary"] = original_summary
            result["original_summary"] = original_summary
        else:
            fallback = _build_skills_education_summary(source_text, result, doc=parsed_doc)
            if fallback and not _find_ungrounded_numbers(fallback, source_text):
                result["optimized_summary"] = fallback
            else:
                result["optimized_summary"] = original_summary if original_summary else ""
            result["summary_grounding_note"] = (
                "The AI-generated summary contained metrics that could not be verified against your resume. "
                "Please add quantified achievements (numbers, percentages, scale) to your resume "
                "to generate a grounded summary."
            )
        guard_applied = True

    for key in (
        "optimized_skills",
        "skills_to_highlight",
        "added_keywords",
        "missing_keywords",
        "improvement_explanation",
        "ats_tips",
        "overall_improvement",
    ):
        if key in result:
            sanitized = _sanitize_numbered_generated_value(result[key], source_text, key, user_id)
            if sanitized != result[key]:
                result[key] = sanitized
                guard_applied = True

    # The UI already has a deterministic keyword-coverage fallback for this
    # display value. Do not return an LLM-invented score as candidate data.
    for key in ("match_score_estimate", "confidence_level"):
        if key in result:
            logger.warning(
                "Optimizer number guard removed model-controlled %s for user %s",
                key,
                user_id,
            )
            result.pop(key, None)
            guard_applied = True

    if guard_applied:
        _append_number_grounding_warning(result)
    return result


def _audit_resume_numbers_against_source(result: dict, source_text: str) -> list[dict[str, str]]:
    rows_by_number: dict[str, dict[str, str]] = {}
    source_variants = _source_number_variants(source_text)
    for piece in _resume_number_audit_pieces(result):
        for match in NUMBER_TOKEN_RE.finditer(piece):
            number = re.sub(r"\s+", " ", match.group(0)).strip()
            key = number.lower()
            variants = _number_token_variants(number)
            appears = bool(variants and not variants.isdisjoint(source_variants))
            grounded = appears and _number_context_is_grounded(
                piece,
                match.start(),
                match.end(),
                source_text,
                variants,
            )
            if appears and not grounded:
                version_key = _version_key(str(piece or ""), match.start(), match.end())
                if version_key and version_key in _source_version_keys(source_text):
                    grounded = True
            status = "yes" if appears and grounded else "no"
            existing = rows_by_number.get(key)
            if existing is None or status == "no":
                rows_by_number[key] = {
                    "number": number,
                    "appears_in_source": status,
                }
    return list(rows_by_number.values())


# Re-exported from services.resume_structure
# _extract_source_skill_groups is imported above


def _extract_source_skills(resume_text: str) -> list[str]:
    groups = _extract_source_skill_groups(resume_text)
    skills: list[str] = []
    for grp_items in groups.values():
        for s in grp_items:
            if s not in skills:
                skills.append(s)

    if not skills:
        # Fallback if no explicit skills section found
        try:
            from routers.job_match import extract_skills
            for skill in extract_skills(resume_text):
                m = re.search(rf"\b{re.escape(skill)}\b", resume_text, re.IGNORECASE)
                display = m.group(0) if m else skill.title()
                if not any(display.lower() == s.lower() for s in skills):
                    skills.append(display)
        except Exception:
            pass

    return skills


def _is_skills_empty(s) -> bool:
    if not s:
        return True
    if isinstance(s, dict):
        return not any(bool(items) for items in s.values())
    if isinstance(s, (list, tuple, set)):
        return len(s) == 0
    return False


CANONICAL_TECH_LOOKUP = {
    "ci/cd": "CI/CD", "xgboost": "XGBoost", "sql": "SQL", "pandas": "Pandas", "numpy": "NumPy",
    "pytorch": "PyTorch", "scikit-learn": "scikit-learn", "sklearn": "scikit-learn", "fastapi": "FastAPI",
    "docker": "Docker", "git": "Git", "mlflow": "MLflow", "aws": "AWS", "linux": "Linux",
    "c++": "C++", "python": "Python", "opencv": "OpenCV", "onnx": "ONNX", "bert": "BERT",
    "resnet": "ResNet", "resnet-50": "ResNet-50", "flask": "Flask",
    "hugging face transformers": "Hugging Face Transformers", "transformers": "Transformers",
    "feature engineering": "Feature Engineering", "model inference": "Model Inference",
    "kubernetes": "Kubernetes", "jenkins": "Jenkins", "spark": "Spark", "kafka": "Kafka",
    "ec2": "EC2", "s3": "S3",
}


def _extract_tech_tokens_from_bullets_and_projects(resume_text: str, doc: Optional[ResumeDocument] = None) -> list[str]:
    tokens: list[str] = []
    if doc is None and resume_text:
        try:
            doc = parse_source_resume(resume_text)
        except Exception:
            doc = None

    if doc:
        for p in doc.projects:
            header = p.header_raw or ""
            if "|" in header:
                parts = header.split("|")
                stack_part = DATE_PATTERN.sub("", parts[1]).strip()
                for raw_item in _split_preserving_parens(stack_part):
                    cleaned = raw_item.strip()
                    if not cleaned:
                        continue
                    c_low = cleaned.lower()
                    if c_low in CANONICAL_TECH_LOOKUP:
                        tokens.append(CANONICAL_TECH_LOOKUP[c_low])
                    else:
                        tokens.append(cleaned)
        for b in doc.all_bullets:
            text = b.original or ""
            for kw, canonical in CANONICAL_TECH_LOOKUP.items():
                if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                    tokens.append(canonical)
    elif resume_text:
        for kw, canonical in CANONICAL_TECH_LOOKUP.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", resume_text, re.IGNORECASE):
                tokens.append(canonical)

    return list(dict.fromkeys(tokens))


def _reorder_by_jd_relevance(skills: list[str], jd_text: str = "") -> list[str]:
    if not skills or not jd_text:
        return skills
    jd_lower = jd_text.lower()

    def score_skill(skill: str) -> int:
        s_clean = skill.strip().lower()
        s_base = re.sub(r"\s*\([^)]*\)", "", s_clean).strip()
        count = jd_lower.count(s_base) if s_base else 0
        if count == 0 and s_clean != s_base:
            count = jd_lower.count(s_clean)
        return count

    return sorted(skills, key=lambda s: score_skill(s), reverse=True)





def _validate_against_source(result: dict, resume_text: str, jd: str) -> dict:
    if not isinstance(result, dict):
        return result

    source_lower = _normalize_grounding_text(resume_text)
    jd_lower = _normalize_grounding_text(jd or "")
    dropped_skills: list[str] = []
    jd_gap_fill_skills: list[str] = []

    def filter_skill_list(items) -> list[str]:
        kept: list[str] = []
        for skill in _split_skill_items(items):
            if _contains_grounded_term(source_lower, skill):
                kept.append(skill)
            elif _contains_grounded_term(jd_lower, skill):
                # JD-only skills are GAPS, NOT candidate skills!
                jd_gap_fill_skills.append(skill)
            else:
                dropped_skills.append(skill)
        return list(dict.fromkeys(kept))

    source_skills = _extract_source_skills(resume_text)
    source_groups = _extract_source_skill_groups(resume_text)
    tech_tokens = _extract_tech_tokens_from_bullets_and_projects(resume_text)

    # Detect parenthetical detailed forms across source and tech tokens (e.g. "AWS (S3, EC2)")
    parenthetical_map: dict[str, str] = {}
    for s in list(source_skills) + list(tech_tokens):
        m = re.match(r"^([^(]+)\s*\(([^)]+)\)$", str(s or "").strip())
        if m:
            base = m.group(1).strip().lower()
            parenthetical_map[base] = str(s).strip()

    # Combined target skills that MUST be in output_skills:
    # superset invariant: set(source_skills) ⊆ set(output_skills)
    # plus any tech token appearing in bullets or project stack lines
    combined_target_skills = []
    seen_target_lower = set()
    for s in list(source_skills) + list(tech_tokens):
        s_clean = str(s or "").strip()
        if not s_clean:
            continue
        s_low = s_clean.lower()
        if s_low in parenthetical_map and "(" not in s_clean:
            s_clean = parenthetical_map[s_low]
            s_low = s_clean.lower()
        if s_low not in seen_target_lower:
            combined_target_skills.append(s_clean)
            seen_target_lower.add(s_low)

    skills = result.get("optimized_skills")
    if _is_skills_empty(skills):
        if source_groups:
            result["optimized_skills"] = {k: list(v) for k, v in source_groups.items()}
        else:
            result["optimized_skills"] = combined_target_skills
        result["skills_optimization_failed"] = True
    elif isinstance(skills, dict):
        for category, items in list(skills.items()):
            kept = filter_skill_list(items)
            dropped = [
                skill for skill in _split_skill_items(items)
                if skill not in kept and not _contains_grounded_term(source_lower, skill)
            ]
            skills[category] = kept
            if dropped:
                logger.warning(f"Dropped ungrounded skills in {category}: {dropped}")

        if _is_skills_empty(skills):
            result["optimized_skills"] = source_groups if source_groups else combined_target_skills
            result["skills_optimization_failed"] = True
        else:
            # FIX D3: Preserve source groups and their order
            if source_groups:
                key_map: dict[str, str] = {}
                for src_k in source_groups.keys():
                    match_cat = next((cat for cat in skills if cat.lower() == src_k.lower()), None)
                    if not match_cat:
                        match_cat = next((cat for cat in skills if src_k.lower() in cat.lower() or cat.lower() in src_k.lower()), None)
                    if match_cat:
                        key_map[src_k] = match_cat

                if key_map:
                    ordered_keys = list(dict.fromkeys(list(key_map.values()) + list(skills.keys())))
                else:
                    ordered_keys = list(dict.fromkeys(list(source_groups.keys()) + list(skills.keys())))

                ordered_skills: dict[str, list[str]] = {k: [] for k in ordered_keys}
                for cat, items in skills.items():
                    target_cat = cat if cat in ordered_skills else None
                    if not target_cat:
                        for src_k, mapped_k in key_map.items():
                            if cat.lower() in src_k.lower() or src_k.lower() in cat.lower() or cat.lower() in mapped_k.lower():
                                target_cat = mapped_k
                                break
                    for item in items:
                        if target_cat:
                            ordered_skills[target_cat].append(item)
                        else:
                            item_low = item.lower()
                            if any(k in item_low for k in ["python", "sql", "c++", "java", "javascript", "golang", "rust", "typescript", "bash"]) and any("language" in k.lower() for k in ordered_skills):
                                t_g = next(k for k in ordered_skills if "language" in k.lower())
                                ordered_skills[t_g].append(item)
                            elif any(k in item_low for k in ["pytorch", "scikit", "pandas", "numpy", "transformers", "xgboost", "tensor", "model", "feature engineering", "opencv", "onnx", "bert", "resnet"]) and any("ml" in k.lower() or "data" in k.lower() for k in ordered_skills):
                                t_g = next(k for k in ordered_skills if "ml" in k.lower() or "data" in k.lower())
                                ordered_skills[t_g].append(item)
                            elif any("tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower() for k in ordered_skills):
                                t_g = next(k for k in ordered_skills if "tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower())
                                ordered_skills[t_g].append(item)
                            else:
                                ordered_skills[list(ordered_skills.keys())[0]].append(item)
                skills = ordered_skills

            # Keep Feature Engineering under ML & Data if ML & Data exists
            if "ML & Data" in skills:
                has_fe = any("feature engineering" in s.lower() for s in combined_target_skills) or any(
                    any("feature engineering" in s.lower() for s in items) for items in skills.values()
                )
                if has_fe:
                    for grp, items in list(skills.items()):
                        if grp != "ML & Data":
                            skills[grp] = [x for x in items if "feature engineering" not in x.lower()]
                    if not any("feature engineering" in s.lower() for s in skills["ML & Data"]):
                        skills["ML & Data"].append("Feature Engineering")

            # Output skills ⊇ source skills + tech tokens: ensure all combined_target_skills are present
            existing_flat = {s.lower() for v in skills.values() for s in (v if isinstance(v, list) else [v])}
            for src_skill in combined_target_skills:
                lower_src = src_skill.lower()
                base_src = re.sub(r"\s*\([^)]*\)", "", lower_src).strip()
                if any(lower_src == s.lower() or (base_src == re.sub(r"\s*\([^)]*\)", "", s.lower()).strip() and "(" in s) for s in existing_flat):
                    continue

                added = False
                if ("feature engineering" in lower_src or "opencv" in lower_src) and any("ml" in k.lower() or "data" in k.lower() for k in skills):
                    target_g = next(k for k in skills if "ml" in k.lower() or "data" in k.lower())
                    skills[target_g].append(src_skill)
                    added = True
                elif any(k in lower_src for k in ["python", "sql", "c++", "java", "javascript", "golang", "rust", "typescript", "bash"]) and any("language" in k.lower() for k in skills):
                    target_g = next(k for k in skills if "language" in k.lower())
                    skills[target_g].append(src_skill)
                    added = True
                elif any(k in lower_src for k in ["pytorch", "scikit", "pandas", "numpy", "transformers", "xgboost", "tensor", "model", "onnx", "bert", "resnet"]) and any("ml" in k.lower() or "data" in k.lower() for k in skills):
                    target_g = next(k for k in skills if "ml" in k.lower() or "data" in k.lower())
                    skills[target_g].append(src_skill)
                    added = True
                elif any(k in lower_src for k in ["docker", "git", "ci/cd", "fastapi", "aws", "linux", "cloud", "mlflow", "flask", "kubernetes", "jenkins"]) and any("tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower() for k in skills):
                    target_g = next(k for k in skills if "tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower())
                    skills[target_g].append(src_skill)
                    added = True
                if not added:
                    src_cat = next((cat for cat, items in source_groups.items() if any(src_skill.lower() == it.lower() for it in items)), None)
                    if src_cat and src_cat in skills:
                        skills[src_cat].append(src_skill)
                        added = True
                if not added and source_groups:
                    target_g = list(skills.keys())[-1]
                    skills[target_g].append(src_skill)
                    added = True
                if added:
                    existing_flat.add(lower_src)

            # Dedupe case-insensitively and merge "AWS" with "AWS (S3, EC2)" keeping detailed form
            for base, detailed in parenthetical_map.items():
                has_detailed = any(any(detailed.lower() == s.lower() for s in items) for items in skills.values())
                if has_detailed:
                    for cat in skills:
                        skills[cat] = [s for s in skills[cat] if s.lower() != base]

            # Reorder each category by JD relevance only (no cap)
            for category in skills:
                if isinstance(skills[category], list):
                    seen_in_cat = set()
                    deduped_cat = []
                    for s in skills[category]:
                        if s.lower() not in seen_in_cat:
                            seen_in_cat.add(s.lower())
                            deduped_cat.append(s)
                    skills[category] = _reorder_by_jd_relevance(deduped_cat, jd)

            result["optimized_skills"] = skills

    elif isinstance(skills, list):
        filtered = filter_skill_list(skills)
        if not filtered:
            result["optimized_skills"] = combined_target_skills
            result["skills_optimization_failed"] = True
        else:
            flat_lower = {s.lower() for s in filtered}
            for src_skill in combined_target_skills:
                if src_skill.lower() not in flat_lower:
                    filtered.append(src_skill)
                    flat_lower.add(src_skill.lower())
            result["optimized_skills"] = _reorder_by_jd_relevance(filtered, jd)

    if _is_skills_empty(result.get("optimized_skills")):
        result["optimized_skills"] = source_skills
        result["skills_optimization_failed"] = True

    for key in ("skills_to_highlight", "added_keywords"):
        if isinstance(result.get(key), list):
            result[key] = filter_skill_list(result.get(key))

    dropped_unique = list(dict.fromkeys(dropped_skills))
    if dropped_unique:
        result["dropped_ungrounded_skills"] = dropped_unique
        _append_grounding_warning(
            result,
            "skills",
            "Dropped skills that were absent from both the source resume and job description.",
            dropped_unique,
        )

    gap_fill_unique = list(dict.fromkeys(jd_gap_fill_skills))
    if gap_fill_unique:
        result["jd_gap_fill_skills"] = gap_fill_unique
        missing = result.setdefault("missing_keywords", [])
        if isinstance(missing, list):
            for g_skill in gap_fill_unique:
                if g_skill not in missing:
                    missing.append(g_skill)

    for collection_key, text_key in (("improved_bullets", "improved"), ("new_bullets", "text")):
        for bullet_obj in result.get(collection_key) or []:
            if not isinstance(bullet_obj, dict):
                continue
            bullet_text = str(bullet_obj.get(text_key, "") or "")
            if not bullet_text:
                continue

            orig_bullet = str(bullet_obj.get("original", "") or "")
            if bullet_obj.get("status") == "reverted_by_guard" or (orig_bullet and bullet_text == orig_bullet):
                bullet_obj[text_key] = orig_bullet
                continue
            bullet_text = _clean_quantifiers(bullet_text)
            if orig_bullet:
                bullet_text = _restore_n_plus_forms(bullet_text, orig_bullet)
            bullet_obj[text_key] = bullet_text

            ungrounded_terms = _find_ungrounded_tech_terms(bullet_text, source_lower, jd_lower)
            if ungrounded_terms:
                _append_grounding_warning(
                    result,
                    "bullet_technology",
                    f"Flagged {collection_key} item containing ungrounded technology terms.",
                    ungrounded_terms,
                )
                logger.warning(
                    f"Flagged ungrounded technologies in {collection_key}: {ungrounded_terms}"
                )

            softened_text, flagged_metrics = _mark_ungrounded_metrics(
                bullet_text,
                source_lower,
                jd_lower,
            )
            if flagged_metrics:
                bullet_obj[text_key] = softened_text
                if text_key == "improved":
                    existing_reason = str(bullet_obj.get("improvement_reason") or "").strip()
                    metric_reason = (
                        "Ungrounded metrics were marked as estimates because they were absent "
                        "from the source resume and JD."
                    )
                    bullet_obj["improvement_reason"] = (
                        f"{existing_reason} {metric_reason}".strip()
                        if existing_reason else metric_reason
                    )
                _append_grounding_warning(
                    result,
                    "metrics",
                    f"Marked ungrounded metrics in {collection_key} as estimates.",
                    ["ungrounded metric claim"],
                )
                logger.warning(
                    f"Marked ungrounded metrics in {collection_key}: {flagged_metrics}"
                )

    return result


def _extract_source_bullet_metrics(text: str) -> list[str]:
    """
    Extracts all numeric metric tokens from a bullet:
    e.g. '500K+', '0.87', '38%', '40K+', '60+', '8,000', '0.71', '0.84', '200 ms', '54,000', '96%', '120+', '25', '0.91'
    """
    cleaned = _clean_quantifiers(text)
    pattern = re.compile(
        r"\b\d[\d,]*(?:\.\d+)?(?:\s*[kmb]\+?|\+|%|\s*ms)?(?!\w)",
        re.IGNORECASE,
    )
    matches = []
    for m in pattern.finditer(cleaned):
        token = m.group(0).strip()
        if token and re.search(r"\d", token):
            matches.append(token)
    return matches


def _all_source_metrics_present(improved_text: str, original_text: str) -> bool:
    """
    Returns True if every metric token present in original_text is also found in improved_text.
    Numbers match as whole numeric tokens ('5' must not match '2025').
    """
    orig_metrics = _extract_source_bullet_metrics(original_text)
    if not orig_metrics:
        return True
    imp_clean = _clean_quantifiers(improved_text).lower().replace(",", "")
    for m in orig_metrics:
        m_norm = m.lower().replace(",", "").strip()
        # Full token with % or + if present, with boundaries
        pat_norm = rf"(?<![A-Za-z0-9]){re.escape(m_norm)}(?![A-Za-z0-9])"
        if re.search(pat_norm, imp_clean):
            continue
        # Base number check: whole numeric token
        m_base = re.sub(r"[\+%]", "", m_norm).strip()
        if m_base:
            pat_base = rf"(?<![0-9]){re.escape(m_base)}(?![0-9])"
            if re.search(pat_base, imp_clean):
                continue
        return False
    return True


def _validate_optimized_structure(
    first: Any,
    second: Any = None,
    job_title: str = "",
    user_id: str = "",
    doc: Optional[ResumeDocument] = None,
    resume_text: str = "",
) -> dict:
    """
    Code owns structure, the LLM only rewrites bullet text.
    Enforces:
    - Parse resume into structured sections once, keeping a source_id on every bullet.
    - The LLM may only return {source_id: rewritten_text} for existing bullets.
      Ignore any id not in the source. Never accept new bullets, entries or headings from the model.
    - Rebuild output from the source structure. Contact, education, skills (all groups, deduped),
      certifications and entry order are copied from the source, never from the model.
    - Summary: keep source summary verbatim. Replace it only if rewrite passes grounding and is longer than 15 words.
    - Section ownership, entry counts, and original hierarchy strictly preserved.
    """
    if isinstance(first, ResumeDocument):
        doc = first
        result = second if isinstance(second, dict) else {}
    elif isinstance(first, dict):
        result = first
        if isinstance(second, ResumeDocument):
            doc = second
        elif isinstance(second, str):
            resume_text = second
    else:
        result = second if isinstance(second, dict) else {}

    if not isinstance(result, dict):
        return result

    if doc is None and resume_text:
        try:
            doc = parse_source_resume(resume_text)
        except Exception:
            pass

    if doc is None:
        return result

    if not resume_text and doc and doc.raw_text:
        resume_text = doc.raw_text

    bullet_map = doc.bullet_map
    valid_source_ids = set(bullet_map.keys())

    # Step 1: Collect incoming rewrites and explanations from result (C3, C4).
    # Accepts {source_id: text}, {"bullet_rewrites": {source_id: text}}, or {"improved_bullets": [...]}
    raw_incoming: dict[str, dict[str, Any]] = {}
    matched_by_source_id = 0
    matched_by_original = 0
    unmatched_count = 0

    norm_to_bullet: dict[str, Any] = {}
    for b in doc.all_bullets:
        norm_to_bullet[" ".join(b.original.lower().split())] = b

    if isinstance(result.get("bullet_rewrites"), dict):
        for sid, val in result["bullet_rewrites"].items():
            s_key = str(sid).strip()
            imp_text = str(val.get("improved") or val.get("text") or val if isinstance(val, dict) else val or "").strip()
            if s_key in valid_source_ids:
                raw_incoming[s_key] = {"text": imp_text}
                matched_by_source_id += 1
            else:
                norm_key = " ".join(s_key.lower().split())
                matched_b = norm_to_bullet.get(norm_key)
                if matched_b:
                    raw_incoming[matched_b.source_id] = {"text": imp_text}
                    matched_by_original += 1
                else:
                    unmatched_count += 1

    for k, v in list(result.items()):
        if k in valid_source_ids and k not in raw_incoming:
            imp_text = str(v.get("improved") or v.get("text") or v if isinstance(v, dict) else v or "").strip()
            raw_incoming[k] = {"text": imp_text}
            matched_by_source_id += 1

    for bullet_obj in result.get("improved_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        sid = str(bullet_obj.get("source_id") or "").strip()
        imp = str(bullet_obj.get("improved") or bullet_obj.get("text") or "").strip()
        orig = str(bullet_obj.get("original") or "").strip()
        kw_added = bullet_obj.get("keywords_added") or []
        m_added = str(bullet_obj.get("metric_added") or "")
        imp_reason = str(bullet_obj.get("improvement_reason") or "")

        target_id = None
        if sid in valid_source_ids:
            target_id = sid
            matched_by_source_id += 1
        elif orig:
            norm_orig = " ".join(orig.lower().split())
            matched_b = norm_to_bullet.get(norm_orig)
            if matched_b:
                target_id = matched_b.source_id
                matched_by_original += 1
            else:
                unmatched_count += 1
        else:
            unmatched_count += 1

        if target_id and imp:
            raw_incoming[target_id] = {
                "text": imp,
                "keywords_added": kw_added,
                "metric_added": m_added,
                "improvement_reason": imp_reason,
            }

    result["rewrite_matching_metadata"] = {
        "matched_by_source_id": matched_by_source_id,
        "matched_by_original": matched_by_original,
        "unmatched_count": unmatched_count,
    }

    # Step 2: Build validated rewrites for EVERY bullet in doc.all_bullets (B4, B5, C3, C9)
    source_lower = _normalize_grounding_text(doc.raw_text)
    validated_rewrites: dict[str, dict[str, Any]] = {}

    for b in doc.all_bullets:
        source_id = b.source_id
        inc = raw_incoming.get(source_id)
        if not inc or not inc.get("text"):
            improved_text = b.original
            status = "no_rewrite_returned"
            improvement_reason = ""
            keywords_added = []
            metric_added = ""
        elif inc.get("status") == "reverted_by_guard" or inc.get("text") == b.original:
            improved_text = b.original
            status = inc.get("status") or "no_rewrite_returned"
            improvement_reason = inc.get("improvement_reason") or ""
            keywords_added = []
            metric_added = ""
        else:
            cand_text = inc["text"]
            cand_text = re.sub(r"\s*\(?continued\)?\s*", " ", cand_text, flags=re.IGNORECASE).strip()
            cand_text = re.sub(r"\s+", " ", cand_text).strip()
            cand_text = _clean_quantifiers(cand_text)
            cand_text = _restore_n_plus_forms(cand_text, b.original)

            revert_reason = ""
            # Guard 1: Technology terms
            ungrounded_tech = _find_ungrounded_tech_terms(cand_text, source_lower)
            if ungrounded_tech:
                revert_reason = f"introduced skills absent from source ({', '.join(ungrounded_tech)})"

            # Guard 2: Numbers (B5)
            if not revert_reason and _find_ungrounded_numbers(cand_text, b.original):
                revert_reason = "introduced ungrounded metrics/numbers absent from source"

            # Guard 3: Claim verbs scoped to entry/bullet (B4, B5)
            if not revert_reason:
                all_entries = (doc.experience or []) + (doc.projects or [])
                entry = next((e for e in all_entries if e.entry_id == b.entry_id), None)
                entry_header = entry.header_raw if entry else ""
                source_scope = f"{entry_header} {b.original}".strip()
                unsupported_verb = _find_unsupported_claim_verb(cand_text, source_scope)
                if unsupported_verb:
                    revert_reason = f"introduced unsupported claim verb '{unsupported_verb}'"

            # Guard 4: Source metrics preserved (C9)
            if not revert_reason and not _all_source_metrics_present(cand_text, b.original):
                revert_reason = "dropped or altered verified source metrics"

            if revert_reason:
                improved_text = b.original
                status = "reverted_by_guard"
                improvement_reason = inc.get("improvement_reason") or f"Kept original bullet because the generated rewrite {revert_reason}."
                keywords_added = []
                metric_added = ""
            else:
                improved_text = cand_text
                status = "rewritten" if cand_text != b.original else "no_rewrite_returned"
                improvement_reason = inc.get("improvement_reason") or ""
                keywords_added = inc.get("keywords_added") or []
                metric_added = inc.get("metric_added") or ""

        validated_rewrites[source_id] = {
            "source_id": source_id,
            "section": b.section,
            "original": b.original,
            "improved": improved_text,
            "keywords_added": keywords_added,
            "metric_added": metric_added,
            "improvement_reason": improvement_reason,
            "status": status,
        }

    status_counts = {
        "rewritten": sum(1 for v in validated_rewrites.values() if v["status"] == "rewritten"),
        "reverted_by_guard": sum(1 for v in validated_rewrites.values() if v["status"] == "reverted_by_guard"),
        "no_rewrite_returned": sum(1 for v in validated_rewrites.values() if v["status"] == "no_rewrite_returned"),
    }
    result["rewrite_status_counts"] = status_counts

    # Step 3: Never accept new bullets, entries, or headings from the model
    result["new_bullets"] = []
    result["improved_bullets"] = [validated_rewrites[b.source_id] for b in doc.all_bullets]
    result["bullet_rewrites"] = {b.source_id: validated_rewrites[b.source_id]["improved"] for b in doc.all_bullets}

    # Step 4: Summary handling
    # Keep source summary verbatim. Replace only if rewrite passes grounding and is longer than 15 words.
    source_summary = (doc.summary or "").strip()
    if not source_summary and result.get("original_summary"):
        source_summary = str(result["original_summary"]).strip()
    if not source_summary and resume_text:
        try:
            parsed_doc = parse_source_resume(resume_text)
            if parsed_doc and parsed_doc.summary:
                source_summary = parsed_doc.summary.strip()
        except Exception:
            pass

    if source_summary:
        source_summary = re.sub(r"^(?:professional\s+)?summary[:|-]?\s*", "", source_summary, flags=re.IGNORECASE).strip()

    candidate_summary = str(result.get("optimized_summary") or "").strip()
    cand_words = [w for w in candidate_summary.split() if w]
    cand_passes_grounding = False
    if len(cand_words) > 15:
        is_val, _ = _verify_optimizer_summary(candidate_summary, resume_text, job_title)
        no_ungrounded_nums = not _find_ungrounded_numbers(candidate_summary, resume_text)
        cand_passes_grounding = is_val and no_ungrounded_nums

    if source_summary:
        if cand_passes_grounding and candidate_summary != source_summary:
            summary = candidate_summary
        else:
            summary = source_summary
    else:
        if cand_passes_grounding:
            summary = candidate_summary
        else:
            summary = _build_skills_education_summary(resume_text, result, doc=doc)

    result["optimized_summary"] = summary

    # Step 5: Rebuild output from the source structure deterministically.
    # Contact, education, skills (all groups, deduped), certifications and entry order
    # are copied from the source, never from the model.
    reconstructed = reconstruct_resume_structure(
        doc=doc,
        bullet_rewrites=validated_rewrites,
        optimized_summary=summary,
        optimized_skills=None,  # Copied from source, never model!
    )

    result["reconstructed_resume"] = reconstructed
    result["experience_entries"] = reconstructed["experience"]
    result["project_entries"] = reconstructed["projects"]

    # A3-g: Maintain JD-relevance ORDER over the SAME source skill set
    prior_skills = result.get("optimized_skills")
    source_skills = reconstructed.get("skills") or []
    if isinstance(source_skills, list) and isinstance(prior_skills, list) and prior_skills:
        source_skill_set = set(source_skills)
        seen = set()
        ordered = []
        for s in prior_skills:
            if s in source_skill_set and s not in seen:
                seen.add(s)
                ordered.append(s)
        for s in source_skills:
            if s not in seen:
                seen.add(s)
                ordered.append(s)
        result["optimized_skills"] = ordered
        result["reconstructed_resume"]["skills"] = ordered
    else:
        result["optimized_skills"] = source_skills

    # Record entry counts
    result["original_experience_count"] = doc.experience_count
    result["optimized_experience_count"] = len(reconstructed["experience"])
    result["original_project_count"] = doc.project_count
    result["optimized_project_count"] = len(reconstructed["projects"])
    result["original_education_count"] = doc.education_count
    result["optimized_education_count"] = len(reconstructed["education"])
    result["original_certification_count"] = doc.certification_count
    result["optimized_certification_count"] = len(reconstructed["certifications"])

    return result


def _summary_clean_text(value: str) -> str:
    text = str(value or "")
    text = SUMMARY_EMAIL_RE.sub("", text)
    text = SUMMARY_PHONE_RE.sub("", text)
    text = re.sub(r"[\u2026]|\.{2,}", ".", text)
    text = re.sub(r"\*\*", "", text)
    text = SUMMARY_WEAK_PHRASES_RE.sub("focused on", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _summary_word_count(value: str) -> int:
    return len(re.findall(r"\b[\w+#.%-]+\b", value or ""))


def _summary_role(raw_role: str = "") -> str:
    cleaned = _summary_clean_text(raw_role)
    cleaned = re.sub(r"^(target role|role|job title)\s*[:|-]\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[.]+$", "", cleaned).strip()
    lowered = cleaned.lower()
    if re.search(r"\b(machine learning engineer|ml engineer|ai engineer)\b", lowered):
        return "Machine Learning Engineer"
    if "data scientist" in lowered:
        return "Data Scientist"
    if re.search(r"data analyst|analytics", lowered):
        return "Data Analyst"
    if re.search(r"frontend|front-end|react", lowered):
        return "Frontend Engineer"
    if re.search(r"backend|back-end|api", lowered):
        return "Backend Engineer"
    if re.search(r"full stack|full-stack", lowered):
        return "Full Stack Engineer"
    if re.search(r"devops|cloud|site reliability|sre", lowered):
        return "Cloud Engineer"
    if "software" in lowered:
        return "Software Engineer"
    return cleaned.title() if cleaned else "Software Engineer"


def _summary_skill_items(value) -> list[str]:
    items: list[str] = []
    if isinstance(value, dict):
        for group_values in value.values():
            items.extend(_summary_skill_items(group_values))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            items.extend(_summary_skill_items(item))
    elif value:
        text = _summary_clean_text(str(value))
        for part in re.split(r"[,|;/]", text):
            cleaned = re.sub(r"^[A-Za-z &]+:\s*", "", part.strip())
            if cleaned:
                items.append(cleaned)
    return items


def _summary_top_skills(result: dict, resume_text: str = "") -> list[str]:
    candidates: list[str] = []
    for key in ("optimized_skills", "skills_to_highlight", "added_keywords"):
        candidates.extend(_summary_skill_items(result.get(key)))

    in_skills_section = False
    for raw_line in str(resume_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^(skills|technical skills|core skills|technologies)\b", line, re.IGNORECASE):
            in_skills_section = True
            continue
        if in_skills_section and re.match(
            r"^(experience|work experience|education|projects|certifications|summary|profile|objective)\b",
            line,
            re.IGNORECASE,
        ):
            break
        if in_skills_section:
            candidates.extend(_summary_skill_items(line))

    seen: set[str] = set()
    skills: list[str] = []
    for item in candidates:
        cleaned = re.sub(r"\s+", " ", str(item or "").strip())
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        if SUMMARY_EMAIL_RE.search(cleaned) or SUMMARY_PHONE_RE.search(cleaned):
            continue
        seen.add(key)
        skills.append(cleaned)
        if len(skills) == 5:
            break
    return skills


def _summary_domains(job_description: str = "", result: dict | None = None, role: str = "") -> list[str]:
    result = result or {}
    jd_text = _summary_clean_text(job_description)
    keyword_text = " ".join(_summary_skill_items(result.get("added_keywords")))
    text = f"{jd_text} {keyword_text}".lower()
    domains: list[str] = []

    for pattern, domain in SUMMARY_DOMAIN_PATTERNS:
        if re.search(pattern, text) and domain not in domains:
            domains.append(domain)

    if len(domains) < 2 and re.search(r"\b(machine learning|ml engineer|data scientist)\b", text):
        for fallback_domain in ("predictive modeling", "model deployment"):
            if fallback_domain not in domains:
                domains.append(fallback_domain)

    if len(domains) < 2 and re.search(r"\b(ai|artificial intelligence)\b", text):
        for fallback_domain in ("scalable AI systems", "data pipelines"):
            if fallback_domain not in domains:
                domains.append(fallback_domain)

    if len(domains) < 2 and "machine learning engineer" in role.lower():
        for fallback_domain in ("scalable AI systems", "data pipelines"):
            if fallback_domain not in domains:
                domains.append(fallback_domain)

    return domains[:2]


def _summary_key_tools(
    job_description: str = "",
    resume_text: str = "",
    optimized_skills: list[str] | None = None,
    sentence_text: str = "",
) -> list[str]:
    source = f"{job_description} {resume_text}"
    skill_keys = {re.sub(r"[^a-z0-9+#.]+", " ", skill.lower()).strip() for skill in (optimized_skills or [])}
    sentence_lower = sentence_text.lower()
    tools: list[str] = []
    for tool in SUMMARY_TOOL_NAMES:
        tool_pattern = re.escape(tool).replace(r"\ ", r"\s+")
        if not re.search(rf"\b{tool_pattern}\b", source, re.IGNORECASE):
            continue
        key = re.sub(r"[^a-z0-9+#.]+", " ", tool.lower()).strip()
        if key in skill_keys or tool.lower() in sentence_lower:
            continue
        if key in {"ai", "machine learning"}:
            continue
        tools.append(tool)
        if len(tools) == 3:
            break
    return tools


def _summary_metric_value(metric: str) -> float:
    match = re.search(r"\d+(?:\.\d+)?", metric or "")
    if not match:
        return 0
    value = float(match.group(0))
    lowered = metric.lower()
    if "k" in lowered:
        value *= 1_000
    elif "m" in lowered:
        value *= 1_000_000
    elif "b" in lowered:
        value *= 1_000_000_000
    return value


def _summary_duration_value_ms(metric: str) -> float:
    match = re.search(r"\d+(?:\.\d+)?", metric or "")
    if not match:
        return 0
    value = float(match.group(0))
    lowered = metric.lower()
    if re.search(r"\b(s|sec|secs|second|seconds)\b", lowered):
        value *= 1_000
    return value


def _summary_best_duration_pair(text: str) -> tuple[str, str]:
    metrics = SUMMARY_DURATION_RE.findall(_summary_clean_text(text))
    if len(metrics) < 2:
        return ("", "")
    ordered = sorted(metrics, key=_summary_duration_value_ms, reverse=True)
    start, end = ordered[0], ordered[-1]
    if _summary_duration_value_ms(start) <= _summary_duration_value_ms(end):
        return ("", "")
    return (start, end)


def _summary_best_duration(text: str) -> str:
    metrics = SUMMARY_DURATION_RE.findall(_summary_clean_text(text))
    if not metrics:
        return ""
    return min(metrics, key=_summary_duration_value_ms)


def _summary_best_metric(text: str) -> str:
    cleaned = _summary_clean_text(text)
    percentages = SUMMARY_PERCENT_RE.findall(cleaned)
    if percentages:
        return max(percentages, key=_summary_metric_value)

    count_metrics = [
        metric.strip()
        for metric in SUMMARY_COUNT_RE.findall(cleaned)
        if not re.fullmatch(r"(19|20)\d{2}", metric.strip())
    ]
    if count_metrics:
        return max(count_metrics, key=_summary_metric_value)
    return ""


def _summary_best_percent(text: str) -> str:
    percentages = SUMMARY_PERCENT_RE.findall(_summary_clean_text(text))
    return max(percentages, key=_summary_metric_value) if percentages else ""


def _summary_best_count(text: str) -> str:
    count_metrics = [
        metric.strip()
        for metric in SUMMARY_COUNT_RE.findall(_summary_clean_text(text))
        if not re.fullmatch(r"(19|20)\d{2}", metric.strip())
    ]
    return max(count_metrics, key=_summary_metric_value) if count_metrics else ""


def _summary_large_count(count_metric: str) -> str:
    return count_metric if _summary_metric_value(count_metric) >= 10_000 else ""


def _summary_scale_suffix(count_metric: str, context: str = "") -> str:
    if not count_metric:
        return ""
    if _summary_large_count(count_metric):
        return f" for {count_metric}"
    if re.search(r"\b(data|records|patients|entries|pipeline|processing|dataset)\b", context, re.IGNORECASE):
        return " for records"
    return " for source workflows"


def _summary_impact_method(text: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if re.search(r"pipeline|processing|automation|automated|etl", lowered):
        return "optimizing data pipelines"
    if re.search(r"docker|kubernetes|deploy|production|cloud", lowered):
        return "optimizing production systems"
    if re.search(r"java|jdbc|database|sql|query", lowered):
        return "optimizing database queries"
    if re.search(r"html|css|webpage|interface|frontend|react", lowered):
        return "optimizing frontend interfaces"
    if re.search(r"\b(?:model|model\s+training|machine\s+learning|prediction|classifier)\b", lowered):
        return "optimizing model deployment"
    if re.search(r"api|backend|service", lowered):
        return "optimizing backend services"
    return ""


def _summary_metric_action(text: str, metric_type: str = "") -> str:
    lowered = _summary_clean_text(text).lower()
    if re.search(r"\b(reduced|reduce|reducing|decreased|decrease|lowered|cut|shortened)\b", lowered):
        return "Reduced"
    if re.search(r"\b(increased|increase|increasing|scaled|grew|expanded)\b", lowered):
        return "Increased"
    if re.search(r"\b(improved|improve|improving|boosted|raised|enhanced|achieved)\b", lowered):
        return "Improved"
    if metric_type == "accuracy":
        return "Improved"
    if metric_type == "scale":
        return "Increased"
    return "Reduced" if re.search(r"\b(latency|processing|retrieval|query|load|response|time)\b", lowered) else "Improved"


def _summary_metric_system(text: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if re.search(r"\b(pipeline|etl|data processing|batch|workflow)\b", lowered):
        return "data pipelines"
    if re.search(r"\b(model|training|classifier|prediction|accuracy|inference|mlops)\b", lowered):
        return "model deployment"
    if re.search(r"\b(api|backend|service|database|query|sql|retrieval|latency|request)\b", lowered):
        return "backend systems"
    if re.search(r"\b(docker|kubernetes|cloud|deploy|production)\b", lowered):
        return "production systems"
    return "backend systems"


def _summary_metric_outcome(text: str, metric_type: str, action: str, system: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if metric_type == "accuracy" or re.search(r"\b(accuracy|precision|recall|f1|auc|score)\b", lowered):
        return "model accuracy"
    if re.search(r"\b(retrieval|query|database|sql)\b", lowered):
        return "data retrieval time"
    if re.search(r"\b(processing|pipeline|etl|batch)\b", lowered):
        return "data processing time"
    if re.search(r"\b(latency|response time|load time)\b", lowered):
        return "latency"
    if metric_type == "scale":
        if system == "data pipelines":
            return "pipeline capacity"
        if system == "model deployment":
            return "model serving capacity"
        return "backend capacity"
    if system == "data pipelines":
        return "data processing time" if action == "Reduced" else "pipeline efficiency"
    if system == "model deployment":
        return "model deployment"
    return "backend efficiency"


def _summary_metric_context(text: str, metric_type: str, system: str) -> str:
    lowered = _summary_clean_text(text).lower()
    count_metric = _summary_best_count(text)
    if count_metric:
        return f"handling {count_metric}"
    if re.search(r"\b(patient|patients|clinical|healthcare|medical)\b", lowered):
        return "patient data workflows"
    if re.search(r"\b(query|queries|database|sql|retrieval)\b", lowered):
        return "database queries"
    if re.search(r"\b(record|records)\b", lowered):
        return "record processing"
    if re.search(r"\b(data point|data points|sample|samples|dataset|datasets|batch)\b", lowered):
        return "dataset processing"
    if re.search(r"\b(request|requests|api)\b", lowered):
        return "API requests"
    if re.search(r"\b(user|users|traffic)\b", lowered):
        return "user workflows"
    if re.search(r"\b(model|inference|prediction|classifier)\b", lowered):
        return "model workflows"
    if system == "data pipelines":
        return "data pipeline workflows"
    if system == "model deployment":
        return "model workflows"
    return "backend workflows"


def _summary_metric_type(text: str, metric: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if metric.endswith("%") and re.search(r"\b(accuracy|precision|recall|f1|auc|score)\b", lowered):
        return "accuracy"
    if metric.endswith("%"):
        return "percentage"
    return "scale"


def _summary_metric_record(text: str, metric: str, metric_type: str = "") -> dict:
    cleaned = _summary_clean_text(text)
    resolved_type = metric_type or _summary_metric_type(cleaned, metric)
    action = _summary_metric_action(cleaned, resolved_type)
    system = _summary_metric_system(cleaned)
    outcome = _summary_metric_outcome(cleaned, resolved_type, action, system)
    context = _summary_metric_context(cleaned, resolved_type, system)
    return {
        "metric_value": metric,
        "metric_type": resolved_type,
        "action": action,
        "system": system,
        "outcome": outcome,
        "context": context,
        "source_text": cleaned,
        "score": _summary_metric_value(metric),
    }


def _summary_performance_record(text: str, start_duration: str, end_duration: str) -> dict:
    cleaned = _summary_clean_text(text)
    system = _summary_metric_system(cleaned)
    return {
        "metric_value": f"from {start_duration} to {end_duration}",
        "metric_type": "performance",
        "action": "Reduced",
        "system": system,
        "outcome": _summary_metric_outcome(cleaned, "performance", "Reduced", system),
        "context": _summary_metric_context(cleaned, "performance", system),
        "source_text": cleaned,
        "score": _summary_duration_value_ms(start_duration) - _summary_duration_value_ms(end_duration),
    }


def _summary_metric_source_lines(result: dict, resume_text: str = "") -> list[str]:
    candidates: list[str] = []
    fallback_candidates: list[str] = []
    section_open = False
    section_found = False
    section_start_re = re.compile(
        r"^(work\s+experience|professional\s+experience|experience|employment|projects?|"
        r"project\s+experience|academic\s+projects?|personal\s+projects?)\b",
        re.IGNORECASE,
    )
    section_end_re = re.compile(
        r"^(education|skills|technical\s+skills|core\s+skills|certifications?|"
        r"summary|profile|objective|contact|achievements?|awards?)\b",
        re.IGNORECASE,
    )

    for raw_line in str(resume_text or "").splitlines():
        raw = raw_line.strip()
        line = re.sub(r"^[\s\-*\u2022\u25cf\u25aa]+", "", raw)
        if not line:
            continue
        if section_start_re.match(line):
            section_open = True
            section_found = True
            continue
        if section_open and section_end_re.match(line):
            section_open = False
            continue
        if section_open:
            candidates.append(line)
        elif re.match(r"^[\-*\u2022\u25cf\u25aa]\s+", raw):
            fallback_candidates.append(line)

    if not section_found:
        candidates.extend(fallback_candidates)

    seen: set[str] = set()
    clean_candidates: list[str] = []
    for candidate in candidates:
        cleaned = _summary_clean_text(candidate)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        clean_candidates.append(cleaned)
    return clean_candidates


def _summary_extract_metric_records(result: dict, resume_text: str = "") -> list[dict]:
    records: list[dict] = []
    for line in _summary_metric_source_lines(result, resume_text):
        start_duration, end_duration = _summary_best_duration_pair(line)
        if start_duration and end_duration:
            records.append(_summary_performance_record(line, start_duration, end_duration))
        for metric in SUMMARY_PERCENT_RE.findall(line):
            records.append(_summary_metric_record(line, metric))
        for metric in SUMMARY_COUNT_RE.findall(line):
            metric = metric.strip()
            if re.fullmatch(r"(19|20)\d{2}", metric):
                continue
            records.append(_summary_metric_record(line, metric, "scale"))

    return records


def _summary_metric_priority(record: dict) -> tuple:
    metric_type = record.get("metric_type", "")
    source = record.get("source_text", "")
    metric_value = float(record.get("score") or 0)
    action_bonus = 1 if re.search(
        r"\b(reduced|decreased|cut|lowered|improved|increased|optimized)\b",
        source,
        re.IGNORECASE,
    ) else 0

    if metric_type in {"percentage", "accuracy"}:
        if re.search(r"\b(latency|processing|retrieval|query|load time|response time|deployment time|time)\b", source, re.IGNORECASE):
            tie_breaker = 3
        elif metric_type == "percentage":
            tie_breaker = 2
        else:
            tie_breaker = 1
        return (3, metric_value, tie_breaker, action_bonus)

    if metric_type == "performance":
        return (2, metric_value, action_bonus, 0)

    if metric_type == "scale":
        scale_rank = 1 if _summary_metric_value(record.get("metric_value", "")) >= 10_000 else 0
        return (1, scale_rank, metric_value, action_bonus)

    return (0, metric_value, action_bonus, 0)


def _summary_select_metric(result: dict, resume_text: str = "") -> dict:
    records = _summary_extract_metric_records(result, resume_text)
    if not records:
        return {}
    return max(records, key=_summary_metric_priority)


def _summary_metric_sentence(record: dict) -> str:
    action = record.get("action") or "Improved"
    metric = record.get("metric_value") or ""
    metric_type = record.get("metric_type") or ""
    outcome = record.get("outcome") or "system efficiency"
    context = record.get("context") or ""
    context_phrase = (
        f" {context}"
        if context.startswith("handling ")
        else f" for {context}" if context else ""
    )
    method = _summary_impact_method(record.get("source_text", ""))
    method_phrase = f" by {method}" if method else ""

    if metric_type == "accuracy":
        return f"Improved model accuracy to {metric}{method_phrase}{context_phrase}."
    if metric_type == "performance":
        return f"{action} {outcome} {metric}{method_phrase}{context_phrase}."
    if metric_type == "scale":
        return f"{action} {outcome} to {metric}{method_phrase}."
    return f"{action} {outcome} by {metric}{method_phrase}{context_phrase}."


def _summary_join_skills(skills: list[str]) -> str:
    if not skills:
        return ""
    if len(skills) == 1:
        return skills[0]
    if len(skills) == 2:
        return f"{skills[0]} and {skills[1]}"
    return f"{', '.join(skills[:-1])}, and {skills[-1]}"


def _summary_join_tools(tools: list[str]) -> str:
    if not tools:
        return ""
    if len(tools) == 1:
        return tools[0]
    if len(tools) == 2:
        return f"{tools[0]} and {tools[1]}"
    return f"{tools[0]}, {tools[1]}, and {tools[2]}"


def _summary_has_specific_system(result: dict, resume_text: str = "") -> bool:
    source_parts = [resume_text]
    for key in ("improved_bullets", "new_bullets"):
        bullets = result.get(key, [])
        if not isinstance(bullets, list):
            continue
        for bullet in bullets:
            if isinstance(bullet, dict):
                source_parts.append(str(bullet.get("improved") or bullet.get("text") or ""))
            else:
                source_parts.append(str(bullet or ""))
    source = " ".join(source_parts).lower()
    return bool(re.search(
        r"\b(pipeline|model|api|backend|database|dashboard|application|service|deployment|"
        r"classifier|prediction|etl|system|platform)\b",
        source,
    ))


def _summary_complete_sentences(value: str) -> list[str]:
    text = _summary_clean_text(value).replace("!", ".").replace("?", ".")
    matches = re.findall(r"[^.!?]+[.!?]", text)
    sentences: list[str] = []
    seen: set[str] = set()
    for match in matches:
        sentence = re.sub(r"\s+", " ", match).strip()
        sentence = re.sub(r"[.!?]+$", ".", sentence)
        key = re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        sentences.append(sentence[0].upper() + sentence[1:])
    return sentences


def _summary_metrics_valid(summary: str) -> bool:
    lowered = summary.lower()
    count_unit = r"(?:users|records|requests|data points|transactions|patients|entries|patient records|samples?)"
    count_value = rf"\d+(?:\.\d+)?\s*(?:k|m|b)?\+?\s*(?:daily\s+|monthly\s+)?{count_unit}"

    if re.search(rf"\b(accuracy|precision|recall|f1|auc|score|model quality)\b[^.]*\b{count_value}\b", lowered):
        return False
    if re.search(rf"\b{count_value}\b[^.]*\b(accuracy|precision|recall|f1|auc|score|model quality)\b", lowered):
        return False
    if re.search(r"\bimproved\s+by\s+\d+(?:\.\d+)?%", lowered):
        return False
    if re.search(r"\b(improved|enhanced)\s+performance\b(?!\s+by\s+\d+(?:\.\d+)?%)", lowered):
        return False
    if "machine learning" in lowered and "artificial intelligence" in lowered:
        return False
    if "python" in lowered and "coding" in lowered:
        return False
    if "docker" in lowered and "containers" in lowered:
        return False
    return True


def _summary_valid(value: str) -> bool:
    sentences = _summary_complete_sentences(value)
    if len(sentences) != 2:
        return False
    summary = " ".join(sentences)
    if "..." in summary or "\u2026" in summary:
        return False
    if SUMMARY_BUZZWORD_RE.search(summary):
        return False
    if SUMMARY_WEAK_PHRASES_RE.search(summary):
        return False
    if any(SUMMARY_BANNED_OPENER_RE.search(sentence) for sentence in sentences):
        return False
    if not _summary_metrics_valid(summary):
        return False
    if not re.search(r"\b(backend systems|data pipelines|model deployment|production systems)\b", summary, re.IGNORECASE):
        return False
    if not re.search(r"\b(accuracy|latency|uptime|processing|retrieval|deployment|capacity|performance|efficiency|processed|handled|supported)\b", summary, re.IGNORECASE):
        return False
    words = _summary_word_count(summary)
    return words <= 45 and all(sentence.endswith(".") for sentence in sentences)


def _build_skills_education_summary(
    resume_text: str,
    result: dict | None = None,
    doc: Optional[ResumeDocument] = None,
    skills_only: bool = False,
) -> str:
    """
    Plain, verified skills + education fallback line.
    Never returns contact info, raw resume dumps, or fabricated metrics.
    Degree is extracted ONLY from doc.education lines (not the full resume text).
    Never emits "Technical background with core proficiencies in ...".
    Never emits a summary consisting only of a skills list.
    """
    if doc is None and resume_text:
        try:
            doc = parse_source_resume(resume_text)
        except Exception:
            pass

    # If source summary exists and passes grounding, return it unchanged
    orig_summary = (doc.summary if doc and doc.summary else "").strip()
    if not orig_summary and result and result.get("original_summary"):
        orig_summary = str(result["original_summary"]).strip()
    if orig_summary and len(orig_summary) >= 10:
        no_ungrounded = not _find_ungrounded_numbers(orig_summary, resume_text)
        no_contact = not (
            SUMMARY_EMAIL_RE.search(orig_summary)
            or SUMMARY_PHONE_RE.search(orig_summary)
            or re.search(r"https?://|www\.|linkedin\.com|github\.com", orig_summary, re.IGNORECASE)
        )
        if no_ungrounded and no_contact:
            return orig_summary

    # ── Degree extraction — ONLY from parsed education lines ──────────
    degree = ""
    if not skills_only and doc is not None:
        edu_lines: list[str] = list(doc.education or [])
        edu_text = "\n".join(edu_lines)

        _DEGREE_RE = re.compile(
            r"\b(B\.?S\.?|B\.?Tech|B\.?E\.?|Bachelor(?:'s)?|M\.?S\.?|M\.?Tech|M\.?E\.?|Master(?:'s)?|Ph\.?D\.?)"
            r"(?:\s+(?:of|in)\s+|[,\s]+)"
            r"([A-Za-z\s&]+?)"
            r"(?:,|\.|\n|\||–|-|\d{4}|$)",
            re.IGNORECASE,
        )
        edu_match = _DEGREE_RE.search(edu_text) if edu_text else None
        if edu_match:
            degree_type = edu_match.group(1).strip()
            field = edu_match.group(2).strip()
            field_words = [
                w for w in field.split()
                if w.lower() not in (
                    "from", "at", "university", "college", "institute",
                    "gpa", "of", "the", "and",
                )
            ]
            clean_field = " ".join(field_words[:3]).strip()
            if degree_type.replace(".", "").lower() == "ms" and clean_field.lower().startswith("office"):
                clean_field = ""
            if clean_field:
                degree = f"{degree_type} in {clean_field}"

    # ── Extract top verified skills that actually appear in source resume ──
    skills: list[str] = []
    if result and isinstance(result.get("optimized_skills"), dict):
        for group, items in result["optimized_skills"].items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str) and item.lower() in resume_text.lower():
                        skills.append(item)
    if not skills and result:
        skills = _summary_top_skills(result, resume_text)
        skills = [s for s in skills if s.lower() in resume_text.lower()]
    if not skills:
        for kw in [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C",
            "SQL", "Go", "Rust", "React", "Node.js", "Docker", "Git",
            "AWS", "Linux",
        ]:
            if re.search(rf"\b{re.escape(kw)}\b", resume_text, re.IGNORECASE):
                skills.append(kw)

    unique_skills: list[str] = []
    for s in skills:
        if s not in unique_skills and len(unique_skills) < 4:
            unique_skills.append(s)

    skills_text = ", ".join(unique_skills) if unique_skills else "software engineering"

    has_internship = (
        bool(re.search(r"\bintern(?:ship)?s?\b", resume_text, re.IGNORECASE))
        or (doc is not None and any(bool(re.search(r"\bintern(?:ship)?s?\b", str(getattr(e, "title", "") or ""), re.IGNORECASE)) for e in (doc.experience or [])))
    )

    edu_text = "\n".join(doc.education) if (doc is not None and doc.education) else ""
    is_grad = bool(re.search(r"\bgraduate[ds]?\b", edu_text, re.IGNORECASE)) and not bool(re.search(r"\b(?:expected|candidate|current|student)\b", edu_text, re.IGNORECASE))

    if degree:
        degree_label = f"{degree} graduate" if is_grad else degree
        if has_internship:
            return f"{degree_label} with internship experience in {skills_text}."
        return f"{degree_label} with core technical skills in {skills_text}."

    if has_internship:
        return f"Technical background with internship experience in {skills_text}."

    return f"Technical background and foundation in {skills_text}."


def _verify_optimizer_summary(
    summary: str,
    source_text: str,
    job_title: str = "",
) -> tuple[bool, str]:
    """
    Verify summary against source resume (FIX B+C):
    - No contact details (email, phone, address, links)
    - No raw resume text / header dumps
    - Never uses target job title as identity
    - Every number must appear in source (compare numbers, not trailing words)
    - Tech-term scan: skip the FIRST WORD of each sentence, then only flag
      terms that are known lexicon entries (GROUNDING_TECH_TERMS / HARD_TECH_SKILLS)
      or mid-sentence capitalized tokens.  This ensures words like
      "Aspiring", "Motivated", or "Entry-level" do not trip the guard.
    """
    if not summary or not summary.strip():
        return False, "empty_summary"

    clean_summary = summary.strip()

    # 1. Contact info check
    if SUMMARY_EMAIL_RE.search(clean_summary):
        return False, "contains_email"
    if SUMMARY_PHONE_RE.search(clean_summary):
        return False, "contains_phone"
    if re.search(r"https?://|www\.|linkedin\.com|github\.com", clean_summary, re.IGNORECASE):
        return False, "contains_url"
    if re.search(r"\b(phone|tel|email|address|street|pincode|zip code)\s*:", clean_summary, re.IGNORECASE):
        return False, "contains_contact_info"

    # 3. Target job title as identity check
    if job_title:
        target_lower = re.sub(r"\s+", " ", job_title.strip().lower())
        jt_clean = re.sub(r"^(senior|junior|lead|staff|principal)\s+", "", target_lower, flags=re.IGNORECASE).strip()
        if len(jt_clean) > 4:
            first_sentence = clean_summary.split(".")[0].lower()
            title_pat = rf"^(?:(?:senior|junior|lead|staff|principal)\s+)?{re.escape(jt_clean)}\b"
            identity_pat = rf"\b(?:as an?|as a|i am an?|experienced|an?)\s+(?:(?:senior|junior|lead|staff|principal)\s+)?{re.escape(jt_clean)}\b"
            if re.search(title_pat, first_sentence) or re.search(identity_pat, first_sentence):
                # Verify that candidate actually held this title in source experience
                try:
                    from services.professional_resume_pdf import _has_held_title
                    from services.resume_structure import parse_source_resume
                    doc_exp = parse_source_resume(source_text).experience
                    has_held = _has_held_title(job_title, doc_exp, source_text) or _has_held_title(jt_clean, doc_exp, source_text)
                except Exception:
                    has_held = jt_clean in source_text.lower()
                if not has_held:
                    return False, "target_job_title_as_identity"

    # 4. Number check (compare numbers, not trailing words)
    source_variants = _source_number_variants(source_text)
    for match in NUMBER_TOKEN_RE.finditer(clean_summary):
        raw = re.sub(r"\s+", " ", match.group(0)).strip()
        variants = _number_token_variants(raw)
        if not variants:
            continue
        if variants.isdisjoint(source_variants):
            return False, f"ungrounded_number: {raw}"

    # 5. Technical terms check (FIX B) ────────────────────────────────
    # Build a set of character positions that are the first word of a
    # sentence so we can skip them.
    _sentence_first_word_spans: set[tuple[int, int]] = set()
    for sent_match in re.finditer(r"(?:^|[.!?\n]+)\s*([A-Za-z][a-zA-Z0-9+#./-]*)", clean_summary):
        _sentence_first_word_spans.add((sent_match.start(1), sent_match.end(1)))

    source_lower = source_text.lower()

    # Build the combined lexicon set (lowercase) for "is this a known tech term?" checks
    _lexicon_lower: set[str] = set()
    for t in GROUNDING_TECH_TERMS:
        _lexicon_lower.add(t.lower())
    for t in HARD_TECH_SKILLS:
        _lexicon_lower.add(t.lower())

    # Ignored words are common English/resume words that happen to start
    # with a capital letter and are NOT tech terms.
    ignored_words = {
        "the", "this", "with", "and", "for", "built", "developed", "engineered",
        "designed", "implemented", "created", "led", "spearheaded", "proven",
        "strong", "focused", "experienced", "specializing", "student", "intern",
        "graduate", "candidate", "developer", "developers", "engineer", "engineers",
        "analyst", "analysts", "bachelor", "master", "degree", "university", "college",
        "institute", "technology", "technologies", "science", "skills", "projects",
        "experience", "summary", "professional", "technical", "hands", "key",
        "core", "major", "minor", "across", "using", "through", "within", "both",
        "also", "well", "high", "good", "excellent", "results", "impact", "systems",
        "system", "solutions", "solution", "services", "service", "applications",
        "application", "background", "proficient", "data", "work", "practical",
        "software", "hardware", "firmware", "reduced", "increased", "managed",
        "improved", "optimized", "scaled", "automated", "delivered", "maintained",
        "collaborated", "architected", "launched", "enhanced", "code", "program",
        "platform", "platforms", "tool", "tools", "pipeline", "pipelines",
        "architecture", "design", "team", "teams", "user", "users", "client",
        "clients", "proficiency", "knowledge", "domain", "focus", "execution",
        "latency", "performance", "efficiency", "accuracy", "quality", "metric",
        "metrics", "scale", "production", "testing", "test", "tests", "deployment",
        "process", "processing", "operation", "operations", "method", "methods",
        "practices", "standard", "standards", "fast", "clean", "real", "time",
        "modern", "deep", "broad", "solid", "direct", "active", "daily", "weekly",
        "monthly", "annual", "annualized", "full", "stack", "front", "end", "back",
        "lead", "senior", "junior", "associate", "staff", "principal", "internship",
        "fellow", "fellowship", "undergraduate", "first", "second", "third",
        # Additional soft/career words that start with a capital at sentence
        # boundaries but are NOT technology:
        "aspiring", "motivated", "entry", "level", "enthusiastic", "passionate",
        "dedicated", "detail", "oriented", "driven", "results", "self", "eager",
        "recent", "resourceful", "proactive", "innovative", "creative",
        "collaborative", "adaptive", "versatile", "capable", "skilled",
        "demonstrated", "adept",
    }

    for term_match in re.finditer(r'\b[A-Z][a-zA-Z0-9+#.]{2,}\b', clean_summary):
        term = term_match.group(0)
        t = term.lower().strip("*")
        if len(t) < 3 or t in ignored_words or t in OPTIMIZER_IGNORED_TECH_TERMS:
            continue

        span = (term_match.start(), term_match.end())

        # Skip the first word of each sentence — it's capitalised by grammar,
        # not because it's a tech term.
        is_sentence_start = any(
            span[0] == fw_start for fw_start, _ in _sentence_first_word_spans
        )
        if is_sentence_start:
            # Only flag if it's a KNOWN lexicon tech term despite being
            # sentence-leading.  This lets "Aspiring developer…" pass
            # while still catching "Kubernetes-based…" if Kubernetes
            # is absent from the source.
            if t not in _lexicon_lower:
                continue

        # Mid-sentence: flag only if it's a known lexicon term OR a
        # camelCase / mixed-case / symbol token (heuristic for tech).
        is_known_tech = t in _lexicon_lower
        is_tech_looking = bool(
            re.search(r"[a-z][A-Z]|[A-Z]{2,}[a-z]|[a-zA-Z][0-9]|[0-9][a-zA-Z]|[+#.]", term)
        )
        if not is_known_tech and not is_tech_looking:
            continue

        if t not in source_lower:
            return False, f"unsupported_tech_term: {term}"

    return True, "valid"


async def _retry_summary_generation(
    resume_text: str,
    job_title: str,
    fail_reason: str,
) -> str:
    """
    Retry summary generation once with Groq when the initial attempt fails verification.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert resume writer. Generate a concise 2-to-3 sentence professional summary for this candidate.\n"
                "STRICT RULES:\n"
                "1. Use ONLY skills and technical terms that appear in the candidate's resume.\n"
                "2. Use ONLY metrics/numbers that appear in the candidate's resume verbatim. If the resume has no numbers, DO NOT include any numbers or percentages.\n"
                "3. Accurately represent the candidate's real career stage/role from their resume (e.g. Student, Intern, Junior Developer). NEVER use the target job title as candidate identity.\n"
                "4. NEVER include contact details (email, phone, address, URLs) or raw resume text.\n"
                "5. Return strictly valid JSON: {\"optimized_summary\": \"...\"}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Candidate Resume:\n{resume_text[:2500]}\n\n"
                f"Target Role: {job_title or 'Software Engineering'}\n\n"
                f"Note: Previous summary attempt was rejected due to: {fail_reason}. "
                "Write a clean, strictly grounded 2-to-3 sentence summary adhering to the rules."
            ),
        },
    ]
    try:
        raw = await call_groq(messages, json_mode=True, temperature=0.0)
        data = _extract_json(raw)
        return str(data.get("optimized_summary", "") or "").strip()
    except Exception as e:
        logger.warning("Summary retry call failed: %s", e)
        return ""


def generate_structured_summary(
    result: dict,
    resume_text: str = "",
    job_title: str = "",
    job_description: str = "",
) -> str:
    """
    Build a grounded, evidence-based 2-sentence summary.

    Rule: NEVER introduce a persona (e.g. "Machine Learning Engineer") that is
    not supported by resume_text or job_title. The role is derived from the
    user's own data, not hardcoded.

    Returns ADD_EVIDENCE_REQUIRED when there are no grounded metrics to anchor
    the second sentence.
    """
    metric_record = _summary_select_metric(result, resume_text)
    if not metric_record:
        return SUMMARY_NOT_SUPPORTED

    # Derive role from user-supplied data only.
    role = _summary_role(job_title) if job_title else _summary_role("")
    top_skills = _summary_top_skills(result, resume_text)
    if top_skills:
        skills_phrase = _summary_join_skills(top_skills[:3])
        first_sentence = f"{role} specializing in {skills_phrase}."
    else:
        first_sentence = f"{role} with a background in software engineering."

    impact_sentence = _summary_metric_sentence(metric_record)
    return " ".join([first_sentence, impact_sentence])


def _sentence_shares_over_60_percent_with_any_bullet(sentence: str, bullets: list[str]) -> bool:
    """
    Returns True if sentence shares > 60% of its tokens with any single bullet.
    """
    s_tokens = set(re.findall(r"\b[A-Za-z0-9+#.-]+\b", sentence.lower()))
    if not s_tokens:
        return False
    for b in bullets:
        b_tokens = set(re.findall(r"\b[A-Za-z0-9+#.-]+\b", b.lower()))
        if not b_tokens:
            continue
        overlap = len(s_tokens & b_tokens) / len(s_tokens)
        if overlap > 0.60:
            return True
    return False


def _build_deduped_summary(
    candidate_summary: str,
    resume_text: str,
    doc: Optional[ResumeDocument],
    result: dict,
    job_title: str = "",
) -> str:
    """
    FIX F: Summary dedup & grounding:
    - If the source summary exists and is grounded, keep it verbatim.
    - Add at most ONE extra sentence (<=25 words) and only if it contains a metric
      NOT already used in any bullet.
    - Hard cap: 2 sentences, 50 words.
    - Guarantee: no summary sentence shares >60% of its tokens with any bullet.
    """
    # 1. Collect all bullets (source, improved, new)
    all_bullets: list[str] = []
    if doc and doc.all_bullets:
        all_bullets.extend(b.original for b in doc.all_bullets if b.original)
    for b_obj in result.get("improved_bullets") or []:
        if isinstance(b_obj, dict):
            imp = str(b_obj.get("improved") or "").strip()
            orig = str(b_obj.get("original") or "").strip()
            if imp:
                all_bullets.append(imp)
            if orig:
                all_bullets.append(orig)
    for b_obj in result.get("new_bullets") or []:
        if isinstance(b_obj, dict):
            text = str(b_obj.get("text") or "").strip()
            if text:
                all_bullets.append(text)

    # 2. Collect all numeric metrics already used in any bullet
    used_bullet_numbers: set[str] = set()
    for b in all_bullets:
        for m in NUMBER_TOKEN_RE.finditer(b):
            variants = _number_token_variants(m.group(0))
            used_bullet_numbers.update(variants)
        for num in re.findall(r"\b\d+[\d,.]*(?:%|\+|k|m|ms|s)?\b", b.lower()):
            used_bullet_numbers.add(num.replace(",", ""))

    # 3. Check for source summary
    source_summary = ""
    if doc and doc.summary:
        source_summary = doc.summary.strip()
    if not source_summary and result.get("original_summary"):
        source_summary = str(result["original_summary"]).strip()
    if not source_summary and resume_text:
        try:
            parsed_doc = parse_source_resume(resume_text)
            if parsed_doc and parsed_doc.summary:
                source_summary = parsed_doc.summary.strip()
        except Exception:
            pass

    if source_summary:
        source_summary = re.sub(r"^(?:professional\s+)?summary[:|-]?\s*", "", source_summary, flags=re.IGNORECASE).strip()

    # Is source summary grounded?
    source_grounded = False
    if source_summary and len(source_summary) >= 10:
        no_ungrounded_nums = not _find_ungrounded_numbers(source_summary, resume_text)
        no_contact = not (
            SUMMARY_EMAIL_RE.search(source_summary)
            or SUMMARY_PHONE_RE.search(source_summary)
            or re.search(r"https?://|www\.|linkedin\.com|github\.com", source_summary, re.IGNORECASE)
        )
        if no_ungrounded_nums and no_contact:
            source_grounded = True

    if source_grounded:
        # Source summary exists and is grounded -> keep it verbatim!
        source_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", source_summary) if s.strip()]
        filtered_source_sents = [
            s for s in source_sentences
            if not _sentence_shares_over_60_percent_with_any_bullet(s, all_bullets)
        ]
        base_sents = filtered_source_sents if filtered_source_sents else source_sentences[:1]
        base_summary = " ".join(base_sents)

        extra_sentence = ""
        # Add at most ONE extra sentence (<=25 words) and only if it contains a metric NOT already used in any bullet.
        if len(base_sents) < 2 and candidate_summary:
            cand_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", candidate_summary) if s.strip()]
            for cs in cand_sents:
                if cs.lower() in base_summary.lower():
                    continue
                words = re.findall(r"\b[\w+#.%-]+\b", cs)
                if len(words) > 25:
                    continue
                # Must contain a metric
                cs_nums: set[str] = set()
                for m in NUMBER_TOKEN_RE.finditer(cs):
                    cs_nums.update(_number_token_variants(m.group(0)))
                for num in re.findall(r"\b\d+[\d,.]*(?:%|\+|k|m|ms|s)?\b", cs.lower()):
                    cs_nums.add(num.replace(",", ""))
                # Grounded in source resume (compare numbers, not trailing words)
                source_number_vars = _source_number_variants(resume_text)
                if any(v and v.isdisjoint(source_number_vars) for v in [_number_token_variants(m.group(0)) for m in NUMBER_TOKEN_RE.finditer(cs)]):
                    continue
                # Metric NOT already used in any bullet
                unused_metrics = cs_nums - used_bullet_numbers
                if not unused_metrics:
                    continue
                # Overlap check
                if _sentence_shares_over_60_percent_with_any_bullet(cs, all_bullets):
                    continue
                is_valid, _ = _verify_optimizer_summary(cs, resume_text, job_title)
                if not is_valid:
                    continue
                # Total word count <= 50
                combined_words = re.findall(r"\b[\w+#.%-]+\b", f"{base_summary} {cs}")
                if len(combined_words) <= 50:
                    extra_sentence = cs
                    break

        if extra_sentence:
            return f"{base_summary} {extra_sentence}".strip()
        return base_summary

    # Fallback if no source summary or source summary ungrounded
    cand_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", candidate_summary) if s.strip()]
    valid_sents = []
    for cs in cand_sents:
        if _sentence_shares_over_60_percent_with_any_bullet(cs, all_bullets):
            continue
        is_val, _ = _verify_optimizer_summary(cs, resume_text, job_title)
        if is_val:
            valid_sents.append(cs)
        if len(valid_sents) == 2:
            break

    if valid_sents:
        summary_text = " ".join(valid_sents)
    else:
        summary_text = _build_skills_education_summary(resume_text, result, doc=doc)

    s_list = [s.strip() for s in re.split(r"(?<=[.!?])\s+", summary_text) if s.strip()][:2]
    result_text = " ".join(s_list)
    words = result_text.split()
    if len(words) > 50:
        result_text = " ".join(words[:50])
        if not result_text.endswith("."):
            result_text = re.sub(r"[,;:\s]+$", "", result_text) + "."

    return result_text


RECRUITER_DIMENSION_MAXES = {
    "title_clarity": 10,
    "company_signal": 10,
    "tenure_stability": 10,
    "scannability": 15,
    "skills_quality": 15,
    "quantification_rate": 20,
    "red_flag_free": 20,
    "red_flag_penalty": 20,  # Deprecated alias for red_flag_free
}


class OptimizeRequest(BaseModel):
    resume_text: str = Field(..., max_length=20000)
    job_description: str = Field(..., max_length=20000)
    job_title: Optional[str] = ""


class AnalyseRequest(BaseModel):
    resume_text: str = Field(..., max_length=20000)
    job_description: Optional[str] = Field("", max_length=20000)
    job_title: Optional[str] = ""


class ProfessionalResumePdfRequest(BaseModel):
    name: Optional[str] = Field("", max_length=200)
    email: Optional[str] = Field("", max_length=200)
    phone: Optional[str] = Field("", max_length=50)
    linkedin: Optional[str] = Field("", max_length=300)
    github: Optional[str] = Field("", max_length=300)
    location: Optional[str] = Field("", max_length=200)
    job_title: Optional[str] = Field("", max_length=200)
    source_resume_text: Optional[str] = Field("", max_length=50000)
    content: dict[str, Any]


def _safe_pdf_filename(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return f"{slug or 'professional-resume'}.pdf"


@router.post("/professional-resume-pdf")
@_safe_limit("15/hour")  # PDF generation endpoint — resource protection
async def generate_professional_resume_pdf(
    request: Request,
    body: ProfessionalResumePdfRequest,
    user=Depends(get_authenticated_user),
    premium=Depends(require_premium),
):
    # Cap content size on the PDF request
    content_json = json.dumps(body.content)
    if len(content_json) > 100_000:
        raise HTTPException(status_code=400, detail="Resume content exceeds maximum allowed size.")

    try:
        generated = await asyncio.to_thread(
            build_professional_resume_pdf,
            name=body.name or "Your Name",
            email=body.email or "",
            phone=body.phone or "",
            linkedin=body.linkedin or "",
            github=body.github or "",
            location=body.location or "",
            content=body.content,
            source_resume_text=body.source_resume_text or "",
        )
    except ValueError as e:
        logger.error(f"Professional PDF text regression failed for user {user['user_id']}: {e}")
        raise HTTPException(status_code=500, detail="Could not generate a readable resume PDF.")
    except Exception as e:
        logger.error(f"Professional PDF generation failed for user {user['user_id']}: {e}")
        raise HTTPException(status_code=500, detail="Could not generate a readable resume PDF.")

    filename = _safe_pdf_filename(body.name or body.job_title or "professional-resume")
    return Response(
        content=generated.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Extracted-Text-Chars": str(len(generated.extracted_text)),
            "X-Extraction-Ratio": f"{generated.extraction_ratio:.3f}",
        },
    )


OPTIMIZER_ML_MARKERS = [
    "tensorflow", "pytorch", "scikit", "sklearn", "keras",
    "machine learning", "neural network", "deep learning",
    "model training", "model deployment", "feature engineering",
    "data pipeline", "mlops", "xgboost", "lightgbm",
    "natural language processing", "computer vision",
    "transformers", "bert", "llm", "reinforcement learning",
]


def _has_ml_marker(text: str, marker: str) -> bool:
    if not text or not marker:
        return False
    pattern = rf"(?<![A-Za-z0-9]){re.escape(marker)}(?![A-Za-z0-9])"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _get_ml_markers(text: str) -> list[str]:
    if not text:
        return []
    return [kw for kw in OPTIMIZER_ML_MARKERS if _has_ml_marker(text, kw)]


def _has_ml_markers(text: str) -> bool:
    return len(_get_ml_markers(text)) > 0

OPTIMIZER_IGNORED_TECH_TERMS = {
    "accelerated", "achieved", "architected", "automated", "built",
    "configured", "constructed", "delivered", "deployed", "designed",
    "developed", "engineered", "established", "evaluated",
    "implemented", "integrated", "launched", "managed", "migrated",
    "optimized", "orchestrated", "reconstructed", "reduced",
    "spearheaded", "streamlined", "trained", "using", "with",
    "machine", "learning", "model", "deployment", "feature",
    "engineering", "data", "pipeline", "natural", "language",
    "processing", "computer", "vision", "neural", "network",
    "deep", "reinforcement",
}

OPTIMIZER_UNSAFE_SCALE_PATTERNS = [
    r"100,000\+",
    r"1,000\+\s+daily\s+users",
    r"99\.9%\s+uptime",
    r"10,000\+\s+concurrent\s+users",
]


def _optimized_text_for_ats(result: dict) -> str:
    if not isinstance(result, dict):
        return ""

    rec = result.get("reconstructed_resume")
    if rec:
        pieces: list[str] = []
        if isinstance(rec, str):
            pieces.append(rec)
        elif isinstance(rec, dict):
            if rec.get("summary"):
                pieces.append(str(rec["summary"]))
            for exp in rec.get("experience") or []:
                if isinstance(exp, dict):
                    if exp.get("title"):
                        pieces.append(str(exp["title"]))
                    if exp.get("organization"):
                        pieces.append(str(exp["organization"]))
                    for b in exp.get("bullets") or []:
                        if b:
                            pieces.append(str(b))
                elif exp:
                    pieces.append(str(exp))
            for proj in rec.get("projects") or []:
                if isinstance(proj, dict):
                    if proj.get("name"):
                        pieces.append(str(proj["name"]))
                    if proj.get("technologies"):
                        pieces.append(str(proj["technologies"]))
                    for b in proj.get("bullets") or []:
                        if b:
                            pieces.append(str(b))
                elif proj:
                    pieces.append(str(proj))
            pieces.extend(_flatten_skills(rec.get("skills")))
            pieces.extend(_flatten_skills(rec.get("education")))
            pieces.extend(_flatten_skills(rec.get("certifications")))
        return " ".join(piece for piece in pieces if piece)

    pieces: list[str] = [str(result.get("optimized_summary", "") or "")]

    for collection_key, text_key in (("improved_bullets", "improved"), ("new_bullets", "text")):
        for bullet_obj in result.get(collection_key) or []:
            if isinstance(bullet_obj, dict):
                pieces.append(str(bullet_obj.get(text_key, "") or ""))
            elif bullet_obj:
                pieces.append(str(bullet_obj))

    pieces.extend(_flatten_skills(result.get("optimized_skills")))
    return " ".join(piece for piece in pieces if piece)


def _resume_number_audit_pieces(result: dict) -> list[str]:
    if not isinstance(result, dict):
        return []

    pieces: list[str] = [str(result.get("optimized_summary", "") or "")]
    for collection_key in ("improved_bullets", "new_bullets"):
        for bullet_obj in result.get(collection_key) or []:
            if isinstance(bullet_obj, dict):
                for key, value in bullet_obj.items():
                    if key in {"original", "source_id", "entry_id", "section"}:
                        continue
                    pieces.extend(_flatten_skills(value))
            elif bullet_obj:
                pieces.append(str(bullet_obj))
    for key in (
        "optimized_skills",
        "skills_to_highlight",
        "added_keywords",
        "missing_keywords",
        "improvement_explanation",
        "ats_tips",
        "overall_improvement",
    ):
        pieces.extend(_flatten_skills(result.get(key)))
    return [piece for piece in pieces if piece]


class _NoneAtsScores(tuple):
    """Sentinel tuple returned when no JD skills are found. Evaluates to (None, None) and == None."""
    def __new__(cls):
        return super().__new__(cls, (None, None))

    def __eq__(self, other):
        if other is None:
            return True
        return super().__eq__(other)

    def __bool__(self):
        return False


def _stamp_ats_scores(result: dict, resume_text: str, job_description: str) -> tuple[Optional[int], Optional[int]]:
    jd_skills = extract_jd_hard_skills(job_description)
    if not jd_skills:
        result["ats_before"] = None
        result["ats_after"] = None
        result["reachable_max"] = None
        result["ats_reachable_max"] = None
        result["reachable_max_skills"] = []
        result["jd_hard_skills"] = []
        result["ats_regressed"] = False
        result["ats_regression_severe"] = False
        result["hide_ats_bar"] = True
        return _NoneAtsScores()

    result["hide_ats_bar"] = False

    # Source skills present in candidate's original source resume text
    source_skills = {s for s in jd_skills if _skill_in_text(s, resume_text)}
    reachable_max = int((len(source_skills) / len(jd_skills)) * 100)
    result["reachable_max"] = reachable_max
    result["ats_reachable_max"] = reachable_max
    result["reachable_max_skills"] = sorted(source_skills)
    result["jd_hard_skills"] = sorted(jd_skills)

    # ats_before & ats_after: compute with the same function over the same text scope (C5)
    doc = parse_source_resume(resume_text)
    if "reconstructed_resume" in result and isinstance(result["reconstructed_resume"], dict):
        rec_before = reconstruct_resume_structure(doc, bullet_rewrites={})
        before_text = _optimized_text_for_ats({"reconstructed_resume": rec_before.dict() if hasattr(rec_before, "dict") else rec_before})
        if not before_text.strip():
            before_text = resume_text
    else:
        original_primary_text = " ".join([doc.summary] + [b.original for b in doc.all_bullets] + doc.skills).strip()
        before_text = original_primary_text if original_primary_text else resume_text

    before_skills = {s for s in jd_skills if _skill_in_text(s, before_text) and s in source_skills}
    ats_before = int((len(before_skills) / len(jd_skills)) * 100)

    optimized_text = _optimized_text_for_ats(result)
    if not optimized_text.strip():
        optimized_text = before_text
    after_skills = {s for s in jd_skills if _skill_in_text(s, optimized_text) and s in source_skills}
    ats_after = int((len(after_skills) / len(jd_skills)) * 100)

    result["ats_before"] = ats_before
    result["ats_after"] = ats_after
    result["ats_regressed"] = ats_after < ats_before
    result["ats_regression_severe"] = (ats_before - ats_after) > 5
    return ats_before, ats_after


_SECTION_HEADER_RE = re.compile(
    r"^(work\s+experience|professional\s+experience|experience|employment|"
    r"projects?|project\s+experience|academic\s+projects?|personal\s+projects?|"
    r"education|skills|technical\s+skills|core\s+skills|certifications?|"
    r"summary|profile|objective|contact|achievements?|awards?)\b",
    re.IGNORECASE,
)


def _get_bullet_source_section_text(
    bullet_obj: dict,
    resume_text: str,
    doc: Optional[ResumeDocument] = None,
) -> str:
    """Returns the text of the source resume entry / bullet containing this bullet."""
    original_text = str(bullet_obj.get("original") or "").strip()
    source_id = str(bullet_obj.get("source_id") or "").strip()

    if doc is None and resume_text:
        try:
            doc = parse_source_resume(resume_text)
        except Exception:
            doc = None

    if doc:
        source_bullet = None
        if source_id and source_id in doc.bullet_map:
            source_bullet = doc.bullet_map[source_id]
        elif original_text:
            for b in doc.all_bullets:
                if (
                    b.original.strip() == original_text
                    or b.original.strip() in original_text
                    or original_text in b.original.strip()
                ):
                    source_bullet = b
                    break

        if source_bullet:
            all_entries = (doc.experience or []) + (doc.projects or [])
            entry = next((e for e in all_entries if e.entry_id == source_bullet.entry_id), None)
            if entry:
                return f"{entry.header_raw} {source_bullet.original}".strip()
            return source_bullet.original.strip()

    lines = resume_text.splitlines()
    target_idx = -1
    for i, line in enumerate(lines):
        if original_text and (original_text in line or line.strip() in original_text):
            target_idx = i
            break

    if target_idx != -1:
        return lines[target_idx].strip()

    return ""


CLAIM_VERB_PATTERNS = [
    ("team of", re.compile(r"\bteam\s+of\b", re.IGNORECASE)),
    ("cross-functional", re.compile(r"\bcross[-\s]functional\b", re.IGNORECASE)),
    ("led", re.compile(r"\bled\b", re.IGNORECASE)),
    ("managed", re.compile(r"\bmanaged\b", re.IGNORECASE)),
    ("mentored", re.compile(r"\bmentored\b", re.IGNORECASE)),
    ("owned", re.compile(r"\bowned\b", re.IGNORECASE)),
    ("headed", re.compile(r"\bheaded\b", re.IGNORECASE)),
    ("directed", re.compile(r"\bdirected\b", re.IGNORECASE)),
    ("spearheaded", re.compile(r"\bspearheaded\b", re.IGNORECASE)),
    ("architected", re.compile(r"\barchitected\b", re.IGNORECASE)),
]


def _find_unsupported_claim_verb(improved_text: str, source_scope_text: str) -> Optional[str]:
    for verb_phrase, verb_re in CLAIM_VERB_PATTERNS:
        if verb_phrase == "led":
            # "which/that led to..." is a consequence/result, not a leadership claim
            imp_cleaned = re.sub(r"\b(?:which|that)\s+led\s+to\b", " ", improved_text, flags=re.IGNORECASE)
            src_cleaned = re.sub(r"\b(?:which|that)\s+led\s+to\b", " ", source_scope_text, flags=re.IGNORECASE)
            if verb_re.search(imp_cleaned) and not verb_re.search(src_cleaned):
                return verb_phrase
        else:
            if verb_re.search(improved_text) and not verb_re.search(source_scope_text):
                return verb_phrase
    return None


def _apply_optimizer_safety_filters(
    result: dict,
    resume_text: str,
    job_description: str,
    job_title: str = "",
    user_id: str = "",
    doc: Optional[ResumeDocument] = None,
) -> dict:
    if doc is None and resume_text:
        try:
            doc = parse_source_resume(resume_text)
        except Exception:
            doc = None

    result = _validate_against_source(result, resume_text, job_description)

    # If the JD requires >= 3 ML skills and the original resume has 0,
    # we cannot optimize without fabrication. Block and flag.
    jd_lower = job_description.lower()
    original_lower = resume_text.lower()
    jd_ml_hits = len(_get_ml_markers(jd_lower))
    resume_ml_hits = len(_get_ml_markers(original_lower))

    if jd_ml_hits >= 3 and resume_ml_hits == 0:
        result["insufficient_data"] = True
        result["domain_mismatch"] = True
        result["flag_reason"] = (
            f"Domain mismatch: JD requires {jd_ml_hits} ML skills, "
            f"original resume has 0. Output will contain fabricated ML "
            f"credentials that cannot be defended in interviews."
        )
        logger.warning(
            f"Domain mismatch for user {user_id}: "
            f"jd_ml_hits={jd_ml_hits}, resume_ml_hits={resume_ml_hits}"
        )

    result.setdefault("insufficient_data", False)
    result.setdefault("domain_mismatch", False)
    result.setdefault("is_suspicious", False)

    # Log for debugging - KEEP THIS LINE permanently
    logger.info(
        f"Optimizer flags for user {user_id}: "
        f"insufficient_data={result.get('insufficient_data')}, "
        f"domain_mismatch={result.get('domain_mismatch')}, "
        f"flag_reason={result.get('flag_reason', '')[:120]}"
    )

    # Candidate technologies in bullets must be grounded in the source resume.
    # Rely on _find_ungrounded_tech_terms to detect ungrounded tools/technologies.
    fabricated_skills = []

    for bullet_obj in result.get("improved_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        bullet_text = str(bullet_obj.get("improved", "") or "")
        ungrounded = _find_ungrounded_tech_terms(bullet_text, original_lower, jd_lower)
        if ungrounded:
            logger.warning(
                "optimizer.guard_trip: code=revert_unsupported_tech source_id=%s ungrounded_count=%d",
                bullet_obj.get("source_id", ""),
                len(ungrounded),
            )
            fabricated_skills.extend(ungrounded)
            # Revert the bullet to original immediately
            bullet_obj["improved"] = str(bullet_obj.get("original") or "")
            bullet_obj["keywords_added"] = []
            bullet_obj["improvement_reason"] = (
                f"Kept original bullet because the generated rewrite introduced skills absent from the original resume ({', '.join(ungrounded)})."
            )

    for bullet_obj in result.get("new_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        bullet_text = str(bullet_obj.get("text", "") or "")
        ungrounded = _find_ungrounded_tech_terms(bullet_text, original_lower, jd_lower)
        if ungrounded:
            logger.warning(
                "optimizer.guard_trip: code=drop_unsupported_tech_new_bullet source_id=%s ungrounded_count=%d",
                bullet_obj.get("source_id", ""),
                len(ungrounded),
            )
            fabricated_skills.extend(ungrounded)

    # ── Claim-Verb Guard (FIX A) ───────────────────────────────────────
    # Verbs and phrases claiming leadership, ownership, or organizational scope:
    # led, managed, mentored, owned, headed, directed, spearheaded, architected,
    # "team of", "cross-functional"
    # These MUST already exist in the original bullet or its section in the source resume;
    # otherwise, revert the bullet.
    CLAIM_VERB_PATTERNS = [
        ("team of", re.compile(r"\bteam\s+of\b", re.IGNORECASE)),
        ("cross-functional", re.compile(r"\bcross[-\s]functional\b", re.IGNORECASE)),
        ("led", re.compile(r"\bled\b", re.IGNORECASE)),
        ("managed", re.compile(r"\bmanaged\b", re.IGNORECASE)),
        ("mentored", re.compile(r"\bmentored\b", re.IGNORECASE)),
        ("owned", re.compile(r"\bowned\b", re.IGNORECASE)),
        ("headed", re.compile(r"\bheaded\b", re.IGNORECASE)),
        ("directed", re.compile(r"\bdirected\b", re.IGNORECASE)),
        ("spearheaded", re.compile(r"\bspearheaded\b", re.IGNORECASE)),
        ("architected", re.compile(r"\barchitected\b", re.IGNORECASE)),
    ]

    for bullet_obj in result.get("improved_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        original_text = str(bullet_obj.get("original") or "")
        improved_text = str(bullet_obj.get("improved") or "")
        if not improved_text or improved_text == original_text:
            continue

        section_text = _get_bullet_source_section_text(bullet_obj, resume_text, doc)
        source_scope_text = f"{original_text} {section_text}"

        revert_verb = _find_unsupported_claim_verb(improved_text, source_scope_text)

        if revert_verb:
            logger.warning(
                "optimizer.guard_trip: code=revert_unsupported_claim_verb source_id=%s verb=%s",
                bullet_obj.get("source_id", ""),
                revert_verb,
            )
            bullet_obj["improved"] = original_text
            bullet_obj["keywords_added"] = []
            bullet_obj["improvement_reason"] = (
                f"Kept original bullet because the generated rewrite added leadership/scope claims ('{revert_verb}') absent from the source bullet or section."
            )
            _append_grounding_warning(
                result,
                "claim_verbs",
                f"Reverted bullet introducing unsupported leadership claim verb '{revert_verb}'.",
                [revert_verb],
            )

    claim_filtered_new_bullets = []
    for bullet_obj in result.get("new_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        nb_text = str(bullet_obj.get("text") or "")
        dropped_verb = _find_unsupported_claim_verb(nb_text, resume_text)
        if dropped_verb:
            logger.warning(
                "optimizer.guard_trip: code=drop_unsupported_claim_verb_new_bullet verb=%s",
                dropped_verb,
            )
            _append_grounding_warning(
                result,
                "claim_verbs",
                f"Dropped new bullet introducing unsupported leadership claim verb '{dropped_verb}'.",
                [dropped_verb],
            )
            continue
        claim_filtered_new_bullets.append(bullet_obj)
    result["new_bullets"] = claim_filtered_new_bullets

    # Claim-level grounding for new_bullets:
    # Require that the action/capability described has reasonable lexical overlap
    # with the source resume's actual bullets/sentences.
    action_stopwords = {
        "a", "an", "the", "and", "or", "with", "for", "to", "of", "in", "on", "at",
        "by", "from", "using", "as", "is", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "our", "your", "my", "their",
        "its", "this", "that", "these", "those", "we", "i", "you", "they", "it",
        "into", "over", "after", "before", "between", "through", "during", "without",
        "again", "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "can", "will", "just", "should", "now", "etc", "across", "per",
    }
    source_bullet_word_sets: list[set[str]] = []
    for line in resume_text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        words = {
            w.lower()
            for w in re.findall(r"\b[A-Za-z][A-Za-z0-9+#.]*\b", line_clean)
            if len(w) > 2 and w.lower() not in action_stopwords
        }
        if words:
            source_bullet_word_sets.append(words)

    grounded_new_bullets = []
    unsupported_action_bullets = []
    unsupported_action_terms = []

    for bullet_obj in result.get("new_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        bullet_text = str(bullet_obj.get("text", "") or "")
        bullet_words = {
            w.lower()
            for w in re.findall(r"\b[A-Za-z][A-Za-z0-9+#.]*\b", bullet_text)
            if len(w) > 2 and w.lower() not in action_stopwords
        }
        max_overlap = max(
            (len(bullet_words & s_set) for s_set in source_bullet_word_sets),
            default=0,
        )
        if max_overlap < 2:
            unsupported_action_bullets.append(bullet_text)
            terms = _find_ungrounded_tech_terms(bullet_text, original_lower, jd_lower)
            if terms:
                unsupported_action_terms.extend(terms)
            continue
        grounded_new_bullets.append(bullet_obj)

    if unsupported_action_bullets:
        result["is_suspicious"] = True
        result["domain_mismatch"] = True
        result["insufficient_data"] = True
        flagged_snippet = ", ".join(dict.fromkeys(unsupported_action_terms)) if unsupported_action_terms else unsupported_action_bullets[0][:60]
        existing_reason = result.get("flag_reason") or ""
        action_flag_reason = (
            f"Fabricated action capability in new bullets: {flagged_snippet}. "
            f"Action has no counterpart in source resume."
        )
        result["flag_reason"] = f"{action_flag_reason} {existing_reason}".strip()
        _append_grounding_warning(
            result,
            "new_bullets_action",
            "Removed new bullets describing actions/capabilities absent from source resume.",
            unsupported_action_terms or [b[:60] for b in unsupported_action_bullets],
        )
        result["new_bullets"] = grounded_new_bullets

    if result.get("domain_mismatch"):
        ml_display_names = {
            "tensorflow": "TensorFlow",
            "pytorch": "PyTorch",
            "scikit": "Scikit-learn",
            "sklearn": "Scikit-learn",
            "keras": "Keras",
            "machine learning": "Machine Learning",
            "neural network": "Neural Network",
            "deep learning": "Deep Learning",
            "model training": "Model Training",
            "model deployment": "Model Deployment",
            "feature engineering": "Feature Engineering",
            "data pipeline": "Data Pipeline",
            "mlops": "MLOps",
            "xgboost": "XGBoost",
            "lightgbm": "LightGBM",
            "natural language processing": "Natural Language Processing",
            "computer vision": "Computer Vision",
            "transformers": "Transformers",
            "bert": "BERT",
            "llm": "LLM",
            "reinforcement learning": "Reinforcement Learning",
        }
        jd_gaps = [
            ml_display_names.get(kw, kw)
            for kw in OPTIMIZER_ML_MARKERS
            if _has_ml_marker(jd_lower, kw) and not _has_ml_marker(original_lower, kw)
        ]
        result["jd_gaps"] = list(dict.fromkeys(jd_gaps))[:8]
        if "fabricated_skills" not in result:
            result["fabricated_skills"] = result["jd_gaps"]  # deprecated alias

    fabricated_unique = list(dict.fromkeys(fabricated_skills))[:8]

    if fabricated_unique:
        result["is_suspicious"] = True
        result["fabricated_skills"] = fabricated_unique
        existing_reason = result.get("flag_reason") or ""
        result["flag_reason"] = (
            f"Fabricated skills not in original resume: "
            f"{', '.join(fabricated_unique)}. "
            + existing_reason
        ).strip()
        logger.info(
            f"Hallucination guard fired for user {user_id}: "
            f"count={len(fabricated_unique)}"
        )

        fabricated_lower = [term.lower() for term in fabricated_unique]
        for bullet_obj in result.get("improved_bullets") or []:
            if not isinstance(bullet_obj, dict):
                continue
            bullet_text = str(bullet_obj.get("improved", ""))
            if any(_contains_grounded_term(bullet_text.lower(), term) for term in fabricated_lower):
                logger.warning(
                    "optimizer.guard_trip: code=revert_bullet_to_original source_id=%s ungrounded_count=%d",
                    bullet_obj.get("source_id", ""),
                    len(fabricated_lower),
                )
                bullet_obj["improved"] = str(bullet_obj.get("original") or "")
                bullet_obj["keywords_added"] = []
                bullet_obj["improvement_reason"] = (
                    "Kept original bullet because the generated rewrite introduced skills absent from the original resume."
                )

        result["new_bullets"] = [
            bullet_obj for bullet_obj in result.get("new_bullets") or []
            if isinstance(bullet_obj, dict)
            and not any(_contains_grounded_term(str(bullet_obj.get("text", "")).lower(), term) for term in fabricated_lower)
        ]

    no_employment_history = not re.search(
        r"\b(intern|internship|employment|work experience|professional experience|"
        r"software engineer|developer|engineer at|developer at|analyst|consultant|freelance|"
        r"\d+\+?\s+years?\s+(?:of\s+)?experience)\b",
        original_lower,
    )
    if no_employment_history:
        unsafe_scale_hits = []
        for bullet_obj in result.get("improved_bullets") or []:
            if not isinstance(bullet_obj, dict):
                continue
            bullet_text = str(bullet_obj.get("improved", ""))
            if any(re.search(pattern, bullet_text, re.IGNORECASE) for pattern in OPTIMIZER_UNSAFE_SCALE_PATTERNS):
                unsafe_scale_hits.append(bullet_text)
                bullet_obj["improved"] = str(bullet_obj.get("original") or "")
                bullet_obj["keywords_added"] = []
                bullet_obj["improvement_reason"] = (
                    "Kept original bullet because the generated rewrite used impossible scale for a student/no-employment profile."
                )

        safe_new_bullets = []
        for bullet_obj in result.get("new_bullets") or []:
            if not isinstance(bullet_obj, dict):
                continue
            bullet_text = str(bullet_obj.get("text", ""))
            if any(re.search(pattern, bullet_text, re.IGNORECASE) for pattern in OPTIMIZER_UNSAFE_SCALE_PATTERNS):
                unsafe_scale_hits.append(bullet_text)
                continue
            safe_new_bullets.append(bullet_obj)
        result["new_bullets"] = safe_new_bullets

        if unsafe_scale_hits:
            result["is_suspicious"] = True
            existing_reason = result.get("flag_reason") or ""
            result["flag_reason"] = (
                "Removed impossible scale claims for a student/no-employment profile. "
                + existing_reason
            ).strip()

    # Stop replacing LLM summary with a template. Verify and handle fallbacks (FIX 1)
    if result.get("domain_mismatch"):
        # FIX B+C: Use skills-only line on domain mismatch instead of blank
        fallback = _build_skills_education_summary(resume_text, result, doc=doc, skills_only=True)
        result["optimized_summary"] = fallback
        result["summary_grounding_note"] = (
            "Domain mismatch detected — summary uses verified skills from your resume."
        )
    else:
        existing_summary = str(result.get("optimized_summary", "") or "").strip()
        is_valid, reason = _verify_optimizer_summary(existing_summary, resume_text, job_title)

        orig_summary = (doc.summary if doc and doc.summary else "").strip()
        if not orig_summary and result.get("original_summary"):
            orig_summary = str(result["original_summary"]).strip()
        if not orig_summary and resume_text:
            try:
                parsed_doc = parse_source_resume(resume_text)
                if parsed_doc and parsed_doc.summary:
                    orig_summary = parsed_doc.summary.strip()
            except Exception:
                pass

        if orig_summary:
            deduped = _build_deduped_summary(
                candidate_summary=existing_summary if is_valid else "",
                resume_text=resume_text,
                doc=doc,
                result=result,
                job_title=job_title,
            )
            result["optimized_summary"] = deduped
            if not is_valid or deduped == orig_summary:
                result["summary_grounding_note"] = (
                    "The AI-generated summary failed verification and was replaced with your original resume summary."
                )
        elif is_valid:
            result["optimized_summary"] = existing_summary
        else:
            fallback = _build_skills_education_summary(resume_text, result, doc=doc)
            result["optimized_summary"] = fallback
            result["summary_grounding_note"] = (
                "The AI-generated summary contained ungrounded claims and was replaced with a verified skills and education overview."
            )

    result = _enforce_source_number_grounding(result, resume_text, user_id)
    return result


def _ats_regression_retry_addendum(ats_before: int, ats_after: int) -> str:
    gap = max(0, ats_before - ats_after)
    return (
        "\n\nATS REGRESSION RETRY:\n"
        f"The prior attempt under-covered JD keywords and scored {ats_after}, "
        f"while the original resume scored {ats_before}. Close the {gap}-point gap.\n"
        "- Regenerate the same JSON structure.\n"
        "- Incorporate JD keywords supported by candidate source context into improved bullets.\n"
        "- Copy missing JD technical phrases verbatim when they are supported by source context.\n"
        "- Do not reintroduce anything ungrounded or fabricated.\n"
        "- The revised ats keyword coverage must be at least the original resume.\n"
    )


async def _generate_optimizer_attempt(
    system: str,
    user_msg: str,
    resume_text: str,
    job_description: str,
    job_title: str,
    user_id: str,
    retry_addendum: str = "",
    doc: Optional[ResumeDocument] = None,
) -> tuple[dict, int, int]:
    if doc is None:
        doc = parse_source_resume(resume_text)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{user_msg}{retry_addendum}"},
    ]
    text = await call_groq(messages, json_mode=True, temperature=0.0)
    try:
        result = _extract_json(text)
    except Exception as parse_err:
        logger.warning(
            "First JSON extraction failed for user %s (%s). Retrying model with strict syntax instruction...",
            user_id,
            parse_err,
        )
        retry_messages = list(messages) + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": (
                    "Your previous response had a JSON formatting error. "
                    "Return ONLY valid, perfectly formatted JSON conforming to RFC 8259. "
                    "Ensure every key and string is double-quoted and all list/dict elements are separated by commas."
                ),
            },
        ]
        retry_text = await call_groq(retry_messages, json_mode=True, temperature=0.0)
        result = _extract_json(retry_text)

    if not isinstance(result, dict):
        raise ValueError("Optimizer response was not a JSON object.")

    # Retry summary once with model if initial attempt is invalid (FIX 1)
    if not result.get("domain_mismatch"):
        summary = str(result.get("optimized_summary", "") or "").strip()
        is_valid, reason = _verify_optimizer_summary(summary, resume_text, job_title)
        if not is_valid and summary:
            logger.info("Optimizer summary attempt 1 invalid (%s); retrying model once...", reason)
            try:
                retried_summary = await _retry_summary_generation(
                    resume_text=resume_text,
                    job_title=job_title,
                    fail_reason=reason,
                )
                if retried_summary and _verify_optimizer_summary(retried_summary, resume_text, job_title)[0]:
                    result["optimized_summary"] = retried_summary
            except Exception as retry_err:
                logger.warning("Summary retry failed: %s", retry_err)

    result = _apply_optimizer_safety_filters(
        result,
        resume_text,
        job_description,
        job_title,
        user_id,
        doc=doc,
    )
    result = _validate_optimized_structure(
        doc,
        result,
        job_title=job_title,
        user_id=user_id,
    )
    ats_before, ats_after = _stamp_ats_scores(result, resume_text, job_description)
    return result, ats_before, ats_after


@router.post("/")
@_safe_limit("15/hour")  # AI-calling endpoint — prevent abuse
async def optimize_resume(request: Request, body: OptimizeRequest, user=Depends(get_authenticated_user), premium=Depends(require_premium)):
    if not body.resume_text.strip() or not body.job_description.strip():
        raise HTTPException(status_code=400, detail="Resume and job description required.")

    doc = parse_source_resume(body.resume_text)
    source_items = build_source_items_for_prompt(doc)

    system = (
        "Rephrase and reorder what the candidate actually did, "
        "using JD wording only where the source supports it. "
        "Never add skills or numbers. "
        "You respond ONLY in valid JSON with no markdown, no code fences, no extra text.\n\n"
        "NUMBER GROUNDING - NON-NEGOTIABLE:\n"
        "Never introduce a number, percentage, count, scale, duration, or "
        "quantitative claim unless the same figure appears in the ORIGINAL "
        "RESUME verbatim or as a direct paraphrase of that exact figure. "
        "If a source bullet has no metric, improve clarity and impact without "
        "adding a number to fill the gap.\n\n"
        "REALITY AND SCALE - NON-NEGOTIABLE:\n"
        "Treat every quantitative statement as source evidence, never as "
        "a target to invent. Do not use any sample value, scale limit, or "
        "job-description number as a resume claim. Preserve a source metric "
        "only with its original unit and meaning.\n"
        "For student and project-only profiles, prefer precise technical "
        "wording over unsupported claims of business impact or scale.\n"
        "If the resume has no ML experience and JD requires ML:\n"
        "  Set insufficient_data: true immediately.\n"
        "  Do NOT generate TensorFlow/PyTorch bullets.\n"
        "  Do NOT generate model training accuracy claims.\n"
        "  Return flag_reason: 'domain_mismatch: no ML in original resume'\n"
    )

    user_msg = (
        # ── EXISTING CONTENT: Keep everything below unchanged ─────
        "You are an elite technical resume writer. Your output must be "
        "specific, credible, ATS-optimized, and indistinguishable from "
        "a real engineer's resume. Generic or AI-sounding content is a "
        "failure. Every word must sound like a real engineer wrote it.\n\n"
        
        f"TARGET JOB TITLE: {body.job_title or 'Software Developer'}\n\n"
        f"JOB DESCRIPTION:\n{body.job_description}\n\n"
        f"ORIGINAL RESUME:\n{body.resume_text}\n\n"
        f"SOURCE BULLETS TO TRANSFORM (preserve every source_id exactly):\n{json.dumps(source_items, indent=2)}\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 0 — PRESERVE REALITY (NON-NEGOTIABLE)\n"
        "════════════════════════════════════════════════════════\n"
        "- Never invent job titles, companies, or degrees not in original\n"
        "- Never add experience at companies not mentioned\n"
        "- Only enhance what exists — never fabricate what doesn't\n"
        "- Never introduce a number, percentage, count, scale, duration,\n"
        "  or quantitative claim unless the same figure appears in the\n"
        "  ORIGINAL RESUME verbatim or as a direct paraphrase of that\n"
        "  exact source figure\n"
        "- If a bullet has no source metric, improve wording without\n"
        "  inventing a number to fill the gap\n"
        "- If original has 2 experience entries → output has exactly 2\n"
        "- If original has 3 project entries → output has exactly 3\n"
        "- Do NOT merge, split, or reorder existing entries\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 1 — REALISM OVER IMPRESSIVENESS\n"
        "════════════════════════════════════════════════════════\n"
        "- Never fabricate unrealistic achievements\n"
        "- Never claim revenue or business impact unless explicitly\n"
        "  stated in the original resume\n"
        "- Do not generate numerical scale limits, quotas, or improvement\n"
        "  percentages for any experience level\n"
        "- If no metric exists in the source bullet, do NOT add any\n"
        "  number, percentage, count, duration, or scale claim\n"
        "- Never borrow numeric examples from this prompt or from the JD;\n"
        "  numeric claims must come from the ORIGINAL RESUME only\n"
        "- Conservative + specific > impressive + vague\n"
        "- If resume lacks sufficient data to produce quality output:\n"
        "  set insufficient_data: true and return minimal safe output\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 2 — SUMMARY (EVIDENCE-BASED SYNTHESIS)\n"
        "════════════════════════════════════════════════════════\n"
        "- Hard cap: 2 sentences, 50 words total.\n"
        "- If the source resume summary exists and is grounded, keep it verbatim.\n"
        "- Add at most ONE extra sentence (<= 25 words) and ONLY if it contains a metric NOT already used in any bullet.\n"
        "- Ensure no summary sentence shares >60% of its tokens with any bullet.\n"
        "- Synthesize using ONLY:\n"
        "  (a) Skills and technologies explicitly present in the candidate's source resume.\n"
        "  (b) Verifiable metrics and numbers present in the source resume verbatim (never invent, inflate, or adjust figures).\n"
        "  (c) The candidate's real current role, stage, or background from their resume (e.g. 'Computer Science graduate with ML internship experience', 'Computer Science Student', 'Software Engineering Intern', 'Junior Developer').\n"
        "- NEVER use the target job title as candidate identity (e.g. if a student targets a Senior role or ML Engineer role, do NOT introduce them with that target title).\n"
        "- If the original resume has no numbers or metrics, do NOT invent one. State their verified core skills and technical focus honestly.\n"
        "- NEVER include contact information (email, phone, address, LinkedIn/GitHub links).\n"
        "- NEVER copy-paste raw resume header chunks or contact lines.\n"
        "- Never use buzzwords or empty filler: 'passionate', 'hardworking', 'dynamic', 'self-starter', 'various', 'multiple'.\n"
        "- Never start a sentence with 'I', 'My', 'Uses', or 'Has'.\n"
        "- Every sentence must end with a period.\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 3 — SKILLS (GROUPED BY DOMAIN)\n"
        "════════════════════════════════════════════════════════\n"
        "Return optimized_skills as a grouped object ONLY.\n"
        "Choose the correct group set based on candidate domain:\n\n"
        "ML / Data Science roles:\n"
        "  { Languages, ML & Data, Tools & Platforms, Concepts }\n\n"
        "Web Development roles:\n"
        "  { Languages, Frameworks, Databases, DevOps }\n\n"
        "Data Engineering roles:\n"
        "  { Languages, Data Tools, Cloud & Platforms, Concepts }\n\n"
        "Backend / Systems roles:\n"
        "  { Languages, Frameworks, Databases, Tools & DevOps }\n\n"
        "Rules for all groups:\n"
        "- Remove the global cap. Output skills must be a superset of source skills, plus any tech token appearing in bullets or project stack lines.\n"
        "- Preserve parentheticals ('AWS (S3, EC2)') and preserve 'CI/CD' without splitting.\n"
        "- Reorder by JD relevance only.\n"
        "- Feature Engineering belongs under 'ML & Data'.\n"
        "- Output skills must contain all source skills (set(source_skills) ⊆ set(output_skills)).\n"
        "- No duplicates across groups\n"
        "- Never mix group name sets across a single response\n"
        "- Pick one domain set and apply it consistently\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 4 — BULLET REWRITING & WORDING\n"
        "════════════════════════════════════════════════════════\n"
        "Each bullet should be:\n"
        "- Concise (preferred 15–28 words, hard maximum 32 words)\n"
        "- Specific, technically accurate, and relevant to the target JD\n"
        "- Don't drop domain nouns ('leaf images', 'customer records', 'loan data', 'annotated resumes') when shortening bullets.\n"
        "- Outcome-oriented when source evidence supports an outcome\n"
        "- Never invent a metric simply to satisfy a format\n"
        "- If the source has no metric, do not create one\n"
        "- When the source already contains a metric, preserve the exact\n"
        "  source figure and its unit; otherwise, omit the metric entirely\n"
        "- No vague filler phrases: 'scalable', 'robust', 'efficient', 'various', 'multiple'\n"
        "- All bullets in past tense\n\n"
        "BAD examples — NEVER generate these:\n"
        "'Engineered a scalable system' ← vague, no specifics\n"
        "'Achieved an unsupported accuracy claim' ← no context, sounds fabricated\n"
        "'Increased business revenue by an unsupported percentage' ← unverifiable,\n"
        " destroys recruiter trust instantly\n"
        "'Worked on backend development' ← weak verb, no detail\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 5 — ACTION VERBS & STYLE\n"
        "════════════════════════════════════════════════════════\n"
        "- Prefer strong action verbs (Engineered, Built, Developed, Designed,\n"
        "  Implemented, Deployed, Optimized, Automated, Integrated, Launched, Streamlined, etc.)\n"
        "- Avoid passive or weak openings (worked, helped, assisted, involved, responsible, participated)\n"
        "- Avoid repetitive openings where natural, but never replace an accurate verb with an\n"
        "  unnatural synonym merely to increase vocabulary diversity.\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 6 — JD EXACT PHRASE MATCHING\n"
        "════════════════════════════════════════════════════════\n"
        "- Use JD wording only for terms the resume already contains.\n"
        "- Copy technical terms VERBATIM from JD when supported by source — ATS matches\n"
        "  exact strings, not paraphrases\n"
        "- Never introduce JD terms, tools, or scope not present in the original resume\n"
        "- Never substitute a synonym for a technical term the candidate actually used\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 7 — JD GAPS ARE ANALYSIS RESULTS, NOT FABRICATION LICENSE\n"
        "════════════════════════════════════════════════════════\n"
        "- JD requirements absent from the original resume are candidate GAPS.\n"
        "- Report missing JD requirements in missing_keywords.\n"
        "- NEVER fabricate experience, projects, technologies, or skills to fill JD gaps.\n"
        "- Do NOT invent new experience or project entries.\n"
        "- Do NOT write fabricated bullets claiming candidate experience with JD-only technologies.\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 8 — METRIC FORMATTING\n"
        "════════════════════════════════════════════════════════\n"
        "Wrap ALL source-grounded numbers and metrics in **double asterisks**:\n"
        "  Preserve **[exact source figure]** with its source unit and meaning\n"
        "  If the source has no number, do not add one\n"
        "Apply to: improved_bullets, summary\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 9 — ANTI-HALLUCINATION FILTER\n"
        "════════════════════════════════════════════════════════\n"
        "Before finalizing each bullet, ask internally:\n"
        "  1. Does every number in this bullet appear in the original resume?\n"
        "  2. Is this technology actually in the original resume?\n"
        "     JD presence alone is not permission to claim it.\n"
        "  3. Would a real recruiter believe this?\n"
        "If any answer is NO → rewrite without the unsupported claim\n"
        "Never guess company-scale business impact\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 10 — APPLICATION SCORING\n"
        "════════════════════════════════════════════════════════\n"
        "Do not return a match score estimate or confidence level. The\n"
        "application calculates score presentation deterministically.\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "OUTPUT FORMAT — STRICT JSON ONLY\n"
        "No markdown, no backticks, no explanation outside JSON\n"
        "════════════════════════════════════════════════════════\n"
        
        "{\n"
        '  "insufficient_data": false,\n'
        
        '  "optimized_summary": "2-3 clear sentences using only source skills, verbatim metrics, and real candidate stage",\n'
        
        '  "optimized_skills": {\n'
        '    "Languages": ["Python", "Java"],\n'
        '    "ML & Data": ["Machine Learning", "Feature Engineering"],\n'
        '    "Tools & Platforms": ["Docker", "Git"],\n'
        '    "Concepts": ["Data Pipelines", "Model Training"]\n'
        '  },\n'
        
        '  "improved_bullets": [\n'
        '    {\n'
        '      "source_id": "experience_001_bullet_001",\n'
        '      "section": "experience",\n'
        '      "original": "exact original bullet text",\n'
        '      "improved": "concise, technically accurate rewrite with optional source metric",\n'
        '      "keywords_added": ["source-supported keyword"],\n'
        '      "verb_upgrade": {"from": "worked", "to": "Engineered"},\n'
        '      "metric_added": "source metric preserved from original bullet, or empty string",\n'
        '      "improvement_reason": "plain English one sentence"\n'
        '    }\n'
        '  ],\n'
        
        '  "added_keywords": ["every source-grounded JD keyword present in output"],\n'
        '  "missing_keywords": ["JD keywords still not coverable from candidate resume"],\n'
        
        '  "improvement_explanation": {\n'
        '    "keywords_added": ["<example_keyword_1>", "<example_keyword_2>"],\n'
        '    "verbs_upgraded": [\n'
        '      {"from": "worked", "to": "Engineered"},\n'
        '      {"from": "helped", "to": "Implemented"}\n'
        '    ],\n'
        '    "metrics_added": [\n'
        '      "Source metric preserved in rewritten bullet",\n'
        '      "No metric added where source bullet had none"\n'
        '    ],\n'
        '    "sections_improved": [\n'
        '      "<example_section_improvement>"\n'
        '    ]\n'
        '  },\n'
        
        '  "ats_tips": [\n'
        '    "<example_ats_tip>"\n'
        '  ],\n'
        
        '  "overall_improvement": "one specific sentence not generic"\n'
        "}"
    )

    try:
        result, ats_before, ats_after = await _generate_optimizer_attempt(
            system,
            user_msg,
            body.resume_text,
            body.job_description,
            body.job_title or "",
            user["user_id"],
            doc=doc,
        )

        bullets_changed = any(
            (b.get("improved") or "").strip() != (b.get("original") or "").strip()
            for b in result.get("improved_bullets") or []
        )
        if ats_before is not None and ats_after is not None and (ats_before - ats_after) > 5 and bullets_changed:
            first_attempt_after = ats_after
            logger.warning(
                f"ATS regression detected for user {user['user_id']}: "
                f"before={ats_before}, after={ats_after}. Retrying once."
            )
            try:
                result, ats_before, ats_after = await _generate_optimizer_attempt(
                    system,
                    user_msg,
                    body.resume_text,
                    body.job_description,
                    body.job_title or "",
                    user["user_id"],
                    _ats_regression_retry_addendum(ats_before, ats_after),
                    doc=doc,
                )
                result["ats_retry_attempted"] = True
            except Exception as retry_error:
                result["ats_retry_attempted"] = True
                result["ats_retry_failed"] = True
                logger.warning(
                    f"ATS regression retry failed for user {user['user_id']}: {retry_error}"
                )

        result.pop("ats_retry_error", None)

        if ats_before is not None and ats_after is not None:
            result["ats_regressed"] = ats_after < ats_before
            result["ats_regression_severe"] = (ats_before - ats_after) > 5
        else:
            result["ats_regressed"] = False
            result["ats_regression_severe"] = False
        result.setdefault("ats_retry_attempted", False)

        # Check truncation for optimize_resume
        resume_truncated = len(body.resume_text) > 8000
        jd_truncated = len(body.job_description) > 3000
        if resume_truncated or jd_truncated:
            trunc_parts = []
            if resume_truncated:
                trunc_parts.append("Resume text exceeded 8,000 characters and was truncated for optimization.")
            if jd_truncated:
                trunc_parts.append("Job description exceeded 3,000 characters and was truncated for optimization.")
            result["truncation_notice"] = " ".join(trunc_parts)

        try:
            await asyncio.to_thread(
                lambda: supabase.table("resume_optimizations").insert({
                    "user_id":         user["user_id"],
                    "job_title":       body.job_title or "",
                    "job_description": body.job_description[:500],
                    "result_json":     result,
                }).execute()
            )
        except Exception as e:
            logger.warning(f"DB save failed: {e}")

        return {
            "success": True,
            "optimization": result,
            "ats_before": ats_before,
            "ats_after": ats_after,
            "ats_reachable_max": result.get("ats_reachable_max"),
            "ats_regressed": result["ats_regressed"],
            "truncation_notice": result.get("truncation_notice"),
            "summary_grounding_note": result.get("summary_grounding_note"),
        }

        # ── Domain mismatch threshold check ─────────────────────────────
        # If the JD requires >= 3 ML skills and the original resume has 0,
        # we cannot optimize without fabrication. Block and flag.
        # Log for debugging - KEEP THIS LINE permanently
        # ── Hallucination guard ───────────────────────────────────────────
        # A skill can only appear in output if it existed in the original
        # resume. JD presence alone is NOT enough — the candidate must
        # actually have the skill. Skills in the JD but absent from the
        # resume are the GAPS, not license to fabricate.
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization error for user {user['user_id']}: {e}", exc_info=True)
        err_str = str(e).lower()
        if "429" in err_str or "rate limit" in err_str:
            raise HTTPException(
                status_code=429,
                detail="The AI service is experiencing high traffic. Please wait a few seconds and try again.",
            )
        raise HTTPException(
            status_code=500,
            detail="Resume optimization could not be completed due to a temporary AI formatting issue. Please try again.",
        )


@router.get("/history")
async def get_optimization_history(user=Depends(get_authenticated_user), premium=Depends(require_premium)):
    result = supabase.table("resume_optimizations") \
        .select("id,job_title,job_description,created_at") \
        .eq("user_id", user["user_id"]) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()
    return {"success": True, "history": result.data}


# ── Section-aware truncation ──────────────────────────────────────────
# Reuses the same section-header patterns from _summary_metric_source_lines.
# Priority order: EXPERIENCE > PROJECTS > SUMMARY > SKILLS > CERTIFICATIONS > EDUCATION
# When truncation is needed, the lowest-priority sections are trimmed first.


# Higher number = trimmed first when over budget.
_SECTION_PRIORITY = {
    "education": 6,
    "certifications": 5,
    "certification": 5,
    "awards": 5,
    "achievements": 5,
    "contact": 5,
    "objective": 4,
    "skills": 4,
    "technical skills": 4,
    "core skills": 4,
    "summary": 3,
    "profile": 3,
    "projects": 2,
    "project": 2,
    "project experience": 2,
    "academic projects": 2,
    "personal projects": 2,
    "work experience": 1,
    "professional experience": 1,
    "experience": 1,
    "employment": 1,
}


def _smart_truncate_resume(text: str, max_chars: int = 8000) -> str:
    """Split resume into sections, truncate lowest-priority sections first."""
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, list[str]]] = []
    current_name = "__header__"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        match = _SECTION_HEADER_RE.match(stripped)
        if match:
            sections.append((current_name, current_lines))
            current_name = match.group(1).lower().strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    sections.append((current_name, current_lines))

    total = sum(sum(len(l) for l in s_lines) for _, s_lines in sections)
    if total <= max_chars:
        return text

    # Sort sections by priority (highest trim-priority first) but keep
    # order stable within same priority.
    indexed = [(i, name, s_lines) for i, (name, s_lines) in enumerate(sections)]
    trim_order = sorted(
        indexed,
        key=lambda t: (-_SECTION_PRIORITY.get(t[1], 0), -t[0]),
    )

    excess = total - max_chars
    for idx, name, s_lines in trim_order:
        if excess <= 0:
            break
        section_len = sum(len(l) for l in s_lines)
        # Keep at least the header line
        header_len = len(s_lines[0]) if s_lines else 0
        removable = section_len - header_len
        if removable <= 0:
            continue
        if removable <= excess:
            # Remove all body lines, keep header only
            sections[idx] = (name, [s_lines[0]] if s_lines else [])
            excess -= removable
        else:
            # Trim from the end of this section
            keep = section_len - excess
            kept: list[str] = []
            acc = 0
            for line in s_lines:
                if acc + len(line) > keep:
                    break
                kept.append(line)
                acc += len(line)
            sections[idx] = (name, kept)
            excess = 0

    return "".join(l for _, s_lines in sections for l in s_lines)


@router.post("/analyse")
@limiter.limit("15/hour")  # AI-calling endpoint — prevent abuse
async def analyse_resume(
    request: Request,
    body: AnalyseRequest,
    user=Depends(get_authenticated_user),
    premium=Depends(require_premium),
):
    """
    5-module resume intelligence analysis.
    Runs: ATS scan, recruiter-lens score, bullet audit,
    skill gap matrix, rejection diagnosis.
    Does NOT rewrite or consume an optimization credit.
    """
    resume_text = body.resume_text or ""
    job_description = body.job_description or ""
    job_title = body.job_title or ""

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required.")

    resume_truncated = len(resume_text) > 8000
    jd_truncated = len(job_description) > 3000
    if resume_truncated:
        resume_text = _smart_truncate_resume(resume_text, 8000)

    has_job_description = bool(job_description.strip())
    jd_section = (
        f"JOB TITLE: {job_title}\n\n"
        f"JOB DESCRIPTION:\n{job_description[:3000]}\n\n"
        if has_job_description
        else "JOB DESCRIPTION: Not provided. Run modules 1, 2, 3, 5 only. "
             "Set module4_skill_gap fields to empty arrays. "
             "Set keyword_coverage found=0 and missing=[].\n\n"
    )

    user_msg = (
        f"{jd_section}"
        f"RESUME:\n{resume_text}\n\n"
        f"{ANALYST_OUTPUT_SCHEMA}"
    )

    try:
        raw = await call_groq([
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ], json_mode=True, temperature=0.0)
        analysis = _extract_json(raw)
        if not isinstance(analysis, dict):
            raise ValueError("Analysis response was not a JSON object.")

        # Tell the user when text is truncated
        if resume_truncated or jd_truncated:
            truncation_parts = []
            if resume_truncated:
                truncation_parts.append("Resume text exceeded 8,000 characters and was truncated for analysis.")
            if jd_truncated:
                truncation_parts.append("Job description exceeded 3,000 characters and was truncated for analysis.")
            analysis["truncation_notice"] = " ".join(truncation_parts)
            analysis["is_truncated"] = True

        # Safe defaults and dimension clamping for module2_recruiter_lens (E1, E3)
        m2 = analysis.get("module2_recruiter_lens")
        if not isinstance(m2, dict):
            m2 = {}
            analysis["module2_recruiter_lens"] = m2
        dims = m2.get("dimensions")
        if not isinstance(dims, dict):
            dims = {}
            m2["dimensions"] = dims

        # Support red_flag_free and keep red_flag_penalty alias (E1)
        if "red_flag_penalty" in dims and "red_flag_free" not in dims:
            dims["red_flag_free"] = dims["red_flag_penalty"]

        canonical_dim_keys = [
            "title_clarity", "company_signal", "tenure_stability",
            "scannability", "skills_quality", "quantification_rate", "red_flag_free",
        ]
        computed_total = 0
        for dim_key in canonical_dim_keys:
            v = dims.get(dim_key)
            if isinstance(v, dict):
                max_val = RECRUITER_DIMENSION_MAXES.get(dim_key, int(v.get("max", 10) or 10))
                try:
                    raw_score = int(float(v.get("score", 0) or 0))
                except Exception:
                    raw_score = 0
                clamped_score = max(0, min(raw_score, max_val))
                v["score"] = clamped_score
                v["max"] = max_val
                computed_total += clamped_score

        # Maintain deprecated alias for frontend contract compatibility (E1)
        if "red_flag_free" in dims:
            dims["red_flag_penalty"] = dict(dims["red_flag_free"])

        m2["total"] = computed_total
        total = computed_total
        if total >= 85:
            interp = "Strong"
        elif total >= 70:
            interp = "Good"
        elif total >= 55:
            interp = "Average"
        elif total >= 40:
            interp = "Weak"
        else:
            interp = "Critical"
        m2["interpretation"] = interp

        # B3(b) Drop any audit row whose original (and evidence) is not a whitespace/case-normalised substring of the resume
        raw_audits = analysis.get("module3_bullet_audit")
        if isinstance(raw_audits, list):
            norm_resume = " ".join(resume_text.lower().split())
            valid_audits = []
            for row in raw_audits:
                if not isinstance(row, dict):
                    continue
                orig = str(row.get("original", "") or "")
                evidence = str(row.get("evidence", "") or "")
                norm_orig = " ".join(orig.lower().split())
                norm_evid = " ".join(evidence.lower().split())
                is_grounded = False
                if norm_orig and norm_orig in norm_resume:
                    is_grounded = True
                elif norm_evid and norm_evid in norm_resume:
                    is_grounded = True

                if not is_grounded:
                    continue

                # B3(a) Run _find_ungrounded_numbers and _find_ungrounded_tech_terms on each module3_bullet_audit[].rewrite
                # If ungrounded, blank it and set optional rewrite_unverified: true.
                rewrite = str(row.get("rewrite", "") or "")
                if rewrite:
                    ungrounded_nums = _find_ungrounded_numbers(rewrite, resume_text)
                    ungrounded_tech = _find_ungrounded_tech_terms(rewrite, resume_text)
                    if ungrounded_nums or ungrounded_tech:
                        row["rewrite"] = ""
                        row["rewrite_unverified"] = True
                valid_audits.append(row)
            analysis["module3_bullet_audit"] = valid_audits

        # No-JD analyses must not surface skill-gap or keyword-missing content.
        if not has_job_description:
            analysis["module4_skill_gap"] = {
                "critical": [],
                "partial": [],
                "strengths": [],
                "irrelevant": [],
            }
            ats = analysis.setdefault("module1_ats", {})
            keyword_coverage = ats.setdefault("keyword_coverage", {})
            keyword_coverage["jd_keywords_checked"] = 0
            keyword_coverage["found"] = 0
            keyword_coverage["missing"] = []
            keyword_coverage["buried"] = []

        # Keep the rejection diagnosis contract stable for the frontend.
        diagnoses = analysis.get("module5_rejection_diagnosis")
        if not isinstance(diagnoses, list):
            diagnoses = []
        normalized_diagnoses = []
        for index in range(3):
            item = diagnoses[index] if index < len(diagnoses) and isinstance(diagnoses[index], dict) else {}
            normalized_diagnoses.append({
                "rank": index + 1,
                "summary": str(item.get("summary", "")),
                "evidence": str(item.get("evidence", "")),
                "recruiter_thought": str(item.get("recruiter_thought", "")),
                "fix": str(item.get("fix", "")),
            })
        analysis["module5_rejection_diagnosis"] = normalized_diagnoses

        # Deterministic guard for obvious ML-role/domain mismatches using shared helper (B11)
        role_context = f"{job_title}\n{job_description}"
        ml_jd = _has_ml_markers(role_context)
        ml_resume = _has_ml_markers(resume_text)
        if has_job_description and ml_jd and not ml_resume:
            analysis["domain_mismatch"] = True
            analysis["domain_mismatch_reason"] = (
                analysis.get("domain_mismatch_reason")
                or "The job description is ML/AI-focused, but the resume has no clear ML/AI skill, project, framework, or deployment signal."
            )
            analysis["optimizable"] = False
            analysis["optimizable_reason"] = (
                analysis.get("optimizable_reason")
                or "Keyword optimization cannot fix a missing core ML/AI experience signal for this role."
            )

        # Compute reachable max ATS score for analysis if JD is provided (E2)
        if has_job_description:
            jd_skills = extract_jd_hard_skills(job_description)
            if jd_skills:
                source_skills = {s for s in jd_skills if _skill_in_text(s, resume_text)}
                reachable_max = int((len(source_skills) / len(jd_skills)) * 100)
                analysis["ats_reachable_max"] = reachable_max
                analysis["reachable_max"] = reachable_max
                analysis["reachable_max_skills"] = sorted(source_skills)
                analysis["jd_hard_skills"] = sorted(jd_skills)

                # Clamp LLM ats_score and keyword_coverage.found to reachable_max (E2)
                ats = analysis.setdefault("module1_ats", {})
                if isinstance(ats, dict):
                    llm_ats = ats.get("ats_score")
                    if isinstance(llm_ats, (int, float)) and llm_ats > reachable_max:
                        ats["ats_score"] = reachable_max
                        ats["clamped_to_reachable_max"] = True

                    kw_cov = ats.get("keyword_coverage")
                    if isinstance(kw_cov, dict):
                        found_cnt = kw_cov.get("found", 0)
                        max_found = len(source_skills)
                        if isinstance(found_cnt, (int, float)) and found_cnt > max_found:
                            kw_cov["found"] = max_found
                            kw_cov["clamped_to_reachable_max"] = True
            else:
                analysis["ats_reachable_max"] = None
                analysis["reachable_max"] = None
                analysis["reachable_max_skills"] = []
                analysis["jd_hard_skills"] = []
        else:
            analysis["ats_reachable_max"] = None
            analysis["reachable_max"] = None

        if analysis.get("domain_mismatch"):
            analysis["summary_grounding_note"] = "Domain mismatch detected — summary uses verified skills from your resume."

        # Save analysis to DB async (F1)
        try:
            await asyncio.to_thread(
                lambda: supabase.table("resume_analyses").insert({
                    "user_id":         user["user_id"],
                    "job_title":       job_title,
                    "job_description": job_description[:500],
                    "result_json":     analysis,
                }).execute()
            )
        except Exception as db_err:
            logger.warning(f"Analysis DB save failed: {db_err}")

        return {
            "success":           True,
            "analysis":          analysis,
            "recruiter_score":   analysis.get("module2_recruiter_lens", {}).get("total", 0),
            "interpretation":    analysis.get("module2_recruiter_lens", {}).get("interpretation", ""),
            "optimizable":       analysis.get("optimizable", True),
            "optimizable_reason": analysis.get("optimizable_reason", ""),
            "domain_mismatch":   analysis.get("domain_mismatch", False),
            "next_action":       analysis.get("next_action", ""),
            "ats_reachable_max": analysis.get("ats_reachable_max"),
            "summary_grounding_note": analysis.get("summary_grounding_note"),
            "truncation_notice": analysis.get("truncation_notice"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error for user {user['user_id']}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Resume analysis could not be completed. Please try again.")


@router.get("/analyse/history")
async def get_analysis_history(user=Depends(get_authenticated_user), premium=Depends(require_premium)):
    result = (
        supabase.table("resume_analyses")
        .select("id, job_title, job_description, created_at, result_json")
        .eq("user_id", user["user_id"])
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    return {"success": True, "history": result.data}