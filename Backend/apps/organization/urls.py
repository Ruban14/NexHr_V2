"""Organization URL routes."""

from django.urls import path

from apps.organization.views import (
    CurrentOrganizationView,
    CurrentUserProfileView,
    IndustryTypeListView,
    OrganizationCreateView,
    OrganizationSetupStatusView,
)

urlpatterns = [
    path('industry-types', IndustryTypeListView.as_view(), name='organization-industry-types'),
    path('setup-status', OrganizationSetupStatusView.as_view(), name='organization-setup-status'),
    path('create', OrganizationCreateView.as_view(), name='organization-create'),
    path('current', CurrentOrganizationView.as_view(), name='organization-current'),
    path('profile', CurrentUserProfileView.as_view(), name='organization-profile'),
]
