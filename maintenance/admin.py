from django.contrib import admin
from .models import MaintenanceLog, ActionTakenOption


@admin.register(ActionTakenOption)
class ActionTakenOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'date_reported', 'maintenance_status',
        'action_taken', 'cost_of_repair', 'date_completed'
    ]
    list_filter = ['maintenance_status', 'date_reported', 'action_taken']
    search_fields = ['asset__asset_id', 'description']
    readonly_fields = ['timestamp', 'created_at', 'updated_at']
    fieldsets = (
        ('Asset Information', {
            'fields': ('asset', 'previous_assigned_user')
        }),
        ('Maintenance Details', {
            'fields': (
                'date_reported', 'date_completed', 'description',
                'action_taken', 'cost_of_repair', 'maintenance_status'
            )
        }),
        ('Personnel', {
            'fields': ('reported_by', 'completed_by')
        }),
        ('Additional Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('timestamp', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'date_reported'
