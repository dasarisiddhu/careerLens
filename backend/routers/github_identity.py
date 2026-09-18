# ============================================================
# CareerLens -- GitHub Identity Router
# File: backend/routers/github_identity.py
#
# Enforces durable GitHub ownership at the database level.
#
# Invariant A: UNIQUE(github_user_id)  -- one CareerLens user per GitHub account
# Invariant B: UNIQUE(careerlens_user_id) -- one GitHub account per CareerLens user
#
# The numeric GitHub account ID is obtained from the validated Supabase OAuth
# identity record (auth.identities.provider_id), never from a client-submitted
# field. This prevents IDOR via forged github_user_id values.
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_authenticated_user
from database import supabase
import logging

logger = logging.getLogger("careerlens.github_identity")
router = APIRouter()


def _get_github_provider_id_from_supabase(user_id: str) -> tuple[str, str, str | None]:
    """
    Fetch the GitHub numeric ID (provider_id) and login from Supabase auth admin API.
    Returns (github_user_id_as_text, github_login, avatar_url_or_None).
    Raises HTTPException if no GitHub identity found.

    SECURITY: provider_id comes from the validated OAuth exchange stored server-side
    by Supabase. It is NOT trusted from any client request body.
    """
    try:
        admin_user = supabase.auth.admin.get_user_by_id(user_id)
    except Exception as e:
        logger.error("Failed to fetch admin user data for %s: %s", user_id, e)
        raise HTTPException(status_code=503, detail="Could not verify your GitHub identity. Please try again.")

    user_obj = getattr(admin_user, "user", None)
    if user_obj is None:
        raise HTTPException(status_code=404, detail="User not found.")

    identities = getattr(user_obj, "identities", None) or []
    github_identity = None
    for identity in identities:
        provider = (
            identity.get("provider") if isinstance(identity, dict)
            else getattr(identity, "provider", None)
        )
        if provider == "github":
            github_identity = identity
            break

    if github_identity is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "No GitHub identity found for your account. "
                "Please sign in or link your account via GitHub OAuth first."
            ),
        )

    if isinstance(github_identity, dict):
        provider_id = github_identity.get("provider_id") or github_identity.get("id")
        identity_data = github_identity.get("identity_data") or {}
    else:
        provider_id = getattr(github_identity, "provider_id", None) or getattr(github_identity, "id", None)
        identity_data = getattr(github_identity, "identity_data", None) or {}

    if not provider_id:
        logger.error("GitHub identity for user %s is missing provider_id: %s", user_id, github_identity)
        raise HTTPException(
            status_code=503,
            detail="Could not extract your GitHub account ID. Please unlink and re-link your GitHub account.",
        )

    github_user_id_text = str(provider_id)
    github_login = (
        identity_data.get("user_name")
        or identity_data.get("preferred_username")
        or identity_data.get("login")
        or identity_data.get("name")
        or ""
    )
    avatar_url = identity_data.get("avatar_url") or identity_data.get("picture")

    return github_user_id_text, github_login, avatar_url


