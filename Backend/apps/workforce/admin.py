"""Django admin for workforce domain models."""

from django.contrib import admin

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


@admin.register(EmployeeLifecycleStatus)
class EmployeeLifecycleStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'ordinal', 'is_initial', 'is_terminal', 'is_active')
    list_filter = ('is_active', 'is_initial', 'is_terminal')
    search_fields = ('name', 'key')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('ordinal', 'name')


@admin.register(EmployeeLifecycleTransition)
class EmployeeLifecycleTransitionAdmin(admin.ModelAdmin):
    list_display = ('action_label', 'from_status', 'to_status', 'sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('action_label', 'from_status__name', 'to_status__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('from_status', 'to_status', 'created_by', 'updated_by')


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

