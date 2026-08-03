"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class AttendanceBreak(UUIDModel, TimeStampedModel, AuditedModel):
    """Breaks taken during a session."""

    session = models.ForeignKey('organization.AttendanceSession',
        on_delete=models.CASCADE,
        related_name="breaks",
    )

    break_start = models.DateTimeField()

    break_end = models.DateTimeField(
        null=True,
        blank=True,
    )

    break_duration = models.DurationField(
        null=True,
        blank=True,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "attendance_breaks"
        ordering = ["break_start"]

    def __str__(self):
        return (
            f"{self.session.attendance.employee} "
            f"- Break"
        )
