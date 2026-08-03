"""Organization master / lookup models and user profiles."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import AuditedModel, TimeStampedModel, UUIDModel


class IndustryType(UUIDModel, TimeStampedModel, AuditedModel):
    """School, College, IT office, etc."""
    name = models.CharField(max_length=160, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

class Organization(UUIDModel, TimeStampedModel, AuditedModel):
    """Primary tenant / company record."""

    class OrganizationSize(models.TextChoices):
        SIZE_1_10 = '1-10', '1-10'
        SIZE_11_50 = '11-50', '11-50'
        SIZE_51_200 = '51-200', '51-200'
        SIZE_201_500 = '201-500', '201-500'
        SIZE_500_PLUS = '500+', '500+'

    organization_code = models.CharField(max_length=64, unique=True, db_index=True)
    legal_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, db_index=True)
    industry_type = models.ForeignKey(IndustryType,on_delete=models.CASCADE,null=True,blank=True,related_name='organizations')
    organization_size = models.CharField(max_length=32,choices=OrganizationSize.choices,blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    logo = models.TextField(blank=True, default='')
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    currency = models.CharField(max_length=3, default='INR')
    notice_period_days = models.PositiveIntegerField(
        default=30,
        help_text='Default notice period duration in days used to calculate exit date.',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='owned_organizations')

    class Meta:
        ordering = ['display_name']
        indexes = [
            models.Index(fields=['is_active', 'display_name']),
        ]

    def __str__(self) -> str:
        return self.display_name or self.legal_name


class OrganizationBranch(UUIDModel, TimeStampedModel):
    """Organization branch / location."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    organization = models.ForeignKey(Organization,on_delete=models.CASCADE,related_name='branches')
    branch_code = models.CharField(max_length=32)
    branch_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_headquarters = models.BooleanField(default=False)
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.ACTIVE,db_index=True)

    class Meta:
        ordering = ['-is_headquarters', 'branch_name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'branch_code'],
                name='uniq_organization_branch_code',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.branch_name} ({self.organization.organization_code})'


class Department(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization department (flat list per organization)."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='departments',
    )
    name = models.CharField(max_length=150, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='uniq_department_name_per_organization',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'is_active'], name='organizatio_organiz_dept_idx'),
        ]

    def __str__(self) -> str:
        return self.name


class Designation(UUIDModel, TimeStampedModel, AuditedModel):
    """Department designation with optional parent hierarchy."""

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='designations',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    name = models.CharField(max_length=160, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['department', 'name'],
                name='uniq_designation_per_department',
            ),
        ]
        indexes = [
            models.Index(fields=['department', 'is_active'], name='organizatio_departm_desig_idx'),
            models.Index(fields=['parent', 'sort_order'], name='organizatio_parent_sort_idx'),
        ]

    def __str__(self) -> str:
        return self.name


class EmployeeType(UUIDModel, TimeStampedModel, AuditedModel):
    """permanent, contract, intern, External, etc."""

    name = models.CharField(max_length=160, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class AccessType(UUIDModel, TimeStampedModel, AuditedModel):
    """Admin, Employee, Manager"""

    industry_type = models.ForeignKey(IndustryType,on_delete=models.CASCADE,null=True,blank=True,related_name='access_types')
    name = models.CharField(max_length=160, db_index=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

class OrganizationMembership(UUIDModel, TimeStampedModel, AuditedModel):
    """Links a user to an organization branch with role and employment details."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        PENDING = 'pending', 'Pending'
        EXITED = 'exited', 'Exited'

    branch = models.ForeignKey(OrganizationBranch, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    employee_type = models.ForeignKey(
        EmployeeType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    access_type = models.ForeignKey(
        AccessType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='memberships',
    )
    employee_code = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    joining_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'user'],
                name='uniq_org_membership_branch_user',
            ),
            models.UniqueConstraint(
                fields=['branch', 'employee_code'],
                condition=~models.Q(employee_code=''),
                name='uniq_org_membership_branch_employee_code',
            ),
        ]
        indexes = [
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    @property
    def organization(self):
        return self.branch.organization

    def __str__(self) -> str:
        return f'{self.user} @ {self.branch}'


class Shift(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization shift."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='shifts',
    )

    name = models.CharField(max_length=150)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_shift_name_per_org",
            )
        ]

    def __str__(self):
        return self.name


class WorkWeek(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization work week."""

    class WeekDay(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="work_weeks",
    )
    name = models.CharField(max_length=100)
    working_days = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_workweek_name_per_org",
            )
        ]

    def __str__(self):
        return self.name


