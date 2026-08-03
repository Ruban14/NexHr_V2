"""Django admin for leave domain models."""

from django.contrib import admin

from apps.leave.models import (
    EmployeeLeaveBalance,
    EmployeeLeaveLog,
    LeaveApplication,
    LeavePolicy,
    LeavePolicyRule,
)


class LeavePolicyRuleInline(admin.TabularInline):
    model = LeavePolicyRule
    extra = 0
    fields = (
        'leave_type',
        'allocation_frequency',
        'allocation_quantity',
        'annual_limit',
        'carry_forward_allowed',
        'carry_forward_limit',
        'encashment_allowed',
        'encashment_limit',
        'allow_half_day',
        'allow_negative_balance',
        'minimum_service_days',
        'maximum_consecutive_days',
        'is_active',
    )
    raw_id_fields = ('leave_type',)
    ordering = ('leave_type__name', 'id')


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'employee_type',
        'effective_from',
        'effective_to',
        'is_default',
        'organization',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'is_default', 'employee_type')
    search_fields = (
        'code',
        'name',
        'description',
        'employee_type__name',
        'organization__display_name',
        'organization__organization_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'employee_type', 'created_by', 'updated_by')
    inlines = (LeavePolicyRuleInline,)


@admin.register(LeavePolicyRule)
class LeavePolicyRuleAdmin(admin.ModelAdmin):
    list_display = (
        'policy',
        'leave_type',
        'allocation_frequency',
        'allocation_quantity',
        'annual_limit',
        'carry_forward_allowed',
        'encashment_allowed',
        'is_active',
        'created_at',
    )
    list_filter = (
        'allocation_frequency',
        'is_active',
        'carry_forward_allowed',
        'encashment_allowed',
    )
    search_fields = (
        'policy__code',
        'policy__name',
        'leave_type__name',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('policy', 'leave_type', 'created_by', 'updated_by')


@admin.register(EmployeeLeaveBalance)
class EmployeeLeaveBalanceAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'leave_type',
        'allocated',
        'used',
        'balance',
        'organization',
        'updated_at',
    )
    list_filter = ('leave_type',)
    search_fields = (
        'employee__employee_code',
        'employee__email',
        'leave_type__name',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'employee', 'leave_type', 'created_by', 'updated_by')


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'leave_type',
        'from_date',
        'to_date',
        'number_of_days',
        'status',
        'organization',
        'created_at',
    )
    list_filter = ('status', 'is_half_day', 'leave_type')
    search_fields = (
        'employee__employee_code',
        'employee__email',
        'leave_type__name',
        'reason',
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'approved_at')
    raw_id_fields = (
        'organization',
        'employee',
        'leave_type',
        'approved_by',
        'created_by',
        'updated_by',
    )


@admin.register(EmployeeLeaveLog)
class EmployeeLeaveLogAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'leave_type',
        'transaction_type',
        'quantity',
        'balance_before',
        'balance_after',
        'organization',
        'created_at',
    )
    list_filter = ('transaction_type', 'leave_type')
    search_fields = (
        'employee__employee_code',
        'employee__email',
        'leave_type__name',
        'remarks',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = (
        'organization',
        'employee',
        'leave_type',
        'leave_application',
        'created_by',
        'updated_by',
    )

