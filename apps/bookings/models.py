from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.venues.models import Room
import json


class Booking(models.Model):
    """预约模型"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('待审批')
        APPROVED = 'approved', _('已通过')
        REJECTED = 'rejected', _('已拒绝')
        CANCELLED = 'cancelled', _('已取消')
        COMPLETED = 'completed', _('已完成')
        EXPIRED = 'expired', _('已过期')
    
    class BookingType(models.TextChoices):
        TEACHING = 'teaching', _('教学')
        MEETING = 'meeting', _('会议')
        ACTIVITY = 'activity', _('活动')
        SELF_STUDY = 'self_study', _('自习')
    
    booking_no = models.CharField(
        _('预约编号'),
        max_length=50,
        unique=True,
        db_index=True
    )
    
    venue = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('场地')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('预约人')
    )
    
    title = models.CharField(
        _('使用目的'),
        max_length=200
    )
    
    booking_type = models.CharField(
        _('预约用途'),
        max_length=20,
        choices=BookingType.choices,
        default=BookingType.MEETING
    )
    
    start_time = models.DateTimeField(
        _('开始时间'),
        db_index=True
    )
    
    end_time = models.DateTimeField(
        _('结束时间'),
        db_index=True
    )
    
    participant_count = models.IntegerField(
        _('参与人数')
    )
    
    required_equipments = models.JSONField(
        _('所需设备'),
        default=list,
        blank=True,
        help_text=_('设备ID列表')
    )
    
    contact_name = models.CharField(
        _('联系人'),
        max_length=100,
        blank=True,
        null=True
    )
    
    contact_phone = models.CharField(
        _('联系电话'),
        max_length=20,
        blank=True,
        null=True
    )
    
    remark = models.TextField(
        _('备注'),
        blank=True,
        null=True
    )
    
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    
    priority = models.IntegerField(
        _('优先级'),
        default=0,
        help_text=_('教师=1，学生=0')
    )
    
    cancel_reason = models.TextField(
        _('取消原因'),
        blank=True,
        null=True
    )
    
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_bookings',
        verbose_name=_('取消人')
    )
    
    cancelled_at = models.DateTimeField(
        _('取消时间'),
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(
        _('创建时间'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('更新时间'),
        auto_now=True
    )
    
    class Meta:
        db_table = 'bookings_booking'
        verbose_name = _('预约')
        verbose_name_plural = _('预约')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['venue', 'start_time', 'end_time'], name='idx_booking_time'),
            models.Index(fields=['user', 'status'], name='idx_booking_user'),
        ]
    
    def __str__(self):
        return f"{self.booking_no} - {self.venue.name}"
    
    @property
    def duration(self):
        """计算预约时长（分钟）"""
        duration = self.end_time - self.start_time
        return int(duration.total_seconds() / 60)
    
    @property
    def duration_display(self):
        """显示预约时长"""
        minutes = self.duration
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0 and mins > 0:
            return f"{hours}小时{mins}分钟"
        elif hours > 0:
            return f"{hours}小时"
        else:
            return f"{mins}分钟"
    
    def get_required_equipment_names(self):
        """获取所需设备名称列表"""
        from apps.venues.models import Equipment
        
        if not self.required_equipments:
            return []
        
        equipment_ids = self.required_equipments if isinstance(self.required_equipments, list) else json.loads(self.required_equipments)
        equipments = Equipment.objects.filter(id__in=equipment_ids)
        return [eq.name for eq in equipments]
    
    def save(self, *args, **kwargs):
        """保存时自动设置优先级"""
        if not self.priority:
            # 教师优先级为1，学生为0
            if hasattr(self.user, 'role') and self.user.role == 'teacher':
                self.priority = 1
            else:
                self.priority = 0
        
        super().save(*args, **kwargs)
    
    def get_status_color(self):
        """获取状态对应的颜色"""
        colors = {
            self.Status.PENDING: '#ffc107',      # 黄色
            self.Status.APPROVED: '#28a745',     # 绿色
            self.Status.REJECTED: '#dc3545',     # 红色
            self.Status.CANCELLED: '#6c757d',    # 灰色
            self.Status.COMPLETED: '#17a2b8',    # 青色
            self.Status.EXPIRED: '#856404',      # 深黄色
        }
        return colors.get(self.status, '#007bff')
    
    def get_status_badge_class(self):
        """获取状态对应的 Bootstrap badge 类"""
        classes = {
            self.Status.PENDING: 'warning',
            self.Status.APPROVED: 'success',
            self.Status.REJECTED: 'danger',
            self.Status.CANCELLED: 'secondary',
            self.Status.COMPLETED: 'info',
            self.Status.EXPIRED: 'dark',
        }
        return classes.get(self.status, 'primary')


class Approval(models.Model):
    """审批记录模型"""
    
    class Action(models.TextChoices):
        APPROVE = 'approve', _('通过')
        REJECT = 'reject', _('拒绝')
    
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name=_('预约')
    )
    
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name=_('审批人')
    )
    
    action = models.CharField(
        _('审批动作'),
        max_length=20,
        choices=Action.choices
    )
    
    comment = models.TextField(
        _('审批意见'),
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(
        _('审批时间'),
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'bookings_approval'
        verbose_name = _('审批记录')
        verbose_name_plural = _('审批记录')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.booking.booking_no} - {self.get_action_display()} - {self.approver.username}"


class Notification(models.Model):
    """站内消息模型"""
    
    class NotificationType(models.TextChoices):
        SYSTEM = 'system', _('系统消息')
        BOOKING = 'booking', _('预约消息')
        APPROVAL = 'approval', _('审批消息')
        REMINDER = 'reminder', _('提醒消息')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('接收用户')
    )
    
    title = models.CharField(
        _('消息标题'),
        max_length=200
    )
    
    content = models.TextField(
        _('消息内容')
    )
    
    notification_type = models.CharField(
        _('消息类型'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    
    is_read = models.BooleanField(
        _('是否已读'),
        default=False,
        db_index=True
    )
    
    link = models.CharField(
        _('相关链接'),
        max_length=200,
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(
        _('创建时间'),
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'bookings_notification'
        verbose_name = _('站内消息')
        verbose_name_plural = _('站内消息')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='idx_notification_user_read'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """标记为已读"""
        self.is_read = True
        self.save(update_fields=['is_read'])