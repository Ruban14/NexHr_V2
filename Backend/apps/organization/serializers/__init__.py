"""Organization API serializers."""

from __future__ import annotations

import re

from rest_framework import serializers

from apps.organizations.models import Organization

IFSC_PATTERN = re.compile(r'^[A-Z]{4}0[A-Z0-9]{6}$')
ACCOUNT_NUMBER_PATTERN = re.compile(r'^[A-Za-z0-9]{6,64}$')


def _validate_bank_account_number(value: str) -> str:
    cleaned = value.strip().replace(' ', '').replace('-', '')
    if not cleaned:
        return ''
    if not ACCOUNT_NUMBER_PATTERN.fullmatch(cleaned):
        raise serializers.ValidationError('Enter a valid account number (6–64 letters or digits).')
    return cleaned


def _validate_bank_ifsc_code(value: str) -> str:
    cleaned = value.strip().upper().replace(' ', '')
    if not cleaned:
        return ''
    if not IFSC_PATTERN.fullmatch(cleaned):
        raise serializers.ValidationError('Enter a valid 11-character IFSC code (e.g. HDFC0001234).')
    return cleaned


def _parse_json_list(value, *, field_name: str):
    if value is None or value == '':
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        import json

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise serializers.ValidationError({field_name: ['Provide a valid JSON list.']}) from exc
        if not isinstance(parsed, list):
            raise serializers.ValidationError({field_name: ['Provide a JSON list.']})
        return parsed
    raise serializers.ValidationError({field_name: ['Provide a JSON list.']})


def _as_plain_dict(data) -> dict:
    """Convert QueryDict/multipart data to a plain dict.

    DRF treats objects with ``getlist`` as HTML form input and then ignores
    JSON-encoded nested lists such as ``bank_details``.
    """
    if isinstance(data, dict) and not hasattr(data, 'getlist'):
        return dict(data)
    if hasattr(data, 'keys'):
        return {key: data.get(key) for key in data.keys()}
    return dict(data)


class EmployeeBankDetailItemSerializer(serializers.Serializer):
    account_holder_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    bank_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    account_number = serializers.CharField(max_length=64, required=False, allow_blank=True, default='')
    ifsc_code = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    is_primary = serializers.BooleanField(required=False, default=False)

    def validate_account_number(self, value: str) -> str:
        return _validate_bank_account_number(value)

    def validate_ifsc_code(self, value: str) -> str:
        return _validate_bank_ifsc_code(value)

    def validate_is_primary(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)


class EmployeeTaxDetailSerializer(serializers.Serializer):
    pan_number = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    aadhaar_number = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    uan_number = serializers.CharField(max_length=30, required=False, allow_blank=True, default='')
    pf_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    esi_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    tax_regime = serializers.ChoiceField(choices=['old', 'new'], required=False, default='new')
    tax_identification_number = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default='',
    )
    is_pf_applicable = serializers.BooleanField(required=False, default=True)
    is_esi_applicable = serializers.BooleanField(required=False, default=False)
    professional_tax_applicable = serializers.BooleanField(required=False, default=False)
    labour_welfare_fund_applicable = serializers.BooleanField(required=False, default=False)

    def validate_is_pf_applicable(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)

    def validate_is_esi_applicable(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)

    def validate_professional_tax_applicable(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)

    def validate_labour_welfare_fund_applicable(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)


class EmployeeEducationItemSerializer(serializers.Serializer):
    degree = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    institution = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    field_of_study = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    year_of_passing = serializers.IntegerField(required=False, allow_null=True, min_value=1950, max_value=2100)
    grade = serializers.CharField(max_length=64, required=False, allow_blank=True, default='')

    def to_internal_value(self, data):
        mutable = dict(data) if isinstance(data, dict) else data
        if isinstance(mutable, dict) and mutable.get('year_of_passing') in ('', None):
            mutable = {**mutable, 'year_of_passing': None}
        return super().to_internal_value(mutable)

    def validate_year_of_passing(self, value):
        if value in ('', None):
            return None
        return value


class EmployeeJobExperienceItemSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    job_title = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    start_date = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d', 'iso-8601'],
    )
    end_date = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d', 'iso-8601'],
    )
    is_current = serializers.BooleanField(required=False, default=False)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    description = serializers.CharField(required=False, allow_blank=True, default='')

    def to_internal_value(self, data):
        mutable = dict(data) if isinstance(data, dict) else data
        if isinstance(mutable, dict):
            for key in ('start_date', 'end_date'):
                if mutable.get(key) in ('', None):
                    mutable = {**mutable, key: None}
            if isinstance(mutable.get('is_current'), str):
                mutable = {
                    **mutable,
                    'is_current': mutable.get('is_current', '').strip().lower()
                    in {'1', 'true', 'yes', 'on'},
                }
        return super().to_internal_value(mutable)

    def validate(self, attrs):
        is_current = bool(attrs.get('is_current'))
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if is_current:
            attrs['end_date'] = None
        elif start and end and end < start:
            raise serializers.ValidationError(
                {'end_date': ['End date must be on or after start date.']},
            )
        return attrs


class IndustryTypeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
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
    logo = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=3, required=False, allow_blank=True)
    notice_period_days = serializers.IntegerField(required=False, min_value=1, max_value=365)

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
        cleaned = value.strip()
        if not cleaned:
            return ''
        # Temporary inline storage until object storage / buckets are adopted.
        if cleaned.startswith('data:image/'):
            if len(cleaned) > 1_500_000:
                raise serializers.ValidationError('Logo image must be under ~1 MB.')
            return cleaned
        if cleaned.startswith(('http://', 'https://')):
            if len(cleaned) > 2048:
                raise serializers.ValidationError('Logo URL is too long.')
            return cleaned
        raise serializers.ValidationError('Provide an http(s) image URL or upload an image.')

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
    profile_photo = serializers.FileField(required=False, allow_null=True)
    clear_profile_photo = serializers.BooleanField(required=False, default=False)
    mobile_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    alternate_mobile = serializers.CharField(max_length=32, required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    emergency_contact_relationship = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    bank_details = EmployeeBankDetailItemSerializer(many=True, required=False)
    education_details = EmployeeEducationItemSerializer(many=True, required=False)
    job_experiences = EmployeeJobExperienceItemSerializer(many=True, required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        if mutable.get('date_of_birth') == '':
            mutable['date_of_birth'] = None
        for key in ('bank_details', 'education_details', 'job_experiences'):
            if key in mutable:
                parsed = _parse_json_list(mutable.get(key), field_name=key)
                if parsed is None:
                    mutable.pop(key, None)
                else:
                    mutable[key] = parsed
        return super().to_internal_value(mutable)
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
    languages_known = serializers.CharField(required=False, allow_blank=True)

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

    def validate_emergency_contact_phone(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ''
        digits = ''.join(ch for ch in cleaned if ch.isdigit())
        if len(digits) < 7 or len(digits) > 20:
            raise serializers.ValidationError('Enter a valid phone number.')
        return cleaned

    def validate_profile_photo(self, value):
        from django.conf import settings

        if value is None:
            return value
        content_type = getattr(value, 'content_type', '') or ''
        allowed = getattr(settings, 'PROFILE_PHOTO_CONTENT_TYPES', ())
        if content_type not in allowed:
            raise serializers.ValidationError('Upload a JPG, PNG, WEBP, or GIF image.')
        max_bytes = getattr(settings, 'PROFILE_PHOTO_MAX_BYTES', 2 * 1024 * 1024)
        if value.size > max_bytes:
            raise serializers.ValidationError('Photo must be 2 MB or smaller.')
        return value

    def validate_languages_known(self, value: str):
        if not value or not str(value).strip():
            return []
        raw = str(value).strip()
        if raw.startswith('['):
            import json

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError('Provide languages as a comma-separated list.') from exc
            if not isinstance(parsed, list):
                raise serializers.ValidationError('Provide languages as a comma-separated list.')
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [part.strip() for part in raw.split(',') if part.strip()]

    def validate_clear_profile_photo(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)


class MasterNameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)


class MasterUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160, required=False)
    is_active = serializers.BooleanField(required=False)


class AccessTypeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True, default='')


class AccessTypeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class DesignationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    parent_id = serializers.UUIDField(required=False, allow_null=True)


class DesignationUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160, required=False)
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)


class DesignationMoveSerializer(serializers.Serializer):
    direction = serializers.ChoiceField(choices=['up', 'down'])


class DesignationRepositionSerializer(serializers.Serializer):
    target_id = serializers.UUIDField()
    position = serializers.ChoiceField(choices=['before', 'after', 'inside'])


class ShiftCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H:%M:%S'])
    end_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H:%M:%S'])


class ShiftUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    start_time = serializers.TimeField(
        format='%H:%M',
        input_formats=['%H:%M', '%H:%M:%S'],
        required=False,
    )
    end_time = serializers.TimeField(
        format='%H:%M',
        input_formats=['%H:%M', '%H:%M:%S'],
        required=False,
    )
    is_active = serializers.BooleanField(required=False)


class WorkWeekCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    working_days = serializers.ListField(child=serializers.IntegerField(min_value=1, max_value=7), allow_empty=False)


class WorkWeekUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    working_days = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7),
        required=False,
        allow_empty=False,
    )
    is_active = serializers.BooleanField(required=False)


class HolidayCalendarCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    year = serializers.IntegerField(min_value=2000, max_value=2100)


class HolidayCalendarUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)
    is_active = serializers.BooleanField(required=False)


class HolidayCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    date = serializers.DateField()


class HolidayUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    date = serializers.DateField(required=False)


class DocumentCategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    display_order = serializers.IntegerField(required=False, min_value=0, default=0)


class DocumentCategoryUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    display_order = serializers.IntegerField(required=False, min_value=0)
    is_active = serializers.BooleanField(required=False)


class DocumentDefinitionCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    category_id = serializers.UUIDField()
    description = serializers.CharField(required=False, allow_blank=True, default='')


class DocumentDefinitionUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    category_id = serializers.UUIDField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class DocumentPolicyItemSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    display_order = serializers.IntegerField(required=False, min_value=0, default=0)
    is_required = serializers.BooleanField(required=False, default=True)
    allow_multiple = serializers.BooleanField(required=False, default=False)
    verification_required = serializers.BooleanField(required=False, default=True)
    requires_expiry = serializers.BooleanField(required=False, default=False)


class DocumentPolicyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    employee_type_id = serializers.UUIDField()
    description = serializers.CharField(required=False, allow_blank=True, default='')
    is_default = serializers.BooleanField(required=False, default=False)
    items = DocumentPolicyItemSerializer(many=True, required=False, default=list)


class DocumentPolicyUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    employee_type_id = serializers.UUIDField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_default = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    items = DocumentPolicyItemSerializer(many=True, required=False)


class EmployeeCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    display_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    designation_id = serializers.UUIDField(required=False, allow_null=True)
    employee_type_id = serializers.UUIDField(required=False, allow_null=True)
    access_type_id = serializers.UUIDField(required=False, allow_null=True)
    joining_date = serializers.DateField(required=False, allow_null=True)


class EmployeeUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    display_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    profile_photo = serializers.FileField(required=False, allow_null=True)
    clear_profile_photo = serializers.BooleanField(required=False, default=False)
    mobile_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    alternate_mobile = serializers.CharField(max_length=32, required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    emergency_contact_relationship = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    bank_details = EmployeeBankDetailItemSerializer(many=True, required=False)
    education_details = EmployeeEducationItemSerializer(many=True, required=False)
    job_experiences = EmployeeJobExperienceItemSerializer(many=True, required=False)
    tax_detail = EmployeeTaxDetailSerializer(required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
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
    languages_known = serializers.CharField(required=False, allow_blank=True)
    designation_id = serializers.UUIDField(required=False, allow_null=True)
    employee_type_id = serializers.UUIDField(required=False, allow_null=True)
    access_type_id = serializers.UUIDField(required=False, allow_null=True)
    reporting_manager_id = serializers.UUIDField(required=False, allow_null=True)
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    joining_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    exit_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    is_active = serializers.BooleanField(required=False)

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        for key in (
            'date_of_birth',
            'joining_date',
            'exit_date',
            'designation_id',
            'employee_type_id',
            'access_type_id',
            'reporting_manager_id',
        ):
            if mutable.get(key) == '':
                mutable[key] = None
        if 'is_active' in mutable and isinstance(mutable.get('is_active'), str):
            mutable['is_active'] = mutable.get('is_active', '').strip().lower() in {'1', 'true', 'yes', 'on'}
        for key in ('bank_details', 'education_details', 'job_experiences'):
            if key in mutable:
                parsed = _parse_json_list(mutable.get(key), field_name=key)
                if parsed is None:
                    mutable.pop(key, None)
                else:
                    mutable[key] = parsed
        if 'tax_detail' in mutable:
            raw = mutable.get('tax_detail')
            if raw in (None, ''):
                mutable.pop('tax_detail', None)
            elif isinstance(raw, str):
                import json

                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise serializers.ValidationError({'tax_detail': ['Provide a valid JSON object.']}) from exc
                if not isinstance(parsed, dict):
                    raise serializers.ValidationError({'tax_detail': ['Provide a JSON object.']})
                mutable['tax_detail'] = parsed
        return super().to_internal_value(mutable)

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

    def validate_emergency_contact_phone(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ''
        digits = ''.join(ch for ch in cleaned if ch.isdigit())
        if len(digits) < 7 or len(digits) > 20:
            raise serializers.ValidationError('Enter a valid phone number.')
        return cleaned

    def validate_profile_photo(self, value):
        from django.conf import settings

        if value is None:
            return value
        content_type = getattr(value, 'content_type', '') or ''
        allowed = getattr(settings, 'PROFILE_PHOTO_CONTENT_TYPES', ())
        if content_type not in allowed:
            raise serializers.ValidationError('Upload a JPG, PNG, WEBP, or GIF image.')
        max_bytes = getattr(settings, 'PROFILE_PHOTO_MAX_BYTES', 2 * 1024 * 1024)
        if value.size > max_bytes:
            raise serializers.ValidationError('Photo must be 2 MB or smaller.')
        return value

    def validate_languages_known(self, value: str):
        if not value or not str(value).strip():
            return []
        raw = str(value).strip()
        if raw.startswith('['):
            import json

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError('Provide languages as a comma-separated list.') from exc
            if not isinstance(parsed, list):
                raise serializers.ValidationError('Provide languages as a comma-separated list.')
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [part.strip() for part in raw.split(',') if part.strip()]

    def validate_clear_profile_photo(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)


class EmployeeLifecycleTransitionSerializer(serializers.Serializer):
    to_status_id = serializers.UUIDField()
    remarks = serializers.CharField(required=False, allow_blank=True, default='')
    exit_date = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d', 'iso-8601'],
    )

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        if mutable.get('exit_date') == '':
            mutable['exit_date'] = None
        return super().to_internal_value(mutable)


class EmployeeDocumentUploadSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    file = serializers.FileField()
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        for key in ('issue_date', 'expiry_date'):
            if mutable.get(key) in ('', None):
                mutable[key] = None
        return super().to_internal_value(mutable)


class EmployeeDocumentReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_approve(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)


class AssetTypeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default='')


class AssetTypeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class AssetCreateSerializer(serializers.Serializer):
    asset_type_id = serializers.UUIDField()
    asset_code = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=150)
    brand = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    model = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    serial_number = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    purchase_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    warranty_expiry = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    status = serializers.ChoiceField(
        choices=['available', 'assigned', 'lost', 'damaged', 'retired'],
        required=False,
        default='available',
    )
    remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        for key in ('purchase_date', 'warranty_expiry'):
            if mutable.get(key) in ('', None):
                mutable[key] = None
        return super().to_internal_value(mutable)


class AssetUpdateSerializer(serializers.Serializer):
    asset_type_id = serializers.UUIDField(required=False)
    asset_code = serializers.CharField(max_length=50, required=False)
    name = serializers.CharField(max_length=150, required=False)
    brand = serializers.CharField(max_length=100, required=False, allow_blank=True)
    model = serializers.CharField(max_length=100, required=False, allow_blank=True)
    serial_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    purchase_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    warranty_expiry = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    status = serializers.ChoiceField(
        choices=['available', 'assigned', 'lost', 'damaged', 'retired'],
        required=False,
    )
    remarks = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        for key in ('purchase_date', 'warranty_expiry'):
            if key in mutable and mutable.get(key) in ('', None):
                mutable[key] = None
        return super().to_internal_value(mutable)


class AssetAssignSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()
    assigned_at = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    expected_return_at = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d', 'iso-8601'],
    )
    remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        for key in ('assigned_at', 'expected_return_at'):
            if mutable.get(key) in ('', None):
                mutable[key] = None
        return super().to_internal_value(mutable)


class AssetRevokeSerializer(serializers.Serializer):
    returned_at = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', 'iso-8601'])
    remarks = serializers.CharField(required=False, allow_blank=True, default='')
    mark_lost = serializers.BooleanField(required=False, default=False)

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        if mutable.get('returned_at') in ('', None):
            mutable['returned_at'] = None
        return super().to_internal_value(mutable)

    def validate_mark_lost(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)


