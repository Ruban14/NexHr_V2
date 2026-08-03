"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class LeaveApplication(UUIDModel, TimeStampedModel, AuditedModel):
    """Employee leave request."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="leave_applications",
    )

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name="leave_applications",
    )

    leave_type = models.ForeignKey('organization.LeaveType',
        on_delete=models.PROTECT,
        related_name="applications",
    )

    from_date = models.DateField()

    to_date = models.DateField()

    number_of_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    is_half_day = models.BooleanField(
        default=False,
    )

    reason = models.TextField()

    attachment = models.FileField(
        upload_to="leave_attachments/",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "leave_applications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.leave_type}"

