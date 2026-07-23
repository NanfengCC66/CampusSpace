"""
测试预约创建功能
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.venues.models import Room
from apps.bookings.services import BookingService

User = get_user_model()

print("=" * 60)
print("测试预约创建功能")
print("=" * 60)
print()

# 获取测试用户和场地
user = User.objects.filter(role='student').first()
venue = Room.objects.filter(status='available').first()

if not user:
    print("❌ 没有找到学生用户")
    sys.exit(1)

if not venue:
    print("❌ 没有找到可用场地")
    sys.exit(1)

print(f"✅ 测试用户: {user.username}")
print(f"✅ 测试场地: {venue.name} (容量: {venue.capacity})")
print()

# 测试创建预约
print("【测试1】创建正常预约")
print("-" * 60)

start_time = timezone.now() + timedelta(days=1, hours=9)
end_time = timezone.now() + timedelta(days=1, hours=11)

print(f"开始时间: {start_time}")
print(f"结束时间: {end_time}")
print(f"参与人数: 10")
print()

try:
    result = BookingService.create_booking(
        user=user,
        venue=venue,
        title='测试预约',
        booking_type='meeting',
        start_time=start_time,
        end_time=end_time,
        participant_count=10
    )
    
    print("预约创建结果:")
    print(f"  成功: {result['success']}")
    
    if result['success']:
        print(f"  预约编号: {result['booking'].booking_no}")
        print(f"  预约ID: {result['booking'].id}")
        print(f"  状态: {result['booking'].status}")
    else:
        print(f"  冲突数: {len(result['conflicts'])}")
        for conflict in result['conflicts']:
            print(f"    - {conflict['message']}")
    
except Exception as e:
    print(f"❌ 创建预约失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)