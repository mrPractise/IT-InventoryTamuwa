from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('directory/', views.directory_view, name='directory'),
    path('directory/person/<int:person_id>/', views.person_assets_view, name='person_assets'),
    path('directory/add-person/', views.add_person_view, name='add_person'),
    path('directory/department/<int:dept_id>/', views.department_assets_view, name='department_assets'),
    path('directory/add-department/', views.add_department_view, name='add_department'),
]
