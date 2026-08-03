from django.db import migrations


DEFAULT_CATEGORIES = [
    ('Identity Proof', 'Government-issued identity documents', 10),
    ('Address Proof', 'Residential address verification documents', 20),
    ('Education', 'Academic certificates and transcripts', 30),
    ('Employment', 'Previous employment and experience proofs', 40),
    ('Compliance', 'Statutory and regulatory compliance documents', 50),
    ('Medical', 'Medical and fitness certificates', 60),
    ('Other', 'Miscellaneous documents', 100),
]


def seed_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('organization', 'DocumentCategory')
    for name, description, display_order in DEFAULT_CATEGORIES:
        DocumentCategory.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'display_order': display_order,
                'is_active': True,
            },
        )


def unseed_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('organization', 'DocumentCategory')
    DocumentCategory.objects.filter(name__in=[name for name, _, _ in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0027_document_policy_models'),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