class LeavePolicyRuleSerializer(serializers.Serializer):
    leave_type_id = serializers.UUIDField()
    allocation_frequency = serializers.ChoiceField(
        choices=['yearly', 'monthly', 'quarterly'],
        required=False,
        default='yearly',
    )
    allocation_quantity = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    annual_limit = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    carry_forward_allowed = serializers.BooleanField(required=False, default=False)
    carry_forward_limit = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    encashment_allowed = serializers.BooleanField(required=False, default=False)
    encashment_limit = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    allow_half_day = serializers.BooleanField(required=False, default=False)
    allow_negative_balance = serializers.BooleanField(required=False, default=False)
    minimum_service_days = serializers.IntegerField(required=False, min_value=0, default=0)
    maximum_consecutive_days = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    is_active = serializers.BooleanField(required=False, default=True)

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        if mutable.get('maximum_consecutive_days') in ('', None):
            mutable['maximum_consecutive_days'] = None
        return super().to_internal_value(mutable)


class LeavePolicyCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=30)
    name = serializers.CharField(max_length=150)
    employee_type_id = serializers.UUIDField()
    description = serializers.CharField(required=False, allow_blank=True, default='')
    effective_from = serializers.DateField(input_formats=['%Y-%m-%d', 'iso-8601'])
    effective_to = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d', 'iso-8601'],
    )
    is_default = serializers.BooleanField(required=False, default=False)
    rules = LeavePolicyRuleSerializer(many=True, required=False, default=list)

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        if mutable.get('effective_to') in ('', None):
            mutable['effective_to'] = None
        return super().to_internal_value(mutable)


class LeavePolicyUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=30, required=False)
    name = serializers.CharField(max_length=150, required=False)
    employee_type_id = serializers.UUIDField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    effective_from = serializers.DateField(required=False, input_formats=['%Y-%m-%d', 'iso-8601'])
    effective_to = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d', 'iso-8601'],
    )
    is_default = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    rules = LeavePolicyRuleSerializer(many=True, required=False)

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        if 'effective_to' in mutable and mutable.get('effective_to') in ('', None):
            mutable['effective_to'] = None
        return super().to_internal_value(mutable)


class LeaveBalanceAllocateSerializer(serializers.Serializer):
    leave_type_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=5, decimal_places=2)
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class LeaveBalanceAdjustSerializer(serializers.Serializer):
    leave_type_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=5, decimal_places=2)
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class LeaveApplicationCreateSerializer(serializers.Serializer):
    leave_type_id = serializers.UUIDField()
    from_date = serializers.DateField(input_formats=['%Y-%m-%d', 'iso-8601'])
    to_date = serializers.DateField(input_formats=['%Y-%m-%d', 'iso-8601'])
    is_half_day = serializers.BooleanField(required=False, default=False)
    reason = serializers.CharField()
    attachment = serializers.FileField(required=False, allow_null=True)

    def to_internal_value(self, data):
        mutable = _as_plain_dict(data)
        if isinstance(mutable.get('is_half_day'), str):
            mutable['is_half_day'] = mutable['is_half_day'].strip().lower() in {
                '1',
                'true',
                'yes',
                'on',
            }
        if mutable.get('attachment') in ('', None):
            mutable.pop('attachment', None)
        return super().to_internal_value(mutable)


class LeaveApplicationReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_approve(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)


class LeaveApplicationCancelSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class AttendancePunchSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True, default='')
    source = serializers.ChoiceField(
        choices=['web', 'mobile', 'biometric', 'rfid', 'manual', 'api'],
        required=False,
        default='web',
    )


class AttendanceManualSerializer(serializers.Serializer):
    attendance_date = serializers.DateField(input_formats=['%Y-%m-%d', 'iso-8601'])
    status = serializers.ChoiceField(
        choices=['present', 'absent', 'half_day', 'leave', 'holiday', 'week_off'],
        required=False,
        default='present',
    )
    check_in = serializers.CharField(required=True, allow_blank=False)
    check_out = serializers.CharField(required=True, allow_blank=False)
    remarks = serializers.CharField(required=True, allow_blank=False, max_length=2000)
    session_remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_remarks(self, value):
        cleaned = (value or '').strip()
        if not cleaned:
            raise serializers.ValidationError('Remarks are required for manual attendance.')
        return cleaned



class AttendanceReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_approve(self, value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)
