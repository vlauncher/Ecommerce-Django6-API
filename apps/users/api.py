from typing import Optional
from ninja import Router, File, Form, UploadedFile
from .schemas import (
    RegisterIn, VerifyOTPIn, LoginIn, ResendOTPIn,
    ForgotPasswordIn, ResetPasswordIn, ChangePasswordIn, RefreshTokenIn,
    MessageOut, TokenOut, UserProfileOut
)
from .auth import JWTAuth
from . import services

auth_router = Router(tags=["Authentication"])
user_router = Router(tags=["User Profile"])


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
