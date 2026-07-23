#!/usr/bin/env python
"""直接测试预约创建服务"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.venues.models import Room
from apps.bookings.models import Booking
from apps.bookings.services import BookingService
from datetime import datetime, timedelta

User = get_user_model()

def test_booking_service():
    """直接测试预约创建服务"""
    print("=" * 60)
    print("测试预约创建服务")
    print("=" * 60)
    
    # 1. 获取用户
    print("\n1. 获取测试用户...")
    student = User.objects.filter(username='student').first()
    if not student:
        print("❌ 学生账号不存在")
        return False
    print(f"✅ 学生账号: {student.username}")
    
    # 2. 获取场地
    print("\n2. 获取可用场地...")
    venue = Room.objects.filter(status='available').first()
    if not venue:
        print("❌ 没有可用场地")
        return False
    print(f"✅ 场地: {venue.name} (容量: {venue.capacity})")
    print(f"   楼宇: {venue.building.name}")
    
    # 3. 准备预约数据
    print("\n3. 准备预约数据...")
    now = timezone.now()
    start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
    
    print(f"   标题: 测试预约-服务层验证")
    print(f"   开始时间: {start_time}")
    print(f"   结束时间: {end_time}")
    print(f"   参与人数: 10")
    
    # 4. 创建预约
    print("\n4. 创建预约...")
    try:
        result = BookingService.create_booking(
            user=student,
            venue=venue,
            title='测试预约-服务层验证',
            booking_type='meeting',
            start_time=start_time,
            end_time=end_time,
            participant_count=10,
            required_equipments=[],
            contact_name='测试联系人',
            contact_phone='13800138000',
            remark='服务层测试'
        )
        
        if result['success']:
            print("✅ 预约创建成功!")
            booking = result['booking']
            print(f"   预约编号: {booking.booking_no}")
            print(f"   预约状态: {booking.get_status_display()}")
            print(f"   场地: {booking.venue.name}")
            print(f"   时间: {booking.start_time} ~ {booking.end_time}")
            
            if result.get('equipment_warning'):
                print(f"   ⚠️  设备警告: {result['equipment_warning']}")
            
            return True
        else:
            print("❌ 预约创建失败")
            print(f"   冲突信息:")
            for conflict in result.get('conflicts', []):
                print(f"   - {conflict.get('message', conflict)}")
            
            if result.get('equipment_warning'):
                print(f"   设备警告: {result['equipment_warning']}")
            
            return False
            
    except Exception as e:
        print(f"❌ 创建预约时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conflict_detection():
    """测试冲突检测"""
    print("\n" + "=" * 60)
    print("测试冲突检测")
    print("=" * 60)
    
    student = User.objects.filter(username='student').first()
    venue = Room.objects.filter(status='available').first()
    
    # 创建第一个预约
    now = timezone.now()
    start_time = (now + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=2)).replace(hour=16, minute=0, second=0, microsecond=0)
    
    print("\n1. 创建第一个预约...")
    result1 = BookingService.create_booking(
        user=student,
        venue=venue,
        title='冲突测试-预约1',
        booking_type='meeting',
        start_time=start_time,
        end_time=end_time,
        participant_count=10,
        required_equipments=[]
    )
    
    if result1['success']:
        print(f"✅ 第一个预约创建成功: {result1['booking'].booking_no}")
    else:
        print("⚠️  第一个预约创建失败（可能已存在冲突）")
    
    # 尝试创建冲突预约
    print("\n2. 尝试创建冲突预约...")
    conflict_start = (now + timedelta(days=2)).replace(hour=15, minute=0, second=0, microsecond=0)
    conflict_end = (now + timedelta(days=2)).replace(hour=17, minute=0, second=0, microsecond=0)
    
    result2 = BookingService.create_booking(
        user=student,
        venue=venue,
        title='冲突测试-预约2',
        booking_type='meeting',
        start_time=conflict_start,
        end_time=conflict_end,
        participant_count=10,
        required_equipments=[]
    )
    
    if result2['success']:
        print("⚠️  冲突预约创建成功（不应该）")
        return False
    else:
        print("✅ 冲突检测正常工作")
        print(f"   冲突信息:")
        for conflict in result2.get('conflicts', []):
            print(f"   - {conflict.get('message', conflict)}")
        return True

def test_form_data():
    """测试表单数据格式"""
    print("\n" + "=" * 60)
    print("测试表单数据格式")
    print("=" * 60)
    
    from apps.bookings.forms import BookingCreateForm
    
    now = timezone.now()
    start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
    
    # 测试有效数据
    print("\n1. 测试有效数据...")
    valid_data = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': start_time,
        'end_time': end_time,
        'participant_count': 10,
    }
    
    form = BookingCreateForm(data=valid_data)
    if form.is_valid():
        print("✅ 表单验证通过")
        print(f"   清洗后数据: {form.cleaned_data}")
    else:
        print("❌ 表单验证失败")
        print(f"   错误: {form.errors}")
    
    # 测试无效数据 - 过去时间
    print("\n2. 测试无效数据（过去时间）...")
    invalid_data = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': now - timedelta(hours=2),
        'end_time': now + timedelta(hours=2),
        'participant_count': 10,
    }
    
    form = BookingCreateForm(data=invalid_data)
    if form.is_valid():
        print("⚠️  表单验证通过（不应该）")
    else:
        print("✅ 表单验证正确失败")
        print(f"   错误: {form.errors}")
    
    # 测试无效数据 - 时长不足
    print("\n3. 测试无效数据（时长不足）...")
    invalid_data2 = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': start_time,
        'end_time': start_time + timedelta(minutes=15),
        'participant_count': 10,
    }
    
    form = BookingCreateForm(data=invalid_data2)
    if form.is_valid():
        print("⚠️  表单验证通过（不应该）")
    else:
        print("✅ 表单验证正确失败")
        print(f"   错误: {form.errors}")

if __name__ == '__main__':
    try:
        success1 = test_booking_service()
        success2 = test_conflict_detection()
        test_form_data()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("✅ 所有测试通过")
        else:
            print("⚠️  部分测试失败")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()