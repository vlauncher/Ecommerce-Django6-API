import json
import random
import string
import logging
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from ninja.errors import HttpError
import cloudinary.uploader

from .models import User, UserProfile
from .selectors import aget_user_by_email, aget_user_by_id, aget_profile_by_user
from .auth import create_jwt_token, decode_jwt_token

logger = logging.getLogger(__name__)


async def acheck_rate_limit(key: str, limit: int, window: int) -> None:
    def check():
        cache_key = f"rate:{key}"
        if cache.add(cache_key, 1, timeout=window):
            return
        try:
            count = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=window)
            return
        if count > limit:
            raise HttpError(429, "Too many attempts. Please try again later.")
    await sync_to_async(check)()


# ─── Cache & Email Helpers (Wrapped for Async) ──────────────────────────
async def agenerate_otp(purpose: str, email: str) -> str:
    """
    Generates a 6-digit numeric OTP and stores it in cache keyed by OTP string (async wrapper).
    """
    def _generate():
        otp = "".join(random.choices(string.digits, k=6))
        cache_key = f"otp:{purpose}:{otp}"
        payload = {"email": email, "purpose": purpose}
        ttl = getattr(settings, "OTP_EXPIRY_MINUTES", 10) * 60
        cache.set(cache_key, json.dumps(payload), timeout=ttl)
        return otp

    return await sync_to_async(_generate)()


async def averify_otp(purpose: str, otp: str) -> str:
    """
    Verifies the provided OTP for the specified purpose and deletes it (async wrapper).
    """
    def _verify():
        cache_key = f"otp:{purpose}:{otp}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            raise HttpError(400, "Invalid or expired OTP.")

        payload = json.loads(cached_data)
        email = payload.get("email")
        cache.delete(cache_key)
        return email

    return await sync_to_async(_verify)()


async def asend_otp_email(email: str, otp: str, purpose: str) -> None:
    """
    Sends an email with the OTP to the given email address (async wrapper).
    """
    def _send():
        subject_map = {
            "register": "Account Verification OTP",
            "forgot_password": "Password Reset OTP",
        }
        subject = subject_map.get(purpose, "Your OTP Code")
        message = f"Your OTP code for {purpose.replace('_', ' ')} is: {otp}. It is valid for {getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} minutes."

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ecommerce.com"),
            recipient_list=[email],
            fail_silently=False,
        )

    await sync_to_async(_send)()


# ─── Auth Business Logic (Async) ─────────────────────────────────────────
async def aregister_user(validated_data: dict) -> User:
    """
    Handles user registration logic asynchronously.
    """
    email = validated_data["email"]
    password = validated_data["password"]
    confirm_password = validated_data["confirm_password"]
    first_name = validated_data["first_name"]
    last_name = validated_data["last_name"]

    if password != confirm_password:
        raise HttpError(400, "Passwords do not match.")

    user = await aget_user_by_email(email)
    if user:
        if user.is_verified:
            raise HttpError(400, "User with this email already exists.")
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            await user.asave()
    else:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_verified=False,
            terms_accepted_at=timezone.now() if validated_data.get("accept_terms") else None,
            privacy_accepted_at=timezone.now() if validated_data.get("accept_privacy") else None,
        )
        user.set_password(password)
        await user.asave()

    otp = await agenerate_otp(purpose="register", email=email)
    await asend_otp_email(email=email, otp=otp, purpose="register")
    return user


async def averify_registration_otp(otp: str) -> User:
    """
    Verifies OTP for user registration and marks the user as verified.
    """
    email = await averify_otp(purpose="register", otp=otp)
    user = await aget_user_by_email(email)
    if not user:
        raise HttpError(400, "Associated user for this OTP was not found.")

    user.is_verified = True
    await user.asave()
    return user


async def alogin_user(email: str, password: str) -> dict:
    """
    Authenticates user and returns JWT token pair asynchronously.
    """
    await acheck_rate_limit(f"login:{email.lower()}", 10, 900)
    user = await aget_user_by_email(email)
    if not user or not user.check_password(password):
        raise HttpError(401, "Invalid email or password.")

    if not user.is_verified:
        raise HttpError(401, "Account is not verified. Please verify your email via OTP.")

    if not user.is_active:
        raise HttpError(401, "User account is disabled.")

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


