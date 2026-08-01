from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(name="send_otp_email_task")
def send_otp_email_task(user_id: int, otp_code: str, template_name: str = "otp_verification"):
    """Celery task to dispatch OTP verification email via Gmail SMTP."""
    from emails.services import EmailService

    try:
        user = User.objects.get(id=user_id)
        EmailService.send_otp_email(
            user=user,
            otp_code=otp_code,
            template_name=template_name,
        )
    except User.DoesNotExist:
        pass


@shared_task(name="send_welcome_email_task")
def send_welcome_email_task(user_id: int):
    """Celery task to dispatch welcome email upon account activation."""
    from emails.services import EmailService

    try:
        user = User.objects.get(id=user_id)
        EmailService.send_welcome_email(user=user)
    except User.DoesNotExist:
        pass

