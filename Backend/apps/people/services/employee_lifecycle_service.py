"""Database-driven employee lifecycle engine (no hardcoded transition rules)."""

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
    EmployeeLifecycleTransition,
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


class EmployeeLifecycleEngine:
    """Generic lifecycle engine driven entirely by status/transition tables."""

    @classmethod
    def get_initial_status(cls) -> EmployeeLifecycleStatus:
        status = (
            EmployeeLifecycleStatus.objects.filter(is_active=True, is_initial=True)
            .order_by('ordinal', 'name')
            .first()
        )
        if status is None:
            raise ValidationServiceError(
                'No initial lifecycle status is configured.',
                code='lifecycle_initial_missing',
            )
        return status

    @classmethod
    def list_statuses(cls, *, active_only: bool = True) -> list[EmployeeLifecycleStatus]:
        qs = EmployeeLifecycleStatus.objects.all().order_by('ordinal', 'name')
        if active_only:
            qs = qs.filter(is_active=True)
        return list(qs)

    @classmethod
    def get_available_transitions(
        cls,
        *,
        from_status: EmployeeLifecycleStatus | None,
    ) -> list[EmployeeLifecycleTransition]:
        if from_status is None:
            return []
        return list(
            EmployeeLifecycleTransition.objects.select_related('from_status', 'to_status')
            .filter(
                from_status=from_status,
                is_active=True,
                to_status__is_active=True,
            )
            .order_by('sort_order', 'action_label')
        )

    @classmethod
    def find_transition(
        cls,
        *,
        from_status: EmployeeLifecycleStatus | None,
        to_status: EmployeeLifecycleStatus,
    ) -> EmployeeLifecycleTransition | None:
        if from_status is None:
            return None
        return (
            EmployeeLifecycleTransition.objects.select_related('from_status', 'to_status')
            .filter(
                from_status=from_status,
                to_status=to_status,
                is_active=True,
                to_status__is_active=True,
            )
            .first()
        )

    @classmethod
    def can_transition(
        cls,
        *,
        from_status: EmployeeLifecycleStatus | None,
        to_status: EmployeeLifecycleStatus,
    ) -> bool:
        return cls.find_transition(from_status=from_status, to_status=to_status) is not None

    @classmethod
    @transaction.atomic
    def apply_transition(
        cls,
        *,
        employee: Employee,
        to_status: EmployeeLifecycleStatus,
        changed_by: User | None,
        remarks: str = '',
        exit_date: date | None = None,
    ) -> Employee:
        from_status = employee.lifecycle_status
        transition = cls.find_transition(from_status=from_status, to_status=to_status)
        if transition is None:
            from_name = from_status.name if from_status else 'None'
            raise ValidationServiceError(
                f'Transition from “{from_name}” to “{to_status.name}” is not allowed.',
                code='lifecycle_transition_not_allowed',
                details={
                    'from_status_id': str(from_status.id) if from_status else None,
                    'to_status_id': str(to_status.id),
                },
            )

        update_fields = ['lifecycle_status', 'updated_by', 'updated_at']
        employee.lifecycle_status = to_status
        employee.updated_by = changed_by

        if to_status.key == 'notice_period':
            resolved_exit = exit_date
            if resolved_exit is None:
                days = getattr(employee.organization, 'notice_period_days', None) or 0
                if days < 1:
                    raise ValidationServiceError(
                        'Exit date is required when organization notice period days is not configured.',
                        code='exit_date_required',
                    )
                resolved_exit = timezone.localdate() + timedelta(days=days)
            employee.exit_date = resolved_exit
            update_fields.append('exit_date')
        elif to_status.key == 'released':
            resolved_exit = exit_date or employee.exit_date or timezone.localdate()
            employee.exit_date = resolved_exit
            update_fields.append('exit_date')

        employee.save(update_fields=update_fields)

        EmployeeLifecycleHistory.objects.create(
            employee=employee,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            remarks=(remarks or '').strip(),
        )
        return employee

    @classmethod
    def serialize_status(cls, status: EmployeeLifecycleStatus) -> dict:
        return {
            'id': str(status.id),
            'name': status.name,
            'key': status.key,
            'ordinal': status.ordinal,
            'is_initial': status.is_initial,
            'is_terminal': status.is_terminal,
            'is_active': status.is_active,
        }

    @classmethod
    def serialize_transition(cls, transition: EmployeeLifecycleTransition) -> dict:
        return {
            'id': str(transition.id),
            'action_label': transition.action_label,
            'sort_order': transition.sort_order,
            'from_status': cls.serialize_status(transition.from_status),
            'to_status': cls.serialize_status(transition.to_status),
        }

    @classmethod
    def serialize_history(cls, row: EmployeeLifecycleHistory) -> dict:
        return {
            'id': str(row.id),
            'from_status': cls.serialize_status(row.from_status) if row.from_status else None,
            'to_status': cls.serialize_status(row.to_status),
            'changed_by_id': str(row.changed_by_id) if row.changed_by_id else None,
            'changed_by_name': (
                row.changed_by.full_name or row.changed_by.email
                if row.changed_by
                else None
            ),
            'changed_at': row.changed_at.isoformat(),
            'remarks': row.remarks,
        }


