# ============================================================
# CareerLens – Interview Probability Engine
# File: backend/routers/interview_probability.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from middleware.auth import get_authenticated_user, get_user_profile
from database import supabase
from services.gemini_service import call_groq, _extract_json
from services.github_service import get_github_data
import logging, re
from urllib.parse import urlparse

logger = logging.getLogger("careerlens.interview_probability")
router = APIRouter()


# ============================================================
# Models
# ============================================================

class ProbabilityRequest(BaseModel):
    resume_text: str
    github_url: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    job_description: str


def normalize_github_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="GitHub URL cannot be empty.")

    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    if host == "www.github.com":
        host = "github.com"
    if host != "github.com":
        raise HTTPException(status_code=400, detail="GitHub URL must be a github.com profile URL.")

    path_parts = [p for p in (parsed.path or "").split("/") if p]
    if not path_parts:
        raise HTTPException(status_code=400, detail="GitHub URL must include a username.")
    return f"https://github.com/{path_parts[0]}"


# ============================================================
# Scoring Helpers
# ============================================================

KNOWN_SKILLS = [
    "python","javascript","typescript","java","c++","c#","go","rust","php","ruby","swift","kotlin",
    "react","vue","angular","next.js","node.js","express","django","fastapi","flask","spring",
    "sql","postgresql","mysql","mongodb","redis","elasticsearch","firebase","supabase",
    "aws","gcp","azure","docker","kubernetes","terraform","ci/cd","github actions","jenkins",
    "machine learning","deep learning","tensorflow","pytorch","pandas","numpy","scikit-learn","nlp",
    "rest api","graphql","microservices","system design","linux","git","html","css","tailwind",
    "figma","agile","scrum","devops","data structures","algorithms","opencv","langchain"
]

def extract_skills_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    return list(set(s for s in KNOWN_SKILLS if s in text_lower))

def compute_skill_match(resume_skills, jd_skills) -> float:
    if not jd_skills:
        return 40.0
    overlap = len(set(s.lower() for s in resume_skills) & set(s.lower() for s in jd_skills))
    return round((overlap / len(jd_skills)) * 100, 1)

def compute_ats_score(resume_text: str, jd_text: str) -> float:
    words = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.]*\b', jd_text.lower()))
    stopwords = {"the","and","for","with","that","this","will","have","from","you","are","your","our","they","can","has"}
    keywords = [w for w in words if len(w) > 3 and w not in stopwords]
    if not keywords:
        return 40.0
    resume_lower = resume_text.lower()
    matches = sum(1 for k in keywords if k in resume_lower)
    return round((matches / len(keywords)) * 100, 1)

def compute_portfolio_score(github_data: dict) -> float:
    if not github_data:
        return 15.0
    score = 0
    repos     = github_data.get("public_repos", 0)
    stars     = github_data.get("total_stars", 0)
    followers = github_data.get("followers", 0)
    langs     = len(github_data.get("languages", []))

    if repos >= 20:   score += 30
    elif repos >= 10: score += 22
    elif repos >= 5:  score += 12
    elif repos >= 2:  score += 5

    if stars >= 50:   score += 25
    elif stars >= 20: score += 17
    elif stars >= 5:  score += 9
    else:             score += 1

    if followers >= 50:   score += 20
    elif followers >= 20: score += 13
    elif followers >= 5:  score += 7
    else:                 score += 1

    if langs >= 5:   score += 25
    elif langs >= 3: score += 16
    elif langs >= 1: score += 7

    return min(float(score), 100.0)

def compute_experience_score(resume_text: str) -> float:
    years = re.findall(r'(\d+)\+?\s*years?', resume_text.lower())
    total = sum(int(y) for y in years) if years else 0
    if total >= 5:  return 95.0
    if total >= 3:  return 75.0
    if total >= 1:  return 45.0
    if "intern" in resume_text.lower():   return 28.0
    if "fresher" in resume_text.lower():  return 18.0
    return 12.0

