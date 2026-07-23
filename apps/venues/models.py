from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Building(models.Model):
    """楼宇模型"""
    
    name = models.CharField(
        _('楼宇名称'),
        max_length=100,
        unique=True
    )
    
    location = models.CharField(
        _('位置'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('楼宇的具体位置描述')
    )
    
    total_floors = models.IntegerField(
        _('总楼层数'),
        default=1
    )
    
    description = models.TextField(
        _('描述'),
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
    
    class Meta:
        db_table = 'venues_building'
        verbose_name = _('楼宇')
        verbose_name_plural = _('楼宇')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def room_count(self):
        """统计该楼宇的场地数量"""
        return self.rooms.count()


class Room(models.Model):
    """场地/教室模型"""
    
    class VenueType(models.TextChoices):
        CLASSROOM = 'classroom', _('教室')
        MEETING_ROOM = 'meeting_room', _('会议室')
        LAB = 'lab', _('实验室')
        ACTIVITY_ROOM = 'activity_room', _('活动室')
    
    class Status(models.TextChoices):
        AVAILABLE = 'available', _('可用')
        MAINTENANCE = 'maintenance', _('维修中')
        DISABLED = 'disabled', _('已停用')
    
    name = models.CharField(
        _('场地名称'),
        max_length=200
    )
    
    venue_type = models.CharField(
        _('场地类型'),
        max_length=50,
        choices=VenueType.choices,
        default=VenueType.CLASSROOM
    )
    
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name=_('所属楼宇')
    )
    
    floor = models.IntegerField(
        _('楼层'),
        blank=True,
        null=True
    )
    
    room_number = models.CharField(
        _('房间号'),
        max_length=50,
        blank=True,
        null=True
    )
    
    capacity = models.IntegerField(
        _('容纳人数'),
        help_text=_('场地可容纳的最大人数')
    )
    
    area = models.DecimalField(
        _('面积'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('单位：平方米')
    )
    
    manager = models.CharField(
        _('负责人'),
        max_length=100,
        blank=True,
        null=True
    )
    
    manager_phone = models.CharField(
        _('负责人电话'),
        max_length=20,
        blank=True,
        null=True
    )
    
    description = models.TextField(
        _('描述'),
        blank=True,
        null=True
    )
    
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
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
        related_name='created_rooms',
        verbose_name=_('创建人')
    )
    
    class Meta:
        db_table = 'venues_room'
        verbose_name = _('场地')
        verbose_name_plural = _('场地')
        ordering = ['building__name', 'floor', 'room_number']
        indexes = [
            models.Index(fields=['name'], name='idx_room_name'),
            models.Index(fields=['venue_type'], name='idx_room_type'),
            models.Index(fields=['building'], name='idx_room_building'),
            models.Index(fields=['status'], name='idx_room_status'),
        ]
    
    def __str__(self):
        return f"{self.building.name} - {self.name}"
    
    @property
    def full_name(self):
        """完整名称：楼宇-楼层-房间号"""
        parts = [self.building.name]
        if self.floor:
            parts.append(f"{self.floor}楼")
        if self.room_number:
            parts.append(self.room_number)
        return '-'.join(parts)
    
    @property
    def is_available(self):
        """判断是否可用"""
        return self.status == self.Status.AVAILABLE


class Equipment(models.Model):
    """设备模型"""
    
    name = models.CharField(
        _('设备名称'),
        max_length=100,
        unique=True
    )
    
    code = models.CharField(
        _('设备编码'),
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    
    category = models.CharField(
        _('设备分类'),
        max_length=50,
        blank=True,
        null=True
    )
    
    description = models.TextField(
        _('描述'),
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'venues_equipment'
        verbose_name = _('设备')
        verbose_name_plural = _('设备')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class RoomEquipment(models.Model):
    """场地设备关联模型"""
    
    class Status(models.TextChoices):
        NORMAL = 'normal', _('正常')
        BROKEN = 'broken', _('已损坏')
        MAINTENANCE = 'maintenance', _('维修中')
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='room_equipments',
        verbose_name=_('场地')
    )
    
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='room_equipments',
        verbose_name=_('设备')
    )
    
    quantity = models.IntegerField(
        _('数量'),
        default=1
    )
    
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.NORMAL
    )
    
    last_maintenance_date = models.DateField(
        _('最后维护日期'),
        blank=True,
        null=True
    )
    
    next_maintenance_date = models.DateField(
        _('下次维护日期'),
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'venues_room_equipment'
        verbose_name = _('场地设备')
        verbose_name_plural = _('场地设备')
        unique_together = ['room', 'equipment']
    
    def __str__(self):
        return f"{self.room.name} - {self.equipment.name}"