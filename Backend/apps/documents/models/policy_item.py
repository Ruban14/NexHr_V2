"""Domain models."""

from __future__ import annotations

from django.db import models

from apps.core.models import UUIDModel, TimeStampedModel, AuditedModel


class DocumentPolicyItem(UUIDModel, TimeStampedModel, AuditedModel):
    """Documents required under a policy."""

    policy = models.ForeignKey('organization.DocumentPolicy',
        on_delete=models.CASCADE,
        related_name="items",
    )

    document = models.ForeignKey('organization.DocumentDefinition',
        on_delete=models.PROTECT,
        related_name="policy_items",
    )

    display_order = models.PositiveIntegerField(default=0)

    is_required = models.BooleanField(default=True)
    allow_multiple = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=True)
    requires_expiry = models.BooleanField(default=False)

    class Meta:
        app_label = 'organization'
        db_table = "document_policy_items"
        ordering = ["display_order", "id"]
        unique_together = ("policy", "document")

    def __str__(self):
        return f"{self.policy.name} - {self.document.name}"

