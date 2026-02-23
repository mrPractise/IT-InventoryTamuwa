from django.contrib import admin
from .models import Asset, Category, StatusOption, Department, AssignmentHistory, ActivityLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(StatusOption)
class StatusOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


class AssignmentHistoryInline(admin.TabularInline):
    model = AssignmentHistory
    extra = 0
    readonly_fields = ['start_date', 'end_date']
    can_delete = False


class ActivityLogInline(admin.TabularInline):
    model = ActivityLog
    extra = 0
    readonly_fields = ['user', 'action', 'description', 'timestamp']
    can_delete = False
    max_num = 10


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'asset_id', 'category', 'model_description', 'serial_number',
        'assigned_to', 'status', 'purchase_date', 'created_at'
    ]
    list_filter = ['status', 'category', 'assigned_to', 'created_at', 'purchase_date']
    search_fields = ['asset_id', 'serial_number', 'model_description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_id', 'category', 'model_description', 'serial_number', 'purchase_date')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'department', 'last_known_user', 'status')
        }),
        ('Additional Information', {
            'fields': ('admin_comments',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )
    inlines = [AssignmentHistoryInline, ActivityLogInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'status', 'assigned_to', 'department')


@admin.register(AssignmentHistory)
class AssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = ['asset', 'user', 'start_date', 'end_date']
    list_filter = ['start_date', 'end_date']
    search_fields = ['asset__asset_id', 'user__username']
    readonly_fields = ['created_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['asset', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['asset__asset_id', 'user__username', 'description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
