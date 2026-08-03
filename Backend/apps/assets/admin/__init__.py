"""Django admin for assets domain models."""

from django.contrib import admin

from apps.assets.models import (
    Asset,
    AssetType,
    EmployeeAssetAssignment,
)


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = (
        'name',
        'organization__display_name',
        'organization__organization_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'created_by', 'updated_by')


class EmployeeAssetAssignmentInline(admin.TabularInline):
    model = EmployeeAssetAssignment
    extra = 0
    fields = (
        'employee',
        'assigned_at',
        'expected_return_at',
        'returned_at',
        'status',
        'issued_by',
        'received_by',
        'remarks',
    )
    raw_id_fields = ('employee', 'issued_by', 'received_by')
    readonly_fields = ('assigned_at', 'returned_at', 'status')
    ordering = ('-assigned_at',)
    show_change_link = True


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_code',
        'name',
        'asset_type',
        'status',
        'organization',
        'is_active',
        'created_at',
    )
    list_filter = ('status', 'is_active')
    search_fields = (
        'asset_code',
        'name',
        'serial_number',
        'brand',
        'model',
        'organization__display_name',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'asset_type', 'created_by', 'updated_by')
    inlines = (EmployeeAssetAssignmentInline,)


@admin.register(EmployeeAssetAssignment)
class EmployeeAssetAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'employee',
        'status',
        'assigned_at',
        'returned_at',
        'organization',
        'created_at',
    )
    list_filter = ('status',)
    search_fields = (
        'asset__asset_code',
        'asset__name',
        'employee__employee_code',
        'employee__email',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = (
        'organization',
        'employee',
        'asset',
        'issued_by',
        'received_by',
        'created_by',
        'updated_by',
    )

