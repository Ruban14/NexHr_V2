"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class Designation(UUIDModel, TimeStampedModel, AuditedModel):
    """Department designation with optional parent hierarchy."""

    department = models.ForeignKey('organization.Department',
        on_delete=models.CASCADE,
        related_name='designations',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    name = models.CharField(max_length=160, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['department', 'name'],
                name='uniq_designation_per_department',
            ),
        ]
        indexes = [
            models.Index(fields=['department', 'is_active'], name='organizatio_departm_desig_idx'),
            models.Index(fields=['parent', 'sort_order'], name='organizatio_parent_sort_idx'),
        ]

    def __str__(self) -> str:
        return self.name

