import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailService:
    """Centralized email service with HTML template rendering and plain text fallback."""

    @staticmethod
    def _send(subject: str, template_name: str, context: dict, to_email: str):
        """Render HTML template and send email with plain text alternative."""
        html_content = render_to_string(f"emails/{template_name}.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @classmethod
    def send_otp_email(cls, user, otp_code: str, template_name: str = "otp_verification"):
        """Send OTP verification or resend email."""
        context = {
            "user": user,
            "otp_code": otp_code,
            "expiry_minutes": settings.OTP_EXPIRY_MINUTES,
            "app_name": "Ecommerce",
            "year": datetime.datetime.now().year,
        }
        subject_map = {
            "otp_verification": "Verify Your Account",
            "otp_resend": "Your New Verification Code",
        }
        cls._send(
            subject=f"🔐 {subject_map.get(template_name, 'Verification Code')}",
            template_name=template_name,
            context=context,
            to_email=user.email,
        )

    @classmethod
    def send_welcome_email(cls, user):
        """Send welcome email upon successful account activation."""
        context = {
            "user": user,
            "app_name": "Ecommerce",
            "frontend_url": getattr(settings, "FRONTEND_URL", "#"),
            "year": datetime.datetime.now().year,
        }
        cls._send(
            subject="🎉 Welcome to Ecommerce!",
            template_name="welcome",
            context=context,
            to_email=user.email,
        )

    @classmethod
    def send_email(cls, subject: str, to_email: str, template_name: str = "welcome", context: dict = None):
        """Generic email dispatch method."""
        if context is None:
            context = {}
        context.setdefault("app_name", "Ecommerce")
        context.setdefault("year", datetime.datetime.now().year)
        cls._send(
            subject=subject,
            template_name=template_name,
            context=context,
            to_email=to_email,
        )

