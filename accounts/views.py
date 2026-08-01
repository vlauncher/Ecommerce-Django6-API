from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import OTP
from .services import GoogleOAuthService
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    GoogleAuthSerializer,
    EmailTokenObtainPairSerializer,
    UserSerializer,
)
from .tasks import send_otp_email_task, send_welcome_email_task
from .throttles import OTPResendThrottle

User = get_user_model()


@extend_schema(
    tags=["Authentication"],
    summary="Register User Account",
    description="Registers a new user (inactive) and enqueues a 6-digit OTP email verification code.",
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate OTP and enqueue background email task
        otp = OTP.generate_for_user(user)
        send_otp_email_task.enqueue(
            user_id=user.id,
            otp_code=otp.code,
            template_name="otp_verification",
        )

        return Response(
            {
                "detail": "Registration successful. Please check your email for the verification code.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Verify Email with OTP",
    description="Validates the 6-digit OTP code, activates user account, sends welcome email, and returns JWT tokens.",
)
class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp_code = serializer.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = (
            OTP.objects.filter(user=user, code=otp_code, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp or not otp.is_valid:
            return Response(
                {"detail": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark OTP used and activate user
        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user.is_active = True
        user.save(update_fields=["is_active"])

        # Enqueue welcome email task
        send_welcome_email_task.enqueue(user_id=user.id)

        # Issue JWT tokens
        refresh = EmailTokenObtainPairSerializer.get_token(user)

        return Response(
            {
                "detail": "Account verified successfully.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Resend Verification OTP",
    description="Resends a fresh 6-digit OTP verification code to pending user accounts. Rate-limited to 3 requests/minute.",
)
class ResendOTPView(generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = (AllowAny,)
    throttle_classes = (OTPResendThrottle,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email, is_active=False)
            otp = OTP.generate_for_user(user)
            send_otp_email_task.enqueue(
                user_id=user.id,
                otp_code=otp.code,
                template_name="otp_resend",
            )
        except User.DoesNotExist:
            # Silently pass to prevent enumeration
            pass

        return Response(
            {"detail": "If an account with that email exists and is pending verification, a new OTP has been sent."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Authentication"],
    summary="User Login (Email & Password)",
    description="Authenticates active user with email & password, returning access and refresh JWT tokens.",
)
class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@extend_schema(
    tags=["Authentication"],
    summary="Refresh Access Token",
    description="Obtains a new access token using a valid refresh token.",
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Get Authenticated User Profile",
    description="Retrieves the current authenticated user's profile details.",
)
class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Authentication"],
    summary="Google OAuth 2.0 Login",
    description="Exchanges Google ID token for SimpleJWT access & refresh tokens. Automatically creates or activates account.",
)
class GoogleLoginView(generics.GenericAPIView):
    serializer_class = GoogleAuthSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_string = serializer.validated_data["id_token"]
        id_info = GoogleOAuthService.verify_token(token_string)

        email = id_info.get("email")
        if not email:
            return Response(
                {"detail": "Email not provided by Google OAuth payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        first_name = id_info.get("given_name", id_info.get("name", "Google User"))
        last_name = id_info.get("family_name", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
            },
        )

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        # Generate JWT tokens
        refresh = EmailTokenObtainPairSerializer.get_token(user)

        return Response(
            {
                "detail": "Google login successful.",
                "created": created,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )
