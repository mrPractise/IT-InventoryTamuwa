from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html', http_method_names=['get', 'post']), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('password-change-required/', views.password_change_required_view, name='password_change_required'),
    
    # User Management (Admin only)
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:user_id>/reset-password/', views.user_reset_password_view, name='user_reset_password'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active_view, name='user_toggle_active'),
    
    # Directory
    path('directory/', views.directory_view, name='directory'),
    path('directory/person/<int:person_id>/', views.person_assets_view, name='person_assets'),
    path('directory/add-person/', views.add_person_view, name='add_person'),
    path('directory/person/<int:person_id>/edit/', views.edit_person_view, name='edit_person'),
    path('directory/person/<int:person_id>/delete/', views.delete_person_view, name='delete_person'),
    path('directory/department/<int:dept_id>/', views.department_assets_view, name='department_assets'),
    path('directory/add-department/', views.add_department_view, name='add_department'),
    path('directory/department/<int:dept_id>/edit/', views.edit_department_view, name='edit_department'),
    path('directory/department/<int:dept_id>/delete/', views.delete_department_view, name='delete_department'),
]
