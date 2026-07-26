# Generated manually — indexes/constraints after profile merge

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0018_merge_userprofile_into_employee'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['user', 'is_active'], name='organizatio_user_id_aa377b_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(
                fields=['is_profile_completed', 'completed_status'],
                name='organizatio_is_prof_e45cd8_idx',
            ),
        ),
        migrations.AddConstraint(
            model_name='employee',
            constraint=models.UniqueConstraint(
                condition=models.Q(('user__isnull', False)),
                fields=('organization', 'user'),
                name='uniq_employee_user_per_organization',
            ),
        ),
    ]
