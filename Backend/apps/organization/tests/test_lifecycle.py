"""Tests for the database-driven employee lifecycle engine."""

from __future__ import annotations

from django.test import TestCase

from apps.authentication.models import User
from apps.core.exceptions import ValidationServiceError
from apps.organization.models import (
    Employee,
    EmployeeLifecycleHistory,
    EmployeeLifecycleStatus,
    EmployeeLifecycleTransition,
    IndustryType,
    Organization,
    OrganizationBranch,
)
from apps.organization.services.lifecycle import EmployeeLifecycleEngine


class EmployeeLifecycleEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='Passw0rd!',
            first_name='Org',
            last_name='Owner',
        )
        self.user.is_email_verified = True
        self.user.save(update_fields=['is_email_verified'])
        industry = IndustryType.objects.create(name='IT', is_active=True)
        self.organization = Organization.objects.create(
            organization_code='ORG001',
            legal_name='Acme Ltd',
            display_name='Acme',
            industry_type=industry,
            owner=self.user,
        )
        self.branch = OrganizationBranch.objects.create(
            organization=self.organization,
            branch_code='HQ',
            branch_name='Headquarters',
            is_headquarters=True,
        )
        # Use seeded statuses from migration when present; otherwise create locally.
        self.statuses = {
            item.key: item for item in EmployeeLifecycleStatus.objects.filter(is_active=True)
        }
        if not self.statuses:
            self._seed_statuses()

    def _seed_statuses(self):
        defs = [
            ('Draft', 'draft', 10, True),
            ('Onboarding Started', 'onboarding_started', 20, False),
            ('Active Employee', 'active', 30, False),
            ('Notice Period', 'notice_period', 40, False),
            ('Released', 'released', 50, False),
            ('Rehire', 'rehire', 60, False),
        ]
        for name, key, ordinal, is_initial in defs:
            self.statuses[key] = EmployeeLifecycleStatus.objects.create(
                name=name,
                key=key,
                ordinal=ordinal,
                is_initial=is_initial,
                is_active=True,
            )
        edges = [
            ('draft', 'onboarding_started', 'Start Onboarding'),
            ('onboarding_started', 'active', 'Activate'),
            ('active', 'notice_period', 'Start Notice'),
            ('notice_period', 'released', 'Release'),
            ('released', 'rehire', 'Rehire'),
            ('rehire', 'onboarding_started', 'Start Onboarding'),
        ]
        for from_key, to_key, label in edges:
            EmployeeLifecycleTransition.objects.create(
                from_status=self.statuses[from_key],
                to_status=self.statuses[to_key],
                action_label=label,
                is_active=True,
            )

    def _employee(self, status_key='draft'):
        return Employee.objects.create(
            organization=self.organization,
            branch=self.branch,
            lifecycle_status=self.statuses[status_key],
            display_name='Alex Employee',
            email='alex@example.com',
            created_by=self.user,
            updated_by=self.user,
        )

    def test_initial_status_comes_from_database(self):
        initial = EmployeeLifecycleEngine.get_initial_status()
        self.assertTrue(initial.is_initial)
        self.assertEqual(initial.key, 'draft')

    def test_allowed_transition_succeeds_and_writes_history(self):
        employee = self._employee('draft')
        EmployeeLifecycleEngine.apply_transition(
            employee=employee,
            to_status=self.statuses['onboarding_started'],
            changed_by=self.user,
            remarks='Onboarding kicked off',
        )
        employee.refresh_from_db()
        self.assertEqual(employee.lifecycle_status.key, 'onboarding_started')
        history = EmployeeLifecycleHistory.objects.filter(employee=employee)
        self.assertEqual(history.count(), 1)
        row = history.first()
        self.assertEqual(row.from_status.key, 'draft')
        self.assertEqual(row.to_status.key, 'onboarding_started')
        self.assertEqual(row.remarks, 'Onboarding kicked off')

    def test_disallowed_transition_is_rejected(self):
        employee = self._employee('draft')
        with self.assertRaises(ValidationServiceError) as ctx:
            EmployeeLifecycleEngine.apply_transition(
                employee=employee,
                to_status=self.statuses['active'],
                changed_by=self.user,
            )
        self.assertEqual(ctx.exception.code, 'lifecycle_transition_not_allowed')
        employee.refresh_from_db()
        self.assertEqual(employee.lifecycle_status.key, 'draft')
        self.assertEqual(EmployeeLifecycleHistory.objects.filter(employee=employee).count(), 0)

    def test_released_to_onboarding_is_rejected_but_rehire_is_allowed(self):
        employee = self._employee('released')
        self.assertFalse(
            EmployeeLifecycleEngine.can_transition(
                from_status=employee.lifecycle_status,
                to_status=self.statuses['onboarding_started'],
            )
        )
        self.assertTrue(
            EmployeeLifecycleEngine.can_transition(
                from_status=employee.lifecycle_status,
                to_status=self.statuses['rehire'],
            )
        )
        EmployeeLifecycleEngine.apply_transition(
            employee=employee,
            to_status=self.statuses['rehire'],
            changed_by=self.user,
        )
        employee.refresh_from_db()
        self.assertEqual(employee.lifecycle_status.key, 'rehire')

    def test_available_actions_come_from_transitions_table(self):
        employee = self._employee('active')
        actions = EmployeeLifecycleEngine.get_available_transitions(
            from_status=employee.lifecycle_status,
        )
        labels = [item.action_label for item in actions]
        to_keys = [item.to_status.key for item in actions]
        self.assertEqual(labels, ['Start Notice'])
        self.assertEqual(to_keys, ['notice_period'])

    def test_history_cannot_be_deleted(self):
        employee = self._employee('draft')
        EmployeeLifecycleEngine.apply_transition(
            employee=employee,
            to_status=self.statuses['onboarding_started'],
            changed_by=self.user,
        )
        row = EmployeeLifecycleHistory.objects.get(employee=employee)
        with self.assertRaises(PermissionError):
            row.delete()