class LeaveType(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization leave type."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leave_types",
    )
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_leave_type_per_org",
            )
        ]

    def __str__(self):
        return self.name

class HolidayCalendar(UUIDModel, TimeStampedModel, AuditedModel):
    """Holiday calendar."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="holiday_calendars",
    )
    name = models.CharField(max_length=150)
    year = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-year", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name", "year"],
                name="uniq_holiday_calendar_per_org",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.year})"


class Holiday(UUIDModel, TimeStampedModel, AuditedModel):
    """Holiday inside a calendar."""

    holiday_calendar = models.ForeignKey(
        HolidayCalendar,
        on_delete=models.CASCADE,
        related_name="holidays",
    )
    name = models.CharField(max_length=150)
    date = models.DateField()

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["holiday_calendar", "date"],
                name="uniq_holiday_date_per_calendar",
            )
        ]

    def __str__(self):
        return self.name


class EmployeeLifecycleStatus(UUIDModel, TimeStampedModel, AuditedModel):
    """Configurable employee lifecycle statuses (Draft, Active, …)."""

    name = models.CharField(max_length=120)
    key = models.SlugField(max_length=64, unique=True)
    ordinal = models.PositiveIntegerField(default=0, db_index=True)
    is_initial = models.BooleanField(default=False, db_index=True)
    is_terminal = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['ordinal', 'name']
        indexes = [
            models.Index(fields=['is_active', 'ordinal']),
        ]

    def __str__(self) -> str:
        return self.name


class Employee(UUIDModel, TimeStampedModel, AuditedModel):
    """Organization employee record (profile + employment + lifecycle)."""

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer not to say'

    class BloodGroup(models.TextChoices):
        A_POSITIVE = 'A+', 'A+'
        A_NEGATIVE = 'A-', 'A-'
        B_POSITIVE = 'B+', 'B+'
        B_NEGATIVE = 'B-', 'B-'
        AB_POSITIVE = 'AB+', 'AB+'
        AB_NEGATIVE = 'AB-', 'AB-'
        O_POSITIVE = 'O+', 'O+'
        O_NEGATIVE = 'O-', 'O-'
        UNKNOWN = 'unknown', 'Unknown'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='employees',
    )
    branch = models.ForeignKey(
        OrganizationBranch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employee_records',
    )
    lifecycle_status = models.ForeignKey(
        EmployeeLifecycleStatus,
        on_delete=models.CASCADE,
        related_name='employees',
    )
    employee_code = models.CharField(max_length=64, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    profile_photo = models.FileField(upload_to='employee_photos/', blank=True)
    mobile_number = models.CharField(max_length=32, blank=True, db_index=True)
    alternate_mobile = models.CharField(max_length=32, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=32, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=32, choices=Gender.choices, blank=True)
    blood_group = models.CharField(max_length=16, choices=BloodGroup.choices, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    mother_language = models.CharField(max_length=100, blank=True)
    languages_known = models.JSONField(default=list, blank=True)
    is_profile_completed = models.BooleanField(default=False, db_index=True)
    completed_status = models.CharField(max_length=10, blank=True)
    designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    employee_type = models.ForeignKey(
        EmployeeType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    access_type = models.ForeignKey(
        AccessType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
    )
    reporting_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        help_text='Manager who approves leave and similar requests for this employee.',
    )
    joining_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'employee_code'],
                condition=~models.Q(employee_code=''),
                name='uniq_employee_code_per_organization',
            ),
            models.UniqueConstraint(
                fields=['organization', 'email'],
                condition=~models.Q(email=''),
                name='uniq_employee_email_per_organization',
            ),
            models.UniqueConstraint(
                fields=['organization', 'user'],
                condition=models.Q(user__isnull=False),
                name='uniq_employee_user_per_organization',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'lifecycle_status']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_profile_completed', 'completed_status']),
        ]

    def __str__(self) -> str:
        return self.display_name or self.email or str(self.id)


class EmployeeBankDetail(UUIDModel, TimeStampedModel, AuditedModel):
    """Salary / payroll bank account linked to an employee."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='bank_details',
    )
    account_holder_name = models.CharField(max_length=150, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-is_primary', 'created_at']
        verbose_name = 'Employee bank detail'
        verbose_name_plural = 'Employee bank details'
        constraints = [
            models.UniqueConstraint(
                fields=['employee'],
                condition=models.Q(is_primary=True),
                name='uniq_primary_bank_per_employee',
            ),
        ]
        indexes = [
            models.Index(fields=['employee', 'is_primary']),
        ]

    def __str__(self) -> str:
        label = self.bank_name or self.account_number or 'Bank account'
        return f'{self.employee_id}: {label}'


class EmployeeEducation(UUIDModel, TimeStampedModel, AuditedModel):
    """Education / qualification record linked to an employee."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='education_details',
    )
    degree = models.CharField(max_length=150, blank=True)
    institution = models.CharField(max_length=255, blank=True)
    field_of_study = models.CharField(max_length=150, blank=True)
    year_of_passing = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-year_of_passing', 'created_at']
        verbose_name = 'Employee education'
        verbose_name_plural = 'Employee educations'
        indexes = [
            models.Index(fields=['employee', 'year_of_passing']),
        ]

    def __str__(self) -> str:
        label = self.degree or self.institution or 'Education'
        return f'{self.employee_id}: {label}'


class EmployeeJobExperience(UUIDModel, TimeStampedModel, AuditedModel):
    """Prior / external job experience linked to an employee."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='job_experiences',
    )
    company_name = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False, db_index=True)
    location = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-is_current', '-start_date', 'created_at']
        verbose_name = 'Employee job experience'
        verbose_name_plural = 'Employee job experiences'
        indexes = [
            models.Index(fields=['employee', 'start_date']),
        ]

    def __str__(self) -> str:
        label = self.job_title or self.company_name or 'Experience'
        return f'{self.employee_id}: {label}'


