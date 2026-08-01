from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class GoogleOAuthService:
    """Service to verify Google OAuth ID Tokens."""

    @staticmethod
    def verify_token(token_string: str) -> dict:
        """Verifies Google ID token against Google's public keys and returns token claims payload."""
        try:
            client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
            id_info = id_token.verify_oauth2_token(
                token_string,
                requests.Request(),
                audience=client_id if client_id and client_id != "your-google-client-id.apps.googleusercontent.com" else None,
            )
            return id_info
        except Exception as e:
            raise AuthenticationFailed(f"Invalid Google token: {str(e)}")
