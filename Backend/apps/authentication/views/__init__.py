"""Authentication API views."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.authentication.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
)
from apps.authentication.services.auth import AuthService
from apps.authentication.services.device import parse_device_info
from apps.authentication.services.email_verification import EmailVerificationService
from apps.authentication.services.password import PasswordService
from apps.authentication.throttles import AuthAnonRateThrottle, AuthUserRateThrottle
from apps.core.responses import success_response


class RegisterView(APIView):
    """Register a new user account."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register(**serializer.validated_data)
        return success_response(
            data=AuthService.build_register_response(user),
            message='Registration successful. Please verify your email.',
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate and issue JWT tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = parse_device_info(request)
        result = AuthService.login(device=device, **serializer.validated_data)
        return success_response(
            data=AuthService.build_login_response(result),
            message='Login successful.',
        )


class LogoutView(APIView):
    """Invalidate refresh token and session."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthUserRateThrottle]

    def post(self, request: Request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = parse_device_info(request)
        AuthService.logout(refresh_token=serializer.validated_data['refresh'], device=device)
        return success_response(message='Logout successful.')


class RefreshView(APIView):
    """Rotate JWT refresh token."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = parse_device_info(request)
        tokens = AuthService.refresh(refresh_token=serializer.validated_data['refresh'], device=device)
        return success_response(
            data=AuthService.build_token_response(tokens),
            message='Token refreshed.',
        )


class ForgotPasswordView(APIView):
    """Request a password reset email."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = parse_device_info(request)
        message = PasswordService.request_reset(
            email=serializer.validated_data['email'],
            ip_address=device.ip_address,
        )
        return success_response(message=message)


class ResetPasswordView(APIView):
    """Reset password using a bearer token."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PasswordService.reset_password(
            raw_token=serializer.validated_data['token'],
            new_password=serializer.validated_data['password'],
        )
        return success_response(message='Password reset successful.')


class ChangePasswordView(APIView):
    """Change password for the authenticated user."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthUserRateThrottle]

    def post(self, request: Request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = PasswordService.change_password(
            user=request.user,
            current_password=serializer.validated_data['current_password'],
            new_password=serializer.validated_data['password'],
        )
        return success_response(
            data=AuthService.get_profile(user),
            message='Password updated successfully.',
        )


class VerifyEmailView(APIView):
    """Verify a user's email address."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = EmailVerificationService.verify(serializer.validated_data['token'])
        return success_response(
            data=AuthService.get_profile(user),
            message='Email verified successfully.',
        )


class ResendVerificationView(APIView):
    """Resend the email verification link."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        EmailVerificationService.resend(email=serializer.validated_data['email'])
        return success_response(
            message='If the account exists and is unverified, a verification email has been sent.',
        )


class MeView(APIView):
    """Return the authenticated user's profile."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthUserRateThrottle]

    def get(self, request: Request):
        return success_response(
            data=AuthService.get_profile(request.user),
            message='Profile retrieved.',
        )
