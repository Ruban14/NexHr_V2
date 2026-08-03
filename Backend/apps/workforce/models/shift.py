"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class Shift(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization shift."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name='shifts',
    )

    name = models.CharField(max_length=150)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_shift_name_per_org",
            )
        ]

    def __str__(self):
        return self.name

