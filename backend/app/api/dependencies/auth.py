from fastapi import HTTPException, Request

from app.domain.types.auth import AuthContext
from app.infra.models.api_key_model import ApiKeyModel
from app.infra.session import get_session
from app.infra.settings import settings
from app.services.api_key_service import hash_api_key
from app.services.rate_limiter import rate_limiter


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "error_code": "unauthorized",
            "message": "Missing or invalid API key.",
        },
    )


def get_auth_context(request: Request) -> AuthContext:
    if settings.auth_mode != "api_key":
        return AuthContext(
            mode="off",
            api_key_id=None,
            name=None,
            role=None,
            rate_limit_key="anonymous",
        )

    header_value = request.headers.get(settings.auth_header_name)
    if not header_value:
        raise _unauthorized()

    key_hash = hash_api_key(header_value)
    with get_session() as session:
        api_key = session.query(ApiKeyModel).filter_by(key_hash=key_hash).first()

    if not api_key or not api_key.active:
        raise _unauthorized()

    return AuthContext(
        mode="api_key",
        api_key_id=api_key.id,
        name=api_key.name,
        role=api_key.role,
        rate_limit_key=api_key.id or key_hash,
    )


def enforce_rate_limit(request: Request) -> AuthContext:
    auth_context = get_auth_context(request)
    if not rate_limiter.allow(auth_context.rate_limit_key):
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": "rate_limited",
                "message": "Too many requests. Try again later.",
            },
        )
    return auth_context
