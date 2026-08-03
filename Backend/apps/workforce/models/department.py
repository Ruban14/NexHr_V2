"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class Department(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization department (flat list per organization)."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name='departments',
    )
    name = models.CharField(max_length=150, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='uniq_department_name_per_organization',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'is_active'], name='organizatio_organiz_dept_idx'),
        ]

    def __str__(self) -> str:
        return self.name

