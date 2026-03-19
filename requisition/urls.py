from django.urls import path
from . import views

app_name = 'requisition'

urlpatterns = [
    path('', views.requisition_list, name='list'),
    path('create/', views.requisition_create, name='create'),
    path('unapproved/', views.unapproved_items, name='unapproved_items'),
    path('bought-queue/', views.bought_items_queue, name='bought_items_queue'),
    path('bought-queue/<int:item_pk>/process/', views.mark_item_processed, name='mark_item_processed'),
    path('<int:pk>/', views.requisition_detail, name='detail'),
    path('<int:pk>/edit/', views.requisition_update, name='update'),
]
