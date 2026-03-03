from django.urls import path
from . import views

app_name = 'requisition'

urlpatterns = [
    path('', views.requisition_list, name='list'),
    path('create/', views.requisition_create, name='create'),
    path('unapproved/', views.unapproved_items, name='unapproved_items'),
    path('bought-queue/', views.bought_items_queue, name='bought_items_queue'),
    path('<int:pk>/', views.requisition_detail, name='detail'),
    path('<int:pk>/edit/', views.requisition_update, name='update'),
]
