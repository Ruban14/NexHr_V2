"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class AccessType(UUIDModel, TimeStampedModel, AuditedModel):
    """Admin, Employee, Manager"""

    industry_type = models.ForeignKey('organization.IndustryType',on_delete=models.CASCADE,null=True,blank=True,related_name='access_types')
    name = models.CharField(max_length=160, db_index=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

