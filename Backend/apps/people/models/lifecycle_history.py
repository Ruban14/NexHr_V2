"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel


class EmployeeLifecycleHistory(UUIDModel, TimeStampedModel):
    """Immutable audit trail of employee lifecycle movements."""

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name='lifecycle_history',
    )
    from_status = models.ForeignKey('organization.EmployeeLifecycleStatus',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='history_as_from',
    )
    to_status = models.ForeignKey('organization.EmployeeLifecycleStatus',
        on_delete=models.CASCADE,
        related_name='history_as_to',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_lifecycle_changes',
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    remarks = models.TextField(blank=True, default='')

    class Meta:
        app_label = 'organization'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['employee', 'changed_at']),
        ]
        default_permissions = ('add', 'view', 'delete')

    def __str__(self) -> str:
        return f'{self.employee_id}: {self.from_status_id} → {self.to_status_id}'

    def delete(self, using=None, keep_parents=False):
        raise PermissionError('Lifecycle history is immutable and cannot be deleted.')

