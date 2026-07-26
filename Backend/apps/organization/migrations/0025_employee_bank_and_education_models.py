# Move flat Employee bank columns onto EmployeeBankDetail; add EmployeeEducation.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_bank_details_forward(apps, schema_editor):
    Employee = apps.get_model('organization', 'Employee')
    EmployeeBankDetail = apps.get_model('organization', 'EmployeeBankDetail')
    for employee in Employee.objects.all().iterator():
        holder = (employee.bank_account_holder_name or '').strip()
        bank = (employee.bank_name or '').strip()
        number = (employee.bank_account_number or '').strip()
        ifsc = (employee.bank_ifsc_code or '').strip()
        if not any([holder, bank, number, ifsc]):
            continue
        EmployeeBankDetail.objects.create(
            employee=employee,
            account_holder_name=holder,
            bank_name=bank,
            account_number=number,
            ifsc_code=ifsc,
            is_primary=True,
            created_by_id=employee.updated_by_id or employee.created_by_id,
            updated_by_id=employee.updated_by_id or employee.created_by_id,
        )


def copy_bank_details_backward(apps, schema_editor):
    Employee = apps.get_model('organization', 'Employee')
    EmployeeBankDetail = apps.get_model('organization', 'EmployeeBankDetail')
    for detail in EmployeeBankDetail.objects.filter(is_primary=True).select_related('employee'):
        employee = detail.employee
        employee.bank_account_holder_name = detail.account_holder_name or ''
        employee.bank_name = detail.bank_name or ''
        employee.bank_account_number = detail.account_number or ''
        employee.bank_ifsc_code = detail.ifsc_code or ''
        employee.save(
            update_fields=[
                'bank_account_holder_name',
                'bank_name',
                'bank_account_number',
                'bank_ifsc_code',
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0024_employee_bank_details'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeBankDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_holder_name', models.CharField(blank=True, max_length=150)),
                ('bank_name', models.CharField(blank=True, max_length=150)),
                ('account_number', models.CharField(blank=True, max_length=64)),
                ('ifsc_code', models.CharField(blank=True, max_length=20)),
                ('is_primary', models.BooleanField(db_index=True, default=False)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='created_employeebankdetails',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'employee',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='bank_details',
                        to='organization.employee',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='updated_employeebankdetails',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-is_primary', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='EmployeeEducation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('degree', models.CharField(blank=True, max_length=150)),
                ('institution', models.CharField(blank=True, max_length=255)),
                ('field_of_study', models.CharField(blank=True, max_length=150)),
                ('year_of_passing', models.PositiveIntegerField(blank=True, null=True)),
                ('grade', models.CharField(blank=True, max_length=64)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='created_employeeeducations',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'employee',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='education_details',
                        to='organization.employee',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='updated_employeeeducations',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-year_of_passing', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='employeebankdetail',
            index=models.Index(fields=['employee', 'is_primary'], name='org_emp_bank_primary_idx'),
        ),
        migrations.AddConstraint(
            model_name='employeebankdetail',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_primary', True)),
                fields=('employee',),
                name='uniq_primary_bank_per_employee',
            ),
        ),
        migrations.AddIndex(
            model_name='employeeeducation',
            index=models.Index(fields=['employee', 'year_of_passing'], name='org_emp_edu_year_idx'),
        ),
        migrations.RunPython(copy_bank_details_forward, copy_bank_details_backward),
        migrations.RemoveField(
            model_name='employee',
            name='bank_account_holder_name',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='bank_account_number',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='bank_ifsc_code',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='bank_name',
        ),
    ]
