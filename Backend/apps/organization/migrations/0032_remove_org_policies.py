# Generated manually to remove org policy acknowledgement models.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0031_org_policies'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PolicyAcknowledgement',
        ),
        migrations.DeleteModel(
            name='Policy',
        ),
    ]
