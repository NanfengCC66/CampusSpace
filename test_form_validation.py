#!/usr/bin/env python
"""直接测试表单验证"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.bookings.forms import BookingCreateForm
from django.utils import timezone
from datetime import timedelta

def test_form():
    print("=" * 60)
    print("测试BookingCreateForm验证")
    print("=" * 60)
    
    now = timezone.now()
    start_time = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    
    # 测试1: 使用datetime-local格式字符串
    print("\n1. 测试datetime-local格式字符串...")
    data1 = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
        'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
        'participant_count': 15,
    }
    
    form1 = BookingCreateForm(data=data1)
    print(f"   表单验证结果: {form1.is_valid()}")
    if not form1.is_valid():
        print(f"   错误: {form1.errors}")
    else:
        print(f"   清洗后数据: {form1.cleaned_data}")
    
    # 测试2: 使用datetime对象
    print("\n2. 测试datetime对象...")
    data2 = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': start_time,
        'end_time': end_time,
        'participant_count': 15,
    }
    
    form2 = BookingCreateForm(data=data2)
    print(f"   表单验证结果: {form2.is_valid()}")
    if not form2.is_valid():
        print(f"   错误: {form2.errors}")
    else:
        print(f"   清洗后数据: {form2.cleaned_data}")
    
    # 测试3: 使用标准格式字符串
    print("\n3. 测试标准格式字符串...")
    data3 = {
        'title': '测试预约',
        'booking_type': 'meeting',
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'participant_count': 15,
    }
    
    form3 = BookingCreateForm(data=data3)
    print(f"   表单验证结果: {form3.is_valid()}")
    if not form3.is_valid():
        print(f"   错误: {form3.errors}")
    else:
        print(f"   清洗后数据: {form3.cleaned_data}")

if __name__ == '__main__':
    test_form()