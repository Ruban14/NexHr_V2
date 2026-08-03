"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class HolidayCalendar(UUIDModel, TimeStampedModel, AuditedModel):
    """Holiday calendar."""

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="holiday_calendars",
    )
    name = models.CharField(max_length=150)
    year = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        ordering = ["-year", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name", "year"],
                name="uniq_holiday_calendar_per_org",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.year})"


class Holiday(UUIDModel, TimeStampedModel, AuditedModel):
    """Holiday inside a calendar."""

    holiday_calendar = models.ForeignKey(
        HolidayCalendar,
        on_delete=models.CASCADE,
        related_name="holidays",
    )
    name = models.CharField(max_length=150)
    date = models.DateField()

    class Meta:
        app_label = 'organization'
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["holiday_calendar", "date"],
                name="uniq_holiday_date_per_calendar",
            )
        ]

    def __str__(self):
        return self.name

