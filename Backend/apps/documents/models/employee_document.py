"""Domain models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeDocument(UUIDModel, TimeStampedModel, AuditedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    employee = models.ForeignKey('organization.Employee',
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document = models.ForeignKey('organization.DocumentDefinition',
        on_delete=models.PROTECT,
        related_name="employee_documents",
    )

    file = models.ForeignKey('organization.File',
        on_delete=models.CASCADE,
        related_name="employee_documents",
    )

    issue_date = models.DateField(
        null=True,
        blank=True,
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    remarks = models.TextField(blank=True)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_documents",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "employee_documents"
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee_id} · {self.document_id} · {self.status}'

