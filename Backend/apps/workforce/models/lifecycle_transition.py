"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeLifecycleTransition(UUIDModel, TimeStampedModel, AuditedModel):
    """Allowed edges between lifecycle statuses (e.g. Draft → Onboarding Started)."""

    from_status = models.ForeignKey('organization.EmployeeLifecycleStatus',
        on_delete=models.CASCADE,
        related_name='outgoing_transitions',
    )
    to_status = models.ForeignKey('organization.EmployeeLifecycleStatus',
        on_delete=models.CASCADE,
        related_name='incoming_transitions',
    )
    action_label = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['sort_order', 'action_label']
        constraints = [
            models.UniqueConstraint(
                fields=['from_status', 'to_status'],
                name='uniq_lifecycle_transition_from_to',
            ),
        ]
        indexes = [
            models.Index(fields=['from_status', 'is_active']),
        ]

    def __str__(self) -> str:
        return f'{self.from_status} → {self.to_status}'

