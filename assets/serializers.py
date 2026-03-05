from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Asset,
    Category,
    StatusOption,
    Department,
    Person,
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


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "first_name", "last_name", "full_name", "department"]


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
    assigned_to = PersonSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(),
        source="assigned_to",
        write_only=True,
        allow_null=True,
        required=False,
    )
    last_known_person = PersonSerializer(read_only=True)
    last_known_person_id = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(),
        source="last_known_person",
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
            "last_known_person",
            "last_known_person_id",
            "status",
            "status_id",
            "admin_comments",
            "purchased_from",
            "purchase_cost",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AssignmentHistorySerializer(serializers.ModelSerializer):
    asset = serializers.SlugRelatedField(
        slug_field="asset_id", queryset=Asset.objects.all()
    )
    person = PersonSerializer(read_only=True)
    person_id = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(),
        source="person",
        write_only=True,
        allow_null=True,
        required=False,
    )
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = AssignmentHistory
        fields = [
            "id",
            "asset",
            "person",
            "person_id",
            "department",
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
