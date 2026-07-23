"""
模型测试
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.venues.models import Building, Room
from apps.bookings.models import Booking


class BookingModelTest(TestCase):
    """预约模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.student = User.objects.create_user(
            username='student1',
            password='test123',
            role='student'
        )
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='test123',
            role='teacher'
        )
        
        self.building = Building.objects.create(
            name='测试楼宇',
            total_floors=5
        )
        self.venue = Room.objects.create(
            name='测试教室',
            building=self.building,
            floor=1,
            room_number='101',
            capacity=60
        )
    
    def test_booking_duration(self):
        """测试预约时长计算"""
        now = timezone.now()
        booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.student,
            title='测试预约',
            booking_type='meeting',
            start_time=now,
            end_time=now + timedelta(hours=2),
            participant_count=30
        )
        
        # 时长应为120分钟
        self.assertEqual(booking.duration, 120)
        self.assertEqual(booking.duration_display, '2小时')
    
    def test_booking_priority_student(self):
        """测试学生预约优先级"""
        booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.student,
            title='学生预约',
            booking_type='meeting',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            participant_count=30
        )
        
        self.assertEqual(booking.priority, 0)
    
    def test_booking_priority_teacher(self):
        """测试教师预约优先级"""
        booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.teacher,
            title='教师预约',
            booking_type='teaching',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            participant_count=30
        )
        
        self.assertEqual(booking.priority, 1)
    
    def test_booking_str(self):
        """测试预约字符串表示"""
        booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.student,
            title='测试预约',
            booking_type='meeting',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            participant_count=30
        )
        
        self.assertEqual(str(booking), 'BK20260717000001 - 测试教室')