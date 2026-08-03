"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class Organization(UUIDModel, TimeStampedModel, AuditedModel):
    """Primary tenant / company record."""

    class OrganizationSize(models.TextChoices):
        SIZE_1_10 = '1-10', '1-10'
        SIZE_11_50 = '11-50', '11-50'
        SIZE_51_200 = '51-200', '51-200'
        SIZE_201_500 = '201-500', '201-500'
        SIZE_500_PLUS = '500+', '500+'

    organization_code = models.CharField(max_length=64, unique=True, db_index=True)
    legal_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, db_index=True)
    industry_type = models.ForeignKey('organization.IndustryType',on_delete=models.CASCADE,null=True,blank=True,related_name='organizations')
    organization_size = models.CharField(max_length=32,choices=OrganizationSize.choices,blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    logo = models.TextField(blank=True, default='')
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    currency = models.CharField(max_length=3, default='INR')
    notice_period_days = models.PositiveIntegerField(
        default=30,
        help_text='Default notice period duration in days used to calculate exit date.',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='owned_organizations')

    class Meta:
        app_label = 'organization'
        ordering = ['display_name']
        indexes = [
            models.Index(fields=['is_active', 'display_name']),
        ]

    def __str__(self) -> str:
        return self.display_name or self.legal_name

