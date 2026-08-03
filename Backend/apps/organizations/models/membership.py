"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class OrganizationMembership(UUIDModel, TimeStampedModel, AuditedModel):
    """Links a user to an organization branch with role and employment details."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        PENDING = 'pending', 'Pending'
        EXITED = 'exited', 'Exited'

    branch = models.ForeignKey('organization.OrganizationBranch', on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    designation = models.ForeignKey('organization.Designation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    employee_type = models.ForeignKey('organization.EmployeeType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    access_type = models.ForeignKey('organization.AccessType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    employee_code = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    joining_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)

    class Meta:
        app_label = 'organization'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'user'],
                name='uniq_org_membership_branch_user',
            ),
            models.UniqueConstraint(
                fields=['branch', 'employee_code'],
                condition=~models.Q(employee_code=''),
                name='uniq_org_membership_branch_employee_code',
            ),
        ]
        indexes = [
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    @property
    def organization(self):
        return self.branch.organization

    def __str__(self) -> str:
        return f'{self.user} @ {self.branch}'

