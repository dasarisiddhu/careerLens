# ============================================================
# CareerLens – Resume Analysis Router
# File: backend/routers/resume.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from middleware.auth import get_authenticated_user, get_user_profile
from services.pdf_service import extract_text_from_pdf, extract_text_from_pdf_base64
from services.github_service import fetch_github_profile
from services.gemini_service import (
    call_groq,
    _extract_json,
    _ensure_learning_resources,
    _calibrate_resume_scores,
    _fallback_ats_match,
)
from database import supabase
from config import settings
import uuid, logging, base64, re
from urllib.parse import urlparse

logger = logging.getLogger("careerlens.resume")
router = APIRouter()


def validate_url(url: str, platform: str):
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail=f"{platform} URL must start with https://")


def normalize_github_url(url: str) -> str:
    """
    Canonicalize to https://github.com/<username-or-org>
    so repeated analyses don't fail on trivial URL variants.
    """
    raw = (url or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="GitHub URL is required.")

    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    if host == "www.github.com":
        host = "github.com"
    if host != "github.com":
        raise HTTPException(status_code=400, detail="GitHub URL must be a github.com profile URL.")

    path_parts = [p for p in (parsed.path or "").split("/") if p]
    if not path_parts:
        raise HTTPException(status_code=400, detail="GitHub URL must include a username.")

    username = path_parts[0]
    return f"https://github.com/{username}"


def is_resume_analysis_duplicate_error(err: Exception) -> bool:
    msg = str(err).lower()
    return "unique_github_linkedin_per_user" in msg or ("duplicate key value" in msg and "resume_analyses" in msg)


BRUTAL_RESUME_SYSTEM_PREFIX = (
    "You are a brutally honest senior recruiter. You do NOT \n"
    "inflate scores. You score based on market reality:\n"
    "- 80-100: Only for candidates with 2+ years real experience,\n"
    "  strong GitHub (10+ repos, 50+ stars), proven projects\n"
    "- 60-79: Solid junior candidate, some real projects, \n"
    "  good skills coverage\n"
    "- 40-59: Student or fresher with decent foundations\n"
    "- 20-39: Missing critical skills or projects\n"
    "- 0-19: Not ready for the job market yet\n\n"
    "Penalize heavily for:\n"
    "- Fewer than 5 GitHub repos: -15 points\n"
    "- No quantified achievements: -10 points  \n"
    "- Generic bullet points: -10 points\n"
    "- No internship or real work experience: -10 points\n"
    "- Mismatch between claimed skills and projects: -15 points\n\n"
    "Never give more than 65 to a fresher with no work experience.\n"
    "Never give more than 45 if GitHub has fewer than 3 repos."
)

BRUTAL_ATS_SYSTEM_PREFIX = (
    "Be brutally honest about ATS compatibility. Most resumes \n"
    "fail ATS before a human sees them. Score conservatively:\n"
    "- 80+: Excellent keyword match, will pass most ATS systems\n"
    "- 60-79: Decent match but missing important keywords\n"
    "- 40-59: Will likely be filtered out by strict ATS\n"
    "- Below 40: Almost certainly filtered — needs major work\n"
    "Do not inflate scores to make users feel better."
)

COMMON_TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node", "node.js", "next.js",
    "vue", "angular", "sql", "postgresql", "mysql", "mongodb", "redis", "aws", "azure",
    "gcp", "docker", "kubernetes", "terraform", "git", "github", "rest", "api", "fastapi",
    "django", "flask", "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "graphql", "microservices", "ci/cd",
]


def _to_int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _resume_has_quantified_achievements(text: str) -> bool:
    return bool(re.search(r"(\d+%|\d+\+|\$\d+|\d+\s*(users|customers|clients|requests|ms|sec|hours|days|months|years|stars|repos))", text or "", re.I))


