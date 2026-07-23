from django.urls import path
from .views import (
    BookingListView,
    BookingDetailView,
    BookingCreateView,
    RecommendationView,
    ApprovalListView,
    CalendarView,
    StatisticsView,
    check_availability,
    cancel_booking,
    approve_booking,
    reject_booking,
    cancel_booking_view,
    calendar_events,
    api_venue_utilization,
    api_booking_trend,
    api_booking_type_statistics,
    api_status_distribution,
    api_popular_venues,
    api_time_distribution,
    api_building_statistics
)

app_name = 'bookings'

urlpatterns = [
    path('', BookingListView.as_view(), name='booking_list'),
    path('create/', BookingCreateView.as_view(), name='booking_create'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/cancel/', cancel_booking, name='booking_cancel'),
    path('<int:pk>/cancel-view/', cancel_booking_view, name='cancel_booking_view'),
    path('check-availability/', check_availability, name='check_availability'),
    path('recommend/', RecommendationView.as_view(), name='recommendation'),
    path('approvals/', ApprovalListView.as_view(), name='approval_list'),
    path('approvals/<int:pk>/approve/', approve_booking, name='approve_booking'),
    path('approvals/<int:pk>/reject/', reject_booking, name='reject_booking'),
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('calendar/events/', calendar_events, name='calendar_events'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    path('api/utilization/', api_venue_utilization, name='api_utilization'),
    path('api/trend/', api_booking_trend, name='api_trend'),
    path('api/booking-types/', api_booking_type_statistics, name='api_booking_types'),
    path('api/status/', api_status_distribution, name='api_status'),
    path('api/popular/', api_popular_venues, name='api_popular'),
    path('api/time/', api_time_distribution, name='api_time'),
    path('api/building/', api_building_statistics, name='api_building'),
]