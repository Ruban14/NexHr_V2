"""Organization asset inventory and employee assignment lifecycle."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.authentication.models import User
from apps.core.exceptions import (
    ConflictServiceError,
    NotFoundServiceError,
    PermissionDeniedServiceError,
    ValidationServiceError,
)
from apps.organizations.models import (
    OrganizationMembership,
)
from apps.people.models import (
    Employee,
)
from apps.assets.models import (
    Asset,
    AssetType,
    EmployeeAssetAssignment,
)
from apps.organizations.services.workspace_service import WorkspaceService


class AssetAssignmentService:
    """Employee asset assignment lifecycle."""

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        from apps.assets.services.asset_service import AssetService

        return AssetService.require_admin(user, branch_id)

    @classmethod
    def _organization(cls, membership: OrganizationMembership):
        from apps.assets.services.asset_service import AssetService

        return AssetService._organization(membership)

    @classmethod
    def _get_employee(cls, *, organization, employee_id: str | UUID) -> Employee:
        from apps.assets.services.asset_service import AssetService

        return AssetService._get_employee(organization=organization, employee_id=employee_id)

    @classmethod
    def serialize_asset(cls, item: Asset) -> dict:
        from apps.assets.services.asset_service import AssetService

        return AssetService.serialize_asset(item)

    # ── Assignments ─────────────────────────────────────────────────────────

    @classmethod
    def list_employee_assignments(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
    ) -> list[dict]:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        rows = (
            EmployeeAssetAssignment.objects.select_related('asset', 'asset__asset_type', 'issued_by', 'received_by')
            .filter(organization=organization, employee=employee)
            .order_by('-assigned_at', '-created_at')
        )
        return [cls.serialize_assignment(row) for row in rows]

    @classmethod
    def list_available_assets(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
    ) -> list[dict]:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        qs = Asset.objects.filter(
            organization=organization,
            is_active=True,
            status=Asset.Status.AVAILABLE,
        ).select_related('asset_type')
        if search:
            term = search.strip()
            qs = qs.filter(
                Q(asset_code__icontains=term)
                | Q(name__icontains=term)
                | Q(serial_number__icontains=term)
            )
        return [cls.serialize_asset(item) for item in qs.order_by('asset_code')[:100]]

    @classmethod
    @transaction.atomic
    def assign_asset(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        asset_id: str | UUID,
        assigned_at: date | None = None,
        expected_return_at: date | None = None,
        remarks: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        asset = (
            Asset.objects.select_related('asset_type')
            .filter(id=asset_id, organization=organization, is_active=True)
            .first()
        )
        if asset is None:
            raise NotFoundServiceError('Asset not found.', code='asset_not_found')
        if asset.status != Asset.Status.AVAILABLE:
            raise ValidationServiceError(
                'Only available assets can be assigned.',
                code='asset_not_available',
            )
        if asset.assignments.filter(status=EmployeeAssetAssignment.Status.ACTIVE).exists():
            raise ConflictServiceError(
                'This asset already has an active assignment.',
                code='asset_already_assigned',
            )

        assigned = assigned_at or timezone.localdate()
        row = EmployeeAssetAssignment.objects.create(
            organization=organization,
            employee=employee,
            asset=asset,
            assigned_at=assigned,
            expected_return_at=expected_return_at,
            issued_by=user,
            status=EmployeeAssetAssignment.Status.ACTIVE,
            remarks=(remarks or '').strip(),
            created_by=user,
            updated_by=user,
        )
        asset.status = Asset.Status.ASSIGNED
        asset.updated_by = user
        asset.save(update_fields=['status', 'updated_by', 'updated_at'])
        return cls.serialize_assignment(row)

    @classmethod
    @transaction.atomic
    def revoke_assignment(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        assignment_id: str | UUID,
        returned_at: date | None = None,
        remarks: str = '',
        mark_lost: bool = False,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        row = (
            EmployeeAssetAssignment.objects.select_related('asset', 'asset__asset_type')
            .filter(id=assignment_id, organization=organization, employee=employee)
            .first()
        )
        if row is None:
            raise NotFoundServiceError('Assignment not found.', code='assignment_not_found')
        if row.status != EmployeeAssetAssignment.Status.ACTIVE:
            raise ValidationServiceError(
                'Only active assignments can be revoked.',
                code='assignment_not_active',
            )

        returned = returned_at or timezone.localdate()
        row.returned_at = returned
        row.received_by = user
        row.status = (
            EmployeeAssetAssignment.Status.LOST
            if mark_lost
            else EmployeeAssetAssignment.Status.RETURNED
        )
        if remarks:
            row.remarks = (row.remarks + '\n' if row.remarks else '') + remarks.strip()
        row.updated_by = user
        row.save()

        asset = row.asset
        asset.status = Asset.Status.LOST if mark_lost else Asset.Status.AVAILABLE
        asset.updated_by = user
        asset.save(update_fields=['status', 'updated_by', 'updated_at'])
        return cls.serialize_assignment(row)


    @classmethod
    def serialize_assignment(cls, row: EmployeeAssetAssignment) -> dict:
        asset = row.asset
        return {
            'id': str(row.id),
            'organization_id': str(row.organization_id),
            'employee_id': str(row.employee_id),
            'asset_id': str(row.asset_id),
            'asset_code': asset.asset_code if asset else None,
            'asset_name': asset.name if asset else None,
            'asset_type_name': asset.asset_type.name if asset and asset.asset_type_id else None,
            'serial_number': asset.serial_number if asset else None,
            'assigned_at': row.assigned_at.isoformat() if row.assigned_at else None,
            'expected_return_at': (
                row.expected_return_at.isoformat() if row.expected_return_at else None
            ),
            'returned_at': row.returned_at.isoformat() if row.returned_at else None,
            'issued_by_id': str(row.issued_by_id) if row.issued_by_id else None,
            'issued_by_name': (
                row.issued_by.full_name or row.issued_by.email if row.issued_by else None
            ),
            'received_by_id': str(row.received_by_id) if row.received_by_id else None,
            'received_by_name': (
                row.received_by.full_name or row.received_by.email if row.received_by else None
            ),
            'status': row.status,
            'remarks': row.remarks,
            'created_at': row.created_at.isoformat(),
            'updated_at': row.updated_at.isoformat(),
        }

