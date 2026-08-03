"""Organization setup / onboarding services."""

from __future__ import annotations

import re
import uuid
from datetime import date

from django.db import transaction

from apps.authentication.models import User
from apps.core.exceptions import ConflictServiceError, NotFoundServiceError, ValidationServiceError
from apps.organizations.models import (
    IndustryType,
    Organization,
    OrganizationBranch,
    OrganizationMembership,
)
from apps.workforce.models import (
    AccessType,
    EmployeeLifecycleStatus,
    EmployeeType,
)
from apps.people.models import (
    Employee,
)
from apps.organization.services.lifecycle import EmployeeService
from apps.organization.services.workspace import WorkspaceService

DEFAULT_INDUSTRIES: tuple[str, ...] = (
    'Information Technology',
    'Healthcare',
    'Education',
    'Finance',
    'Manufacturing',
    'Retail',
    'Hospitality',
    'Construction',
    'Logistics',
    'Others',
)


class OrganizationSetupService:
    """Creates employee profile, organization, and admin membership after email verification."""

    @classmethod
    def ensure_industry_defaults(cls) -> None:
        for name in DEFAULT_INDUSTRIES:
            IndustryType.objects.get_or_create(
                name=name,
                defaults={'is_active': True},
            )

    @classmethod
    def list_industries(cls) -> list[IndustryType]:
        cls.ensure_industry_defaults()
        return list(
            IndustryType.objects.filter(is_active=True).order_by('name'),
        )

    @classmethod
    def get_setup_status(cls, user: User) -> dict:
        employee_exists = Employee.objects.filter(user=user).exists()
        membership_exists = OrganizationMembership.objects.filter(user=user).exists()
        owned = Organization.objects.filter(owner=user).exists()
        needs_setup = not membership_exists and not owned
        return {
            'needs_setup': needs_setup,
            'has_profile': employee_exists,
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
        phone = payload.get('phone') or ''

        access_type = cls._ensure_admin_access_type(industry=industry)
        employee_type = cls._ensure_default_employee_type()
        active_status = cls._get_active_or_initial_lifecycle()

        organization = Organization.objects.create(
            organization_code=cls._generate_organization_code(display_name),
            legal_name=legal_name,
            display_name=display_name,
            industry_type=industry,
            organization_size=payload.get('organization_size') or '',
            email=email,
            phone=phone,
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

        headquarters = cls._create_headquarters_branch(organization=organization)
        employee_code = cls._generate_employee_code(organization)
        person_name = user.full_name or user.email.split('@')[0]

        employee = Employee.objects.create(
            organization=organization,
            branch=headquarters,
            user=user,
            lifecycle_status=active_status,
            employee_code=employee_code,
            email=user.email,
            first_name=user.first_name or '',
            last_name=user.last_name or '',
            display_name=person_name,
            mobile_number=phone,
            employee_type=employee_type,
            access_type=access_type,
            joining_date=date.today(),
            is_active=True,
            is_profile_completed=bool(person_name and phone),
            completed_status='done' if (person_name and phone) else '',
            created_by=user,
            updated_by=user,
        )

        membership = OrganizationMembership.objects.create(
            branch=headquarters,
            user=user,
            employee_type=employee_type,
            access_type=access_type,
            employee_code=employee_code,
            status=OrganizationMembership.Status.ACTIVE,
            joining_date=date.today(),
            created_by=user,
            updated_by=user,
        )

        return {
            'organization': cls._serialize_organization(organization),
            'membership': cls._serialize_membership(membership),
            'profile': cls._serialize_employee_profile(employee),
        }

    @classmethod
    def _get_active_or_initial_lifecycle(cls) -> EmployeeLifecycleStatus:
        active = EmployeeLifecycleStatus.objects.filter(key='active', is_active=True).first()
        if active is not None:
            return active
        return EmployeeLifecycleEngine.get_initial_status()

    @classmethod
    def _create_headquarters_branch(cls, *, organization: Organization) -> OrganizationBranch:
        return OrganizationBranch.objects.create(
            organization=organization,
            branch_code='HQ',
            branch_name=f'{organization.display_name} Headquarters',
            phone=organization.phone,
            email=organization.email,
            city=organization.city,
            state=organization.state,
            country=organization.country,
            is_headquarters=True,
            status=OrganizationBranch.Status.ACTIVE,
        )

    @classmethod
    def _ensure_admin_access_type(cls, *, industry: IndustryType) -> AccessType:
        access_type, _ = AccessType.objects.get_or_create(
            name='Admin',
            defaults={
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
            name='Permanent',
            defaults={'is_active': True},
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
        return EmployeeService._generate_employee_code(organization)

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
            'notice_period_days': organization.notice_period_days,
            'is_active': organization.is_active,
            'owner_id': str(organization.owner_id),
        }

    @classmethod
    def _serialize_membership(cls, membership: OrganizationMembership) -> dict:
        return {
            'id': str(membership.id),
            'organization_id': str(membership.branch.organization_id),
            'branch_id': str(membership.branch_id),
            'user_id': str(membership.user_id),
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
    def _serialize_employee_profile(cls, employee: Employee) -> dict:
        return {
            'id': str(employee.id),
            'user_id': str(employee.user_id) if employee.user_id else None,
            'display_name': employee.display_name,
            'profile_photo': WorkspaceService.profile_photo_url(employee),
            'mobile_number': employee.mobile_number,
            'is_profile_completed': employee.is_profile_completed,
        }
