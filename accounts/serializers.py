from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "password_confirm")

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for validating OTP code during account activation."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for requesting a new OTP email."""
    email = serializers.EmailField()


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth token exchange."""
    id_token = serializers.CharField(help_text="Google ID token obtained from Google Sign-In on client")



class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom SimpleJWT token serializer using email instead of username."""
    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        return token


class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading user profile data."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "full_name", "is_active", "date_joined")
        read_only_fields = fields

    @extend_schema_field(serializers.CharField())
    def get_full_name(self, obj):
        return obj.full_name
