"""Employee attendance daily summaries, sessions, and breaks."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from django.db.models import Prefetch, Q
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
from apps.attendance.models import (
    Attendance,
    AttendanceBreak,
    AttendanceSession,
)
from apps.organizations.services.workspace_service import WorkspaceService


class AttendanceApprovalService:
    """Manual attendance approval inbox and review."""

    @classmethod
    def list_approvals_inbox(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        status: str | None = None,
    ) -> dict:
        from apps.attendance.services.attendance_service import AttendanceService
        membership = AttendanceService._membership(user, branch_id)
        organization = AttendanceService._organization(membership)
        status_filter = (status or Attendance.ApprovalStatus.PENDING).strip().lower()
        if status_filter not in {
            Attendance.ApprovalStatus.PENDING,
            Attendance.ApprovalStatus.APPROVED,
            Attendance.ApprovalStatus.REJECTED,
            'all',
        }:
            status_filter = Attendance.ApprovalStatus.PENDING

        qs = (
            Attendance.objects.filter(organization=organization, is_manual=True)
            .exclude(approval_status=Attendance.ApprovalStatus.NOT_REQUIRED)
            .select_related(
                'employee',
                'employee__designation',
                'employee__reporting_manager',
                'employee__reporting_manager__reporting_manager',
                'employee__designation__parent',
                'employee__designation__parent__parent',
                'approved_by',
            )
            .prefetch_related(AttendanceService._sessions_prefetch())
            .order_by('-attendance_date', '-updated_at')
        )
        if status_filter != 'all':
            qs = qs.filter(approval_status=status_filter)

        pending_qs = Attendance.objects.filter(
            organization=organization,
            is_manual=True,
            approval_status=Attendance.ApprovalStatus.PENDING,
        ).select_related(
            'employee',
            'employee__reporting_manager',
            'employee__reporting_manager__reporting_manager',
            'employee__designation',
            'employee__designation__parent',
            'employee__designation__parent__parent',
        )

        pending_for_me = 0
        for row in pending_qs[:300]:
            if AttendanceService.can_review_attendance(user=user, employee=row.employee):
                pending_for_me += 1

        items: list[dict] = []
        for row in qs[:300]:
            employee = row.employee
            in_scope = (
                AttendanceService.can_review_attendance(user=user, employee=employee)
                or row.approved_by_id == user.id
            )
            if not in_scope:
                continue
            can_review = (
                row.approval_status == Attendance.ApprovalStatus.PENDING
                and AttendanceService.can_review_attendance(user=user, employee=employee)
            )
            items.append(
                AttendanceService.serialize_attendance(
                    row,
                    can_review=can_review,
                    expected_approver=AttendanceService.expected_approver(employee),
                )
            )

        return {
            'pending_count': pending_for_me,
            'items': items,
        }


    @classmethod
    @transaction.atomic
    def review_attendance(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        attendance_id: str | UUID,
        approve: bool,
        remarks: str = '',
    ) -> dict:
        from apps.attendance.services.attendance_service import AttendanceService
        membership = AttendanceService._membership(user, branch_id)
        organization = AttendanceService._organization(membership)
        attendance = (
            Attendance.objects.filter(id=attendance_id, organization=organization)
            .select_related(
                'employee',
                'employee__designation',
                'employee__reporting_manager',
                'employee__reporting_manager__reporting_manager',
                'employee__designation__parent',
                'employee__designation__parent__parent',
            )
            .prefetch_related(AttendanceService._sessions_prefetch())
            .first()
        )
        if attendance is None:
            raise NotFoundServiceError('Attendance record not found.', code='attendance_not_found')
        if not attendance.is_manual:
            raise ValidationServiceError(
                'Only manual attendance entries require approval.',
                code='attendance_not_manual',
            )
        if attendance.approval_status != Attendance.ApprovalStatus.PENDING:
            raise ConflictServiceError(
                'This attendance entry is not pending approval.',
                code='attendance_not_pending',
            )

        if not AttendanceService.can_review_attendance(user=user, employee=attendance.employee):
            raise PermissionDeniedServiceError(
                'Only the reporting manager can review this attendance entry.',
                code='not_attendance_approver',
            )

        attendance.approved_by = user
        attendance.approved_at = timezone.now()
        attendance.approval_remarks = (remarks or '')[:2000]
        attendance.updated_by = user

        pending_checkout_sessions = list(
            AttendanceSession.objects.filter(
                attendance=attendance,
                remarks__contains=AttendanceService.PENDING_CHECKOUT_MARKER,
            )
        )

        if approve:
            for session in pending_checkout_sessions:
                session.remarks = AttendanceService._without_pending_checkout_marker(session.remarks)
                session.updated_by = user
                session.save(update_fields=['remarks', 'updated_by', 'updated_at'])
            attendance.approval_status = Attendance.ApprovalStatus.APPROVED
            attendance.save(
                update_fields=[
                    'approval_status',
                    'approved_by',
                    'approved_at',
                    'approval_remarks',
                    'updated_by',
                    'updated_at',
                ]
            )
        else:
            attendance.approval_status = Attendance.ApprovalStatus.REJECTED
            attendance.is_manual = False
            if pending_checkout_sessions:
                # Missing-logout adjustment: reopen the original punch session.
                for session in pending_checkout_sessions:
                    session.check_out = None
                    session.worked_hours = None
                    session.remarks = AttendanceService._without_pending_checkout_marker(session.remarks)
                    session.updated_by = user
                    session.save(
                        update_fields=[
                            'check_out',
                            'worked_hours',
                            'remarks',
                            'updated_by',
                            'updated_at',
                        ]
                    )
            else:
                AttendanceSession.objects.filter(
                    attendance=attendance,
                    source=AttendanceSession.Source.MANUAL,
                ).delete()
            attendance.save(
                update_fields=[
                    'approval_status',
                    'is_manual',
                    'approved_by',
                    'approved_at',
                    'approval_remarks',
                    'updated_by',
                    'updated_at',
                ]
            )
            attendance = AttendanceService._recompute(attendance, user=user)

        attendance = (
            Attendance.objects.filter(id=attendance.id)
            .select_related('employee', 'employee__designation', 'approved_by')
            .prefetch_related(AttendanceService._sessions_prefetch())
            .get()
        )
        return AttendanceService.serialize_attendance(
            attendance,
            can_review=False,
            expected_approver=AttendanceService.expected_approver(attendance.employee),
        )
