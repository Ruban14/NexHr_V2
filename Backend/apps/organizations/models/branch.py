"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel


class OrganizationBranch(UUIDModel, TimeStampedModel):
    """Organization branch / location."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    organization = models.ForeignKey('organization.Organization',on_delete=models.CASCADE,related_name='branches')
    branch_code = models.CharField(max_length=32)
    branch_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_headquarters = models.BooleanField(default=False)
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.ACTIVE,db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['-is_headquarters', 'branch_name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'branch_code'],
                name='uniq_organization_branch_code',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.branch_name} ({self.organization.organization_code})'

