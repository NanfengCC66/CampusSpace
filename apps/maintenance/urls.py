from django.urls import path
from .views import (
    MaintenanceListView,
    MaintenanceDetailView,
    MaintenanceCreateView,
    MaintenanceUpdateView,
    approve_maintenance,
    start_maintenance,
    complete_maintenance
)

app_name = 'maintenance'

urlpatterns = [
    path('', MaintenanceListView.as_view(), name='maintenance_list'),
    path('<int:pk>/', MaintenanceDetailView.as_view(), name='maintenance_detail'),
    path('create/', MaintenanceCreateView.as_view(), name='maintenance_create'),
    path('<int:pk>/edit/', MaintenanceUpdateView.as_view(), name='maintenance_edit'),
    path('<int:pk>/approve/', approve_maintenance, name='maintenance_approve'),
    path('<int:pk>/start/', start_maintenance, name='maintenance_start'),
    path('<int:pk>/complete/', complete_maintenance, name='maintenance_complete'),
]