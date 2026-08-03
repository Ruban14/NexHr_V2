# Generated manually for attendance manual-entry approval workflow.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0039_attendance_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='approval_remarks',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='attendance',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('not_required', 'Not required'),
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                db_index=True,
                default='not_required',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='attendance',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendance',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_attendances',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='attendance',
            name='is_manual',
            field=models.BooleanField(
                default=False,
                help_text='True when this day includes a manual entry pending or reviewed by a manager.',
            ),
        ),
    ]
