"""
URL configuration for inventory_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Customize admin site
admin.site.site_header = "IT Inventory Administration"
admin.site.site_title = "IT Inventory Admin"
admin.site.index_title = "Welcome to IT Inventory Administration"

from users import views as user_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("assets/", include("assets.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("requisition/", include("requisition.urls")),
    path("issues/", include("issues.urls")),
    path("users/", include("users.urls")),
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
