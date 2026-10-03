from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from jose import jwt
import logging

logger = logging.getLogger("careerlens.rate_limit")


def get_user_or_ip(request: Request) -> str:
    """
    Key rate limits by authenticated user id (JWT 'sub') when present,
    falling back to client IP for unauthenticated requests.
    Prevents multiple users behind a reverse proxy from sharing a global rate limit bucket.
    """
    # 1. Check if user was attached to request state by auth middleware/dependency
    user = getattr(request.state, "user", None)
    if isinstance(user, dict) and user.get("user_id"):
        return f"user:{user['user_id']}"

    # 2. Extract Bearer token from Authorization header if present
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            claims = jwt.get_unverified_claims(token)
            user_id = claims.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass

    # 3. Fallback to client IP address
    return get_remote_address(request)


# Default limiter keys by authenticated user when available, or client IP
limiter = Limiter(key_func=get_user_or_ip, headers_enabled=False)
