"""Django admin registrations for organization masters and profiles."""

from django.contrib import admin

from apps.organization.models import (
    AccessType,
    Designation,
    EmployeeType,
    IndustryType,
    Organization,
    OrganizationMembership,
    UserProfile,
)


@admin.register(IndustryType)
class IndustryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'industry_type', 'is_active', 'created_at')
    list_filter = ('is_active', 'industry_type')
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('industry_type', 'created_by', 'updated_by')


@admin.register(EmployeeType)
class EmployeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(AccessType)
class AccessTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'industry_type', 'is_active', 'created_at')
    list_filter = ('is_active', 'industry_type')
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('industry_type', 'created_by', 'updated_by')


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
        'organization',
        'user_profile',
        'designation',
        'employee_type',
        'access_type',
        'status',
        'joining_date',
        'exit_date',
        'created_at',
    )
    list_filter = ('status', 'employee_type', 'access_type', 'organization')
    search_fields = (
        'employee_code',
        'user_profile__display_name',
        'user_profile__user__email',
        'organization__display_name',
        'organization__organization_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = (
        'organization',
        'user_profile',
        'designation',
        'employee_type',
        'access_type',
        'created_by',
        'updated_by',
    )