def compute_final_probability(skill_match, portfolio_score, ats_score, experience_score) -> int:
    raw = (
        0.40 * skill_match +
        0.20 * portfolio_score +
        0.20 * ats_score +
        0.20 * experience_score
    )
    return max(4, min(87, int(raw)))


def _extract_top_languages(github_data: dict, limit: int = 6) -> list[str]:
    raw_languages = github_data.get("languages", [])
    if isinstance(raw_languages, dict):
        return [str(k) for k in list(raw_languages.keys())[:limit] if k]
    if isinstance(raw_languages, list):
        return [str(v) for v in raw_languages[:limit] if v]
    return []


# ============================================================
# AI Brutal Analysis
# ============================================================

async def get_ai_analysis(resume_text, github_data, job_description, missing_skills, probability) -> dict:
    system = (
        "You are a brutally honest senior tech recruiter with 15 years experience at FAANG. "
        "You do NOT sugarcoat. You give real feedback that helps candidates actually improve. "
        "Be specific, direct, and harsh when needed. No feel-good fluff. Respond ONLY in valid JSON."
    )
    tone = (
        "Be VERY harsh and direct. This candidate is NOT ready and needs to hear it."
        if probability < 35 else
        "Be honest and direct. This candidate has potential but serious gaps to address."
        if probability < 55 else
        "Be constructive but specific. Candidate is competitive but needs polish to land the role."
    )
    top_languages = _extract_top_languages(github_data, limit=6)
    github_summary = (
        f"GitHub: {github_data.get('public_repos',0)} repos, "
        f"{github_data.get('total_stars',0)} stars, "
        f"languages: {', '.join(top_languages) if top_languages else 'none detected'}"
        if github_data else "GitHub: Not provided or empty profile — major red flag for tech roles"
    )
    user_msg = (
        f"Candidate has a {probability}% interview probability for this role.\n\n"
        f"Resume:\n{resume_text[:1800]}\n\n"
        f"{github_summary}\n\n"
        f"Job Description:\n{job_description[:1500]}\n\n"
        f"Missing skills detected: {', '.join(missing_skills[:10])}\n\n"
        f"{tone}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "verdict": "<One brutally honest sentence about their real chances>",\n'
        '  "biggest_weakness": "<Single most critical thing holding them back>",\n'
        '  "missing_skills": ["skill1", "skill2", "skill3", "skill4"],\n'
        '  "recommended_projects": [\n'
        '    {"title": "project name", "why": "specific reason", "estimated_time": "realistic time"}\n'
        '  ],\n'
        '  "resume_improvements": ["specific improvement 1", "specific improvement 2", "specific improvement 3"],\n'
        '  "interview_prep_tips": ["specific tip 1", "specific tip 2", "specific tip 3"],\n'
        '  "realistic_timeline": "honest estimate e.g. 4-6 months of focused work",\n'
        '  "green_flags": ["genuine strength 1", "genuine strength 2"]\n'
        "}"
    )
    try:
        text = await call_groq([
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg}
        ])
        return _extract_json(text)
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return {
            "verdict": "AI analysis unavailable. Your scores above are still accurate.",
            "biggest_weakness": "Could not determine — check your API key.",
            "missing_skills": missing_skills[:5],
            "recommended_projects": [{"title": "Build a full-stack project", "why": "Shows end-to-end ability", "estimated_time": "3-4 weeks"}],
            "resume_improvements": ["Add quantified achievements", "Fix keyword coverage for ATS", "Add GitHub links"],
            "interview_prep_tips": ["Practice LeetCode Medium problems", "Review system design basics", "Prepare STAR method answers"],
            "realistic_timeline": "3-6 months",
            "green_flags": []
        }


# ============================================================
# Main Endpoint
# ============================================================

