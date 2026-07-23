from django.urls import path
from .views import (
    ScheduleListView, 
    ScheduleDetailView, 
    ScheduleCreateView, 
    ScheduleUpdateView, 
    ScheduleDeleteView,
    schedule_calendar
)

app_name = 'schedules'

urlpatterns = [
    path('', ScheduleListView.as_view(), name='schedule_list'),
    path('<int:pk>/', ScheduleDetailView.as_view(), name='schedule_detail'),
    path('create/', ScheduleCreateView.as_view(), name='schedule_create'),
    path('<int:pk>/edit/', ScheduleUpdateView.as_view(), name='schedule_edit'),
    path('<int:pk>/delete/', ScheduleDeleteView.as_view(), name='schedule_delete'),
    path('calendar/<int:venue_id>/', schedule_calendar, name='schedule_calendar'),
]