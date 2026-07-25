# Generated manually for OrganizationBranch + membership.branch

import uuid

import django.db.models.deletion
from django.db import migrations, models


def create_headquarters_and_assign_memberships(apps, schema_editor):
    Organization = apps.get_model('organization', 'Organization')
    OrganizationBranch = apps.get_model('organization', 'OrganizationBranch')
    OrganizationMembership = apps.get_model('organization', 'OrganizationMembership')

    for organization in Organization.objects.all():
        branch, _ = OrganizationBranch.objects.get_or_create(
            organization=organization,
            branch_code='HQ',
            defaults={
                'branch_name': f'{organization.display_name} Headquarters',
                'phone': organization.phone,
                'email': organization.email,
                'city': organization.city,
                'state': organization.state,
                'country': organization.country,
                'is_headquarters': True,
                'status': 'active',
            },
        )
        OrganizationMembership.objects.filter(
            organization=organization,
            branch__isnull=True,
        ).update(branch=branch)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_remove_userprofile_access_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationBranch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch_code', models.CharField(max_length=32)),
                ('branch_name', models.CharField(max_length=255)),
                ('phone', models.CharField(blank=True, max_length=32)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('address', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('is_headquarters', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], db_index=True, default='active', max_length=20)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branches', to='organization.organization')),
            ],
            options={
                'ordering': ['-is_headquarters', 'branch_name'],
            },
        ),
        migrations.AddField(
            model_name='organizationmembership',
            name='branch',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='memberships',
                to='organization.organizationbranch',
            ),
        ),
        migrations.RunPython(create_headquarters_and_assign_memberships, noop_reverse),
        migrations.AlterField(
            model_name='organizationmembership',
            name='branch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='memberships',
                to='organization.organizationbranch',
            ),
        ),
        migrations.AddIndex(
            model_name='organizationbranch',
            index=models.Index(fields=['organization', 'status'], name='organizatio_organiz_8e05b7_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationmembership',
            index=models.Index(fields=['branch', 'status'], name='organizatio_branch__2a1037_idx'),
        ),
        migrations.AddConstraint(
            model_name='organizationbranch',
            constraint=models.UniqueConstraint(fields=('organization', 'branch_code'), name='uniq_organization_branch_code'),
        ),
    ]
