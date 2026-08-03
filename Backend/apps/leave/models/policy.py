"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class LeavePolicy(UUIDModel, TimeStampedModel, AuditedModel):
    """Leave policy assigned to an employee type."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="leave_policies",
    )

    employee_type = models.ForeignKey('organization.EmployeeType',
        on_delete=models.PROTECT,
        related_name="leave_policies",
    )

    code = models.CharField(
        max_length=30,
    )

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    is_default = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "leave_policies"
        ordering = ["name"]
        unique_together = (
            "organization",
            "code",
        )

    def __str__(self):
        return self.name

