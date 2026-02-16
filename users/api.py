from django.contrib.auth.models import User
from rest_framework import viewsets, permissions

from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view of Django users.
    """

    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related("user", "department").all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

