"""Organization API views."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.organization.serializers import IndustryTypeSerializer, OrganizationCreateSerializer
from apps.organization.services.setup import OrganizationSetupService
from apps.core.responses import success_response


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
