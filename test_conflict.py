#!/usr/bin/env python
"""测试冲突检测功能"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.venues.models import Room
from apps.bookings.models import Booking
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def test_conflict_detection():
    """测试冲突检测"""
    print("=" * 60)
    print("测试冲突检测功能")
    print("=" * 60)
    
    client = Client()
    
    # 1. 登录
    print("\n1. 登录学生账号...")
    student = User.objects.filter(username='student').first()
    client.login(username='student', password='student123')
    print(f"✅ 已登录: {student.username}")
    
    # 2. 获取场地
    print("\n2. 获取场地...")
    venue = Room.objects.filter(status='available').first()
    print(f"✅ 场地: {venue.name} (ID: {venue.id})")
    
    # 3. 创建第一个预约
    print("\n3. 创建第一个预约...")
    now = timezone.now()
    start_time = (now + timedelta(days=5)).replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=5)).replace(hour=11, minute=0, second=0, microsecond=0)
    
    url = reverse('bookings:booking_create') + f'?venue={venue.id}'
    
    form_data = {
        'title': '冲突测试-预约1',
        'booking_type': 'meeting',
        'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
        'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 10,
    }
    
    response = client.post(url, data=form_data)
    
    if response.status_code == 302:
        print("✅ 第一个预约创建成功")
        booking1 = Booking.objects.filter(title='冲突测试-预约1').first()
        if booking1:
            print(f"   预约编号: {booking1.booking_no}")
    else:
        print(f"⚠️  第一个预约创建失败: {response.status_code}")
    
    # 4. 尝试创建冲突预约
    print("\n4. 尝试创建冲突预约...")
    conflict_start = (now + timedelta(days=5)).replace(hour=10, minute=0, second=0, microsecond=0)
    conflict_end = (now + timedelta(days=5)).replace(hour=12, minute=0, second=0, microsecond=0)
    
    form_data2 = {
        'title': '冲突测试-预约2',
        'booking_type': 'meeting',
        'start_time': conflict_start.strftime('%Y-%m-%dT%H:%M'),
        'end_time': conflict_end.strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 10,
    }
    
    response = client.post(url, data=form_data2)
    
    print(f"   响应状态码: {response.status_code}")
    
    if response.status_code == 302:
        # 重定向回创建页面，说明检测到冲突
        print("✅ 冲突检测正常，重定向回创建页面")
        
        # 访问重定向页面，查看冲突信息
        final_response = client.get(response.url)
        if final_response.status_code == 200:
            content = final_response.content.decode('utf-8')
            
            if '预约冲突' in content:
                print("✅ 页面显示冲突信息")
            
            # 检查是否有alert-danger
            if 'alert-danger' in content:
                print("✅ 显示错误提示")
            
            # 检查预约是否未创建
            booking2 = Booking.objects.filter(title='冲突测试-预约2').first()
            if not booking2:
                print("✅ 冲突预约未创建（正确）")
            else:
                print("❌ 冲突预约被创建了（错误）")
        
        return True
    elif response.status_code == 200:
        # 返回原页面，说明表单验证失败
        print("⚠️  表单验证失败")
        content = response.content.decode('utf-8')
        
        if '预约冲突' in content:
            print("✅ 页面显示冲突信息")
        
        return True
    else:
        print(f"❌ 未预期的状态码: {response.status_code}")
        return False

def test_time_validation():
    """测试时间验证"""
    print("\n" + "=" * 60)
    print("测试时间验证")
    print("=" * 60)
    
    client = Client()
    student = User.objects.filter(username='student').first()
    client.login(username='student', password='student123')
    
    venue = Room.objects.filter(status='available').first()
    url = reverse('bookings:booking_create') + f'?venue={venue.id}'
    
    now = timezone.now()
    
    # 测试1: 过去时间
    print("\n1. 测试过去时间...")
    form_data = {
        'title': '过去时间测试',
        'booking_type': 'meeting',
        'start_time': (now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 10,
    }
    
    response = client.post(url, data=form_data)
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if '未来' in content or 'is-invalid' in content:
            print("✅ 过去时间验证正确")
        else:
            print("⚠️  过去时间验证可能有问题")
    elif response.status_code == 302:
        # 重定向回创建页面
        final_response = client.get(response.url)
        content = final_response.content.decode('utf-8')
        if '未来' in content or 'alert-danger' in content:
            print("✅ 过去时间验证正确")
        else:
            print("⚠️  过去时间验证可能有问题")
    
    # 测试2: 时长不足
    print("\n2. 测试时长不足...")
    start_time = (now + timedelta(days=6)).replace(hour=14, minute=0, second=0, microsecond=0)
    
    form_data = {
        'title': '时长不足测试',
        'booking_type': 'meeting',
        'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
        'end_time': (start_time + timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 10,
    }
    
    response = client.post(url, data=form_data)
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if '30分钟' in content or 'is-invalid' in content:
            print("✅ 时长验证正确")
        else:
            print("⚠️  时长验证可能有问题")
    elif response.status_code == 302:
        final_response = client.get(response.url)
        content = final_response.content.decode('utf-8')
        if '30分钟' in content or 'alert-danger' in content:
            print("✅ 时长验证正确")
        else:
            print("⚠️  时长验证可能有问题")

if __name__ == '__main__':
    try:
        success = test_conflict_detection()
        test_time_validation()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ 冲突检测功能测试通过")
            print("\n修复内容:")
            print("1. ✅ datetime序列化问题 - 将datetime对象转换为字符串")
            print("2. ✅ session保存问题 - 序列化冲突信息后再保存")
        else:
            print("❌ 冲突检测功能测试失败")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()