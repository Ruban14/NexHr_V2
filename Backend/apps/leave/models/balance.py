"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeLeaveBalance(UUIDModel, TimeStampedModel, AuditedModel):
    """Stores current leave balance of an employee."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="employee_leave_balances",
    )

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name="leave_balances",
    )

    leave_type = models.ForeignKey('organization.LeaveType',
        on_delete=models.PROTECT,
        related_name="employee_balances",
    )

    allocated = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    used = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    balance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    class Meta:
        app_label = 'organization'
        db_table = "employee_leave_balances"
        unique_together = (
            "employee",
            "leave_type",
        )

    def __str__(self):
        return f"{self.employee} - {self.leave_type}"

