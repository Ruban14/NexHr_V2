"""Re-export domain models for backward-compatible imports.

Models live in domain apps but keep app_label='organization' so
migration history and database tables remain unchanged.
"""

from apps.organizations.models import (
    IndustryType,
    Organization,
    OrganizationBranch,
    OrganizationMembership,
)
from apps.workforce.models import (
    AccessType,
    Department,
    Designation,
    EmployeeLifecycleStatus,
    EmployeeLifecycleTransition,
    EmployeeType,
    Holiday,
    HolidayCalendar,
    LeaveType,
    Shift,
    WorkWeek,
)
from apps.people.models import (
    Employee,
    EmployeeBankDetail,
    EmployeeEducation,
    EmployeeJobExperience,
    EmployeeLifecycleHistory,
    EmployeeTaxDetail,
)
from apps.documents.models import (
    DocumentCategory,
    DocumentDefinition,
    DocumentPolicy,
    DocumentPolicyItem,
    EmployeeDocument,
    File,
)
from apps.assets.models import (
    Asset,
    AssetType,
    EmployeeAssetAssignment,
)
from apps.leave.models import (
    EmployeeLeaveBalance,
    EmployeeLeaveLog,
    LeaveApplication,
    LeavePolicy,
    LeavePolicyRule,
)
from apps.attendance.models import (
    Attendance,
    AttendanceBreak,
    AttendanceSession,
)

__all__ = [
    'AccessType',
    'Asset',
    'AssetType',
    'Attendance',
    'AttendanceBreak',
    'AttendanceSession',
    'Department',
    'Designation',
    'DocumentCategory',
    'DocumentDefinition',
    'DocumentPolicy',
    'DocumentPolicyItem',
    'Employee',
    'EmployeeAssetAssignment',
    'EmployeeBankDetail',
    'EmployeeDocument',
    'EmployeeEducation',
    'EmployeeJobExperience',
    'EmployeeLeaveBalance',
    'EmployeeLeaveLog',
    'EmployeeLifecycleHistory',
    'EmployeeLifecycleStatus',
    'EmployeeLifecycleTransition',
    'EmployeeTaxDetail',
    'EmployeeType',
    'File',
    'Holiday',
    'HolidayCalendar',
    'IndustryType',
    'LeaveApplication',
    'LeavePolicy',
    'LeavePolicyRule',
    'LeaveType',
    'Organization',
    'OrganizationBranch',
    'OrganizationMembership',
    'Shift',
    'WorkWeek',
]