class EmployeeLifecycleTransition(UUIDModel, TimeStampedModel, AuditedModel):
    """Allowed edges between lifecycle statuses (e.g. Draft → Onboarding Started)."""

    from_status = models.ForeignKey(
        EmployeeLifecycleStatus,
        on_delete=models.CASCADE,
        related_name='outgoing_transitions',
    )
    to_status = models.ForeignKey(
        EmployeeLifecycleStatus,
        on_delete=models.CASCADE,
        related_name='incoming_transitions',
    )
    action_label = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['sort_order', 'action_label']
        constraints = [
            models.UniqueConstraint(
                fields=['from_status', 'to_status'],
                name='uniq_lifecycle_transition_from_to',
            ),
        ]
        indexes = [
            models.Index(fields=['from_status', 'is_active']),
        ]

    def __str__(self) -> str:
        return f'{self.from_status} → {self.to_status}'


class EmployeeLifecycleHistory(UUIDModel, TimeStampedModel):
    """Immutable audit trail of employee lifecycle movements."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='lifecycle_history',
    )
    from_status = models.ForeignKey(
        EmployeeLifecycleStatus,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='history_as_from',
    )
    to_status = models.ForeignKey(
        EmployeeLifecycleStatus,
        on_delete=models.CASCADE,
        related_name='history_as_to',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_lifecycle_changes',
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    remarks = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['employee', 'changed_at']),
        ]
        default_permissions = ('add', 'view', 'delete')

    def __str__(self) -> str:
        return f'{self.employee_id}: {self.from_status_id} → {self.to_status_id}'

    def delete(self, using=None, keep_parents=False):
        raise PermissionError('Lifecycle history is immutable and cannot be deleted.')


class DocumentCategory(UUIDModel, TimeStampedModel, AuditedModel):
    """Master document categories."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "document_categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class DocumentDefinition(UUIDModel, TimeStampedModel, AuditedModel):
    """Defines available document types."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="document_definitions",
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name="documents",
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "document_definitions"
        ordering = ["category", "name"]
        unique_together = ("organization", "category", "name")

    def __str__(self):
        return self.name


class DocumentPolicy(UUIDModel, TimeStampedModel, AuditedModel):
    """Document policy for an employee type."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="document_policies",
    )

    employee_type = models.ForeignKey(
        EmployeeType,
        on_delete=models.PROTECT,
        related_name="document_policies",
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "document_policies"
        ordering = ["name"]
        unique_together = ("organization", "employee_type", "name")

    def __str__(self):
        return self.name


class DocumentPolicyItem(UUIDModel, TimeStampedModel, AuditedModel):
    """Documents required under a policy."""

    policy = models.ForeignKey(
        DocumentPolicy,
        on_delete=models.CASCADE,
        related_name="items",
    )

    document = models.ForeignKey(
        DocumentDefinition,
        on_delete=models.PROTECT,
        related_name="policy_items",
    )

    display_order = models.PositiveIntegerField(default=0)

    is_required = models.BooleanField(default=True)
    allow_multiple = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=True)
    requires_expiry = models.BooleanField(default=False)

    class Meta:
        db_table = "document_policy_items"
        ordering = ["display_order", "id"]
        unique_together = ("policy", "document")

    def __str__(self):
        return f"{self.policy.name} - {self.document.name}"


