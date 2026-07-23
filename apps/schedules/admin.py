from django.contrib import admin
from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """固定课表Admin"""
    
    list_display = ('course_name', 'venue', 'get_day_display', 'period', 
                    'week_range', 'teacher', 'class_name', 'semester', 'created_at')
    list_filter = ('semester', 'day_of_week', 'venue__building', 'created_at')
    search_fields = ('course_name', 'teacher', 'class_name', 'venue__name')
    ordering = ('-semester', 'day_of_week', 'period')
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('venue', 'course_name', 'teacher', 'semester')
        }),
        ('时间安排', {
            'fields': ('day_of_week', 'period', 'start_week', 'end_week')
        }),
        ('班级信息', {
            'fields': ('class_name', 'student_count')
        }),
        ('其他信息', {
            'fields': ('remark', 'created_by')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_day_display(self, obj):
        """显示星期几"""
        return obj.get_day_display()
    get_day_display.short_description = '星期'
    
    def week_range(self, obj):
        """显示周次范围"""
        return obj.week_range
    week_range.short_description = '周次'
    
    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)