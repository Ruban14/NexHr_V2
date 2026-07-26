# Generated manually — salary bank details on Employee.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0023_employee_emergency_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='bank_account_holder_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='employee',
            name='bank_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='employee',
            name='bank_account_number',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='employee',
            name='bank_ifsc_code',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
