"""Django admin registrations for organization masters and profiles."""

from django.contrib import admin

from apps.organization.models import (
    AccessType,
    Department,
    Designation,
    Employee,
    EmployeeBankDetail,
    EmployeeEducation,
    EmployeeJobExperience,
    EmployeeLifecycleHistory,
    EmployeeLifecycleStatus,
    EmployeeLifecycleTransition,
    EmployeeType,
    Holiday,
    HolidayCalendar,
    IndustryType,
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
    inlines = (EmployeeBankDetailInline, EmployeeEducationInline, EmployeeJobExperienceInline)
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
