"""Organization API views."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.responses import success_response
from apps.organization.serializers import (
    IndustryTypeSerializer,
    OrganizationCreateSerializer,
    OrganizationUpdateSerializer,
    UserProfileUpdateSerializer,
)
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
        data = WorkspaceService.get_organization(request.user)
        return success_response(data=data, message='Organization retrieved.')

    def patch(self, request: Request):
        serializer = OrganizationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = WorkspaceService.update_organization(
            user=request.user,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Organization updated.')


class CurrentUserProfileView(APIView):
    """Retrieve or update the authenticated user's extended profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        data = WorkspaceService.get_profile(request.user)
        return success_response(data=data, message='Profile retrieved.')

    def patch(self, request: Request):
        serializer = UserProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = WorkspaceService.update_profile(
            user=request.user,
            payload=serializer.validated_data,
        )
        return success_response(data=data, message='Profile updated.')
