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
    AssetAssignSerializer,
    AssetCreateSerializer,
    AssetRevokeSerializer,
    AssetTypeCreateSerializer,
    AssetTypeUpdateSerializer,
    AssetUpdateSerializer,
    AttendanceManualSerializer,
    AttendancePunchSerializer,
    AttendanceReviewSerializer,
    DesignationCreateSerializer,
    DesignationMoveSerializer,
    DesignationRepositionSerializer,
    DesignationUpdateSerializer,
    DocumentCategoryCreateSerializer,
    DocumentCategoryUpdateSerializer,
    DocumentDefinitionCreateSerializer,
    DocumentDefinitionUpdateSerializer,
    DocumentPolicyCreateSerializer,
    DocumentPolicyUpdateSerializer,
    EmployeeCreateSerializer,
    EmployeeDocumentReviewSerializer,
    EmployeeDocumentUploadSerializer,
    EmployeeLifecycleTransitionSerializer,
    EmployeeUpdateSerializer,
    HolidayCalendarCreateSerializer,
    HolidayCalendarUpdateSerializer,
    HolidayCreateSerializer,
    HolidayUpdateSerializer,
    IndustryTypeSerializer,
    LeaveApplicationCancelSerializer,
    LeaveApplicationCreateSerializer,
    LeaveApplicationReviewSerializer,
    LeaveBalanceAdjustSerializer,
    LeaveBalanceAllocateSerializer,
    LeavePolicyCreateSerializer,
    LeavePolicyUpdateSerializer,
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
from apps.organization.services.assets import AssetService
from apps.organization.services.attendance import AttendanceService
from apps.organization.services.documents import EmployeeDocumentService
from apps.organization.services.leave_policies import LeavePolicyService
from apps.organization.services.leaves import LeaveService
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


class DocumentCategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_document_categories(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Document categories retrieved.')

    def post(self, request: Request):
        serializer = DocumentCategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_document_category(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            display_order=serializer.validated_data.get('display_order', 0),
        )
        return success_response(
            data=data,
            message='Document category created.',
            status_code=status.HTTP_201_CREATED,
        )


class DocumentCategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = DocumentCategoryUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_document_category(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Document category updated.')


class DocumentDefinitionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_document_definitions(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
            category_id=request.query_params.get('category_id') or None,
        )
        return success_response(data=data, message='Documents retrieved.')

    def post(self, request: Request):
        serializer = DocumentDefinitionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_document_definition(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            category_id=serializer.validated_data['category_id'],
            description=serializer.validated_data.get('description', ''),
        )
        return success_response(data=data, message='Document created.', status_code=status.HTTP_201_CREATED)


class DocumentDefinitionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = DocumentDefinitionUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_document_definition(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Document updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_document_definition(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Document deleted.')


class DocumentPolicyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = MasterService.list_document_policies(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
            employee_type_id=request.query_params.get('employee_type_id') or None,
        )
        return success_response(data=data, message='Document policies retrieved.')

    def post(self, request: Request):
        serializer = DocumentPolicyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = MasterService.create_document_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            employee_type_id=serializer.validated_data['employee_type_id'],
            description=serializer.validated_data.get('description', ''),
            is_default=serializer.validated_data.get('is_default', False),
            items=serializer.validated_data.get('items', []),
        )
        return success_response(
            data=data,
            message='Document policy created.',
            status_code=status.HTTP_201_CREATED,
        )


class DocumentPolicyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, item_id):
        data = MasterService.get_document_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=data, message='Document policy retrieved.')

    def patch(self, request: Request, item_id):
        serializer = DocumentPolicyUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = MasterService.update_document_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Document policy updated.')

    def delete(self, request: Request, item_id):
        MasterService.delete_document_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Document policy deleted.')


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
            exit_date=serializer.validated_data.get('exit_date'),
        )
        return success_response(data=data, message='Lifecycle status updated.')


class EmployeeDocumentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = EmployeeDocumentService.list_documents(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
        )
        return success_response(data=data, message='Employee documents retrieved.')

    def post(self, request: Request, employee_id):
        serializer = EmployeeDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = EmployeeDocumentService.upload_document(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            document_id=serializer.validated_data['document_id'],
            uploaded=serializer.validated_data['file'],
            issue_date=serializer.validated_data.get('issue_date'),
            expiry_date=serializer.validated_data.get('expiry_date'),
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(
            data=data,
            message='Document uploaded.',
            status_code=status.HTTP_201_CREATED,
        )


class EmployeeDocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, employee_id, document_id):
        EmployeeDocumentService.delete_document(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            document_row_id=document_id,
        )
        return success_response(data=None, message='Document deleted.')


class EmployeeDocumentReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id, document_id):
        serializer = EmployeeDocumentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = EmployeeDocumentService.review_document(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            document_row_id=document_id,
            approve=serializer.validated_data['approve'],
            remarks=serializer.validated_data.get('remarks', ''),
        )
        action = 'approved' if serializer.validated_data['approve'] else 'rejected'
        return success_response(data=data, message=f'Document {action}.')


class EmployeeDocumentComplianceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = EmployeeDocumentService.check_policy_compliance(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
        )
        return success_response(data=data, message='Document policy compliance checked.')


class AssetTypeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = AssetService.list_asset_types(
            user=request.user,
            branch_id=get_branch_id(request),
            is_active=parse_bool(request.query_params.get('is_active')),
        )
        return success_response(data=data, message='Asset types retrieved.')

    def post(self, request: Request):
        serializer = AssetTypeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AssetService.create_asset_type(
            user=request.user,
            branch_id=get_branch_id(request),
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
        )
        return success_response(data=data, message='Asset type created.', status_code=status.HTTP_201_CREATED)


class AssetTypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = AssetTypeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = AssetService.update_asset_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Asset type updated.')

    def delete(self, request: Request, item_id):
        AssetService.delete_asset_type(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Asset type deleted.')


class AssetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = AssetService.list_assets(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
            asset_type_id=request.query_params.get('asset_type_id') or None,
            status=request.query_params.get('status') or None,
        )
        return success_response(data=data, message='Assets retrieved.')

    def post(self, request: Request):
        serializer = AssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AssetService.create_asset(
            user=request.user,
            branch_id=get_branch_id(request),
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Asset created.', status_code=status.HTTP_201_CREATED)


class AssetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, item_id):
        serializer = AssetUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = AssetService.update_asset(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Asset updated.')

    def delete(self, request: Request, item_id):
        AssetService.delete_asset(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Asset deleted.')


class AssetAvailableListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = AssetService.list_available_assets(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
        )
        return success_response(data=data, message='Available assets retrieved.')


class EmployeeAssetAssignmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = AssetService.list_employee_assignments(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
        )
        return success_response(data=data, message='Employee asset assignments retrieved.')

    def post(self, request: Request, employee_id):
        serializer = AssetAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AssetService.assign_asset(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            asset_id=serializer.validated_data['asset_id'],
            assigned_at=serializer.validated_data.get('assigned_at'),
            expected_return_at=serializer.validated_data.get('expected_return_at'),
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Asset assigned.', status_code=status.HTTP_201_CREATED)


class EmployeeAssetAssignmentRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id, assignment_id):
        serializer = AssetRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AssetService.revoke_assignment(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            assignment_id=assignment_id,
            returned_at=serializer.validated_data.get('returned_at'),
            remarks=serializer.validated_data.get('remarks', ''),
            mark_lost=serializer.validated_data.get('mark_lost', False),
        )
        return success_response(data=data, message='Asset assignment revoked.')


class LeavePolicyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = LeavePolicyService.list_leave_policies(
            user=request.user,
            branch_id=get_branch_id(request),
            search=request.query_params.get('search', ''),
            page=int(request.query_params.get('page', 1)),
            page_size=int(request.query_params.get('page_size', 20)),
            is_active=parse_bool(request.query_params.get('is_active')),
            employee_type_id=request.query_params.get('employee_type_id') or None,
        )
        return success_response(data=data, message='Leave policies retrieved.')

    def post(self, request: Request):
        serializer = LeavePolicyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = LeavePolicyService.create_leave_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            payload=serializer.validated_data,
        )
        return success_response(
            data=data,
            message='Leave policy created.',
            status_code=status.HTTP_201_CREATED,
        )


class LeavePolicyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, item_id):
        data = LeavePolicyService.get_leave_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=data, message='Leave policy retrieved.')

    def patch(self, request: Request, item_id):
        serializer = LeavePolicyUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = LeavePolicyService.update_leave_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Leave policy updated.')

    def delete(self, request: Request, item_id):
        LeavePolicyService.delete_leave_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            item_id=item_id,
        )
        return success_response(data=None, message='Leave policy deleted.')


class EmployeeLeaveBalanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = LeaveService.list_balances(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
        )
        return success_response(data=data, message='Leave balances retrieved.')


class EmployeeLeaveBalanceAllocateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = LeaveBalanceAllocateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = LeaveService.allocate_balance(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            leave_type_id=serializer.validated_data['leave_type_id'],
            quantity=serializer.validated_data['quantity'],
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Leave allocated.', status_code=status.HTTP_201_CREATED)


class EmployeeLeaveBalanceAdjustView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = LeaveBalanceAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = LeaveService.adjust_balance(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            leave_type_id=serializer.validated_data['leave_type_id'],
            quantity=serializer.validated_data['quantity'],
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Leave balance adjusted.')


class EmployeeLeaveBalanceSeedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        data = LeaveService.seed_from_policy(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
        )
        return success_response(data=data, message='Leave balances seeded from policy.')


class EmployeeLeaveApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = LeaveService.list_applications(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            status=request.query_params.get('status') or None,
        )
        return success_response(data=data, message='Leave applications retrieved.')

    def post(self, request: Request, employee_id):
        serializer = LeaveApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        attachment = payload.pop('attachment', None)
        data = LeaveService.create_application(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            payload=payload,
            attachment=attachment,
        )
        return success_response(
            data=data,
            message='Leave application created.',
            status_code=status.HTTP_201_CREATED,
        )


class EmployeeLeaveApplicationReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id, application_id):
        serializer = LeaveApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = LeaveService.review_application(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            application_id=application_id,
            approve=serializer.validated_data['approve'],
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Leave application reviewed.')


class EmployeeLeaveApplicationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id, application_id):
        serializer = LeaveApplicationCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = LeaveService.cancel_application(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            application_id=application_id,
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Leave application cancelled.')


class EmployeeLeaveLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = LeaveService.list_logs(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
        )
        return success_response(data=data, message='Leave logs retrieved.')


class LeaveApprovalsInboxView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = LeaveService.list_approvals_inbox(
            user=request.user,
            branch_id=get_branch_id(request),
            status=request.query_params.get('status') or None,
        )
        return success_response(data=data, message='Leave approvals retrieved.')


class LeaveApprovalReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, application_id):
        serializer = LeaveApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = LeaveService.review_application_by_id(
            user=request.user,
            branch_id=get_branch_id(request),
            application_id=application_id,
            approve=serializer.validated_data['approve'],
            remarks=serializer.validated_data.get('remarks', ''),
        )
        action = 'approved' if serializer.validated_data['approve'] else 'rejected'
        return success_response(data=data, message=f'Leave application {action}.')


class AttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = AttendanceService.list_org_attendance(
            user=request.user,
            branch_id=get_branch_id(request),
            date_value=request.query_params.get('date') or None,
            date_from=request.query_params.get('date_from') or None,
            date_to=request.query_params.get('date_to') or None,
            status_filter=request.query_params.get('status') or None,
            employee_id=request.query_params.get('employee_id') or None,
            search=request.query_params.get('search') or None,
        )
        return success_response(data=data, message='Attendance retrieved.')


class AttendanceTodayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = AttendanceService.get_today(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=request.query_params.get('employee_id') or None,
        )
        return success_response(data=data, message='Today attendance retrieved.')


class AttendanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, attendance_id):
        data = AttendanceService.get_detail(
            user=request.user,
            branch_id=get_branch_id(request),
            attendance_id=attendance_id,
        )
        return success_response(data=data, message='Attendance detail retrieved.')


class AttendanceCheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.check_in(
            user=request.user,
            branch_id=get_branch_id(request),
            remarks=serializer.validated_data.get('remarks', ''),
            source=serializer.validated_data.get('source', 'web'),
        )
        return success_response(data=data, message='Checked in.', status_code=status.HTTP_201_CREATED)


class AttendanceCheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.check_out(
            user=request.user,
            branch_id=get_branch_id(request),
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Checked out.')


class AttendanceBreakStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.break_start(
            user=request.user,
            branch_id=get_branch_id(request),
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Break started.')


class AttendanceBreakEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.break_end(
            user=request.user,
            branch_id=get_branch_id(request),
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Break ended.')


class EmployeeAttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = AttendanceService.list_employee_attendance(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            date_from=request.query_params.get('date_from') or None,
            date_to=request.query_params.get('date_to') or None,
        )
        return success_response(data=data, message='Employee attendance retrieved.')


class EmployeeAttendanceCheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.check_in(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            remarks=serializer.validated_data.get('remarks', ''),
            source=serializer.validated_data.get('source', 'web'),
        )
        return success_response(data=data, message='Checked in.', status_code=status.HTTP_201_CREATED)


class EmployeeAttendanceCheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.check_out(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Checked out.')


class EmployeeAttendanceBreakStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.break_start(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Break started.')


class EmployeeAttendanceBreakEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = AttendancePunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.break_end(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            remarks=serializer.validated_data.get('remarks', ''),
        )
        return success_response(data=data, message='Break ended.')


class EmployeeAttendanceManualView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, employee_id):
        serializer = AttendanceManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.manual_upsert(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            payload=dict(serializer.validated_data),
        )
        return success_response(
            data=data,
            message='Manual attendance submitted for approval.',
            status_code=status.HTTP_201_CREATED,
        )


class EmployeeAttendanceSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, employee_id):
        data = AttendanceService.list_employee_sessions(
            user=request.user,
            branch_id=get_branch_id(request),
            employee_id=employee_id,
            date_from=request.query_params.get('date_from') or None,
            date_to=request.query_params.get('date_to') or None,
        )
        return success_response(data=data, message='Attendance sessions retrieved.')


class AttendanceApprovalsInboxView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = AttendanceService.list_approvals_inbox(
            user=request.user,
            branch_id=get_branch_id(request),
            status=request.query_params.get('status') or None,
        )
        return success_response(data=data, message='Attendance approvals retrieved.')


class AttendanceApprovalReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, attendance_id):
        serializer = AttendanceReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AttendanceService.review_attendance(
            user=request.user,
            branch_id=get_branch_id(request),
            attendance_id=attendance_id,
            approve=serializer.validated_data['approve'],
            remarks=serializer.validated_data.get('remarks', ''),
        )
        action = 'approved' if serializer.validated_data['approve'] else 'rejected'
        return success_response(data=data, message=f'Manual attendance {action}.')
