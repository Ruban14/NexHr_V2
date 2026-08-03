# Generated manually for reporting manager leave approval.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0037_employee_leave_runtime'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='reporting_manager',
            field=models.ForeignKey(
                blank=True,
                help_text='Manager who approves leave and similar requests for this employee.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='direct_reports',
                to='organization.employee',
            ),
        ),
    ]
