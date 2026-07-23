#!/usr/bin/env python
"""测试前端表单提交"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.venues.models import Room
from apps.bookings.models import Booking
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def test_form_submission():
    """测试表单提交"""
    print("=" * 60)
    print("测试前端表单提交")
    print("=" * 60)
    
    client = Client()
    
    # 1. 登录
    print("\n1. 登录学生账号...")
    student = User.objects.filter(username='student').first()
    logged_in = client.login(username='student', password='student123')
    print(f"   登录状态: {logged_in}")
    
    # 2. 获取场地
    print("\n2. 获取场地...")
    venue = Room.objects.filter(status='available').first()
    print(f"   场地: {venue.name} (ID: {venue.id})")
    
    # 3. 访问预约创建页面
    print("\n3. 访问预约创建页面...")
    url = reverse('bookings:booking_create') + f'?venue={venue.id}'
    print(f"   URL: {url}")
    
    response = client.get(url)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   响应内容: {response.content.decode('utf-8')[:500]}")
        print(f"   响应头: {dict(response.items())}")
    
    if response.status_code == 200:
        print("✅ 页面访问成功")
        content = response.content.decode('utf-8')
        
        # 检查页面内容
        if '创建预约' in content:
            print("✅ 页面标题正确")
        if 'name="title"' in content:
            print("✅ 表单字段存在")
        if 'csrfmiddlewaretoken' in content:
            print("✅ CSRF token存在")
    else:
        print(f"❌ 页面访问失败: {response.status_code}")
        return False
    
    # 4. 提交表单
    print("\n4. 提交表单...")
    
    now = timezone.now()
    start_time = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    
    # 模拟前端表单数据
    # 注意：DateTimeInput with type="datetime-local" expects format: Y-m-dTH:i
    form_data = {
        'title': '前端测试预约',
        'booking_type': 'meeting',
        'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),  # datetime-local格式
        'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 15,
        'contact_name': '测试联系人',
        'contact_phone': '13900139000',
        'remark': '前端表单测试',
    }
    
    print(f"   表单数据:")
    for key, value in form_data.items():
        print(f"   - {key}: {value}")
    
    response = client.post(url, data=form_data)
    print(f"\n   响应状态码: {response.status_code}")
    print(f"   响应URL: {response.url if hasattr(response, 'url') else 'N/A'}")
    
    # 检查重定向
    if response.status_code == 302:
        print(f"✅ 表单提交成功，重定向到: {response.url}")
        
        # 跟随重定向
        final_response = client.get(response.url)
        print(f"   最终页面状态码: {final_response.status_code}")
        
        # 检查消息
        if hasattr(final_response, 'context') and final_response.context:
            messages = list(final_response.context.get('messages', []))
            if messages:
                print("\n   系统消息:")
                for msg in messages:
                    print(f"   - [{msg.level_tag}] {msg.message}")
        
        # 验证预约是否创建
        booking = Booking.objects.filter(
            user=student,
            title='前端测试预约'
        ).order_by('-created_at').first()
        
        if booking:
            print(f"\n✅ 预约创建成功!")
            print(f"   预约编号: {booking.booking_no}")
            print(f"   预约状态: {booking.get_status_display()}")
            return True
        else:
            print("\n❌ 预约未创建")
            return False
            
    elif response.status_code == 200:
        print("⚠️  表单验证失败，返回原页面")
        
        content = response.content.decode('utf-8')
        
        # 打印响应内容的关键部分
        print(f"\n   响应内容长度: {len(content)}")
        
        # 检查是否包含错误信息
        if 'is-invalid' in content:
            print("   ✅ 存在字段验证错误")
        
        if '预约冲突' in content:
            print("   ✅ 存在预约冲突")
        
        if 'invalid-feedback' in content:
            print("   ✅ 存在invalid-feedback")
        
        # 查找表单部分
        form_start = content.find('<form')
        form_end = content.find('</form>') + 7
        if form_start > 0 and form_end > form_start:
            form_html = content[form_start:form_end]
            print(f"\n   表单HTML长度: {len(form_html)}")
            
            # 查找错误信息
            import re
            errors = re.findall(r'class="[^"]*is-invalid[^"]*"', form_html)
            if errors:
                print(f"   找到{len(errors)}个验证错误字段")
        
        # 检查是否有非字段错误
        if 'alert-danger' in content:
            print("   ✅ 存在alert-danger错误")
            # 提取错误消息
            import re
            alert_matches = re.findall(r'<div class="alert alert-danger[^>]*>(.*?)</div>', content, re.DOTALL)
            if alert_matches:
                print(f"\n   错误消息:")
                for match in alert_matches[:2]:
                    # 清理HTML标签
                    clean_text = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_text:
                        print(f"   - {clean_text[:200]}")
        
        # 打印表单HTML的一部分
        if form_start > 0 and form_end > form_start:
            print(f"\n   表单HTML片段（前500字符）:")
            print("   " + form_html[:500])
        
        return False
    else:
        print(f"❌ 未预期的状态码: {response.status_code}")
        return False

def test_ajax_availability():
    """测试AJAX可用性检查"""
    print("\n" + "=" * 60)
    print("测试AJAX可用性检查")
    print("=" * 60)
    
    client = Client()
    student = User.objects.filter(username='student').first()
    client.login(username='student', password='student123')
    
    venue = Room.objects.filter(status='available').first()
    
    now = timezone.now()
    start_time = (now + timedelta(days=1)).replace(hour=13, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
    
    url = reverse('bookings:check_availability')
    
    import json
    data = {
        'venue_id': venue.id,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'participant_count': 20,
        'required_equipments': []
    }
    
    print(f"\n1. 发送AJAX请求...")
    response = client.post(
        url,
        data=json.dumps(data),
        content_type='application/json'
    )
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = json.loads(response.content)
        print(f"✅ 可用性检查成功")
        print(f"   结果: {result}")
        return True
    else:
        print(f"❌ 可用性检查失败")
        return False

if __name__ == '__main__':
    try:
        success1 = test_form_submission()
        success2 = test_ajax_availability()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("✅ 前端表单提交测试通过")
        else:
            print("⚠️  部分测试失败")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()