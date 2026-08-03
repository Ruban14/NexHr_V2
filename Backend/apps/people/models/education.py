"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeEducation(UUIDModel, TimeStampedModel, AuditedModel):
    """Education / qualification record linked to an employee."""

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name='education_details',
    )
    degree = models.CharField(max_length=150, blank=True)
    institution = models.CharField(max_length=255, blank=True)
    field_of_study = models.CharField(max_length=150, blank=True)
    year_of_passing = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=64, blank=True)

    class Meta:
        app_label = 'organization'
        ordering = ['-year_of_passing', 'created_at']
        verbose_name = 'Employee education'
        verbose_name_plural = 'Employee educations'
        indexes = [
            models.Index(fields=['employee', 'year_of_passing']),
        ]

    def __str__(self) -> str:
        label = self.degree or self.institution or 'Education'
        return f'{self.employee_id}: {label}'

