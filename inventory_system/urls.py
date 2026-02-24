"""
URL configuration for inventory_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Customize admin site
admin.site.site_header = "AssetCore Administration"
admin.site.site_title = "AssetCore Admin"
admin.site.index_title = "Welcome to AssetCore Administration"

from users import views as user_views
from assets.api import (
    AssetViewSet,
    CategoryViewSet,
    StatusOptionViewSet,
    DepartmentViewSet,
    AssignmentHistoryViewSet,
    ActivityLogViewSet,
)
from maintenance.api import MaintenanceLogViewSet, ActionTakenOptionViewSet
from users.api import UserViewSet, UserProfileViewSet
from dashboard.api import DashboardStatsView

router = DefaultRouter()
router.register(r"assets", AssetViewSet, basename="api-assets")
router.register(r"categories", CategoryViewSet, basename="api-categories")
router.register(r"status-options", StatusOptionViewSet, basename="api-status-options")
router.register(r"departments", DepartmentViewSet, basename="api-departments")
router.register(
    r"assignment-history",
    AssignmentHistoryViewSet,
    basename="api-assignment-history",
)
router.register(r"activity-logs", ActivityLogViewSet, basename="api-activity-logs")
router.register(
    r"maintenance-logs", MaintenanceLogViewSet, basename="api-maintenance-logs"
)
router.register(
    r"action-taken-options",
    ActionTakenOptionViewSet,
    basename="api-action-taken-options",
)
router.register(r"users", UserViewSet, basename="api-users")
router.register(r"user-profiles", UserProfileViewSet, basename="api-user-profiles")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("assets/", include("assets.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("requisition/", include("requisition.urls")),
    path("issues/", include("issues.urls")),
    path("users/", include("users.urls")),
    path("accounts/login/", user_views.login_view, name="login"),  # For admin login
    path("api/", include(router.urls)),
    path("api/dashboard/", DashboardStatsView.as_view(), name="api-dashboard"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