async def arefresh_token(refresh_token: str) -> dict:
    """
    Refreshes JWT access token from refresh token.
    """
    try:
        payload = decode_jwt_token(refresh_token, expected_type="refresh")
        user = await aget_user_by_id(payload.get("user_id"))
        if not user or not user.is_active:
            raise HttpError(401, "User not active.")

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
    except Exception:
        raise HttpError(401, "Invalid or expired refresh token.")


async def aresend_otp(email: str, purpose: str) -> None:
    """
    Resends a fresh OTP to the provided email if user exists.
    """
    await acheck_rate_limit(f"otp:{purpose}:{email.lower()}", 5, 900)
    user = await aget_user_by_email(email)
    if not user:
        raise HttpError(400, "User with this email does not exist.")

    if purpose == "register" and user.is_verified:
        raise HttpError(400, "User is already verified.")

    otp = await agenerate_otp(purpose=purpose, email=email)
    await asend_otp_email(email=email, otp=otp, purpose=purpose)


async def ainitiate_forgot_password(email: str) -> None:
    """
    Generates and sends a password reset OTP to user.
    """
    user = await aget_user_by_email(email)
    if not user:
        return

    otp = await agenerate_otp(purpose="forgot_password", email=email)
    await asend_otp_email(email=email, otp=otp, purpose="forgot_password")


async def areset_password(otp: str, new_password: str, confirm_password: str) -> None:
    """
    Verifies reset OTP and sets new password for user asynchronously.
    """
    if new_password != confirm_password:
        raise HttpError(400, "Passwords do not match.")

    email = await averify_otp(purpose="forgot_password", otp=otp)
    user = await aget_user_by_email(email)
    if not user:
        raise HttpError(400, "User not found for this OTP.")

    user.set_password(new_password)
    await user.asave()


async def achange_password(user: User, old_password: str, new_password: str, confirm_password: str) -> None:
    """
    Changes password for an authenticated user.
    """
    if new_password != confirm_password:
        raise HttpError(400, "Passwords do not match.")

    if not user.check_password(old_password):
        raise HttpError(400, "Incorrect current password.")

    user.set_password(new_password)
    await user.asave()


async def adelete_account(user: User, password: str) -> None:
    if not user.check_password(password):
        raise HttpError(400, "Incorrect password.")
    user.email = f"deleted-{user.id}@invalid.local"
    user.first_name = "Deleted"
    user.last_name = "User"
    user.is_active = False
    user.is_verified = False
    user.set_unusable_password()
    await user.asave(update_fields=("email", "first_name", "last_name", "is_active", "is_verified", "password", "updated_at"))


async def aget_user_profile(user: User) -> dict:
    """
    Returns user profile with transformed Cloudinary URL.
    """
    profile = await aget_profile_by_user(user)

    profile_pic_url = None
    if profile.profile_pic:
        url = profile.profile_pic.url
        if "cloudinary" in url:
            url = url.replace("/upload/", "/upload/q_auto:eco,f_auto,w_800/")
        profile_pic_url = url

    return {
        "id": profile.id,
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
        },
        "age": profile.age,
        "sex": profile.sex,
        "bio": profile.bio,
        "phone_number": profile.phone_number,
        "profile_pic_url": profile_pic_url,
    }


async def aupdate_user_profile(user: User, data: dict, profile_pic_file=None) -> dict:
    """
    Updates profile details. Deletes old Cloudinary image if new image uploaded.
    """
    profile = await aget_profile_by_user(user)

    for attr, value in data.items():
        if value is not None:
            setattr(profile, attr, value)

    if profile_pic_file:
        def _handle_cloudinary_delete():
            if profile.profile_pic:
                try:
                    cloudinary.uploader.destroy(profile.profile_pic.name)
                except Exception as e:
                    logger.warning(f"Failed to delete old Cloudinary image: {e}")

        await sync_to_async(_handle_cloudinary_delete)()
        profile.profile_pic = profile_pic_file

    await profile.asave()
    return await aget_user_profile(user)
