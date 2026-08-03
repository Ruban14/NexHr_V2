"""Workspace services for current organization, branch context, and user profile."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db import transaction

from apps.authentication.models import User
from apps.core.exceptions import NotFoundServiceError, PermissionDeniedServiceError, ValidationServiceError
from apps.organization.models import Employee, IndustryType, Organization, OrganizationMembership


class WorkspaceService:
    """Read/update the authenticated user's organization and profile."""

    @classmethod
    def list_memberships(cls, user: User) -> list[dict]:
        memberships = (
            OrganizationMembership.objects.select_related(
                'branch',
                'branch__organization',
                'access_type',
                'employee_type',
                'designation',
            )
            .filter(user=user, status=OrganizationMembership.Status.ACTIVE)
            .order_by('branch__organization__display_name', '-branch__is_headquarters', 'branch__branch_name')
        )
        return [cls.serialize_membership_summary(m) for m in memberships]

    @classmethod
    def get_membership(
        cls,
        user: User,
        *,
        branch_id: str | UUID | None = None,
    ) -> OrganizationMembership:
        qs = OrganizationMembership.objects.select_related(
            'branch',
            'branch__organization',
            'branch__organization__industry_type',
            'user',
            'access_type',
            'employee_type',
            'designation',
        ).filter(user=user, status=OrganizationMembership.Status.ACTIVE)

        if branch_id:
            membership = qs.filter(branch_id=branch_id).first()
            if membership is None:
                raise NotFoundServiceError(
                    'No active membership found for the selected branch.',
                    code='branch_membership_not_found',
                )
            return membership

        membership = qs.order_by('-created_at').first()
        if membership is None:
            raise NotFoundServiceError(
                'No organization membership found.',
                code='membership_not_found',
            )
        return membership

    @classmethod
    def get_employee_for_user(
        cls,
        user: User,
        *,
        branch_id: str | UUID | None = None,
    ) -> Employee:
        membership = None
        try:
            membership = cls.get_membership(user, branch_id=branch_id)
        except NotFoundServiceError:
            membership = (
                OrganizationMembership.objects.select_related('branch')
                .filter(user=user, status=OrganizationMembership.Status.ACTIVE)
                .order_by('-created_at')
                .first()
            )

        qs = Employee.objects.select_related(
            'organization',
            'branch',
            'access_type',
            'lifecycle_status',
        ).prefetch_related(
            'bank_details',
            'education_details',
            'job_experiences',
        ).filter(user=user)

        if membership is not None:
            employee = qs.filter(organization_id=membership.branch.organization_id).first()
            if employee is not None:
                return employee

        employee = qs.order_by('-created_at').first()
        if employee is None:
            raise NotFoundServiceError('Employee profile not found.', code='profile_not_found')
        return employee

    @classmethod
    def get_organization(cls, user: User, *, branch_id: str | UUID | None = None) -> dict:
        membership = cls.get_membership(user, branch_id=branch_id)
        data = cls.serialize_organization(
            membership.organization,
            can_edit=membership.organization.owner_id == user.id,
        )
        data['current_branch'] = cls.serialize_branch(membership.branch)
        data['membership'] = cls.serialize_membership_summary(membership)
        return data

    @classmethod
    @transaction.atomic
    def update_organization(
        cls,
        *,
        user: User,
        payload: dict,
        branch_id: str | UUID | None = None,
    ) -> dict:
        membership = cls.get_membership(user, branch_id=branch_id)
        organization = membership.organization
        if organization.owner_id != user.id:
            raise PermissionDeniedServiceError(
                'Only the organization owner can edit organization details.',
                code='not_organization_owner',
            )

        industry_type_id = payload.get('industry_type_id')
        if industry_type_id is not None:
            industry = IndustryType.objects.filter(id=industry_type_id, is_active=True).first()
            if industry is None:
                raise NotFoundServiceError('Industry type not found.', code='industry_not_found')
            organization.industry_type = industry

        field_map = {
            'legal_name': 'legal_name',
            'display_name': 'display_name',
            'organization_size': 'organization_size',
            'email': 'email',
            'phone': 'phone',
            'website': 'website',
            'logo': 'logo',
            'country': 'country',
            'state': 'state',
            'city': 'city',
            'timezone': 'timezone',
            'currency': 'currency',
            'notice_period_days': 'notice_period_days',
        }
        for payload_key, model_field in field_map.items():
            if payload_key in payload:
                value = payload[payload_key]
                if payload_key == 'currency' and value:
                    value = str(value).upper()
                if payload_key == 'notice_period_days':
                    setattr(organization, model_field, int(value))
                    continue
                setattr(organization, model_field, value if value is not None else '')

        if 'legal_name' in payload and not organization.display_name:
            organization.display_name = organization.legal_name

        organization.updated_by = user
        organization.save()
        data = cls.serialize_organization(organization, can_edit=True)
        data['current_branch'] = cls.serialize_branch(membership.branch)
        data['membership'] = cls.serialize_membership_summary(membership)
        return data

    @classmethod
    def get_profile(cls, user: User, *, branch_id: str | UUID | None = None) -> dict:
        employee = cls.get_employee_for_user(user, branch_id=branch_id)
        membership = None
        try:
            membership = cls.get_membership(user, branch_id=branch_id)
        except NotFoundServiceError:
            membership = (
                OrganizationMembership.objects.select_related(
                    'branch',
                    'branch__organization',
                    'access_type',
                )
                .filter(user=user, status=OrganizationMembership.Status.ACTIVE)
                .order_by('-created_at')
                .first()
            )
        return cls.serialize_profile(user=user, employee=employee, membership=membership)

    @classmethod
    @transaction.atomic
    def update_profile(
        cls,
        *,
        user: User,
        payload: dict,
        branch_id: str | UUID | None = None,
    ) -> dict:
        employee = cls.get_employee_for_user(user, branch_id=branch_id)

        user_updates: list[str] = []
        if 'first_name' in payload:
            user.first_name = payload['first_name'] or ''
            employee.first_name = user.first_name
            user_updates.append('first_name')
        if 'last_name' in payload:
            user.last_name = payload['last_name'] or ''
            employee.last_name = user.last_name
            user_updates.append('last_name')
        if user_updates:
            user.save(update_fields=[*user_updates, 'updated_at'])

        profile_fields = {
            'display_name',
            'mobile_number',
            'alternate_mobile',
            'emergency_contact_name',
            'emergency_contact_relationship',
            'emergency_contact_phone',
            'gender',
            'blood_group',
            'country',
            'state',
            'city',
            'address_line1',
            'postal_code',
            'mother_language',
        }
        for field in profile_fields:
            if field in payload:
                value = payload[field]
                setattr(employee, field, value if value is not None else '')

        if payload.get('clear_profile_photo'):
            if employee.profile_photo:
                employee.profile_photo.delete(save=False)
            employee.profile_photo = ''
        elif payload.get('profile_photo') is not None:
            if employee.profile_photo:
                employee.profile_photo.delete(save=False)
            employee.profile_photo = payload['profile_photo']

        if 'date_of_birth' in payload:
            dob = payload['date_of_birth']
            if dob in (None, ''):
                employee.date_of_birth = None
            elif isinstance(dob, date):
                employee.date_of_birth = dob
            else:
                raise ValidationServiceError(
                    'Enter a valid date of birth.',
                    code='invalid_date_of_birth',
                    details={'date_of_birth': ['Enter a valid date (YYYY-MM-DD).']},
                )

        if 'languages_known' in payload:
            languages = payload['languages_known']
            if languages is None:
                employee.languages_known = []
            elif isinstance(languages, list):
                employee.languages_known = [str(item).strip() for item in languages if str(item).strip()]
            else:
                raise ValidationServiceError(
                    'languages_known must be a list.',
                    code='invalid_languages_known',
                    details={'languages_known': ['Provide a list of languages.']},
                )

        has_core = bool(employee.display_name and employee.mobile_number)
        employee.is_profile_completed = has_core
        employee.completed_status = 'done' if has_core else ''
        employee.updated_by = user
        employee.save()

        from apps.organization.services.lifecycle import EmployeeService

        if 'bank_details' in payload and payload['bank_details'] is not None:
            EmployeeService.replace_bank_details(
                employee=employee,
                rows=payload['bank_details'],
                user=user,
            )
        if 'education_details' in payload and payload['education_details'] is not None:
            EmployeeService.replace_education_details(
                employee=employee,
                rows=payload['education_details'],
                user=user,
            )
        if 'job_experiences' in payload and payload['job_experiences'] is not None:
            EmployeeService.replace_job_experiences(
                employee=employee,
                rows=payload['job_experiences'],
                user=user,
            )

        membership = None
        try:
            membership = cls.get_membership(user, branch_id=branch_id)
        except NotFoundServiceError:
            membership = (
                OrganizationMembership.objects.select_related(
                    'branch',
                    'branch__organization',
                    'access_type',
                )
                .filter(user=user, status=OrganizationMembership.Status.ACTIVE)
                .order_by('-created_at')
                .first()
            )
        return cls.serialize_profile(user=user, employee=employee, membership=membership)

    @classmethod
    def serialize_organization(cls, organization: Organization, *, can_edit: bool) -> dict:
        industry = organization.industry_type
        return {
            'id': str(organization.id),
            'organization_code': organization.organization_code,
            'legal_name': organization.legal_name,
            'display_name': organization.display_name,
            'industry_type_id': str(organization.industry_type_id) if organization.industry_type_id else None,
            'industry_type_name': industry.name if industry else None,
            'organization_size': organization.organization_size,
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
            'can_edit': can_edit,
        }

    @classmethod
    def serialize_branch(cls, branch) -> dict:
        return {
            'id': str(branch.id),
            'branch_code': branch.branch_code,
            'branch_name': branch.branch_name,
            'city': branch.city,
            'state': branch.state,
            'country': branch.country,
            'is_headquarters': branch.is_headquarters,
            'status': branch.status,
            'organization_id': str(branch.organization_id),
        }

    @classmethod
    def serialize_membership_summary(cls, membership: OrganizationMembership) -> dict:
        branch = membership.branch
        org = branch.organization
        return {
            'id': str(membership.id),
            'organization_id': str(org.id),
            'organization_name': org.display_name,
            'organization_logo': org.logo,
            'branch_id': str(branch.id),
            'branch_code': branch.branch_code,
            'branch_name': branch.branch_name,
            'is_headquarters': branch.is_headquarters,
            'employee_code': membership.employee_code,
            'status': membership.status,
            'access_type_id': str(membership.access_type_id) if membership.access_type_id else None,
            'access_type_name': membership.access_type.name if membership.access_type else None,
            'employee_type_id': str(membership.employee_type_id) if membership.employee_type_id else None,
            'employee_type_name': membership.employee_type.name if membership.employee_type else None,
            'designation_id': str(membership.designation_id) if membership.designation_id else None,
            'designation_name': membership.designation.name if membership.designation else None,
        }

    @classmethod
    def profile_photo_url(cls, employee: Employee) -> str:
        photo = employee.profile_photo
        if not photo:
            return ''
        name = getattr(photo, 'name', '') or str(photo)
        if not name:
            return ''
        if name.startswith('http://') or name.startswith('https://'):
            return name
        from django.conf import settings

        media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else f'{settings.MEDIA_URL}/'
        origin = settings.PUBLIC_API_ORIGIN.rstrip('/')
        return f'{origin}{media_url}{name.lstrip("/")}'

    @classmethod
    def serialize_profile(
        cls,
        *,
        user: User,
        employee: Employee,
        membership: OrganizationMembership | None,
    ) -> dict:
        return {
            'id': str(employee.id),
            'user_id': str(user.id),
            'email': user.email or employee.email,
            'first_name': employee.first_name or user.first_name,
            'last_name': employee.last_name or user.last_name,
            'full_name': user.full_name,
            'display_name': employee.display_name,
            'profile_photo': cls.profile_photo_url(employee),
            'mobile_number': employee.mobile_number,
            'alternate_mobile': employee.alternate_mobile,
            'emergency_contact_name': employee.emergency_contact_name,
            'emergency_contact_relationship': employee.emergency_contact_relationship,
            'emergency_contact_phone': employee.emergency_contact_phone,
            'bank_details': [
                {
                    'id': str(row.id),
                    'account_holder_name': row.account_holder_name,
                    'bank_name': row.bank_name,
                    'account_number': row.account_number,
                    'ifsc_code': row.ifsc_code,
                    'is_primary': row.is_primary,
                }
                for row in employee.bank_details.all()
            ],
            'education_details': [
                {
                    'id': str(row.id),
                    'degree': row.degree,
                    'institution': row.institution,
                    'field_of_study': row.field_of_study,
                    'year_of_passing': row.year_of_passing,
                    'grade': row.grade,
                }
                for row in employee.education_details.all()
            ],
            'job_experiences': [
                {
                    'id': str(row.id),
                    'company_name': row.company_name,
                    'job_title': row.job_title,
                    'start_date': row.start_date.isoformat() if row.start_date else None,
                    'end_date': row.end_date.isoformat() if row.end_date else None,
                    'is_current': row.is_current,
                    'location': row.location,
                    'description': row.description,
                }
                for row in employee.job_experiences.all()
            ],
            'date_of_birth': employee.date_of_birth.isoformat() if employee.date_of_birth else None,
            'gender': employee.gender,
            'blood_group': employee.blood_group,
            'country': employee.country,
            'state': employee.state,
            'city': employee.city,
            'address_line1': employee.address_line1,
            'postal_code': employee.postal_code,
            'mother_language': employee.mother_language,
            'languages_known': employee.languages_known or [],
            'is_profile_completed': employee.is_profile_completed,
            'employee_code': employee.employee_code or (membership.employee_code if membership else None),
            'organization_id': str(employee.organization_id),
            'organization_name': employee.organization.display_name,
            'branch_id': str(employee.branch_id) if employee.branch_id else (
                str(membership.branch_id) if membership else None
            ),
            'branch_name': (
                employee.branch.branch_name if employee.branch_id else (
                    membership.branch.branch_name if membership else None
                )
            ),
            'access_type_name': (
                employee.access_type.name if employee.access_type else (
                    membership.access_type.name if membership and membership.access_type else None
                )
            ),
        }
