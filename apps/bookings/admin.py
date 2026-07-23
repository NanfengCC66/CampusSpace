from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """预约Admin"""
    
    list_display = ('booking_no', 'venue', 'user', 'title', 'booking_type',
                    'start_time', 'end_time', 'participant_count', 'status', 'priority')
    list_filter = ('status', 'booking_type', 'venue__building', 'created_at')
    search_fields = ('booking_no', 'title', 'user__username', 'venue__name')
    ordering = ('-created_at',)
    
    readonly_fields = ('booking_no', 'created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('booking_no', 'venue', 'user', 'title', 'booking_type')
        }),
        ('时间信息', {
            'fields': ('start_time', 'end_time')
        }),
        ('预约详情', {
            'fields': ('participant_count', 'required_equipments', 'contact_name', 'contact_phone', 'remark')
        }),
        ('状态信息', {
            'fields': ('status', 'priority')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        """批量审批通过"""
        count = queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f'成功审批通过 {count} 条预约')
    approve_selected.short_description = '审批通过所选预约'
    
    def reject_selected(self, request, queryset):
        """批量审批拒绝"""
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'成功审批拒绝 {count} 条预约')
    reject_selected.short_description = '审批拒绝所选预约'