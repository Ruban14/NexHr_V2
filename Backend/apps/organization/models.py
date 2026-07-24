"""Organization master / lookup models and user profiles."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import AuditedModel, TimeStampedModel, UUIDModel


class IndustryType(UUIDModel, TimeStampedModel, AuditedModel):
    """Industry classification lookup for organizations."""

    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=160, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Designation(UUIDModel, TimeStampedModel, AuditedModel):
    """Job title / designation lookup."""

    industry_type = models.ForeignKey(
        IndustryType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='designations',
    )
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=160, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class EmployeeType(UUIDModel, TimeStampedModel, AuditedModel):
    """Employment nature lookup (permanent, contract, intern, ...)."""

    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=160, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class AccessType(UUIDModel, TimeStampedModel, AuditedModel):
    """Portal / system access type lookup."""

    industry_type = models.ForeignKey(
        IndustryType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='access_types',
    )
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=160, db_index=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


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
    industry_type = models.ForeignKey(
        IndustryType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='organizations',
    )
    organization_size = models.CharField(
        max_length=32,
        choices=OrganizationSize.choices,
        blank=True,
    )
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    logo = models.URLField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    currency = models.CharField(max_length=3, default='INR')
    is_active = models.BooleanField(default=True, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
    )

    class Meta:
        ordering = ['display_name']
        indexes = [
            models.Index(fields=['is_active', 'display_name']),
        ]

    def __str__(self) -> str:
        return self.display_name or self.legal_name


class UserProfile(UUIDModel, TimeStampedModel, AuditedModel):
    """Extended profile details for an authenticated user."""

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer not to say'

    class BloodGroup(models.TextChoices):
        A_POSITIVE = 'A+', 'A+'
        A_NEGATIVE = 'A-', 'A-'
        B_POSITIVE = 'B+', 'B+'
        B_NEGATIVE = 'B-', 'B-'
        AB_POSITIVE = 'AB+', 'AB+'
        AB_NEGATIVE = 'AB-', 'AB-'
        O_POSITIVE = 'O+', 'O+'
        O_NEGATIVE = 'O-', 'O-'
        UNKNOWN = 'unknown', 'Unknown'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    display_name = models.CharField(max_length=255, blank=True)
    profile_photo = models.URLField(blank=True)
    mobile_number = models.CharField(max_length=32, blank=True, db_index=True)
    alternate_mobile = models.CharField(max_length=32, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=32, choices=Gender.choices, blank=True)
    blood_group = models.CharField(max_length=16, choices=BloodGroup.choices, blank=True)

    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    mother_language = models.CharField(max_length=100, blank=True)
    languages_known = models.JSONField(default=list, blank=True)

    is_profile_completed = models.BooleanField(default=False, db_index=True)
    completed_status = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_profile_completed', 'completed_status']),
        ]

    def __str__(self) -> str:
        return self.display_name or str(self.user)


class OrganizationMembership(UUIDModel, TimeStampedModel, AuditedModel):
    """Links a user profile to an organization with role and employment details."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        PENDING = 'pending', 'Pending'
        EXITED = 'exited', 'Exited'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    employee_type = models.ForeignKey(
        EmployeeType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    access_type = models.ForeignKey(
        AccessType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    employee_code = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    joining_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user_profile'],
                name='uniq_org_membership_org_profile',
            ),
            models.UniqueConstraint(
                fields=['organization', 'employee_code'],
                condition=~models.Q(employee_code=''),
                name='uniq_org_membership_org_employee_code',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['user_profile', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.user_profile} @ {self.organization}'