@router.post("/")
async def predict_interview_probability(
    body: ProbabilityRequest,
    profile=Depends(get_user_profile),
    user=Depends(get_authenticated_user),
):
    if not body.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required.")
    if not body.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")
    try:
        requested_github_url = (body.github_url or "").strip()
        normalized_requested_github_url = normalize_github_url(requested_github_url) if requested_github_url else None

        linked_github_username = (user.get("github_username") or "").strip()
        linked_github_url = f"https://github.com/{linked_github_username}" if linked_github_username else None

        saved_github_url = (profile.get("github_url") or "").strip()
        normalized_saved_github_url = None
        if saved_github_url:
            try:
                normalized_saved_github_url = normalize_github_url(saved_github_url)
            except HTTPException:
                normalized_saved_github_url = None

        # If GitHub OAuth is linked, trust that identity and auto-heal legacy mismatches.
        if linked_github_url and normalized_saved_github_url and linked_github_url != normalized_saved_github_url:
            normalized_saved_github_url = linked_github_url
            try:
                supabase.table("users").update({"github_url": linked_github_url}).eq("user_id", user["user_id"]).execute()
            except Exception as e:
                logger.warning(f"Could not auto-sync github_url for user {user['user_id']}: {e}")

        if linked_github_url and normalized_requested_github_url and normalized_requested_github_url != linked_github_url:
            raise HTTPException(
                status_code=400,
                detail=f"Your linked GitHub account is {linked_github_url}. Use that profile URL.",
            )

        if (
            normalized_saved_github_url
            and normalized_requested_github_url
            and normalized_requested_github_url != normalized_saved_github_url
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Your account is linked to {normalized_saved_github_url}. Use that GitHub profile.",
            )

        effective_github_url = (
            normalized_requested_github_url
            or normalized_saved_github_url
            or linked_github_url
            or ""
        )

        if not normalized_saved_github_url and effective_github_url:
            try:
                supabase.table("users").update({"github_url": effective_github_url}).eq("user_id", user["user_id"]).execute()
            except Exception as e:
                logger.warning(f"Could not persist github_url for user {user['user_id']}: {e}")

        resume_skills  = extract_skills_from_text(body.resume_text)
        jd_skills      = extract_skills_from_text(body.job_description)
        missing_skills = [s for s in jd_skills if s not in resume_skills]

        github_data = {}
        if effective_github_url:
            username = effective_github_url.rstrip("/").split("/")[-1]
            try:
                github_data = await get_github_data(username)
            except Exception:
                github_data = {}

        skill_match      = compute_skill_match(resume_skills, jd_skills)
        ats_score        = compute_ats_score(body.resume_text, body.job_description)
        portfolio_score  = compute_portfolio_score(github_data)
        experience_score = compute_experience_score(body.resume_text)
        probability      = compute_final_probability(skill_match, portfolio_score, ats_score, experience_score)

        ai = await get_ai_analysis(body.resume_text, github_data, body.job_description, missing_skills, probability)

        try:
            supabase.table("interview_predictions").insert({
                "user_id":               user["user_id"],
                "job_description":       body.job_description[:500],
                "interview_probability": probability,
                "skill_match":           skill_match,
                "ats_score":             ats_score,
                "portfolio_score":       portfolio_score,
                "recommendations_json":  ai,
            }).execute()
        except Exception as e:
            logger.warning(f"DB save failed: {e}")

        return {
            "success":               True,
            "interview_probability": probability,
            "skill_match":           skill_match,
            "ats_score":             ats_score,
            "portfolio_score":       portfolio_score,
            "experience_score":      experience_score,
            "missing_skills":        ai.get("missing_skills", missing_skills),
            "verdict":               ai.get("verdict", ""),
            "biggest_weakness":      ai.get("biggest_weakness", ""),
            "recommended_projects":  ai.get("recommended_projects", []),
            "resume_improvements":   ai.get("resume_improvements", []),
            "interview_prep_tips":   ai.get("interview_prep_tips", []),
            "realistic_timeline":    ai.get("realistic_timeline", ""),
            "green_flags":           ai.get("green_flags", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# History
# ============================================================

@router.get("/history")
async def get_prediction_history(user=Depends(get_authenticated_user)):
    result = supabase.table("interview_predictions") \
        .select("id,job_description,interview_probability,skill_match,ats_score,portfolio_score,created_at") \
        .eq("user_id", user["user_id"]) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()
    return {"success": True, "history": result.data}
