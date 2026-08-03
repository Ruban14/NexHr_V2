"""Django admin for organizations domain models."""

from django.contrib import admin

from apps.organizations.models import (
    IndustryType,
    Organization,
    OrganizationBranch,
    OrganizationMembership,
)


@admin.register(IndustryType)
class IndustryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'organization_code',
        'industry_type',
        'organization_size',
        'notice_period_days',
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

