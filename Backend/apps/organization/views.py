"""Organization API views."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.responses import success_response
from apps.organization.request_context import get_branch_id, parse_bool
from apps.organization.serializers import (
    AccessTypeCreateSerializer,
    AccessTypeUpdateSerializer,
    DesignationCreateSerializer,
    DesignationMoveSerializer,
    DesignationRepositionSerializer,
    DesignationUpdateSerializer,
    EmployeeCreateSerializer,
    EmployeeLifecycleTransitionSerializer,
    EmployeeUpdateSerializer,
    HolidayCalendarCreateSerializer,
    HolidayCalendarUpdateSerializer,
    HolidayCreateSerializer,
    HolidayUpdateSerializer,
    IndustryTypeSerializer,
    MasterNameSerializer,
    MasterUpdateSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    ShiftCreateSerializer,
    ShiftUpdateSerializer,
    UserProfileUpdateSerializer,
    WorkWeekCreateSerializer,
    WorkWeekUpdateSerializer,
)
from apps.organization.services.lifecycle import EmployeeService
from apps.organization.services.masters import MasterService
from apps.organization.services.setup import OrganizationSetupService
from apps.organization.services.workspace import WorkspaceService


class IndustryTypeListView(APIView):
    """List active industry types for organization setup."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        industries = OrganizationSetupService.list_industries()
        data = IndustryTypeSerializer(industries, many=True).data
        return success_response(data=data, message='Industry types retrieved.')


class OrganizationSetupStatusView(APIView):
    """Return whether the authenticated user still needs organization setup."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = OrganizationSetupService.get_setup_status(request.user)
        return success_response(data=data, message='Organization setup status retrieved.')


class OrganizationCreateView(APIView):
    """Create organization, admin profile, and membership for the current user."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = OrganizationSetupService.create_organization(
            user=request.user,
            payload=serializer.validated_data,
        )
        return success_response(
            data=data,
            message='Organization created successfully.',
            status_code=status.HTTP_201_CREATED,
        )


class CurrentOrganizationView(APIView):
    """Retrieve or update the authenticated user's organization."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = WorkspaceService.get_organization(request.user, branch_id=get_branch_id(request))
        return success_response(data=data, message='Organization retrieved.')

    def patch(self, request: Request):
        serializer = OrganizationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = WorkspaceService.update_organization(
            user=request.user,
            payload=serializer.validated_data,
            branch_id=get_branch_id(request),
        )
        return success_response(data=data, message='Organization updated.')


class CurrentUserProfileView(APIView):
    """Retrieve or update the authenticated user's extended profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = WorkspaceService.get_profile(request.user, branch_id=get_branch_id(request))
        return success_response(data=data, message='Profile retrieved.')

    def patch(self, request: Request):
        serializer = UserProfileUpdateSerializer(
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        data = WorkspaceService.update_profile(
            user=request.user,
            payload=serializer.validated_data,
            branch_id=get_branch_id(request),
        )
        return success_response(data=data, message='Profile updated.')


class BranchMembershipListView(APIView):
    """List active branch memberships for the branch switcher."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = WorkspaceService.list_memberships(request.user)
        return success_response(data=data, message='Branches retrieved.')


class DepartmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_departments(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Departments retrieved.')

    def post(self, request: Request):
        serializer = MasterNameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_department(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
        )
        return success_response(data=data, message='Department created.', status_code=status.HTTP_201_CREATED)


class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, department_id):
        serializer = MasterUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_department(
            user=request.user,
            branch_id=get_branch_id(request),
            department_id=department_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Department updated.')

    def delete(self, request: Request, department_id):
        MasterService.delete_department(
            user=request.user,
            branch_id=get_branch_id(request),
            department_id=department_id,
        )
        return success_response(data=None, message='Department deleted.')


class DesignationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, department_id):
        data = MasterService.list_designations(
            user=request.user,
            branch_id=get_branch_id(request),
            department_id=department_id,
            search=request.query_params.get('search', ''),
        )
        return success_response(data=data, message='Designations retrieved.')

    def post(self, request: Request, department_id):
        serializer = DesignationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_designation(
            user=request.user,
            branch_id=get_branch_id(request),
            department_id=department_id,
            name=serializer.validated_data['name'],
            parent_id=serializer.validated_data.get('parent_id'),
        )
        return success_response(data=data, message='Designation created.', status_code=status.HTTP_201_CREATED)


class DesignationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, designation_id):
        serializer = DesignationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_designation(
            user=request.user,
            branch_id=get_branch_id(request),
            designation_id=designation_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Designation updated.')

    def delete(self, request: Request, designation_id):
        MasterService.delete_designation(
            user=request.user,
            branch_id=get_branch_id(request),
            designation_id=designation_id,
        )
        return success_response(data=None, message='Designation deleted.')


class DesignationMoveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, designation_id):
        serializer = DesignationMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.move_designation(
            user=request.user,
            branch_id=get_branch_id(request),
            designation_id=designation_id,
            direction=serializer.validated_data['direction'],
        )
        return success_response(data=data, message='Designation moved.')


class DesignationRepositionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, designation_id):
        serializer = DesignationRepositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.reposition_designation(
            user=request.user,
            branch_id=get_branch_id(request),
            designation_id=designation_id,
            target_id=serializer.validated_data['target_id'],
            position=serializer.validated_data['position'],
        )
        return success_response(data=data, message='Designation repositioned.')


class EmployeeTypeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_employee_types(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Employee types retrieved.')

    def post(self, request: Request):
        serializer = MasterNameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_employee_type(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
        )
        return success_response(data=data, message='Employee type created.', status_code=status.HTTP_201_CREATED)


class EmployeeTypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = MasterUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_employee_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Employee type updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_employee_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Employee type deleted.')


class AccessTypeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_access_types(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Access types retrieved.')

    def post(self, request: Request):
        serializer = AccessTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_access_type(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
        )
        return success_response(data=data, message='Access type created.', status_code=status.HTTP_201_CREATED)


class AccessTypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = AccessTypeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_access_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Access type updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_access_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Access type deleted.')


class ShiftListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_shifts(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Shifts retrieved.')

    def post(self, request: Request):
        serializer = ShiftCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_shift(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            start_time=serializer.validated_data['start_time'],
            end_time=serializer.validated_data['end_time'],
        )
        return success_response(data=data, message='Shift created.', status_code=status.HTTP_201_CREATED)


class ShiftDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = ShiftUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_shift(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Shift updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_shift(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Shift deleted.')


class WorkWeekListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_work_weeks(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Work weeks retrieved.')

    def post(self, request: Request):
        serializer = WorkWeekCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_work_week(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            working_days=serializer.validated_data['working_days'],
        )
        return success_response(data=data, message='Work week created.', status_code=status.HTTP_201_CREATED)


class WorkWeekDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = WorkWeekUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_work_week(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Work week updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_work_week(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Work week deleted.')


class LeaveTypeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_leave_types(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Leave types retrieved.')

    def post(self, request: Request):
        serializer = MasterNameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_leave_type(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
        )
        return success_response(data=data, message='Leave type created.', status_code=status.HTTP_201_CREATED)


class LeaveTypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = MasterUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_leave_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Leave type updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_leave_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Leave type deleted.')


class HolidayCalendarListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        year_raw = request.query_params.get('year')
        year = int(year_raw) if year_raw not in (None, '') else None
        data = MasterService.list_holiday_calendars(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
            year=year,
        )
        return success_response(data=data, message='Holiday calendars retrieved.')

    def post(self, request: Request):
        serializer = HolidayCalendarCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_holiday_calendar(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            year=serializer.validated_data['year'],
        )
        return success_response(
            data=data,
            message='Holiday calendar created.',
            status_code=status.HTTP_201_CREATED,
        )


class HolidayCalendarDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = HolidayCalendarUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_holiday_calendar(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Holiday calendar updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_holiday_calendar(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Holiday calendar deleted.')


class HolidayListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, calendar_id):
        data = MasterService.list_holidays(
            user=request.user,
            branch_id=get_branch_id(request),
            calendar_id=calendar_id,
            search=request.query_params.get('search', ''),
        )
        return success_response(data=data, message='Holidays retrieved.')

    def post(self, request: Request, calendar_id):
        serializer = HolidayCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_holiday(
            user=request.user,
            branch_id=get_branch_id(request),
            calendar_id=calendar_id,
            name=serializer.validated_data['name'],
            date=serializer.validated_data['date'],
        )
        return success_response(data=data, message='Holiday created.', status_code=status.HTTP_201_CREATED)


class HolidayDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, holiday_id):
        serializer = HolidayUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_holiday(
            user=request.user,
            branch_id=get_branch_id(request),
            holiday_id=holiday_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Holiday updated.')

    def delete(self, request: Request, holiday_id):
        MasterService.delete_holiday(
            user=request.user,
            branch_id=get_branch_id(request),
            holiday_id=holiday_id,
        )
        return success_response(data=None, message='Holiday deleted.')


class EmployeeLifecycleConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = EmployeeService.list_lifecycle_config(
            user=request.user,
            branch_id=get_branch_id(request),
        )
        return success_response(data=data, message='Lifecycle configuration retrieved.')


class EmployeeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = EmployeeService.list_employees(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            lifecycle_status_id=request.query_params.get('lifecycle_status_id') or None,
        )
        return success_response(data=data, message='Employees retrieved.')

    def post(self, request: Request):
        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = EmployeeService.create_employee(
            user=request.user,
            branch_id=get_branch_id(request),
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Employee created.', status_code=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = EmployeeService.get_employee(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
        )
        return success_response(data=data, message='Employee retrieved.')

    def patch(self, request: Request, employee_id):
        serializer = EmployeeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = EmployeeService.update_employee(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Employee updated.')


class EmployeeLifecycleTransitionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = EmployeeLifecycleTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = EmployeeService.transition_employee(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            to_status_id=serializer.validated_data['to_status_id'],
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Lifecycle status updated.')
