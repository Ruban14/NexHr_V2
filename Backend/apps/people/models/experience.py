"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeJobExperience(UUIDModel, TimeStampedModel, AuditedModel):
    """Prior / external job experience linked to an employee."""

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name='job_experiences',
    )
    company_name = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False, db_index=True)
    location = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        app_label = 'organization'
        ordering = ['-is_current', '-start_date', 'created_at']
        verbose_name = 'Employee job experience'
        verbose_name_plural = 'Employee job experiences'
        indexes = [
            models.Index(fields=['employee', 'start_date']),
        ]

    def __str__(self) -> str:
        label = self.job_title or self.company_name or 'Experience'
        return f'{self.employee_id}: {label}'

