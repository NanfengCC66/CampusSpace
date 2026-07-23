from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Building, Room


class BuildingListView(LoginRequiredMixin, ListView):
    """楼宇列表视图"""
    model = Building
    template_name = 'venues/building_list.html'
    context_object_name = 'buildings'
    ordering = ['name']


class BuildingDetailView(LoginRequiredMixin, DetailView):
    """楼宇详情视图"""
    model = Building
    template_name = 'venues/building_detail.html'
    context_object_name = 'building'


class RoomListView(LoginRequiredMixin, ListView):
    """场地列表视图"""
    model = Room
    template_name = 'venues/room_list.html'
    context_object_name = 'rooms'
    ordering = ['building__name', 'floor', 'room_number']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        building_id = self.request.GET.get('building')
        venue_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        if venue_type:
            queryset = queryset.filter(venue_type=venue_type)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings'] = Building.objects.all()
        return context


class RoomDetailView(LoginRequiredMixin, DetailView):
    """场地详情视图"""
    model = Room
    template_name = 'venues/room_detail.html'
    context_object_name = 'room'