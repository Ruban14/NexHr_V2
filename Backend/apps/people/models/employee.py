"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class Employee(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization employee record (profile + employment + lifecycle)."""

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

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name='employees',
    )
    branch = models.ForeignKey('organization.OrganizationBranch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employee_records',
    )
    lifecycle_status = models.ForeignKey('organization.EmployeeLifecycleStatus',
        on_delete=models.CASCADE,
        related_name='employees',
    )
    employee_code = models.CharField(max_length=64, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    profile_photo = models.FileField(upload_to='employee_photos/', blank=True)
    mobile_number = models.CharField(max_length=32, blank=True, db_index=True)
    alternate_mobile = models.CharField(max_length=32, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=32, blank=True)
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
    designation = models.ForeignKey('organization.Designation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    employee_type = models.ForeignKey('organization.EmployeeType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    access_type = models.ForeignKey('organization.AccessType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    reporting_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        help_text='Manager who approves leave and similar requests for this employee.',
    )
    joining_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'employee_code'],
                condition=~models.Q(employee_code=''),
                name='uniq_employee_code_per_organization',
            ),
            models.UniqueConstraint(
                fields=['organization', 'email'],
                condition=~models.Q(email=''),
                name='uniq_employee_email_per_organization',
            ),
            models.UniqueConstraint(
                fields=['organization', 'user'],
                condition=models.Q(user__isnull=False),
                name='uniq_employee_user_per_organization',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'lifecycle_status']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_profile_completed', 'completed_status']),
        ]

    def __str__(self) -> str:
        return self.display_name or self.email or str(self.id)

