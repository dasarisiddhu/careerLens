# ============================================================
# CareerLens – Supabase Client
# File: backend/database.py
# Provides a reusable Supabase client for all routers/services
# ============================================================

from supabase import create_client, Client
from config import settings
from jose import jwt as jose_jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
import logging

logger = logging.getLogger("careerlens.database")

# ============================================================
# Supabase client singleton
# Uses the SERVICE ROLE key (full DB access, bypasses RLS)
# Only used server-side – never expose this key to the frontend
# ============================================================

def get_supabase() -> tuple[Client, bool]:
    """
    Returns an authenticated Supabase client.
    Call this inside route handlers or services.
    """
    if not settings.SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL must be set in environment variables.")

    # Prefer backend service role key when valid.
    if settings.SUPABASE_KEY:
        try:
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY), False
        except Exception as e:
            logger.warning(f"Failed to initialize with SUPABASE_KEY: {e}")

    # Fallback for local/dev when service role key is missing/invalid.
    if settings.SUPABASE_ANON_KEY:
        logger.warning(
            "Falling back to SUPABASE_ANON_KEY. "
            "Set a valid SUPABASE_KEY (service role) for full backend access."
        )
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY), True

    raise RuntimeError(
        "Set a valid SUPABASE_KEY (recommended) or SUPABASE_ANON_KEY."
    )


def is_service_role_configured() -> bool:
    """True when backend is using service-role auth (not anon fallback)."""
    return not USING_ANON_FALLBACK


# Module-level client (reused across requests)
try:
    supabase, USING_ANON_FALLBACK = get_supabase()
    logger.info("✅ Supabase client initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase client: {e}")
    supabase = None  # type: ignore
    USING_ANON_FALLBACK = False


# ============================================================
# Helper: Verify Supabase JWT token from Authorization header
# Used by the auth middleware to identify the current user
# ============================================================

async def get_current_user(token: str) -> dict:
    """
    Validates the Supabase JWT LOCALLY (signature + expiry check against
    SUPABASE_JWT_SECRET) and returns the user payload derived from the JWT's
    own claims.

    This intentionally does NOT call supabase.auth.get_user(token), which
    was making a live network round-trip to Supabase's auth API on every
    single authenticated request — adding latency to every action and
    causing transient Supabase slowness/rate-limiting to surface to users as
    "Invalid or expired authentication token" even when their session was
    fine. Local verification is instant and has no external dependency.

    Known trade-off: the JWT payload carries app_metadata and user_metadata
    (which is where we derive providers / github_username below), but NOT
    the full `identities[].identity_data` array that the old
    supabase.auth.get_user() response exposed. In practice Supabase copies
    the OAuth identity's username into user_metadata on sign-in, so this
    covers the common case; if a github_username still can't be resolved
    for a given account, that's a narrower edge case than what we were
    trading away (site-wide latency + flaky false "invalid token" errors).
    """
    payload = None
    keys_to_try = []

    if settings.SUPABASE_JWT_SECRET:
        import base64 as _base64
        try:
            keys_to_try.append(_base64.b64decode(settings.SUPABASE_JWT_SECRET))
        except Exception:
            pass
        keys_to_try.append(settings.SUPABASE_JWT_SECRET.encode("utf-8"))

    # Tier 1: Local token decode (fast, zero network latency)
    for signing_key in keys_to_try:
        try:
            payload = jose_jwt.decode(
                token,
                signing_key,
                algorithms=["HS256"],
                audience="authenticated",
            )
            break
        except ExpiredSignatureError as e:
            raise ValueError("Token has expired") from e
        except (JWTError, JWTClaimsError):
            # Try without strict aud verification in case aud is a project URL or list
            try:
                payload = jose_jwt.decode(
                    token,
                    signing_key,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
                break
            except ExpiredSignatureError as e:
                raise ValueError("Token has expired") from e
            except (JWTError, JWTClaimsError):
                continue

    # Tier 2: Fallback to Supabase live auth API if local validation failed
    if payload is None:
        if supabase:
            try:
                user_resp = supabase.auth.get_user(token)
                user_obj = getattr(user_resp, "user", None)
                if user_obj:
                    user_id = getattr(user_obj, "id", None)
                    email = getattr(user_obj, "email", None)
                    app_metadata = getattr(user_obj, "app_metadata", {}) or {}
                    user_metadata = getattr(user_obj, "user_metadata", {}) or {}
                    providers: list[str] = []
                    p = app_metadata.get("provider")
                    if p and p not in providers:
                        providers.append(p)
                    for pr in app_metadata.get("providers") or []:
                        if pr and pr not in providers:
                            providers.append(pr)
                    github_username = (
                        user_metadata.get("user_name")
                        or user_metadata.get("preferred_username")
                        or user_metadata.get("username")
                        or user_metadata.get("login")
                    )
                    if github_username and "github" not in providers:
                        providers.append("github")
                    return {
                        "user_id": user_id,
                        "email": email,
                        "providers": providers,
                        "github_username": github_username,
                    }
            except Exception as e:
                err_msg = str(e).lower()
                if "expired" in err_msg:
                    raise ValueError("Token has expired") from e
                logger.info("Supabase auth.get_user fallback also rejected token: %s", e)
                raise ValueError("Invalid token") from e
        raise ValueError("Invalid token")

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id:
        raise ValueError("Token missing subject claim")

    app_metadata = payload.get("app_metadata") or {}
    user_metadata = payload.get("user_metadata") or {}

    providers: list[str] = []
    provider_from_metadata = app_metadata.get("provider")
    if provider_from_metadata and provider_from_metadata not in providers:
        providers.append(provider_from_metadata)

    providers_from_metadata = app_metadata.get("providers") or []
    if isinstance(providers_from_metadata, list):
        for provider in providers_from_metadata:
            if provider and provider not in providers:
                providers.append(provider)

    # Some custom Supabase auth hooks embed a lightweight identities claim
    # directly in the JWT — use it if present, otherwise fall back to
    # user_metadata (the common case for standard GitHub OAuth sign-in).
    github_username: str | None = None
    identities = payload.get("identities") or []
    for identity in identities:
        provider = identity.get("provider") if isinstance(identity, dict) else None
        if provider and provider not in providers:
            providers.append(provider)
        if provider == "github":
            identity_data = identity.get("identity_data") or {} if isinstance(identity, dict) else {}
            github_username = (
                identity_data.get("user_name")
                or identity_data.get("preferred_username")
                or identity_data.get("username")
                or identity_data.get("login")
            )

    if not github_username:
        github_username = (
            user_metadata.get("user_name")
            or user_metadata.get("preferred_username")
            or user_metadata.get("username")
            or user_metadata.get("login")
        )

    if github_username and "github" not in providers:
        providers.append("github")

    # If we're running on anon fallback, attach the user's JWT so RLS
    # policies can authorize table queries performed after auth.
    if not is_service_role_configured():
        supabase.postgrest.auth(token)

    return {
        "user_id": user_id,
        "email": email,
        "providers": providers,
        "github_username": github_username,
    }