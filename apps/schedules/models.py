from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.venues.models import Room


class Schedule(models.Model):
    """固定课表模型"""
    
    venue = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('场地')
    )
    
    course_name = models.CharField(
        _('课程名称'),
        max_length=200
    )
    
    teacher = models.CharField(
        _('授课教师'),
        max_length=100,
        blank=True,
        null=True
    )
    
    day_of_week = models.IntegerField(
        _('周几'),
        help_text=_('1-7，周一到周日')
    )
    
    period = models.CharField(
        _('节次'),
        max_length=20,
        help_text=_('如：1-2, 3-4, 5-6等')
    )
    
    start_week = models.IntegerField(
        _('开始周次')
    )
    
    end_week = models.IntegerField(
        _('结束周次')
    )
    
    class_name = models.CharField(
        _('班级'),
        max_length=100,
        blank=True,
        null=True
    )
    
    student_count = models.IntegerField(
        _('学生人数'),
        blank=True,
        null=True
    )
    
    semester = models.CharField(
        _('学期'),
        max_length=50,
        help_text=_('如：2025-2026-2')
    )
    
    remark = models.TextField(
        _('备注'),
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(
        _('创建时间'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('更新时间'),
        auto_now=True
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_schedules',
        verbose_name=_('创建人')
    )
    
    class Meta:
        db_table = 'schedules_schedule'
        verbose_name = _('固定课表')
        verbose_name_plural = _('固定课表')
        ordering = ['semester', 'day_of_week', 'period']
        indexes = [
            models.Index(fields=['venue'], name='idx_schedule_venue'),
            models.Index(fields=['semester'], name='idx_schedule_semester'),
            models.Index(fields=['day_of_week'], name='idx_schedule_day'),
        ]
    
    def __str__(self):
        return f"{self.venue.name} - {self.course_name} ({self.get_day_display()})"
    
    def get_day_display(self):
        """获取星期几的中文显示"""
        days = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return days[self.day_of_week] if 1 <= self.day_of_week <= 7 else ''
    
    @property
    def week_range(self):
        """获取周次范围"""
        if self.start_week == self.end_week:
            return f"第{self.start_week}周"
        return f"第{self.start_week}-{self.end_week}周"
    
    def clean(self):
        """数据验证"""
        from django.core.exceptions import ValidationError
        
        # 验证周几
        if not 1 <= self.day_of_week <= 7:
            raise ValidationError({'day_of_week': '周几必须在1-7之间'})
        
        # 验证周次
        if self.end_week < self.start_week:
            raise ValidationError({'end_week': '结束周次不能小于开始周次'})