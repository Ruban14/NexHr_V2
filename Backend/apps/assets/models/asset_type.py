"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class AssetType(UUIDModel, TimeStampedModel, AuditedModel):
    """Master list of asset types."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="asset_types",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        db_table = "asset_types"
        ordering = ["name"]
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name

