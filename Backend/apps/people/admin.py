"""Django admin for people domain models."""

from django.contrib import admin

from apps.people.models import (
    Employee,
    EmployeeBankDetail,
    EmployeeEducation,
    EmployeeJobExperience,
    EmployeeLifecycleHistory,
    EmployeeTaxDetail,
)


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

