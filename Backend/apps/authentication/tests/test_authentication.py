"""Authentication API and service tests."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import EmailVerification, LoginHistory, PasswordReset, User, UserSession
from apps.authentication.services.auth import AuthService
from apps.authentication.services.device import DeviceInfo
from apps.authentication.services.email_verification import EmailVerificationService
from apps.authentication.services.login_attempt import LoginAttemptService
from apps.authentication.services.password import PasswordService
from apps.core.crypto import generate_secure_token, hash_token
from apps.core.exceptions import AccountLockedError, ConflictServiceError, InvalidCredentialsError


TEST_DEVICE = DeviceInfo(
    device_name='Test Device',
    device_type='desktop',
    browser='Chrome',
    os='Mac OS X',
    ip_address='127.0.0.1',
    user_agent='Mozilla/5.0 Test',
)


@override_settings(
    AUTH_MAX_LOGIN_ATTEMPTS=3,
    AUTH_LOCKOUT_WINDOW_MINUTES=15,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class AuthenticationIntegrationTests(TestCase):
    """End-to-end API tests for authentication flows."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.register_url = '/api/auth/register'
        self.login_url = '/api/auth/login'
        self.logout_url = '/api/auth/logout'
        self.refresh_url = '/api/auth/refresh'
        self.me_url = '/api/auth/me'
        self.forgot_password_url = '/api/auth/forgot-password'
        self.reset_password_url = '/api/auth/reset-password'
        self.verify_email_url = '/api/auth/verify-email'
        self.resend_verification_url = '/api/auth/resend-verification'
        self.password = 'SecurePass123!'

    def _register_payload(self, email: str = 'user@example.com') -> dict[str, str]:
        return {
            'email': email,
            'password': self.password,
            'first_name': 'Test',
            'last_name': 'User',
        }

    def _create_verified_user(self, email: str, password: str | None = None) -> User:
        user = User.objects.create_user(email=email, password=password or self.password)
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        return user

    def test_register_returns_envelope_and_sends_verification_email(self) -> None:
        response = self.client.post(self.register_url, self._register_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertNotIn('tokens', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], 'user@example.com')
        self.assertFalse(response.data['data']['user']['is_email_verified'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(User.objects.count(), 1)

    def test_register_duplicate_email_returns_conflict(self) -> None:
        self.client.post(self.register_url, self._register_payload(), format='json')
        response = self.client.post(self.register_url, self._register_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(response.data['success'])

    def test_login_success_creates_session_and_history(self) -> None:
        self._create_verified_user(email='login@example.com')
        response = self.client.post(
            self.login_url,
            {'email': 'login@example.com', 'password': self.password},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(UserSession.objects.count(), 1)
        self.assertEqual(
            LoginHistory.objects.filter(event_type=LoginHistory.EventType.LOGIN_SUCCESS).count(),
            1,
        )

    def test_login_invalid_credentials_are_generic(self) -> None:
        self._create_verified_user(email='login@example.com')
        response = self.client.post(
            self.login_url,
            {'email': 'login@example.com', 'password': 'WrongPassword123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], 'Invalid email or password.')
        self.assertEqual(response.data['errors']['code'], 'invalid_credentials')

    def test_login_blocks_unverified_email(self) -> None:
        User.objects.create_user(email='pending@example.com', password=self.password)
        response = self.client.post(
            self.login_url,
            {'email': 'pending@example.com', 'password': self.password},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], 'Please verify your email address before signing in.')
        self.assertEqual(response.data['errors']['code'], 'email_not_verified')

    def test_me_requires_authentication(self) -> None:
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile_for_authenticated_user(self) -> None:
        user = User.objects.create_user(email='me@example.com', password=self.password)
        self.client.force_authenticate(user=user)
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['email'], 'me@example.com')

    def test_refresh_rotates_tokens(self) -> None:
        user = self._create_verified_user(email='refresh@example.com')
        login = AuthService.login(email=user.email, password=self.password, device=TEST_DEVICE)
        old_refresh = login.tokens.refresh

        response = self.client.post(self.refresh_url, {'refresh': old_refresh}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['data']['refresh'], old_refresh)

    def test_logout_deactivates_session(self) -> None:
        user = self._create_verified_user(email='logout@example.com')
        login = AuthService.login(email=user.email, password=self.password, device=TEST_DEVICE)
        session = UserSession.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.tokens.access}')

        response = self.client.post(self.logout_url, {'refresh': login.tokens.refresh}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertFalse(session.is_active)

    def test_forgot_password_generic_response_for_unknown_email(self) -> None:
        response = self.client.post(
            self.forgot_password_url,
            {'email': 'missing@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('If an account exists', response.data['message'])
        self.assertEqual(len(mail.outbox), 0)

    def test_forgot_password_sends_email_for_existing_user(self) -> None:
        User.objects.create_user(email='reset@example.com', password=self.password)
        response = self.client.post(
            self.forgot_password_url,
            {'email': 'reset@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(PasswordReset.objects.count(), 1)

    def test_reset_password_with_valid_token(self) -> None:
        user = User.objects.create_user(email='reset@example.com', password=self.password)
        raw_token = generate_secure_token()
        PasswordReset.objects.create(
            user=user,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(hours=1),
        )
        new_password = 'AnotherSecure1!'

        response = self.client.post(
            self.reset_password_url,
            {'token': raw_token, 'password': new_password},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))

    def test_verify_email_marks_user_verified(self) -> None:
        user = User.objects.create_user(email='verify@example.com', password=self.password)
        raw_token = generate_secure_token()
        EmailVerification.objects.create(
            user=user,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(self.verify_email_url, {'token': raw_token}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_resend_verification_for_unverified_user(self) -> None:
        User.objects.create_user(email='resend@example.com', password=self.password)
        response = self.client.post(
            self.resend_verification_url,
            {'email': 'resend@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)


@override_settings(
    AUTH_MAX_LOGIN_ATTEMPTS=2,
    AUTH_LOCKOUT_WINDOW_MINUTES=15,
    AUTH_LOCKOUT_DURATION_MINUTES=15,
)
class LoginAttemptServiceTests(TestCase):
    """Service-layer brute-force protection tests."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(email='locked@example.com', password='SecurePass123!')
        self.user.is_email_verified = True
        self.user.save(update_fields=['is_email_verified'])
        self.device = TEST_DEVICE

    def test_account_lock_after_repeated_failures(self) -> None:
        with self.assertRaises(InvalidCredentialsError):
            AuthService.login(email=self.user.email, password='WrongPassword123!', device=self.device)
        with self.assertRaises(InvalidCredentialsError):
            AuthService.login(email=self.user.email, password='WrongPassword123!', device=self.device)

        # Same IP is throttled; the account itself is not locked by a single IP.
        with self.assertRaises(AccountLockedError):
            AuthService.login(email=self.user.email, password='SecurePass123!', device=self.device)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_locked)

    def test_account_locked_error_includes_forgot_password_recovery(self) -> None:
        with self.assertRaises(InvalidCredentialsError):
            AuthService.login(email=self.user.email, password='WrongPassword123!', device=self.device)
        with self.assertRaises(InvalidCredentialsError):
            AuthService.login(email=self.user.email, password='WrongPassword123!', device=self.device)

        with self.assertRaises(AccountLockedError) as context:
            AuthService.login(email=self.user.email, password='SecurePass123!', device=self.device)

        self.assertEqual(context.exception.details.get('throttle_scope'), 'ip')
        self.assertIn('retry_after_minutes', context.exception.details)

    def test_multi_ip_failures_lock_account(self) -> None:
        other = DeviceInfo(
            device_name='Other',
            device_type='desktop',
            browser='Firefox',
            os='Linux',
            ip_address='10.0.0.2',
            user_agent='Other Agent',
        )
        with self.assertRaises(InvalidCredentialsError):
            AuthService.login(email=self.user.email, password='WrongPassword123!', device=self.device)
        with self.assertRaises(InvalidCredentialsError):
            AuthService.login(email=self.user.email, password='WrongPassword123!', device=other)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)

    def test_password_reset_unlocks_locked_account(self) -> None:
        lock_until = timezone.now() + timedelta(minutes=15)
        self.user.lock(lock_until)
        LoginAttemptService.record_attempt(
            email=self.user.email,
            ip_address=self.device.ip_address,
            succeeded=False,
        )

        raw_token = generate_secure_token()
        PasswordReset.objects.create(
            user=self.user,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(hours=1),
        )

        PasswordService.reset_password(raw_token=raw_token, new_password='AnotherSecure1!')
        self.user.refresh_from_db()

        self.assertFalse(self.user.is_locked)
        self.assertTrue(self.user.check_password('AnotherSecure1!'))
        AuthService.login(email=self.user.email, password='AnotherSecure1!', device=self.device)


class AuthServiceUnitTests(TestCase):
    """Focused unit tests for AuthService behavior."""

    def test_register_conflict_when_email_exists(self) -> None:
        User.objects.create_user(email='exists@example.com', password='SecurePass123!')
        with self.assertRaises(ConflictServiceError):
            AuthService.register(
                email='exists@example.com',
                password='SecurePass123!',
            )

    @patch('apps.authentication.services.email_verification.EmailService.send_verification_email')
    def test_email_verification_invalidates_previous_tokens(self, _mock_send) -> None:
        user = User.objects.create_user(email='token@example.com', password='SecurePass123!')
        EmailVerificationService.create_and_send(user)
        first_count = EmailVerification.objects.filter(user=user, is_active=True).count()
        EmailVerificationService.create_and_send(user)
        second_count = EmailVerification.objects.filter(user=user, is_active=True).count()

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 1)

    def test_password_reset_generic_message(self) -> None:
        message = PasswordService.request_reset(email='unknown@example.com', ip_address='127.0.0.1')
        self.assertEqual(message, PasswordService.GENERIC_FORGOT_MESSAGE)
