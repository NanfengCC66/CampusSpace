from django.urls import path
from .views import BuildingListView, BuildingDetailView, RoomListView, RoomDetailView

app_name = 'venues'

urlpatterns = [
    path('buildings/', BuildingListView.as_view(), name='building_list'),
    path('buildings/<int:pk>/', BuildingDetailView.as_view(), name='building_detail'),
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room_detail'),
]