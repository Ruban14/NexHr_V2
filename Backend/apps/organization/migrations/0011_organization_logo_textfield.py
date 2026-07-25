# Generated manually — store logos as text until object storage is adopted.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0010_department_and_designation_hierarchy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='logo',
            field=models.TextField(blank=True, default=''),
        ),
    ]
