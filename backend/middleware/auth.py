# ============================================================
# CareerLens – Auth Middleware / Dependencies
# File: backend/middleware/auth.py
# Provides FastAPI dependency for protected routes
# ============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_current_user, supabase
import logging

logger = logging.getLogger("careerlens.auth")

# FastAPI bearer token scheme
bearer_scheme = HTTPBearer()


# ============================================================
# Dependency: get_authenticated_user
# Inject into any route to require authentication
#
# Usage:
#   @router.get("/protected")
#   async def route(user=Depends(get_authenticated_user)):
#       return {"user_id": user["user_id"]}
# ============================================================

async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        # Centralized token validation (also attaches JWT for anon-key fallback mode).
        return await get_current_user(token)
    except Exception as e:
        logger.warning(f"Auth token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ============================================================
# Dependency: get_user_profile
# Returns the full user profile from the DB (plan_type, counts)
# ============================================================

async def get_user_profile(
    user: dict = Depends(get_authenticated_user),
) -> dict:
    """
    Fetches the full user profile from public.users table.
    Includes plan_type, usage counts, etc.
    """
    try:
        result = (
            supabase.table("users")
            .select("*")
            .eq("user_id", user["user_id"])
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

        # Auto-bootstrap missing profile rows for accounts created before DB trigger setup.
        email = user.get("email") or ""
        name = email.split("@")[0] if "@" in email else "User"
        try:
            supabase.table("users").insert({
                "user_id": user["user_id"],
                "email": email,
                "name": name,
            }).execute()
        except Exception as create_err:
            logger.warning(f"Auto-create profile failed for user {user['user_id']}: {create_err}")

        # Re-read after best-effort create attempt.
        result = (
            supabase.table("users")
            .select("*")
            .eq("user_id", user["user_id"])
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please sign out and sign in again.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load user profile.",
        )


# ============================================================
# Dependency: require_premium
# Blocks freemium users from accessing premium-only routes
# ============================================================

async def require_premium(
    profile: dict = Depends(get_user_profile),
) -> dict:
    """
    Raises HTTP 403 if the user is not on the premium plan.
    """
    if profile.get("plan_type") != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires a Premium subscription. Please upgrade.",
        )
    return profile
