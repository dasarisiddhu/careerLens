# ============================================================
# CareerLens – GitHub Router
# File: backend/routers/github.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_authenticated_user
from services.github_service import fetch_github_profile, validate_github_username
import logging

logger = logging.getLogger("careerlens.github")
router = APIRouter()


@router.get("/profile")
async def get_github_profile(username: str, user=Depends(get_authenticated_user)):
    """Fetch and return public GitHub profile data."""
    try:
        validated_user = validate_github_username(username)
    except ValueError as e:
        logger.warning(f"Invalid GitHub username '{username}' rejected: {e}")
        raise HTTPException(status_code=422, detail="Invalid GitHub username format.")

    try:
        data = await fetch_github_profile(validated_user)
        return {"success": True, "github": data}
    except ValueError as e:
        msg = str(e)
        logger.warning(f"GitHub profile lookup issue for '{validated_user}': {msg}")
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail="GitHub user not found.")
        raise HTTPException(status_code=422, detail="Invalid GitHub request.")
    except Exception as e:
        logger.error(f"Error fetching GitHub profile for '{validated_user}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch GitHub profile. Please try again.")
