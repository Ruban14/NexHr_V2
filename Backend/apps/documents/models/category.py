"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class DocumentCategory(UUIDModel, TimeStampedModel, AuditedModel):
    """Master document categories."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        db_table = "document_categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

