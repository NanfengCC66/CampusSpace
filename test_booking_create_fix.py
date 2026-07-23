#!/usr/bin/env python
"""测试预约创建功能修复"""
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
from datetime import datetime, timedelta
import json

User = get_user_model()

def test_booking_create():
    """测试预约创建功能"""
    client = Client()
    
    print("=" * 60)
    print("测试预约创建功能修复")
    print("=" * 60)
    
    # 1. 登录学生账号
    print("\n1. 登录学生账号...")
    student = User.objects.filter(username='student').first()
    if not student:
        print("❌ 学生账号不存在")
        return False
    
    client.login(username='student', password='student123')
    print(f"✅ 已登录: {student.username}")
    
    # 2. 获取场地列表
    print("\n2. 获取场地列表...")
    response = client.get(reverse('venues:room_list'))
    print(f"   状态码: {response.status_code}")
    if response.status_code != 200:
        print("❌ 获取场地列表失败")
        return False
    print("✅ 场地列表获取成功")
    
    # 3. 获取一个可用场地
    print("\n3. 获取可用场地...")
    venue = Room.objects.filter(status='available').first()
    if not venue:
        print("❌ 没有可用场地")
        return False
    print(f"✅ 选择场地: {venue.name} (ID: {venue.id})")
    
    # 4. 访问预约创建页面
    print("\n4. 访问预约创建页面...")
    url = reverse('bookings:booking_create') + f'?venue={venue.id}'
    response = client.get(url)
    print(f"   状态码: {response.status_code}")
    if response.status_code != 200:
        print("❌ 预约创建页面访问失败")
        return False
    print("✅ 预约创建页面访问成功")
    
    # 检查模板渲染
    content = response.content.decode('utf-8')
    if '创建预约' in content:
        print("✅ 页面标题正确")
    if 'name="title"' in content:
        print("✅ 表单字段正确")
    
    # 5. 提交预约表单
    print("\n5. 提交预约表单...")
    
    # 准备预约数据
    now = datetime.now()
    start_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
    
    booking_data = {
        'title': '测试预约-修复验证',
        'booking_type': 'meeting',
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'participant_count': 10,
        'contact_name': '测试联系人',
        'contact_phone': '13800138000',
        'remark': '这是一个测试预约，用于验证修复效果',
    }
    
    print(f"   预约数据:")
    print(f"   - 标题: {booking_data['title']}")
    print(f"   - 开始时间: {booking_data['start_time']}")
    print(f"   - 结束时间: {booking_data['end_time']}")
    print(f"   - 参与人数: {booking_data['participant_count']}")
    
    response = client.post(url, data=booking_data, follow=True)
    print(f"   响应状态码: {response.status_code}")
    print(f"   最终URL: {response.request['PATH_INFO']}")
    
    # 检查是否重定向到预约详情页
    if 'booking' in response.request['PATH_INFO'] or 'detail' in response.request['PATH_INFO']:
        print("✅ 表单提交成功，已重定向到预约详情页")
    elif 'list' in response.request['PATH_INFO']:
        print("✅ 表单提交成功，已重定向到预约列表页")
    else:
        print("⚠️  重定向位置不明确")
    
    # 检查消息
    messages = list(response.context.get('messages', []))
    if messages:
        print("\n   系统消息:")
        for msg in messages:
            print(f"   - [{msg.level_tag}] {msg.message}")
    
    # 6. 验证预约是否创建成功
    print("\n6. 验证预约创建结果...")
    booking = Booking.objects.filter(
        user=student,
        title='测试预约-修复验证'
    ).order_by('-created_at').first()
    
    if booking:
        print(f"✅ 预约创建成功!")
        print(f"   预约编号: {booking.booking_no}")
        print(f"   预约状态: {booking.get_status_display()}")
        print(f"   场地: {booking.venue.name}")
        print(f"   时间: {booking.start_time} ~ {booking.end_time}")
        return True
    else:
        print("❌ 预约创建失败")
        
        # 检查是否有表单错误
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'is-invalid' in content:
                print("   ⚠️  表单有验证错误")
            if '预约冲突' in content:
                print("   ⚠️  存在预约冲突")
        
        return False

def test_form_validation():
    """测试表单验证"""
    client = Client()
    
    print("\n" + "=" * 60)
    print("测试表单验证")
    print("=" * 60)
    
    # 登录
    student = User.objects.filter(username='student').first()
    client.login(username='student', password='student123')
    
    # 获取场地
    venue = Room.objects.filter(status='available').first()
    url = reverse('bookings:booking_create') + f'?venue={venue.id}'
    
    # 测试1: 缺少必填字段
    print("\n1. 测试缺少必填字段...")
    response = client.post(url, data={}, follow=True)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'is-invalid' in content or '必须' in content:
            print("✅ 表单验证正确触发")
        else:
            print("⚠️  表单验证可能未触发")
    
    # 测试2: 时间验证
    print("\n2. 测试时间验证...")
    now = datetime.now()
    invalid_data = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': now.strftime('%Y-%m-%d %H:%M:%S'),  # 过去时间
        'end_time': (now + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'participant_count': 10,
    }
    
    response = client.post(url, data=invalid_data, follow=True)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if '未来' in content or 'is-invalid' in content:
            print("✅ 时间验证正确触发")
        else:
            print("⚠️  时间验证可能未触发")
    
    # 测试3: 时长验证
    print("\n3. 测试时长验证...")
    start_time = now + timedelta(days=1)
    invalid_data = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': (start_time + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S'),  # 时长不足30分钟
        'participant_count': 10,
    }
    
    response = client.post(url, data=invalid_data, follow=True)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if '30分钟' in content or 'is-invalid' in content:
            print("✅ 时长验证正确触发")
        else:
            print("⚠️  时长验证可能未触发")

if __name__ == '__main__':
    try:
        success = test_booking_create()
        test_form_validation()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ 预约创建功能修复验证通过")
        else:
            print("❌ 预约创建功能仍有问题")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()