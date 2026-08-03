"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class File(UUIDModel, TimeStampedModel, AuditedModel):
    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="files",
    )
    file = models.FileField(upload_to="documents/%Y/%m/")
    original_name = models.CharField(max_length=255)
    extension = models.CharField(max_length=20)
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    checksum = models.CharField(
        max_length=64,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        app_label = 'organization'
        db_table = "files"

    def __str__(self):
        return self.original_name

