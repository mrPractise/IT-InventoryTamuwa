from django.urls import path
from . import views

app_name = 'issues'

urlpatterns = [
    # Issues
    path('', views.issue_list, name='home'),  # Default to issues
    path('list/', views.issue_list, name='issue_list'),
    path('issues/create/', views.issue_create, name='issue_create'),
    path('issues/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('issues/<int:pk>/edit/', views.issue_update, name='issue_update'),

    # Projects
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_update, name='project_update'),
    path('api/category-assets/<int:category_id>/', views.category_assets_api, name='category_assets_api'),
]
