# Generated manually — emergency contact fields on Employee.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0022_employee_profile_photo_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='emergency_contact_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='employee',
            name='emergency_contact_relationship',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='employee',
            name='emergency_contact_phone',
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
