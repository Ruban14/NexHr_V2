# Generated manually for Department + Designation hierarchy alignment.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def clear_legacy_designations(apps, schema_editor):
    OrganizationMembership = apps.get_model('organization', 'OrganizationMembership')
    Designation = apps.get_model('organization', 'Designation')
    # Avoid CASCADE wiping memberships that still point at legacy designations.
    OrganizationMembership.objects.exclude(designation_id=None).update(designation_id=None)
    Designation.objects.all().delete()


class Migration(migrations.Migration):
    # Postgres cannot ALTER a table in the same transaction as prior DML trigger events.
    atomic = False

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0009_align_lookup_and_membership'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(db_index=True, max_length=150)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL)),
                ('organization_branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departments', to='organization.organizationbranch')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['organization_branch', 'is_active'], name='organizatio_organiz_dept_idx'),
        ),
        migrations.AddConstraint(
            model_name='department',
            constraint=models.UniqueConstraint(fields=('organization_branch', 'name'), name='uniq_department_name_per_branch'),
        ),
        migrations.RunPython(clear_legacy_designations, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='designation',
            name='industry_type',
        ),
        migrations.AddField(
            model_name='designation',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='designations', to='organization.department'),
        ),
        migrations.AddField(
            model_name='designation',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='organization.designation'),
        ),
        migrations.AddField(
            model_name='designation',
            name='sort_order',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterModelOptions(
            name='designation',
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.AddIndex(
            model_name='designation',
            index=models.Index(fields=['department', 'is_active'], name='organizatio_departm_desig_idx'),
        ),
        migrations.AddIndex(
            model_name='designation',
            index=models.Index(fields=['parent', 'sort_order'], name='organizatio_parent_sort_idx'),
        ),
        migrations.AddConstraint(
            model_name='designation',
            constraint=models.UniqueConstraint(fields=('department', 'name'), name='uniq_designation_per_department'),
        ),
    ]