def _resume_has_work_experience(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(keyword in lowered for keyword in [
        "intern", "internship", "work experience", "professional experience",
        "software engineer", "developer at", "engineer at", "analyst at",
        "experience", "employment", "freelance", "consultant",
    ])


def _resume_has_generic_bullets(text: str) -> bool:
    generic_phrases = [
        "worked on", "helped", "assisted", "responsible for",
        "involved in", "participated in", "supported",
    ]
    lowered = str(text or "").lower()
    hits = sum(lowered.count(phrase) for phrase in generic_phrases)
    return hits >= 2


def _resume_has_skill_mismatch(text: str, github_data: dict) -> bool:
    lowered = str(text or "").lower()
    claimed = {skill for skill in COMMON_TECH_SKILLS if skill in lowered}
    if len(claimed) < 6:
        return False

    evidence_parts = []
    evidence_parts.extend((github_data.get("languages") or {}).keys())
    for repo in github_data.get("repos") or []:
        evidence_parts.append(repo.get("name", ""))
        evidence_parts.append(repo.get("description", ""))
    evidence = " ".join(str(part or "") for part in evidence_parts).lower()
    overlap = sum(1 for skill in claimed if skill in evidence)

    return overlap <= max(1, len(claimed) // 5)


def _apply_brutal_resume_scoring(result: dict, resume_text: str, github_data: dict) -> dict:
    adjusted = dict(result or {})
    score = _to_int(adjusted.get("score"), 0)

    public_repos = _to_int(github_data.get("public_repos"), len(github_data.get("repos") or []))
    total_stars = _to_int(github_data.get("total_stars"), 0)
    has_work_experience = _resume_has_work_experience(resume_text)

    if public_repos < 5:
        score -= 15
    if not _resume_has_quantified_achievements(resume_text):
        score -= 10
    if _resume_has_generic_bullets(resume_text):
        score -= 10
    if not has_work_experience:
        score -= 10
    if _resume_has_skill_mismatch(resume_text, github_data):
        score -= 15

    if not has_work_experience:
        score = min(score, 65)
    if public_repos < 3:
        score = min(score, 45)
    if public_repos >= 10 and total_stars >= 50 and has_work_experience:
        score = max(score, min(100, _to_int(adjusted.get("score"), 0)))

    score = max(0, min(100, score))
    adjusted["score"] = score
    adjusted["grade"] = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"
    adjusted["job_readiness"] = "ready" if score >= 80 else "almost ready" if score >= 60 else "needs work"
    adjusted["scoring_note"] = (
        "Scores are brutally calibrated to market reality. "
        "Weak GitHub proof, generic bullets, missing metrics, and lack of real experience are penalized."
    )
    return adjusted


def _apply_brutal_ats_scoring(result: dict) -> dict:
    adjusted = dict(result or {})
    score = _to_int(adjusted.get("ats_score"), 0)
    matched_keywords = adjusted.get("matched_keywords") or []
    missing_keywords = adjusted.get("missing_keywords") or []
    missing_skills = adjusted.get("missing_skills") or []

    coverage = len(matched_keywords) / max(1, len(matched_keywords) + len(missing_keywords))

    if coverage < 0.3 or len(missing_skills) >= 5:
        score = min(score, 39)
    elif coverage < 0.55 or len(missing_keywords) >= 10:
        score = min(score, 59)
    elif coverage < 0.75 or len(missing_keywords) >= 5:
        score = min(score, 79)

    adjusted["ats_score"] = max(0, min(99, score))
    return adjusted


async def run_brutal_resume_analysis(resume_text: str, github_data: dict, job_role: str) -> dict:
    system = (
        BRUTAL_RESUME_SYSTEM_PREFIX
        + "\n\n"
        + "You are an expert career coach and ATS specialist. "
        + "Score strictly and avoid inflated optimism. "
        + "Always respond with valid JSON only, no extra text."
    )
    user = f"""Analyze this resume and return ONLY a valid JSON object.

RESUME: {resume_text[:4000]}
GITHUB: Username={github_data.get("username","N/A")}, Repos={github_data.get("public_repos",0)}, OriginalRepos={github_data.get("original_repos",0)}, Forks={github_data.get("forked_repos",0)}, Readmes={github_data.get("repos_with_readme",0)}/{github_data.get("readme_checked_repos",0)}, Deployed={github_data.get("deployed_repos",0)}, Active30d={github_data.get("recent_active_repos_30d",0)}, Active180d={github_data.get("recent_active_repos",0)}, LastActivity={github_data.get("last_activity_at","unknown")}, Languages={", ".join(list(github_data.get("languages",{}).keys())[:6])}, Stars={github_data.get("total_stars",0)}, Projects={", ".join([r["name"] for r in github_data.get("repos",[])[:4]])}
Target Role: {job_role}

Return this exact JSON:
{{
  "score": <0-100>, "grade": "<A/B/C/D/F>",
  "summary": "<2-3 sentence blunt assessment>",
  "strengths": ["<s1>","<s2>","<s3>"],
  "weaknesses": ["<problem 1>","<problem 2>","<problem 3>"],
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
  "github_analysis": {{"profile_strength":"<strong/moderate/weak>","verdict":"<1 blunt sentence>","highlights":["<h>"],"problems":["<p1>","<p2>"],"improvements":["<i>"]}},
  "top_keywords_missing": ["<k1>","<k2>"],
  "estimated_salary_range": "<e.g. $80,000-$110,000>",
  "job_readiness": "<ready/almost ready/needs work>"
}}

Rules:
- For each learning_roadmap week, include 2-3 real learning resources with working https URLs.
- Prioritize official docs or highly trusted learning providers.
- Keep resources specific to the missing skills and target role.
- Be brutally honest: do not inflate score just for potential.
- Treat missing sections, weak action verbs, lack of quantified achievements, and keyword gaps as explicit problems.
- Put those problems in weaknesses and missing_skills bluntly, not as polite suggestions.
- In github_analysis, explicitly judge original repos vs forks, README coverage, deployed projects, activity frequency, recency, and code quality signals from real repo evidence.
- If the GitHub is weak, say so directly in github_analysis.verdict with concrete evidence.
- If there are critical role gaps, keep score conservative (typically 35-60)."""
    text = await call_groq([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    parsed = _ensure_learning_resources(_extract_json(text))
    calibrated = _calibrate_resume_scores(parsed, resume_text=resume_text, github_data=github_data or {}, job_role=job_role)
    return _apply_brutal_resume_scoring(calibrated, resume_text, github_data or {})


async def run_brutal_ats_check(resume_text: str, job_description: str) -> dict:
    baseline = _fallback_ats_match(resume_text, job_description)
    system = f"{BRUTAL_ATS_SYSTEM_PREFIX}\n\nYou are an ATS system. Respond only in JSON."
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
            {"role": "user", "content": user},
        ])
        ai = _extract_json(text)
        if not isinstance(ai, dict):
            return _apply_brutal_ats_scoring(baseline)

        merged = dict(baseline)
        honest_verdict = ai.get("honest_verdict")
        suggestions = ai.get("suggestions")

        if isinstance(honest_verdict, str) and honest_verdict.strip():
            merged["honest_verdict"] = honest_verdict.strip()
        if isinstance(suggestions, list) and suggestions:
            merged["suggestions"] = [str(s) for s in suggestions if str(s).strip()][:5]

        return _apply_brutal_ats_scoring(merged)
    except Exception as e:
        logger.warning(f"ATS AI fallback activated: {e}")
        return _apply_brutal_ats_scoring(baseline)


@router.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    github_url: str = Form(...),
    job_role: str = Form(...),
    profile=Depends(get_user_profile),
    user=Depends(get_authenticated_user),
):
    """
    Full AI resume analysis pipeline.
    1. Validate inputs & freemium limits
    2. Extract PDF text
    3. Fetch GitHub data
    4. Send to AI
    5. Store & return results
    """
    user_id = profile.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user profile. Please sign in again.")

    # ---- Freemium gate ----
    plan_type = profile.get("plan_type", "freemium")
    resume_analysis_count = int(profile.get("resume_analysis_count") or 0)
    if plan_type == "freemium" and resume_analysis_count >= settings.FREEMIUM_MAX_ANALYSES:
        raise HTTPException(status_code=403, detail="Freemium limit reached. Upgrade to Premium for unlimited analyses.")

    # ---- Validate URLs ----
    validate_url(github_url, "GitHub")
    github_url = normalize_github_url(github_url)

    linked_github_username = (user.get("github_username") or "").strip()
    linked_github_url = f"https://github.com/{linked_github_username}" if linked_github_username else None
    if linked_github_url and github_url != linked_github_url:
        raise HTTPException(
            status_code=400,
            detail=f"Your linked GitHub account is {linked_github_url}. Use that profile for analysis.",
        )

    saved_github_url = profile.get("github_url")
    normalized_saved_github_url = None
    if saved_github_url:
        try:
            normalized_saved_github_url = normalize_github_url(saved_github_url)
        except HTTPException:
            # Gracefully recover from legacy/invalid saved values.
            logger.warning(f"Invalid saved github_url for user {user_id}; replacing with new value.")

    # If GitHub OAuth is linked, trust that identity and auto-heal legacy mismatches.
    if linked_github_url and normalized_saved_github_url and linked_github_url != normalized_saved_github_url:
        normalized_saved_github_url = linked_github_url
        supabase.table("users").update({"github_url": linked_github_url}).eq("user_id", user_id).execute()

    # ---- Enforce one GitHub profile per user; allow unlimited re-runs with the same profile ----
    if normalized_saved_github_url and github_url != normalized_saved_github_url:
        raise HTTPException(
            status_code=400,
            detail=f"Your account is linked to {normalized_saved_github_url}. Use that GitHub profile for resume analysis.",
        )
    if not normalized_saved_github_url:
        supabase.table("users").update({"github_url": github_url}).eq("user_id", user_id).execute()

    # ---- Backward-compatible placeholder for DB schemas that require linkedin_url ----
    linkedin_url = ""

    # ---- Create analysis run ----
    analysis_id = str(uuid.uuid4())
    processing_record_created = False

    try:
        # ---- Validate file ----
        if resume.content_type not in settings.ALLOWED_RESUME_TYPES:
            raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
        content = await resume.read()
        if len(content) > settings.MAX_RESUME_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Resume must be under {settings.MAX_RESUME_SIZE_MB}MB.")

        # ---- Create DB record (pending) ----
        try:
            supabase.table("resume_analyses").insert({
                "id": analysis_id,
                "user_id": user_id,
                "github_url": github_url,
                "linkedin_url": linkedin_url,
                "job_role": job_role,
                "status": "processing",
            }).execute()
            processing_record_created = True
        except Exception as insert_err:
            # Backward compatibility: if old DB unique constraint still exists,
            # reuse the latest row for the same GitHub profile instead of failing.
            if not is_resume_analysis_duplicate_error(insert_err):
                raise

            existing = (
                supabase.table("resume_analyses")
                .select("id")
                .eq("user_id", user_id)
                .eq("github_url", github_url)
                .eq("linkedin_url", linkedin_url)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if not existing.data:
                raise

            analysis_id = existing.data[0]["id"]
            supabase.table("resume_analyses").update({
                "job_role": job_role,
                "status": "processing",
                "score": None,
                "results_json": None,
            }).eq("id", analysis_id).execute()
            processing_record_created = True

        # ---- Extract PDF text ----
        resume_text = extract_text_from_pdf(base64.b64encode(content).decode('utf-8'))

        # ---- Fetch GitHub data ----
        github_username = github_url.rstrip("/").split("/")[-1]
        github_data = await fetch_github_profile(github_username)

        # ---- Call Gemini AI ----
        result = await run_brutal_resume_analysis(
            resume_text=resume_text,
            github_data=github_data,
            job_role=job_role,
        )

        # Save to progress history
        try:
            from datetime import datetime, timezone

            version_number = 1
            latest_version = (
                supabase.table("resume_versions")
                .select("version_number")
                .eq("user_id", user_id)
                .order("version_number", desc=True)
                .limit(1)
                .execute()
            )
            if latest_version.data:
                version_number = int(latest_version.data[0].get("version_number") or 0) + 1

            supabase.table("resume_versions").insert({
                "user_id": user_id,
                "version_number": version_number,
                "resume_score": result.get("score"),
                "ats_score": result.get("ats_score"),
                "job_role": job_role,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            logger.warning(f"Could not save progress: {e}")

        # ---- Update DB with results ----
        supabase.table("resume_analyses").update({
            "score": result.get("score", 0),
            "results_json": result,
            "status": "done",
        }).eq("id", analysis_id).execute()

        # ---- Increment usage counter ----
        supabase.rpc("increment_resume_count", {"p_user_id": user_id}).execute()

        return {"success": True, "analysis_id": analysis_id, "result": result}
    
    except HTTPException:
        raise
    except Exception as e:
        if processing_record_created:
            try:
                supabase.table("resume_analyses").update({"status": "failed"}).eq("id", analysis_id).execute()
            except Exception as update_err:
                logger.warning(f"Could not mark analysis as failed for {analysis_id}: {update_err}")
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/history")
async def get_history(user=Depends(get_authenticated_user)):
    """Return all past analyses for the current user."""
    result = supabase.table("resume_analyses").select("*").eq("user_id", user["user_id"]).order("created_at", desc=True).execute()
    return {"success": True, "analyses": result.data}


@router.get("/progress")
async def get_progress(user=Depends(get_authenticated_user)):
    try:
        result = (
            supabase.table("resume_versions")
            .select("*")
            .eq("user_id", user["user_id"])
            .order("created_at", desc=False)
            .execute()
        )
        return {"success": True, "history": result.data}
    except Exception as e:
        # Progress history is optional; degrade gracefully when table/migration is missing.
        logger.warning(f"Could not fetch progress history for user {user['user_id']}: {e}")
        return {"success": True, "history": []}


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str, user=Depends(get_authenticated_user)):
    """Return a single analysis result."""
    result = (
        supabase.table("resume_analyses")
        .select("*")
        .eq("id", analysis_id)
        .eq("user_id", user["user_id"])
        .limit(1)
        .execute()
    )
    row = result.data[0] if result.data else None
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"success": True, "analysis": row}

class ExtractTextRequest(BaseModel):
    pdf_base64: str

@router.post("/extract-text")
async def extract_resume_text(
    body: ExtractTextRequest,
    user=Depends(get_authenticated_user)
):
    try:
        if not body.pdf_base64 or not body.pdf_base64.strip():
            raise HTTPException(status_code=400, detail="No PDF data provided.")
        
        from services.pdf_service import extract_text_from_pdf_base64
        text = extract_text_from_pdf_base64(body.pdf_base64)
        
        if not text or len(text.strip()) < 20:
            raise HTTPException(
                status_code=422,
                detail="PDF text is empty. Please paste your resume text manually."
            )
        
        # Log success for debugging
        import logging
        logging.getLogger("careerlens").info(
            f"PDF extraction success: {len(text)} chars extracted"
        )
        
        return {"success": True, "text": text.strip(), "char_count": len(text.strip())}
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger("careerlens").error(f"PDF extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}. Please paste your resume text manually."
        )

class ATSCheckRequest(BaseModel):
    resume_pdf: str
    job_description: str


@router.post("/ats-check")
async def ats_check(body: ATSCheckRequest, user=Depends(get_authenticated_user)):
    if not body.resume_pdf or not body.job_description.strip():
        raise HTTPException(status_code=400, detail="Resume PDF and job description are required.")

    pdf_base64 = body.resume_pdf
    if "," in pdf_base64:
        pdf_base64 = pdf_base64.split(",", 1)[1]

    try:
        resume_text = extract_text_from_pdf_base64(pdf_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await run_brutal_ats_check(resume_text, body.job_description)
    return {"success": True, "result": result}
