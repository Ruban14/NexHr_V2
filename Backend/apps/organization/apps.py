from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.organization'
    label = 'organization'
    verbose_name = 'Organization'

    def ready(self) -> None:
        from apps.organization.admin_grouping import install_admin_grouping

        install_admin_grouping()
