import logging
import requests
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
from ninja.errors import HttpError
from asgiref.sync import sync_to_async

from .models import User
from .selectors import aget_user_by_email
from .auth import create_jwt_token

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_google_auth_url() -> str:
    """
    Build the Google OAuth2 authorization URL for the consent screen.
    """
    client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    redirect_uri = getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "")

    if not client_id:
        raise HttpError(500, "Google OAuth is not configured.")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query_string}"


def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange the authorization code for Google tokens.
    Returns the parsed JSON response containing id_token, access_token, etc.
    """
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", ""),
            "client_secret": getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", ""),
            "redirect_uri": getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", ""),
            "grant_type": "authorization_code",
        },
        timeout=10,
    )

    if response.status_code != 200:
        logger.error(f"Google token exchange failed: {response.text}")
        raise HttpError(400, "Failed to exchange authorization code with Google.")

    return response.json()


def verify_google_id_token(token: str) -> dict:
    """
    Verify and decode the Google ID token.
    Returns the decoded payload with email, name, sub, etc.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            GoogleRequest(),
            getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", ""),
        )
        if idinfo.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            raise HttpError(401, "Invalid token issuer.")
        return idinfo
    except ValueError as e:
        logger.error(f"Google ID token verification failed: {e}")
        raise HttpError(401, "Invalid Google ID token.")


async def agoogle_oauth_callback(code: str) -> dict:
    """
    Full Google OAuth callback handler:
    1. Exchange code for tokens
    2. Verify ID token
    3. Find or create user
    4. Return app JWT tokens
    """
    token_data = await sync_to_async(exchange_code_for_tokens)(code)

    raw_id_token = token_data.get("id_token")
    if not raw_id_token:
        raise HttpError(400, "No ID token received from Google.")

    google_user = await sync_to_async(verify_google_id_token)(raw_id_token)

    email = google_user.get("email")
    if not email:
        raise HttpError(400, "Google account does not have an email address.")

    user = await aget_user_by_email(email)

    if not user:
        first_name = google_user.get("given_name", "")
        last_name = google_user.get("family_name", "")
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_verified=True,
            is_active=True,
        )
        user.set_unusable_password()
        await user.asave()
    else:
        if not user.is_active:
            raise HttpError(401, "User account is disabled.")
        if not user.is_verified:
            user.is_verified = True
            await user.asave()

    tokens = create_jwt_token(user.id)
    return {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
        },
    }
