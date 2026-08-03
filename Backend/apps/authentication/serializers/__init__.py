"""Request and response serializers for authentication endpoints."""

from __future__ import annotations

from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    """Validate user registration input."""

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, min_length=9, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')


class LoginSerializer(serializers.Serializer):
    """Validate login credentials."""

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class RefreshSerializer(serializers.Serializer):
    """Validate refresh token input."""

    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Validate logout refresh token input."""

    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    """Validate forgot-password email input."""

    email = serializers.EmailField(max_length=254)


class ResetPasswordSerializer(serializers.Serializer):
    """Validate password reset input."""

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=9, trim_whitespace=False)


class VerifyEmailSerializer(serializers.Serializer):
    """Validate email verification token input."""

    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    """Validate resend verification email input."""

    email = serializers.EmailField(max_length=254)


class ChangePasswordSerializer(serializers.Serializer):
    """Validate authenticated password change input."""

    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    password = serializers.CharField(write_only=True, min_length=9, trim_whitespace=False)


class UserProfileSerializer(serializers.Serializer):
    """Read-only user profile representation."""

    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True, allow_null=True)
