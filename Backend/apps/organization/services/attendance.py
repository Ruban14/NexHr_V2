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
from apps.organization.services.leaves import LeaveService
from apps.organization.services.workspace import WorkspaceService


class AttendanceService:
    """Manage attendance punch records and daily summaries."""

    @classmethod
    def require_admin(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        membership = WorkspaceService.get_membership(user, branch_id=branch_id)
        access_name = (membership.access_type.name if membership.access_type else '').lower()
        is_owner = membership.branch.organization.owner_id == user.id
        if not is_owner and access_name not in {'admin', 'administrator'}:
            raise PermissionDeniedServiceError(
                'Only organization admins can manage attendance records.',
                code='not_organization_admin',
            )
        return membership

    @classmethod
    def _membership(cls, user: User, branch_id: str | UUID | None) -> OrganizationMembership:
        return WorkspaceService.get_membership(user, branch_id=branch_id)

    @classmethod
    def _organization(cls, membership: OrganizationMembership):
        return membership.branch.organization

    @classmethod
    def _get_employee(cls, *, organization, employee_id: str | UUID) -> Employee:
        employee = (
            Employee.objects.filter(id=employee_id, organization=organization)
            .select_related(
                'designation',
                'designation__parent',
                'designation__parent__parent',
                'reporting_manager',
                'reporting_manager__reporting_manager',
            )
            .first()
        )
        if employee is None:
            raise NotFoundServiceError('Employee not found.', code='employee_not_found')
        return employee

    @classmethod
    def _employee_for_user(cls, *, organization, user: User) -> Employee:
        employee = (
            Employee.objects.filter(organization=organization, user=user)
            .select_related(
                'designation',
                'designation__parent',
                'designation__parent__parent',
                'reporting_manager',
                'reporting_manager__reporting_manager',
            )
            .first()
        )
        if employee is None:
            raise ValidationServiceError(
                'No employee profile is linked to your account.',
                code='employee_profile_missing',
            )
        return employee

    @classmethod
    def _assert_own_employee(
        cls,
        *,
        user: User,
        employee: Employee,
        action: str = 'manage attendance for',
    ) -> None:
        """Attendance punch/manual/history is self-service only."""
        if employee.user_id and employee.user_id == user.id:
            return
        raise PermissionDeniedServiceError(
            f'You can only {action} your own profile.',
            code='attendance_self_only',
        )

    @classmethod
    def _assert_can_submit_manual(
        cls,
        *,
        user: User,
        membership: OrganizationMembership,
        employee: Employee,
    ) -> None:
        del membership  # kept for call-site compatibility
        cls._assert_own_employee(user=user, employee=employee, action='submit manual attendance for')

    @classmethod
    def _assert_can_punch(
        cls,
        *,
        user: User,
        membership: OrganizationMembership,
        employee: Employee,
    ) -> None:
        del membership  # kept for call-site compatibility
        cls._assert_own_employee(user=user, employee=employee, action='punch attendance for')

    @classmethod
    def _org_tz(cls, organization) -> ZoneInfo:
        name = (getattr(organization, 'timezone', None) or 'Asia/Kolkata').strip() or 'Asia/Kolkata'
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            return ZoneInfo('Asia/Kolkata')

    @classmethod
    def _local_now(cls, organization) -> datetime:
        return timezone.now().astimezone(cls._org_tz(organization))

    @classmethod
    def _local_today(cls, organization) -> date:
        return cls._local_now(organization).date()

    @classmethod
    def _parse_date(cls, value: str | date | None, *, field: str) -> date | None:
        if value in (None, ''):
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError as exc:
            raise ValidationServiceError(f'Invalid date for {field}.', code='invalid_date') from exc

    @classmethod
    def _parse_datetime(cls, value, *, organization, field: str) -> datetime | None:
        if value in (None, ''):
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            raw = str(value).strip()
            try:
                if len(raw) == 10:
                    return datetime.fromisoformat(f'{raw}T00:00:00').replace(
                        tzinfo=cls._org_tz(organization)
                    )
                dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            except ValueError as exc:
                raise ValidationServiceError(
                    f'Invalid datetime for {field}.',
                    code='invalid_datetime',
                ) from exc
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, cls._org_tz(organization))
        return dt

    @classmethod
    def _duration_hours(cls, value: timedelta | None) -> str | None:
        if value is None:
            return None
        hours = value.total_seconds() / 3600
        return f'{hours:.2f}'

    @classmethod
    def _employee_display_name(cls, employee: Employee | None) -> str | None:
        if employee is None:
            return None
        return (
            employee.display_name
            or ' '.join(part for part in [employee.first_name, employee.last_name] if part).strip()
            or employee.email
            or None
        )

    @classmethod
    def _sessions_prefetch(cls):
        return Prefetch(
            'sessions',
            queryset=AttendanceSession.objects.prefetch_related('breaks').order_by('check_in'),
        )

    @classmethod
    def _get_or_create_day(
        cls,
        *,
        organization,
        employee: Employee,
        attendance_date: date,
        user: User,
        status: str | None = None,
    ) -> Attendance:
        defaults = {
            'organization': organization,
            'status': status or Attendance.Status.PRESENT,
            'created_by': user,
            'updated_by': user,
        }
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            attendance_date=attendance_date,
            defaults=defaults,
        )
        if not created and status and attendance.status != status:
            attendance.status = status
            attendance.updated_by = user
            attendance.save(update_fields=['status', 'updated_by', 'updated_at'])
        return attendance

    @classmethod
    def _open_session(cls, attendance: Attendance) -> AttendanceSession | None:
        return (
            AttendanceSession.objects.filter(attendance=attendance, check_out__isnull=True)
            .order_by('-check_in')
            .first()
        )

    @classmethod
    def _open_break(cls, session: AttendanceSession) -> AttendanceBreak | None:
        return (
            AttendanceBreak.objects.filter(session=session, break_end__isnull=True)
            .order_by('-break_start')
            .first()
        )

    @classmethod
    def _recompute(cls, attendance: Attendance, *, user: User) -> Attendance:
        sessions = list(
            AttendanceSession.objects.filter(attendance=attendance)
            .prefetch_related('breaks')
            .order_by('check_in')
        )
        total_worked = timedelta(0)
        total_break = timedelta(0)
        first_in = None
        last_out = None

        for session in sessions:
            break_total = timedelta(0)
            for item in session.breaks.all():
                if item.break_end and item.break_start:
                    duration = item.break_end - item.break_start
                    if duration.total_seconds() < 0:
                        duration = timedelta(0)
                    if item.break_duration != duration:
                        item.break_duration = duration
                        item.updated_by = user
                        item.save(update_fields=['break_duration', 'updated_by', 'updated_at'])
                    break_total += duration
                elif item.break_duration:
                    break_total += item.break_duration

            total_break += break_total
            if first_in is None or session.check_in < first_in:
                first_in = session.check_in
            if session.check_out:
                if last_out is None or session.check_out > last_out:
                    last_out = session.check_out
                worked = session.check_out - session.check_in - break_total
                if worked.total_seconds() < 0:
                    worked = timedelta(0)
            else:
                worked = None

            if session.worked_hours != worked:
                session.worked_hours = worked
                session.updated_by = user
                session.save(update_fields=['worked_hours', 'updated_by', 'updated_at'])
            if worked is not None:
                total_worked += worked

        attendance.first_check_in = first_in
        attendance.last_check_out = last_out
        attendance.total_worked_hours = total_worked if sessions else None
        attendance.total_break_hours = total_break if sessions else None
        attendance.updated_by = user
        attendance.save(
            update_fields=[
                'first_check_in',
                'last_check_out',
                'total_worked_hours',
                'total_break_hours',
                'updated_by',
                'updated_at',
            ]
        )
        return attendance

    @classmethod
    def serialize_break(cls, item: AttendanceBreak) -> dict:
        return {
            'id': str(item.id),
            'session_id': str(item.session_id),
            'break_start': item.break_start.isoformat() if item.break_start else None,
            'break_end': item.break_end.isoformat() if item.break_end else None,
            'break_duration_hours': cls._duration_hours(item.break_duration),
            'remarks': item.remarks,
            'is_open': item.break_end is None,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_session(cls, item: AttendanceSession) -> dict:
        breaks = (
            list(item.breaks.all())
            if hasattr(item, '_prefetched_objects_cache')
            else list(item.breaks.order_by('break_start'))
        )
        return {
            'id': str(item.id),
            'attendance_id': str(item.attendance_id),
            'check_in': item.check_in.isoformat() if item.check_in else None,
            'check_out': item.check_out.isoformat() if item.check_out else None,
            'worked_hours': cls._duration_hours(item.worked_hours),
            'source': item.source,
            'remarks': item.remarks,
            'is_open': item.check_out is None,
            'breaks': [cls.serialize_break(row) for row in breaks],
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def serialize_attendance(
        cls,
        item: Attendance,
        *,
        include_sessions: bool = True,
        can_review: bool | None = None,
        expected_approver: Employee | None = None,
    ) -> dict:
        employee = getattr(item, 'employee', None)
        sessions = []
        open_session = False
        on_break = False
        if include_sessions:
            if hasattr(item, '_prefetched_objects_cache') and 'sessions' in item._prefetched_objects_cache:
                session_rows = list(item.sessions.all())
            else:
                session_rows = list(
                    item.sessions.prefetch_related('breaks').order_by('check_in')
                )
            sessions = [cls.serialize_session(row) for row in session_rows]
            for row in session_rows:
                if row.check_out is None:
                    open_session = True
                    if any(b.break_end is None for b in row.breaks.all()):
                        on_break = True
                    break

        expected_name = None
        expected_id = None
        if expected_approver is not None:
            expected_id = str(expected_approver.id)
            expected_name = cls._employee_display_name(expected_approver)

        return {
            'id': str(item.id),
            'organization_id': str(item.organization_id),
            'employee_id': str(item.employee_id),
            'employee_name': cls._employee_display_name(employee),
            'employee_code': employee.employee_code if employee is not None else None,
            'employee_designation_name': (
                employee.designation.name
                if employee is not None and getattr(employee, 'designation', None) is not None
                else None
            ),
            'attendance_date': item.attendance_date.isoformat() if item.attendance_date else None,
            'first_check_in': item.first_check_in.isoformat() if item.first_check_in else None,
            'last_check_out': item.last_check_out.isoformat() if item.last_check_out else None,
            'total_worked_hours': cls._duration_hours(item.total_worked_hours),
            'total_break_hours': cls._duration_hours(item.total_break_hours),
            'overtime_hours': cls._duration_hours(item.overtime_hours),
            'status': item.status,
            'is_manual': bool(item.is_manual),
            'approval_status': item.approval_status,
            'approved_by_id': str(item.approved_by_id) if item.approved_by_id else None,
            'approved_by_name': (
                item.approved_by.full_name or item.approved_by.email if item.approved_by else None
            ),
            'approved_at': item.approved_at.isoformat() if item.approved_at else None,
            'approval_remarks': item.approval_remarks,
            'expected_approver_id': expected_id,
            'expected_approver_name': expected_name,
            'can_review': (
                bool(can_review)
                if item.approval_status == Attendance.ApprovalStatus.PENDING
                else False
            ),
            'remarks': item.remarks,
            'has_open_session': open_session,
            'on_break': on_break,
            'sessions': sessions if include_sessions else [],
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

    @classmethod
    def list_org_attendance(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        date_value: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status_filter: str | None = None,
        employee_id: str | None = None,
        search: str | None = None,
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        self_employee = cls._employee_for_user(organization=organization, user=user)
        today = cls._local_today(organization)

        day = cls._parse_date(date_value, field='date')
        start = cls._parse_date(date_from, field='date_from')
        end = cls._parse_date(date_to, field='date_to')
        if day is None and start is None and end is None:
            day = today

        if employee_id and str(employee_id) != str(self_employee.id):
            raise PermissionDeniedServiceError(
                'You can only view attendance for your own profile.',
                code='attendance_self_only',
            )

        qs = (
            Attendance.objects.filter(organization=organization, employee=self_employee)
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .order_by('-attendance_date', 'employee__display_name')
        )
        if day is not None:
            qs = qs.filter(attendance_date=day)
        else:
            if start is not None:
                qs = qs.filter(attendance_date__gte=start)
            if end is not None:
                qs = qs.filter(attendance_date__lte=end)

        if status_filter and status_filter != 'all':
            qs = qs.filter(status=status_filter)
        if search and search.strip():
            term = search.strip()
            qs = qs.filter(
                Q(employee__display_name__icontains=term)
                | Q(employee__first_name__icontains=term)
                | Q(employee__last_name__icontains=term)
                | Q(employee__employee_code__icontains=term)
                | Q(employee__email__icontains=term)
                | Q(remarks__icontains=term)
            )

        items = [cls.serialize_attendance(row) for row in qs[:500]]
        present_count = sum(
            1
            for row in items
            if row['status'] == Attendance.Status.PRESENT
            and row['approval_status']
            in {
                Attendance.ApprovalStatus.NOT_REQUIRED,
                Attendance.ApprovalStatus.APPROVED,
            }
        )
        return {
            'date': (day or today).isoformat(),
            'present_count': present_count,
            'total_count': len(items),
            'items': items,
        }

    @classmethod
    def list_employee_attendance(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        cls._assert_own_employee(user=user, employee=employee, action='view attendance for')

        today = cls._local_today(organization)
        start = cls._parse_date(date_from, field='date_from') or (today - timedelta(days=30))
        end = cls._parse_date(date_to, field='date_to') or today
        qs = (
            Attendance.objects.filter(
                organization=organization,
                employee=employee,
                attendance_date__gte=start,
                attendance_date__lte=end,
            )
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .order_by('-attendance_date')
        )
        return [cls.serialize_attendance(row) for row in qs]

    @classmethod
    def list_employee_sessions(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Flattened check-in / check-out sessions for an employee."""
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        cls._assert_own_employee(user=user, employee=employee, action='view attendance for')
        today = cls._local_today(organization)
        start = cls._parse_date(date_from, field='date_from') or (today - timedelta(days=30))
        end = cls._parse_date(date_to, field='date_to') or today

        sessions = (
            AttendanceSession.objects.filter(
                attendance__organization=organization,
                attendance__employee=employee,
                attendance__attendance_date__gte=start,
                attendance__attendance_date__lte=end,
            )
            .select_related('attendance', 'attendance__employee', 'attendance__employee__designation')
            .prefetch_related('breaks')
            .order_by('-check_in')
        )
        rows: list[dict] = []
        for session in sessions:
            payload = cls.serialize_session(session)
            attendance = session.attendance
            payload.update(
                {
                    'attendance_date': (
                        attendance.attendance_date.isoformat() if attendance.attendance_date else None
                    ),
                    'attendance_status': attendance.status,
                    'approval_status': attendance.approval_status,
                    'is_manual_day': bool(attendance.is_manual),
                    'employee_id': str(attendance.employee_id),
                    'employee_name': cls._employee_display_name(attendance.employee),
                    'employee_code': attendance.employee.employee_code,
                }
            )
            rows.append(payload)
        return rows

    @classmethod
    def get_today(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID | None = None,
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        if employee_id:
            employee = cls._get_employee(organization=organization, employee_id=employee_id)
            cls._assert_own_employee(user=user, employee=employee, action='view attendance for')
        else:
            employee = cls._employee_for_user(organization=organization, user=user)

        today = cls._local_today(organization)
        attendance = (
            Attendance.objects.filter(
                organization=organization,
                employee=employee,
                attendance_date=today,
            )
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .first()
        )
        if attendance is None:
            return {
                'id': None,
                'organization_id': str(organization.id),
                'employee_id': str(employee.id),
                'employee_name': cls._employee_display_name(employee),
                'employee_code': employee.employee_code,
                'employee_designation_name': (
                    employee.designation.name if employee.designation_id else None
                ),
                'attendance_date': today.isoformat(),
                'first_check_in': None,
                'last_check_out': None,
                'total_worked_hours': None,
                'total_break_hours': None,
                'overtime_hours': None,
                'status': None,
                'remarks': '',
                'has_open_session': False,
                'on_break': False,
                'sessions': [],
                'created_at': None,
                'updated_at': None,
            }
        return cls.serialize_attendance(attendance)

    @classmethod
    def get_detail(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        attendance_id: str | UUID,
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        attendance = (
            Attendance.objects.filter(id=attendance_id, organization=organization)
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .first()
        )
        if attendance is None:
            raise NotFoundServiceError('Attendance record not found.', code='attendance_not_found')
        cls._assert_own_employee(
            user=user,
            employee=attendance.employee,
            action='view attendance for',
        )
        return cls.serialize_attendance(attendance)

    @classmethod
    @transaction.atomic
    def check_in(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID | None = None,
        remarks: str = '',
        source: str = AttendanceSession.Source.WEB,
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        if employee_id:
            employee = cls._get_employee(organization=organization, employee_id=employee_id)
        else:
            employee = cls._employee_for_user(organization=organization, user=user)
        cls._assert_can_punch(user=user, membership=membership, employee=employee)

        if source not in AttendanceSession.Source.values:
            source = AttendanceSession.Source.WEB

        today = cls._local_today(organization)
        now = timezone.now()
        attendance = cls._get_or_create_day(
            organization=organization,
            employee=employee,
            attendance_date=today,
            user=user,
            status=Attendance.Status.PRESENT,
        )
        open_session = cls._open_session(attendance)
        if open_session is not None:
            raise ConflictServiceError(
                'You already have an open attendance session. Check out first.',
                code='attendance_session_open',
            )

        AttendanceSession.objects.create(
            attendance=attendance,
            check_in=now,
            source=source,
            remarks=(remarks or '')[:255],
            created_by=user,
            updated_by=user,
        )
        attendance = cls._recompute(attendance, user=user)
        attendance = (
            Attendance.objects.filter(id=attendance.id)
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .get()
        )
        return cls.serialize_attendance(attendance)

    @classmethod
    @transaction.atomic
    def check_out(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID | None = None,
        remarks: str = '',
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        if employee_id:
            employee = cls._get_employee(organization=organization, employee_id=employee_id)
        else:
            employee = cls._employee_for_user(organization=organization, user=user)
        cls._assert_can_punch(user=user, membership=membership, employee=employee)

        today = cls._local_today(organization)
        attendance = Attendance.objects.filter(
            organization=organization,
            employee=employee,
            attendance_date=today,
        ).first()
        if attendance is None:
            raise ValidationServiceError(
                'No attendance record for today. Check in first.',
                code='attendance_missing',
            )

        session = cls._open_session(attendance)
        if session is None:
            raise ValidationServiceError(
                'No open session to check out.',
                code='attendance_session_closed',
            )

        open_break = cls._open_break(session)
        if open_break is not None:
            raise ConflictServiceError(
                'End your break before checking out.',
                code='attendance_break_open',
            )

        now = timezone.now()
        if now < session.check_in:
            raise ValidationServiceError(
                'Check-out cannot be before check-in.',
                code='invalid_check_out',
            )
        session.check_out = now
        if remarks:
            session.remarks = ((session.remarks + ' ' if session.remarks else '') + remarks)[:255]
        session.updated_by = user
        session.save(update_fields=['check_out', 'remarks', 'updated_by', 'updated_at'])

        attendance = cls._recompute(attendance, user=user)
        attendance = (
            Attendance.objects.filter(id=attendance.id)
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .get()
        )
        return cls.serialize_attendance(attendance)

    @classmethod
    @transaction.atomic
    def break_start(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID | None = None,
        remarks: str = '',
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        if employee_id:
            employee = cls._get_employee(organization=organization, employee_id=employee_id)
        else:
            employee = cls._employee_for_user(organization=organization, user=user)
        cls._assert_can_punch(user=user, membership=membership, employee=employee)

        today = cls._local_today(organization)
        attendance = Attendance.objects.filter(
            organization=organization,
            employee=employee,
            attendance_date=today,
        ).first()
        if attendance is None:
            raise ValidationServiceError(
                'No attendance record for today. Check in first.',
                code='attendance_missing',
            )
        session = cls._open_session(attendance)
        if session is None:
            raise ValidationServiceError(
                'Check in before starting a break.',
                code='attendance_session_closed',
            )
        if cls._open_break(session) is not None:
            raise ConflictServiceError(
                'A break is already in progress.',
                code='attendance_break_open',
            )

        AttendanceBreak.objects.create(
            session=session,
            break_start=timezone.now(),
            remarks=(remarks or '')[:255],
            created_by=user,
            updated_by=user,
        )
        attendance = (
            Attendance.objects.filter(id=attendance.id)
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .get()
        )
        return cls.serialize_attendance(attendance)

    @classmethod
    @transaction.atomic
    def break_end(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID | None = None,
        remarks: str = '',
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        if employee_id:
            employee = cls._get_employee(organization=organization, employee_id=employee_id)
        else:
            employee = cls._employee_for_user(organization=organization, user=user)
        cls._assert_can_punch(user=user, membership=membership, employee=employee)

        today = cls._local_today(organization)
        attendance = Attendance.objects.filter(
            organization=organization,
            employee=employee,
            attendance_date=today,
        ).first()
        if attendance is None:
            raise ValidationServiceError(
                'No attendance record for today.',
                code='attendance_missing',
            )
        session = cls._open_session(attendance)
        if session is None:
            raise ValidationServiceError(
                'No open session found.',
                code='attendance_session_closed',
            )
        open_break = cls._open_break(session)
        if open_break is None:
            raise ValidationServiceError(
                'No open break to end.',
                code='attendance_break_closed',
            )

        now = timezone.now()
        if now < open_break.break_start:
            raise ValidationServiceError(
                'Break end cannot be before break start.',
                code='invalid_break_end',
            )
        open_break.break_end = now
        open_break.break_duration = now - open_break.break_start
        if remarks:
            open_break.remarks = (
                (open_break.remarks + ' ' if open_break.remarks else '') + remarks
            )[:255]
        open_break.updated_by = user
        open_break.save(
            update_fields=['break_end', 'break_duration', 'remarks', 'updated_by', 'updated_at']
        )

        attendance = cls._recompute(attendance, user=user)
        attendance = (
            Attendance.objects.filter(id=attendance.id)
            .select_related('employee', 'employee__designation')
            .prefetch_related(cls._sessions_prefetch())
            .get()
        )
        return cls.serialize_attendance(attendance)

    @classmethod
    @transaction.atomic
    def manual_upsert(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        employee_id: str | UUID,
        payload: dict,
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
        employee = cls._get_employee(organization=organization, employee_id=employee_id)
        cls._assert_can_submit_manual(user=user, membership=membership, employee=employee)

        attendance_date = cls._parse_date(payload.get('attendance_date'), field='attendance_date')
        if attendance_date is None:
            raise ValidationServiceError(
                'Attendance date is required.',
                code='attendance_date_required',
            )

        status_value = (payload.get('status') or Attendance.Status.PRESENT).strip().lower()
        if status_value not in Attendance.Status.values:
            raise ValidationServiceError('Invalid attendance status.', code='invalid_status')

        check_in = cls._parse_datetime(
            payload.get('check_in'),
            organization=organization,
            field='check_in',
        )
        check_out = cls._parse_datetime(
            payload.get('check_out'),
            organization=organization,
            field='check_out',
        )
        if check_in is None:
            raise ValidationServiceError(
                'Check-in time is required for manual entry.',
                code='check_in_required',
            )
        if check_out and check_out < check_in:
            raise ValidationServiceError(
                'Check-out cannot be before check-in.',
                code='invalid_check_out',
            )

        existing = (
            Attendance.objects.select_for_update()
            .filter(employee=employee, attendance_date=attendance_date)
            .first()
        )
        if (
            existing is not None
            and existing.is_manual
            and existing.approval_status == Attendance.ApprovalStatus.APPROVED
        ):
            raise ValidationServiceError(
                'Manual attendance for this date is already approved and cannot be changed.',
                code='manual_already_approved',
            )

        if existing is not None:
            has_live_punches = (
                AttendanceSession.objects.filter(attendance=existing)
                .exclude(source=AttendanceSession.Source.MANUAL)
                .exists()
            )
            if has_live_punches:
                raise ValidationServiceError(
                    'Check-in/check-out already exists for this date. Manual adjustment is not allowed.',
                    code='manual_not_allowed_with_punches',
                )

        attendance = cls._get_or_create_day(
            organization=organization,
            employee=employee,
            attendance_date=attendance_date,
            user=user,
            status=status_value,
        )
        attendance.status = status_value
        attendance.remarks = (payload.get('remarks') or '')[:2000]
        attendance.is_manual = True
        attendance.approval_status = Attendance.ApprovalStatus.PENDING
        attendance.approved_by = None
        attendance.approved_at = None
        attendance.approval_remarks = ''
        attendance.updated_by = user
        attendance.save(
            update_fields=[
                'status',
                'remarks',
                'is_manual',
                'approval_status',
                'approved_by',
                'approved_at',
                'approval_remarks',
                'updated_by',
                'updated_at',
            ]
        )

        # Replace previous manual sessions only; keep live web/mobile punches.
        # One manual request per day — pending edits overwrite the existing session.
        AttendanceSession.objects.filter(
            attendance=attendance,
            source=AttendanceSession.Source.MANUAL,
        ).delete()
        AttendanceSession.objects.create(
            attendance=attendance,
            check_in=check_in,
            check_out=check_out,
            source=AttendanceSession.Source.MANUAL,
            remarks=(payload.get('session_remarks') or '')[:255],
            created_by=user,
            updated_by=user,
        )

        attendance = cls._recompute(attendance, user=user)
        attendance = (
            Attendance.objects.filter(id=attendance.id)
            .select_related(
                'employee',
                'employee__designation',
                'employee__reporting_manager',
                'approved_by',
            )
            .prefetch_related(cls._sessions_prefetch())
            .get()
        )
        return cls.serialize_attendance(
            attendance,
            expected_approver=LeaveService.expected_approver(employee),
        )

    @classmethod
    def list_approvals_inbox(
        cls,
        *,
        user: User,
        branch_id: str | UUID | None,
        status: str | None = None,
    ) -> dict:
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
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
            .prefetch_related(cls._sessions_prefetch())
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
            if LeaveService.can_review_leave(
                user=user,
                employee=row.employee,
                membership=membership,
            ):
                pending_for_me += 1

        items: list[dict] = []
        for row in qs[:300]:
            employee = row.employee
            in_scope = LeaveService.can_review_leave(
                user=user,
                employee=employee,
                membership=membership,
            ) or row.approved_by_id == user.id
            if not in_scope:
                continue
            can_review = (
                row.approval_status == Attendance.ApprovalStatus.PENDING
                and LeaveService.can_review_leave(
                    user=user,
                    employee=employee,
                    membership=membership,
                )
            )
            items.append(
                cls.serialize_attendance(
                    row,
                    can_review=can_review,
                    expected_approver=LeaveService.expected_approver(employee),
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
        membership = cls._membership(user, branch_id)
        organization = cls._organization(membership)
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
            .prefetch_related(cls._sessions_prefetch())
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

        if not LeaveService.can_review_leave(
            user=user,
            employee=attendance.employee,
            membership=membership,
        ):
            raise PermissionDeniedServiceError(
                'Only the reporting manager or a higher manager can review this attendance entry.',
                code='not_attendance_approver',
            )

        attendance.approved_by = user
        attendance.approved_at = timezone.now()
        attendance.approval_remarks = (remarks or '')[:2000]
        attendance.updated_by = user

        if approve:
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
            AttendanceSession.objects.filter(
                attendance=attendance,
                source=AttendanceSession.Source.MANUAL,
            ).delete()
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
            attendance = cls._recompute(attendance, user=user)

        attendance = (
            Attendance.objects.filter(id=attendance.id)
            .select_related('employee', 'employee__designation', 'approved_by')
            .prefetch_related(cls._sessions_prefetch())
            .get()
        )
        return cls.serialize_attendance(
            attendance,
            can_review=False,
            expected_approver=LeaveService.expected_approver(attendance.employee),
        )
