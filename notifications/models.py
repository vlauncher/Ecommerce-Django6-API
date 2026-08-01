from django.db import models
from django.conf import settings
from common.models import TimeStampedModel


class Notification(TimeStampedModel):
    """User in-app and multi-channel notification log."""

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push Notification"
        IN_APP = "in_app", "In-App Notification"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.IN_APP
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.title} ({'Read' if self.is_read else 'Unread'})"
