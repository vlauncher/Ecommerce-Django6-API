from typing import Optional
from django.http import HttpResponseRedirect
from ninja import Router, File, Form, UploadedFile
from .schemas import (
    RegisterIn, VerifyOTPIn, LoginIn, ResendOTPIn,
    ForgotPasswordIn, ResetPasswordIn, ChangePasswordIn, RefreshTokenIn,
    MessageOut, TokenOut, UserProfileOut, DeleteAccountIn
)
from .auth import JWTAuth
from . import services
from .google_oauth import get_google_auth_url, agoogle_oauth_callback

auth_router = Router(tags=["Authentication"])
user_router = Router(tags=["User Profile"])


@auth_router.get("/google/login/", auth=None)
async def google_login(request):
    """
    Redirect to Google OAuth consent screen.
    """
    auth_url = get_google_auth_url()
    return HttpResponseRedirect(auth_url)


@auth_router.get("/google/callback/", auth=None, response={200: TokenOut})
async def google_callback(request, code: str):
    """
    Handle Google OAuth callback. Exchanges auth code for tokens,
    finds or creates user, and returns JWT tokens.
    """
    return await agoogle_oauth_callback(code)


@auth_router.post("/register", response={201: MessageOut})
async def register(request, payload: RegisterIn):
    """
    Register a new user account and dispatch 6-digit OTP to email.
    """
    await services.aregister_user(payload.model_dump())
    return 201, {"detail": "User registered successfully. Verification OTP sent to your email."}


@auth_router.post("/verify-otp", response={200: MessageOut})
async def verify_otp(request, payload: VerifyOTPIn):
    """
    Verify account using the 6-digit OTP code (only OTP passed in body).
    """
    await services.averify_registration_otp(payload.otp)
    return {"detail": "Account verified successfully. You can now log in."}


@auth_router.post("/login", response={200: TokenOut})
async def login(request, payload: LoginIn):
    """
    Authenticate user and return JWT access and refresh tokens.
    """
    return await services.alogin_user(payload.email, payload.password)


@auth_router.post("/refresh", response={200: TokenOut})
async def refresh_token(request, payload: RefreshTokenIn):
    """
    Refresh access token using valid refresh token.
    """
    return await services.arefresh_token(payload.refresh)


@auth_router.post("/resend-otp", response={200: MessageOut})
async def resend_otp(request, payload: ResendOTPIn):
    """
    Resend a fresh OTP to the user's email.
    """
    await services.aresend_otp(payload.email, payload.purpose)
    return {"detail": "A new OTP has been sent to your email."}


@auth_router.post("/forgot-password", response={200: MessageOut})
async def forgot_password(request, payload: ForgotPasswordIn):
    """
    Initiate forgot password flow by sending an OTP.
    """
    await services.ainitiate_forgot_password(payload.email)
    return {"detail": "If the email is registered, a password reset OTP has been sent."}


@auth_router.post("/reset-password", response={200: MessageOut})
async def reset_password(request, payload: ResetPasswordIn):
    """
    Reset password using the 6-digit OTP code.
    """
    await services.areset_password(payload.otp, payload.new_password, payload.confirm_password)
    return {"detail": "Password has been reset successfully. You can now log in with your new password."}


@auth_router.post("/change-password", auth=JWTAuth(), response={200: MessageOut})
async def change_password(request, payload: ChangePasswordIn):
    """
    Change password for authenticated user.
    """
    await services.achange_password(request.auth, payload.old_password, payload.new_password, payload.confirm_password)
    return {"detail": "Password changed successfully."}


@auth_router.delete("/account", auth=JWTAuth(), response={200: MessageOut})
async def delete_account(request, payload: DeleteAccountIn):
    await services.adelete_account(request.auth, payload.password)
    return {"detail": "Your account has been deactivated and anonymized."}


@user_router.get("/data-export", auth=JWTAuth())
async def export_account_data(request):
    from apps.commerce.models import Address, Order
    addresses = [{"id": item.id, "label": item.label, "recipient_name": item.recipient_name, "phone": item.phone, "line1": item.line1, "line2": item.line2, "city": item.city, "state": item.state, "country": item.country, "postal_code": item.postal_code} async for item in Address.objects.filter(user=request.auth)]
    orders = [{"id": item.id, "number": item.number, "status": item.status, "total_minor": item.total_minor, "currency": item.currency, "created_at": item.created_at} async for item in Order.objects.filter(user=request.auth)]
    return {"user": {"id": request.auth.id, "email": request.auth.email, "first_name": request.auth.first_name, "last_name": request.auth.last_name}, "addresses": addresses, "orders": orders}


@user_router.get("/profile", auth=JWTAuth(), response={200: UserProfileOut})
async def get_profile(request):
    """
    Get profile details for authenticated user.
    """
    return await services.aget_user_profile(request.auth)


@user_router.patch("/profile", auth=JWTAuth(), response={200: UserProfileOut})
async def update_profile(
    request,
    age: Optional[int] = Form(None),
    sex: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    profile_pic: Optional[UploadedFile] = File(None),
):
    """
    Update profile details. Profile pictures uploaded via Cloudinary are optimized to <= 200KB.
    """
    data = {
        "age": age,
        "sex": sex,
        "bio": bio,
        "phone_number": phone_number,
    }
    return await services.aupdate_user_profile(request.auth, data, profile_pic)
