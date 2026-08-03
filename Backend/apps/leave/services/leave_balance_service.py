"""Employee leave balance allocation and adjustments."""

from __future__ import annotations

from apps.leave.models import EmployeeLeaveBalance


class LeaveBalanceService:
    """Balance-focused API; delegates to LeaveService implementations."""

    @classmethod
    def list_balances(cls, **kwargs):
        from apps.leave.services.leave_service import LeaveService

        return LeaveService.list_balances(**kwargs)

    @classmethod
    def allocate_balance(cls, **kwargs):
        from apps.leave.services.leave_service import LeaveService

        return LeaveService.allocate_balance(**kwargs)

    @classmethod
    def adjust_balance(cls, **kwargs):
        from apps.leave.services.leave_service import LeaveService

        return LeaveService.adjust_balance(**kwargs)

    @classmethod
    def seed_from_policy(cls, **kwargs):
        from apps.leave.services.leave_service import LeaveService

        return LeaveService.seed_from_policy(**kwargs)

    @classmethod
    def serialize_balance(cls, item: EmployeeLeaveBalance) -> dict:
        from apps.leave.services.leave_service import LeaveService

        return LeaveService.serialize_balance(item)
