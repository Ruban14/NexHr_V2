"""Organization setup / onboarding services."""

from __future__ import annotations

import re
import uuid
from datetime import date

from django.db import transaction

from apps.authentication.models import User
from apps.core.exceptions import ConflictServiceError, NotFoundServiceError, ValidationServiceError
from apps.organization.models import (
    AccessType,
    EmployeeType,
    IndustryType,
    Organization,
    OrganizationMembership,
    UserProfile,
)

DEFAULT_INDUSTRIES: tuple[tuple[str, str], ...] = (
    ('it', 'Information Technology'),
    ('healthcare', 'Healthcare'),
    ('education', 'Education'),
    ('finance', 'Finance'),
    ('manufacturing', 'Manufacturing'),
    ('retail', 'Retail'),
    ('hospitality', 'Hospitality'),
    ('construction', 'Construction'),
    ('logistics', 'Logistics'),
    ('others', 'Others'),
)


class OrganizationSetupService:
    """Creates profile, organization, and admin membership after email verification."""

    @classmethod
    def ensure_industry_defaults(cls) -> None:
        for code, name in DEFAULT_INDUSTRIES:
            IndustryType.objects.get_or_create(
                code=code,
                defaults={'name': name, 'is_active': True},
            )

    @classmethod
    def list_industries(cls) -> list[IndustryType]:
        cls.ensure_industry_defaults()
        return list(
            IndustryType.objects.filter(is_active=True).order_by('name'),
        )

    @classmethod
    def get_setup_status(cls, user: User) -> dict:
        profile = UserProfile.objects.filter(user=user).first()
        membership_exists = False
        if profile is not None:
            membership_exists = OrganizationMembership.objects.filter(
                user_profile=profile,
            ).exists()
        owned = Organization.objects.filter(owner=user).exists()
        needs_setup = not membership_exists and not owned
        return {
            'needs_setup': needs_setup,
            'has_profile': profile is not None,
            'has_membership': membership_exists,
            'has_owned_organization': owned,
        }

    @classmethod
    @transaction.atomic
    def create_organization(cls, *, user: User, payload: dict) -> dict:
        if not user.is_email_verified:
            raise ValidationServiceError(
                'Please verify your email before creating an organization.',
                code='email_not_verified',
            )

        status = cls.get_setup_status(user)
        if not status['needs_setup']:
            raise ConflictServiceError(
                'You already belong to an organization.',
                code='organization_exists',
            )

        industry = IndustryType.objects.filter(
            id=payload['industry_type_id'],
            is_active=True,
        ).first()
        if industry is None:
            raise NotFoundServiceError('Industry type not found.', code='industry_not_found')

        legal_name = payload['legal_name']
        display_name = (payload.get('display_name') or legal_name).strip() or legal_name
        email = (payload.get('email') or user.email).strip()
        website = payload.get('website') or ''

        profile = cls._ensure_admin_profile(user=user, phone=payload.get('phone') or '')
        access_type = cls._ensure_admin_access_type(industry=industry)
        employee_type = cls._ensure_default_employee_type()

        organization = Organization.objects.create(
            organization_code=cls._generate_organization_code(display_name),
            legal_name=legal_name,
            display_name=display_name,
            industry_type=industry,
            organization_size=payload.get('organization_size') or '',
            email=email,
            phone=payload['phone'],
            website=website,
            country=payload.get('country') or '',
            state=payload.get('state') or '',
            city=payload.get('city') or '',
            timezone=payload.get('timezone') or 'Asia/Kolkata',
            currency=(payload.get('currency') or 'INR').upper(),
            is_active=True,
            owner=user,
            created_by=user,
            updated_by=user,
        )

        membership = OrganizationMembership.objects.create(
            organization=organization,
            user_profile=profile,
            employee_type=employee_type,
            access_type=access_type,
            employee_code=cls._generate_employee_code(organization),
            status=OrganizationMembership.Status.ACTIVE,
            joining_date=date.today(),
            created_by=user,
            updated_by=user,
        )

        return {
            'organization': cls._serialize_organization(organization),
            'membership': cls._serialize_membership(membership),
            'profile': cls._serialize_profile(profile),
        }

    @classmethod
    def _ensure_admin_profile(cls, *, user: User, phone: str) -> UserProfile:
        display_name = user.full_name or user.email.split('@')[0]
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'display_name': display_name,
                'mobile_number': phone,
                'is_profile_completed': False,
                'completed_status': '',
                'created_by': user,
                'updated_by': user,
            },
        )
        if not created:
            updates: list[str] = []
            if not profile.display_name:
                profile.display_name = display_name
                updates.append('display_name')
            if phone and not profile.mobile_number:
                profile.mobile_number = phone
                updates.append('mobile_number')
            if updates:
                profile.updated_by = user
                updates.append('updated_by')
                profile.save(update_fields=[*updates, 'updated_at'])
        return profile

    @classmethod
    def _ensure_admin_access_type(cls, *, industry: IndustryType) -> AccessType:
        access_type, _ = AccessType.objects.get_or_create(
            code='admin',
            defaults={
                'name': 'Admin',
                'description': 'Organization administrator',
                'industry_type': industry,
                'is_active': True,
            },
        )
        if access_type.industry_type_id is None:
            access_type.industry_type = industry
            access_type.save(update_fields=['industry_type', 'updated_at'])
        return access_type

    @classmethod
    def _ensure_default_employee_type(cls) -> EmployeeType:
        employee_type, _ = EmployeeType.objects.get_or_create(
            code='permanent',
            defaults={
                'name': 'Permanent',
                'is_active': True,
            },
        )
        return employee_type

    @classmethod
    def _generate_organization_code(cls, display_name: str) -> str:
        slug = re.sub(r'[^a-z0-9]+', '-', display_name.lower()).strip('-')[:20] or 'org'
        for _ in range(8):
            code = f'{slug}-{uuid.uuid4().hex[:6]}'.upper()
            if not Organization.objects.filter(organization_code=code).exists():
                return code
        return f'ORG-{uuid.uuid4().hex[:10]}'.upper()

    @classmethod
    def _generate_employee_code(cls, organization: Organization) -> str:
        prefix = re.sub(r'[^A-Z0-9]', '', organization.organization_code.upper())[:6] or 'EMP'
        return f'{prefix}-001'

    @classmethod
    def _serialize_organization(cls, organization: Organization) -> dict:
        return {
            'id': str(organization.id),
            'organization_code': organization.organization_code,
            'legal_name': organization.legal_name,
            'display_name': organization.display_name,
            'industry_type_id': (
                str(organization.industry_type_id) if organization.industry_type_id else None
            ),
            'email': organization.email,
            'phone': organization.phone,
            'website': organization.website,
            'logo': organization.logo,
            'country': organization.country,
            'state': organization.state,
            'city': organization.city,
            'timezone': organization.timezone,
            'currency': organization.currency,
            'is_active': organization.is_active,
            'owner_id': str(organization.owner_id),
        }

    @classmethod
    def _serialize_membership(cls, membership: OrganizationMembership) -> dict:
        return {
            'id': str(membership.id),
            'organization_id': str(membership.organization_id),
            'user_profile_id': str(membership.user_profile_id),
            'access_type_id': (
                str(membership.access_type_id) if membership.access_type_id else None
            ),
            'employee_type_id': (
                str(membership.employee_type_id) if membership.employee_type_id else None
            ),
            'employee_code': membership.employee_code,
            'status': membership.status,
            'joining_date': (
                membership.joining_date.isoformat() if membership.joining_date else None
            ),
        }

    @classmethod
    def _serialize_profile(cls, profile: UserProfile) -> dict:
        return {
            'id': str(profile.id),
            'user_id': str(profile.user_id),
            'display_name': profile.display_name,
            'profile_photo': profile.profile_photo,
            'mobile_number': profile.mobile_number,
            'is_profile_completed': profile.is_profile_completed,
        }
