# ============================================================
# CareerLens – GitHub Router
# File: backend/routers/github.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_authenticated_user
from services.github_service import fetch_github_profile
import logging

logger = logging.getLogger("careerlens.github")
router = APIRouter()


@router.get("/profile")
async def get_github_profile(username: str, user=Depends(get_authenticated_user)):
    """Fetch and return public GitHub profile data."""
    try:
        data = await fetch_github_profile(username)
        return {"success": True, "github": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