@router.get("/")
async def get_github_identity(user=Depends(get_authenticated_user)):
    """Return the caller'\''s github_identity record."""
    user_id = user["user_id"]
    try:
        result = (
            supabase.table("github_identities")
            .select("github_user_id, github_login, avatar_url, created_at, updated_at")
            .eq("careerlens_user_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return {"success": True, "identity": result.data[0]}
        return {"success": True, "identity": None}
    except Exception as e:
        logger.error("Failed to fetch github identity for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Could not fetch GitHub identity.")


@router.post("/link")
async def link_github_identity(user=Depends(get_authenticated_user)):
    """
    Register or confirm the caller'\''s GitHub identity from their Supabase OAuth record.

    The GitHub numeric ID is obtained from Supabase'\''s server-side OAuth record
    (auth.identities.provider_id) -- NOT from the request body.

    Concurrent race (User A and User B both linking the same GitHub):
    DB UNIQUE constraint guarantees exactly one INSERT succeeds.
    """
    user_id = user["user_id"]

    # 1. Obtain durable numeric ID from Supabase admin API (server-side only)
    github_user_id, github_login, avatar_url = _get_github_provider_id_from_supabase(user_id)

    # 2. Check for existing record (idempotent: same user + same GitHub ID = OK)
    try:
        existing = (
            supabase.table("github_identities")
            .select("careerlens_user_id, github_user_id, github_login")
            .eq("careerlens_user_id", user_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            row = existing.data[0]
            if row["github_user_id"] == github_user_id:
                # Idempotent: same link exists. Refresh mutable login if changed.
                if row.get("github_login") != github_login and github_login:
                    supabase.table("github_identities").update(
                        {"github_login": github_login, "avatar_url": avatar_url}
                    ).eq("careerlens_user_id", user_id).execute()
                return {
                    "success": True,
                    "github_user_id": github_user_id,
                    "github_login": github_login,
                    "message": "GitHub identity confirmed.",
                }
            # Different GitHub ID for this user -- reject (Invariant B)
            raise HTTPException(
                status_code=409,
                detail=(
                    "Your account is already linked to a different GitHub account. "
                    "Unlink the existing GitHub account before linking a new one."
                ),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking existing identity for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Could not verify existing GitHub link.")

    # 3. Check whether this GitHub account is already owned by another user (pre-check)
    try:
        conflict = (
            supabase.table("github_identities")
            .select("careerlens_user_id")
            .eq("github_user_id", github_user_id)
            .limit(1)
            .execute()
        )
        if conflict.data and conflict.data[0]["careerlens_user_id"] != user_id:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This GitHub account is already linked to another CareerLens account. "
                    "If this is your GitHub account, please contact support."
                ),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking GitHub conflict for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Could not check GitHub account availability.")

    # 4. INSERT -- DB UNIQUE constraints are the final authority.
    #    Concurrent race between two users for same GitHub ID:
    #    exactly one INSERT succeeds; the other gets a constraint violation.
    try:
        insert_payload = {
            "careerlens_user_id": user_id,
            "github_user_id": github_user_id,
            "github_login": github_login,
        }
        if avatar_url:
            insert_payload["avatar_url"] = avatar_url

        supabase.table("github_identities").insert(insert_payload).execute()

        # Sync users.github_url for backward compatibility
        if github_login:
            github_url = f"https://github.com/{github_login}"
            try:
                supabase.table("users").update({"github_url": github_url}).eq(
                    "user_id", user_id
                ).execute()
            except Exception as url_err:
                logger.warning("Could not sync github_url for user %s: %s", user_id, url_err)

        logger.info(
            "GitHub identity linked: user_id=%s github_user_id=%s github_login=%s",
            user_id, github_user_id, github_login,
        )
        return {
            "success": True,
            "github_user_id": github_user_id,
            "github_login": github_login,
            "message": "GitHub account linked successfully.",
        }

    except HTTPException:
        raise
    except Exception as e:
        err_str = str(e).lower()
        if "unique" in err_str or "duplicate" in err_str:
            # Translate constraint violations into clear domain errors
            try:
                conflict_check = (
                    supabase.table("github_identities")
                    .select("careerlens_user_id")
                    .eq("github_user_id", github_user_id)
                    .limit(1)
                    .execute()
                )
                if conflict_check.data and conflict_check.data[0]["careerlens_user_id"] != user_id:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "This GitHub account was just linked to another account. "
                            "If this is your GitHub account, please contact support."
                        ),
                    )
            except HTTPException:
                raise
            except Exception:
                pass
            raise HTTPException(status_code=409, detail="Your account already has a linked GitHub identity.")
        logger.error("Failed to insert github identity for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Could not link GitHub identity. Please try again.")


@router.delete("/unlink")
async def unlink_github_identity(user=Depends(get_authenticated_user)):
    """Remove the caller'\''s GitHub identity link (does not affect Supabase Auth identity)."""
    user_id = user["user_id"]
    try:
        result = (
            supabase.table("github_identities")
            .delete()
            .eq("careerlens_user_id", user_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="No linked GitHub identity found for your account.")
        logger.info("GitHub identity unlinked for user %s", user_id)
        return {"success": True, "message": "GitHub identity unlinked."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to unlink github identity for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Could not unlink GitHub identity. Please try again.")
