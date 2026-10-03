# ============================================================
# CareerLens - Resume Optimizer (Fixed - No Hallucination)
# File: backend/routers/optimizer.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel
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
)
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
            try:
                return await wrapped(*args, **kwargs)
            except Exception as e:
                if "parameter `response` must be an instance of" in str(e):
                    return await fn(*args, **kwargs)
                raise
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
1. Never fabricate a number. Use "~", "up to", or range language if unavailable.
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
      "red_flag_penalty":    {"score": 0, "max": 20, "reason": ""}
    },
    "interpretation": "Strong | Good | Average | Weak | Critical"
  },

  "module3_bullet_audit": [
    {
      "original": "exact bullet text from resume",
      "grade": "WEAK | AVERAGE | STRONG",
      "grade_reason": "one line why",
      "rewrite": "rewritten bullet — Action + Context + Scope + Outcome. NEVER invent metrics. Use ~ or range language if no data."
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


def count_kw_coverage(text: str, jd: str, source_text: str = "") -> int:
    import re
    stopwords = {
        "the", "and", "for", "with", "that", "this", "will", "have",
        "from", "you", "are", "your", "our", "they", "can", "has", "was",
        "were", "been", "their", "into", "about", "which", "when", "who",
        "what", "how", "all", "also", "both", "each", "more", "other",
        "some", "such", "than", "then", "them", "these", "those", "very",
        "shall", "should", "could", "would", "may", "might", "must",
        "have", "had", "its", "his", "her", "their", "our", "we", "is",
        "a", "an", "of", "to", "in", "on", "at", "by", "or", "not", "be"
    }
    words = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.]*\b', jd.lower()))
    keywords = [w for w in words if len(w) > 3 and w not in stopwords]
    if not keywords:
        return 30
    text_lower = text.lower()
    source_lower = source_text.lower() if source_text else ""
    matches = 0
    for k in keywords:
        if k in text_lower:
            # If source_text is provided, reward keyword only if supported by candidate's source resume
            if not source_lower or k in source_lower:
                matches += 1
    return min(int((matches / len(keywords)) * 100), 99)


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
}


