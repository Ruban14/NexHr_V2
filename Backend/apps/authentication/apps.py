from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration for the authentication application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentication'

    def ready(self) -> None:
        """Import signal handlers when the app is ready."""
        from apps.authentication import signals  # noqa: F401, PLC0415
