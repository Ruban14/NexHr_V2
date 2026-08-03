"""Employee CRUD and lifecycle operations."""

from __future__ import annotations

import re
import uuid
from datetime import date, timedelta
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.authentication.models import User
from apps.core.exceptions import (
    ConflictServiceError,
    NotFoundServiceError,
    PermissionDeniedServiceError,
    ValidationServiceError,
)
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
)
from apps.workforce.models import (
    EmployeeLifecycleStatus,
)
from apps.people.models import (
    Employee,
    EmployeeBankDetail,
    EmployeeEducation,
    EmployeeJobExperience,
    EmployeeLifecycleHistory,
    EmployeeTaxDetail,
)
from apps.organizations.services.workspace_service import WorkspaceService


from apps.people.services.employee_lifecycle_service import EmployeeLifecycleEngine

class EmployeeService:
    """Employee CRUD + lifecycle operations for the current organization."""

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        if not is_owner and access_name not in {'admin', 'administrator'}:
            raise PermissionDeniedServiceError(
                'Only organization admins can manage employees.',
                code='not_organization_admin',
            )
        return membership

    @classmethod
    def _organization(cls, membership: OrganizationMembership):
        return membership.branch.organization

    @classmethod
    def serialize_bank_detail(cls, detail: EmployeeBankDetail) -> dict:
        return {
            'id': str(detail.id),
            'account_holder_name': detail.account_holder_name,
            'bank_name': detail.bank_name,
            'account_number': detail.account_number,
            'ifsc_code': detail.ifsc_code,
            'is_primary': detail.is_primary,
        }

    @classmethod
    def serialize_education(cls, row: EmployeeEducation) -> dict:
        return {
            'id': str(row.id),
            'degree': row.degree,
            'institution': row.institution,
            'field_of_study': row.field_of_study,
            'year_of_passing': row.year_of_passing,
            'grade': row.grade,
        }

    @classmethod
    def serialize_job_experience(cls, row: EmployeeJobExperience) -> dict:
        return {
            'id': str(row.id),
            'company_name': row.company_name,
            'job_title': row.job_title,
            'start_date': row.start_date.isoformat() if row.start_date else None,
            'end_date': row.end_date.isoformat() if row.end_date else None,
            'is_current': row.is_current,
            'location': row.location,
            'description': row.description,
        }

    @classmethod
    def serialize_tax_detail(cls, detail: EmployeeTaxDetail | None) -> dict:
        if detail is None:
            return {
                'pan_number': '',
                'aadhaar_number': '',
                'uan_number': '',
                'pf_number': '',
                'esi_number': '',
                'tax_regime': EmployeeTaxDetail.TaxRegime.NEW,
                'tax_identification_number': '',
                'is_pf_applicable': True,
                'is_esi_applicable': False,
                'professional_tax_applicable': False,
                'labour_welfare_fund_applicable': False,
            }
        return {
            'id': str(detail.id),
            'pan_number': detail.pan_number,
            'aadhaar_number': detail.aadhaar_number,
            'uan_number': detail.uan_number,
            'pf_number': detail.pf_number,
            'esi_number': detail.esi_number,
            'tax_regime': detail.tax_regime,
            'tax_identification_number': detail.tax_identification_number,
            'is_pf_applicable': detail.is_pf_applicable,
            'is_esi_applicable': detail.is_esi_applicable,
            'professional_tax_applicable': detail.professional_tax_applicable,
            'labour_welfare_fund_applicable': detail.labour_welfare_fund_applicable,
        }

    @classmethod
    def upsert_tax_detail(cls, *, employee: Employee, payload: dict, user: User) -> EmployeeTaxDetail:
        detail, _created = EmployeeTaxDetail.objects.get_or_create(
            employee=employee,
            defaults={'created_by': user, 'updated_by': user},
        )
        string_fields = (
            'pan_number',
            'aadhaar_number',
            'uan_number',
            'pf_number',
            'esi_number',
            'tax_identification_number',
        )
        for field in string_fields:
            if field in payload and payload[field] is not None:
                value = str(payload[field]).strip()
                if field == 'pan_number':
                    value = value.upper().replace(' ', '')
                if field == 'aadhaar_number':
                    value = ''.join(ch for ch in value if ch.isdigit())
                setattr(detail, field, value)

        if 'tax_regime' in payload and payload['tax_regime'] is not None:
            regime = str(payload['tax_regime']).strip().lower()
            if regime not in {EmployeeTaxDetail.TaxRegime.OLD, EmployeeTaxDetail.TaxRegime.NEW}:
                raise ValidationServiceError(
                    'Tax regime must be old or new.',
                    code='invalid_tax_regime',
                    details={'tax_regime': ['Select Old Regime or New Regime.']},
                )
            detail.tax_regime = regime

        bool_fields = (
            'is_pf_applicable',
            'is_esi_applicable',
            'professional_tax_applicable',
            'labour_welfare_fund_applicable',
        )
        for field in bool_fields:
            if field in payload and payload[field] is not None:
                value = payload[field]
                if isinstance(value, str):
                    value = value.strip().lower() in {'1', 'true', 'yes', 'on'}
                setattr(detail, field, bool(value))

        pan = detail.pan_number
        if pan and not re.fullmatch(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
            raise ValidationServiceError(
                'Enter a valid PAN (e.g. ABCDE1234F).',
                code='invalid_pan',
                details={'tax_detail.pan_number': ['Enter a valid PAN (e.g. ABCDE1234F).']},
            )
        aadhaar = detail.aadhaar_number
        if aadhaar and not re.fullmatch(r'^\d{12}$', aadhaar):
            raise ValidationServiceError(
                'Enter a valid 12-digit Aadhaar number.',
                code='invalid_aadhaar',
                details={'tax_detail.aadhaar_number': ['Enter a valid 12-digit Aadhaar number.']},
            )

        detail.updated_by = user
        if not detail.created_by_id:
            detail.created_by = user
        detail.save()
        return detail

    @classmethod
    def replace_bank_details(cls, *, employee: Employee, rows: list, user: User) -> None:
        employee.bank_details.all().delete()
        if not rows:
            return
        primary_index = next(
            (index for index, row in enumerate(rows) if bool(row.get('is_primary'))),
            0,
        )
        for index, row in enumerate(rows):
            EmployeeBankDetail.objects.create(
                employee=employee,
                account_holder_name=(row.get('account_holder_name') or '').strip(),
                bank_name=(row.get('bank_name') or '').strip(),
                account_number=(row.get('account_number') or '').strip(),
                ifsc_code=(row.get('ifsc_code') or '').strip().upper(),
                is_primary=index == primary_index,
                created_by=user,
                updated_by=user,
            )

    @classmethod
    def replace_education_details(cls, *, employee: Employee, rows: list, user: User) -> None:
        employee.education_details.all().delete()
        for row in rows or []:
            year = row.get('year_of_passing')
            EmployeeEducation.objects.create(
                employee=employee,
                degree=(row.get('degree') or '').strip(),
                institution=(row.get('institution') or '').strip(),
                field_of_study=(row.get('field_of_study') or '').strip(),
                year_of_passing=year if year not in ('', None) else None,
                grade=(row.get('grade') or '').strip(),
                created_by=user,
                updated_by=user,
            )

    @classmethod
    def replace_job_experiences(cls, *, employee: Employee, rows: list, user: User) -> None:
        employee.job_experiences.all().delete()
        for row in rows or []:
            is_current = bool(row.get('is_current'))
            EmployeeJobExperience.objects.create(
                employee=employee,
                company_name=(row.get('company_name') or '').strip(),
                job_title=(row.get('job_title') or '').strip(),
                start_date=row.get('start_date') or None,
                end_date=None if is_current else (row.get('end_date') or None),
                is_current=is_current,
                location=(row.get('location') or '').strip(),
                description=(row.get('description') or '').strip(),
                created_by=user,
                updated_by=user,
            )

    @classmethod
    def serialize_employee(cls, employee: Employee, *, include_actions: bool = False) -> dict:
        from apps.organizations.services.workspace_service import WorkspaceService

        status = employee.lifecycle_status
        payload = {
            'id': str(employee.id),
            'organization_id': str(employee.organization_id),
            'branch_id': str(employee.branch_id) if employee.branch_id else None,
            'user_id': str(employee.user_id) if employee.user_id else None,
            'employee_code': employee.employee_code,
            'email': employee.email,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'display_name': employee.display_name
            or ' '.join(part for part in [employee.first_name, employee.last_name] if part).strip()
            or employee.email
            or 'Employee',
            'profile_photo': WorkspaceService.profile_photo_url(employee),
            'mobile_number': employee.mobile_number,
            'alternate_mobile': employee.alternate_mobile,
            'emergency_contact_name': employee.emergency_contact_name,
            'emergency_contact_relationship': employee.emergency_contact_relationship,
            'emergency_contact_phone': employee.emergency_contact_phone,
            'bank_details': [cls.serialize_bank_detail(row) for row in employee.bank_details.all()],
            'education_details': [cls.serialize_education(row) for row in employee.education_details.all()],
            'job_experiences': [
                cls.serialize_job_experience(row) for row in employee.job_experiences.all()
            ],
            'tax_detail': cls.serialize_tax_detail(getattr(employee, 'tax_detail', None)),
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
            'joining_date': employee.joining_date.isoformat() if employee.joining_date else None,
            'exit_date': employee.exit_date.isoformat() if employee.exit_date else None,
            'is_active': employee.is_active,
            'designation_id': str(employee.designation_id) if employee.designation_id else None,
            'designation_name': employee.designation.name if employee.designation_id else None,
            'reporting_manager_id': (
                str(employee.reporting_manager_id) if employee.reporting_manager_id else None
            ),
            'reporting_manager_name': (
                (
                    employee.reporting_manager.display_name
                    or ' '.join(
                        part
                        for part in [
                            employee.reporting_manager.first_name,
                            employee.reporting_manager.last_name,
                        ]
                        if part
                    ).strip()
                    or employee.reporting_manager.email
                )
                if employee.reporting_manager_id
                else None
            ),
            'employee_type_id': str(employee.employee_type_id) if employee.employee_type_id else None,
            'employee_type_name': employee.employee_type.name if employee.employee_type_id else None,
            'access_type_id': str(employee.access_type_id) if employee.access_type_id else None,
            'access_type_name': employee.access_type.name if employee.access_type_id else None,
            'is_email_verified': bool(employee.user and employee.user.is_email_verified),
            'email_editable': not bool(employee.user and employee.user.is_email_verified),
            'lifecycle_status': EmployeeLifecycleEngine.serialize_status(status),
            'created_at': employee.created_at.isoformat(),
            'updated_at': employee.updated_at.isoformat(),
        }
        if include_actions:
            payload['available_transitions'] = [
                EmployeeLifecycleEngine.serialize_transition(item)
                for item in EmployeeLifecycleEngine.get_available_transitions(from_status=status)
            ]
        return payload

    @classmethod
    def list_employees(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        lifecycle_status_id: str | UUID | None = None,
    ) -> dict:
        from django.db.models import Q

        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = (
            Employee.objects.select_related('lifecycle_status')
            .filter(organization=membership.branch.organization)
            .order_by('-created_at')
        )
        if lifecycle_status_id:
            qs = qs.filter(lifecycle_status_id=lifecycle_status_id)
        if search:
            term = search.strip()
            qs = qs.filter(
                Q(display_name__icontains=term)
                | Q(first_name__icontains=term)
                | Q(last_name__icontains=term)
                | Q(email__icontains=term)
                | Q(employee_code__icontains=term)
            )
        return cls._paginate(qs, page=page, page_size=page_size)

    @classmethod
    def get_employee(cls, *, user: User, branch_id: str | UUID | None, employee_id: str | UUID) -> dict:
        from django.db.models import Q

        from apps.workforce.models import AccessType, Designation, EmployeeType

        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        employee = (
            Employee.objects.select_related(
                'lifecycle_status',
                'designation',
                'employee_type',
                'access_type',
                'reporting_manager',
                'user',
                'tax_detail',
            )
            .prefetch_related('bank_details', 'education_details', 'job_experiences')
            .filter(id=employee_id, organization=organization)
            .first()
        )
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')
        data = cls.serialize_employee(employee, include_actions=True)
        data['timeline_statuses'] = [
            EmployeeLifecycleEngine.serialize_status(item)
            for item in EmployeeLifecycleEngine.list_statuses(active_only=True)
        ]
        data['history'] = [
            EmployeeLifecycleEngine.serialize_history(row)
            for row in employee.lifecycle_history.select_related(
                'from_status',
                'to_status',
                'changed_by',
            ).order_by('-changed_at')[:100]
        ]
        data['master_options'] = {
            'employee_types': [
                {'id': str(item.id), 'name': item.name}
                for item in EmployeeType.objects.filter(is_active=True).order_by('name')
            ],
            'access_types': [
                {'id': str(item.id), 'name': item.name}
                for item in AccessType.objects.filter(
                    Q(industry_type_id=organization.industry_type_id) | Q(industry_type__isnull=True),
                    is_active=True,
                ).order_by('name')
            ],
            'designations': [
                {
                    'id': str(item.id),
                    'name': item.name,
                    'department_name': item.department.name if item.department_id else '',
                }
                for item in Designation.objects.select_related('department')
                .filter(department__organization=organization, is_active=True)
                .order_by('department__name', 'name')
            ],
        }
        return data

    @classmethod
    def _ensure_unique_email(
        cls,
        *,
        organization_id,
        email: str,
        exclude_employee_id=None,
    ) -> str:
        normalized = (email or '').strip().lower()
        if not normalized:
            return ''
        qs = Employee.objects.filter(organization_id=organization_id, email__iexact=normalized)
        if exclude_employee_id is not None:
            qs = qs.exclude(id=exclude_employee_id)
        if qs.exists():
            raise ConflictServiceError(
                'An employee with this email already exists in the organization.',
                code='employee_email_exists',
                details={'email': ['This email is already in use.']},
            )
        return normalized

    @classmethod
    def _generate_employee_code(cls, organization: Organization) -> str:
        """Assign the next org-scoped code like ACME-001, ACME-002, …"""
        prefix = re.sub(r'[^A-Z0-9]', '', (organization.organization_code or '').upper())[:6] or 'EMP'
        stem = f'{prefix}-'
        max_n = 0
        for code in Employee.objects.filter(
            organization_id=organization.id,
            employee_code__istartswith=stem,
        ).values_list('employee_code', flat=True):
            suffix = str(code)[len(stem) :]
            if suffix.isdigit():
                max_n = max(max_n, int(suffix))

        for offset in range(1, 10_000):
            candidate = f'{prefix}-{max_n + offset:03d}'
            if not Employee.objects.filter(
                organization_id=organization.id,
                employee_code__iexact=candidate,
            ).exists():
                return candidate
        return f'{prefix}-{uuid.uuid4().hex[:8].upper()}'

    @classmethod
    def _create_login_user(
        cls,
        *,
        email: str,
        first_name: str,
        last_name: str,
        temporary_password: str,
    ) -> User:
        if User.objects.filter(email__iexact=email).exists():
            raise ConflictServiceError(
                'A user account with this email already exists.',
                code='user_email_exists',
                details={'email': ['This email is already registered.']},
            )
        return User.objects.create_user(
            email=email,
            password=temporary_password,
            first_name=first_name,
            last_name=last_name,
            is_email_verified=True,
            is_active=True,
            must_change_password=True,
        )

    @classmethod
    def accept_invite_on_login(cls, *, user: User) -> None:
        """Move draft invitees into onboarding and activate pending memberships."""
        onboarding = EmployeeLifecycleStatus.objects.filter(
            key='onboarding_started',
            is_active=True,
        ).first()
        if onboarding is None:
            return

        employees = (
            Employee.objects.select_related('lifecycle_status')
            .filter(user=user, lifecycle_status__key='draft')
        )
        for employee in employees:
            if not EmployeeLifecycleEngine.can_transition(
                from_status=employee.lifecycle_status,
                to_status=onboarding,
            ):
                continue
            EmployeeLifecycleEngine.apply_transition(
                employee=employee,
                to_status=onboarding,
                changed_by=user,
                remarks='Invite accepted on first login',
            )

        OrganizationMembership.objects.filter(
            user=user,
            status=OrganizationMembership.Status.PENDING,
        ).update(
            status=OrganizationMembership.Status.ACTIVE,
            updated_by=user,
        )

    @classmethod
    @transaction.atomic
    def create_employee(cls, *, user: User, branch_id: str | UUID | None, payload: dict) -> dict:
        from django.conf import settings

        from apps.authentication.services.email import EmailService

        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        initial = EmployeeLifecycleEngine.get_initial_status()

        display_name = (payload.get('display_name') or '').strip()
        first_name = (payload.get('first_name') or '').strip()
        last_name = (payload.get('last_name') or '').strip()
        if not display_name:
            display_name = ' '.join(part for part in [first_name, last_name] if part).strip()

        email = cls._ensure_unique_email(
            organization_id=organization.id,
            email=payload.get('email') or '',
        )
        if not email:
            raise ValidationServiceError(
                'Email is required to create an employee account.',
                code='employee_email_required',
                details={'email': ['Enter a valid email address.']},
            )

        employee_code = cls._generate_employee_code(organization)

        temporary_password = settings.EMPLOYEE_DEFAULT_PASSWORD
        account = cls._create_login_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            temporary_password=temporary_password,
        )

        employee = Employee.objects.create(
            organization=organization,
            branch=membership.branch,
            user=account,
            lifecycle_status=initial,
            email=email,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            employee_code=employee_code,
            designation_id=payload.get('designation_id') or None,
            employee_type_id=payload.get('employee_type_id') or None,
            access_type_id=payload.get('access_type_id') or None,
            joining_date=payload.get('joining_date'),
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        OrganizationMembership.objects.create(
            branch=membership.branch,
            user=account,
            designation_id=payload.get('designation_id') or None,
            employee_type_id=payload.get('employee_type_id') or None,
            access_type_id=payload.get('access_type_id') or None,
            employee_code=employee_code,
            status=OrganizationMembership.Status.PENDING,
            joining_date=payload.get('joining_date'),
            created_by=user,
            updated_by=user,
        )
        EmployeeLifecycleHistory.objects.create(
            employee=employee,
            from_status=None,
            to_status=initial,
            changed_by=user,
            remarks='Employee created and invite sent',
        )

        EmailService.send_employee_invite_email(
            email=email,
            display_name=display_name or first_name or email,
            organization_name=organization.display_name or organization.legal_name,
            temporary_password=temporary_password,
        )
        return cls.serialize_employee(employee, include_actions=True)

    @classmethod
    @transaction.atomic
    def update_employee(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        employee = Employee.objects.filter(
            id=employee_id,
            organization=membership.branch.organization,
        ).first()
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')

        if 'email' in payload and payload['email'] is not None:
            linked = employee.user
            if linked is not None and linked.is_email_verified:
                raise ValidationServiceError(
                    'Email cannot be changed after it has been verified.',
                    code='email_locked',
                    details={'email': ['Verified email addresses cannot be edited.']},
                )
            employee.email = cls._ensure_unique_email(
                organization_id=employee.organization_id,
                email=str(payload['email']),
                exclude_employee_id=employee.id,
            )

        for field in ('first_name', 'last_name', 'display_name'):
            if field in payload and payload[field] is not None:
                setattr(employee, field, str(payload[field]).strip())

        profile_fields = (
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
        )
        for field in profile_fields:
            if field in payload and payload[field] is not None:
                setattr(employee, field, str(payload[field]).strip())

        if 'date_of_birth' in payload:
            employee.date_of_birth = payload['date_of_birth'] or None

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

        if payload.get('clear_profile_photo'):
            if employee.profile_photo:
                employee.profile_photo.delete(save=False)
            employee.profile_photo = ''
        elif payload.get('profile_photo') is not None:
            if employee.profile_photo:
                employee.profile_photo.delete(save=False)
            employee.profile_photo = payload['profile_photo']

        for field in ('joining_date', 'exit_date', 'is_active'):
            if field in payload:
                setattr(employee, field, payload[field])

        for field, attr in (
            ('designation_id', 'designation_id'),
            ('employee_type_id', 'employee_type_id'),
            ('access_type_id', 'access_type_id'),
            ('branch_id', 'branch_id'),
        ):
            if field in payload:
                setattr(employee, attr, payload[field] or None)

        if 'reporting_manager_id' in payload:
            manager_id = payload.get('reporting_manager_id') or None
            if manager_id:
                if str(manager_id) == str(employee.id):
                    raise ValidationServiceError(
                        'An employee cannot report to themselves.',
                        code='invalid_reporting_manager',
                        details={'reporting_manager_id': ['Select a different employee.']},
                    )
                manager = Employee.objects.filter(
                    id=manager_id,
                    organization_id=employee.organization_id,
                    is_active=True,
                ).first()
                if manager is None:
                    raise NotFoundServiceError(
                        'Reporting manager not found in this organization.',
                        code='reporting_manager_not_found',
                        details={'reporting_manager_id': ['Select a valid employee.']},
                    )
                # Prevent cycles: manager (or anyone above) must not already report to employee.
                cursor = manager
                seen = {employee.id}
                while cursor is not None:
                    if cursor.id in seen:
                        raise ValidationServiceError(
                            'This reporting manager would create a circular hierarchy.',
                            code='reporting_manager_cycle',
                            details={'reporting_manager_id': ['Choose a manager outside this chain.']},
                        )
                    seen.add(cursor.id)
                    cursor = cursor.reporting_manager
                employee.reporting_manager = manager
            else:
                employee.reporting_manager = None

        if not employee.display_name:
            employee.display_name = ' '.join(
                part for part in [employee.first_name, employee.last_name] if part
            ).strip()

        employee.is_profile_completed = bool(employee.display_name and employee.mobile_number)
        employee.completed_status = 'done' if employee.is_profile_completed else ''
        employee.updated_by = user
        employee.save()

        if 'bank_details' in payload and payload['bank_details'] is not None:
            cls.replace_bank_details(employee=employee, rows=payload['bank_details'], user=user)
        if 'education_details' in payload and payload['education_details'] is not None:
            cls.replace_education_details(employee=employee, rows=payload['education_details'], user=user)
        if 'job_experiences' in payload and payload['job_experiences'] is not None:
            cls.replace_job_experiences(employee=employee, rows=payload['job_experiences'], user=user)
        if 'tax_detail' in payload and payload['tax_detail'] is not None:
            cls.upsert_tax_detail(employee=employee, payload=payload['tax_detail'], user=user)

        linked_user = employee.user
        if linked_user is not None:
            user_fields: list[str] = []
            if 'first_name' in payload and payload['first_name'] is not None:
                linked_user.first_name = employee.first_name
                user_fields.append('first_name')
            if 'last_name' in payload and payload['last_name'] is not None:
                linked_user.last_name = employee.last_name
                user_fields.append('last_name')
            if 'email' in payload and payload['email'] is not None and employee.email:
                if (
                    linked_user.email != employee.email
                    and User.objects.filter(email__iexact=employee.email)
                    .exclude(id=linked_user.id)
                    .exists()
                ):
                    raise ConflictServiceError(
                        'A user account with this email already exists.',
                        code='user_email_exists',
                        details={'email': ['This email is already registered.']},
                    )
                linked_user.email = employee.email
                user_fields.append('email')
            if user_fields:
                linked_user.save(update_fields=[*user_fields, 'updated_at'])

        return cls.get_employee(user=user, branch_id=branch_id, employee_id=employee.id)

    @classmethod
    @transaction.atomic
    def transition_employee(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        to_status_id: str | UUID,
        remarks: str = '',
        exit_date: date | None = None,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        employee = (
            Employee.objects.select_related('lifecycle_status', 'organization')
            .filter(id=employee_id, organization=membership.branch.organization)
            .first()
        )
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')

        to_status = EmployeeLifecycleStatus.objects.filter(id=to_status_id, is_active=True).first()
        if to_status is None:
            raise NotFoundServiceError('Lifecycle status not found.', code='lifecycle_status_not_found')

        EmployeeLifecycleEngine.apply_transition(
            employee=employee,
            to_status=to_status,
            changed_by=user,
            remarks=remarks,
            exit_date=exit_date,
        )
        employee.refresh_from_db()
        return cls.get_employee(user=user, branch_id=branch_id, employee_id=employee.id)

    @classmethod
    def list_lifecycle_config(cls, *, user: User, branch_id: str | UUID | None) -> dict:
        WorkspaceService.get_membership(user, branch_id=branch_id)
        statuses = EmployeeLifecycleEngine.list_statuses(active_only=False)
        transitions = (
            EmployeeLifecycleTransition.objects.select_related('from_status', 'to_status')
            .filter(is_active=True)
            .order_by('sort_order', 'action_label')
        )
        return {
            'statuses': [EmployeeLifecycleEngine.serialize_status(item) for item in statuses if item.is_active],
            'transitions': [EmployeeLifecycleEngine.serialize_transition(item) for item in transitions],
        }

    @classmethod
    def _paginate(cls, qs, *, page: int, page_size: int) -> dict:
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 20)))
        total = qs.count()
        start = (page - 1) * page_size
        items = [cls.serialize_employee(row) for row in qs[start : start + page_size]]
        return {
            'items': items,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': max(1, (total + page_size - 1) // page_size),
            },
        }
