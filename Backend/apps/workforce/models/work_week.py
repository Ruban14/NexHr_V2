"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class WorkWeek(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization work week."""

    class WeekDay(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    organization = models.ForeignKey('organization.Organization',
        on_delete=models.CASCADE,
        related_name="work_weeks",
    )
    name = models.CharField(max_length=100)
    working_days = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'organization'
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_workweek_name_per_org",
            )
        ]

    def __str__(self):
        return self.name

