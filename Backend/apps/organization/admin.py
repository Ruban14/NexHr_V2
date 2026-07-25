"""Django admin registrations for organization masters and profiles."""

from django.contrib import admin

from apps.organization.models import (
    AccessType,
    Department,
    Designation,
    EmployeeType,
    Holiday,
    HolidayCalendar,
    IndustryType,
    LeaveType,
    Organization,
    OrganizationBranch,
    OrganizationMembership,
    Shift,
    UserProfile,
    WorkWeek,
)


@admin.register(IndustryType)
class IndustryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = (
        'name',
        'organization__display_name',
        'organization__organization_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'created_by', 'updated_by')


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'parent', 'sort_order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = (
        'name',
        'department__name',
        'department__organization__display_name',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('department', 'parent', 'created_by', 'updated_by')


@admin.register(EmployeeType)
class EmployeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(AccessType)
class AccessTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry_type', 'is_active', 'created_at')
    list_filter = ('is_active', 'industry_type')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('industry_type', 'created_by', 'updated_by')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'start_time', 'end_time', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'organization__display_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'created_by', 'updated_by')


@admin.register(WorkWeek)
class WorkWeekAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'organization__display_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'created_by', 'updated_by')


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'organization__display_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'created_by', 'updated_by')


@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active', 'year')
    search_fields = ('name', 'organization__display_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'created_by', 'updated_by')


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'holiday_calendar', 'created_at')
    list_filter = ('date',)
    search_fields = ('name', 'holiday_calendar__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('holiday_calendar', 'created_by', 'updated_by')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'organization_code',
        'industry_type',
        'organization_size',
        'email',
        'owner',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'industry_type', 'organization_size', 'country')
    search_fields = (
        'display_name',
        'legal_name',
        'organization_code',
        'email',
        'phone',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('owner', 'created_by', 'updated_by', 'industry_type')


@admin.register(OrganizationBranch)
class OrganizationBranchAdmin(admin.ModelAdmin):
    list_display = (
        'branch_name',
        'branch_code',
        'organization',
        'city',
        'country',
        'is_headquarters',
        'status',
        'created_at',
    )
    list_filter = ('status', 'is_headquarters', 'country')
    search_fields = (
        'branch_name',
        'branch_code',
        'organization__display_name',
        'organization__organization_code',
        'city',
        'email',
        'phone',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'user',
        'mobile_number',
        'is_profile_completed',
        'completed_status',
        'created_at',
    )
    list_filter = (
        'is_profile_completed',
        'completed_status',
        'gender',
    )
    search_fields = (
        'display_name',
        'user__email',
        'mobile_number',
        'city',
        'country',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'created_by', 'updated_by')


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'employee_code',
        'branch',
        'user',
        'designation',
        'employee_type',
        'access_type',
        'status',
        'joining_date',
        'exit_date',
        'created_at',
    )
    list_filter = ('status', 'employee_type', 'access_type', 'branch')
    search_fields = (
        'employee_code',
        'user__email',
        'user__first_name',
        'user__last_name',
        'branch__organization__display_name',
        'branch__organization__organization_code',
        'branch__branch_name',
        'branch__branch_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = (
        'branch',
        'user',
        'designation',
        'employee_type',
        'access_type',
        'created_by',
        'updated_by',
    )
