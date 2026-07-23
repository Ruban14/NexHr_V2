"""Django admin registrations for authentication models."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.authentication.models import (
    EmailVerification,
    LoginAttempt,
    LoginHistory,
    PasswordReset,
    User,
    UserSession,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User."""

    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_email_verified', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_email_verified')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login', 'locked_until')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        (
            'Status',
            {'fields': ('is_active', 'is_email_verified', 'is_staff', 'is_superuser', 'locked_until')},
        ),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
            },
        ),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession."""

    list_display = ('user', 'device_type', 'browser', 'os', 'is_active', 'last_used_at', 'expires_at')
    list_filter = ('is_active', 'device_type')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at', 'refresh_token_hash')


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin interface for LoginHistory."""

    list_display = ('email', 'event_type', 'ip_address', 'device_name', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('email', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """Admin interface for EmailVerification."""

    list_display = ('user', 'is_active', 'expires_at', 'used_at', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'token_hash')


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """Admin interface for PasswordReset."""

    list_display = ('user', 'is_active', 'expires_at', 'used_at', 'requested_ip', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'token_hash')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Admin interface for LoginAttempt."""

    list_display = ('email', 'ip_address', 'succeeded', 'created_at')
    list_filter = ('succeeded',)
    search_fields = ('email', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at')
