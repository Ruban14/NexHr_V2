"""Workspace services for current organization, branch context, and user profile."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db import transaction

from apps.authentication.models import User
from apps.core.exceptions import NotFoundServiceError, PermissionDeniedServiceError, ValidationServiceError
from apps.organization.models import IndustryType, Organization, OrganizationMembership, UserProfile


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
        }
        for payload_key, model_field in field_map.items():
            if payload_key in payload:
                value = payload[payload_key]
                if payload_key == 'currency' and value:
                    value = str(value).upper()
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
        profile = UserProfile.objects.filter(user=user).first()
        if profile is None:
            raise NotFoundServiceError('User profile not found.', code='profile_not_found')
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
        return cls.serialize_profile(user=user, profile=profile, membership=membership)

    @classmethod
    @transaction.atomic
    def update_profile(
        cls,
        *,
        user: User,
        payload: dict,
        branch_id: str | UUID | None = None,
    ) -> dict:
        profile = UserProfile.objects.filter(user=user).first()
        if profile is None:
            raise NotFoundServiceError('User profile not found.', code='profile_not_found')

        user_updates: list[str] = []
        if 'first_name' in payload:
            user.first_name = payload['first_name'] or ''
            user_updates.append('first_name')
        if 'last_name' in payload:
            user.last_name = payload['last_name'] or ''
            user_updates.append('last_name')
        if user_updates:
            user.save(update_fields=[*user_updates, 'updated_at'])

        profile_fields = {
            'display_name',
            'profile_photo',
            'mobile_number',
            'alternate_mobile',
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
                setattr(profile, field, value if value is not None else '')

        if 'date_of_birth' in payload:
            dob = payload['date_of_birth']
            if dob in (None, ''):
                profile.date_of_birth = None
            elif isinstance(dob, date):
                profile.date_of_birth = dob
            else:
                raise ValidationServiceError(
                    'Enter a valid date of birth.',
                    code='invalid_date_of_birth',
                    details={'date_of_birth': ['Enter a valid date (YYYY-MM-DD).']},
                )

        if 'languages_known' in payload:
            languages = payload['languages_known']
            if languages is None:
                profile.languages_known = []
            elif isinstance(languages, list):
                profile.languages_known = [str(item).strip() for item in languages if str(item).strip()]
            else:
                raise ValidationServiceError(
                    'languages_known must be a list.',
                    code='invalid_languages_known',
                    details={'languages_known': ['Provide a list of languages.']},
                )

        has_core = bool(profile.display_name and profile.mobile_number)
        profile.is_profile_completed = has_core
        profile.completed_status = 'done' if has_core else ''
        profile.updated_by = user
        profile.save()

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
        return cls.serialize_profile(user=user, profile=profile, membership=membership)

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
    def serialize_profile(
        cls,
        *,
        user: User,
        profile: UserProfile,
        membership: OrganizationMembership | None,
    ) -> dict:
        return {
            'id': str(profile.id),
            'user_id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'display_name': profile.display_name,
            'profile_photo': profile.profile_photo,
            'mobile_number': profile.mobile_number,
            'alternate_mobile': profile.alternate_mobile,
            'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            'gender': profile.gender,
            'blood_group': profile.blood_group,
            'country': profile.country,
            'state': profile.state,
            'city': profile.city,
            'address_line1': profile.address_line1,
            'postal_code': profile.postal_code,
            'mother_language': profile.mother_language,
            'languages_known': profile.languages_known or [],
            'is_profile_completed': profile.is_profile_completed,
            'employee_code': membership.employee_code if membership else None,
            'organization_id': (
                str(membership.branch.organization_id) if membership else None
            ),
            'organization_name': (
                membership.branch.organization.display_name if membership else None
            ),
            'branch_id': str(membership.branch_id) if membership else None,
            'branch_name': membership.branch.branch_name if membership else None,
            'access_type_name': (
                membership.access_type.name if membership and membership.access_type else None
            ),
        }
