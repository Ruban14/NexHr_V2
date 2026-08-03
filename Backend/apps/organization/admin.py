"""Django admin registrations for organization masters and profiles."""

from django.contrib import admin

from apps.organization.models import (
    AccessType,
    Asset,
    AssetType,
    Attendance,
    AttendanceBreak,
    AttendanceSession,
    Department,
    Designation,
    DocumentCategory,
    DocumentDefinition,
    DocumentPolicy,
    DocumentPolicyItem,
    Employee,
    EmployeeAssetAssignment,
    EmployeeBankDetail,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeJobExperience,
    EmployeeLeaveBalance,
    EmployeeLeaveLog,
    EmployeeLifecycleHistory,
    EmployeeLifecycleStatus,
    EmployeeLifecycleTransition,
    EmployeeTaxDetail,
    EmployeeType,
    File,
    Holiday,
    HolidayCalendar,
    IndustryType,
    LeaveApplication,
    LeavePolicy,
    LeavePolicyRule,
    LeaveType,
    Organization,
    OrganizationBranch,
    OrganizationMembership,
    Shift,
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


class EmployeeBankDetailInline(admin.TabularInline):
    model = EmployeeBankDetail
    extra = 0
    fields = (
        'account_holder_name',
        'bank_name',
        'account_number',
        'ifsc_code',
        'is_primary',
    )


class EmployeeEducationInline(admin.TabularInline):
    model = EmployeeEducation
    extra = 0
    fields = (
        'degree',
        'institution',
        'field_of_study',
        'year_of_passing',
        'grade',
    )


class EmployeeJobExperienceInline(admin.TabularInline):
    model = EmployeeJobExperience
    extra = 0
    fields = (
        'company_name',
        'job_title',
        'start_date',
        'end_date',
        'is_current',
        'location',
        'description',
    )


class EmployeeTaxDetailInline(admin.StackedInline):
    model = EmployeeTaxDetail
    extra = 0
    max_num = 1
    fields = (
        'pan_number',
        'aadhaar_number',
        'uan_number',
        'pf_number',
        'esi_number',
        'tax_regime',
        'tax_identification_number',
        'is_pf_applicable',
        'is_esi_applicable',
        'professional_tax_applicable',
        'labour_welfare_fund_applicable',
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'employee_code',
        'email',
        'mobile_number',
        'organization',
        'lifecycle_status',
        'is_profile_completed',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'lifecycle_status', 'is_profile_completed', 'gender')
    search_fields = (
        'display_name',
        'email',
        'employee_code',
        'first_name',
        'last_name',
        'mobile_number',
        'emergency_contact_name',
        'emergency_contact_phone',
        'user__email',
    )
    inlines = (
        EmployeeBankDetailInline,
        EmployeeEducationInline,
        EmployeeJobExperienceInline,
        EmployeeTaxDetailInline,
    )
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'organization',
                    'branch',
                    'user',
                    'lifecycle_status',
                    'employee_code',
                    'email',
                    'first_name',
                    'last_name',
                    'display_name',
                    'profile_photo',
                    'is_active',
                    'is_profile_completed',
                    'completed_status',
                ),
            },
        ),
        (
            'Contact',
            {
                'fields': (
                    'mobile_number',
                    'alternate_mobile',
                    'country',
                    'state',
                    'city',
                    'address_line1',
                    'postal_code',
                ),
            },
        ),
        (
            'Emergency contact',
            {
                'fields': (
                    'emergency_contact_name',
                    'emergency_contact_relationship',
                    'emergency_contact_phone',
                ),
            },
        ),
        (
            'Personal',
            {
                'fields': (
                    'date_of_birth',
                    'gender',
                    'blood_group',
                    'mother_language',
                    'languages_known',
                ),
            },
        ),
        (
            'Employment',
            {
                'fields': (
                    'designation',
                    'employee_type',
                    'access_type',
                    'reporting_manager',
                    'joining_date',
                    'exit_date',
                ),
            },
        ),
        (
            'Audit',
            {
                'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            },
        ),
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = (
        'organization',
        'branch',
        'user',
        'lifecycle_status',
        'designation',
        'employee_type',
        'access_type',
        'reporting_manager',
        'created_by',
        'updated_by',
    )


@admin.register(EmployeeBankDetail)
class EmployeeBankDetailAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'bank_name',
        'account_holder_name',
        'account_number',
        'ifsc_code',
        'is_primary',
        'updated_at',
    )
    list_filter = ('is_primary',)
    search_fields = (
        'employee__display_name',
        'employee__email',
        'employee__employee_code',
        'bank_name',
        'account_holder_name',
        'account_number',
        'ifsc_code',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('employee', 'created_by', 'updated_by')


@admin.register(EmployeeEducation)
class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'degree',
        'institution',
        'field_of_study',
        'year_of_passing',
        'grade',
        'updated_at',
    )
    list_filter = ('year_of_passing',)
    search_fields = (
        'employee__display_name',
        'employee__email',
        'employee__employee_code',
        'degree',
        'institution',
        'field_of_study',
        'grade',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('employee', 'created_by', 'updated_by')


@admin.register(EmployeeJobExperience)
class EmployeeJobExperienceAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'company_name',
        'job_title',
        'start_date',
        'end_date',
        'is_current',
        'location',
        'updated_at',
    )
    list_filter = ('is_current',)
    search_fields = (
        'employee__display_name',
        'employee__email',
        'employee__employee_code',
        'company_name',
        'job_title',
        'location',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('employee', 'created_by', 'updated_by')


@admin.register(EmployeeLifecycleHistory)
class EmployeeLifecycleHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('to_status',)
    search_fields = ('employee__display_name', 'employee__email', 'remarks')
    readonly_fields = (
        'id',
        'employee',
        'from_status',
        'to_status',
        'changed_by',
        'changed_at',
        'remarks',
        'created_at',
        'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # History is read-only in its own admin (obj is None on changelist).
        # Return True for a concrete row so parent deletes (User/Employee)
        # can cascade — Django 4.2 checks this ModelAdmin method.
        return obj is not None

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions


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


@admin.register(EmployeeTaxDetail)
class EmployeeTaxDetailAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'pan_number',
        'tax_regime',
        'is_pf_applicable',
        'is_esi_applicable',
        'professional_tax_applicable',
        'updated_at',
    )
    list_filter = (
        'tax_regime',
        'is_pf_applicable',
        'is_esi_applicable',
        'professional_tax_applicable',
        'labour_welfare_fund_applicable',
    )
    search_fields = (
        'employee__employee_code',
        'employee__email',
        'pan_number',
        'aadhaar_number',
        'uan_number',
        'pf_number',
        'esi_number',
        'tax_identification_number',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('employee', 'created_by', 'updated_by')


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
