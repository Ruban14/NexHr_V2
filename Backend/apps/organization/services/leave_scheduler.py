"""Scheduled leave allocation and year-end carry-forward jobs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.organizations.models import (
    Organization,
)
from apps.people.models import (
    Employee,
)
from apps.leave.models import (
    EmployeeLeaveBalance,
    EmployeeLeaveLog,
    LeavePolicy,
    LeavePolicyRule,
)


class LeaveSchedulerService:
    """System jobs for periodic leave credit and carry-forward."""

    FREQ_MONTHLY = LeavePolicyRule.AllocationFrequency.MONTHLY
    FREQ_QUARTERLY = LeavePolicyRule.AllocationFrequency.QUARTERLY
    FREQ_YEARLY = LeavePolicyRule.AllocationFrequency.YEARLY

    @classmethod
    def period_key(cls, frequency: str, on_date: date | None = None) -> str:
        day = on_date or timezone.localdate()
        if frequency == cls.FREQ_MONTHLY:
            return f'{day.year}-{day.month:02d}'
        if frequency == cls.FREQ_QUARTERLY:
            quarter = (day.month - 1) // 3 + 1
            return f'{day.year}-Q{quarter}'
        return str(day.year)

    @classmethod
    def allocation_marker(cls, frequency: str, period: str) -> str:
        return f'scheduler:{frequency}:{period}'

    @classmethod
    def carry_forward_marker(cls, from_year: int) -> str:
        return f'scheduler:carry_forward:{from_year}'

    @classmethod
    def run_allocation(
        cls,
        *,
        frequency: str,
        on_date: date | None = None,
        organization_id=None,
        dry_run: bool = False,
    ) -> dict:
        """Credit leave for active employees matching policy rules of ``frequency``."""
        if frequency not in {cls.FREQ_MONTHLY, cls.FREQ_QUARTERLY, cls.FREQ_YEARLY}:
            raise ValueError(f'Unsupported allocation frequency: {frequency}')

        day = on_date or timezone.localdate()
        period = cls.period_key(frequency, day)
        marker = cls.allocation_marker(frequency, period)

        orgs = Organization.objects.filter(is_active=True)
        if organization_id:
            orgs = orgs.filter(id=organization_id)

        summary = {
            'frequency': frequency,
            'period': period,
            'dry_run': dry_run,
            'organizations': 0,
            'employees_considered': 0,
            'allocated': 0,
            'skipped_already': 0,
            'skipped_zero': 0,
            'skipped_annual_cap': 0,
            'errors': [],
        }

        for organization in orgs.iterator():
            summary['organizations'] += 1
            try:
                stats = cls._allocate_for_organization(
                    organization=organization,
                    frequency=frequency,
                    day=day,
                    period=period,
                    marker=marker,
                    dry_run=dry_run,
                )
            except Exception as exc:  # noqa: BLE001 - job must continue across orgs
                summary['errors'].append({'organization_id': str(organization.id), 'error': str(exc)})
                continue
            for key in (
                'employees_considered',
                'allocated',
                'skipped_already',
                'skipped_zero',
                'skipped_annual_cap',
            ):
                summary[key] += stats[key]

        return summary

    @classmethod
    def run_carry_forward(
        cls,
        *,
        on_date: date | None = None,
        organization_id=None,
        dry_run: bool = False,
    ) -> dict:
        """
        Apply year-end carry-forward for rules that allow it.

        Typically run on the first day of a new leave year (calendar year default).
        Carries remaining balance up to ``carry_forward_limit``, resets used to 0,
        and sets allocated/balance to the carried amount.
        """
        day = on_date or timezone.localdate()
        from_year = day.year - 1
        marker = cls.carry_forward_marker(from_year)

        orgs = Organization.objects.filter(is_active=True)
        if organization_id:
            orgs = orgs.filter(id=organization_id)

        summary = {
            'from_year': from_year,
            'dry_run': dry_run,
            'organizations': 0,
            'employees_considered': 0,
            'carried': 0,
            'skipped_already': 0,
            'skipped_zero': 0,
            'errors': [],
        }

        for organization in orgs.iterator():
            summary['organizations'] += 1
            try:
                stats = cls._carry_forward_for_organization(
                    organization=organization,
                    day=day,
                    from_year=from_year,
                    marker=marker,
                    dry_run=dry_run,
                )
            except Exception as exc:  # noqa: BLE001
                summary['errors'].append({'organization_id': str(organization.id), 'error': str(exc)})
                continue
            for key in ('employees_considered', 'carried', 'skipped_already', 'skipped_zero'):
                summary[key] += stats[key]

        return summary

    # ── Internals ───────────────────────────────────────────────────────────

    @classmethod
    def _active_policies(cls, organization, day: date):
        return (
            LeavePolicy.objects.filter(
                organization=organization,
                is_active=True,
                effective_from__lte=day,
            )
            .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=day))
            .prefetch_related('rules__leave_type')
            .order_by('-is_default', '-effective_from')
        )

    @classmethod
    def _eligible_employees(cls, organization, employee_type_id):
        return Employee.objects.filter(
            organization=organization,
            employee_type_id=employee_type_id,
            is_active=True,
        ).exclude(
            lifecycle_status__is_terminal=True,
        ).select_related('lifecycle_status')

    @classmethod
    def _policy_for_employee_type(cls, policies, employee_type_id):
        matches = [p for p in policies if p.employee_type_id == employee_type_id]
        if not matches:
            return None
        defaults = [p for p in matches if p.is_default]
        return defaults[0] if defaults else matches[0]

    @classmethod
    def _already_logged(cls, *, employee, leave_type, transaction_type: str, marker: str) -> bool:
        return EmployeeLeaveLog.objects.filter(
            employee=employee,
            leave_type=leave_type,
            transaction_type=transaction_type,
            remarks=marker,
        ).exists()

    @classmethod
    def _year_allocated_qty(cls, *, employee, leave_type, year: int) -> Decimal:
        """Sum of scheduler allocation quantities credited in ``year``."""
        prefix = f'scheduler:'
        year_markers = [
            f'{prefix}{cls.FREQ_MONTHLY}:{year}-{month:02d}' for month in range(1, 13)
        ] + [
            f'{prefix}{cls.FREQ_QUARTERLY}:{year}-Q{q}' for q in range(1, 5)
        ] + [
            f'{prefix}{cls.FREQ_YEARLY}:{year}',
        ]
        total = (
            EmployeeLeaveLog.objects.filter(
                employee=employee,
                leave_type=leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.ALLOCATION,
                remarks__in=year_markers,
            ).aggregate(total=Sum('quantity'))['total']
            or Decimal('0')
        )
        return Decimal(total)

    @classmethod
    def _get_or_create_balance(cls, *, organization, employee, leave_type) -> EmployeeLeaveBalance:
        balance, _ = EmployeeLeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            defaults={
                'organization': organization,
                'allocated': Decimal('0'),
                'used': Decimal('0'),
                'balance': Decimal('0'),
            },
        )
        return balance

    @classmethod
    def _allocate_for_organization(
        cls,
        *,
        organization,
        frequency: str,
        day: date,
        period: str,
        marker: str,
        dry_run: bool,
    ) -> dict:
        stats = {
            'employees_considered': 0,
            'allocated': 0,
            'skipped_already': 0,
            'skipped_zero': 0,
            'skipped_annual_cap': 0,
        }
        policies = list(cls._active_policies(organization, day))
        if not policies:
            return stats

        # Prefer one policy per employee type (default first).
        by_type: dict = {}
        for policy in policies:
            by_type.setdefault(policy.employee_type_id, policy)

        for employee_type_id, policy in by_type.items():
            rules = [
                rule
                for rule in policy.rules.all()
                if rule.is_active and rule.allocation_frequency == frequency and rule.leave_type_id
            ]
            if not rules:
                continue

            employees = list(cls._eligible_employees(organization, employee_type_id))
            for employee in employees:
                stats['employees_considered'] += 1
                for rule in rules:
                    result = cls._allocate_rule(
                        organization=organization,
                        employee=employee,
                        rule=rule,
                        day=day,
                        marker=marker,
                        dry_run=dry_run,
                    )
                    stats[result] += 1
        return stats

    @classmethod
    def _allocate_rule(
        cls,
        *,
        organization,
        employee,
        rule: LeavePolicyRule,
        day: date,
        marker: str,
        dry_run: bool,
    ) -> str:
        leave_type = rule.leave_type
        if cls._already_logged(
            employee=employee,
            leave_type=leave_type,
            transaction_type=EmployeeLeaveLog.TransactionType.ALLOCATION,
            marker=marker,
        ):
            return 'skipped_already'

        qty = Decimal(rule.allocation_quantity or 0)
        if qty <= 0:
            return 'skipped_zero'

        annual_limit = Decimal(rule.annual_limit or 0)
        if annual_limit > 0:
            already = cls._year_allocated_qty(
                employee=employee,
                leave_type=leave_type,
                year=day.year,
            )
            remaining = annual_limit - already
            if remaining <= 0:
                return 'skipped_annual_cap'
            if qty > remaining:
                qty = remaining

        if dry_run:
            return 'allocated'

        with transaction.atomic():
            balance = cls._get_or_create_balance(
                organization=organization,
                employee=employee,
                leave_type=leave_type,
            )
            # Re-check inside transaction for race safety.
            if cls._already_logged(
                employee=employee,
                leave_type=leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.ALLOCATION,
                marker=marker,
            ):
                return 'skipped_already'

            before = balance.balance or Decimal('0')
            balance.allocated = (balance.allocated or Decimal('0')) + qty
            balance.balance = (balance.balance or Decimal('0')) + qty
            balance.save(update_fields=['allocated', 'balance', 'updated_at'])
            EmployeeLeaveLog.objects.create(
                organization=organization,
                employee=employee,
                leave_type=leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.ALLOCATION,
                quantity=qty,
                balance_before=before,
                balance_after=balance.balance,
                remarks=marker,
            )
        return 'allocated'

    @classmethod
    def _carry_forward_for_organization(
        cls,
        *,
        organization,
        day: date,
        from_year: int,
        marker: str,
        dry_run: bool,
    ) -> dict:
        stats = {
            'employees_considered': 0,
            'carried': 0,
            'skipped_already': 0,
            'skipped_zero': 0,
        }
        policies = list(cls._active_policies(organization, day))
        by_type: dict = {}
        for policy in policies:
            by_type.setdefault(policy.employee_type_id, policy)

        for employee_type_id, policy in by_type.items():
            rules = [
                rule
                for rule in policy.rules.all()
                if rule.is_active and rule.carry_forward_allowed and rule.leave_type_id
            ]
            if not rules:
                continue

            employees = list(cls._eligible_employees(organization, employee_type_id))
            for employee in employees:
                stats['employees_considered'] += 1
                for rule in rules:
                    result = cls._carry_forward_rule(
                        organization=organization,
                        employee=employee,
                        rule=rule,
                        marker=marker,
                        dry_run=dry_run,
                    )
                    stats[result] += 1
        return stats

    @classmethod
    def _carry_forward_rule(
        cls,
        *,
        organization,
        employee,
        rule: LeavePolicyRule,
        marker: str,
        dry_run: bool,
    ) -> str:
        leave_type = rule.leave_type
        if cls._already_logged(
            employee=employee,
            leave_type=leave_type,
            transaction_type=EmployeeLeaveLog.TransactionType.CARRY_FORWARD,
            marker=marker,
        ):
            return 'skipped_already'

        balance = EmployeeLeaveBalance.objects.filter(
            employee=employee,
            leave_type=leave_type,
        ).first()
        remaining = Decimal(balance.balance) if balance else Decimal('0')
        if remaining <= 0:
            return 'skipped_zero'

        limit = Decimal(rule.carry_forward_limit or 0)
        carry = remaining if limit <= 0 else min(remaining, limit)
        if carry <= 0:
            return 'skipped_zero'

        if dry_run:
            return 'carried'

        with transaction.atomic():
            if balance is None:
                balance = cls._get_or_create_balance(
                    organization=organization,
                    employee=employee,
                    leave_type=leave_type,
                )
            if cls._already_logged(
                employee=employee,
                leave_type=leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.CARRY_FORWARD,
                marker=marker,
            ):
                return 'skipped_already'

            before = balance.balance or Decimal('0')
            balance.allocated = carry
            balance.used = Decimal('0')
            balance.balance = carry
            balance.save(update_fields=['allocated', 'used', 'balance', 'updated_at'])
            EmployeeLeaveLog.objects.create(
                organization=organization,
                employee=employee,
                leave_type=leave_type,
                transaction_type=EmployeeLeaveLog.TransactionType.CARRY_FORWARD,
                quantity=carry,
                balance_before=before,
                balance_after=carry,
                remarks=marker,
            )
        return 'carried'
