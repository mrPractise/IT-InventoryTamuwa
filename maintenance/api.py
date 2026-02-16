from rest_framework import viewsets, permissions

from .models import MaintenanceLog, ActionTakenOption
from .serializers import MaintenanceLogSerializer, ActionTakenOptionSerializer


class ActionTakenOptionViewSet(viewsets.ModelViewSet):
    queryset = ActionTakenOption.objects.all().order_by("name")
    serializer_class = ActionTakenOptionSerializer
    permission_classes = [permissions.IsAuthenticated]


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = (
        MaintenanceLog.objects.select_related("asset", "action_taken")
        .all()
        .order_by("-timestamp")
    )
    serializer_class = MaintenanceLogSerializer
    permission_classes = [permissions.IsAuthenticated]

