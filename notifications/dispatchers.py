from abc import ABC, abstractmethod
from emails.services import EmailService
from notifications.models import Notification


class BaseNotificationDispatcher(ABC):
    @abstractmethod
    def send(self, user, title: str, message: str, **kwargs):
        pass


class EmailNotificationDispatcher(BaseNotificationDispatcher):
    """Dispatches HTML email via existing emails app EmailService."""

    def send(self, user, title: str, message: str, **kwargs):
        EmailService.send_email(
            subject=title,
            to_email=user.email,
            template_name="welcome",
            context={"first_name": user.first_name, "message": message},
        )



class InAppNotificationDispatcher(BaseNotificationDispatcher):
    """Creates persistent in-app notification DB record."""

    def send(self, user, title: str, message: str, **kwargs):
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            channel=Notification.Channel.IN_APP,
        )


class MultiChannelNotificationEngine:
    """Strategy Engine coordinating multi-channel notification dispatch."""

    dispatchers = [InAppNotificationDispatcher(), EmailNotificationDispatcher()]

    @classmethod
    def notify_user(cls, user, title: str, message: str, **kwargs):
        for dispatcher in cls.dispatchers:
            try:
                dispatcher.send(user, title, message, **kwargs)
            except Exception as e:
                # Log dispatch error without breaking request thread
                print(f"[Notification Engine] Dispatch error: {e}")
