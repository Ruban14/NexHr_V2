"""Django admin for documents domain models."""

from django.contrib import admin

from apps.documents.models import (
    DocumentCategory,
    DocumentDefinition,
    DocumentPolicy,
    DocumentPolicyItem,
    EmployeeDocument,
    File,
)


class DocumentPolicyItemInline(admin.TabularInline):
    model = DocumentPolicyItem
    extra = 0
    fields = (
        'document',
        'display_order',
        'is_required',
        'allow_multiple',
        'verification_required',
        'requires_expiry',
    )
    raw_id_fields = ('document',)
    ordering = ('display_order', 'id')


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('created_by', 'updated_by')


@admin.register(DocumentDefinition)
class DocumentDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = (
        'name',
        'description',
        'category__name',
        'organization__display_name',
        'organization__organization_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'category', 'created_by', 'updated_by')


@admin.register(DocumentPolicy)
class DocumentPolicyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'employee_type',
        'organization',
        'is_default',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'is_default', 'employee_type')
    search_fields = (
        'name',
        'description',
        'employee_type__name',
        'organization__display_name',
        'organization__organization_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('organization', 'employee_type', 'created_by', 'updated_by')
    inlines = (DocumentPolicyItemInline,)


@admin.register(DocumentPolicyItem)
class DocumentPolicyItemAdmin(admin.ModelAdmin):
    list_display = (
        'policy',
        'document',
        'display_order',
        'is_required',
        'allow_multiple',
        'verification_required',
        'requires_expiry',
    )
    list_filter = ('is_required', 'allow_multiple', 'verification_required', 'requires_expiry')
    search_fields = ('policy__name', 'document__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('policy', 'document', 'created_by', 'updated_by')
    ordering = ('policy', 'display_order', 'id')


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        'original_name',
        'organization',
        'extension',
        'mime_type',
        'file_size',
        'is_active',
        'is_deleted',
        'created_at',
    )
    list_filter = ('is_active', 'is_deleted', 'extension')
    search_fields = ('original_name', 'organization__display_name', 'checksum')
    readonly_fields = ('id', 'created_at', 'updated_at', 'checksum')
    raw_id_fields = ('organization', 'created_by', 'updated_by')


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'document',
        'status',
        'issue_date',
        'expiry_date',
        'verified_by',
        'verified_at',
        'created_at',
    )
    list_filter = ('status',)
    search_fields = (
        'employee__employee_code',
        'employee__email',
        'document__name',
        'remarks',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = (
        'employee',
        'document',
        'file',
        'verified_by',
        'created_by',
        'updated_by',
    )

