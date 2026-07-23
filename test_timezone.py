#!/usr/bin/env python
"""测试时区显示修复"""
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

def test_timezone_display():
    """测试时区显示"""
    print("=" * 70)
    print(" 测试时区显示修复")
    print("=" * 70)
    
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
    
    # 3. 创建第一个预约（使用本地时间）
    print("\n3. 创建第一个预约...")
    now = timezone.now()
    # 使用本地时间：下午2点到4点
    local_now = timezone.localtime(now)
    print(f"   当前本地时间: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建明天的预约：14:00-16:00（本地时间）
    tomorrow = local_now.date() + timedelta(days=1)
    start_time_local = timezone.make_aware(
        timezone.datetime.combine(tomorrow, timezone.datetime.min.time().replace(hour=14, minute=0))
    )
    end_time_local = timezone.make_aware(
        timezone.datetime.combine(tomorrow, timezone.datetime.min.time().replace(hour=16, minute=0))
    )
    
    print(f"   预约时间（本地）: {timezone.localtime(start_time_local).strftime('%Y-%m-%d %H:%M')} - {timezone.localtime(end_time_local).strftime('%Y-%m-%d %H:%M')}")
    print(f"   预约时间（UTC）: {start_time_local.strftime('%Y-%m-%d %H:%M')} - {end_time_local.strftime('%Y-%m-%d %H:%M')}")
    
    url = reverse('bookings:booking_create') + f'?venue={venue.id}'
    
    # 表单提交使用datetime-local格式（本地时间）
    form_data = {
        'title': '时区测试-预约1',
        'booking_type': 'meeting',
        'start_time': start_time_local.strftime('%Y-%m-%dT%H:%M'),
        'end_time': end_time_local.strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 10,
    }
    
    response = client.post(url, data=form_data)
    
    if response.status_code == 302:
        print("✅ 第一个预约创建成功")
        booking1 = Booking.objects.filter(title='时区测试-预约1').first()
        if booking1:
            print(f"   预约编号: {booking1.booking_no}")
            print(f"   数据库时间（UTC）: {booking1.start_time.strftime('%Y-%m-%d %H:%M')} - {booking1.end_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"   本地时间: {timezone.localtime(booking1.start_time).strftime('%Y-%m-%d %H:%M')} - {timezone.localtime(booking1.end_time).strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"⚠️  第一个预约创建失败: {response.status_code}")
    
    # 4. 尝试创建冲突预约
    print("\n4. 尝试创建冲突预约...")
    # 创建一个重叠的预约：15:00-17:00（本地时间）
    conflict_start_local = timezone.make_aware(
        timezone.datetime.combine(tomorrow, timezone.datetime.min.time().replace(hour=15, minute=0))
    )
    conflict_end_local = timezone.make_aware(
        timezone.datetime.combine(tomorrow, timezone.datetime.min.time().replace(hour=17, minute=0))
    )
    
    print(f"   冲突预约时间（本地）: {timezone.localtime(conflict_start_local).strftime('%Y-%m-%d %H:%M')} - {timezone.localtime(conflict_end_local).strftime('%Y-%m-%d %H:%M')}")
    
    form_data2 = {
        'title': '时区测试-预约2',
        'booking_type': 'meeting',
        'start_time': conflict_start_local.strftime('%Y-%m-%dT%H:%M'),
        'end_time': conflict_end_local.strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 10,
    }
    
    response = client.post(url, data=form_data2)
    
    print(f"   响应状态码: {response.status_code}")
    
    if response.status_code == 302:
        # 重定向回创建页面，说明检测到冲突
        print("✅ 冲突检测正常")
        
        # 访问重定向页面，查看冲突信息
        final_response = client.get(response.url)
        if final_response.status_code == 200:
            content = final_response.content.decode('utf-8')
            
            # 提取冲突提示中的时间
            import re
            time_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})至(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
            matches = re.findall(time_pattern, content)
            
            if matches:
                print("\n   冲突提示中显示的时间:")
                for start, end in matches:
                    print(f"   - {start} 至 {end}")
                
                # 检查是否是本地时间
                expected_start = timezone.localtime(booking1.start_time).strftime('%Y-%m-%d %H:%M')
                expected_end = timezone.localtime(booking1.end_time).strftime('%Y-%m-%d %H:%M')
                
                print(f"\n   期望显示的时间（本地）: {expected_start} 至 {expected_end}")
                
                if matches[0][0] == expected_start and matches[0][1] == expected_end:
                    print("✅ 时区显示正确！显示的是本地时间")
                    return True
                else:
                    print("❌ 时区显示错误！显示的不是本地时间")
                    return False
            else:
                print("⚠️  未找到冲突提示")
                return False
    else:
        print(f"❌ 未预期的状态码: {response.status_code}")
        return False

if __name__ == '__main__':
    try:
        success = test_timezone_display()
        
        print("\n" + "=" * 70)
        if success:
            print("✅ 时区显示修复成功")
        else:
            print("❌ 时区显示修复失败")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()