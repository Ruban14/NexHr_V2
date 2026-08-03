"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeBankDetail(UUIDModel, TimeStampedModel, AuditedModel):
    """Salary / payroll bank account linked to an employee."""

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name='bank_details',
    )
    account_holder_name = models.CharField(max_length=150, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)

    class Meta:
        app_label = 'organization'
        ordering = ['-is_primary', 'created_at']
        verbose_name = 'Employee bank detail'
        verbose_name_plural = 'Employee bank details'
        constraints = [
            models.UniqueConstraint(
                fields=['employee'],
                condition=models.Q(is_primary=True),
                name='uniq_primary_bank_per_employee',
            ),
        ]
        indexes = [
            models.Index(fields=['employee', 'is_primary']),
        ]

    def __str__(self) -> str:
        label = self.bank_name or self.account_number or 'Bank account'
        return f'{self.employee_id}: {label}'

