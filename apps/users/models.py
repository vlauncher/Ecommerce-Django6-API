from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from cloudinary_storage.storage import MediaCloudinaryStorage
from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using email as the primary identifier.
    """
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class UserProfile(models.Model):
    """
    Extended user profile for storing personal metadata and profile picture.
    """
    class SexChoices(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.PositiveIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SexChoices.choices, blank=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_pic = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        null=True,
        storage=MediaCloudinaryStorage(),
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
