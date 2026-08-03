# Generated manually for organization notice period days.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0032_remove_org_policies'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='notice_period_days',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Default notice period duration in days used to calculate exit date.',
            ),
        ),
    ]
