# ============================================================
# CareerLens – Auth Router
# File: backend/routers/auth.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from database import supabase
from middleware.auth import get_authenticated_user, get_user_profile
import logging
from urllib.parse import urlparse

logger = logging.getLogger("careerlens.auth")
router = APIRouter()

try:
    import email_validator  # type: ignore # noqa: F401
    EmailType = EmailStr
except Exception:
    # Keep backend bootable even if optional email validator dependency is missing.
    EmailType = str


# ---- Pydantic Models ----

class SignUpRequest(BaseModel):
    email: EmailType
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailType
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailType

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    github_url: str | None = None
    desired_role: str | None = None


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


def github_url_from_username(username: str | None) -> str | None:
    handle = (username or "").strip()
    return f"https://github.com/{handle}" if handle else None


# ---- Routes ----

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignUpRequest):
    """Register a new user via Supabase Auth."""
    try:
        res = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {"data": {"name": body.name}},
        })
        if res.user is None:
            raise HTTPException(status_code=400, detail="Signup failed. Email may already be registered.")
        return {"success": True, "message": "Account created. Please verify your email.", "user_id": res.user.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login(body: LoginRequest):
    """Authenticate user and return Supabase session tokens."""
    try:
        res = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        return {
            "success": True,
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": {"id": res.user.id, "email": res.user.email},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password.")


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Send password reset email via Supabase."""
    try:
        supabase.auth.reset_password_email(body.email)
        return {"success": True, "message": "Password reset email sent if the account exists."}
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return {"success": True, "message": "Password reset email sent if the account exists."}


@router.post("/logout")
async def logout(user=Depends(get_authenticated_user)):
    """Sign out the current user."""
    try:
        supabase.auth.sign_out()
        return {"success": True, "message": "Logged out successfully."}
    except Exception:
        return {"success": True, "message": "Logged out."}


@router.get("/me")
async def get_me(profile=Depends(get_user_profile), user=Depends(get_authenticated_user)):
    """Return the current authenticated user's full profile."""
    merged = dict(profile)
    auth_providers = user.get("providers") or []
    github_username = user.get("github_username")
    linked_github_url = github_url_from_username(github_username)

    current_github_url = merged.get("github_url")
    normalized_current_github_url = None
    if current_github_url:
        try:
            normalized_current_github_url = normalize_github_url(current_github_url)
        except HTTPException:
            normalized_current_github_url = None

    # Auto-populate and persist GitHub URL for OAuth users.
    desired_github_url = linked_github_url or normalized_current_github_url
    if desired_github_url:
        merged["github_url"] = desired_github_url
        if desired_github_url != current_github_url:
            try:
                supabase.table("users").update({"github_url": desired_github_url}).eq("user_id", user["user_id"]).execute()
            except Exception as e:
                logger.warning(f"Could not auto-sync github_url for user {user['user_id']}: {e}")

    merged["auth_providers"] = auth_providers
    merged["github_username"] = github_username
    return {"success": True, "user": merged}


@router.put("/me")
async def update_profile(body: UpdateProfileRequest, user=Depends(get_authenticated_user)):
    """Update user profile fields."""
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    try:
        existing_q = (
            supabase.table("users")
            .select("github_url")
            .eq("user_id", user["user_id"])
            .limit(1)
            .execute()
        )
        if not existing_q.data:
            raise HTTPException(status_code=404, detail="User profile not found.")

        existing_github_url = existing_q.data[0].get("github_url")
        normalized_existing_github_url = None
        if existing_github_url:
            try:
                normalized_existing_github_url = normalize_github_url(existing_github_url)
            except HTTPException:
                normalized_existing_github_url = None

        normalized_requested_github_url = None
        if "github_url" in updates:
            normalized_requested_github_url = normalize_github_url(updates["github_url"])
            updates["github_url"] = normalized_requested_github_url

        linked_github_url = github_url_from_username(user.get("github_username"))

        # If GitHub OAuth is linked, trust that identity and auto-heal legacy mismatches.
        if linked_github_url and normalized_existing_github_url and normalized_existing_github_url != linked_github_url:
            normalized_existing_github_url = linked_github_url
            updates["github_url"] = linked_github_url

        # Once set, github_url is immutable for account integrity.
        if normalized_existing_github_url:
            if (
                normalized_requested_github_url
                and normalized_requested_github_url != normalized_existing_github_url
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"GitHub profile is locked to {normalized_existing_github_url} and cannot be changed.",
                )
            updates["github_url"] = normalized_existing_github_url
        else:
            # If user is authenticated via GitHub, profile URL must match linked identity.
            if linked_github_url:
                if normalized_requested_github_url and normalized_requested_github_url != linked_github_url:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Your linked GitHub account is {linked_github_url}. Use that profile URL.",
                    )
                updates["github_url"] = linked_github_url

        result = supabase.table("users").update(updates).eq("user_id", user["user_id"]).execute()
        return {"success": True, "user": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
