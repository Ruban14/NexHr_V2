# Generated manually for attendance daily summary, sessions, and breaks.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0038_employee_reporting_manager'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attendance_date', models.DateField()),
                ('first_check_in', models.DateTimeField(blank=True, null=True)),
                ('last_check_out', models.DateTimeField(blank=True, null=True)),
                ('total_worked_hours', models.DurationField(blank=True, null=True)),
                ('total_break_hours', models.DurationField(blank=True, null=True)),
                ('overtime_hours', models.DurationField(blank=True, null=True)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('present', 'Present'),
                            ('absent', 'Absent'),
                            ('half_day', 'Half Day'),
                            ('leave', 'Leave'),
                            ('holiday', 'Holiday'),
                            ('week_off', 'Week Off'),
                        ],
                        default='present',
                        max_length=20,
                    ),
                ),
                ('remarks', models.TextField(blank=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='created_%(class)ss',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'employee',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attendances',
                        to='organization.employee',
                    ),
                ),
                (
                    'organization',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attendances',
                        to='organization.organization',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='updated_%(class)ss',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'attendances',
                'ordering': ['-attendance_date'],
                'unique_together': {('employee', 'attendance_date')},
            },
        ),
        migrations.CreateModel(
            name='AttendanceSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('check_in', models.DateTimeField()),
                ('check_out', models.DateTimeField(blank=True, null=True)),
                ('worked_hours', models.DurationField(blank=True, null=True)),
                (
                    'source',
                    models.CharField(
                        choices=[
                            ('web', 'Web'),
                            ('mobile', 'Mobile'),
                            ('biometric', 'Biometric'),
                            ('rfid', 'RFID'),
                            ('manual', 'Manual'),
                            ('api', 'API'),
                        ],
                        default='web',
                        max_length=20,
                    ),
                ),
                ('remarks', models.CharField(blank=True, max_length=255)),
                (
                    'attendance',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='sessions',
                        to='organization.attendance',
                    ),
                ),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='created_%(class)ss',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='updated_%(class)ss',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'attendance_sessions',
                'ordering': ['check_in'],
            },
        ),
        migrations.CreateModel(
            name='AttendanceBreak',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('break_start', models.DateTimeField()),
                ('break_end', models.DateTimeField(blank=True, null=True)),
                ('break_duration', models.DurationField(blank=True, null=True)),
                ('remarks', models.CharField(blank=True, max_length=255)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='created_%(class)ss',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'session',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='breaks',
                        to='organization.attendancesession',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='updated_%(class)ss',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'attendance_breaks',
                'ordering': ['break_start'],
            },
        ),
    ]
