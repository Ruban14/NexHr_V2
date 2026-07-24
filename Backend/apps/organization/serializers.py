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


class OrganizationUpdateSerializer(serializers.Serializer):
    """Validate organization update payload."""

    legal_name = serializers.CharField(max_length=255, required=False)
    display_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    industry_type_id = serializers.UUIDField(required=False)
    organization_size = serializers.ChoiceField(
        choices=Organization.OrganizationSize.choices,
        required=False,
        allow_blank=True,
    )
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    website = serializers.CharField(max_length=200, required=False, allow_blank=True)
    logo = serializers.URLField(required=False, allow_blank=True, max_length=200)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=3, required=False, allow_blank=True)

    def validate_legal_name(self, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Organization name must be at least 2 characters.')
        return cleaned

    def validate_phone(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ''
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

    def validate_logo(self, value: str) -> str:
        return value.strip()

    def validate_currency(self, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned and len(cleaned) != 3:
            raise serializers.ValidationError('Currency must be a 3-letter code.')
        return cleaned


class UserProfileUpdateSerializer(serializers.Serializer):
    """Validate authenticated user profile update payload."""

    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    display_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    profile_photo = serializers.URLField(required=False, allow_blank=True, max_length=200)
    mobile_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    alternate_mobile = serializers.CharField(max_length=32, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other', 'prefer_not_to_say', ''],
        required=False,
        allow_blank=True,
    )
    blood_group = serializers.ChoiceField(
        choices=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown', ''],
        required=False,
        allow_blank=True,
    )
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    mother_language = serializers.CharField(max_length=100, required=False, allow_blank=True)
    languages_known = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
    )

    def validate_mobile_number(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ''
        digits = ''.join(ch for ch in cleaned if ch.isdigit())
        if len(digits) < 7 or len(digits) > 20:
            raise serializers.ValidationError('Enter a valid mobile number.')
        return cleaned

    def validate_alternate_mobile(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ''
        digits = ''.join(ch for ch in cleaned if ch.isdigit())
        if len(digits) < 7 or len(digits) > 20:
            raise serializers.ValidationError('Enter a valid mobile number.')
        return cleaned

    def validate_profile_photo(self, value: str) -> str:
        return value.strip()
