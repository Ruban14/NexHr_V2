"""Django admin for attendance domain models."""

from django.contrib import admin

from apps.attendance.models import (
    Attendance,
    AttendanceBreak,
    AttendanceSession,
)


class AttendanceSessionInline(admin.TabularInline):
    model = AttendanceSession
    extra = 0
    fields = ('check_in', 'check_out', 'worked_hours', 'source', 'remarks')
    readonly_fields = ('worked_hours',)
    ordering = ('check_in',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'attendance_date',
        'status',
        'is_manual',
        'approval_status',
        'first_check_in',
        'last_check_out',
        'total_worked_hours',
        'organization',
        'updated_at',
    )
    list_filter = ('status', 'is_manual', 'approval_status')
    search_fields = (
        'employee__employee_code',
        'employee__email',
        'employee__display_name',
        'remarks',
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'approved_at')
    raw_id_fields = ('organization', 'employee', 'approved_by', 'created_by', 'updated_by')
    inlines = (AttendanceSessionInline,)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = (
        'attendance',
        'check_in',
        'check_out',
        'worked_hours',
        'source',
        'created_at',
    )
    list_filter = ('source',)
    search_fields = (
        'attendance__employee__employee_code',
        'attendance__employee__email',
        'remarks',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('attendance', 'created_by', 'updated_by')


@admin.register(AttendanceBreak)
class AttendanceBreakAdmin(admin.ModelAdmin):
    list_display = (
        'session',
        'break_start',
        'break_end',
        'break_duration',
        'created_at',
    )
    search_fields = (
        'session__attendance__employee__employee_code',
        'session__attendance__employee__email',
        'remarks',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('session', 'created_by', 'updated_by')

