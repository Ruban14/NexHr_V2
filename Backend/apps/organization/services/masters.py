"""Organization master data services (departments, designations, lookups)."""

from __future__ import annotations

from uuid import UUID

from django.db import transaction
from django.db.models import Q

from apps.authentication.models import User
from apps.core.exceptions import (
    ConflictServiceError,
    NotFoundServiceError,
    PermissionDeniedServiceError,
    ValidationServiceError,
)
from apps.organizations.models import (
    OrganizationBranch,
    OrganizationMembership,
)
from apps.workforce.models import (
    AccessType,
    Department,
    Designation,
    EmployeeType,
    Holiday,
    HolidayCalendar,
    LeaveType,
    Shift,
    WorkWeek,
)
from apps.documents.models import (
    DocumentCategory,
    DocumentDefinition,
    DocumentPolicy,
    DocumentPolicyItem,
)
from apps.organization.services.workspace import WorkspaceService


class MasterService:
    """CRUD for organization setup masters scoped by the active organization."""

    # ── Branch / org helpers ────────────────────────────────────────────────

    @classmethod
    def resolve_branch(cls, user: User, branch_id: str | UUID | None) -> OrganizationBranch:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        return membership.branch

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        if not is_owner and access_name not in {'admin', 'administrator'}:
            raise PermissionDeniedServiceError(
                'Only organization admins can manage masters.',
                code='not_organization_admin',
            )
        return membership

    @classmethod
    def _organization(cls, membership: OrganizationMembership):
        return membership.branch.organization

    # ── Departments (flat, organization-scoped) ─────────────────────────────

    @classmethod
    def list_departments(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = Department.objects.filter(organization=membership.branch.organization)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return cls._paginate(qs.order_by('name'), page=page, page_size=page_size, serialize=cls.serialize_department)

    @classmethod
    @transaction.atomic
    def create_department(cls, *, user: User, branch_id: str | UUID | None, name: str) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Department name must be at least 2 characters.', code='invalid_name')
        if Department.objects.filter(organization=organization, name__iexact=cleaned).exists():
            raise ConflictServiceError('A department with this name already exists.', code='department_exists')
        dept = Department.objects.create(
            organization=organization,
            name=cleaned,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_department(dept)

    @classmethod
    @transaction.atomic
    def update_department(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        department_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        dept = Department.objects.filter(id=department_id, organization=organization).first()
        if dept is None:
            raise NotFoundServiceError('Department not found.', code='department_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Department name must be at least 2 characters.', code='invalid_name')
            if (
                Department.objects.filter(organization=organization, name__iexact=cleaned)
                .exclude(id=dept.id)
                .exists()
            ):
                raise ConflictServiceError('A department with this name already exists.', code='department_exists')
            dept.name = cleaned
        if 'is_active' in payload and payload['is_active'] is not None:
            dept.is_active = bool(payload['is_active'])
        dept.updated_by = user
        dept.save()
        return cls.serialize_department(dept)

    @classmethod
    @transaction.atomic
    def delete_department(cls, *, user: User, branch_id: str | UUID | None, department_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        dept = Department.objects.filter(id=department_id, organization=organization).first()
        if dept is None:
            raise NotFoundServiceError('Department not found.', code='department_not_found')
        if dept.designations.exists():
            raise ConflictServiceError(
                'Remove designations before deleting this department.',
                code='department_has_designations',
            )
        dept.delete()

    # ── Designations (tree per department) ──────────────────────────────────

    @classmethod
    def list_designations(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        department_id: str | UUID,
        search: str = '',
    ) -> list[dict]:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        department = Department.objects.filter(
            id=department_id,
            organization=membership.branch.organization,
        ).first()
        if department is None:
            raise NotFoundServiceError('Department not found.', code='department_not_found')
        qs = Designation.objects.filter(department=department).order_by('sort_order', 'name')
        if search:
            qs = qs.filter(name__icontains=search.strip())
        rows = [cls.serialize_designation(item) for item in qs]
        return cls.build_designation_tree(rows)

    @classmethod
    @transaction.atomic
    def create_designation(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        department_id: str | UUID,
        name: str,
        parent_id: str | UUID | None = None,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        department = Department.objects.filter(
            id=department_id,
            organization=membership.branch.organization,
        ).first()
        if department is None:
            raise NotFoundServiceError('Department not found.', code='department_not_found')

        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Designation name must be at least 2 characters.', code='invalid_name')
        if Designation.objects.filter(department=department, name__iexact=cleaned).exists():
            raise ConflictServiceError('A designation with this name already exists.', code='designation_exists')

        parent = None
        if parent_id:
            parent = Designation.objects.filter(id=parent_id, department=department).first()
            if parent is None:
                raise NotFoundServiceError('Parent designation not found.', code='parent_not_found')

        siblings = Designation.objects.filter(department=department, parent=parent)
        next_order = (siblings.order_by('-sort_order').values_list('sort_order', flat=True).first() or -1) + 1

        item = Designation.objects.create(
            department=department,
            parent=parent,
            name=cleaned,
            sort_order=next_order,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_designation(item)

    @classmethod
    @transaction.atomic
    def update_designation(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        designation_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        item = (
            Designation.objects.select_related('department')
            .filter(id=designation_id, department__organization=membership.branch.organization)
            .first()
        )
        if item is None:
            raise NotFoundServiceError('Designation not found.', code='designation_not_found')

        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Designation name must be at least 2 characters.', code='invalid_name')
            if (
                Designation.objects.filter(department=item.department, name__iexact=cleaned)
                .exclude(id=item.id)
                .exists()
            ):
                raise ConflictServiceError('A designation with this name already exists.', code='designation_exists')
            item.name = cleaned

        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])

        if 'parent_id' in payload:
            parent_id = payload['parent_id']
            if parent_id in (None, ''):
                item.parent = None
            else:
                if str(parent_id) == str(item.id):
                    raise ValidationServiceError('A designation cannot be its own parent.', code='invalid_parent')
                parent = Designation.objects.filter(id=parent_id, department=item.department).first()
                if parent is None:
                    raise NotFoundServiceError('Parent designation not found.', code='parent_not_found')
                if cls._is_descendant(parent, item):
                    raise ValidationServiceError(
                        'Cannot move a designation under its own descendant.',
                        code='invalid_parent',
                    )
                item.parent = parent

        item.updated_by = user
        item.save()
        return cls.serialize_designation(item)

    @classmethod
    @transaction.atomic
    def delete_designation(cls, *, user: User, branch_id: str | UUID | None, designation_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        item = Designation.objects.filter(
            id=designation_id,
            department__organization=membership.branch.organization,
        ).first()
        if item is None:
            raise NotFoundServiceError('Designation not found.', code='designation_not_found')
        # Re-parent children to deleted node's parent so hierarchy stays intact.
        Designation.objects.filter(parent=item).update(parent=item.parent)
        item.delete()

    @classmethod
    @transaction.atomic
    def move_designation(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        designation_id: str | UUID,
        direction: str,
    ) -> list[dict]:
        membership = cls.require_admin(user, branch_id)
        item = Designation.objects.filter(
            id=designation_id,
            department__organization=membership.branch.organization,
        ).first()
        if item is None:
            raise NotFoundServiceError('Designation not found.', code='designation_not_found')

        siblings = list(
            Designation.objects.filter(department=item.department, parent_id=item.parent_id).order_by(
                'sort_order',
                'name',
            )
        )
        index = next((i for i, row in enumerate(siblings) if row.id == item.id), None)
        if index is None:
            raise NotFoundServiceError('Designation not found.', code='designation_not_found')

        if direction == 'up' and index > 0:
            siblings[index], siblings[index - 1] = siblings[index - 1], siblings[index]
        elif direction == 'down' and index < len(siblings) - 1:
            siblings[index], siblings[index + 1] = siblings[index + 1], siblings[index]

        for order, sibling in enumerate(siblings):
            if sibling.sort_order != order:
                sibling.sort_order = order
                sibling.updated_by = user
                sibling.save(update_fields=['sort_order', 'updated_by', 'updated_at'])

        qs = Designation.objects.filter(department=item.department).order_by('sort_order', 'name')
        rows = [cls.serialize_designation(row) for row in qs]
        return cls.build_designation_tree(rows)

    @classmethod
    @transaction.atomic
    def reposition_designation(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        designation_id: str | UUID,
        target_id: str | UUID,
        position: str,
    ) -> list[dict]:
        membership = cls.require_admin(user, branch_id)
        item = Designation.objects.filter(
            id=designation_id,
            department__organization=membership.branch.organization,
        ).first()
        if item is None:
            raise NotFoundServiceError('Designation not found.', code='designation_not_found')

        target = Designation.objects.filter(
            id=target_id,
            department_id=item.department_id,
        ).first()
        if target is None:
            raise NotFoundServiceError('Drop target not found.', code='target_not_found')

        if item.id == target.id:
            return cls._tree_for_department(item.department_id)

        if position == 'inside':
            new_parent = target
            if cls._is_descendant(target, item) or target.id == item.id:
                raise ValidationServiceError(
                    'Cannot move a designation under itself or its descendant.',
                    code='invalid_parent',
                )
            ordered = list(
                Designation.objects.filter(department=item.department, parent=target)
                .exclude(id=item.id)
                .order_by('sort_order', 'name')
            )
            ordered.append(item)
        else:
            new_parent = target.parent
            if new_parent is not None and cls._is_descendant(new_parent, item):
                raise ValidationServiceError(
                    'Cannot move a designation under its own descendant.',
                    code='invalid_parent',
                )
            ordered = list(
                Designation.objects.filter(department=item.department, parent_id=target.parent_id)
                .exclude(id=item.id)
                .order_by('sort_order', 'name')
            )
            try:
                target_index = next(i for i, row in enumerate(ordered) if row.id == target.id)
            except StopIteration:
                raise NotFoundServiceError('Drop target not found.', code='target_not_found')
            insert_at = target_index if position == 'before' else target_index + 1
            ordered.insert(insert_at, item)

        old_parent_id = item.parent_id
        new_parent_id = new_parent.id if new_parent is not None else None

        item.parent = new_parent
        item.updated_by = user
        item.save(update_fields=['parent', 'updated_by', 'updated_at'])

        for order, sibling in enumerate(ordered):
            updates: list[str] = []
            if sibling.parent_id != new_parent_id:
                sibling.parent = new_parent
                updates.append('parent')
            if sibling.sort_order != order:
                sibling.sort_order = order
                updates.append('sort_order')
            if updates:
                sibling.updated_by = user
                updates.extend(['updated_by', 'updated_at'])
                sibling.save(update_fields=updates)

        if old_parent_id != new_parent_id:
            cls._renumber_siblings(
                department_id=item.department_id,
                parent_id=old_parent_id,
                user=user,
            )

        return cls._tree_for_department(item.department_id)

    @classmethod
    def _renumber_siblings(cls, *, department_id, parent_id, user: User) -> None:
        siblings = Designation.objects.filter(
            department_id=department_id,
            parent_id=parent_id,
        ).order_by('sort_order', 'name')
        for order, sibling in enumerate(siblings):
            if sibling.sort_order != order:
                sibling.sort_order = order
                sibling.updated_by = user
                sibling.save(update_fields=['sort_order', 'updated_by', 'updated_at'])

    @classmethod
    def _tree_for_department(cls, department_id) -> list[dict]:
        qs = Designation.objects.filter(department_id=department_id).order_by('sort_order', 'name')
        rows = [cls.serialize_designation(row) for row in qs]
        return cls.build_designation_tree(rows)

    # ── Employee types (global) ─────────────────────────────────────────────

    @classmethod
    def list_employee_types(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> dict:
        cls.resolve_branch(user, branch_id)
        qs = EmployeeType.objects.all()
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return cls._paginate(qs.order_by('name'), page=page, page_size=page_size, serialize=cls.serialize_employee_type)

    @classmethod
    @transaction.atomic
    def create_employee_type(cls, *, user: User, branch_id: str | UUID | None, name: str) -> dict:
        cls.require_admin(user, branch_id)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Employee type name must be at least 2 characters.', code='invalid_name')
        if EmployeeType.objects.filter(name__iexact=cleaned).exists():
            raise ConflictServiceError('An employee type with this name already exists.', code='employee_type_exists')
        item = EmployeeType.objects.create(name=cleaned, is_active=True, created_by=user, updated_by=user)
        return cls.serialize_employee_type(item)

    @classmethod
    @transaction.atomic
    def update_employee_type(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        cls.require_admin(user, branch_id)
        item = EmployeeType.objects.filter(id=item_id).first()
        if item is None:
            raise NotFoundServiceError('Employee type not found.', code='employee_type_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Employee type name must be at least 2 characters.', code='invalid_name')
            if EmployeeType.objects.filter(name__iexact=cleaned).exclude(id=item.id).exists():
                raise ConflictServiceError(
                    'An employee type with this name already exists.',
                    code='employee_type_exists',
                )
            item.name = cleaned
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_employee_type(item)

    @classmethod
    @transaction.atomic
    def delete_employee_type(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        cls.require_admin(user, branch_id)
        item = EmployeeType.objects.filter(id=item_id).first()
        if item is None:
            raise NotFoundServiceError('Employee type not found.', code='employee_type_not_found')
        if item.memberships.exists():
            raise ConflictServiceError(
                'This employee type is in use and cannot be deleted.',
                code='employee_type_in_use',
            )
        item.delete()

    # ── Access types (industry-scoped) ──────────────────────────────────────

    @classmethod
    def list_access_types(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        industry_id = membership.branch.organization.industry_type_id
        qs = AccessType.objects.filter(Q(industry_type_id=industry_id) | Q(industry_type__isnull=True))
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(Q(name__icontains=search.strip()) | Q(description__icontains=search.strip()))
        return cls._paginate(qs.order_by('name'), page=page, page_size=page_size, serialize=cls.serialize_access_type)

    @classmethod
    @transaction.atomic
    def create_access_type(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        description: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Access type name must be at least 2 characters.', code='invalid_name')
        industry = membership.branch.organization.industry_type
        if AccessType.objects.filter(name__iexact=cleaned, industry_type=industry).exists():
            raise ConflictServiceError('An access type with this name already exists.', code='access_type_exists')
        item = AccessType.objects.create(
            name=cleaned,
            description=(description or '').strip(),
            industry_type=industry,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_access_type(item)

    @classmethod
    @transaction.atomic
    def update_access_type(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        industry_id = membership.branch.organization.industry_type_id
        item = AccessType.objects.filter(
            Q(id=item_id) & (Q(industry_type_id=industry_id) | Q(industry_type__isnull=True))
        ).first()
        if item is None:
            raise NotFoundServiceError('Access type not found.', code='access_type_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Access type name must be at least 2 characters.', code='invalid_name')
            if (
                AccessType.objects.filter(name__iexact=cleaned, industry_type_id=item.industry_type_id)
                .exclude(id=item.id)
                .exists()
            ):
                raise ConflictServiceError('An access type with this name already exists.', code='access_type_exists')
            item.name = cleaned
        if 'description' in payload and payload['description'] is not None:
            item.description = str(payload['description']).strip()
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_access_type(item)

    @classmethod
    @transaction.atomic
    def delete_access_type(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        industry_id = membership.branch.organization.industry_type_id
        item = AccessType.objects.filter(
            Q(id=item_id) & (Q(industry_type_id=industry_id) | Q(industry_type__isnull=True))
        ).first()
        if item is None:
            raise NotFoundServiceError('Access type not found.', code='access_type_not_found')
        if item.memberships.exists():
            raise ConflictServiceError(
                'This access type is in use and cannot be deleted.',
                code='access_type_in_use',
            )
        item.delete()

    # ── Shifts (organization-scoped) ────────────────────────────────────────

    @classmethod
    def list_shifts(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = Shift.objects.filter(organization=membership.branch.organization)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return cls._paginate(qs.order_by('name'), page=page, page_size=page_size, serialize=cls.serialize_shift)

    @classmethod
    @transaction.atomic
    def create_shift(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        start_time,
        end_time,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Shift name must be at least 2 characters.', code='invalid_name')
        if Shift.objects.filter(organization=organization, name__iexact=cleaned).exists():
            raise ConflictServiceError('A shift with this name already exists.', code='shift_exists')
        item = Shift.objects.create(
            organization=organization,
            name=cleaned,
            start_time=start_time,
            end_time=end_time,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_shift(item)

    @classmethod
    @transaction.atomic
    def update_shift(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = Shift.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Shift not found.', code='shift_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Shift name must be at least 2 characters.', code='invalid_name')
            if Shift.objects.filter(organization=organization, name__iexact=cleaned).exclude(id=item.id).exists():
                raise ConflictServiceError('A shift with this name already exists.', code='shift_exists')
            item.name = cleaned
        if 'start_time' in payload and payload['start_time'] is not None:
            item.start_time = payload['start_time']
        if 'end_time' in payload and payload['end_time'] is not None:
            item.end_time = payload['end_time']
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_shift(item)

    @classmethod
    @transaction.atomic
    def delete_shift(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        item = Shift.objects.filter(id=item_id, organization=cls._organization(membership)).first()
        if item is None:
            raise NotFoundServiceError('Shift not found.', code='shift_not_found')
        item.delete()

    # ── Work weeks (organization-scoped) ────────────────────────────────────

    @classmethod
    def list_work_weeks(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = WorkWeek.objects.filter(organization=membership.branch.organization)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return cls._paginate(qs.order_by('name'), page=page, page_size=page_size, serialize=cls.serialize_work_week)

    @classmethod
    @transaction.atomic
    def create_work_week(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        working_days: list,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Work week name must be at least 2 characters.', code='invalid_name')
        days = cls._normalize_working_days(working_days)
        if WorkWeek.objects.filter(organization=organization, name__iexact=cleaned).exists():
            raise ConflictServiceError('A work week with this name already exists.', code='work_week_exists')
        item = WorkWeek.objects.create(
            organization=organization,
            name=cleaned,
            working_days=days,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_work_week(item)

    @classmethod
    @transaction.atomic
    def update_work_week(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = WorkWeek.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Work week not found.', code='work_week_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Work week name must be at least 2 characters.', code='invalid_name')
            if WorkWeek.objects.filter(organization=organization, name__iexact=cleaned).exclude(id=item.id).exists():
                raise ConflictServiceError('A work week with this name already exists.', code='work_week_exists')
            item.name = cleaned
        if 'working_days' in payload and payload['working_days'] is not None:
            item.working_days = cls._normalize_working_days(payload['working_days'])
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_work_week(item)

    @classmethod
    @transaction.atomic
    def delete_work_week(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        item = WorkWeek.objects.filter(id=item_id, organization=cls._organization(membership)).first()
        if item is None:
            raise NotFoundServiceError('Work week not found.', code='work_week_not_found')
        item.delete()

    # ── Leave types (organization-scoped) ───────────────────────────────────

    @classmethod
    def list_leave_types(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = LeaveType.objects.filter(organization=membership.branch.organization)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return cls._paginate(qs.order_by('name'), page=page, page_size=page_size, serialize=cls.serialize_leave_type)

    @classmethod
    @transaction.atomic
    def create_leave_type(cls, *, user: User, branch_id: str | UUID | None, name: str) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Leave type name must be at least 2 characters.', code='invalid_name')
        if LeaveType.objects.filter(organization=organization, name__iexact=cleaned).exists():
            raise ConflictServiceError('A leave type with this name already exists.', code='leave_type_exists')
        item = LeaveType.objects.create(
            organization=organization,
            name=cleaned,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_leave_type(item)

    @classmethod
    @transaction.atomic
    def update_leave_type(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = LeaveType.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Leave type not found.', code='leave_type_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Leave type name must be at least 2 characters.', code='invalid_name')
            if LeaveType.objects.filter(organization=organization, name__iexact=cleaned).exclude(id=item.id).exists():
                raise ConflictServiceError('A leave type with this name already exists.', code='leave_type_exists')
            item.name = cleaned
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_leave_type(item)

    @classmethod
    @transaction.atomic
    def delete_leave_type(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        item = LeaveType.objects.filter(id=item_id, organization=cls._organization(membership)).first()
        if item is None:
            raise NotFoundServiceError('Leave type not found.', code='leave_type_not_found')
        item.delete()

    # ── Holiday calendars (organization-scoped) ─────────────────────────────

    @classmethod
    def list_holiday_calendars(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        year: int | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = HolidayCalendar.objects.filter(organization=membership.branch.organization)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if year is not None:
            qs = qs.filter(year=year)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return cls._paginate(
            qs.order_by('-year', 'name'),
            page=page,
            page_size=page_size,
            serialize=cls.serialize_holiday_calendar,
        )

    @classmethod
    @transaction.atomic
    def create_holiday_calendar(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        year: int,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Calendar name must be at least 2 characters.', code='invalid_name')
        year_value = cls._normalize_year(year)
        if HolidayCalendar.objects.filter(organization=organization, name__iexact=cleaned, year=year_value).exists():
            raise ConflictServiceError(
                'A holiday calendar with this name already exists for that year.',
                code='holiday_calendar_exists',
            )
        item = HolidayCalendar.objects.create(
            organization=organization,
            name=cleaned,
            year=year_value,
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_holiday_calendar(item)

    @classmethod
    @transaction.atomic
    def update_holiday_calendar(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = HolidayCalendar.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Holiday calendar not found.', code='holiday_calendar_not_found')
        next_name = item.name
        next_year = item.year
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Calendar name must be at least 2 characters.', code='invalid_name')
            next_name = cleaned
        if 'year' in payload and payload['year'] is not None:
            next_year = cls._normalize_year(payload['year'])
        if (
            HolidayCalendar.objects.filter(organization=organization, name__iexact=next_name, year=next_year)
            .exclude(id=item.id)
            .exists()
        ):
            raise ConflictServiceError(
                'A holiday calendar with this name already exists for that year.',
                code='holiday_calendar_exists',
            )
        item.name = next_name
        item.year = next_year
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_holiday_calendar(item)

    @classmethod
    @transaction.atomic
    def delete_holiday_calendar(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        item = HolidayCalendar.objects.filter(id=item_id, organization=cls._organization(membership)).first()
        if item is None:
            raise NotFoundServiceError('Holiday calendar not found.', code='holiday_calendar_not_found')
        item.delete()

    # ── Holidays (per calendar) ─────────────────────────────────────────────

    @classmethod
    def list_holidays(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        calendar_id: str | UUID,
        search: str = '',
    ) -> list[dict]:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        calendar = HolidayCalendar.objects.filter(
            id=calendar_id,
            organization=membership.branch.organization,
        ).first()
        if calendar is None:
            raise NotFoundServiceError('Holiday calendar not found.', code='holiday_calendar_not_found')
        qs = Holiday.objects.filter(holiday_calendar=calendar).order_by('date')
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return [cls.serialize_holiday(item) for item in qs]

    @classmethod
    @transaction.atomic
    def create_holiday(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        calendar_id: str | UUID,
        name: str,
        date,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        calendar = HolidayCalendar.objects.filter(
            id=calendar_id,
            organization=membership.branch.organization,
        ).first()
        if calendar is None:
            raise NotFoundServiceError('Holiday calendar not found.', code='holiday_calendar_not_found')
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Holiday name must be at least 2 characters.', code='invalid_name')
        if Holiday.objects.filter(holiday_calendar=calendar, date=date).exists():
            raise ConflictServiceError('A holiday already exists on this date.', code='holiday_exists')
        item = Holiday.objects.create(
            holiday_calendar=calendar,
            name=cleaned,
            date=date,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_holiday(item)

    @classmethod
    @transaction.atomic
    def update_holiday(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        holiday_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        item = (
            Holiday.objects.select_related('holiday_calendar')
            .filter(id=holiday_id, holiday_calendar__organization=membership.branch.organization)
            .first()
        )
        if item is None:
            raise NotFoundServiceError('Holiday not found.', code='holiday_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Holiday name must be at least 2 characters.', code='invalid_name')
            item.name = cleaned
        if 'date' in payload and payload['date'] is not None:
            next_date = payload['date']
            if (
                Holiday.objects.filter(holiday_calendar=item.holiday_calendar, date=next_date)
                .exclude(id=item.id)
                .exists()
            ):
                raise ConflictServiceError('A holiday already exists on this date.', code='holiday_exists')
            item.date = next_date
        item.updated_by = user
        item.save()
        return cls.serialize_holiday(item)

    @classmethod
    @transaction.atomic
    def delete_holiday(cls, *, user: User, branch_id: str | UUID | None, holiday_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        item = Holiday.objects.filter(
            id=holiday_id,
            holiday_calendar__organization=membership.branch.organization,
        ).first()
        if item is None:
            raise NotFoundServiceError('Holiday not found.', code='holiday_not_found')
        item.delete()

    # ── Document categories (global masters) ────────────────────────────────

    @classmethod
    def list_document_categories(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        is_active: bool | None = True,
    ) -> list[dict]:
        WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = DocumentCategory.objects.all()
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return [cls.serialize_document_category(item) for item in qs.order_by('display_order', 'name')]

    @classmethod
    @transaction.atomic
    def create_document_category(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        description: str = '',
        display_order: int = 0,
    ) -> dict:
        cls.require_admin(user, branch_id)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Category name must be at least 2 characters.', code='invalid_name')
        if DocumentCategory.objects.filter(name__iexact=cleaned).exists():
            raise ConflictServiceError('A document category with this name already exists.', code='category_exists')
        item = DocumentCategory.objects.create(
            name=cleaned,
            description=(description or '').strip(),
            display_order=max(0, int(display_order or 0)),
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_document_category(item)

    @classmethod
    @transaction.atomic
    def update_document_category(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        cls.require_admin(user, branch_id)
        item = DocumentCategory.objects.filter(id=item_id).first()
        if item is None:
            raise NotFoundServiceError('Document category not found.', code='category_not_found')
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Category name must be at least 2 characters.', code='invalid_name')
            if DocumentCategory.objects.filter(name__iexact=cleaned).exclude(id=item.id).exists():
                raise ConflictServiceError(
                    'A document category with this name already exists.',
                    code='category_exists',
                )
            item.name = cleaned
        if 'description' in payload and payload['description'] is not None:
            item.description = str(payload['description']).strip()
        if 'display_order' in payload and payload['display_order'] is not None:
            item.display_order = max(0, int(payload['display_order']))
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_document_category(item)

    # ── Document definitions (organization-scoped) ──────────────────────────

    @classmethod
    def list_document_definitions(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        category_id: str | UUID | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        qs = DocumentDefinition.objects.filter(
            Q(organization=organization) | Q(organization__isnull=True)
        ).select_related('category')
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if search:
            qs = qs.filter(
                Q(name__icontains=search.strip())
                | Q(description__icontains=search.strip())
                | Q(category__name__icontains=search.strip())
            )
        return cls._paginate(
            qs.order_by('category__display_order', 'category__name', 'name'),
            page=page,
            page_size=page_size,
            serialize=cls.serialize_document_definition,
        )

    @classmethod
    @transaction.atomic
    def create_document_definition(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        category_id: str | UUID,
        description: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Document name must be at least 2 characters.', code='invalid_name')
        category = DocumentCategory.objects.filter(id=category_id, is_active=True).first()
        if category is None:
            raise NotFoundServiceError('Document category not found.', code='category_not_found')
        if DocumentDefinition.objects.filter(
            organization=organization,
            category=category,
            name__iexact=cleaned,
        ).exists():
            raise ConflictServiceError(
                'A document with this name already exists in the category.',
                code='document_exists',
            )
        item = DocumentDefinition.objects.create(
            organization=organization,
            category=category,
            name=cleaned,
            description=(description or '').strip(),
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        return cls.serialize_document_definition(item)

    @classmethod
    @transaction.atomic
    def update_document_definition(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = DocumentDefinition.objects.filter(id=item_id, organization=organization).select_related('category').first()
        if item is None:
            raise NotFoundServiceError('Document not found.', code='document_not_found')
        category = item.category
        if 'category_id' in payload and payload['category_id'] is not None:
            category = DocumentCategory.objects.filter(id=payload['category_id'], is_active=True).first()
            if category is None:
                raise NotFoundServiceError('Document category not found.', code='category_not_found')
            item.category = category
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Document name must be at least 2 characters.', code='invalid_name')
            if (
                DocumentDefinition.objects.filter(
                    organization=organization,
                    category=category,
                    name__iexact=cleaned,
                )
                .exclude(id=item.id)
                .exists()
            ):
                raise ConflictServiceError(
                    'A document with this name already exists in the category.',
                    code='document_exists',
                )
            item.name = cleaned
        if 'description' in payload and payload['description'] is not None:
            item.description = str(payload['description']).strip()
        if 'is_active' in payload and payload['is_active'] is not None:
            item.is_active = bool(payload['is_active'])
        item.updated_by = user
        item.save()
        return cls.serialize_document_definition(item)

    @classmethod
    @transaction.atomic
    def delete_document_definition(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        item = DocumentDefinition.objects.filter(id=item_id, organization=organization).first()
        if item is None:
            raise NotFoundServiceError('Document not found.', code='document_not_found')
        if item.policy_items.exists():
            raise ConflictServiceError(
                'Remove this document from policies before deleting it.',
                code='document_in_use',
            )
        item.delete()

    # ── Document policies (organization-scoped) ─────────────────────────────

    @classmethod
    def list_document_policies(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        search: str = '',
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        employee_type_id: str | UUID | None = None,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        qs = DocumentPolicy.objects.filter(organization=membership.branch.organization).select_related(
            'employee_type'
        ).prefetch_related('items__document__category')
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if employee_type_id:
            qs = qs.filter(employee_type_id=employee_type_id)
        if search:
            qs = qs.filter(
                Q(name__icontains=search.strip())
                | Q(description__icontains=search.strip())
                | Q(employee_type__name__icontains=search.strip())
            )
        return cls._paginate(
            qs.order_by('name'),
            page=page,
            page_size=page_size,
            serialize=cls.serialize_document_policy,
        )

    @classmethod
    def get_document_policy(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        item = (
            DocumentPolicy.objects.filter(id=item_id, organization=membership.branch.organization)
            .select_related('employee_type')
            .prefetch_related('items__document__category')
            .first()
        )
        if item is None:
            raise NotFoundServiceError('Document policy not found.', code='policy_not_found')
        return cls.serialize_document_policy(item)

    @classmethod
    @transaction.atomic
    def create_document_policy(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        name: str,
        employee_type_id: str | UUID,
        description: str = '',
        is_default: bool = False,
        items: list[dict] | None = None,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValidationServiceError('Policy name must be at least 2 characters.', code='invalid_name')
        employee_type = EmployeeType.objects.filter(id=employee_type_id, is_active=True).first()
        if employee_type is None:
            raise NotFoundServiceError('Employee type not found.', code='employee_type_not_found')
        if DocumentPolicy.objects.filter(
            organization=organization,
            employee_type=employee_type,
            name__iexact=cleaned,
        ).exists():
            raise ConflictServiceError(
                'A policy with this name already exists for the employee type.',
                code='policy_exists',
            )
        if is_default:
            DocumentPolicy.objects.filter(
                organization=organization,
                employee_type=employee_type,
                is_default=True,
            ).update(is_default=False, updated_by=user)
        policy = DocumentPolicy.objects.create(
            organization=organization,
            employee_type=employee_type,
            name=cleaned,
            description=(description or '').strip(),
            is_default=bool(is_default),
            is_active=True,
            created_by=user,
            updated_by=user,
        )
        cls._replace_policy_items(policy=policy, organization=organization, items=items or [], user=user)
        return cls.get_document_policy(user=user, branch_id=branch_id, item_id=policy.id)

    @classmethod
    @transaction.atomic
    def update_document_policy(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        item_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        organization = cls._organization(membership)
        policy = DocumentPolicy.objects.filter(id=item_id, organization=organization).first()
        if policy is None:
            raise NotFoundServiceError('Document policy not found.', code='policy_not_found')
        employee_type = policy.employee_type
        if 'employee_type_id' in payload and payload['employee_type_id'] is not None:
            employee_type = EmployeeType.objects.filter(
                id=payload['employee_type_id'],
                is_active=True,
            ).first()
            if employee_type is None:
                raise NotFoundServiceError('Employee type not found.', code='employee_type_not_found')
            policy.employee_type = employee_type
        if 'name' in payload and payload['name'] is not None:
            cleaned = str(payload['name']).strip()
            if len(cleaned) < 2:
                raise ValidationServiceError('Policy name must be at least 2 characters.', code='invalid_name')
            if (
                DocumentPolicy.objects.filter(
                    organization=organization,
                    employee_type=employee_type,
                    name__iexact=cleaned,
                )
                .exclude(id=policy.id)
                .exists()
            ):
                raise ConflictServiceError(
                    'A policy with this name already exists for the employee type.',
                    code='policy_exists',
                )
            policy.name = cleaned
        if 'description' in payload and payload['description'] is not None:
            policy.description = str(payload['description']).strip()
        if 'is_default' in payload and payload['is_default'] is not None:
            policy.is_default = bool(payload['is_default'])
            if policy.is_default:
                DocumentPolicy.objects.filter(
                    organization=organization,
                    employee_type=employee_type,
                    is_default=True,
                ).exclude(id=policy.id).update(is_default=False, updated_by=user)
        if 'is_active' in payload and payload['is_active'] is not None:
            policy.is_active = bool(payload['is_active'])
        policy.updated_by = user
        policy.save()
        if 'items' in payload and payload['items'] is not None:
            cls._replace_policy_items(
                policy=policy,
                organization=organization,
                items=payload['items'],
                user=user,
            )
        return cls.get_document_policy(user=user, branch_id=branch_id, item_id=policy.id)

    @classmethod
    @transaction.atomic
    def delete_document_policy(cls, *, user: User, branch_id: str | UUID | None, item_id: str | UUID) -> None:
        membership = cls.require_admin(user, branch_id)
        policy = DocumentPolicy.objects.filter(id=item_id, organization=cls._organization(membership)).first()
        if policy is None:
            raise NotFoundServiceError('Document policy not found.', code='policy_not_found')
        policy.delete()

    @classmethod
    def _replace_policy_items(
        cls,
        *,
        policy: DocumentPolicy,
        organization,
        items: list[dict],
        user: User,
    ) -> None:
        seen_documents: set[UUID] = set()
        normalized: list[dict] = []
        for index, raw in enumerate(items):
            document_id = raw.get('document_id')
            if document_id is None:
                raise ValidationServiceError('Each policy item needs a document.', code='invalid_policy_item')
            document_uuid = UUID(str(document_id))
            if document_uuid in seen_documents:
                raise ValidationServiceError('Duplicate documents are not allowed in a policy.', code='duplicate_document')
            seen_documents.add(document_uuid)
            document = DocumentDefinition.objects.filter(
                Q(organization=organization) | Q(organization__isnull=True),
                id=document_uuid,
                is_active=True,
            ).first()
            if document is None:
                raise NotFoundServiceError('Document not found.', code='document_not_found')
            normalized.append(
                {
                    'document': document,
                    'display_order': int(raw.get('display_order', index) or index),
                    'is_required': bool(raw.get('is_required', True)),
                    'allow_multiple': bool(raw.get('allow_multiple', False)),
                    'verification_required': bool(raw.get('verification_required', True)),
                    'requires_expiry': bool(raw.get('requires_expiry', False)),
                }
            )
        policy.items.all().delete()
        DocumentPolicyItem.objects.bulk_create(
            [
                DocumentPolicyItem(
                    policy=policy,
                    document=row['document'],
                    display_order=row['display_order'],
                    is_required=row['is_required'],
                    allow_multiple=row['allow_multiple'],
                    verification_required=row['verification_required'],
                    requires_expiry=row['requires_expiry'],
                    created_by=user,
                    updated_by=user,
                )
                for row in normalized
            ]
        )

    # ── Serialization / helpers ─────────────────────────────────────────────

    @classmethod
    def serialize_document_category(cls, item: DocumentCategory) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'description': item.description,
            'display_order': item.display_order,
            'is_active': item.is_active,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_document_definition(cls, item: DocumentDefinition) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'description': item.description,
            'is_active': item.is_active,
            'organization_id': str(item.organization_id) if item.organization_id else None,
            'category_id': str(item.category_id),
            'category_name': item.category.name if item.category_id else None,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_document_policy_item(cls, item: DocumentPolicyItem) -> dict:
        document = item.document
        return {
            'id': str(item.id),
            'document_id': str(item.document_id),
            'document_name': document.name if document else None,
            'category_id': str(document.category_id) if document else None,
            'category_name': document.category.name if document and document.category_id else None,
            'display_order': item.display_order,
            'is_required': item.is_required,
            'allow_multiple': item.allow_multiple,
            'verification_required': item.verification_required,
            'requires_expiry': item.requires_expiry,
        }

    @classmethod
    def serialize_document_policy(cls, item: DocumentPolicy) -> dict:
        items = sorted(item.items.all(), key=lambda row: (row.display_order, str(row.id)))
        return {
            'id': str(item.id),
            'name': item.name,
            'description': item.description,
            'is_default': item.is_default,
            'is_active': item.is_active,
            'organization_id': str(item.organization_id),
            'employee_type_id': str(item.employee_type_id),
            'employee_type_name': item.employee_type.name if item.employee_type_id else None,
            'item_count': len(items),
            'items': [cls.serialize_document_policy_item(row) for row in items],
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_department(cls, item: Department) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'is_active': item.is_active,
            'organization_id': str(item.organization_id),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_shift(cls, item: Shift) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'start_time': item.start_time.strftime('%H:%M'),
            'end_time': item.end_time.strftime('%H:%M'),
            'is_active': item.is_active,
            'organization_id': str(item.organization_id),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_work_week(cls, item: WorkWeek) -> dict:
        days = [int(day) for day in (item.working_days or [])]
        return {
            'id': str(item.id),
            'name': item.name,
            'working_days': days,
            'is_active': item.is_active,
            'organization_id': str(item.organization_id),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_leave_type(cls, item: LeaveType) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'is_active': item.is_active,
            'organization_id': str(item.organization_id),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_holiday_calendar(cls, item: HolidayCalendar) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'year': item.year,
            'is_active': item.is_active,
            'organization_id': str(item.organization_id),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_holiday(cls, item: Holiday) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'date': item.date.isoformat(),
            'holiday_calendar_id': str(item.holiday_calendar_id),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def _normalize_year(cls, year) -> int:
        try:
            value = int(year)
        except (TypeError, ValueError):
            raise ValidationServiceError('Enter a valid year.', code='invalid_year')
        if value < 2000 or value > 2100:
            raise ValidationServiceError('Year must be between 2000 and 2100.', code='invalid_year')
        return value

    @classmethod
    def _normalize_working_days(cls, working_days) -> list[int]:
        if not isinstance(working_days, list) or not working_days:
            raise ValidationServiceError('Select at least one working day.', code='invalid_working_days')
        valid = {choice.value for choice in WorkWeek.WeekDay}
        normalized: list[int] = []
        for day in working_days:
            try:
                value = int(day)
            except (TypeError, ValueError):
                raise ValidationServiceError('Working days must be numbers 1–7.', code='invalid_working_days')
            if value not in valid:
                raise ValidationServiceError('Working days must be numbers 1–7.', code='invalid_working_days')
            if value not in normalized:
                normalized.append(value)
        return sorted(normalized)

    @classmethod
    def serialize_designation(cls, item: Designation) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'is_active': item.is_active,
            'department_id': str(item.department_id),
            'parent_id': str(item.parent_id) if item.parent_id else None,
            'sort_order': item.sort_order,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_employee_type(cls, item: EmployeeType) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'is_active': item.is_active,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_access_type(cls, item: AccessType) -> dict:
        return {
            'id': str(item.id),
            'name': item.name,
            'description': item.description,
            'is_active': item.is_active,
            'industry_type_id': str(item.industry_type_id) if item.industry_type_id else None,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def build_designation_tree(cls, rows: list[dict]) -> list[dict]:
        by_id: dict[str, dict] = {
            row['id']: {**row, 'children': []} for row in rows
        }
        roots: list[dict] = []
        for row in rows:
            node = by_id[row['id']]
            parent_id = row.get('parent_id')
            if parent_id and parent_id in by_id:
                by_id[parent_id]['children'].append(node)
            else:
                roots.append(node)
        return roots

    @classmethod
    def _is_descendant(cls, candidate: Designation, ancestor: Designation) -> bool:
        current = candidate
        seen: set[UUID] = set()
        while current is not None:
            if current.id == ancestor.id:
                return True
            if current.id in seen:
                break
            seen.add(current.id)
            current = current.parent
        return False

    @classmethod
    def _paginate(cls, qs, *, page: int, page_size: int, serialize) -> dict:
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 20)))
        total = qs.count()
        start = (page - 1) * page_size
        items = [serialize(row) for row in qs[start : start + page_size]]
        return {
            'items': items,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': max(1, (total + page_size - 1) // page_size),
            },
        }

