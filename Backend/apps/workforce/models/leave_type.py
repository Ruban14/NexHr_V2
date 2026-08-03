"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class LeaveType(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization leave type."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="leave_types",
    )
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_leave_type_per_org",
            )
        ]

    def __str__(self):
        return self.name

