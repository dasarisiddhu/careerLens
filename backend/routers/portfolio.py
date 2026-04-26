# backend/routers/portfolio.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from middleware.auth import get_user_profile
from services.gemini_service import generate_portfolio_html
from services.pdf_service import extract_text_from_pdf
from database import supabase
from config import settings
import logging, base64

logger = logging.getLogger("careerlens.portfolio")

router = APIRouter()

@router.post("/generate")
async def generate_portfolio(
    resume: UploadFile = File(...),
    name: str = Form(""),
    github_username: str = Form(""),
    profile=Depends(get_user_profile),
):
    user_id = profile["user_id"]
    current_count = int(profile.get("portfolio_gen_count") or 0)
    limit = settings.FREEMIUM_MAX_PORTFOLIO_GENS

    if profile.get("plan_type") == "freemium" and current_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Portfolio generation limit reached ({limit}). Upgrade to Premium for unlimited access.",
        )

    if resume.content_type not in settings.ALLOWED_RESUME_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await resume.read()
    if len(content) > settings.MAX_RESUME_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Resume must be under {settings.MAX_RESUME_SIZE_MB}MB.")

    try:
        resume_text = extract_text_from_pdf(base64.b64encode(content).decode('utf-8')).strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    try:
        html = await generate_portfolio_html(resume_text, github_username, name)
    except Exception as e:
        logger.error(f"Portfolio generation failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Portfolio generation failed: {str(e)}")

    counter_updated = False
    next_count = current_count
    try:
        try:
            supabase.rpc("increment_portfolio_count", {"p_user_id": user_id}).execute()
            counter_updated = True
        except Exception:
            supabase.table("users").update({"portfolio_gen_count": current_count + 1}).eq("user_id", user_id).execute()
            counter_updated = True
        if counter_updated:
            next_count = current_count + 1
    except Exception as e:
        logger.warning(f"Portfolio usage counter update failed for user {user_id}: {e}")
        if profile.get("plan_type") == "freemium":
            raise HTTPException(
                status_code=500,
                detail="Could not update portfolio usage counter. Apply backend/sql/portfolio_usage.sql in Supabase and retry.",
            )

    remaining = None
    if profile.get("plan_type") == "freemium":
        remaining = max(0, limit - next_count)

    return {
        "success": True,
        "html": html,
        "usage": {
            "portfolio_gen_count": next_count,
            "remaining": remaining,
            "limit": limit if profile.get("plan_type") == "freemium" else None,
        },
    }