class File(UUIDModel, TimeStampedModel, AuditedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="files",
    )
    file = models.FileField(upload_to="documents/%Y/%m/")
    original_name = models.CharField(max_length=255)
    extension = models.CharField(max_length=20)
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    checksum = models.CharField(
        max_length=64,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "files"

    def __str__(self):
        return self.original_name


class EmployeeDocument(UUIDModel, TimeStampedModel, AuditedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document = models.ForeignKey(
        DocumentDefinition,
        on_delete=models.PROTECT,
        related_name="employee_documents",
    )

    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name="employee_documents",
    )

    issue_date = models.DateField(
        null=True,
        blank=True,
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    remarks = models.TextField(blank=True)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_documents",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "employee_documents"
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee_id} · {self.document_id} · {self.status}'


class EmployeeTaxDetail(UUIDModel, TimeStampedModel, AuditedModel):
    """Employee tax information."""

    class TaxRegime(models.TextChoices):
        OLD = 'old', 'Old Regime'
        NEW = 'new', 'New Regime'

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='tax_detail',
    )

    pan_number = models.CharField(max_length=20, blank=True)
    aadhaar_number = models.CharField(max_length=20, blank=True)
    uan_number = models.CharField(max_length=30, blank=True)
    pf_number = models.CharField(max_length=50, blank=True)
    esi_number = models.CharField(max_length=50, blank=True)

    tax_regime = models.CharField(
        max_length=20,
        choices=TaxRegime.choices,
        default=TaxRegime.NEW,
    )

    tax_identification_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='TIN / SSN / National Tax ID based on country.',
    )

    is_pf_applicable = models.BooleanField(default=True)
    is_esi_applicable = models.BooleanField(default=False)
    professional_tax_applicable = models.BooleanField(default=False)
    labour_welfare_fund_applicable = models.BooleanField(default=False)

    class Meta:
        db_table = 'employee_tax_details'

    def __str__(self):
        return f'{self.employee_id} - Tax Details'


