"""Organization profile and membership workspace operations."""

from __future__ import annotations

from apps.organizations.services.workspace_service import WorkspaceService


class OrganizationService:
    """Tenant organization read/update API (workspace-backed)."""

    list_memberships = WorkspaceService.list_memberships
    get_membership = WorkspaceService.get_membership
    get_organization = WorkspaceService.get_organization
    update_organization = WorkspaceService.update_organization
    serialize_organization = WorkspaceService.serialize_organization
    serialize_branch = WorkspaceService.serialize_branch
    serialize_membership_summary = WorkspaceService.serialize_membership_summary
