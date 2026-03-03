from django.urls import path
from . import views

app_name = 'technicians'

urlpatterns = [
    path('', views.technician_list, name='list'),
    path('create/', views.technician_create, name='create'),
    path('<int:pk>/', views.technician_detail, name='detail'),
    path('<int:pk>/edit/', views.technician_update, name='update'),
    path('<int:technician_pk>/assistant/add/', views.assistant_create, name='add_assistant'),
    path('<int:technician_pk>/service/add/', views.service_create, name='add_service'),
    path('recommendations/', views.recommendation_list, name='recommendation_list'),
    path('recommendations/add/', views.recommendation_create, name='add_recommendation'),
]