def _normalize_grounding_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _contains_grounded_term(haystack: str, term: str) -> bool:
    cleaned = _normalize_grounding_text(term)
    if not cleaned:
        return False
    if cleaned in haystack:
        return True
    pattern = re.escape(cleaned).replace(r"\ ", r"\s+")
    if bool(re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", haystack)):
        return True
    # Handle common tech variants / abbreviations
    if cleaned == "rest" and "restful" in haystack:
        return True
    if cleaned == "restful" and "rest" in haystack:
        return True
    if cleaned == "kubernetes" and "k8s" in haystack:
        return True
    if cleaned == "k8s" and "kubernetes" in haystack:
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
        return [item.strip() for item in re.split(r"[,|;/]", value) if item.strip()]
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

    # 2. Check general tech candidates (mixed-case names, symbols, or curated ML markers)
    tech_candidates = re.findall(r"\b[A-Z][a-zA-Z0-9+#.]{2,}\b", text)
    for cand in tech_candidates:
        cand_lower = cand.lower().strip("*")
        if len(cand_lower) < 3 or cand_lower in OPTIMIZER_IGNORED_TECH_TERMS:
            continue
        is_tech = (
            cand_lower in GROUNDING_TECH_TERMS
            or cand_lower in OPTIMIZER_ML_MARKERS
            or bool(re.search(r"[a-z][A-Z]|[A-Z]{2,}[a-z]|[a-zA-Z][0-9]|[0-9][a-zA-Z]|[+#.]", cand))
        )
        if not is_tech:
            continue
        if not _contains_grounded_term(source_lower, cand_lower):
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


def _mark_ungrounded_metrics(text: str, source_lower: str, jd_lower: str) -> tuple[str, list[str]]:
    flagged: list[str] = []

    def replace_metric(match: re.Match) -> str:
        metric = match.group(0)
        following = text[match.end():match.end() + 12]
        if re.match(r"\s*years?\b", following, flags=re.IGNORECASE):
            return metric
        if re.fullmatch(r"(?:19|20)\d{2}", metric.strip()):
            return metric
        if _metric_is_estimated(text, match.start()):
            return metric
        if _metric_is_grounded(metric, source_lower, jd_lower):
            return metric
        flagged.append(metric.strip())
        softened = re.sub(r"\s*\+\s*", " ", metric).strip()
        softened = re.sub(r"\s+", " ", softened)
        return f"~{softened}"

    return GROUNDING_METRIC_RE.sub(replace_metric, text), list(dict.fromkeys(flagged))


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


def _number_context_is_grounded(
    text: str,
    start: int,
    end: int,
    source_text: str,
    variants: set[str],
) -> bool:
    after_words = _number_after_context_words(text, end)
    context_keys = _number_word_keys(after_words or _number_before_context_words(text, start))
    if not context_keys:
        return True

    for source_keys in _source_contexts_for_number(source_text, variants, include_before=not after_words):
        if source_keys and all(key in source_keys for key in context_keys):
            return True
    return False


def _find_ungrounded_numbers(text: str, source_text: str) -> list[dict[str, str]]:
    source_variants = _source_number_variants(source_text)
    ungrounded: list[dict[str, str]] = []
    for match in NUMBER_TOKEN_RE.finditer(str(text or "")):
        raw = re.sub(r"\s+", " ", match.group(0)).strip()
        variants = _number_token_variants(raw)
        if not variants:
            continue
        if variants.isdisjoint(source_variants):
            ungrounded.append({"number": raw, "reason": "absent_from_source"})
            continue
        # Compare numbers, not trailing words: percentages (e.g. 40%) are verified by number value
        if not raw.endswith("%") and not _number_context_is_grounded(text, match.start(), match.end(), source_text, variants):
            ungrounded.append({"number": raw, "reason": "source_context_mismatch"})
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
        # Never fall back to source_text[:120] and never return ADD_EVIDENCE_REQUIRED as summary.
        original_summary = str(result.get("original_summary", "") or "")
        original_ungrounded = _find_ungrounded_numbers(original_summary, source_text) if original_summary else True
        if original_summary and not original_ungrounded:
            result["optimized_summary"] = original_summary
        else:
            fallback = _build_skills_education_summary(source_text, result)
            if fallback and not _find_ungrounded_numbers(fallback, source_text):
                result["optimized_summary"] = fallback
            else:
                result["optimized_summary"] = ""
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
            status = "yes" if appears and grounded else "no"
            existing = rows_by_number.get(key)
            if existing is None or status == "no":
                rows_by_number[key] = {
                    "number": number,
                    "appears_in_source": status,
                }
    return list(rows_by_number.values())


def _extract_source_skills(resume_text: str) -> list[str]:
    skills: list[str] = []
    in_skills_section = False
    for line in resume_text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        lower = trimmed.lower()
        if re.match(r"^(?:technical\s+|core\s+)?skills?\s*[:|-]", lower):
            parts = re.split(r"[:|-]", trimmed, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                for item in re.split(r"[,|;/•\t]", parts[1]):
                    s = item.strip().strip("-*•")
                    if s and len(s) > 1 and s not in skills:
                        skills.append(s)
            in_skills_section = True
            continue
        elif in_skills_section:
            if re.match(r"^(?:experience|education|projects|summary|certifications|awards|work)\b", lower):
                in_skills_section = False
            else:
                for item in re.split(r"[,|;/•\t]", trimmed):
                    s = item.strip().strip("-*•")
                    if s and len(s) > 1 and s not in skills:
                        skills.append(s)

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

    skills = result.get("optimized_skills")
    if isinstance(skills, dict):
        for category, items in list(skills.items()):
            kept = filter_skill_list(items)
            dropped = [
                skill for skill in _split_skill_items(items)
                if skill not in kept and not _contains_grounded_term(source_lower, skill)
            ]
            skills[category] = kept
            if dropped:
                logger.warning(f"Dropped ungrounded skills in {category}: {dropped}")
    elif isinstance(skills, list):
        result["optimized_skills"] = filter_skill_list(skills)

    if _is_skills_empty(result.get("optimized_skills")):
        source_skills = _extract_source_skills(resume_text)
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


def _validate_optimized_structure(doc: ResumeDocument, result: dict, user_id: str = "") -> dict:
    """
    Validates structural integrity of the optimized resume against the parsed source document.
    Enforces:
    - Section ownership (experience vs projects never mix)
    - Source ID validity
    - Original entry count preservation (no dropped experiences or projects)
    - Company, role, and date preservation
    - Document hierarchy reconstruction
    """
    if not isinstance(result, dict) or not doc:
        return result

    bullet_map = doc.bullet_map
    valid_source_ids = set(bullet_map.keys())

    validated_rewrites: dict[str, dict[str, Any]] = {}
    for bullet_obj in result.get("improved_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue

        source_id = str(bullet_obj.get("source_id") or "").strip()
        original_text = str(bullet_obj.get("original") or "").strip()
        improved_text = str(bullet_obj.get("improved") or "").strip()

        if not source_id or source_id not in valid_source_ids:
            # Attempt to resolve by original text match
            matched_bullet = None
            if original_text:
                for b in doc.all_bullets:
                    if b.source_id not in validated_rewrites and (
                        b.original.strip() == original_text
                        or b.original.strip() in original_text
                        or original_text in b.original.strip()
                    ):
                        matched_bullet = b
                        break
            if matched_bullet:
                source_id = matched_bullet.source_id
                bullet_obj["source_id"] = source_id
            else:
                logger.warning(
                    "optimizer.source_id_invalid: Rejected item with unknown or missing source_id '%s' for user %s",
                    source_id,
                    user_id,
                )
                _append_grounding_warning(
                    result,
                    "structure",
                    f"Rejected item with unknown source_id '{source_id}'.",
                    [source_id or "missing_source_id"],
                )
                continue

        source_bullet = bullet_map[source_id]

        # Enforce section ownership: an experience bullet CANNOT become a project bullet and vice-versa
        claimed_section = str(bullet_obj.get("section") or source_bullet.section).strip().lower()
        if claimed_section != source_bullet.section:
            logger.warning(
                "optimizer.structure_mismatch: Section mismatch for source_id '%s': claimed '%s', expected '%s'",
                source_id,
                claimed_section,
                source_bullet.section,
            )
            bullet_obj["section"] = source_bullet.section
            _append_grounding_warning(
                result,
                "structure",
                f"Enforced section ownership for {source_id} to {source_bullet.section}.",
                [source_id],
            )

        # Phase 8: Reject unsupported technology claims in improved bullets
        source_lower = _normalize_grounding_text(doc.raw_text)
        ungrounded_tech = _find_ungrounded_tech_terms(improved_text, source_lower)
        if ungrounded_tech:
            logger.warning(
                "optimizer.tech_rejected: Reverting %s due to unsupported tech: %s",
                source_id,
                ungrounded_tech,
            )
            improved_text = source_bullet.original
            bullet_obj["improved"] = improved_text
            bullet_obj["keywords_added"] = []
            bullet_obj["metric_added"] = ""
            bullet_obj["improvement_reason"] = (
                "Kept original bullet because the generated rewrite introduced technologies absent from the source resume."
            )

        validated_rewrites[source_id] = {
            "source_id": source_id,
            "section": source_bullet.section,
            "original": source_bullet.original,
            "improved": improved_text if improved_text else source_bullet.original,
            "keywords_added": bullet_obj.get("keywords_added", []),
            "metric_added": bullet_obj.get("metric_added", ""),
            "improvement_reason": bullet_obj.get("improvement_reason", ""),
        }

    # Ensure NO original bullet is omitted: restore missing bullets
    for b in doc.all_bullets:
        if b.source_id not in validated_rewrites:
            logger.info("optimizer.bullet_restored: Restoring omitted source bullet %s", b.source_id)
            validated_rewrites[b.source_id] = {
                "source_id": b.source_id,
                "section": b.section,
                "original": b.original,
                "improved": b.original,
                "keywords_added": [],
                "metric_added": "",
                "improvement_reason": "Restored original bullet because model omitted this item.",
            }

    # Reconstruct improved_bullets list in stable source order
    final_improved_bullets = [
        validated_rewrites[b.source_id]
        for b in doc.all_bullets
    ]
    result["improved_bullets"] = final_improved_bullets

    # Reject any new_bullets that attempt to invent new entries or projects or claim unsupported tech
    safe_new_bullets = []
    source_lower = _normalize_grounding_text(doc.raw_text)
    for nb in result.get("new_bullets") or []:
        if not isinstance(nb, dict):
            continue
        if nb.get("is_new_entry") or nb.get("new_project") or nb.get("new_company"):
            logger.warning("optimizer.structure_mismatch: Rejected invented project/entry in new_bullets")
            continue
        nb_text = str(nb.get("text", "") or "")
        if _find_ungrounded_tech_terms(nb_text, source_lower):
            logger.warning("optimizer.tech_rejected: Dropping new_bullet due to ungrounded tech: %s", nb_text)
            continue
        safe_new_bullets.append(nb)
    result["new_bullets"] = safe_new_bullets

    # Reconstruct resume structure deterministically
    reconstructed = reconstruct_resume_structure(
        doc=doc,
        bullet_rewrites=validated_rewrites,
        optimized_summary=result.get("optimized_summary", ""),
        optimized_skills=result.get("optimized_skills"),
    )

    result["reconstructed_resume"] = reconstructed
    result["experience_entries"] = reconstructed["experience"]
    result["project_entries"] = reconstructed["projects"]

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
    if re.search(r"machine learning|(^|\s)ml(\s|$)|artificial intelligence|\bai\b", lowered):
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
        return "optimizing backend systems"
    if re.search(r"html|css|webpage|interface|frontend|react", lowered):
        return "optimizing backend systems"
    if re.search(r"model|training|machine learning|prediction|classifier", lowered):
        return "optimizing model deployment"
    if re.search(r"api|backend|service", lowered):
        return "optimizing backend systems"
    return "optimizing backend systems"


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
    outcome = record.get("outcome") or "backend efficiency"
    system = record.get("system") or "backend systems"
    context = record.get("context") or "backend workflows"
    context_phrase = (
        f" {context}"
        if context.startswith("handling ")
        else f" for {context}"
    )

    if metric_type == "accuracy":
        return f"Improved model accuracy to {metric} by optimizing {system}{context_phrase}."
    if metric_type == "performance":
        return f"{action} {outcome} {metric} by optimizing {system}{context_phrase}."
    if metric_type == "scale":
        return f"{action} {outcome} to {metric} by optimizing {system}."
    return f"{action} {outcome} by {metric} by optimizing {system}{context_phrase}."


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


def _build_skills_education_summary(resume_text: str, result: dict | None = None) -> str:
    """
    Plain, verified skills + education fallback line.
    Never returns contact info, raw resume dumps, or fabricated metrics.
    """
    degree = ""
    edu_match = re.search(
        r"\b(B\.?S\.?|B\.?Tech|Bachelor(?:'s)?|M\.?S\.?|M\.?Tech|Master(?:'s)?|Ph\.?D\.?|Associate(?:'s)?)\s+(?:of\s+|in\s+)?([A-Za-z\s]+?)(?:,|\.|\n|\||-|\d{4})",
        resume_text,
        re.IGNORECASE,
    )
    if edu_match:
        degree_type = edu_match.group(1).strip()
        field = edu_match.group(2).strip()
        field_words = [w for w in field.split() if w.lower() not in ("from", "at", "university", "college", "institute", "gpa")]
        clean_field = " ".join(field_words[:3]).strip()
        if clean_field:
            degree = f"{degree_type} in {clean_field}"
        else:
            degree = f"{degree_type} graduate"
    elif re.search(r"\bcomputer science\b", resume_text, re.IGNORECASE):
        degree = "Computer Science graduate"
    elif re.search(r"\bengineering\b", resume_text, re.IGNORECASE):
        degree = "Engineering graduate"

    # Extract top verified skills that actually appear in source resume
    skills = []
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
        for kw in ["Python", "Java", "JavaScript", "TypeScript", "C++", "C", "SQL", "Go", "Rust", "React", "Node.js", "Docker", "Git", "AWS", "Linux"]:
            if re.search(rf"\b{re.escape(kw)}\b", resume_text, re.IGNORECASE):
                skills.append(kw)

    unique_skills = []
    for s in skills:
        if s not in unique_skills and len(unique_skills) < 4:
            unique_skills.append(s)

    skills_text = ", ".join(unique_skills) if unique_skills else "software engineering"

    if degree:
        return f"{degree} with core technical skills in {skills_text}."
    return f"Technical background with core proficiencies in {skills_text}."


def _verify_optimizer_summary(
    summary: str,
    source_text: str,
    job_title: str = "",
) -> tuple[bool, str]:
    """
    Verify summary against source resume:
    - No contact details (email, phone, address, links)
    - No raw resume text / header dumps
    - Never uses target job title as identity
    - Every number must appear in source (compare numbers, not trailing words)
    - Every technical term must appear in source
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

    # 2. Raw resume text / header dump check
    if len(clean_summary) > 40 and clean_summary.lower() in source_text[:300].lower():
        return False, "raw_resume_header_dump"

    # 3. Target job title as identity check
    if job_title:
        jt_clean = re.sub(r"^(senior|junior|lead|staff|principal)\s+", "", job_title.strip(), flags=re.IGNORECASE).lower()
        if len(jt_clean) > 4 and jt_clean not in source_text.lower():
            first_sentence = clean_summary.split(".")[0].lower()
            if first_sentence.startswith(jt_clean) or re.search(rf"\b(as an?|as a|i am an?)\s+{re.escape(jt_clean)}\b", first_sentence):
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

    # 5. Technical terms check
    source_lower = source_text.lower()
    tech_terms = re.findall(r'\b[A-Z][a-zA-Z0-9+#.]{2,}\b', clean_summary)
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
    }
    for term in tech_terms:
        t = term.lower().strip("*")
        if len(t) < 3 or t in ignored_words or t in OPTIMIZER_IGNORED_TECH_TERMS:
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
        raw = await call_groq(messages, json_mode=True, temperature=0.1)
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


class OptimizeRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: Optional[str] = ""


class AnalyseRequest(BaseModel):
    resume_text: str
    job_description: Optional[str] = ""
    job_title: Optional[str] = ""


class ProfessionalResumePdfRequest(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    location: Optional[str] = ""
    job_title: Optional[str] = ""
    source_resume_text: Optional[str] = ""
    content: dict[str, Any]


def _safe_pdf_filename(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return f"{slug or 'professional-resume'}.pdf"


@router.post("/professional-resume-pdf")
@limiter.limit("15/hour")  # AI-calling endpoint — prevent abuse
async def generate_professional_resume_pdf(
    request: Request,
    body: ProfessionalResumePdfRequest,
    user=Depends(get_authenticated_user),
    premium=Depends(require_premium),
):
    try:
        generated = build_professional_resume_pdf(
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
        raise HTTPException(status_code=500, detail=str(e))
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

    pieces: list[str] = [str(result.get("optimized_summary", "") or "")]

    for collection_key, text_key in (("improved_bullets", "improved"), ("new_bullets", "text")):
        for bullet_obj in result.get(collection_key) or []:
            if isinstance(bullet_obj, dict):
                pieces.append(str(bullet_obj.get(text_key, "") or ""))
            elif bullet_obj:
                pieces.append(str(bullet_obj))

    pieces.extend(_flatten_skills(result.get("optimized_skills")))
    pieces.extend(_flatten_skills(result.get("added_keywords")))
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


def _stamp_ats_scores(result: dict, resume_text: str, job_description: str) -> tuple[int, int]:
    ats_before = count_kw_coverage(resume_text, job_description)
    ats_after = count_kw_coverage(_optimized_text_for_ats(result), job_description, source_text=resume_text)
    result["ats_before"] = ats_before
    result["ats_after"] = ats_after
    result["ats_regressed"] = ats_after < ats_before
    return ats_before, ats_after


def _apply_optimizer_safety_filters(
    result: dict,
    resume_text: str,
    job_description: str,
    job_title: str = "",
    user_id: str = "",
) -> dict:
    result = _validate_against_source(result, resume_text, job_description)

    # If the JD requires >= 3 ML skills and the original resume has 0,
    # we cannot optimize without fabrication. Block and flag.
    jd_lower = job_description.lower()
    original_lower = resume_text.lower()
    jd_ml_hits = sum(1 for kw in OPTIMIZER_ML_MARKERS if kw in jd_lower)
    resume_ml_hits = sum(1 for kw in OPTIMIZER_ML_MARKERS if kw in original_lower)

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
    # The JD is NEVER evidence for candidate skills or technical experience.
    fabricated_skills = []

    for bullet_obj in result.get("improved_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        bullet_text = str(bullet_obj.get("improved", "") or "")
        tech_terms = re.findall(r'\b[A-Z][a-zA-Z0-9+#.]{2,}\b', bullet_text)
        for term in tech_terms:
            t = term.lower().strip("*")
            if len(t) < 3 or t in OPTIMIZER_IGNORED_TECH_TERMS:
                continue
            if t not in original_lower:
                fabricated_skills.append(term)

    for bullet_obj in result.get("new_bullets") or []:
        if not isinstance(bullet_obj, dict):
            continue
        bullet_text = str(bullet_obj.get("text", "") or "")
        tech_terms = re.findall(r'\b[A-Z][a-zA-Z0-9+#.]{2,}\b', bullet_text)
        for term in tech_terms:
            t = term.lower().strip("*")
            if len(t) < 3 or t in OPTIMIZER_IGNORED_TECH_TERMS:
                continue
            if t not in original_lower:
                fabricated_skills.append(term)

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
            terms = [
                t for t in re.findall(r'\b[A-Z][a-zA-Z0-9+#.]{2,}\b', bullet_text)
                if t.lower() not in original_lower
            ]
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
        fabricated_skills.extend([
            ml_display_names.get(kw, kw)
            for kw in OPTIMIZER_ML_MARKERS
            if kw in jd_lower and kw not in original_lower
        ])

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
            f"{fabricated_unique}"
        )

        fabricated_lower = [term.lower() for term in fabricated_unique]
        for bullet_obj in result.get("improved_bullets") or []:
            if not isinstance(bullet_obj, dict):
                continue
            bullet_text = str(bullet_obj.get("improved", ""))
            if any(term in bullet_text.lower() for term in fabricated_lower):
                bullet_obj["improved"] = str(bullet_obj.get("original") or "")
                bullet_obj["keywords_added"] = []
                bullet_obj["improvement_reason"] = (
                    "Kept original bullet because the generated rewrite introduced skills absent from the original resume."
                )

        result["new_bullets"] = [
            bullet_obj for bullet_obj in result.get("new_bullets") or []
            if isinstance(bullet_obj, dict)
            and not any(term in str(bullet_obj.get("text", "")).lower() for term in fabricated_lower)
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
        result["optimized_summary"] = ""
        result["summary_grounding_note"] = (
            "Summary omitted due to domain mismatch between candidate background and job requirements."
        )
    else:
        existing_summary = str(result.get("optimized_summary", "") or "").strip()
        is_valid, reason = _verify_optimizer_summary(existing_summary, resume_text, job_title)
        if is_valid:
            result["optimized_summary"] = existing_summary
        else:
            logger.info(
                "Optimizer summary failed verification (%s) for user %s; using verified skills+education fallback",
                reason,
                user_id,
            )
            fallback = _build_skills_education_summary(resume_text, result)
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
    logger.info(
        "Optimizer model payload for user %s:\n%s",
        user_id,
        json.dumps(messages, ensure_ascii=False, indent=2),
    )
    text = await call_groq(messages, json_mode=True)
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
        retry_text = await call_groq(retry_messages, json_mode=True, temperature=0.1)
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
    )
    result = _validate_optimized_structure(
        doc,
        result,
        user_id,
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
        "You are an elite ATS optimization specialist and resume writer. "
        "Your ONLY job is to maximize keyword density and ATS score. "
        "You inject EVERY technical keyword from the job description "
        "into the resume. You rewrite EVERY bullet point to include "
        "job keywords plus source-grounded metrics only. You respond ONLY in "
        "valid JSON with no markdown, no code fences, no extra text.\n\n"
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
        "RULE 2 — SUMMARY (EVIDENCE-BASED 2-3 SENTENCE SYNTHESIS)\n"
        "════════════════════════════════════════════════════════\n"
        "- Generate a concise, high-impact 2-to-3 sentence summary (maximum 50 words).\n"
        "- Synthesize using ONLY:\n"
        "  (a) Skills and technologies explicitly present in the candidate's source resume.\n"
        "  (b) Verifiable metrics and numbers present in the source resume verbatim (never invent, inflate, or adjust figures).\n"
        "  (c) The candidate's real current role, stage, or background from their resume (e.g. Computer Science Student, Software Engineering Intern, Junior Developer).\n"
        "- NEVER use the target job title as candidate identity (e.g. if a student targets a Senior role, do NOT introduce them as a Senior Engineer).\n"
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
        "- Maximum 6 items per group\n"
        "- No duplicates across groups\n"
        "- Most JD-relevant items listed first within each group\n"
        "- Never mix group name sets across a single response\n"
        "- Pick one domain set and apply it consistently\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 4 — BULLET REWRITING & WORDING\n"
        "════════════════════════════════════════════════════════\n"
        "Each bullet should be:\n"
        "- Concise (preferred 15–28 words, hard maximum 32 words)\n"
        "- Specific, technically accurate, and relevant to the target JD\n"
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
        "- Prefer strong action verbs (Engineered, Architected, Built, Developed, Designed,\n"
        "  Implemented, Deployed, Optimized, Automated, Integrated, Launched, Streamlined, etc.)\n"
        "- Avoid passive or weak openings (worked, helped, assisted, involved, responsible, participated)\n"
        "- Avoid repetitive openings where natural, but never replace an accurate verb with an\n"
        "  unnatural synonym merely to increase vocabulary diversity.\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 6 — JD EXACT PHRASE MATCHING\n"
        "════════════════════════════════════════════════════════\n"
        "- Copy technical terms VERBATIM from JD — ATS matches\n"
        "  exact strings, not paraphrases\n"
        "- 'microservices architecture' → use those exact words\n"
        "- 'CI/CD pipelines' → use those exact words\n"
        "- 'cross-functional teams' → use those exact words\n"
        "- Never substitute a synonym for a technical term\n\n"
        
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
        "Apply to: improved_bullets, new_bullets, summary\n\n"
        
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
        
        '  "new_bullets": [\n'
        '    {\n'
        '      "text": "verb + technology + optional source metric",\n'
        '      "reason": "JD requires X, missing from original",\n'
        '      "jd_requirement": "exact JD phrase this addresses"\n'
        '    }\n'
        '  ],\n'
        
        '  "added_keywords": ["every source-grounded JD keyword present in output"],\n'
        '  "missing_keywords": ["JD keywords still not coverable from candidate resume"],\n'
        
        '  "improvement_explanation": {\n'
        '    "keywords_added": ["REST API", "Docker", "Microservices"],\n'
        '    "verbs_upgraded": [\n'
        '      {"from": "worked", "to": "Engineered"},\n'
        '      {"from": "helped", "to": "Implemented"}\n'
        '    ],\n'
        '    "metrics_added": [\n'
        '      "Source metric preserved in rewritten bullet",\n'
        '      "No metric added where source bullet had none"\n'
        '    ],\n'
        '    "sections_improved": [\n'
        '      "Summary rewritten with JD-specific technologies",\n'
        '      "Skills grouped by domain category",\n'
        '      "All bullets rewritten with power verbs and metrics"\n'
        '    ]\n'
        '  },\n'
        
        '  "ats_tips": [\n'
        '    "Highlight microservices in summary sentence 2",\n'
        '    "Mention CI/CD in experience bullet 3"\n'
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

        if result.get("ats_regressed"):
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
                result["ats_retry_previous_after"] = first_attempt_after
            except Exception as retry_error:
                result["ats_retry_attempted"] = True
                result["ats_retry_failed"] = True
                result["ats_retry_error"] = str(retry_error)[:200]
                logger.warning(
                    f"ATS regression retry failed for user {user['user_id']}: {retry_error}"
                )

        result["ats_regressed"] = ats_after < ats_before
        result.setdefault("ats_retry_attempted", False)

        try:
            supabase.table("resume_optimizations").insert({
                "user_id":         user["user_id"],
                "job_title":       body.job_title or "",
                "job_description": body.job_description[:500],
                "result_json":     result,
            }).execute()
        except Exception as e:
            logger.warning(f"DB save failed: {e}")

        return {
            "success": True,
            "optimization": result,
            "ats_before": ats_before,
            "ats_after": ats_after,
            "ats_regressed": result["ats_regressed"],
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

_SECTION_HEADER_RE = re.compile(
    r"^(work\s+experience|professional\s+experience|experience|employment|"
    r"projects?|project\s+experience|academic\s+projects?|personal\s+projects?|"
    r"education|skills|technical\s+skills|core\s+skills|certifications?|"
    r"summary|profile|objective|contact|achievements?|awards?)\b",
    re.IGNORECASE,
)

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
    7-module resume intelligence analysis.
    Runs: ATS scan, recruiter-lens score, bullet audit,
    skill gap matrix, rejection diagnosis.
    Does NOT rewrite or consume an optimization credit.
    """
    resume_text = body.resume_text or ""
    job_description = body.job_description or ""
    job_title = body.job_title or ""

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required.")

    if len(resume_text) > 8000:
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
        ], json_mode=True)
        analysis = _extract_json(raw)
        if not isinstance(analysis, dict):
            raise ValueError("Analysis response was not a JSON object.")

        # Compute recruiter lens total from dimensions if model got it wrong
        dims = analysis.get("module2_recruiter_lens", {}).get("dimensions", {})
        if dims:
            computed_total = 0
            for v in dims.values():
                if isinstance(v, dict):
                    try:
                        computed_total += int(float(v.get("score", 0) or 0))
                    except Exception:
                        computed_total += 0
            analysis["module2_recruiter_lens"]["total"] = computed_total

            # Set interpretation band
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
            analysis["module2_recruiter_lens"]["interpretation"] = interp

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

        # Deterministic guard for obvious ML-role/domain mismatches.
        role_context = f"{job_title}\n{job_description}".lower()
        resume_context = resume_text.lower()
        ml_jd = bool(re.search(
            r"\b(machine learning|ml|ai|artificial intelligence|deep learning|"
            r"pytorch|tensorflow|scikit-learn|sklearn|nlp|computer vision|mlops|llm)\b",
            role_context,
        ))
        ml_resume = bool(re.search(
            r"\b(machine learning|ml|ai|artificial intelligence|deep learning|pytorch|"
            r"tensorflow|scikit-learn|sklearn|nlp|computer vision|mlops|llm|"
            r"model training|data science)\b",
            resume_context,
        ))
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

        # Save analysis to DB
        try:
            supabase.table("resume_analyses").insert({
                "user_id":         user["user_id"],
                "job_title":       job_title,
                "job_description": job_description[:500],
                "result_json":     analysis,
            }).execute()
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