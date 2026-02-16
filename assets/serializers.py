from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Asset,
    Category,
    StatusOption,
    Department,
    AssignmentHistory,
    ActivityLog,
)


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "description", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at", "updated_at"]


class StatusOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusOption
        fields = ["id", "name", "color", "is_active", "created_at"]


class AssetSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    status = StatusOptionSerializer(read_only=True)
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=StatusOption.objects.all(), source="status", write_only=True
    )
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="department",
        write_only=True,
        allow_null=True,
        required=False,
    )
    assigned_to = UserSummarySerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="assigned_to",
        write_only=True,
        allow_null=True,
        required=False,
    )
    last_known_user = UserSummarySerializer(read_only=True)
    last_known_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="last_known_user",
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Asset
        fields = [
            "id",
            "asset_id",
            "category",
            "category_id",
            "model_description",
            "serial_number",
            "purchase_date",
            "assigned_to",
            "assigned_to_id",
            "department",
            "department_id",
            "last_known_user",
            "last_known_user_id",
            "status",
            "status_id",
            "admin_comments",
            "qr_code",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["qr_code", "created_at", "updated_at"]


class AssignmentHistorySerializer(serializers.ModelSerializer):
    asset = serializers.SlugRelatedField(
        slug_field="asset_id", queryset=Asset.objects.all()
    )
    user = UserSummarySerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="user",
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = AssignmentHistory
        fields = [
            "id",
            "asset",
            "user",
            "user_id",
            "start_date",
            "end_date",
            "notes",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ActivityLogSerializer(serializers.ModelSerializer):
    asset = serializers.SlugRelatedField(
        slug_field="asset_id", read_only=True
    )
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "asset",
            "user",
            "action",
            "description",
            "old_value",
            "new_value",
            "timestamp",
            "ip_address",
        ]
        read_only_fields = fields

