"""
URL configuration for inventory_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Customize admin site
admin.site.site_header = "IT Inventory Administration"
admin.site.site_title = "IT Inventory Admin"
admin.site.index_title = "Welcome to IT Inventory Administration"

from users import views as user_views

def health_check(request):
    """Simple health check endpoint for Railway — no auth required."""
    return HttpResponse("OK", content_type="text/plain", status=200)


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("assets/", include("assets.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("requisition/", include("requisition.urls")),
    path("issues/", include("issues.urls")),
    path("users/", include("users.urls")),
    path("tasks/", include("tasks.urls")),
    path("technicians/", include("technicians.urls")),
    path("accounts/login/", user_views.login_view, name="login"),
    # Centralized API endpoints
    path("api/", include("api.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'inventory_system.views.handler404'
handler500 = 'inventory_system.views.handler500'
handler403 = 'inventory_system.views.handler403'
