from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from .models import Maintenance
from apps.venues.models import Room


class MaintenanceListView(LoginRequiredMixin, ListView):
    """维修停用列表视图"""
    model = Maintenance
    template_name = 'maintenance/maintenance_list.html'
    context_object_name = 'maintenances'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        venue_id = self.request.GET.get('venue')
        
        if status:
            queryset = queryset.filter(status=status)
        if venue_id:
            queryset = queryset.filter(venue_id=venue_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venues'] = Room.objects.all()
        context['status_choices'] = Maintenance.Status.choices
        return context


class MaintenanceDetailView(LoginRequiredMixin, DetailView):
    """维修停用详情视图"""
    model = Maintenance
    template_name = 'maintenance/maintenance_detail.html'
    context_object_name = 'maintenance'


class MaintenanceCreateView(LoginRequiredMixin, CreateView):
    """创建维修停用视图"""
    model = Maintenance
    template_name = 'maintenance/maintenance_form.html'
    fields = ['venue', 'reason', 'start_time', 'end_time', 'remark']
    success_url = reverse_lazy('maintenance:maintenance_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '维修申请已提交，等待审批！')
        return super().form_valid(form)


class MaintenanceUpdateView(LoginRequiredMixin, UpdateView):
    """更新维修停用视图"""
    model = Maintenance
    template_name = 'maintenance/maintenance_form.html'
    fields = ['venue', 'reason', 'start_time', 'end_time', 'remark']
    success_url = reverse_lazy('maintenance:maintenance_list')
    
    def form_valid(self, form):
        messages.success(self.request, '维修信息更新成功！')
        return super().form_valid(form)


@login_required
def approve_maintenance(request, pk):
    """审批维修申请"""
    maintenance = get_object_or_404(Maintenance, pk=pk)
    
    if maintenance.status != Maintenance.Status.PENDING:
        messages.error(request, '该维修申请已处理！')
        return redirect('maintenance:maintenance_detail', pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            maintenance.approve(request.user)
            messages.success(request, '维修申请已通过！')
        elif action == 'reject':
            maintenance.reject(request.user)
            messages.warning(request, '维修申请已拒绝！')
        
        return redirect('maintenance:maintenance_list')
    
    return render(request, 'maintenance/maintenance_approve.html', {'maintenance': maintenance})


@login_required
def start_maintenance(request, pk):
    """开始维修"""
    maintenance = get_object_or_404(Maintenance, pk=pk)
    
    if maintenance.status != Maintenance.Status.APPROVED:
        messages.error(request, '该维修申请未审批或已开始！')
        return redirect('maintenance:maintenance_detail', pk=pk)
    
    maintenance.start()
    messages.success(request, '维修已开始！')
    return redirect('maintenance:maintenance_detail', pk=pk)


@login_required
def complete_maintenance(request, pk):
    """完成维修"""
    maintenance = get_object_or_404(Maintenance, pk=pk)
    
    if maintenance.status != Maintenance.Status.ONGOING:
        messages.error(request, '该维修未开始或已完成！')
        return redirect('maintenance:maintenance_detail', pk=pk)
    
    maintenance.complete()
    messages.success(request, '维修已完成！')
    return redirect('maintenance:maintenance_detail', pk=pk)