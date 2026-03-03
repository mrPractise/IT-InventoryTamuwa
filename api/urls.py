"""
Centralized API URL Configuration.

This module provides a single entry point for all API endpoints.
External applications can integrate with the system using these endpoints.

Base URL: /api/

Available Endpoints:
    - /api/assets/ - Asset management
    - /api/categories/ - Category management
    - /api/status-options/ - Status option management
    - /api/departments/ - Department management
    - /api/assignment-history/ - Assignment history (read-only)
    - /api/activity-logs/ - Activity logs (read-only)
    - /api/maintenance-logs/ - Maintenance log management
    - /api/action-taken-options/ - Action taken options
    - /api/technicians/ - Technician management
    - /api/users/ - User management (read-only)
    - /api/user-profiles/ - User profile management
    - /api/dashboard/ - Dashboard statistics
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()

# Assets endpoints
router.register(r"assets", views.AssetViewSet, basename="asset")
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"status-options", views.StatusOptionViewSet, basename="status-option")
router.register(r"departments", views.DepartmentViewSet, basename="department")
router.register(r"assignment-history", views.AssignmentHistoryViewSet, basename="assignment-history")
router.register(r"activity-logs", views.ActivityLogViewSet, basename="activity-log")

# Users endpoints
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"user-profiles", views.UserProfileViewSet, basename="user-profile")

# Maintenance endpoints
router.register(r"maintenance-logs", views.MaintenanceLogViewSet, basename="maintenance-log")
router.register(r"action-taken-options", views.ActionTakenOptionViewSet, basename="action-taken-option")

# Technicians endpoints
router.register(r"technicians", views.TechnicianViewSet, basename="technician")

# API URL patterns
urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", views.DashboardStatsView.as_view(), name="dashboard-stats"),
]
