# ============================================================
# CareerLens – Supabase Client
# File: backend/database.py
# Provides a reusable Supabase client for all routers/services
# ============================================================

from supabase import create_client, Client
from config import settings
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
    Validates the Supabase JWT and returns the user payload.
    Raises an exception if the token is invalid or expired.
    """
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise ValueError("Invalid or expired token")

        auth_user = user_response.user
        providers: list[str] = []
        github_username: str | None = None

        identities = getattr(auth_user, "identities", None) or []
        for identity in identities:
            provider = getattr(identity, "provider", None)
            if provider is None and isinstance(identity, dict):
                provider = identity.get("provider")
            if provider and provider not in providers:
                providers.append(provider)

            if provider == "github":
                identity_data = getattr(identity, "identity_data", None)
                if identity_data is None and isinstance(identity, dict):
                    identity_data = identity.get("identity_data")
                identity_data = identity_data or {}
                github_username = (
                    identity_data.get("user_name")
                    or identity_data.get("preferred_username")
                    or identity_data.get("username")
                    or identity_data.get("login")
                )

        app_metadata = getattr(auth_user, "app_metadata", None) or {}
        provider_from_metadata = app_metadata.get("provider")
        if provider_from_metadata and provider_from_metadata not in providers:
            providers.append(provider_from_metadata)

        # Supabase may expose multiple providers under app_metadata.providers.
        providers_from_metadata = app_metadata.get("providers") or []
        if isinstance(providers_from_metadata, list):
            for provider in providers_from_metadata:
                if provider and provider not in providers:
                    providers.append(provider)

        user_metadata = getattr(auth_user, "user_metadata", None) or {}
        if not github_username:
            github_username = (
                user_metadata.get("user_name")
                or user_metadata.get("preferred_username")
                or user_metadata.get("username")
                or user_metadata.get("login")
            )

        # If a GitHub-like username exists in metadata, treat the account as GitHub-linked.
        if github_username and "github" not in providers:
            providers.append("github")

        # If we're running on anon fallback, attach the user's JWT so RLS
        # policies can authorize table queries performed after auth.
        if not is_service_role_configured():
            supabase.postgrest.auth(token)

        return {
            "user_id": auth_user.id,
            "email": auth_user.email,
            "providers": providers,
            "github_username": github_username,
        }
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise
