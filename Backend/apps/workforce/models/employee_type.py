"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeType(UUIDModel, TimeStampedModel, AuditedModel):
    """permanent, contract, intern, External, etc."""

    name = models.CharField(max_length=160, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

