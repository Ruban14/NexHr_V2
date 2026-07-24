"""Organization URL routes."""

from django.urls import path

from apps.organization.views import (
    IndustryTypeListView,
    OrganizationCreateView,
    OrganizationSetupStatusView,
)

urlpatterns = [
    path('industry-types', IndustryTypeListView.as_view(), name='organization-industry-types'),
    path('setup-status', OrganizationSetupStatusView.as_view(), name='organization-setup-status'),
    path('create', OrganizationCreateView.as_view(), name='organization-create'),
]