class AssetType(UUIDModel, TimeStampedModel, AuditedModel):
    """Master list of asset types."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="asset_types",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "asset_types"
        ordering = ["name"]
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class Asset(UUIDModel, TimeStampedModel, AuditedModel):
    """Physical or logical asset owned by an organization."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ASSIGNED = "assigned", "Assigned"
        LOST = "lost", "Lost"
        DAMAGED = "damaged", "Damaged"
        RETIRED = "retired", "Retired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="assets",
    )

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        related_name="assets",
    )

    asset_code = models.CharField(
        max_length=50,
        help_text="Unique organization asset code.",
    )

    name = models.CharField(
        max_length=150,
        help_text="Example: Dell Latitude 5440",
    )

    brand = models.CharField(
        max_length=100,
        blank=True,
    )

    model = models.CharField(
        max_length=100,
        blank=True,
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
    )

    purchase_date = models.DateField(
        null=True,
        blank=True,
    )

    warranty_expiry = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "assets"
        ordering = ["asset_code"]
        unique_together = (
            "organization",
            "asset_code",
        )

    def __str__(self):
        return self.asset_code


class EmployeeAssetAssignment(UUIDModel, TimeStampedModel, AuditedModel):
    """History of asset assignments."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RETURNED = "returned", "Returned"
        LOST = "lost", "Lost"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="asset_assignments",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="asset_assignments",
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="assignments",
    )

    assigned_at = models.DateField()

    expected_return_at = models.DateField(
        null=True,
        blank=True,
    )

    returned_at = models.DateField(
        null=True,
        blank=True,
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_assets",
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_assets",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    remarks = models.TextField(blank=True)

    class Meta:
        db_table = "employee_asset_assignments"
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["organization", "employee"]),
            models.Index(fields=["asset"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} -> {self.employee}"


class LeavePolicy(UUIDModel, TimeStampedModel, AuditedModel):
    """Leave policy assigned to an employee type."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leave_policies",
    )

    employee_type = models.ForeignKey(
        EmployeeType,
        on_delete=models.PROTECT,
        related_name="leave_policies",
    )

    code = models.CharField(
        max_length=30,
    )

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    is_default = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "leave_policies"
        ordering = ["name"]
        unique_together = (
            "organization",
            "code",
        )

    def __str__(self):
        return self.name


class LeavePolicyRule(UUIDModel, TimeStampedModel, AuditedModel):
    """Leave entitlement rule."""

    class AllocationFrequency(models.TextChoices):
        YEARLY = "yearly", "Yearly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"

    policy = models.ForeignKey(
        LeavePolicy,
        on_delete=models.CASCADE,
        related_name="rules",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="policy_rules",
    )

    allocation_frequency = models.CharField(
        max_length=20,
        choices=AllocationFrequency.choices,
        default=AllocationFrequency.YEARLY,
    )

    allocation_quantity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Quantity allocated every allocation frequency.",
    )

    annual_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Maximum leave that can be allocated in a leave year.",
    )

    carry_forward_allowed = models.BooleanField(
        default=False,
    )

    carry_forward_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    encashment_allowed = models.BooleanField(
        default=False,
    )

    encashment_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    allow_half_day = models.BooleanField(
        default=False,
    )

    allow_negative_balance = models.BooleanField(
        default=False,
    )

    minimum_service_days = models.PositiveIntegerField(
        default=0,
    )

    maximum_consecutive_days = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "leave_policy_rules"
        unique_together = (
            "policy",
            "leave_type",
        )

    def __str__(self):
        return f"{self.policy.name} - {self.leave_type.name}"


