"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class DocumentDefinition(UUIDModel, TimeStampedModel, AuditedModel):
    """Defines available document types."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="document_definitions",
        null=True,
        blank=True,
    )

    category = models.ForeignKey('organization.DocumentCategory',
        on_delete=models.PROTECT,
        related_name="documents",
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        db_table = "document_definitions"
        ordering = ["category", "name"]
        unique_together = ("organization", "category", "name")

    def __str__(self):
        return self.name

