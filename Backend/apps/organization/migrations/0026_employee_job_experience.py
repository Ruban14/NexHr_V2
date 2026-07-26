# Generated manually for EmployeeJobExperience.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0025_employee_bank_and_education_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeJobExperience',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company_name', models.CharField(blank=True, max_length=255)),
                ('job_title', models.CharField(blank=True, max_length=150)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('is_current', models.BooleanField(db_index=True, default=False)),
                ('location', models.CharField(blank=True, max_length=150)),
                ('description', models.TextField(blank=True, default='')),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='created_employeejobexperiences',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'employee',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='job_experiences',
                        to='organization.employee',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='updated_employeejobexperiences',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Employee job experience',
                'verbose_name_plural': 'Employee job experiences',
                'ordering': ['-is_current', '-start_date', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='employeejobexperience',
            index=models.Index(fields=['employee', 'start_date'], name='org_emp_job_exp_start_idx'),
        ),
    ]
