"""Leave policy CRUD for organization setup."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.db import transaction
from django.db.models import Q

from apps.authentication.models import User
from apps.core.exceptions import (
    ConflictServiceError,
    NotFoundServiceError,
    PermissionDeniedServiceError,
    ValidationServiceError,
)
from apps.organizations.models import (
    OrganizationMembership,
)
from apps.workforce.models import (
    EmployeeType,
    LeaveType,
)
from apps.leave.models import (
    LeavePolicy,
    LeavePolicyRule,
)
from apps.organization.services.workspace import WorkspaceService


class LeavePolicyService:
    """CRUD for leave policies and entitlement rules."""

    ALLOCATION_FREQUENCIES = {choice.value for choice in LeavePolicyRule.AllocationFrequency}

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        if not is_owner and access_name not in {'admin', 'administrator'}:
            raise PermissionDeniedServiceError(
                'Only organization admins can manage leave policies.',
                code='not_organization_admin',
            )
        return membership

    @classmethod
    def _organization(cls, membership: OrganizationMembership):
        return membership.branch.organization

    @classmethod
    def _paginate(cls, qs, *, page: int, page_size: int, serialize) -> dict:
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 20)))
        total = qs.count()
        start = (page - 1) * page_size
        items = list(qs[start : start + page_size])
        return {
            'items': [serialize(item) for item in items],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': max(1, (total + page_size - 1) // page_size),
            },
        }

    @classmethod
    def _decimal(cls, value, *, field: str, default: Decimal = Decimal('0')) -> Decimal:
        if value in (None, ''):
            return default
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationServiceError(f'Invalid value for {field}.', code='invalid_decimal') from exc

    @classmethod
    def _clear_other_defaults(cls, *, organization, employee_type, exclude_id=None, user: User) -> None:
        qs = LeavePolicy.objects.filter(
            organization=organization,
            employee_type=employee_type,
            is_default=True,
        )
        if exclude_id is not None:
            qs = qs.exclude(id=exclude_id)
        qs.update(is_default=False, updated_by=user)

    @classmethod
    def list_leave_policies(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        employee_type_id: str | UUID | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = (
            LeavePolicy.objects.filter(organization=membership.branch.organization)
            .select_related('employee_type')
            .prefetch_related('rules__leave_type')
        )
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if employee_type_id:
            qs = qs.filter(employee_type_id=employee_type_id)
        if search:
            term = search.strip()
            qs = qs.filter(
                Q(name__icontains=term)
                | Q(code__icontains=term)
                | Q(description__icontains=term)
                | Q(employee_type__name__icontains=term)
            )
        return cls._paginate(
            qs.order_by('-is_default', 'name'),
            page=page,
            page_size=page_size,
            serialize=cls.serialize_leave_policy,
        )

    @classmethod
    def get_leave_policy(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        item = (
            LeavePolicy.objects.filter(id=item_id, organization=membership.branch.organization)
            .select_related('employee_type')
            .prefetch_related('rules__leave_type')
            .first()
        )
        if item is None:
            raise NotFoundServiceError('Leave policy not found.', code='leave_policy_not_found')
        return cls.serialize_leave_policy(item)

    @classmethod
    @transaction.atomic
    def create_leave_policy(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)

        code = str(payload.get('code') or '').strip().upper()
        name = str(payload.get('name') or '').strip()
        if len(code) < 2:
            raise ValidationServiceError('Policy code must be at least 2 characters.', code='invalid_code')
        if len(name) < 2:
            raise ValidationServiceError('Policy name must be at least 2 characters.', code='invalid_name')

        employee_type = EmployeeType.objects.filter(
            id=payload['employee_type_id'],
            is_active=True,
        ).first()
        if employee_type is None:
            raise NotFoundServiceError('Employee type not found.', code='employee_type_not_found')

        if LeavePolicy.objects.filter(organization=organization, code__iexact=code).exists():
            raise ConflictServiceError('A leave policy with this code already exists.', code='policy_code_exists')

        effective_from = payload.get('effective_from')
        if effective_from is None:
            raise ValidationServiceError('Effective from date is required.', code='invalid_effective_from')
        effective_to = payload.get('effective_to')
        if effective_to and effective_to < effective_from:
            raise ValidationServiceError(
                'Effective to must be on or after effective from.',
                code='invalid_effective_range',
            )

        is_default = bool(payload.get('is_default', False))
        if is_default:
            cls._clear_other_defaults(
                organization=organization,
                employee_type=employee_type,
                user=user,
            )

        policy = LeavePolicy.objects.create(
            organization=organization,
            employee_type=employee_type,
            code=code,
            name=name,
            description=str(payload.get('description') or '').strip(),
            effective_from=effective_from,
            effective_to=effective_to,
            is_default=is_default,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        cls._replace_rules(
            policy=policy,
            organization=organization,
            rules=payload.get('rules') or [],
            user=user,
        )
        return cls.get_leave_policy(user=user, branch_id=branch_id, item_id=policy.id)

    @classmethod
    @transaction.atomic
    def update_leave_policy(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        policy = LeavePolicy.objects.filter(id=item_id, organization=organization).first()
        if policy is None:
            raise NotFoundServiceError('Leave policy not found.', code='leave_policy_not_found')

        employee_type = policy.employee_type
        if 'employee_type_id' in payload and payload['employee_type_id'] is not None:
            employee_type = EmployeeType.objects.filter(
                id=payload['employee_type_id'],
                is_active=True,
            ).first()
            if employee_type is None:
                raise NotFoundServiceError('Employee type not found.', code='employee_type_not_found')
            policy.employee_type = employee_type

        if 'code' in payload and payload['code'] is not None:
            code = str(payload['code']).strip().upper()
            if len(code) < 2:
                raise ValidationServiceError('Policy code must be at least 2 characters.', code='invalid_code')
            if (
                LeavePolicy.objects.filter(organization=organization, code__iexact=code)
                .exclude(id=policy.id)
                .exists()
            ):
                raise ConflictServiceError(
                    'A leave policy with this code already exists.',
                    code='policy_code_exists',
                )
            policy.code = code

        if 'name' in payload and payload['name'] is not None:
            name = str(payload['name']).strip()
            if len(name) < 2:
                raise ValidationServiceError('Policy name must be at least 2 characters.', code='invalid_name')
            policy.name = name

        if 'description' in payload and payload['description'] is not None:
            policy.description = str(payload['description']).strip()

        if 'effective_from' in payload and payload['effective_from'] is not None:
            policy.effective_from = payload['effective_from']

        if 'effective_to' in payload:
            policy.effective_to = payload['effective_to']

        if policy.effective_to and policy.effective_from and policy.effective_to < policy.effective_from:
            raise ValidationServiceError(
                'Effective to must be on or after effective from.',
                code='invalid_effective_range',
            )

        if 'is_default' in payload and payload['is_default'] is not None:
            policy.is_default = bool(payload['is_default'])
            if policy.is_default:
                cls._clear_other_defaults(
                    organization=organization,
                    employee_type=employee_type,
                    exclude_id=policy.id,
                    user=user,
                )

        if 'is_active' in payload and payload['is_active'] is not None:
            policy.is_active = bool(payload['is_active'])

        policy.updated_by = user
        policy.save()

        if 'rules' in payload and payload['rules'] is not None:
            cls._replace_rules(
                policy=policy,
                organization=organization,
                rules=payload['rules'],
                user=user,
            )

        return cls.get_leave_policy(user=user, branch_id=branch_id, item_id=policy.id)

    @classmethod
    @transaction.atomic
    def delete_leave_policy(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        policy = LeavePolicy.objects.filter(
            id=item_id,
            organization=cls._organization(membership),
        ).first()
        if policy is None:
            raise NotFoundServiceError('Leave policy not found.', code='leave_policy_not_found')
        policy.delete()

    @classmethod
    def _replace_rules(
        cls,
        *,
        policy: LeavePolicy,
        organization,
        rules: list[dict],
        user: User,
    ) -> None:
        seen_leave_types: set[UUID] = set()
        normalized: list[dict] = []
        for raw in rules:
            leave_type_id = raw.get('leave_type_id')
            if leave_type_id is None:
                raise ValidationServiceError('Each rule needs a leave type.', code='invalid_policy_rule')
            leave_type_uuid = UUID(str(leave_type_id))
            if leave_type_uuid in seen_leave_types:
                raise ValidationServiceError(
                    'Duplicate leave types are not allowed in a policy.',
                    code='duplicate_leave_type',
                )
            seen_leave_types.add(leave_type_uuid)
            leave_type = LeaveType.objects.filter(
                id=leave_type_uuid,
                organization=organization,
                is_active=True,
            ).first()
            if leave_type is None:
                raise NotFoundServiceError('Leave type not found.', code='leave_type_not_found')

            frequency = str(
                raw.get('allocation_frequency') or LeavePolicyRule.AllocationFrequency.YEARLY
            ).strip().lower()
            if frequency not in cls.ALLOCATION_FREQUENCIES:
                raise ValidationServiceError(
                    'Invalid allocation frequency.',
                    code='invalid_allocation_frequency',
                )

            allocation_quantity = cls._decimal(
                raw.get('allocation_quantity'),
                field='allocation_quantity',
            )
            annual_limit = cls._decimal(raw.get('annual_limit'), field='annual_limit')
            if allocation_quantity < 0 or annual_limit < 0:
                raise ValidationServiceError(
                    'Allocation values cannot be negative.',
                    code='invalid_allocation_values',
                )
            if annual_limit and allocation_quantity > annual_limit:
                raise ValidationServiceError(
                    'Allocation quantity cannot exceed annual limit.',
                    code='allocation_exceeds_annual_limit',
                )

            max_consecutive = raw.get('maximum_consecutive_days')
            if max_consecutive in ('', None):
                max_consecutive = None
            else:
                max_consecutive = int(max_consecutive)
                if max_consecutive < 1:
                    raise ValidationServiceError(
                        'Maximum consecutive days must be at least 1.',
                        code='invalid_max_consecutive',
                    )

            minimum_service_days = int(raw.get('minimum_service_days') or 0)
            if minimum_service_days < 0:
                raise ValidationServiceError(
                    'Minimum service days cannot be negative.',
                    code='invalid_minimum_service_days',
                )

            normalized.append(
                {
                    'leave_type': leave_type,
                    'allocation_frequency': frequency,
                    'allocation_quantity': allocation_quantity,
                    'annual_limit': annual_limit,
                    'carry_forward_allowed': bool(raw.get('carry_forward_allowed', False)),
                    'carry_forward_limit': cls._decimal(
                        raw.get('carry_forward_limit'),
                        field='carry_forward_limit',
                    ),
                    'encashment_allowed': bool(raw.get('encashment_allowed', False)),
                    'encashment_limit': cls._decimal(
                        raw.get('encashment_limit'),
                        field='encashment_limit',
                    ),
                    'allow_half_day': bool(raw.get('allow_half_day', False)),
                    'allow_negative_balance': bool(raw.get('allow_negative_balance', False)),
                    'minimum_service_days': minimum_service_days,
                    'maximum_consecutive_days': max_consecutive,
                    'is_active': bool(raw.get('is_active', True)),
                }
            )

        policy.rules.all().delete()
        LeavePolicyRule.objects.bulk_create(
            [
                LeavePolicyRule(
                    policy=policy,
                    leave_type=row['leave_type'],
                    allocation_frequency=row['allocation_frequency'],
                    allocation_quantity=row['allocation_quantity'],
                    annual_limit=row['annual_limit'],
                    carry_forward_allowed=row['carry_forward_allowed'],
                    carry_forward_limit=row['carry_forward_limit'],
                    encashment_allowed=row['encashment_allowed'],
                    encashment_limit=row['encashment_limit'],
                    allow_half_day=row['allow_half_day'],
                    allow_negative_balance=row['allow_negative_balance'],
                    minimum_service_days=row['minimum_service_days'],
                    maximum_consecutive_days=row['maximum_consecutive_days'],
                    is_active=row['is_active'],
                    created_by=user,
                    updated_by=user,
                )
                for row in normalized
            ]
        )

    @classmethod
    def serialize_leave_policy_rule(cls, item: LeavePolicyRule) -> dict:
        return {
            'id': str(item.id),
            'leave_type_id': str(item.leave_type_id),
            'leave_type_name': item.leave_type.name if item.leave_type_id else None,
            'allocation_frequency': item.allocation_frequency,
            'allocation_quantity': str(item.allocation_quantity),
            'annual_limit': str(item.annual_limit),
            'carry_forward_allowed': item.carry_forward_allowed,
            'carry_forward_limit': str(item.carry_forward_limit),
            'encashment_allowed': item.encashment_allowed,
            'encashment_limit': str(item.encashment_limit),
            'allow_half_day': item.allow_half_day,
            'allow_negative_balance': item.allow_negative_balance,
            'minimum_service_days': item.minimum_service_days,
            'maximum_consecutive_days': item.maximum_consecutive_days,
            'is_active': item.is_active,
        }

    @classmethod
    def serialize_leave_policy(cls, item: LeavePolicy) -> dict:
        rules = sorted(
            item.rules.all(),
            key=lambda row: ((row.leave_type.name if row.leave_type_id else ''), str(row.id)),
        )
        return {
            'id': str(item.id),
            'organization_id': str(item.organization_id),
            'employee_type_id': str(item.employee_type_id),
            'employee_type_name': item.employee_type.name if item.employee_type_id else None,
            'code': item.code,
            'name': item.name,
            'description': item.description,
            'effective_from': item.effective_from.isoformat() if item.effective_from else None,
            'effective_to': item.effective_to.isoformat() if item.effective_to else None,
            'is_default': item.is_default,
            'is_active': item.is_active,
            'rule_count': len(rules),
            'rules': [cls.serialize_leave_policy_rule(rule) for rule in rules],
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }
