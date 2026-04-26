# ============================================================
# CareerLens – AI Service (Groq API)
# File: backend/services/gemini_service.py
# Uses Groq's fast inference API with Llama models
# ============================================================

import httpx
import json
import re
import logging
import uuid
import math
from config import settings

logger = logging.getLogger("careerlens.ai")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = settings.GROQ_MODEL

# Curated fallback resources used when the model omits usable links.
DEFAULT_RESOURCES = {
    "ml_fundamentals": [
        {"title": "Google Machine Learning Crash Course", "url": "https://developers.google.com/machine-learning/crash-course", "type": "course"},
        {"title": "Machine Learning Specialization (Coursera)", "url": "https://www.coursera.org/specializations/machine-learning-introduction/", "type": "course"},
    ],
    "deep_learning": [
        {"title": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials", "type": "docs"},
        {"title": "PyTorch Tutorials", "url": "https://docs.pytorch.org/tutorials/", "type": "docs"},
        {"title": "Deep Learning Specialization", "url": "https://www.deeplearning.ai/courses/deep-learning-specialization/", "type": "course"},
    ],
    "nlp": [
        {"title": "Hugging Face LLM Course", "url": "https://huggingface.co/learn/nlp-course", "type": "course"},
        {"title": "scikit-learn Text Tutorial", "url": "https://scikit-learn.org/1.3/tutorial/text_analytics/working_with_text_data.html", "type": "docs"},
    ],
    "mlops": [
        {"title": "Made With ML MLOps Course", "url": "https://madewithml.com/courses/mlops/", "type": "course"},
        {"title": "Full Stack Deep Learning Course", "url": "https://fullstackdeeplearning.com/course/", "type": "course"},
    ],
}


def _extract_url(text: str) -> str:
    match = re.search(r"https?://[^\s)>\],]+", text or "")
    return match.group(0).strip() if match else ""


def _normalize_resources(resources) -> list[dict]:
    normalized = []
    if not isinstance(resources, list):
        return normalized

    for resource in resources:
        if isinstance(resource, str):
            url = _extract_url(resource)
            title = resource.replace(url, "").strip(" -\u2013\u2014") if url else resource.strip()
            normalized.append({
                "title": title or url or "Learning Resource",
                "url": url,
                "type": "resource",
            })
        elif isinstance(resource, dict):
            title = str(resource.get("title") or resource.get("name") or resource.get("resource") or "").strip()
            url = str(resource.get("url") or resource.get("link") or "").strip()
            if not url:
                url = _extract_url(title)
            if not title:
                title = url or "Learning Resource"
            normalized.append({
                "title": title,
                "url": url,
                "type": str(resource.get("type") or "resource"),
            })

    # Keep a compact and deduplicated list.
    deduped = []
    seen = set()
    for item in normalized:
        key = (item.get("title", "").lower(), item.get("url", "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:4]


def _fallback_resources_for_focus(focus: str, missing_skills: list | None = None) -> list[dict]:
    text = f"{focus} {' '.join(missing_skills or [])}".lower()
    candidates = []

    if any(k in text for k in ["nlp", "natural language", "llm", "transformer", "bert"]):
        candidates.extend(DEFAULT_RESOURCES["nlp"])
    if any(k in text for k in ["deep learning", "neural", "cnn", "rnn", "tensorflow", "pytorch", "keras"]):
        candidates.extend(DEFAULT_RESOURCES["deep_learning"])
    if any(k in text for k in ["deploy", "deployment", "mlops", "cloud", "production", "project", "portfolio"]):
        candidates.extend(DEFAULT_RESOURCES["mlops"])
    if not candidates:
        candidates.extend(DEFAULT_RESOURCES["ml_fundamentals"])

    deduped = []
    seen_urls = set()
    for item in candidates:
        url = item["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(item)
    return deduped[:3]


def _ensure_learning_resources(result: dict) -> dict:
    roadmap = result.get("learning_roadmap")
    if not isinstance(roadmap, list):
        return result

    missing_skills = result.get("missing_skills", [])
    for step in roadmap:
        if not isinstance(step, dict):
            continue
        focus = str(step.get("focus", ""))
        normalized = _normalize_resources(step.get("resources"))
        with_urls = [r for r in normalized if str(r.get("url", "")).startswith("http")]
        step["resources"] = with_urls[:3] if with_urls else _fallback_resources_for_focus(focus, missing_skills)

    result["learning_roadmap"] = roadmap
    return result


def _to_int(value, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return default


def _clamp(value: int | float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(round(value))))


def _grade_from_score(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _readiness_from_score(score: int) -> str:
    if score >= 80:
        return "ready"
    if score >= 60:
        return "almost ready"
    return "needs work"


def _count_resume_sections(resume_text: str) -> int:
    if not isinstance(resume_text, str):
        return 0
    text = resume_text.lower()
    patterns = [
        r"\beducation\b",
        r"\bexperience\b",
        r"\bprojects?\b",
        r"\bskills?\b",
        r"\b(certifications?|licenses?)\b",
        r"\b(summary|objective|profile)\b",
    ]
    return sum(1 for p in patterns if re.search(p, text))


def _count_critical_ml_missing(missing_skills: list, job_role: str) -> int:
    role_text = str(job_role or "").lower()
    ml_role = any(k in role_text for k in ["ml", "machine learning", "ai", "data science", "nlp", "computer vision"])
    if not ml_role:
        return 0

    critical_keywords = {
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "scikit",
        "statistics",
        "linear algebra",
        "data analysis",
        "feature engineering",
        "model evaluation",
        "sql",
    }
    count = 0
    for skill in missing_skills:
        s = str(skill or "").lower()
        if any(k in s for k in critical_keywords):
            count += 1
    return count


def _coerce_list(value) -> list:
    if isinstance(value, list):
        return value
    return []


def _calibrate_resume_scores(result: dict, resume_text: str, github_data: dict, job_role: str) -> dict:
    calibrated = dict(result or {})

    skill_match = _clamp(_to_int(calibrated.get("skill_match_percentage"), 0))
    strengths = _coerce_list(calibrated.get("strengths"))
    weaknesses = _coerce_list(calibrated.get("weaknesses"))
    missing_skills = _coerce_list(calibrated.get("missing_skills"))
    top_keywords_missing = _coerce_list(calibrated.get("top_keywords_missing"))

    github_profile = calibrated.get("github_analysis") if isinstance(calibrated.get("github_analysis"), dict) else {}
    profile_strength = str(github_profile.get("profile_strength", "")).lower()
    profile_boost = {"strong": 6, "moderate": 2, "weak": -4}.get(profile_strength, 0)

    public_repos = _to_int(github_data.get("public_repos"), 0)
    total_stars = _to_int(github_data.get("total_stars"), 0)
    languages_count = len(github_data.get("languages", {}) or {})

    repo_points = min(10, public_repos * 0.6)
    stars_points = min(5, math.log1p(max(total_stars, 0)) * 1.5)
    language_points = min(4, languages_count * 1.0)

    critical_ml_missing = _count_critical_ml_missing(missing_skills, job_role)
    missing_penalty = min(20, len(missing_skills) * 2.5)
    weakness_penalty = min(12, len(weaknesses) * 2.5)
    critical_penalty = min(12, critical_ml_missing * 4)
    short_resume_penalty = 5 if len(str(resume_text or "")) < 700 else 0

    raw_score = (
        22
        + (skill_match * 0.5)
        + min(10, len(strengths) * 3)
        + repo_points
        + stars_points
        + language_points
        + profile_boost
        - missing_penalty
        - weakness_penalty
        - critical_penalty
        - short_resume_penalty
    )
    score = _clamp(raw_score)

    section_count = _count_resume_sections(resume_text)
    section_bonus = min(12, section_count * 2)
    keyword_penalty = min(20, len(top_keywords_missing) * 4)
    ats_raw = (
        24
        + (skill_match * 0.5)
        + section_bonus
        - keyword_penalty
        - min(18, len(missing_skills) * 2.5)
    )
    ats_score = _clamp(ats_raw)

    calibrated["skill_match_percentage"] = skill_match
    calibrated["score"] = score
    calibrated["ats_score"] = ats_score
    calibrated["grade"] = _grade_from_score(score)
    calibrated["job_readiness"] = _readiness_from_score(score)
    calibrated["scoring_note"] = "Scores are strictly calibrated for realism based on skill match, role gaps, and evidence."
    return calibrated


async def call_groq(messages: list, temperature: float = 0.3) -> str:
    groq_api_key = settings.GROQ_API_KEY
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in your .env file")
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_completion_tokens": 2048,
            },
        )
        if response.status_code >= 400:
            err_detail = response.text
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    err = payload.get("error", payload)
                    if isinstance(err, dict):
                        err_detail = err.get("message") or err.get("type") or response.text
                    else:
                        err_detail = str(err)
            except Exception:
                pass
            raise ValueError(f"Groq API error ({response.status_code}): {err_detail}")

        data = response.json()
        return data["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    def _sanitize_json_text(value: str) -> str:
        # Remove non-printable control chars and escape raw newlines inside strings.
        value = value.replace("\u0000", "")
        value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", value)

        out = []
        in_str = False
        escape = False
        for ch in value:
            if in_str:
                if escape:
                    escape = False
                    out.append(ch)
                    continue
                if ch == "\\":
                    escape = True
                    out.append(ch)
                    continue
                if ch == '"':
                    in_str = False
                    out.append(ch)
                    continue
                if ch == "\n":
                    out.append("\\n")
                    continue
                if ch == "\r":
                    continue
                if ch == "\t":
                    out.append("\\t")
                    continue
                if ord(ch) < 32:
                    continue
                out.append(ch)
            else:
                if ch == '"':
                    in_str = True
                out.append(ch)
        return "".join(out)

    text = re.sub(r"```json|```", "", text).strip()
    text = _sanitize_json_text(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(_sanitize_json_text(match.group()))
        raise ValueError(f"Could not parse JSON: {text[:300]}")


async def analyze_resume_with_gemini(resume_text, github_data, job_role):
    system = (
        "You are an expert career coach and ATS specialist. "
        "Score strictly and avoid inflated optimism. "
        "Always respond with valid JSON only, no extra text."
    )
    user = f"""Analyze this resume and return ONLY a valid JSON object.

RESUME: {resume_text[:4000]}
GITHUB: Username={github_data.get("username","N/A")}, Repos={github_data.get("public_repos",0)}, Languages={", ".join(list(github_data.get("languages",{}).keys())[:6])}, Stars={github_data.get("total_stars",0)}, Projects={", ".join([r["name"] for r in github_data.get("repos",[])[:4]])}
Target Role: {job_role}

Return this exact JSON:
{{
  "score": <0-100>, "grade": "<A/B/C/D/F>",
  "summary": "<2-3 sentence assessment>",
  "strengths": ["<s1>","<s2>","<s3>"],
  "weaknesses": ["<w1>","<w2>","<w3>"],
  "missing_skills": ["<sk1>","<sk2>","<sk3>","<sk4>","<sk5>"],
  "skill_match_percentage": <0-100>,
  "suggested_projects": [{{"title":"<n>","description":"<d>","skills":["<s>"],"impact":"<i>"}}],
  "learning_roadmap": [
    {{"week":1,"focus":"<t>","resources":[{{"title":"<resource title>","url":"<https://...>","type":"<course/docs/video>"}}],"goal":"<g>"}},
    {{"week":4,"focus":"<t>","resources":[{{"title":"<resource title>","url":"<https://...>","type":"<course/docs/video>"}}],"goal":"<g>"}},
    {{"week":8,"focus":"<t>","resources":[{{"title":"<resource title>","url":"<https://...>","type":"<course/docs/video>"}}],"goal":"<g>"}},
    {{"week":12,"focus":"<t>","resources":[{{"title":"<resource title>","url":"<https://...>","type":"<course/docs/video>"}}],"goal":"<g>"}}
  ],
  "ats_tips": ["<t1>","<t2>","<t3>"],
  "ats_score": <0-100>,
  "github_analysis": {{"profile_strength":"<strong/moderate/weak>","highlights":["<h>"],"improvements":["<i>"]}},
  "top_keywords_missing": ["<k1>","<k2>"],
  "estimated_salary_range": "<e.g. $80,000-$110,000>",
  "job_readiness": "<ready/almost ready/needs work>"
}}

Rules:
- For each learning_roadmap week, include 2-3 real learning resources with working https URLs.
- Prioritize official docs or highly trusted learning providers.
- Keep resources specific to the missing skills and target role.
- Be brutally honest: do not inflate score just for potential.
- If there are critical role gaps, keep score conservative (typically 35-60)."""
    text = await call_groq([{"role":"system","content":system},{"role":"user","content":user}])
    parsed = _ensure_learning_resources(_extract_json(text))
    return _calibrate_resume_scores(parsed, resume_text=resume_text, github_data=github_data or {}, job_role=job_role)


# ============================================================
# CHANGED: generate_interview_questions
# - Accepts company_context parameter
# - Generates coding questions with real code snippets
# - Enforces category diversity (technical, behavioral, coding)
# ============================================================
async def generate_interview_questions(
    job_role: str,
    skills: list,
    github_projects: list,
    question_count: int = 8,
    company_context: str = "",
) -> list[dict]:
    count = max(5, min(12, int(question_count)))
    variation_seed = uuid.uuid4().hex[:8]

    # Determine best language for coding questions based on role
    role_lower = (job_role or "").lower()
    if any(k in role_lower for k in ["python", "data", "ml", "ai", "machine"]):
        code_lang = "python"
    elif any(k in role_lower for k in ["frontend", "react", "vue", "angular", "ui"]):
        code_lang = "javascript"
    elif any(k in role_lower for k in ["android", "kotlin"]):
        code_lang = "kotlin"
    elif any(k in role_lower for k in ["ios", "swift"]):
        code_lang = "swift"
    elif any(k in role_lower for k in ["java", "spring"]):
        code_lang = "java"
    else:
        code_lang = "python"

    # How many of each type to request
    behavioral_count = min(2, count // 4)
    coding_count = max(2, count // 4)
    technical_count = count - behavioral_count - coding_count

    system = (
        "You are a senior technical interviewer at a top tech company. "
        "You write brutally realistic interview questions. "
        "Respond with a valid JSON array only — no markdown, no extra text."
    )

    user = f"""Generate exactly {count} interview questions for: {job_role}

{"=" * 60}
{company_context}
{"=" * 60}

CANDIDATE CONTEXT:
- Skills: {", ".join(skills) if skills else "general software engineering"}
- Projects: {", ".join(github_projects) if github_projects else "not specified"}
- Variation seed: {variation_seed}

QUESTION BREAKDOWN — you MUST follow this exactly:
- {technical_count} questions with category "technical" (system design, concepts, architecture)
- {behavioral_count} questions with category "behavioral" (STAR format, past experience)
- {coding_count} questions with category "code_fix" OR "code_write" OR "debugging" OR "error_handling"

CODING QUESTION RULES (mandatory for all coding categories):
- "code_fix"       → Write a {code_lang} function with a REAL subtle bug (off-by-one, wrong logic, race condition, etc). The bug must not be obvious. Set code_snippet to the buggy code.
- "code_write"     → Write a clear algorithmic problem statement. Set code_snippet to null.
- "debugging"      → Write {code_lang} code with a RUNTIME or LOGIC error (null pointer, infinite loop, wrong output). Set code_snippet to the broken code.
- "error_handling" → Write {code_lang} code that CRASHES on edge cases (empty input, division by zero, missing key). Set code_snippet to the fragile code.

For code_snippet: write 8-18 lines of REALISTIC, PLAUSIBLE-LOOKING code — not toy examples. 
The bug/issue must be genuinely subtle. Indent properly using \\n for newlines.

SCORING CONTEXT (tell the evaluator what a good answer looks like):
- expected_points should be 3-4 specific things a strong answer must cover
- For coding: include the CORRECT fix/approach in expected_points so the evaluator knows what to look for

Return ONLY this JSON array (exactly {count} items):
[
  {{
    "id": 1,
    "question": "<the question text>",
    "category": "technical|behavioral|situational|code_fix|code_write|debugging|error_handling",
    "difficulty": "easy|medium|hard",
    "expected_points": ["<specific point 1>", "<specific point 2>", "<specific point 3>"],
    "code_snippet": "<{code_lang} code with bug/issue, or null for code_write/technical/behavioral>",
    "language": "{code_lang} or null for non-coding questions"
  }}
]"""

    text = await call_groq(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.85,
    )
    cleaned = re.sub(r"```json|```", "", text).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try extracting array
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            raise ValueError("AI returned unparseable interview questions.")

    if isinstance(parsed, dict):
        parsed = parsed.get("questions", [])
    if not isinstance(parsed, list):
        raise ValueError("Invalid interview questions payload from AI.")

    valid_categories = {
        "technical", "behavioral", "situational",
        "code_fix", "code_write", "debugging", "error_handling",
    }
    coding_categories = {"code_fix", "code_write", "debugging", "error_handling"}

    normalized: list[dict] = []
    seen: set[str] = set()

    for i, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            continue
        question_text = str(item.get("question") or "").strip()
        if not question_text:
            continue
        key = re.sub(r"\s+", " ", question_text).lower()
        if key in seen:
            continue
        seen.add(key)

        category = str(item.get("category") or "technical").strip().lower()
        if category not in valid_categories:
            category = "technical"

        difficulty = str(item.get("difficulty") or "medium").strip().lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"

        expected_points = item.get("expected_points") or []
        if not isinstance(expected_points, list):
            expected_points = []
        expected_points = [str(p).strip() for p in expected_points if str(p).strip()][:4]

        # Code fields — only for coding categories
        code_snippet = None
        language = None
        if category in coding_categories:
            raw = item.get("code_snippet") or item.get("code") or ""
            code_snippet = str(raw).strip() or None
            raw_lang = item.get("language") or code_lang
            language = str(raw_lang).strip().lower() or code_lang

        normalized.append({
            "id": i,
            "question": question_text,
            "category": category,
            "difficulty": difficulty,
            "expected_points": expected_points,
            "code_snippet": code_snippet,
            "language": language,
        })

    if len(normalized) < max(3, count // 2):
        raise ValueError("AI returned too few usable interview questions.")

    # ── Pad to exact count if AI returned fewer ────────────────────────────────
    # Generic fallback questions per category to fill gaps
    FALLBACK_QUESTIONS = [
        {"question": f"Walk me through how you would design a scalable REST API for a {job_role} role. What would your tech stack look like and why?", "category": "technical", "difficulty": "medium", "expected_points": ["API design principles", "authentication strategy", "scalability considerations", "error handling approach"]},
        {"question": "Tell me about the most technically complex project you've worked on. What was your specific contribution and what did you learn?", "category": "behavioral", "difficulty": "medium", "expected_points": ["specific technical details", "personal ownership", "challenges faced", "measurable outcome"]},
        {"question": f"Write a function in {code_lang} that finds all duplicate elements in an array and returns them. Optimize for time complexity.", "category": "code_write", "difficulty": "medium", "expected_points": [f"hash set approach O(n)", "handles edge cases (empty, all duplicates)", "correct return type", "clean readable code"], "code_snippet": None, "language": code_lang},
        {"question": "How do you approach debugging a production issue when you have no logs and users are complaining?", "category": "situational", "difficulty": "hard", "expected_points": ["systematic investigation approach", "communication with stakeholders", "rollback decision criteria", "post-mortem process"]},
        {"question": f"Explain the difference between concurrency and parallelism with a practical example in {code_lang}.", "category": "technical", "difficulty": "medium", "expected_points": ["correct definitions", "real-world analogy", "when to use each", "implementation awareness"]},
        {"question": "Describe a situation where you had to push back on a deadline or a requirement. How did you handle it?", "category": "behavioral", "difficulty": "medium", "expected_points": ["clear communication", "data-driven reasoning", "stakeholder management", "final outcome"]},
    ]

    while len(normalized) < count:
        fallback_idx = len(normalized) % len(FALLBACK_QUESTIONS)
        fb = dict(FALLBACK_QUESTIONS[fallback_idx])
        fb["id"] = len(normalized) + 1
        # Avoid duplicates
        key = re.sub(r"\s+", " ", fb["question"]).lower()
        if key not in seen:
            seen.add(key)
            if "code_snippet" not in fb:
                fb["code_snippet"] = None
            if "language" not in fb:
                fb["language"] = None
            normalized.append(fb)
        else:
            break  # Can't add more unique fallbacks

    # Trim to exact count in case AI gave more
    return normalized[:count]



# Lookup table — maps platform names the AI commonly returns → their real URLs
PLATFORM_URL_MAP: dict[str, str] = {
    "leetcode": "https://leetcode.com/",
    "neetcode": "https://neetcode.io/",
    "hackerrank": "https://www.hackerrank.com/",
    "codewars": "https://www.codewars.com/",
    "codecademy": "https://www.codecademy.com/",
    "freecodecamp": "https://www.freecodecamp.org/",
    "udemy": "https://www.udemy.com/",
    "coursera": "https://www.coursera.org/",
    "edx": "https://www.edx.org/",
    "pluralsight": "https://www.pluralsight.com/",
    "linkedin learning": "https://www.linkedin.com/learning/",
    "udacity": "https://www.udacity.com/",
    "mit opencourseware": "https://ocw.mit.edu/",
    "khan academy": "https://www.khanacademy.org/",
    "youtube": "https://www.youtube.com/",
    "github": "https://github.com/",
    "stackoverflow": "https://stackoverflow.com/",
    "medium": "https://medium.com/",
    "dev.to": "https://dev.to/",
    "roadmap.sh": "https://roadmap.sh/",
    "system design primer": "https://github.com/donnemartin/system-design-primer",
    "bytebytego": "https://bytebytego.com/",
    "designing data-intensive applications": "https://dataintensive.net/",
    "cracking the coding interview": "https://www.crackingthecodinginterview.com/",
    "fast.ai": "https://www.fast.ai/",
    "hugging face": "https://huggingface.co/learn/",
    "tensorflow": "https://www.tensorflow.org/tutorials",
    "pytorch": "https://pytorch.org/tutorials/",
    "scikit-learn": "https://scikit-learn.org/stable/tutorial/",
    "django": "https://docs.djangoproject.com/",
    "fastapi": "https://fastapi.tiangolo.com/tutorial/",
    "react": "https://react.dev/learn",
    "node.js": "https://nodejs.org/en/learn/",
    "docker": "https://docs.docker.com/get-started/",
    "kubernetes": "https://kubernetes.io/docs/tutorials/",
    "aws": "https://aws.amazon.com/training/",
    "google cloud": "https://cloud.google.com/learn/training",
    "azure": "https://learn.microsoft.com/en-us/training/",
    "pramp": "https://www.pramp.com/",
    "interviewing.io": "https://interviewing.io/",
    "exponent": "https://www.tryexponent.com/",
    "visualgo": "https://visualgo.net/",
    "refactoring.guru": "https://refactoring.guru/design-patterns",
    "cs50": "https://cs50.harvard.edu/x/",
    "cs229": "https://cs229.stanford.edu/",
    "sqlzoo": "https://sqlzoo.net/",
    "mode": "https://mode.com/sql-tutorial/",
    "karpathy": "https://karpathy.ai/zero-to-hero.html",
    "madewithml": "https://madewithml.com/",
}


def _resolve_resource_url(resource_str: str) -> tuple[str, str]:
    """
    Given a resource string from the AI, return (title, url).
    Tries: embedded URL → platform name lookup → empty string.
    """
    s = str(resource_str or "").strip()

    # 1. Extract embedded URL
    url_match = re.search(r"https?://[^\s\"')]+", s)
    if url_match:
        url = url_match.group(0).rstrip(".,;)")
        # Title = everything before the URL, cleaned
        title = s[:s.index(url_match.group(0))].strip(" —-–→")
        if not title:
            title = url.replace("https://", "").replace("www.", "").split("/")[0]
        return title, url

    # 2. Strip arrows/dashes to get clean name
    clean = re.sub(r"[\-–—→]+", " ", s).strip()
    # Remove leading "topic: " or "skill — " prefix patterns
    clean = re.sub(r"^[^:]+:\s*", "", clean).strip()

    # 3. Lookup by platform name (case-insensitive)
    lower = clean.lower()
    for platform, url in PLATFORM_URL_MAP.items():
        if platform in lower:
            # Use the original clean string as title (may have extra context)
            title = clean if len(clean) < 80 else platform.title()
            return title, url

    # 4. No URL found — return name only
    return clean or s, ""


# ============================================================
# CHANGED: evaluate_interview
# - Strict per-question scoring rules (0-10, no inflation)
# - Mathematical overall score derived from question scores
# - Brutally honest feedback on wrong/blank answers
# - Resources mapped to actual weak areas with real URLs
# ============================================================
async def evaluate_interview(job_role: str, transcript: list[dict]) -> dict:
    n = len(transcript)
    transcript_text = "\n\n".join([
        f"Q{i+1} [{t.get('category', 'technical')}]: {t['question']}\nA{i+1}: {t['answer'] or '[NO ANSWER PROVIDED]'}"
        for i, t in enumerate(transcript)
    ])

    system = (
        "You are a brutally honest senior technical interviewer. "
        "You do NOT inflate scores. You do NOT give credit for effort alone. "
        "You score based on correctness, depth, and completeness — nothing else. "
        "Respond with valid JSON only."
    )

    user = f"""Evaluate this {job_role} interview transcript. Be ruthlessly honest.

{transcript_text}

STRICT SCORING RULES — follow exactly, no exceptions:
- 9-10: Exceptionally complete, correct, with depth and edge cases covered
- 7-8:  Correct and solid, minor gaps only
- 5-6:  Partially correct, key points missing but shows some understanding
- 3-4:  Mostly wrong or very shallow — shows limited understanding
- 1-2:  Wrong, blank, irrelevant, or "I don't know"
- 0:    No answer at all

ADDITIONAL RULES:
- An answer under 20 words scores MAX 3/10 regardless of content
- "I don't know" or blank answers score 0-1
- Vague buzzwords with no specifics score MAX 4/10
- For coding questions: partial/incorrect code scores MAX 4/10; correct working solution scores 7+
- overall_score MUST equal: round(average of all question scores * 10) — no exceptions
- Do NOT add points for "good effort", "enthusiasm", or "potential"
- If {n} answers were given and most were weak, overall_score should reflect that mathematically

For recommended_resources: list EXACTLY 6 resources using this format:
"Resource Name — https://actual-url.com"
Examples of correct format:
"LeetCode Top 150 — https://leetcode.com/studyplan/top-interview-150/"
"NeetCode DSA Roadmap — https://neetcode.io/roadmap"
"System Design Primer — https://github.com/donnemartin/system-design-primer"
Pick resources specifically matched to the weak areas you identified.

Return ONLY this JSON:
{{
  "overall_score": <MUST equal round(avg_question_score * 10)>,
  "technical_score": <0-100, average of technical/coding question scores * 10>,
  "communication_score": <0-100, based purely on answer clarity and structure>,
  "confidence_score": <0-100, based on answer completeness and consistency>,
  "hire_recommendation": "Strong Yes — exceptional performance|Yes — solid with minor gaps|Maybe — potential but significant gaps|No — too many weak answers|Strong No — fundamental gaps, needs basics",
  "summary": "<2-3 sentences, honest assessment, name specific failures and wins>",
  "strengths": ["<only genuine strengths with evidence from answers>"],
  "improvements": ["<specific skill/topic the candidate clearly failed — name the exact gap>"],
  "question_feedback": [
    {{
      "question": "<exact question text>",
      "score": <0-10, follow strict rules above>,
      "feedback": "<specific: what was right, what was wrong, what was missing>",
      "ideal_answer_hint": "<what a correct answer should have included>"
    }}
  ],
  "recommended_resources": [
    "Resource Name — https://actual-url.com",
    "Resource Name — https://actual-url.com",
    "Resource Name — https://actual-url.com",
    "Resource Name — https://actual-url.com",
    "Resource Name — https://actual-url.com",
    "Resource Name — https://actual-url.com"
  ],
  "weak_areas": ["<specific topic or skill the candidate needs to study>"]
}}

IMPORTANT: question_feedback must have exactly {n} entries, one per question in order."""

    text = await call_groq(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    result = _extract_json(text)

    # Post-process resources: resolve any missing URLs using the platform lookup
    raw_resources = result.get("recommended_resources") or []
    resolved = []
    for r in raw_resources:
        title, url = _resolve_resource_url(str(r))
        if url:
            resolved.append(f"{title} — {url}")
        elif title:
            # Still include it so frontend shows the name even without a link
            resolved.append(title)
    if resolved:
        result["recommended_resources"] = resolved

    return result


async def chat_with_gemini(history, user_message):
    messages = [{"role":"system","content":"You are CareerLens AI, an expert career coach. Help with resumes, job searching, interviews, salary negotiation, and learning paths. Be concise and practical. Keep responses under 200 words."}]
    for msg in history[-8:]:
        messages.append({"role":"user" if msg["role"]=="user" else "assistant","content":msg["content"]})
    messages.append({"role":"user","content":user_message})
    return await call_groq(messages, temperature=0.7)

async def generate_beginner_roadmap(background, target_field, hours_per_day, timeline, goal):
    system = "You are an expert tech career coach for complete beginners. Always respond with valid JSON only, no extra text."
    user = f"""Create a beginner roadmap for:
- Background: {background}
- Target field: {target_field}
- Study time: {hours_per_day}
- Timeline: {timeline}
- Goal: {goal}

Return ONLY this JSON:
{{
  "summary": "<encouraging 2-3 sentence overview>",
  "total_weeks": <number>,
  "total_skills": <number>,
  "difficulty": "Beginner Friendly",
  "phases": [
    {{
      "title": "<phase name>",
      "week_start": 1,
      "week_end": 4,
      "topics": ["<topic 1>", "<topic 2>", "<topic 3>"],
      "free_resources": [
        {{"name": "<resource name>", "url": "<https://actual-link.com>", "type": "<YouTube/Website/Course>"}},
        {{"name": "<resource name>", "url": "<https://actual-link.com>", "type": "<YouTube/Website/Course>"}}
      ]
    }}
  ],
  "start_today": ["<action 1>", "<action 2>", "<action 3>"],
  "reality_check": "<honest but encouraging paragraph>",
  "useful_links": [
    {{"name": "<site name>", "url": "<https://actual-link.com>", "description": "<what it offers>"}},
    {{"name": "<site name>", "url": "<https://actual-link.com>", "description": "<what it offers>"}},
    {{"name": "<site name>", "url": "<https://actual-link.com>", "description": "<what it offers>"}}
  ]
}}"""
    text = await call_groq([
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ])
    return _extract_json(text)


def _extract_ats_keywords(text: str) -> list[str]:
    stopwords = {
        "the", "and", "for", "with", "from", "that", "this", "your", "you", "are", "our", "their",
        "will", "have", "has", "had", "into", "onto", "over", "under", "using", "use", "used", "to",
        "in", "on", "of", "is", "it", "as", "be", "by", "or", "an", "a", "at", "we", "they", "them",
        "job", "role", "required", "requirements", "responsibilities", "candidate", "experience",
        "skills", "ability", "strong", "good", "excellent", "work", "working", "team", "teams",
        "years", "year", "plus", "preferred", "knowledge", "understanding", "build", "develop",
        "design", "maintain", "improve", "ensure", "support", "including", "across",
    }
    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}", (text or "").lower())
    keywords = []
    seen = set()
    for token in raw:
        t = token.strip(".-")
        if not t or t in stopwords:
            continue
        if len(t) < 3 and t not in {"ai", "ml", "js", "go", "c", "c++"}:
            continue
        if t in seen:
            continue
        seen.add(t)
        keywords.append(t)
    return keywords


def _fallback_ats_match(resume_text: str, job_description: str) -> dict:
    resume_keywords = _extract_ats_keywords(resume_text)
    jd_keywords = _extract_ats_keywords(job_description)
    resume_set = set(resume_keywords)

    if not jd_keywords:
        jd_keywords = ["python", "sql", "git"]

    matched_keywords = [k for k in jd_keywords if k in resume_set][:30]
    missing_keywords = [k for k in jd_keywords if k not in resume_set][:30]

    skill_bank = [
        "python", "java", "javascript", "typescript", "react", "node", "node.js", "fastapi", "django",
        "flask", "sql", "postgresql", "mysql", "mongodb", "redis", "aws", "azure", "gcp", "docker",
        "kubernetes", "terraform", "ci/cd", "git", "github", "rest", "api", "machine learning",
        "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    ]

    jd_lower = (job_description or "").lower()
    resume_lower = (resume_text or "").lower()
    matched_skills = [s for s in skill_bank if s in jd_lower and s in resume_lower][:12]
    missing_skills = [s for s in skill_bank if s in jd_lower and s not in resume_lower][:12]

    keyword_ratio = len(matched_keywords) / max(1, len(jd_keywords))
    score = int(round(max(0, min(100, keyword_ratio * 100 - min(20, len(missing_skills) * 2)))))

    if score >= 75:
        verdict = "strong match"
    elif score >= 55:
        verdict = "moderate match"
    elif score >= 35:
        verdict = "weak match"
    else:
        verdict = "not qualified"

    if verdict == "strong match":
        honest_verdict = "Your resume aligns well with the role requirements. Keep refining impact metrics and role-specific keywords."
    elif verdict == "moderate match":
        honest_verdict = "You match part of the role, but important requirements are missing. You will be filtered out for stronger applicants unless you close the gaps."
    elif verdict == "weak match":
        honest_verdict = "This resume is weak for this job. Too many role-specific keywords and skills are missing to pass ATS reliably."
    else:
        honest_verdict = "You are currently not qualified for this role based on ATS keyword and skill coverage. Apply after fixing core missing skills."

    suggestions = []
    if missing_skills:
        suggestions.append(f"Add evidence for missing core skills: {', '.join(missing_skills[:5])}.")
    if missing_keywords:
        suggestions.append(f"Include high-impact JD keywords in projects/experience: {', '.join(missing_keywords[:6])}.")
    suggestions.append("Rewrite bullet points with measurable impact (numbers, scale, latency, revenue, users).")
    suggestions.append("Tailor resume summary and skills section to this exact job description before applying.")

    return {
        "ats_score": score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "honest_verdict": honest_verdict,
        "suggestions": suggestions[:5],
        "verdict": verdict,
    }


async def check_ats_match(resume_text, job_description):
    baseline = _fallback_ats_match(resume_text, job_description)
    system = "You are an ATS system. Respond only in JSON."
    user = f"""You are a BRUTAL, NO-NONSENSE ATS system and senior recruiter.
Do NOT sugarcoat. Do NOT be encouraging. Be 100% honest.

If this resume is bad for this job — say it clearly.
If keywords are missing — list ALL of them.
If the candidate is not qualified — say they are not qualified.

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{job_description[:2000]}

Return ONLY this JSON:
{{
  "ats_score": <brutally honest 0-100>,
  "matched_keywords": ["<keyword found in both>"],
  "missing_keywords": ["<keyword in JD not in resume>"],
  "matched_skills": ["<skill the candidate actually has>"],
  "missing_skills": ["<required skill the candidate lacks>"],
  "honest_verdict": "<2 sentences, brutally honest, no sugarcoating>",
  "suggestions": ["<very specific fix, not generic>"],
  "verdict": "<strong match/moderate match/weak match/not qualified>"
  }}"""
    try:
        text = await call_groq([
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ])
        ai = _extract_json(text)
        if not isinstance(ai, dict):
            return baseline

        # Keep the ATS score and keyword coverage honest and deterministic
        merged = dict(baseline)
        honest_verdict = ai.get("honest_verdict")
        suggestions = ai.get("suggestions")

        if isinstance(honest_verdict, str) and honest_verdict.strip():
            merged["honest_verdict"] = honest_verdict.strip()
        if isinstance(suggestions, list) and suggestions:
            merged["suggestions"] = [str(s) for s in suggestions if str(s).strip()][:5]

        return merged
    except Exception as e:
        logger.warning(f"ATS AI fallback activated: {e}")
        return baseline

async def detect_resume_fraud(resume_text, github_data):
    system = "You are a resume fraud detection expert. Respond only in JSON."
    user = f"""Analyze if this resume has fake or exaggerated claims compared to GitHub evidence.

RESUME:
{resume_text[:3000]}

GITHUB FACTS:
- Repos: {github_data.get("public_repos", 0)}
- Stars: {github_data.get("total_stars", 0)}
- Languages: {list(github_data.get("languages", {}).keys())}
- Forked repos (no original work): {github_data.get("forked_repos", 0)}
- Original repos: {github_data.get("original_repos", 0)}

Return ONLY this JSON:
{{
  "authenticity_score": <0-100, 100 = fully authentic>,
  "fraud_risk": "<low/medium/high>",
  "red_flags": ["<specific suspicious claim>"],
  "verified_claims": ["<claim that matches GitHub evidence>"],
  "unverified_claims": ["<claim with no GitHub evidence>"],
  "recommendation": "<honest summary>"
}}"""
    text = await call_groq([
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ])
    return _extract_json(text)

async def generate_portfolio_html(resume_text, github_username, name):
    system = "You are an expert web developer. Generate only clean HTML with embedded CSS."
    user = f"""Create a beautiful dark-themed single-page portfolio website HTML for:

Name: {name}
GitHub: {github_username}
Resume: {resume_text[:2000]}

Requirements:
- Dark background (#0f172a), purple/indigo accents
- Sections: Hero, About, Skills, Projects, Contact
- Fully self-contained single HTML file with embedded CSS
- Professional and modern design
- No external dependencies

Return ONLY the complete HTML code, nothing else."""
    return await call_groq([
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ])


def _safe_list(value) -> list:
    return value if isinstance(value, list) else []


def _profile_hard_cap(github_data: dict) -> int:
    public_repos = _to_int((github_data or {}).get("public_repos"), 0)
    total_stars = _to_int((github_data or {}).get("total_stars"), 0)
    langs = _safe_list(list(((github_data or {}).get("languages") or {}).keys()))

    if public_repos <= 1:
        cap = 28
    elif public_repos <= 3:
        cap = 42
    elif public_repos <= 6:
        cap = 56
    elif public_repos <= 12:
        cap = 70
    else:
        cap = 82

    if total_stars == 0:
        cap -= 5
    if len(langs) <= 1:
        cap -= 4
    elif len(langs) >= 5:
        cap += 3

    return _clamp(cap, 20, 90)


def _normalize_role_shape(role: dict) -> dict:
    role = role if isinstance(role, dict) else {}
    resources = _normalize_resources(role.get("resources"))
    resources = [
        {
            "name": str(r.get("title") or r.get("name") or "Learning Resource"),
            "url": str(r.get("url") or ""),
            "type": str(r.get("type") or "resource"),
        }
        for r in resources
    ]
    if not resources:
        resources = [
            {
                "name": str(r.get("title") or "Learning Resource"),
                "url": str(r.get("url") or ""),
                "type": str(r.get("type") or "resource"),
            }
            for r in _fallback_resources_for_focus(
                str(role.get("category") or "software engineering"),
                _safe_list(role.get("missing_skills")),
            )
        ]
    return {
        "title": str(role.get("title") or "Software Engineer"),
        "category": str(role.get("category") or "Software Engineering"),
        "match_score": _clamp(_to_int(role.get("match_score"), 0)),
        "description": str(role.get("description") or "Role fit based on current public project evidence."),
        "avg_salary": str(role.get("avg_salary") or "$70,000-$120,000"),
        "demand": str(role.get("demand") or "High"),
        "time_to_job": str(role.get("time_to_job") or "6-12 months"),
        "matching_skills": [str(s) for s in _safe_list(role.get("matching_skills"))][:8],
        "missing_skills": [str(s) for s in _safe_list(role.get("missing_skills"))][:10],
        "learning_path": [str(s) for s in _safe_list(role.get("learning_path"))][:6],
        "resources": resources,
        "job_search_tip": str(role.get("job_search_tip") or "Build 2-3 public, role-aligned projects and apply with proof-first portfolio links."),
    }


def _calibrate_recommendation_scores(result: dict, github_data: dict) -> dict:
    data = dict(result or {})
    roles = [_normalize_role_shape(r) for r in _safe_list(data.get("roles"))][:4]
    hard_cap = _profile_hard_cap(github_data)

    for role in roles:
        raw = _clamp(_to_int(role.get("match_score"), 0))
        matching_count = len(_safe_list(role.get("matching_skills")))
        missing_count = len(_safe_list(role.get("missing_skills")))

        bonus = min(7, matching_count * 1.5)
        penalty = min(24, missing_count * 2.2)

        conservative = min(raw, hard_cap) + bonus - penalty
        role["match_score"] = _clamp(conservative, 8, 95)

    roles.sort(key=lambda r: r.get("match_score", 0), reverse=True)
    data["roles"] = roles

    public_repos = _to_int((github_data or {}).get("public_repos"), 0)
    total_stars = _to_int((github_data or {}).get("total_stars"), 0)
    top_languages = _safe_list(list(((github_data or {}).get("languages") or {}).keys()))[:4]

    if hard_cap <= 42:
        evidence_level = "weak"
        brutal_truth = (
            "Your GitHub evidence is currently too thin for competitive hiring. "
            "Most applications will be filtered unless you ship stronger, role-specific projects."
        )
    elif hard_cap <= 60:
        evidence_level = "moderate"
        brutal_truth = (
            "You have a base to build on, but profile depth is still below interview-ready for most roles. "
            "You need higher-quality, end-to-end projects with measurable impact."
        )
    else:
        evidence_level = "strong"
        brutal_truth = (
            "Your GitHub profile has credible signals, but role fit still depends on closing missing core skills. "
            "Treat the scores as conservative, not guaranteed interview outcomes."
        )

    data["github_profile_assessment"] = {
        "evidence_level": evidence_level,
        "public_repos": public_repos,
        "total_stars": total_stars,
        "top_languages": top_languages,
        "score_cap_applied": hard_cap,
    }
    data["brutal_truth"] = str(data.get("brutal_truth") or brutal_truth)
    data["summary"] = str(data.get("summary") or "Recommendations are based on your real GitHub evidence, scored conservatively.")
    return data


def _fallback_career_recommendations(github_data: dict, interests: list[str], desired_role: str) -> dict:
    langs = [str(x).lower() for x in _safe_list(list((github_data.get("languages") or {}).keys()))]
    interests_lower = [str(i).lower() for i in _safe_list(interests)]
    public_repos = _to_int(github_data.get("public_repos"), 0)

    catalog = [
        {
            "title": "Backend Engineer",
            "category": "Software Engineering",
            "signals": ["python", "go", "java", "fastapi", "node.js", "sql"],
            "missing": ["System Design", "Testing", "APIs at scale", "Caching"],
            "avg_salary": "$95,000-$165,000",
            "time_to_job": "6-12 months",
        },
        {
            "title": "Frontend Engineer",
            "category": "Web Development",
            "signals": ["javascript", "typescript", "react", "vue", "html", "css"],
            "missing": ["Accessibility", "Performance Optimization", "Testing", "State Management"],
            "avg_salary": "$90,000-$155,000",
            "time_to_job": "5-10 months",
        },
        {
            "title": "Data Analyst",
            "category": "Data",
            "signals": ["python", "sql", "pandas", "numpy"],
            "missing": ["Dashboards", "Business Metrics", "Experiment Design", "Stakeholder Communication"],
            "avg_salary": "$75,000-$125,000",
            "time_to_job": "4-9 months",
        },
        {
            "title": "Machine Learning Engineer",
            "category": "Artificial Intelligence",
            "signals": ["python", "tensorflow", "pytorch", "machine learning"],
            "missing": ["Model Deployment", "MLOps", "Statistics", "Feature Engineering"],
            "avg_salary": "$110,000-$185,000",
            "time_to_job": "8-14 months",
        },
    ]

    roles = []
    cap = _profile_hard_cap(github_data)
    for item in catalog:
        overlap = sum(1 for s in item["signals"] if any(s in lang for lang in langs) or any(s in it for it in interests_lower))
        base = 18 + overlap * 12
        if desired_role and desired_role.lower() in item["title"].lower():
            base += 10
        if public_repos < 3:
            base -= 8

        score = _clamp(min(base, cap), 10, 92)
        roles.append({
            "title": item["title"],
            "category": item["category"],
            "match_score": score,
            "description": "Fit estimate is based on evidence in your public GitHub profile, not claimed skills.",
            "avg_salary": item["avg_salary"],
            "demand": "High",
            "time_to_job": item["time_to_job"],
            "matching_skills": item["signals"][: min(overlap, len(item["signals"]))] or ["Basic coding"],
            "missing_skills": item["missing"],
            "learning_path": [
                "Build one role-focused project with clear README and architecture notes",
                "Add automated tests and deployment proof",
                "Publish measurable results and technical decisions",
            ],
            "resources": _fallback_resources_for_focus(item["category"], item["missing"]),
            "job_search_tip": "Apply after shipping at least 2 public projects relevant to this role with visible commits.",
        })

    roles.sort(key=lambda r: r["match_score"], reverse=True)
    return _calibrate_recommendation_scores({
        "summary": "This fallback recommendation is generated conservatively from your GitHub evidence only.",
        "brutal_truth": "If your public projects are shallow, your hiring odds are shallow. Build proof first.",
        "roles": roles[:4],
    }, github_data)


async def get_career_recommendations(
    skills,
    experience,
    interests,
    github_data: dict | None = None,
    desired_role: str = "",
):
    github_data = github_data or {}
    top_languages = list((github_data.get("languages") or {}).keys())[:8]
    repos = _safe_list(github_data.get("repos"))[:8]
    repo_lines = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        name = str(repo.get("name") or "repo")
        lang = str(repo.get("language") or "unknown")
        stars = _to_int(repo.get("stars"), 0)
        desc = str(repo.get("description") or "").strip()
        snippet = f"{name} | {lang} | {stars} stars"
        if desc:
            snippet += f" | {desc[:90]}"
        repo_lines.append(snippet)

    system = (
        "You are a brutally honest tech recruiter and engineering manager. "
        "You must evaluate role fit using evidence from GitHub only. "
        "Never inflate scores and never assume unproven skills. "
        "If the profile is weak, say it directly."
    )
    user = (
        "Generate top 4 career recommendations using the user's GitHub profile as primary evidence.\n\n"
        f"GITHUB USERNAME: {github_data.get('username', 'unknown')}\n"
        f"GITHUB METRICS: repos={github_data.get('public_repos', 0)}, stars={github_data.get('total_stars', 0)}, "
        f"followers={github_data.get('followers', 0)}, top_languages={', '.join(top_languages) if top_languages else 'none'}\n"
        f"GITHUB REPOS (sample): {'; '.join(repo_lines) if repo_lines else 'none'}\n\n"
        f"OPTIONAL SELF-REPORTED CONTEXT (less trusted than GitHub): skills={', '.join(skills or [])}, "
        f"experience={experience or 'not provided'}, interests={', '.join(interests or [])}, "
        f"desired_role={desired_role or 'not provided'}\n\n"
        "Scoring policy:\n"
        "- Be conservative and evidence-based.\n"
        "- If GitHub is weak, highest role score should usually be <=45.\n"
        "- Do not give high scores for 'potential'.\n"
        "- Mention critical gaps explicitly.\n\n"
        "Return ONLY this JSON:\n"
        "{\n"
        '  "summary": "<2 sentence summary>",\n'
        '  "brutal_truth": "<direct, no-sugarcoating assessment>",\n'
        '  "roles": [\n'
        "    {\n"
        '      "title": "<role name>",\n'
        '      "category": "<e.g. Web Development>",\n'
        '      "match_score": <0-100>,\n'
        '      "description": "<evidence-based reason>",\n'
        '      "avg_salary": "<e.g. $70,000-$110,000>",\n'
        '      "demand": "<Very High/High/Medium>",\n'
        '      "time_to_job": "<e.g. 3-6 months>",\n'
        '      "matching_skills": ["<shown by GitHub evidence>"],\n'
        '      "missing_skills": ["<critical missing skill>"],\n'
        '      "learning_path": ["<step 1>", "<step 2>", "<step 3>"],\n'
        '      "resources": [{"name":"<n>","url":"<https://...>","type":"<Course/YouTube/Website>"}],\n'
        '      "job_search_tip": "<practical action>"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    try:
        text = await call_groq(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        parsed = _extract_json(text)
        return _calibrate_recommendation_scores(parsed, github_data)
    except Exception as e:
        logger.warning(f"Career recommendation fallback activated: {e}")
        return _fallback_career_recommendations(github_data, interests or [], desired_role or "")