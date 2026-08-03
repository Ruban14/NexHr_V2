"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeLeaveLog(UUIDModel, TimeStampedModel, AuditedModel):
    """Audit log for every leave balance change."""

    class TransactionType(models.TextChoices):
        ALLOCATION = "allocation", "Allocation"
        LEAVE_APPROVED = "leave_approved", "Leave Approved"
        LEAVE_CANCELLED = "leave_cancelled", "Leave Cancelled"
        ADJUSTMENT = "adjustment", "Adjustment"
        CARRY_FORWARD = "carry_forward", "Carry Forward"

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="leave_logs",
    )

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name="leave_logs",
    )

    leave_type = models.ForeignKey('organization.LeaveType',
        on_delete=models.PROTECT,
        related_name="leave_logs",
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
    )

    quantity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    balance_before = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    balance_after = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    leave_application = models.ForeignKey('organization.LeaveApplication',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "employee_leave_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.transaction_type}"

