"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class DocumentPolicy(UUIDModel, TimeStampedModel, AuditedModel):
    """Document policy for an employee type."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="document_policies",
    )

    employee_type = models.ForeignKey('organization.EmployeeType',
        on_delete=models.PROTECT,
        related_name="document_policies",
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        db_table = "document_policies"
        ordering = ["name"]
        unique_together = ("organization", "employee_type", "name")

    def __str__(self):
        return self.name

