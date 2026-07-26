# Generated manually — store profile photos as uploaded files.

import django.db.models.deletion
from django.db import migrations, models


def clear_external_photo_urls(apps, schema_editor):
    Employee = apps.get_model('organization', 'Employee')
    for employee in Employee.objects.exclude(profile_photo='').iterator():
        value = str(employee.profile_photo or '')
        if value.startswith('http://') or value.startswith('https://'):
            employee.profile_photo = ''
            employee.save(update_fields=['profile_photo'])


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0021_uniq_employee_email_per_organization'),
    ]

    operations = [
        migrations.RunPython(clear_external_photo_urls, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee',
            name='profile_photo',
            field=models.FileField(blank=True, upload_to='employee_photos/'),
        ),
    ]
