# Generated manually — remove Invited from the default lifecycle path.

from django.db import migrations


def remove_invited_status(apps, schema_editor):
    Status = apps.get_model('organization', 'EmployeeLifecycleStatus')
    Transition = apps.get_model('organization', 'EmployeeLifecycleTransition')
    Employee = apps.get_model('organization', 'Employee')
    History = apps.get_model('organization', 'EmployeeLifecycleHistory')

    invited = Status.objects.filter(key='invited').first()
    if invited is None:
        return

    draft = Status.objects.filter(key='draft').first()
    onboarding = Status.objects.filter(key='onboarding_started').first()
    rehire = Status.objects.filter(key='rehire').first()

    if draft is not None:
        Employee.objects.filter(lifecycle_status=invited).update(lifecycle_status=draft)

    # QuerySet.delete bypasses EmployeeLifecycleHistory.delete() immutability guard.
    History.objects.filter(from_status=invited).delete()
    History.objects.filter(to_status=invited).delete()

    Transition.objects.filter(from_status=invited).delete()
    Transition.objects.filter(to_status=invited).delete()

    if draft is not None and onboarding is not None:
        Transition.objects.get_or_create(
            from_status=draft,
            to_status=onboarding,
            defaults={
                'action_label': 'Start Onboarding',
                'sort_order': 10,
                'is_active': True,
            },
        )

    if rehire is not None and onboarding is not None:
        Transition.objects.get_or_create(
            from_status=rehire,
            to_status=onboarding,
            defaults={
                'action_label': 'Start Onboarding',
                'sort_order': 10,
                'is_active': True,
            },
        )

    ordinal_map = {
        'draft': 10,
        'onboarding_started': 20,
        'active': 30,
        'notice_period': 40,
        'released': 50,
        'rehire': 60,
    }
    for key, ordinal in ordinal_map.items():
        Status.objects.filter(key=key).update(ordinal=ordinal)

    invited.delete()


def restore_invited_status(apps, schema_editor):
    Status = apps.get_model('organization', 'EmployeeLifecycleStatus')
    Transition = apps.get_model('organization', 'EmployeeLifecycleTransition')

    if Status.objects.filter(key='invited').exists():
        return

    invited = Status.objects.create(
        name='Invited',
        key='invited',
        ordinal=20,
        is_initial=False,
        is_terminal=False,
        is_active=True,
    )
    Status.objects.filter(key='onboarding_started').update(ordinal=30)
    Status.objects.filter(key='active').update(ordinal=40)
    Status.objects.filter(key='notice_period').update(ordinal=50)
    Status.objects.filter(key='released').update(ordinal=60)
    Status.objects.filter(key='rehire').update(ordinal=70)

    draft = Status.objects.filter(key='draft').first()
    onboarding = Status.objects.filter(key='onboarding_started').first()
    rehire = Status.objects.filter(key='rehire').first()

    if draft and onboarding:
        Transition.objects.filter(from_status=draft, to_status=onboarding).delete()
        Transition.objects.get_or_create(
            from_status=draft,
            to_status=invited,
            defaults={'action_label': 'Invite', 'sort_order': 10, 'is_active': True},
        )
        Transition.objects.get_or_create(
            from_status=invited,
            to_status=onboarding,
            defaults={'action_label': 'Start Onboarding', 'sort_order': 10, 'is_active': True},
        )

    if rehire and onboarding:
        Transition.objects.filter(from_status=rehire, to_status=onboarding).delete()
        Transition.objects.get_or_create(
            from_status=rehire,
            to_status=invited,
            defaults={'action_label': 'Send Invitation', 'sort_order': 10, 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0019_employee_profile_indexes'),
    ]

    operations = [
        migrations.RunPython(remove_invited_status, restore_invited_status),
    ]
