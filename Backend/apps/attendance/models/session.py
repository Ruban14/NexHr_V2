"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class AttendanceSession(UUIDModel, TimeStampedModel, AuditedModel):
    """Each check-in/check-out session."""

    class Source(models.TextChoices):
        WEB = "web", "Web"
        MOBILE = "mobile", "Mobile"
        BIOMETRIC = "biometric", "Biometric"
        RFID = "rfid", "RFID"
        MANUAL = "manual", "Manual"
        API = "api", "API"

    attendance = models.ForeignKey('organization.Attendance',
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    check_in = models.DateTimeField()

    check_out = models.DateTimeField(
        null=True,
        blank=True,
    )

    worked_hours = models.DurationField(
        null=True,
        blank=True,
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WEB,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "attendance_sessions"
        ordering = ["check_in"]

    def __str__(self):
        return (
            f"{self.attendance.employee} "
            f"- Session"
        )

