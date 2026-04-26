# backend/routers/recommendations.py
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from middleware.auth import get_authenticated_user, get_user_profile
from services.gemini_service import get_career_recommendations
from services.github_service import fetch_github_profile

router = APIRouter()


class RecommendRequest(BaseModel):
    skills: list[str] = Field(default_factory=list)
    experience: str = ""
    interests: list[str] = Field(default_factory=list)


def _extract_github_username(github_url: str | None) -> str:
    raw = (github_url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    parts = [p for p in (parsed.path or "").split("/") if p]
    return parts[0] if parts else ""


@router.post("/")
async def recommend(
    body: RecommendRequest,
    user=Depends(get_authenticated_user),
    profile=Depends(get_user_profile),
):
    github_username = (user.get("github_username") or "").strip() or _extract_github_username(profile.get("github_url"))
    if not github_username:
        raise HTTPException(
            status_code=400,
            detail="Link your GitHub profile in Profile before requesting AI recommendations.",
        )

    try:
        github_data = await fetch_github_profile(github_username)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=502, detail="Could not fetch GitHub profile right now. Please try again.")

    result = await get_career_recommendations(
        body.skills,
        body.experience,
        body.interests,
        github_data=github_data,
        desired_role=(profile.get("desired_role") or "").strip(),
    )
    return {
        "success": True,
        "recommendations": result,
        "github": {
            "username": github_data.get("username"),
            "public_repos": github_data.get("public_repos", 0),
            "total_stars": github_data.get("total_stars", 0),
            "top_languages": list((github_data.get("languages") or {}).keys())[:5],
        },
    }
