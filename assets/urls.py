from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.asset_list, name='list'),
    path('create/', views.asset_create, name='create'),
    path('<int:pk>/', views.asset_detail, name='detail'),
    path('<int:pk>/edit/', views.asset_update, name='update'),
    path('<int:pk>/delete/', views.asset_delete, name='delete'),
    path('export/excel/', views.asset_export_excel, name='export_excel'),
    path('api/get-next-asset-id/', views.get_next_asset_id, name='get_next_asset_id'),
]
