"""Employee document upload, approval, and policy compliance."""

from __future__ import annotations

import hashlib
import mimetypes
from datetime import date
from pathlib import Path
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.authentication.models import User
from apps.core.exceptions import (
    NotFoundServiceError,
    PermissionDeniedServiceError,
    ValidationServiceError,
)
from apps.organization.models import (
    DocumentDefinition,
    DocumentPolicy,
    Employee,
    EmployeeDocument,
    File,
    OrganizationMembership,
)
from apps.organization.services.workspace import WorkspaceService

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    '.pdf',
    '.png',
    '.jpg',
    '.jpeg',
    '.webp',
    '.doc',
    '.docx',
    '.xls',
    '.xlsx',
}


class EmployeeDocumentService:
    """CRUD and compliance checks for employee documents."""

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        if not cls._is_admin_membership(membership, user):
            raise PermissionDeniedServiceError(
                'Only organization admins can manage employee documents.',
                code='not_organization_admin',
            )
        return membership

    @classmethod
    def _is_admin_membership(cls, membership: OrganizationMembership, user: User) -> bool:
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        return is_owner or access_name in {'admin', 'administrator'}

    @classmethod
    def _get_employee(cls, *, organization, employee_id: str | UUID) -> Employee:
        employee = (
            Employee.objects.select_related('employee_type')
            .filter(id=employee_id, organization=organization)
            .first()
        )
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')
        return employee

    @classmethod
    def _file_url(cls, file_obj: File) -> str:
        from django.conf import settings

        name = getattr(file_obj.file, 'name', '') or ''
        if not name:
            return ''
        if name.startswith('http://') or name.startswith('https://'):
            return name
        media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else f'{settings.MEDIA_URL}/'
        origin = settings.PUBLIC_API_ORIGIN.rstrip('/')
        return f'{origin}{media_url}{name.lstrip("/")}'

    @classmethod
    def serialize_document(cls, item: EmployeeDocument) -> dict:
        file_obj = item.file
        document = item.document
        return {
            'id': str(item.id),
            'employee_id': str(item.employee_id),
            'document_id': str(item.document_id),
            'document_name': document.name if document else None,
            'category_id': str(document.category_id) if document and document.category_id else None,
            'category_name': document.category.name if document and document.category_id else None,
            'file_id': str(item.file_id),
            'file_name': file_obj.original_name if file_obj else None,
            'file_url': cls._file_url(file_obj) if file_obj else '',
            'file_size': file_obj.file_size if file_obj else 0,
            'mime_type': file_obj.mime_type if file_obj else '',
            'issue_date': item.issue_date.isoformat() if item.issue_date else None,
            'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
            'status': item.status,
            'remarks': item.remarks,
            'verified_by_id': str(item.verified_by_id) if item.verified_by_id else None,
            'verified_by_name': (
                (item.verified_by.full_name or item.verified_by.email)
                if item.verified_by_id and item.verified_by
                else None
            ),
            'verified_at': item.verified_at.isoformat() if item.verified_at else None,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def list_documents(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
    ) -> list[dict]:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        employee = cls._get_employee(
            organization=membership.branch.organization,
            employee_id=employee_id,
        )
        rows = (
            EmployeeDocument.objects.select_related(
                'document',
                'document__category',
                'file',
                'verified_by',
            )
            .filter(employee=employee, file__is_deleted=False)
            .order_by('-created_at')
        )
        return [cls.serialize_document(row) for row in rows]

    @classmethod
    def _store_file(cls, *, organization, uploaded, user: User) -> File:
        original_name = Path(getattr(uploaded, 'name', '') or 'document').name
        extension = Path(original_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationServiceError(
                'Unsupported file type. Upload PDF, image, or Office documents.',
                code='invalid_file_type',
            )
        size = int(getattr(uploaded, 'size', 0) or 0)
        if size <= 0:
            raise ValidationServiceError('Uploaded file is empty.', code='empty_file')
        if size > MAX_DOCUMENT_BYTES:
            raise ValidationServiceError('File must be 10 MB or smaller.', code='file_too_large')

        mime_type = getattr(uploaded, 'content_type', '') or mimetypes.guess_type(original_name)[0] or ''
        checksum = ''
        try:
            digest = hashlib.sha256()
            for chunk in uploaded.chunks():
                digest.update(chunk)
            checksum = digest.hexdigest()
            uploaded.seek(0)
        except Exception:
            checksum = ''

        return File.objects.create(
            organization=organization,
            file=uploaded,
            original_name=original_name[:255],
            extension=extension.lstrip('.')[:20],
            mime_type=(mime_type or 'application/octet-stream')[:100],
            file_size=size,
            checksum=checksum,
            is_active=True,
            is_deleted=False,
            created_by=user,
            updated_by=user,
        )

    @classmethod
    @transaction.atomic
    def upload_document(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        document_id: str | UUID,
        uploaded,
        issue_date=None,
        expiry_date=None,
        remarks: str = '',
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        is_admin = cls._is_admin_membership(membership, user)
        is_self = employee.user_id == user.id
        if not is_admin and not is_self:
            raise PermissionDeniedServiceError(
                'You can only upload documents for yourself.',
                code='not_allowed',
            )

        from django.db.models import Q

        definition = DocumentDefinition.objects.filter(
            Q(organization=organization) | Q(organization__isnull=True),
            id=document_id,
            is_active=True,
        ).first()
        if definition is None:
            raise NotFoundServiceError('Document type not found.', code='document_not_found')

        file_obj = cls._store_file(organization=organization, uploaded=uploaded, user=user)

        if is_admin:
            status = EmployeeDocument.Status.APPROVED
            cleaned_remarks = (remarks or '').strip() or 'Uploaded by admin'
            verified_by = user
            verified_at = timezone.now()
        else:
            status = EmployeeDocument.Status.PENDING
            cleaned_remarks = (remarks or '').strip()
            verified_by = None
            verified_at = None

        item = EmployeeDocument.objects.create(
            employee=employee,
            document=definition,
            file=file_obj,
            issue_date=issue_date,
            expiry_date=expiry_date,
            status=status,
            remarks=cleaned_remarks,
            verified_by=verified_by,
            verified_at=verified_at,
            created_by=user,
            updated_by=user,
        )
        item = (
            EmployeeDocument.objects.select_related(
                'document',
                'document__category',
                'file',
                'verified_by',
            )
            .get(id=item.id)
        )
        return cls.serialize_document(item)

    @classmethod
    @transaction.atomic
    def review_document(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        document_row_id: str | UUID,
        approve: bool,
        remarks: str = '',
    ) -> dict:
        membership = cls.require_admin(user, branch_id)
        employee = cls._get_employee(
            organization=membership.branch.organization,
            employee_id=employee_id,
        )
        item = (
            EmployeeDocument.objects.select_related(
                'document',
                'document__category',
                'file',
                'verified_by',
            )
            .filter(id=document_row_id, employee=employee)
            .first()
        )
        if item is None:
            raise NotFoundServiceError('Employee document not found.', code='employee_document_not_found')
        if item.status != EmployeeDocument.Status.PENDING:
            raise ValidationServiceError(
                'Only pending documents can be reviewed.',
                code='invalid_document_status',
            )

        item.status = (
            EmployeeDocument.Status.APPROVED if approve else EmployeeDocument.Status.REJECTED
        )
        note = (remarks or '').strip()
        if note:
            item.remarks = note
        elif not approve and not item.remarks:
            item.remarks = 'Rejected by admin'
        item.verified_by = user
        item.verified_at = timezone.now()
        item.updated_by = user
        item.save()
        return cls.serialize_document(item)

    @classmethod
    @transaction.atomic
    def delete_document(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        document_row_id: str | UUID,
    ) -> None:
        membership = cls.require_admin(user, branch_id)
        employee = cls._get_employee(
            organization=membership.branch.organization,
            employee_id=employee_id,
        )
        item = EmployeeDocument.objects.select_related('file').filter(
            id=document_row_id,
            employee=employee,
        ).first()
        if item is None:
            raise NotFoundServiceError('Employee document not found.', code='employee_document_not_found')
        file_obj = item.file
        item.delete()
        if file_obj and not file_obj.employee_documents.exists():
            file_obj.is_deleted = True
            file_obj.is_active = False
            file_obj.updated_by = user
            file_obj.save(update_fields=['is_deleted', 'is_active', 'updated_by', 'updated_at'])

    @classmethod
    def _resolve_policy(cls, *, organization, employee: Employee) -> DocumentPolicy | None:
        if not employee.employee_type_id:
            return None
        qs = (
            DocumentPolicy.objects.filter(
                organization=organization,
                employee_type_id=employee.employee_type_id,
                is_active=True,
            )
            .select_related('employee_type')
            .prefetch_related('items__document__category')
            .order_by('-is_default', 'name')
        )
        return qs.first()

    @classmethod
    def check_policy_compliance(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
    ) -> dict:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        organization = membership.branch.organization
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        policy = cls._resolve_policy(organization=organization, employee=employee)

        uploads = list(
            EmployeeDocument.objects.select_related(
                'document',
                'document__category',
                'file',
                'verified_by',
            )
            .filter(employee=employee, file__is_deleted=False)
            .order_by('-created_at')
        )
        by_definition: dict[str, list[EmployeeDocument]] = {}
        for row in uploads:
            by_definition.setdefault(str(row.document_id), []).append(row)

        if policy is None:
            return {
                'policy': None,
                'overall_status': 'no_policy',
                'message': (
                    'No active document policy for this employee type.'
                    if employee.employee_type_id
                    else 'Assign an employee type to evaluate document policy.'
                ),
                'summary': {
                    'required': 0,
                    'approved': 0,
                    'pending': 0,
                    'missing': 0,
                    'expired': 0,
                    'rejected': 0,
                    'optional': 0,
                },
                'items': [],
                'pending': [cls.serialize_document(row) for row in uploads if row.status == EmployeeDocument.Status.PENDING],
                'uploads': [cls.serialize_document(row) for row in uploads],
            }

        today = date.today()
        items_payload = []
        summary = {
            'required': 0,
            'approved': 0,
            'pending': 0,
            'missing': 0,
            'expired': 0,
            'rejected': 0,
            'optional': 0,
        }

        for policy_item in sorted(policy.items.all(), key=lambda row: (row.display_order, str(row.id))):
            definition = policy_item.document
            rows = by_definition.get(str(definition.id), [])
            latest = rows[0] if rows else None
            status = 'missing'
            if latest is None:
                status = 'missing' if policy_item.is_required else 'optional_missing'
            elif latest.status == EmployeeDocument.Status.PENDING:
                status = 'pending'
            elif latest.status == EmployeeDocument.Status.REJECTED:
                status = 'rejected'
            elif latest.status == EmployeeDocument.Status.APPROVED:
                if (
                    policy_item.requires_expiry
                    and latest.expiry_date
                    and latest.expiry_date < today
                ):
                    status = 'expired'
                else:
                    status = 'approved'
            else:
                status = latest.status

            if policy_item.is_required:
                summary['required'] += 1
                if status == 'approved':
                    summary['approved'] += 1
                elif status == 'pending':
                    summary['pending'] += 1
                elif status == 'expired':
                    summary['expired'] += 1
                elif status == 'rejected':
                    summary['rejected'] += 1
                else:
                    summary['missing'] += 1
            else:
                summary['optional'] += 1
                if status == 'approved':
                    summary['approved'] += 1
                elif status == 'pending':
                    summary['pending'] += 1

            items_payload.append(
                {
                    'policy_item_id': str(policy_item.id),
                    'document_id': str(definition.id),
                    'document_name': definition.name,
                    'category_name': definition.category.name if definition.category_id else None,
                    'is_required': policy_item.is_required,
                    'allow_multiple': policy_item.allow_multiple,
                    'verification_required': policy_item.verification_required,
                    'requires_expiry': policy_item.requires_expiry,
                    'display_order': policy_item.display_order,
                    'status': status,
                    'latest_document': cls.serialize_document(latest) if latest else None,
                    'upload_count': len(rows),
                }
            )

        if summary['required'] == 0:
            overall = 'compliant'
            message = 'Policy has no required documents.'
        elif summary['missing'] or summary['rejected'] or summary['expired']:
            overall = 'incomplete'
            message = 'Some required documents are missing, rejected, or expired.'
        elif summary['pending']:
            overall = 'pending_review'
            message = 'Required documents are uploaded and waiting for approval.'
        else:
            overall = 'compliant'
            message = 'All required documents are approved.'

        return {
            'policy': {
                'id': str(policy.id),
                'name': policy.name,
                'description': policy.description,
                'is_default': policy.is_default,
                'employee_type_id': str(policy.employee_type_id),
                'employee_type_name': (
                    policy.employee_type.name if policy.employee_type_id else None
                ),
            },
            'overall_status': overall,
            'message': message,
            'summary': summary,
            'items': items_payload,
            'pending': [
                cls.serialize_document(row)
                for row in uploads
                if row.status == EmployeeDocument.Status.PENDING
            ],
            'uploads': [cls.serialize_document(row) for row in uploads],
        }
