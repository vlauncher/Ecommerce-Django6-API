from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("verify-otp/", views.VerifyOTPView.as_view(), name="verify_otp"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("resend-otp/", views.ResendOTPView.as_view(), name="resend_otp"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset_password"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("refresh/", views.TokenRefreshView.as_view(), name="token_refresh"),
]
