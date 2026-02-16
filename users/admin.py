from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'employee_id', 'phone_number']
    list_filter = ['role', 'department']
    search_fields = ['user__username', 'user__email', 'employee_id']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Role & Department', {
            'fields': ('role', 'department')
        }),
        ('Contact Information', {
            'fields': ('phone_number',)
        }),
        ('Additional Information', {
            'fields': ('employee_id', 'profile_picture')
        }),
    )
