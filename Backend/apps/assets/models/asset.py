"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class Asset(UUIDModel, TimeStampedModel, AuditedModel):
    """Physical or logical asset owned by an organization."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ASSIGNED = "assigned", "Assigned"
        LOST = "lost", "Lost"
        DAMAGED = "damaged", "Damaged"
        RETIRED = "retired", "Retired"

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="assets",
    )

    asset_type = models.ForeignKey('organization.AssetType',
        on_delete=models.PROTECT,
        related_name="assets",
    )

    asset_code = models.CharField(
        max_length=50,
        help_text="Unique organization asset code.",
    )

    name = models.CharField(
        max_length=150,
        help_text="Example: Dell Latitude 5440",
    )

    brand = models.CharField(
        max_length=100,
        blank=True,
    )

    model = models.CharField(
        max_length=100,
        blank=True,
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
    )

    purchase_date = models.DateField(
        null=True,
        blank=True,
    )

    warranty_expiry = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        db_table = "assets"
        ordering = ["asset_code"]
        unique_together = (
            "organization",
            "asset_code",
        )

    def __str__(self):
        return self.asset_code

