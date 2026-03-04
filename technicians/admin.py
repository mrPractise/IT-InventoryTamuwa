from django.contrib import admin
from .models import Technician, TechnicianAssistant, TechnicianService, TechnicianRecommendation


class TechnicianAssistantInline(admin.TabularInline):
    model = TechnicianAssistant
    extra = 1


class TechnicianServiceInline(admin.TabularInline):
    model = TechnicianService
    extra = 1


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'technician_name', 'phone_number', 'email', 'specialization', 'is_active']
    list_filter = ['is_active', 'specialization']
    search_fields = ['company_name', 'technician_name', 'email', 'phone_number']
    inlines = [TechnicianAssistantInline, TechnicianServiceInline]


@admin.register(TechnicianRecommendation)
class TechnicianRecommendationAdmin(admin.ModelAdmin):
    list_display = ['technician', 'category_name', 'recommendation_type', 'priority', 'is_completed', 'created_at']
    list_filter = ['recommendation_type', 'priority', 'is_completed']
    search_fields = ['technician__technician_name', 'category_name', 'description']
