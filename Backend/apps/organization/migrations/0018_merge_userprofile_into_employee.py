# Generated manually for merging UserProfile into Employee (schema + data)

from django.conf import settings
from django.db import migrations, models


PROFILE_FIELDS = (
    'display_name',
    'profile_photo',
    'mobile_number',
    'alternate_mobile',
    'date_of_birth',
    'gender',
    'blood_group',
    'country',
    'state',
    'city',
    'address_line1',
    'postal_code',
    'mother_language',
    'languages_known',
    'is_profile_completed',
    'completed_status',
)


def _apply_profile(employee, profile):
    for field in PROFILE_FIELDS:
        value = getattr(profile, field)
        if field == 'languages_known':
            employee.languages_known = value if isinstance(value, list) else []
            continue
        if field == 'date_of_birth':
            employee.date_of_birth = value or None
            continue
        if field == 'is_profile_completed':
            employee.is_profile_completed = bool(value)
            continue
        current = getattr(employee, field, '') or ''
        if not value and current:
            continue
        setattr(employee, field, value or '')


def merge_userprofiles_into_employees(apps, schema_editor):
    UserProfile = apps.get_model('organization', 'UserProfile')
    Employee = apps.get_model('organization', 'Employee')
    OrganizationMembership = apps.get_model('organization', 'OrganizationMembership')
    EmployeeLifecycleStatus = apps.get_model('organization', 'EmployeeLifecycleStatus')
    User = apps.get_model(settings.AUTH_USER_MODEL)

    lifecycle = (
        EmployeeLifecycleStatus.objects.filter(key='active', is_active=True).first()
        or EmployeeLifecycleStatus.objects.filter(is_initial=True, is_active=True).order_by('ordinal').first()
        or EmployeeLifecycleStatus.objects.filter(is_active=True).order_by('ordinal').first()
    )
    if lifecycle is None:
        return

    profiles_by_user = {p.user_id: p for p in UserProfile.objects.all()}
    seen = set()

    for membership in OrganizationMembership.objects.select_related('branch').iterator():
        org_id = membership.branch.organization_id
        key = (org_id, membership.user_id)
        if key in seen:
            continue
        seen.add(key)

        employee = Employee.objects.filter(organization_id=org_id, user_id=membership.user_id).first()
        user = User.objects.filter(id=membership.user_id).first()
        profile = profiles_by_user.get(membership.user_id)

        if employee is None:
            employee = Employee(
                organization_id=org_id,
                branch_id=membership.branch_id,
                user_id=membership.user_id,
                lifecycle_status=lifecycle,
                employee_code=membership.employee_code or '',
                email=(user.email if user else '') or '',
                first_name=(user.first_name if user else '') or '',
                last_name=(user.last_name if user else '') or '',
                designation_id=membership.designation_id,
                employee_type_id=membership.employee_type_id,
                access_type_id=membership.access_type_id,
                joining_date=membership.joining_date or None,
                exit_date=membership.exit_date or None,
                is_active=membership.status == 'active',
                created_by_id=membership.created_by_id,
                updated_by_id=membership.updated_by_id,
            )

        if profile is not None:
            _apply_profile(employee, profile)
            if profile.created_by_id and not employee.created_by_id:
                employee.created_by_id = profile.created_by_id
            if profile.updated_by_id:
                employee.updated_by_id = profile.updated_by_id

        if not employee.display_name:
            employee.display_name = (
                ((f'{user.first_name} {user.last_name}').strip() if user else '')
                or (user.email.split('@')[0] if user and user.email else '')
                or 'Employee'
            )
        if user and not employee.email:
            employee.email = user.email or ''
        if user and not employee.first_name:
            employee.first_name = user.first_name or ''
        if user and not employee.last_name:
            employee.last_name = user.last_name or ''
        if not employee.employee_code and membership.employee_code:
            employee.employee_code = membership.employee_code
        if employee.branch_id is None:
            employee.branch_id = membership.branch_id

        employee.save()

    for profile in UserProfile.objects.all().iterator():
        for employee in Employee.objects.filter(user_id=profile.user_id):
            _apply_profile(employee, profile)
            employee.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0017_history_changed_by_set_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='address_line1',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='employee',
            name='alternate_mobile',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='employee',
            name='blood_group',
            field=models.CharField(
                blank=True,
                choices=[
                    ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                    ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
                    ('unknown', 'Unknown'),
                ],
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='employee',
            name='completed_status',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='employee',
            name='country',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='employee',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[
                    ('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other'),
                    ('prefer_not_to_say', 'Prefer not to say'),
                ],
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='is_profile_completed',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='employee',
            name='languages_known',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='employee',
            name='mobile_number',
            field=models.CharField(blank=True, db_index=True, max_length=32),
        ),
        migrations.AddField(
            model_name='employee',
            name='mother_language',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='employee',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='employee',
            name='profile_photo',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='state',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.RunPython(merge_userprofiles_into_employees, noop_reverse),
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]
