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
from apps.organization.services.workspace import WorkspaceService


class AssetService:
    """CRUD for asset types, assets, and employee assignments."""

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        if not is_owner and access_name not in {'admin', 'administrator'}:
            raise PermissionDeniedServiceError(
                'Only organization admins can manage assets.',
                code='not_organization_admin',
            )
        return membership

    @classmethod
    def _organization(cls, membership: OrganizationMembership):
        return membership.branch.organization

    @classmethod
    def _paginate(cls, qs, *, page: int, page_size: int, serialize) -> dict:
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 20)))
        total = qs.count()
        start = (page - 1) * page_size
        items = list(qs[start : start + page_size])
        return {
            'items': [serialize(item) for item in items],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': max(1, (total + page_size - 1) // page_size),
            },
        }

    @classmethod
    def _get_employee(cls, *, organization, employee_id: str | UUID) -> Employee:
        employee = Employee.objects.filter(id=employee_id, organization=organization).first()
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')
        return employee

    # ── Asset types ─────────────────────────────────────────────────────────

    @classmethod
    def list_asset_types(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        is_active: bool | None = True,
    ) -> list[dict]:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        qs = AssetType.objects.filter(organization=organization)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return [cls.serialize_asset_type(item) for item in qs.order_by('name')]

    @classmethod
    @transaction.atomic
    def create_asset_type(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        description: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = (name or '').strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Asset type name must be at least 2 characters.', code='invalid_name')
        if AssetType.objects.filter(organization=organization, name__iexact=cleaned).exists():
            raise ConflictServiceError('An asset type with this name already exists.', code='asset_type_exists')
        item = AssetType.objects.create(
            organization=organization,
            name=cleaned,
            description=(description or '').strip(),
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_asset_type(item)

    @classmethod
    @transaction.atomic
    def update_asset_type(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = AssetType.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Asset type not found.', code='asset_type_not_found')
        if 'name' in payload:
            cleaned = (payload.get('name') or '').strip()
            if len(cleaned) < 2:
                raise ValidationServiceError(
                    'Asset type name must be at least 2 characters.',
                    code='invalid_name',
                )
            if (
                AssetType.objects.filter(organization=organization, name__iexact=cleaned)
                .exclude(id=item.id)
                .exists()
            ):
                raise ConflictServiceError(
                    'An asset type with this name already exists.',
                    code='asset_type_exists',
                )
            item.name = cleaned
        if 'description' in payload:
            item.description = (payload.get('description') or '').strip()
        if 'is_active' in payload:
            item.is_active = bool(payload.get('is_active'))
        item.updated_by = user
        item.save()
        return cls.serialize_asset_type(item)

    @classmethod
    @transaction.atomic
    def delete_asset_type(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
    ) -> None:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = AssetType.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Asset type not found.', code='asset_type_not_found')
        if item.assets.exists():
            raise ValidationServiceError(
                'Cannot delete an asset type that still has assets.',
                code='asset_type_in_use',
            )
        item.delete()

    # ── Assets ──────────────────────────────────────────────────────────────

    @classmethod
    def list_assets(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        asset_type_id: str | UUID | None = None,
        status: str | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        qs = Asset.objects.filter(organization=organization).select_related('asset_type')
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if asset_type_id:
            qs = qs.filter(asset_type_id=asset_type_id)
        if status:
            qs = qs.filter(status=status)
        if search:
            term = search.strip()
            qs = qs.filter(
                Q(asset_code__icontains=term)
                | Q(name__icontains=term)
                | Q(brand__icontains=term)
                | Q(model__icontains=term)
                | Q(serial_number__icontains=term)
                | Q(asset_type__name__icontains=term)
            )
        return cls._paginate(
            qs.order_by('asset_code'),
            page=page,
            page_size=page_size,
            serialize=cls.serialize_asset,
        )

    @classmethod
    @transaction.atomic
    def create_asset(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        asset_type = AssetType.objects.filter(
            id=payload['asset_type_id'],
            organization=organization,
            is_active=True,
        ).first()
        if asset_type is None:
            raise NotFoundServiceError('Asset type not found.', code='asset_type_not_found')

        code = (payload.get('asset_code') or '').strip().upper()
        name = (payload.get('name') or '').strip()
        if len(code) < 2:
            raise ValidationServiceError('Asset code must be at least 2 characters.', code='invalid_asset_code')
        if len(name) < 2:
            raise ValidationServiceError('Asset name must be at least 2 characters.', code='invalid_name')
        if Asset.objects.filter(organization=organization, asset_code__iexact=code).exists():
            raise ConflictServiceError('An asset with this code already exists.', code='asset_code_exists')

        item = Asset.objects.create(
            organization=organization,
            asset_type=asset_type,
            asset_code=code,
            name=name,
            brand=(payload.get('brand') or '').strip(),
            model=(payload.get('model') or '').strip(),
            serial_number=(payload.get('serial_number') or '').strip(),
            purchase_date=payload.get('purchase_date'),
            warranty_expiry=payload.get('warranty_expiry'),
            status=payload.get('status') or Asset.Status.AVAILABLE,
            remarks=(payload.get('remarks') or '').strip(),
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_asset(item)

    @classmethod
    @transaction.atomic
    def update_asset(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = (
            Asset.objects.select_related('asset_type')
            .filter(id=item_id, organization=organization)
            .first()
        )
        if item is None:
            raise NotFoundServiceError('Asset not found.', code='asset_not_found')

        if 'asset_type_id' in payload:
            asset_type = AssetType.objects.filter(
                id=payload['asset_type_id'],
                organization=organization,
                is_active=True,
            ).first()
            if asset_type is None:
                raise NotFoundServiceError('Asset type not found.', code='asset_type_not_found')
            item.asset_type = asset_type
        if 'asset_code' in payload:
            code = (payload.get('asset_code') or '').strip().upper()
            if len(code) < 2:
                raise ValidationServiceError(
                    'Asset code must be at least 2 characters.',
                    code='invalid_asset_code',
                )
            if (
                Asset.objects.filter(organization=organization, asset_code__iexact=code)
                .exclude(id=item.id)
                .exists()
            ):
                raise ConflictServiceError(
                    'An asset with this code already exists.',
                    code='asset_code_exists',
                )
            item.asset_code = code
        if 'name' in payload:
            name = (payload.get('name') or '').strip()
            if len(name) < 2:
                raise ValidationServiceError('Asset name must be at least 2 characters.', code='invalid_name')
            item.name = name
        for field in ('brand', 'model', 'serial_number', 'remarks'):
            if field in payload:
                setattr(item, field, (payload.get(field) or '').strip())
        for field in ('purchase_date', 'warranty_expiry'):
            if field in payload:
                setattr(item, field, payload.get(field))
        if 'status' in payload and payload.get('status'):
            # Don't allow manual flip away from assigned while an active assignment exists.
            next_status = payload['status']
            if (
                item.status == Asset.Status.ASSIGNED
                and next_status != Asset.Status.ASSIGNED
                and item.assignments.filter(status=EmployeeAssetAssignment.Status.ACTIVE).exists()
            ):
                raise ValidationServiceError(
                    'Revoke the active assignment before changing this asset status.',
                    code='asset_still_assigned',
                )
            item.status = next_status
        if 'is_active' in payload:
            item.is_active = bool(payload.get('is_active'))
        item.updated_by = user
        item.save()
        return cls.serialize_asset(item)

    @classmethod
    @transaction.atomic
    def delete_asset(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
    ) -> None:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = Asset.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Asset not found.', code='asset_not_found')
        if item.assignments.filter(status=EmployeeAssetAssignment.Status.ACTIVE).exists():
            raise ValidationServiceError(
                'Cannot delete an asset with an active assignment.',
                code='asset_still_assigned',
            )
        item.delete()

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

    # ── Serializers ─────────────────────────────────────────────────────────

    @classmethod
    def serialize_asset_type(cls, item: AssetType) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'description': item.description,
            'is_active': item.is_active,
            'organization_id': str(item.organization_id),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_asset(cls, item: Asset) -> dict:
        return {
            'id': str(item.id),
            'organization_id': str(item.organization_id),
            'asset_type_id': str(item.asset_type_id),
            'asset_type_name': item.asset_type.name if item.asset_type_id else None,
            'asset_code': item.asset_code,
            'name': item.name,
            'brand': item.brand,
            'model': item.model,
            'serial_number': item.serial_number,
            'purchase_date': item.purchase_date.isoformat() if item.purchase_date else None,
            'warranty_expiry': item.warranty_expiry.isoformat() if item.warranty_expiry else None,
            'status': item.status,
            'remarks': item.remarks,
            'is_active': item.is_active,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

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
