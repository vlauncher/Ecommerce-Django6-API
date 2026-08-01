from django.core.cache import cache
from django.conf import settings

class RedisOTPService:
    """Redis-backed OTP verification & caching service with 5-minute expiration."""

    EXPIRY_SECONDS = 300 # 5 minutes

    @classmethod
    def store_otp(cls, email: str, code: str):
        cache_key = f"otp:{email.lower()}"
        cache.set(cache_key, code, timeout=cls.EXPIRY_SECONDS)

    @classmethod
    def get_otp(cls, email: str) -> str | None:
        cache_key = f"otp:{email.lower()}"
        return cache.get(cache_key)

    @classmethod
    def verify_otp(cls, email: str, code: str) -> bool:
        stored_code = cls.get_otp(email)
        if stored_code and str(stored_code).strip() == str(code).strip():
            cls.delete_otp(email)
            return True
        return False

    @classmethod
    def delete_otp(cls, email: str):
        cache_key = f"otp:{email.lower()}"
        cache.delete(cache_key)
