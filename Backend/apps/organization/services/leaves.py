"""Employee leave balances, applications, and audit logs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

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
    LeaveType,
)
from apps.people.models import (
    Employee,
)
from apps.leave.models import (
    EmployeeLeaveBalance,
    EmployeeLeaveLog,
    LeaveApplication,
    LeavePolicy,
    LeavePolicyRule,
)
from apps.organization.services.workspace import WorkspaceService


class LeaveService:
    """Manage leave balances and applications for employees."""

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        if not is_owner and access_name not in {'admin', 'administrator'}:
            raise PermissionDeniedServiceError(
                'Only organization admins can manage leave records.',
                code='not_organization_admin',
            )
        return membership

    @classmethod
    def _membership(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        return WorkspaceService.get_membership(user, branch_id=branch_id)

    @classmethod
    def _organization(cls, membership: OrganizationMembership):
        return membership.branch.organization

    @classmethod
    def _is_org_admin(cls, user: User, membership: OrganizationMembership) -> bool:
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        return bool(is_owner or access_name in {'admin', 'administrator'})

    @classmethod
    def resolve_approver_chain(cls, employee: Employee) -> list[Employee]:
        """
        Reporting manager first, then each higher manager up the chain.

        If no reporting manager is set, fall back to active employees holding the
        next higher designation(s) in the same organization.
        """
        chain: list[Employee] = []
        seen: set = set()

        current = employee.reporting_manager
        # Prefer select_related chain when already loaded; otherwise walk FKs.
        while current is not None and current.id not in seen:
            seen.add(current.id)
            if current.is_active and current.user_id and current.id != employee.id:
                chain.append(current)
            current = current.reporting_manager

        if chain:
            return chain

        designation = employee.designation
        while designation is not None and designation.parent_id:
            designation = designation.parent
            if designation is None or designation.id in seen:
                break
            seen.add(designation.id)
            seniors = list(
                Employee.objects.filter(
                    organization_id=employee.organization_id,
                    designation_id=designation.id,
                    is_active=True,
                    user__isnull=False,
                )
                .exclude(id=employee.id)
                .order_by('display_name')[:8]
            )
            if seniors:
                chain.extend(seniors)
                break
        return chain

    @classmethod
    def expected_approver(cls, employee: Employee) -> Employee | None:
        chain = cls.resolve_approver_chain(employee)
        return chain[0] if chain else None

    @classmethod
    def can_review_leave(
        cls,
        *,
        user: User,
        employee: Employee,
        membership: OrganizationMembership,
    ) -> bool:
        """Direct/higher manager can approve; admin only if no manager chain exists."""
        if employee.user_id and employee.user_id == user.id:
            return False

        chain = cls.resolve_approver_chain(employee)
        if any(manager.user_id == user.id for manager in chain):
            return True

        if not chain and cls._is_org_admin(user, membership):
            return True

        # Org owner can always unstick approvals when the assigned manager is unavailable.
        if membership.branch.organization.owner_id == user.id:
            return True

        return False

    @classmethod
    def require_leave_reviewer(
        cls,
        user: User,
        branch_id: str | UUID | None,
        employee: Employee,
    ) -> OrganizationMembership:
        membership = cls._membership(user, branch_id)
        if not cls.can_review_leave(user=user, employee=employee, membership=membership):
            raise PermissionDeniedServiceError(
                'Only the reporting manager or a higher manager can review this leave request.',
                code='not_leave_approver',
            )
        return membership

    @classmethod
    def _get_employee(cls, *, organization, employee_id: str | UUID) -> Employee:
        employee = (
            Employee.objects.filter(id=employee_id, organization=organization)
            .select_related(
                'reporting_manager',
                'reporting_manager__reporting_manager',
                'designation',
                'designation__parent',
                'designation__parent__parent',
            )
            .first()
        )
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')
        return employee

    @classmethod
    def _decimal(cls, value, *, field: str, default: Decimal = Decimal('0')) -> Decimal:
        if value in (None, ''):
            return default
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationServiceError(f'Invalid value for {field}.', code='invalid_decimal') from exc

    @classmethod
    def _calc_days(cls, *, from_date: date, to_date: date, is_half_day: bool) -> Decimal:
        if to_date < from_date:
            raise ValidationServiceError(
                'To date must be on or after from date.',
                code='invalid_leave_range',
            )
        if is_half_day:
            if from_date != to_date:
                raise ValidationServiceError(
                    'Half-day leave must be for a single date.',
                    code='invalid_half_day_range',
                )
            return Decimal('0.5')
        return Decimal((to_date - from_date).days + 1)

    @classmethod
    def _get_or_create_balance(
        cls,
        *,
        organization,
        employee: Employee,
        leave_type: LeaveType,
        user: User,
    ) -> EmployeeLeaveBalance:
        balance, _ = EmployeeLeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            defaults={
                'organization': organization,
                'allocated': Decimal('0'),
                'used': Decimal('0'),
                'balance': Decimal('0'),
                'created_by': user,
                'updated_by': user,
            },
        )
        return balance

    @classmethod
    def _write_log(
        cls,
        *,
        organization,
        employee: Employee,
        leave_type: LeaveType,
        transaction_type: str,
        quantity: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        user: User,
        leave_application: LeaveApplication | None = None,
        remarks: str = '',
    ) -> EmployeeLeaveLog:
        return EmployeeLeaveLog.objects.create(
            organization=organization,
            employee=employee,
            leave_type=leave_type,
            transaction_type=transaction_type,
            quantity=quantity,
            balance_before=balance_before,
            balance_after=balance_after,
            leave_application=leave_application,
            remarks=(remarks or '').strip(),
            created_by=user,
            updated_by=user,
        )

    # ── Balances ────────────────────────────────────────────────────────────

    @classmethod
    def list_balances(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
    ) -> list[dict]:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        rows = (
            EmployeeLeaveBalance.objects.filter(organization=organization, employee=employee)
            .select_related('leave_type')
            .order_by('leave_type__name')
        )
        return [cls.serialize_balance(row) for row in rows]

    @classmethod
    @transaction.atomic
    def allocate_balance(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        leave_type_id: str | UUID,
        quantity: Decimal | str | int | float,
        remarks: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        leave_type = LeaveType.objects.filter(
            id=leave_type_id,
            organization=organization,
            is_active=True,
        ).first()
        if leave_type is None:
            raise NotFoundServiceError('Leave type not found.', code='leave_type_not_found')

        qty = cls._decimal(quantity, field='quantity')
        if qty <= 0:
            raise ValidationServiceError('Quantity must be greater than zero.', code='invalid_quantity')

        balance = cls._get_or_create_balance(
            organization=organization,
            employee=employee,
            leave_type=leave_type,
            user=user,
        )
        before = balance.balance
        balance.allocated = (balance.allocated or Decimal('0')) + qty
        balance.balance = (balance.balance or Decimal('0')) + qty
        balance.updated_by = user
        balance.save(update_fields=['allocated', 'balance', 'updated_by', 'updated_at'])
        cls._write_log(
            organization=organization,
            employee=employee,
            leave_type=leave_type,
            transaction_type=EmployeeLeaveLog.TransactionType.ALLOCATION,
            quantity=qty,
            balance_before=before,
            balance_after=balance.balance,
            user=user,
            remarks=remarks or 'Manual allocation',
        )
        return cls.serialize_balance(balance)

    @classmethod
    @transaction.atomic
    def adjust_balance(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        leave_type_id: str | UUID,
        quantity: Decimal | str | int | float,
        remarks: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        leave_type = LeaveType.objects.filter(
            id=leave_type_id,
            organization=organization,
            is_active=True,
        ).first()
        if leave_type is None:
            raise NotFoundServiceError('Leave type not found.', code='leave_type_not_found')

        qty = cls._decimal(quantity, field='quantity')
        if qty == 0:
            raise ValidationServiceError('Adjustment quantity cannot be zero.', code='invalid_quantity')

        balance = cls._get_or_create_balance(
            organization=organization,
            employee=employee,
            leave_type=leave_type,
            user=user,
        )
        before = balance.balance
        after = before + qty
        if after < 0:
            raise ValidationServiceError(
                'Adjustment would make balance negative.',
                code='insufficient_balance',
            )
        balance.balance = after
        if qty > 0:
            balance.allocated = (balance.allocated or Decimal('0')) + qty
        balance.updated_by = user
        balance.save(update_fields=['allocated', 'balance', 'updated_by', 'updated_at'])
        cls._write_log(
            organization=organization,
            employee=employee,
            leave_type=leave_type,
            transaction_type=EmployeeLeaveLog.TransactionType.ADJUSTMENT,
            quantity=qty,
            balance_before=before,
            balance_after=after,
            user=user,
            remarks=remarks or 'Manual adjustment',
        )
        return cls.serialize_balance(balance)

    @classmethod
    def _seed_quantity_for_rule(cls, rule, *, policy_code: str) -> tuple[Decimal, str]:
        """
        Opening credit depends on allocation mode.

        - yearly / upfront → full annual entitlement
        - monthly / quarterly → one period only (annual_limit is a cap, not opening balance)
        """
        from apps.organization.services.leave_scheduler import LeaveSchedulerService

        frequency = rule.allocation_frequency or LeavePolicyRule.AllocationFrequency.YEARLY
        allocation_qty = Decimal(rule.allocation_quantity or 0)
        annual_limit = Decimal(rule.annual_limit or 0)

        if frequency == LeavePolicyRule.AllocationFrequency.YEARLY:
            qty = annual_limit or allocation_qty
            return qty, f'Seeded from policy {policy_code} (upfront)'

        # Accrual: credit the current period only; mark with scheduler period so cron
        # does not double-credit the same month/quarter.
        qty = allocation_qty
        if qty <= 0:
            return Decimal('0'), ''
        period = LeaveSchedulerService.period_key(frequency)
        marker = LeaveSchedulerService.allocation_marker(frequency, period)
        return qty, marker

    @classmethod
    @transaction.atomic
    def seed_from_policy(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
    ) -> list[dict]:
        """Seed opening balances from the employee type's leave policy.

        Upfront (yearly) rules get the full annual amount.
        Accrual (monthly/quarterly) rules get only the current period quantity.
        """
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        if not employee.employee_type_id:
            raise ValidationServiceError(
                'Employee has no employee type assigned.',
                code='missing_employee_type',
            )

        policy = (
            LeavePolicy.objects.filter(
                organization=organization,
                employee_type_id=employee.employee_type_id,
                is_active=True,
            )
            .filter(Q(is_default=True) | Q(effective_to__isnull=True) | Q(effective_to__gte=timezone.localdate()))
            .prefetch_related('rules__leave_type')
            .order_by('-is_default', '-effective_from')
            .first()
        )
        if policy is None:
            raise NotFoundServiceError(
                'No active leave policy found for this employee type.',
                code='leave_policy_not_found',
            )

        results = []
        for rule in policy.rules.filter(is_active=True).select_related('leave_type'):
            qty, remarks = cls._seed_quantity_for_rule(rule, policy_code=policy.code)
            if qty <= 0:
                continue
            balance = cls._get_or_create_balance(
                organization=organization,
                employee=employee,
                leave_type=rule.leave_type,
                user=user,
            )
            if balance.allocated and balance.allocated > 0:
                results.append(cls.serialize_balance(balance))
                continue
            before = balance.balance
            balance.allocated = qty
            balance.balance = qty
            balance.used = Decimal('0')
            balance.updated_by = user
            balance.save(update_fields=['allocated', 'used', 'balance', 'updated_by', 'updated_at'])
            cls._write_log(
                organization=organization,
                employee=employee,
                leave_type=rule.leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.ALLOCATION,
                quantity=qty,
                balance_before=before,
                balance_after=balance.balance,
                user=user,
                remarks=remarks,
            )
            results.append(cls.serialize_balance(balance))
        return results

    # ── Applications ────────────────────────────────────────────────────────

    @classmethod
    def list_applications(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        status: str | None = None,
    ) -> list[dict]:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        qs = (
            LeaveApplication.objects.filter(organization=organization, employee=employee)
            .select_related('leave_type', 'approved_by')
            .order_by('-created_at')
        )
        if status:
            qs = qs.filter(status=status)
        can_review = cls.can_review_leave(user=user, employee=employee, membership=membership)
        expected = cls.expected_approver(employee)
        return [
            cls.serialize_application(
                row,
                can_review=can_review,
                expected_approver=expected,
            )
            for row in qs
        ]

    @classmethod
    @transaction.atomic
    def create_application(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        payload: dict,
        attachment=None,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)

        leave_type = LeaveType.objects.filter(
            id=payload['leave_type_id'],
            organization=organization,
            is_active=True,
        ).first()
        if leave_type is None:
            raise NotFoundServiceError('Leave type not found.', code='leave_type_not_found')

        from_date = payload['from_date']
        to_date = payload['to_date']
        is_half_day = bool(payload.get('is_half_day', False))
        days = cls._calc_days(from_date=from_date, to_date=to_date, is_half_day=is_half_day)
        reason = str(payload.get('reason') or '').strip()
        if len(reason) < 3:
            raise ValidationServiceError('Reason must be at least 3 characters.', code='invalid_reason')

        overlap = LeaveApplication.objects.filter(
            organization=organization,
            employee=employee,
            status__in=[
                LeaveApplication.Status.PENDING,
                LeaveApplication.Status.APPROVED,
            ],
            from_date__lte=to_date,
            to_date__gte=from_date,
        ).exists()
        if overlap:
            raise ConflictServiceError(
                'This employee already has a leave request overlapping these dates.',
                code='leave_overlap',
            )

        balance = cls._get_or_create_balance(
            organization=organization,
            employee=employee,
            leave_type=leave_type,
            user=user,
        )
        if balance.balance < days:
            raise ValidationServiceError(
                'Insufficient leave balance for this request.',
                code='insufficient_balance',
            )

        application = LeaveApplication.objects.create(
            organization=organization,
            employee=employee,
            leave_type=leave_type,
            from_date=from_date,
            to_date=to_date,
            number_of_days=days,
            is_half_day=is_half_day,
            reason=reason,
            attachment=attachment,
            status=LeaveApplication.Status.PENDING,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_application(
            application,
            can_review=cls.can_review_leave(user=user, employee=employee, membership=membership),
            expected_approver=cls.expected_approver(employee),
        )

    @classmethod
    @transaction.atomic
    def review_application(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        application_id: str | UUID,
        approve: bool,
        remarks: str = '',
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        membership = cls.require_leave_reviewer(user, branch_id, employee)
        application = (
            LeaveApplication.objects.select_related('leave_type')
            .filter(id=application_id, organization=organization, employee=employee)
            .first()
        )
        if application is None:
            raise NotFoundServiceError('Leave application not found.', code='leave_application_not_found')
        if application.status != LeaveApplication.Status.PENDING:
            raise ConflictServiceError(
                'Only pending leave applications can be reviewed.',
                code='leave_not_pending',
            )

        if approve:
            balance = cls._get_or_create_balance(
                organization=organization,
                employee=employee,
                leave_type=application.leave_type,
                user=user,
            )
            if balance.balance < application.number_of_days:
                raise ValidationServiceError(
                    'Insufficient leave balance to approve this request.',
                    code='insufficient_balance',
                )
            before = balance.balance
            balance.used = (balance.used or Decimal('0')) + application.number_of_days
            balance.balance = before - application.number_of_days
            balance.updated_by = user
            balance.save(update_fields=['used', 'balance', 'updated_by', 'updated_at'])
            application.status = LeaveApplication.Status.APPROVED
            cls._write_log(
                organization=organization,
                employee=employee,
                leave_type=application.leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.LEAVE_APPROVED,
                quantity=-application.number_of_days,
                balance_before=before,
                balance_after=balance.balance,
                user=user,
                leave_application=application,
                remarks=remarks or 'Leave approved',
            )
        else:
            application.status = LeaveApplication.Status.REJECTED

        application.approved_by = user
        application.approved_at = timezone.now()
        application.remarks = (remarks or '').strip()
        application.updated_by = user
        application.save(
            update_fields=[
                'status',
                'approved_by',
                'approved_at',
                'remarks',
                'updated_by',
                'updated_at',
            ]
        )
        expected = cls.expected_approver(employee)
        return cls.serialize_application(
            application,
            can_review=False,
            expected_approver=expected,
        )

    @classmethod
    @transaction.atomic
    def cancel_application(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        application_id: str | UUID,
        remarks: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        application = (
            LeaveApplication.objects.select_related('leave_type')
            .filter(id=application_id, organization=organization, employee=employee)
            .first()
        )
        if application is None:
            raise NotFoundServiceError('Leave application not found.', code='leave_application_not_found')
        if application.status not in {
            LeaveApplication.Status.PENDING,
            LeaveApplication.Status.APPROVED,
        }:
            raise ConflictServiceError(
                'Only pending or approved leave can be cancelled.',
                code='leave_not_cancellable',
            )

        if application.status == LeaveApplication.Status.APPROVED:
            balance = cls._get_or_create_balance(
                organization=organization,
                employee=employee,
                leave_type=application.leave_type,
                user=user,
            )
            before = balance.balance
            balance.used = max(Decimal('0'), (balance.used or Decimal('0')) - application.number_of_days)
            balance.balance = before + application.number_of_days
            balance.updated_by = user
            balance.save(update_fields=['used', 'balance', 'updated_by', 'updated_at'])
            cls._write_log(
                organization=organization,
                employee=employee,
                leave_type=application.leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.LEAVE_CANCELLED,
                quantity=application.number_of_days,
                balance_before=before,
                balance_after=balance.balance,
                user=user,
                leave_application=application,
                remarks=remarks or 'Leave cancelled',
            )

        application.status = LeaveApplication.Status.CANCELLED
        if remarks:
            application.remarks = remarks.strip()
        application.updated_by = user
        application.save(update_fields=['status', 'remarks', 'updated_by', 'updated_at'])
        return cls.serialize_application(application)

    @classmethod
    def list_logs(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
    ) -> list[dict]:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        rows = (
            EmployeeLeaveLog.objects.filter(organization=organization, employee=employee)
            .select_related('leave_type', 'leave_application')
            .order_by('-created_at')[:100]
        )
        return [cls.serialize_log(row) for row in rows]

    @classmethod
    def list_approvals_inbox(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        status: str | None = None,
    ) -> dict:
        """Leave requests in this user's manager approval scope."""
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        status_filter = (status or LeaveApplication.Status.PENDING).strip().lower()
        if status_filter not in {
            LeaveApplication.Status.PENDING,
            LeaveApplication.Status.APPROVED,
            LeaveApplication.Status.REJECTED,
            'all',
        }:
            status_filter = LeaveApplication.Status.PENDING

        qs = (
            LeaveApplication.objects.filter(organization=organization)
            .select_related(
                'leave_type',
                'approved_by',
                'employee',
                'employee__reporting_manager',
                'employee__reporting_manager__reporting_manager',
                'employee__designation',
                'employee__designation__parent',
                'employee__designation__parent__parent',
            )
            .order_by('-created_at')
        )
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)
        else:
            qs = qs.exclude(status=LeaveApplication.Status.DRAFT)

        items: list[dict] = []
        pending_for_me = 0

        # Always compute pending count for the badge, independent of the active filter.
        pending_qs = (
            LeaveApplication.objects.filter(
                organization=organization,
                status=LeaveApplication.Status.PENDING,
            )
            .select_related(
                'employee',
                'employee__reporting_manager',
                'employee__reporting_manager__reporting_manager',
                'employee__designation',
                'employee__designation__parent',
                'employee__designation__parent__parent',
            )
        )
        for application in pending_qs[:300]:
            if cls.can_review_leave(
                user=user,
                employee=application.employee,
                membership=membership,
            ):
                pending_for_me += 1

        for application in qs[:300]:
            employee = application.employee
            in_scope = cls.can_review_leave(
                user=user,
                employee=employee,
                membership=membership,
            ) or application.approved_by_id == user.id
            if not in_scope:
                continue

            can_review = (
                application.status == LeaveApplication.Status.PENDING
                and cls.can_review_leave(user=user, employee=employee, membership=membership)
            )

            items.append(
                cls.serialize_application(
                    application,
                    can_review=can_review,
                    expected_approver=cls.expected_approver(employee),
                )
            )

        return {
            'pending_count': pending_for_me,
            'items': items,
        }

    @classmethod
    @transaction.atomic
    def review_application_by_id(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        application_id: str | UUID,
        approve: bool,
        remarks: str = '',
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        application = (
            LeaveApplication.objects.select_related('employee', 'leave_type')
            .filter(id=application_id, organization=organization)
            .first()
        )
        if application is None:
            raise NotFoundServiceError('Leave application not found.', code='leave_application_not_found')
        return cls.review_application(
            user=user,
            branch_id=branch_id,
            employee_id=application.employee_id,
            application_id=application.id,
            approve=approve,
            remarks=remarks,
        )

    # ── Serialize ───────────────────────────────────────────────────────────

    @classmethod
    def serialize_balance(cls, item: EmployeeLeaveBalance) -> dict:
        return {
            'id': str(item.id),
            'organization_id': str(item.organization_id),
            'employee_id': str(item.employee_id),
            'leave_type_id': str(item.leave_type_id),
            'leave_type_name': item.leave_type.name if item.leave_type_id else None,
            'allocated': str(item.allocated),
            'used': str(item.used),
            'balance': str(item.balance),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_application(
        cls,
        item: LeaveApplication,
        *,
        can_review: bool | None = None,
        expected_approver: Employee | None = None,
    ) -> dict:
        attachment_url = None
        if item.attachment:
            try:
                attachment_url = item.attachment.url
            except ValueError:
                attachment_url = None
        expected_name = None
        expected_id = None
        if expected_approver is not None:
            expected_id = str(expected_approver.id)
            expected_name = (
                expected_approver.display_name
                or ' '.join(
                    part
                    for part in [expected_approver.first_name, expected_approver.last_name]
                    if part
                ).strip()
                or expected_approver.email
            )
        return {
            'id': str(item.id),
            'organization_id': str(item.organization_id),
            'employee_id': str(item.employee_id),
            'employee_name': cls._employee_display_name(getattr(item, 'employee', None)),
            'employee_code': (
                item.employee.employee_code
                if getattr(item, 'employee', None) is not None
                else None
            ),
            'employee_designation_name': (
                item.employee.designation.name
                if getattr(item, 'employee', None) is not None
                and getattr(item.employee, 'designation', None) is not None
                else None
            ),
            'leave_type_id': str(item.leave_type_id),
            'leave_type_name': item.leave_type.name if item.leave_type_id else None,
            'from_date': item.from_date.isoformat() if item.from_date else None,
            'to_date': item.to_date.isoformat() if item.to_date else None,
            'number_of_days': str(item.number_of_days),
            'is_half_day': item.is_half_day,
            'reason': item.reason,
            'attachment_url': attachment_url,
            'status': item.status,
            'approved_by_id': str(item.approved_by_id) if item.approved_by_id else None,
            'approved_by_name': (
                item.approved_by.full_name or item.approved_by.email if item.approved_by else None
            ),
            'approved_at': item.approved_at.isoformat() if item.approved_at else None,
            'remarks': item.remarks,
            'expected_approver_id': expected_id,
            'expected_approver_name': expected_name,
            'can_review': bool(can_review) if item.status == LeaveApplication.Status.PENDING else False,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def _employee_display_name(cls, employee: Employee | None) -> str | None:
        if employee is None:
            return None
        return (
            employee.display_name
            or ' '.join(part for part in [employee.first_name, employee.last_name] if part).strip()
            or employee.email
            or None
        )

    @classmethod
    def serialize_log(cls, item: EmployeeLeaveLog) -> dict:
        return {
            'id': str(item.id),
            'organization_id': str(item.organization_id),
            'employee_id': str(item.employee_id),
            'leave_type_id': str(item.leave_type_id),
            'leave_type_name': item.leave_type.name if item.leave_type_id else None,
            'transaction_type': item.transaction_type,
            'quantity': str(item.quantity),
            'balance_before': str(item.balance_before),
            'balance_after': str(item.balance_after),
            'leave_application_id': (
                str(item.leave_application_id) if item.leave_application_id else None
            ),
            'remarks': item.remarks,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }
