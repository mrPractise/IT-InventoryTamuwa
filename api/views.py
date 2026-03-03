"""
Centralized API Views for the Inventory System.

This module aggregates all API endpoints from various apps into a single location,
making it easy for external applications to integrate with the system.

To add a new API endpoint:
1. Create your viewset in the appropriate app's api.py
2. Import and re-export it here
3. Register it in api/urls.py
"""

from rest_framework import permissions, viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone

# Assets API
from assets.models import (
    Asset,
    Category,
    StatusOption,
    Department,
    AssignmentHistory,
    ActivityLog,
)
from assets.serializers import (
    AssetSerializer,
    CategorySerializer,
    StatusOptionSerializer,
    DepartmentSerializer,
    AssignmentHistorySerializer,
    ActivityLogSerializer,
)

# Users API
from django.contrib.auth.models import User
from users.models import UserProfile
from users.serializers import UserSerializer, UserProfileSerializer

# Maintenance API
from maintenance.models import MaintenanceLog, ActionTakenOption
from maintenance.serializers import MaintenanceLogSerializer, ActionTakenOptionSerializer

# Technicians API
from technicians.models import Technician
from technicians.serializers import TechnicianSerializer


# ============================================================================
# PERMISSION CLASSES
# ============================================================================

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Read-only for authenticated users, write for staff/superuser.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff or request.user.is_superuser


# ============================================================================
# ASSETS API VIEWSETS
# ============================================================================

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing asset categories.
    
    list: Get all categories
    create: Create a new category (admin only)
    retrieve: Get a specific category
    update: Update a category (admin only)
    destroy: Delete a category (admin only)
    """
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class StatusOptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing asset status options.
    
    list: Get all status options
    create: Create a new status option (admin only)
    retrieve: Get a specific status option
    update: Update a status option (admin only)
    destroy: Delete a status option (admin only)
    """
    queryset = StatusOption.objects.all().order_by("name")
    serializer_class = StatusOptionSerializer
    permission_classes = [IsAdminOrReadOnly]


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing departments.
    
    list: Get all departments
    create: Create a new department (admin only)
    retrieve: Get a specific department
    update: Update a department (admin only)
    destroy: Delete a department (admin only)
    """
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing assets.
    
    list: Get all assets (supports filtering by category, status, assigned)
    create: Create a new asset
    retrieve: Get a specific asset
    update: Update an asset
    partial_update: Partially update an asset
    destroy: Soft delete an asset
    
    Query Parameters:
        - category: Filter by category ID
        - status: Filter by status ID
        - assigned: Filter by assignment status ('assigned' or 'unassigned')
        - search: Search by asset_id, serial_number, model_description, or assigned user
    """
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "asset_id",
        "serial_number",
        "model_description",
        "assigned_to__username",
    ]
    ordering_fields = ["asset_id", "created_at", "purchase_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = (
            Asset.objects.filter(is_deleted=False)
            .select_related(
                "category", "status", "assigned_to", "department", "last_known_user"
            )
            .all()
        )

        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        status_id = self.request.query_params.get("status")
        if status_id:
            qs = qs.filter(status_id=status_id)

        assigned = self.request.query_params.get("assigned")
        if assigned == "assigned":
            qs = qs.exclude(assigned_to__isnull=True)
        elif assigned == "unassigned":
            qs = qs.filter(assigned_to__isnull=True)

        return qs


class AssignmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing assignment history.
    
    list: Get all assignment history entries
    retrieve: Get a specific assignment history entry
    """
    queryset = (
        AssignmentHistory.objects.select_related("asset", "user")
        .all()
        .order_by("-start_date")
    )
    serializer_class = AssignmentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing activity logs.
    
    list: Get all activity logs
    retrieve: Get a specific activity log
    """
    queryset = (
        ActivityLog.objects.select_related("asset", "user")
        .all()
        .order_by("-timestamp")
    )
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]


# ============================================================================
# USERS API VIEWSETS
# ============================================================================

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing users.
    
    list: Get all users
    retrieve: Get a specific user
    """
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user profiles.
    
    list: Get all user profiles
    create: Create a new user profile
    retrieve: Get a specific user profile
    update: Update a user profile
    partial_update: Partially update a user profile
    destroy: Delete a user profile
    """
    queryset = UserProfile.objects.select_related("user", "department").all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


# ============================================================================
# MAINTENANCE API VIEWSETS
# ============================================================================

class ActionTakenOptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing maintenance action options.
    
    list: Get all action taken options
    create: Create a new action taken option
    retrieve: Get a specific action taken option
    update: Update an action taken option
    destroy: Delete an action taken option
    """
    queryset = ActionTakenOption.objects.all().order_by("name")
    serializer_class = ActionTakenOptionSerializer
    permission_classes = [permissions.IsAuthenticated]


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing maintenance logs.
    
    list: Get all maintenance logs
    create: Create a new maintenance log
    retrieve: Get a specific maintenance log
    update: Update a maintenance log
    partial_update: Partially update a maintenance log
    destroy: Delete a maintenance log
    """
    queryset = (
        MaintenanceLog.objects.select_related("asset", "action_taken", "performed_by")
        .all()
        .order_by("-timestamp")
    )
    serializer_class = MaintenanceLogSerializer
    permission_classes = [permissions.IsAuthenticated]


class TechnicianViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing technicians.
    
    list: Get all technicians
    create: Create a new technician
    retrieve: Get a specific technician
    update: Update a technician
    partial_update: Partially update a technician
    destroy: Delete a technician
    """
    queryset = Technician.objects.filter(is_active=True).order_by("company_name", "technician_name")
    serializer_class = TechnicianSerializer
    permission_classes = [permissions.IsAuthenticated]


# ============================================================================
# DASHBOARD API
# ============================================================================

class DashboardStatsView(APIView):
    """
    API endpoint for dashboard statistics.
    
    get: Returns dashboard statistics including:
        - total_assets: Total number of assets
        - status_counts: Count of assets by status
        - assets_this_month: Assets added this month
        - maintenance_today: Maintenance logs for today
        - categories: Asset distribution by category
        - recent_activity: Recent activity logs
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        assets = Asset.objects.filter(is_deleted=False)

        # Status counts
        status_counts = {}
        status_options = StatusOption.objects.filter(is_active=True)
        for status in status_options:
            status_counts[status.name] = assets.filter(status=status).count()

        total_assets = assets.count()

        this_month_start = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        assets_this_month = assets.filter(created_at__gte=this_month_start).count()

        maintenance_today = MaintenanceLog.objects.filter(
            maintenance_status="Open",
            date_reported=timezone.now().date(),
        ).count()

        category_distribution = Category.objects.annotate(
            asset_count=Count("assets", filter=Q(assets__is_deleted=False))
        ).values("name", "asset_count")

        recent_activities = (
            ActivityLog.objects.select_related("asset", "user")
            .order_by("-timestamp")[:10]
        )

        recent_data = [
            {
                "asset_id": a.asset.asset_id if a.asset else None,
                "action": a.action,
                "description": a.description,
                "user": a.user.username if a.user else None,
                "timestamp": a.timestamp,
            }
            for a in recent_activities
        ]

        data = {
            "total_assets": total_assets,
            "status_counts": status_counts,
            "assets_this_month": assets_this_month,
            "maintenance_today": maintenance_today,
            "categories": list(category_distribution),
            "recent_activity": recent_data,
        }

        return Response(data)
