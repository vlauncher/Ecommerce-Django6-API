from django.tasks import task
from django.contrib.auth import get_user_model

User = get_user_model()


@task(queue_name="emails", priority=5)
def send_otp_email_task(user_id: int, otp_code: str, template_name: str):
    """Background task to send OTP email."""
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


@task(queue_name="emails", priority=3)
def send_welcome_email_task(user_id: int):
    """Background task to send welcome email upon account verification."""
    from emails.services import EmailService

    try:
        user = User.objects.get(id=user_id)
        EmailService.send_welcome_email(user=user)
    except User.DoesNotExist:
        pass
