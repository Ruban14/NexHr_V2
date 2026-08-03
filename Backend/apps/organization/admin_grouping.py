"""Admin index grouping for domain models that share app_label='organization'."""

from __future__ import annotations

from copy import deepcopy

from django.contrib import admin

# Model object_name -> domain section for the admin sidebar.
DOMAIN_SECTIONS: list[tuple[str, str, tuple[str, ...]]] = [
    (
        'organizations',
        'Organizations',
        ('IndustryType', 'Organization', 'OrganizationBranch', 'OrganizationMembership'),
    ),
    (
        'workforce',
        'Workforce',
        (
            'Department',
            'Designation',
            'EmployeeType',
            'AccessType',
            'Shift',
            'WorkWeek',
            'LeaveType',
            'HolidayCalendar',
            'Holiday',
            'EmployeeLifecycleStatus',
            'EmployeeLifecycleTransition',
        ),
    ),
    (
        'people',
        'People',
        (
            'Employee',
            'EmployeeBankDetail',
            'EmployeeEducation',
            'EmployeeJobExperience',
            'EmployeeTaxDetail',
            'EmployeeLifecycleHistory',
        ),
    ),
    (
        'documents',
        'Documents',
        (
            'DocumentCategory',
            'DocumentDefinition',
            'DocumentPolicy',
            'DocumentPolicyItem',
            'File',
            'EmployeeDocument',
        ),
    ),
    (
        'assets',
        'Assets',
        ('AssetType', 'Asset', 'EmployeeAssetAssignment'),
    ),
    (
        'leave',
        'Leave',
        (
            'LeavePolicy',
            'LeavePolicyRule',
            'EmployeeLeaveBalance',
            'LeaveApplication',
            'EmployeeLeaveLog',
        ),
    ),
    (
        'attendance',
        'Attendance',
        ('Attendance', 'AttendanceSession', 'AttendanceBreak'),
    ),
]


def _model_object_name(model_dict: dict) -> str:
    return model_dict.get('object_name') or ''


def build_grouped_app_list(original_app_list: list[dict]) -> list[dict]:
    """Split the monolithic organization app into domain sections in admin."""
    org_app = None
    other_apps: list[dict] = []
    for app in original_app_list:
        if app.get('app_label') == 'organization':
            org_app = app
        else:
            other_apps.append(app)

    if org_app is None:
        return original_app_list

    models_by_name = {_model_object_name(model): model for model in org_app.get('models', [])}
    grouped_apps: list[dict] = []
    used: set[str] = set()

    for app_label, verbose_name, model_names in DOMAIN_SECTIONS:
        section_models = []
        for name in model_names:
            model = models_by_name.get(name)
            if model is not None:
                section_models.append(model)
                used.add(name)
        if not section_models:
            continue
        grouped_apps.append(
            {
                'name': verbose_name,
                'app_label': app_label,
                'app_url': org_app.get('app_url', '/admin/organization/'),
                'has_module_perms': org_app.get('has_module_perms', True),
                'models': section_models,
            }
        )

    leftover = [model for name, model in models_by_name.items() if name not in used]
    if leftover:
        grouped_apps.append(
            {
                'name': 'Organization (other)',
                'app_label': 'organization',
                'app_url': org_app.get('app_url', '/admin/organization/'),
                'has_module_perms': org_app.get('has_module_perms', True),
                'models': leftover,
            }
        )

    # Keep Authentication / other apps first-ish: core-ish after auth.
    result: list[dict] = []
    auth_apps = [app for app in other_apps if app.get('app_label') == 'authentication']
    rest = [app for app in other_apps if app.get('app_label') != 'authentication']
    result.extend(auth_apps)
    result.extend(grouped_apps)
    result.extend(rest)
    return result


_original_get_app_list = None


def install_admin_grouping() -> None:
    """Monkey-patch default admin site index grouping once."""
    global _original_get_app_list
    site = admin.site
    if getattr(site, '_nexhr_domain_grouping', False):
        return

    _original_get_app_list = site.get_app_list

    def get_app_list(request, app_label=None):
        app_list = _original_get_app_list(request, app_label=app_label)
        if app_label is not None:
            # Detail filtered views keep Django's default behaviour.
            return app_list
        return build_grouped_app_list(deepcopy(app_list))

    site.get_app_list = get_app_list  # type: ignore[method-assign]
    site._nexhr_domain_grouping = True