class EmployeeLeaveBalance(UUIDModel, TimeStampedModel, AuditedModel):
    """Stores current leave balance of an employee."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="employee_leave_balances",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_balances",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="employee_balances",
    )

    allocated = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    used = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    balance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    class Meta:
        db_table = "employee_leave_balances"
        unique_together = (
            "employee",
            "leave_type",
        )

    def __str__(self):
        return f"{self.employee} - {self.leave_type}"


class LeaveApplication(UUIDModel, TimeStampedModel, AuditedModel):
    """Employee leave request."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leave_applications",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_applications",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="applications",
    )

    from_date = models.DateField()

    to_date = models.DateField()

    number_of_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    is_half_day = models.BooleanField(
        default=False,
    )

    reason = models.TextField()

    attachment = models.FileField(
        upload_to="leave_attachments/",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "leave_applications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.leave_type}"


class EmployeeLeaveLog(UUIDModel, TimeStampedModel, AuditedModel):
    """Audit log for every leave balance change."""

    class TransactionType(models.TextChoices):
        ALLOCATION = "allocation", "Allocation"
        LEAVE_APPROVED = "leave_approved", "Leave Approved"
        LEAVE_CANCELLED = "leave_cancelled", "Leave Cancelled"
        ADJUSTMENT = "adjustment", "Adjustment"
        CARRY_FORWARD = "carry_forward", "Carry Forward"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leave_logs",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_logs",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="leave_logs",
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
    )

    quantity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    balance_before = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    balance_after = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    leave_application = models.ForeignKey(
        LeaveApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "employee_leave_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.transaction_type}"


class Attendance(UUIDModel, TimeStampedModel, AuditedModel):
    """Daily attendance summary."""

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        HALF_DAY = "half_day", "Half Day"
        LEAVE = "leave", "Leave"
        HOLIDAY = "holiday", "Holiday"
        WEEK_OFF = "week_off", "Week Off"

    class ApprovalStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not required"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="attendances",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendances",
    )

    attendance_date = models.DateField()

    first_check_in = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_check_out = models.DateTimeField(
        null=True,
        blank=True,
    )

    total_worked_hours = models.DurationField(
        null=True,
        blank=True,
    )

    total_break_hours = models.DurationField(
        null=True,
        blank=True,
    )

    overtime_hours = models.DurationField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    is_manual = models.BooleanField(
        default=False,
        help_text='True when this day includes a manual entry pending or reviewed by a manager.',
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_REQUIRED,
        db_index=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_attendances',
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approval_remarks = models.TextField(
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "attendances"
        ordering = ["-attendance_date"]
        unique_together = (
            "employee",
            "attendance_date",
        )

    def __str__(self):
        return f"{self.employee} - {self.attendance_date}"


class AttendanceSession(UUIDModel, TimeStampedModel, AuditedModel):
    """Each check-in/check-out session."""

    class Source(models.TextChoices):
        WEB = "web", "Web"
        MOBILE = "mobile", "Mobile"
        BIOMETRIC = "biometric", "Biometric"
        RFID = "rfid", "RFID"
        MANUAL = "manual", "Manual"
        API = "api", "API"

    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    check_in = models.DateTimeField()

    check_out = models.DateTimeField(
        null=True,
        blank=True,
    )

    worked_hours = models.DurationField(
        null=True,
        blank=True,
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WEB,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        db_table = "attendance_sessions"
        ordering = ["check_in"]

    def __str__(self):
        return (
            f"{self.attendance.employee} "
            f"- Session"
        )


class AttendanceBreak(UUIDModel, TimeStampedModel, AuditedModel):
    """Breaks taken during a session."""

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="breaks",
    )

    break_start = models.DateTimeField()

    break_end = models.DateTimeField(
        null=True,
        blank=True,
    )

    break_duration = models.DurationField(
        null=True,
        blank=True,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        db_table = "attendance_breaks"
        ordering = ["break_start"]

    def __str__(self):
        return (
            f"{self.session.attendance.employee} "
            f"- Break"
        )