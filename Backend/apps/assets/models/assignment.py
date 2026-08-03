"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeAssetAssignment(UUIDModel, TimeStampedModel, AuditedModel):
    """History of asset assignments."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RETURNED = "returned", "Returned"
        LOST = "lost", "Lost"

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="asset_assignments",
    )

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name="asset_assignments",
    )

    asset = models.ForeignKey('organization.Asset',
        on_delete=models.PROTECT,
        related_name="assignments",
    )

    assigned_at = models.DateField()

    expected_return_at = models.DateField(
        null=True,
        blank=True,
    )

    returned_at = models.DateField(
        null=True,
        blank=True,
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_assets",
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_assets",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    remarks = models.TextField(blank=True)

    class Meta:
        app_label = 'organization'
        db_table = "employee_asset_assignments"
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["organization", "employee"]),
            models.Index(fields=["asset"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} -> {self.employee}"

