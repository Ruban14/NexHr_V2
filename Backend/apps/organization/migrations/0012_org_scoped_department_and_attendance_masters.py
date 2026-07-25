# Org-scoped departments + Shift / WorkWeek / LeaveType / Holiday masters.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def migrate_departments_to_organization(apps, schema_editor):
    Department = apps.get_model('organization', 'Department')
    seen: dict[tuple[str, str], object] = {}
    for dept in Department.objects.select_related('organization_branch').all().order_by('created_at'):
        org_id = dept.organization_branch.organization_id
        key = (str(org_id), dept.name.strip().lower())
        if key in seen:
            # Keep unique names per org when collapsing branch-scoped duplicates.
            branch_code = dept.organization_branch.branch_code or str(dept.id)[:8]
            dept.name = f'{dept.name} ({branch_code})'
            key = (str(org_id), dept.name.strip().lower())
            counter = 2
            while key in seen:
                dept.name = f'{dept.name} ({counter})'
                key = (str(org_id), dept.name.strip().lower())
                counter += 1
        dept.organization_id = org_id
        dept.save(update_fields=['organization_id', 'name'])
        seen[key] = dept


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0011_organization_logo_textfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='departments',
                to='organization.organization',
            ),
        ),
        migrations.RunPython(migrate_departments_to_organization, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='department',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='departments',
                to='organization.organization',
            ),
        ),
        migrations.RemoveConstraint(
            model_name='department',
            name='uniq_department_name_per_branch',
        ),
        migrations.RemoveIndex(
            model_name='department',
            name='organizatio_organiz_dept_idx',
        ),
        migrations.RemoveField(
            model_name='department',
            name='organization_branch',
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['organization', 'is_active'], name='organizatio_organiz_dept_idx'),
        ),
        migrations.AddConstraint(
            model_name='department',
            constraint=models.UniqueConstraint(
                fields=('organization', 'name'),
                name='uniq_department_name_per_organization',
            ),
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts', to='organization.organization')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddConstraint(
            model_name='shift',
            constraint=models.UniqueConstraint(fields=('organization', 'name'), name='uniq_shift_name_per_org'),
        ),
        migrations.CreateModel(
            name='WorkWeek',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('working_days', models.JSONField(default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_weeks', to='organization.organization')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddConstraint(
            model_name='workweek',
            constraint=models.UniqueConstraint(fields=('organization', 'name'), name='uniq_workweek_name_per_org'),
        ),
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_types', to='organization.organization')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddConstraint(
            model_name='leavetype',
            constraint=models.UniqueConstraint(fields=('organization', 'name'), name='uniq_leave_type_per_org'),
        ),
        migrations.CreateModel(
            name='HolidayCalendar',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('year', models.PositiveIntegerField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holiday_calendars', to='organization.organization')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-year', 'name'],
            },
        ),
        migrations.AddConstraint(
            model_name='holidaycalendar',
            constraint=models.UniqueConstraint(
                fields=('organization', 'name', 'year'),
                name='uniq_holiday_calendar_per_org',
            ),
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('date', models.DateField()),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL)),
                ('holiday_calendar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holidays', to='organization.holidaycalendar')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.AddConstraint(
            model_name='holiday',
            constraint=models.UniqueConstraint(
                fields=('holiday_calendar', 'date'),
                name='uniq_holiday_date_per_calendar',
            ),
        ),
    ]
