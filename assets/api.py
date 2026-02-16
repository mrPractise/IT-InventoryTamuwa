from rest_framework import viewsets, permissions, filters

from .models import (
    Asset,
    Category,
    StatusOption,
    Department,
    AssignmentHistory,
    ActivityLog,
)
from .serializers import (
    AssetSerializer,
    CategorySerializer,
    StatusOptionSerializer,
    DepartmentSerializer,
    AssignmentHistorySerializer,
    ActivityLogSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Read-only for authenticated users, write for staff/super_admin/admin.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff or request.user.is_superuser


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class StatusOptionViewSet(viewsets.ModelViewSet):
    queryset = StatusOption.objects.all().order_by("name")
    serializer_class = StatusOptionSerializer
    permission_classes = [IsAdminOrReadOnly]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]


class AssetViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for assets.
    Supports search & filtering similar to the HTML view.
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
    Read-only view of assignment history.
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
    Read-only view of activity logs.
    """

    queryset = (
        ActivityLog.objects.select_related("asset", "user")
        .all()
        .order_by("-timestamp")
    )
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

