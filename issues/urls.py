from django.urls import path
from . import views

app_name = 'issues'

urlpatterns = [
    # Combined home with two tabs
    path('', views.issues_home, name='home'),

    # Issues
    path('issues/create/', views.issue_create, name='issue_create'),
    path('issues/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('issues/<int:pk>/edit/', views.issue_update, name='issue_update'),

    # Projects
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_update, name='project_update'),
]
