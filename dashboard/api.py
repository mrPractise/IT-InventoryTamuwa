from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from assets.models import Asset, Category, StatusOption, ActivityLog
from maintenance.models import MaintenanceLog


class DashboardStatsView(APIView):
    """
    API version of the dashboard summary.
    """

    permission_classes = [IsAuthenticated]

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

