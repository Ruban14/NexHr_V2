# Generated manually — enforce unique employee email per organization.

from django.db import migrations, models


def clear_duplicate_emails(apps, schema_editor):
    Employee = apps.get_model('organization', 'Employee')
    seen = {}
    duplicates = (
        Employee.objects.exclude(email='')
        .order_by('organization_id', 'email', 'created_at', 'id')
    )
    for employee in duplicates.iterator():
        key = (str(employee.organization_id), employee.email.strip().lower())
        if key in seen:
            employee.email = ''
            employee.save(update_fields=['email'])
        else:
            seen[key] = employee.id
            normalized = employee.email.strip().lower()
            if employee.email != normalized:
                employee.email = normalized
                employee.save(update_fields=['email'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0020_remove_invited_lifecycle_status'),
    ]

    operations = [
        migrations.RunPython(clear_duplicate_emails, noop_reverse),
        migrations.AddConstraint(
            model_name='employee',
            constraint=models.UniqueConstraint(
                condition=~models.Q(email=''),
                fields=('organization', 'email'),
                name='uniq_employee_email_per_organization',
            ),
        ),
    ]
