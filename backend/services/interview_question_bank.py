"""
Role-based interview question bank used as deterministic fallback and
randomization pool for mock interview sessions.
"""

from __future__ import annotations

from copy import deepcopy


ROLE_KEYWORDS = {
    "frontend": ["frontend", "front-end", "react", "ui", "web", "javascript", "typescript"],
    "backend": ["backend", "back-end", "api", "server", "node", "django", "flask", "fastapi", "java", "spring"],
    "ai_ml": ["ai", "ml", "machine learning", "data scientist", "deep learning", "nlp", "computer vision", "llm"],
}


QUESTION_BANK = {
    "frontend": [
        {
            "question": "How do you optimize React component rendering in a large application?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["memoization", "component splitting", "profiling"],
        },
        {
            "question": "What is the difference between controlled and uncontrolled components in React?",
            "category": "technical",
            "difficulty": "easy",
            "expected_points": ["state ownership", "refs", "form handling tradeoffs"],
        },
        {
            "question": "How would you design a reusable design-system component library?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["tokenization", "accessibility", "documentation"],
        },
        {
            "question": "How do you handle API errors and loading states in a frontend app?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["retry strategy", "error boundaries", "user feedback"],
        },
        {
            "question": "Explain how browser rendering works from HTML parsing to paint.",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["DOM/CSSOM", "layout", "paint/composite"],
        },
        {
            "question": "What strategies do you use to improve Core Web Vitals?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["LCP", "CLS", "INP", "resource optimization"],
        },
        {
            "question": "When would you choose state management libraries over React Context?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["scalability", "update frequency", "developer tooling"],
        },
        {
            "question": "How do you secure a frontend application handling authenticated sessions?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["token handling", "XSS/CSRF", "secure storage"],
        },
        {
            "question": "How would you test a complex UI flow end-to-end?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["unit/integration/e2e", "mocking", "test reliability"],
        },
        {
            "question": "Describe an approach for building accessible, keyboard-friendly interfaces.",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["ARIA", "focus management", "semantic HTML"],
        },
    ],
    "backend": [
        {
            "question": "How would you design a scalable REST API for millions of users?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["stateless design", "pagination", "rate limiting"],
        },
        {
            "question": "What are key differences between SQL and NoSQL databases in production systems?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["consistency", "query patterns", "scaling strategy"],
        },
        {
            "question": "How do you diagnose and reduce API latency in a backend service?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["profiling", "caching", "query optimization"],
        },
        {
            "question": "Explain idempotency and where it matters in API design.",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["HTTP semantics", "safe retries", "duplicate protection"],
        },
        {
            "question": "How would you implement reliable background jobs and retries?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["queueing", "dead-letter handling", "observability"],
        },
        {
            "question": "What is your strategy for authentication and authorization in microservices?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["JWT/OAuth", "service-to-service auth", "RBAC/ABAC"],
        },
        {
            "question": "How do you version APIs while maintaining backward compatibility?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["versioning policy", "deprecation", "contract testing"],
        },
        {
            "question": "How do you ensure transaction consistency in distributed systems?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["saga pattern", "eventual consistency", "compensation"],
        },
        {
            "question": "How do you monitor and alert on backend health effectively?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["SLIs/SLOs", "structured logs", "metrics/traces"],
        },
        {
            "question": "What steps do you take to secure backend services and data?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["input validation", "secrets management", "least privilege"],
        },
    ],
    "ai_ml": [
        {
            "question": "How do you decide whether to use a classical ML model or a deep learning model?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["dataset size", "feature complexity", "latency constraints"],
        },
        {
            "question": "Describe your process for handling data leakage in model training.",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["split strategy", "feature leakage checks", "validation discipline"],
        },
        {
            "question": "How would you evaluate an imbalanced classification model?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["precision/recall", "PR-AUC", "threshold tuning"],
        },
        {
            "question": "How do you monitor model drift in production?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["data drift", "concept drift", "retraining triggers"],
        },
        {
            "question": "Explain bias-variance tradeoff with a practical example.",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["underfit/overfit", "regularization", "model complexity"],
        },
        {
            "question": "How would you design an end-to-end MLOps pipeline?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["experiment tracking", "model registry", "deployment automation"],
        },
        {
            "question": "What are best practices for feature engineering in tabular datasets?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["domain features", "encoding", "data quality checks"],
        },
        {
            "question": "How do you choose and tune hyperparameters efficiently?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["search strategy", "validation setup", "compute budget"],
        },
        {
            "question": "How do you evaluate and improve LLM responses for a domain-specific assistant?",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["eval set", "groundedness", "prompt/retrieval tuning"],
        },
        {
            "question": "What tradeoffs do you consider when deploying models on cloud vs edge?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["latency", "cost", "privacy/resource limits"],
        },
    ],
    "generic": [
        {
            "question": "Tell me about a project you are most proud of and the impact it created.",
            "category": "behavioral",
            "difficulty": "easy",
            "expected_points": ["context", "technical decisions", "measurable impact"],
        },
        {
            "question": "Describe a time you had to debug a critical issue under pressure.",
            "category": "behavioral",
            "difficulty": "medium",
            "expected_points": ["structured debugging", "communication", "postmortem actions"],
        },
        {
            "question": "How do you prioritize tasks when deadlines are tight?",
            "category": "situational",
            "difficulty": "medium",
            "expected_points": ["prioritization framework", "stakeholder alignment", "tradeoffs"],
        },
        {
            "question": "How do you keep your technical skills up to date?",
            "category": "behavioral",
            "difficulty": "easy",
            "expected_points": ["learning strategy", "practice", "knowledge sharing"],
        },
        {
            "question": "Describe a disagreement with a teammate and how you resolved it.",
            "category": "behavioral",
            "difficulty": "medium",
            "expected_points": ["active listening", "data-driven discussion", "resolution outcome"],
        },
        {
            "question": "How do you ensure quality before shipping a feature?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["testing strategy", "reviews", "monitoring/rollback plan"],
        },
    ],
}


def resolve_role_bucket(job_role: str | None) -> str:
    role = (job_role or "").strip().lower()
    if not role:
        return "generic"

    for bucket, keywords in ROLE_KEYWORDS.items():
        if any(keyword in role for keyword in keywords):
            return bucket
    return "generic"


def get_question_bank_for_role(job_role: str | None) -> list[dict]:
    bucket = resolve_role_bucket(job_role)
    role_questions = QUESTION_BANK.get(bucket, [])
    generic_questions = QUESTION_BANK.get("generic", [])
    # Return copies to avoid mutating shared constants.
    return deepcopy(role_questions + generic_questions)

