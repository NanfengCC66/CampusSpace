from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Schedule
from apps.venues.models import Room


class ScheduleListView(LoginRequiredMixin, ListView):
    """固定课表列表视图"""
    model = Schedule
    template_name = 'schedules/schedule_list.html'
    context_object_name = 'schedules'
    ordering = ['-semester', 'day_of_week', 'period']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        semester = self.request.GET.get('semester')
        venue_id = self.request.GET.get('venue')
        day = self.request.GET.get('day')
        
        if semester:
            queryset = queryset.filter(semester=semester)
        if venue_id:
            queryset = queryset.filter(venue_id=venue_id)
        if day:
            queryset = queryset.filter(day_of_week=day)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venues'] = Room.objects.all()
        context['semesters'] = Schedule.objects.values_list('semester', flat=True).distinct()
        return context


class ScheduleDetailView(LoginRequiredMixin, DetailView):
    """固定课表详情视图"""
    model = Schedule
    template_name = 'schedules/schedule_detail.html'
    context_object_name = 'schedule'


class ScheduleCreateView(LoginRequiredMixin, CreateView):
    """创建固定课表视图"""
    model = Schedule
    template_name = 'schedules/schedule_form.html'
    fields = ['venue', 'course_name', 'teacher', 'day_of_week', 'period', 
              'start_week', 'end_week', 'class_name', 'student_count', 
              'semester', 'remark']
    success_url = reverse_lazy('schedules:schedule_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '固定课表创建成功！')
        return super().form_valid(form)


class ScheduleUpdateView(LoginRequiredMixin, UpdateView):
    """更新固定课表视图"""
    model = Schedule
    template_name = 'schedules/schedule_form.html'
    fields = ['venue', 'course_name', 'teacher', 'day_of_week', 'period', 
              'start_week', 'end_week', 'class_name', 'student_count', 
              'semester', 'remark']
    success_url = reverse_lazy('schedules:schedule_list')
    
    def form_valid(self, form):
        messages.success(self.request, '固定课表更新成功！')
        return super().form_valid(form)


class ScheduleDeleteView(LoginRequiredMixin, DeleteView):
    """删除固定课表视图"""
    model = Schedule
    success_url = reverse_lazy('schedules:schedule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '固定课表删除成功！')
        return super().delete(request, *args, **kwargs)


@login_required
def schedule_calendar(request, venue_id):
    """场地课表日历视图"""
    venue = get_object_or_404(Room, pk=venue_id)
    semester = request.GET.get('semester', '2025-2026-2')
    
    schedules = Schedule.objects.filter(venue=venue, semester=semester)
    
    # 转换为日历事件格式
    events = []
    for schedule in schedules:
        events.append({
            'title': f"{schedule.course_name} ({schedule.class_name or ''})",
            'day': schedule.day_of_week,
            'period': schedule.period,
            'teacher': schedule.teacher,
            'weeks': schedule.week_range,
        })
    
    return JsonResponse(events, safe=False)