"""Backward-compatible re-export."""

from apps.people.services.employee_lifecycle_service import EmployeeLifecycleEngine
from apps.people.services.employee_service import EmployeeService

__all__ = ['EmployeeLifecycleEngine', 'EmployeeService']
