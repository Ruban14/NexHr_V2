"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class EmployeeTaxDetail(UUIDModel, TimeStampedModel, AuditedModel):
    """Employee tax information."""

    class TaxRegime(models.TextChoices):
        OLD = 'old', 'Old Regime'
        NEW = 'new', 'New Regime'

    employee = models.OneToOneField('organization.Employee',
        on_delete=models.CASCADE,
        related_name='tax_detail',
    )

    pan_number = models.CharField(max_length=20, blank=True)
    aadhaar_number = models.CharField(max_length=20, blank=True)
    uan_number = models.CharField(max_length=30, blank=True)
    pf_number = models.CharField(max_length=50, blank=True)
    esi_number = models.CharField(max_length=50, blank=True)

    tax_regime = models.CharField(
        max_length=20,
        choices=TaxRegime.choices,
        default=TaxRegime.NEW,
    )

    tax_identification_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='TIN / SSN / National Tax ID based on country.',
    )

    is_pf_applicable = models.BooleanField(default=True)
    is_esi_applicable = models.BooleanField(default=False)
    professional_tax_applicable = models.BooleanField(default=False)
    labour_welfare_fund_applicable = models.BooleanField(default=False)

    class Meta:
        app_label = 'organization'
        db_table = 'employee_tax_details'

    def __str__(self):
        return f'{self.employee_id} - Tax Details'

