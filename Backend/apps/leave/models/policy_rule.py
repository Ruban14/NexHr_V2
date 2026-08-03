"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class LeavePolicyRule(UUIDModel, TimeStampedModel, AuditedModel):
    """Leave entitlement rule."""

    class AllocationFrequency(models.TextChoices):
        YEARLY = "yearly", "Yearly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"

    policy = models.ForeignKey('organization.LeavePolicy',
        on_delete=models.CASCADE,
        related_name="rules",
    )

    leave_type = models.ForeignKey('organization.LeaveType',
        on_delete=models.PROTECT,
        related_name="policy_rules",
    )

    allocation_frequency = models.CharField(
        max_length=20,
        choices=AllocationFrequency.choices,
        default=AllocationFrequency.YEARLY,
    )

    allocation_quantity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Quantity allocated every allocation frequency.",
    )

    annual_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Maximum leave that can be allocated in a leave year.",
    )

    carry_forward_allowed = models.BooleanField(
        default=False,
    )

    carry_forward_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    encashment_allowed = models.BooleanField(
        default=False,
    )

    encashment_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    allow_half_day = models.BooleanField(
        default=False,
    )

    allow_negative_balance = models.BooleanField(
        default=False,
    )

    minimum_service_days = models.PositiveIntegerField(
        default=0,
    )

    maximum_consecutive_days = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        app_label = 'organization'
        db_table = "leave_policy_rules"
        unique_together = (
            "policy",
            "leave_type",
        )

    def __str__(self):
        return f"{self.policy.name} - {self.leave_type.name}"

