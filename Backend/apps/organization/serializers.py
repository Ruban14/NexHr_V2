"""Organization API serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.organization.models import Organization


class IndustryTypeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()


class OrganizationCreateSerializer(serializers.Serializer):
    """Validate authenticated organization setup payload."""

    legal_name = serializers.CharField(max_length=255)
    display_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    industry_type_id = serializers.UUIDField()
    organization_size = serializers.ChoiceField(
        choices=Organization.OrganizationSize.choices,
        required=False,
        allow_blank=True,
    )
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32)
    website = serializers.CharField(max_length=200, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=3, required=False, allow_blank=True)

    def validate_phone(self, value: str) -> str:
        cleaned = value.strip()
        digits = ''.join(ch for ch in cleaned if ch.isdigit())
        if len(digits) < 7 or len(digits) > 20:
            raise serializers.ValidationError('Enter a valid phone number.')
        return cleaned

    def validate_website(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ''
        if not cleaned.startswith(('http://', 'https://')):
            cleaned = f'https://{cleaned}'
        return cleaned

    def validate_legal_name(self, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Organization name must be at least 2 characters.')
        return cleaned
