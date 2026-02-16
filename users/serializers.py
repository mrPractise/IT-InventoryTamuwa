from django.contrib.auth.models import User
from rest_framework import serializers

from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_active"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "user_id",
            "role",
            "department",
            "phone_number",
            "employee_id",
            "profile_picture",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

