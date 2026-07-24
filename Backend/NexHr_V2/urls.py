"""URL configuration for NexHr_V2 project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/organization/', include('apps.organization.urls')),
]
