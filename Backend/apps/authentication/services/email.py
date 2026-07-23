"""Email delivery for authentication workflows."""

from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class EmailService:
    """Send transactional authentication emails."""

    @staticmethod
    def _send_branded_email(
        *,
        subject: str,
        recipient_email: str,
        text_template: str,
        html_template: str,
        context: dict,
    ) -> None:
        """Send a multipart email with HTML and plain-text versions."""
        text_body = render_to_string(text_template, context).strip()
        html_body = render_to_string(html_template, context).strip()

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=settings.EMAIL_FAIL_SILENTLY)

    @staticmethod
    def send_verification_email(*, email: str, token: str) -> None:
        """Send an email verification link."""
        verify_url = f'{settings.FRONTEND_URL}/auth/verify-email?token={token}'
        context = {
            'verify_url': verify_url,
            'expiry_hours': settings.AUTH_EMAIL_VERIFICATION_HOURS,
        }
        EmailService._send_branded_email(
            subject='Verify your NexHr account',
            recipient_email=email,
            text_template='authentication/emails/verify_email.txt',
            html_template='authentication/emails/verify_email.html',
            context=context,
        )

    @staticmethod
    def send_password_reset_email(*, email: str, token: str) -> None:
        """Send a password reset link."""
        reset_url = f'{settings.FRONTEND_URL}/auth/reset-password?token={token}'
        context = {
            'reset_url': reset_url,
            'expiry_hours': settings.AUTH_PASSWORD_RESET_HOURS,
        }
        EmailService._send_branded_email(
            subject='Reset your NexHr password',
            recipient_email=email,
            text_template='authentication/emails/reset_password.txt',
            html_template='authentication/emails/reset_password.html',
            context=context,
        )
