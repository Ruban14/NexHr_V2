"""Shared tenant access and pagination helpers for domain services."""

from __future__ import annotations

from uuid import UUID

from apps.authentication.models import User
from apps.core.exceptions import (
    NotFoundServiceError,
    PermissionDeniedServiceError,
)
from apps.organizations.models import OrganizationMembership
from apps.people.models import Employee


class TenantAccess:
    """Reusable membership / admin / pagination helpers."""

    @classmethod
    def get_membership(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        from apps.organizations.services.workspace_service import WorkspaceService

        return WorkspaceService.get_membership(user, branch_id=branch_id)

    @classmethod
    def require_admin(
        cls,
        user: User,
        branch_id: str | UUID | None,
        *,
        message: str = 'Only organization admins can perform this action.',
        code: str = 'not_organization_admin',
    ) -> OrganizationMembership:
        membership = cls.get_membership(user, branch_id)
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        if not is_owner and access_name not in {'admin', 'administrator'}:
            raise PermissionDeniedServiceError(message, code=code)
        return membership

    @classmethod
    def is_org_admin(cls, user: User, membership: OrganizationMembership) -> bool:
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        return bool(is_owner or access_name in {'admin', 'administrator'})

    @classmethod
    def organization(cls, membership: OrganizationMembership):
        return membership.branch.organization

    @classmethod
    def get_employee(cls, *, organization, employee_id: str | UUID) -> Employee:
        employee = Employee.objects.filter(id=employee_id, organization=organization).first()
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')
        return employee

    @classmethod
    def paginate(cls, qs, *, page: int, page_size: int, serialize) -> dict:
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
