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
        on_delete=models.SET_NULL,
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

class UserProfile(UUIDModel, TimeStampedModel, AuditedModel):
    """Extended profile details for an authenticated user."""

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

    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='profile')
    display_name = models.CharField(max_length=255, blank=True)
    profile_photo = models.URLField(blank=True)
    mobile_number = models.CharField(max_length=32, blank=True, db_index=True)
    alternate_mobile = models.CharField(max_length=32, blank=True)

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

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_profile_completed', 'completed_status']),
        ]

    def __str__(self) -> str:
        return self.display_name or str(self.user)


class OrganizationMembership(UUIDModel, TimeStampedModel, AuditedModel):
    """Links a user profile to an organization branch with role and employment details."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        PENDING = 'pending', 'Pending'
        EXITED = 'exited', 'Exited'

    branch = models.ForeignKey(OrganizationBranch,on_delete=models.CASCADE,related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='memberships')
    designation = models.ForeignKey(Designation,on_delete=models.CASCADE,null=True,blank=True,related_name='memberships')
    employee_type = models.ForeignKey(EmployeeType,on_delete=models.CASCADE,null=True,blank=True,related_name='memberships')
    access_type = models.ForeignKey(AccessType,on_delete=models.CASCADE,null=True,blank=True,related_name='memberships')
    employee_code = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=32,choices=Status.choices,default=Status.ACTIVE,db_index=True)
    joining_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['branch', 'user'],
                name='uniq_org_membership_branch_user',
            ),
            models.UniqueConstraint(fields=['branch', 'employee_code'],
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