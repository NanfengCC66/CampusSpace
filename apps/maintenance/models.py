from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.venues.models import Room


class Maintenance(models.Model):
    """维修停用模型"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('待审批')
        APPROVED = 'approved', _('已审批')
        ONGOING = 'ongoing', _('进行中')
        COMPLETED = 'completed', _('已完成')
        REJECTED = 'rejected', _('已拒绝')
    
    class ApprovalStatus(models.TextChoices):
        PENDING = 'pending', _('待审批')
        APPROVED = 'approved', _('已通过')
        REJECTED = 'rejected', _('已拒绝')
    
    venue = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='maintenances',
        verbose_name=_('场地')
    )
    
    reason = models.CharField(
        _('停用原因'),
        max_length=200
    )
    
    start_time = models.DateTimeField(
        _('开始时间')
    )
    
    end_time = models.DateTimeField(
        _('预计结束时间')
    )
    
    actual_end_time = models.DateTimeField(
        _('实际结束时间'),
        blank=True,
        null=True
    )
    
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    approval_status = models.CharField(
        _('审批状态'),
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_maintenances',
        verbose_name=_('审批人')
    )
    
    approved_at = models.DateTimeField(
        _('审批时间'),
        blank=True,
        null=True
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
        related_name='created_maintenances',
        verbose_name=_('创建人')
    )
    
    class Meta:
        db_table = 'maintenance_maintenance'
        verbose_name = _('维修停用')
        verbose_name_plural = _('维修停用')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['venue'], name='idx_maintenance_venue'),
            models.Index(fields=['status'], name='idx_maintenance_status'),
            models.Index(fields=['start_time', 'end_time'], name='idx_maintenance_time'),
        ]
    
    def __str__(self):
        return f"{self.venue.name} - {self.reason} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """判断是否正在进行"""
        return self.status == self.Status.ONGOING
    
    @property
    def duration(self):
        """计算维修时长"""
        if self.actual_end_time:
            duration = self.actual_end_time - self.start_time
        else:
            duration = self.end_time - self.start_time
        
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}天{hours}小时"
        elif hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def approve(self, user):
        """审批通过"""
        from django.utils import timezone
        
        self.status = self.Status.APPROVED
        self.approval_status = self.ApprovalStatus.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, user):
        """审批拒绝"""
        from django.utils import timezone
        
        self.status = self.Status.REJECTED
        self.approval_status = self.ApprovalStatus.REJECTED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def start(self):
        """开始维修"""
        self.status = self.Status.ONGOING
        self.save()
    
    def complete(self, actual_end_time=None):
        """完成维修"""
        from django.utils import timezone
        
        self.status = self.Status.COMPLETED
        self.actual_end_time = actual_end_time or timezone.now()
        self.save()