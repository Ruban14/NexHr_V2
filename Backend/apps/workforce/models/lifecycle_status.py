"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeLifecycleStatus(UUIDModel, TimeStampedModel, AuditedModel):
    """Configurable employee lifecycle statuses (Draft, Active, …)."""

    name = models.CharField(max_length=120)
    key = models.SlugField(max_length=64, unique=True)
    ordinal = models.PositiveIntegerField(default=0, db_index=True)
    is_initial = models.BooleanField(default=False, db_index=True)
    is_terminal = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['ordinal', 'name']
        indexes = [
            models.Index(fields=['is_active', 'ordinal']),
        ]

    def __str__(self) -> str:
        return self.name

