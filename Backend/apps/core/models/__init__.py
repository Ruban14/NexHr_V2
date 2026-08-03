"""Abstract base models shared across NexHr applications."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    """Abstract model that uses a UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract model with created and updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditedModel(models.Model):
    """Abstract model that tracks which users created and last updated a row."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='created_%(class)ss',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='updated_%(class)ss',
    )

    class Meta:
        abstract = True
