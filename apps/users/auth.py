import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from ninja.security import HttpBearer
from .selectors import aget_user_by_id


def create_jwt_token(user_id: int) -> dict:
    """
    Generate JWT access and refresh tokens for a user.
    """
    now = datetime.now(timezone.utc)
    access_exp = now + timedelta(minutes=getattr(settings, "JWT_ACCESS_EXPIRATION_MINUTES", 30))
    refresh_exp = now + timedelta(days=getattr(settings, "JWT_REFRESH_EXPIRATION_DAYS", 7))
    secret = getattr(settings, "SECRET_KEY")

    access_payload = {
        "token_type": "access",
        "user_id": user_id,
        "exp": access_exp,
        "iat": now,
    }

    refresh_payload = {
        "token_type": "refresh",
        "user_id": user_id,
        "exp": refresh_exp,
        "iat": now,
    }

    access_token = jwt.encode(access_payload, secret, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, secret, algorithm="HS256")

    return {
        "access": access_token,
        "refresh": refresh_token,
    }


def decode_jwt_token(token: str, expected_type: str = "access") -> dict:
    """
    Decodes and validates a JWT token.
    """
    secret = getattr(settings, "SECRET_KEY")
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    if payload.get("token_type") != expected_type:
        raise jwt.InvalidTokenError("Invalid token type")
    return payload


class JWTAuth(HttpBearer):
    """
    Async HTTP Bearer authentication for Django Ninja routes.
    """
    async def authenticate(self, request, token: str):
        try:
            payload = decode_jwt_token(token, expected_type="access")
            user_id = payload.get("user_id")
            user = await aget_user_by_id(user_id)
            if user and user.is_active:
                return user
        except Exception:
            return None
