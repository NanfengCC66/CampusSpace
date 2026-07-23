from django.contrib import admin
from django.utils import timezone
from .models import Maintenance


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    """维修停用Admin"""
    
    list_display = ('venue', 'reason', 'start_time', 'end_time', 
                    'duration', 'status', 'approval_status', 'created_by', 'created_at')
    list_filter = ('status', 'approval_status', 'venue__building', 'created_at')
    search_fields = ('venue__name', 'reason', 'created_by__username')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'duration')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('venue', 'reason', 'remark')
        }),
        ('时间信息', {
            'fields': ('start_time', 'end_time', 'actual_end_time')
        }),
        ('状态信息', {
            'fields': ('status', 'approval_status')
        }),
        ('审批信息', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('其他信息', {
            'fields': ('created_by',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_selected', 'reject_selected', 'start_selected', 'complete_selected']
    
    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def approve_selected(self, request, queryset):
        """批量审批通过"""
        count = 0
        for maintenance in queryset.filter(status='pending'):
            maintenance.approve(request.user)
            count += 1
        self.message_user(request, f'成功审批通过 {count} 条维修申请。')
    approve_selected.short_description = '审批通过所选维修申请'
    
    def reject_selected(self, request, queryset):
        """批量审批拒绝"""
        count = 0
        for maintenance in queryset.filter(status='pending'):
            maintenance.reject(request.user)
            count += 1
        self.message_user(request, f'成功审批拒绝 {count} 条维修申请。')
    reject_selected.short_description = '审批拒绝所选维修申请'
    
    def start_selected(self, request, queryset):
        """批量开始维修"""
        count = queryset.filter(status='approved').update(status='ongoing')
        self.message_user(request, f'成功开始 {count} 条维修。')
    start_selected.short_description = '开始所选维修'
    
    def complete_selected(self, request, queryset):
        """批量完成维修"""
        count = 0
        for maintenance in queryset.filter(status='ongoing'):
            maintenance.complete()
            count += 1
        self.message_user(request, f'成功完成 {count} 条维修。')
    complete_selected.short_description = '完成所选维修'