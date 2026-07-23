import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.venues.models import Building, Room, Equipment
from apps.bookings.models import Booking, Approval
from apps.schedules.models import Schedule
from apps.maintenance.models import Maintenance

User = get_user_model()

print('='*60)
print('CampusSpace 数据统计')
print('='*60)
print()
print('【用户数据】')
print(f'  用户总数：{User.objects.count()}')
print(f'    - 管理员：{User.objects.filter(role="admin").count()}')
print(f'    - 教师：{User.objects.filter(role="teacher").count()}')
print(f'    - 学生：{User.objects.filter(role="student").count()}')
print()
print('【场地数据】')
print(f'  楼宇总数：{Building.objects.count()}')
for building in Building.objects.all():
    print(f'    - {building.name}：{building.rooms.count()} 个场地')
print(f'  场地总数：{Room.objects.count()}')
print(f'  设备类型：{Equipment.objects.count()}')
print()
print('【课表数据】')
print(f'  固定课表：{Schedule.objects.count()}')
print()
print('【预约数据】')
print(f'  预约总数：{Booking.objects.count()}')
print(f'    - 待审批：{Booking.objects.filter(status="pending").count()}')
print(f'    - 已通过：{Booking.objects.filter(status="approved").count()}')
print(f'    - 已拒绝：{Booking.objects.filter(status="rejected").count()}')
print(f'    - 已取消：{Booking.objects.filter(status="cancelled").count()}')
print(f'    - 已完成：{Booking.objects.filter(status="completed").count()}')
print(f'  审批记录：{Approval.objects.count()}')
print()
print('【维修数据】')
print(f'  维修记录：{Maintenance.objects.count()}')
print()
print('='*60)
print('演示账号：')
print('  管理员: admin / admin123')
print('  教师: teacher_zhang / teacher123')
print('  学生: student001 / student123')
print('='*60)