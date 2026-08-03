"""Organization branch helpers."""

from __future__ import annotations

from apps.organizations.services.workspace_service import WorkspaceService


class BranchService:
    """Branch serialization and membership-scoped branch access."""

    serialize_branch = WorkspaceService.serialize_branch
