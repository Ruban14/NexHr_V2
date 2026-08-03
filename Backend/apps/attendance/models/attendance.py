"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class Attendance(UUIDModel, TimeStampedModel, AuditedModel):
    """Daily attendance summary."""

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        HALF_DAY = "half_day", "Half Day"
        LEAVE = "leave", "Leave"
        HOLIDAY = "holiday", "Holiday"
        WEEK_OFF = "week_off", "Week Off"

    class ApprovalStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not required"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="attendances",
    )

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name="attendances",
    )

    attendance_date = models.DateField()

    first_check_in = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_check_out = models.DateTimeField(
        null=True,
        blank=True,
    )

    total_worked_hours = models.DurationField(
        null=True,
        blank=True,
    )

    total_break_hours = models.DurationField(
        null=True,
        blank=True,
    )

    overtime_hours = models.DurationField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    is_manual = models.BooleanField(
        default=False,
        help_text='True when this day includes a manual entry pending or reviewed by a manager.',
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_REQUIRED,
        db_index=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_attendances',
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approval_remarks = models.TextField(
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "attendances"
        ordering = ["-attendance_date"]
        unique_together = (
            "employee",
            "attendance_date",
        )

    def __str__(self):
        return f"{self.employee} - {self.attendance_date}"

