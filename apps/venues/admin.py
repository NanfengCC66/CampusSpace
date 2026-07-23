from django.contrib import admin
from .models import Building, Room, Equipment, RoomEquipment


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    """楼宇Admin"""
    
    list_display = ('name', 'location', 'total_floors', 'room_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'location')
    ordering = ('name',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'location', 'total_floors', 'description')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """场地Admin"""
    
    list_display = ('name', 'building', 'floor', 'room_number', 'venue_type', 
                    'capacity', 'status', 'created_at')
    list_filter = ('venue_type', 'status', 'building', 'created_at')
    search_fields = ('name', 'building__name', 'room_number', 'manager')
    ordering = ('building', 'floor', 'room_number')
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'venue_type', 'building', 'floor', 'room_number')
        }),
        ('容量信息', {
            'fields': ('capacity', 'area')
        }),
        ('管理信息', {
            'fields': ('manager', 'manager_phone', 'status')
        }),
        ('其他信息', {
            'fields': ('description', 'created_by')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """设备Admin"""
    
    list_display = ('name', 'code', 'category', 'description')
    list_filter = ('category',)
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(RoomEquipment)
class RoomEquipmentAdmin(admin.ModelAdmin):
    """场地设备Admin"""
    
    list_display = ('room', 'equipment', 'quantity', 'status', 
                    'last_maintenance_date', 'next_maintenance_date')
    list_filter = ('status', 'equipment')
    search_fields = ('room__name', 'equipment__name')
    ordering = ('room',)
    
    raw_id_fields = ('room', 'equipment')