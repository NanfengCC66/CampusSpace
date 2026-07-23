"""
预约服务测试
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.venues.models import Building, Room
from apps.bookings.models import Booking
from apps.bookings.services import BookingService


class BookingServiceTestCase(TestCase):
    """预约服务测试基类"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            role='student'
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
        
        self.now = timezone.now()
        self.start_time = self.now + timedelta(days=1, hours=8)
        self.end_time = self.now + timedelta(days=1, hours=10)


class GenerateBookingNoTest(BookingServiceTestCase):
    """预约编号生成测试"""
    
    def test_generate_first_booking_no(self):
        """测试生成第一个预约编号"""
        booking_no = BookingService.generate_booking_no()
        
        # 格式：BK + YYYYMMDD + 6位序号
        self.assertTrue(booking_no.startswith('BK'))
        self.assertEqual(len(booking_no), 16)  # BK(2) + YYYYMMDD(8) + 序号(6)
    
    def test_generate_sequential_booking_no(self):
        """测试生成连续的预约编号"""
        # 创建第一个预约
        booking1 = Booking.objects.create(
            booking_no=BookingService.generate_booking_no(),
            venue=self.venue,
            user=self.user,
            title='测试预约1',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            status='pending'
        )
        
        # 生成第二个编号
        booking_no2 = BookingService.generate_booking_no()
        
        # 序号应该递增
        seq1 = int(booking1.booking_no[-6:])
        seq2 = int(booking_no2[-6:])
        self.assertEqual(seq2, seq1 + 1)


class CreateBookingTest(BookingServiceTestCase):
    """创建预约测试"""
    
    def test_create_booking_success(self):
        """测试成功创建预约"""
        result = BookingService.create_booking(
            user=self.user,
            venue=self.venue,
            title='测试会议',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['booking'])
        self.assertEqual(len(result['conflicts']), 0)
        
        # 验证预约属性
        booking = result['booking']
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.venue, self.venue)
        self.assertEqual(booking.title, '测试会议')
        self.assertEqual(booking.status, Booking.Status.PENDING)
    
    def test_create_booking_with_capacity_conflict(self):
        """测试容量冲突时创建预约失败"""
        result = BookingService.create_booking(
            user=self.user,
            venue=self.venue,
            title='测试会议',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=70  # 超过容量
        )
        
        self.assertFalse(result['success'])
        self.assertIsNone(result['booking'])
        self.assertTrue(len(result['conflicts']) > 0)
        
        # 验证冲突类型
        capacity_conflicts = [c for c in result['conflicts'] if c['type'] == 'capacity']
        self.assertEqual(len(capacity_conflicts), 1)
    
    def test_create_booking_with_time_conflict(self):
        """测试时间冲突时创建预约失败"""
        # 创建一个已批准的预约
        existing_booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.user,
            title='已存在预约',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            status='approved'
        )
        
        # 尝试创建冲突的预约
        result = BookingService.create_booking(
            user=self.user,
            venue=self.venue,
            title='新预约',
            booking_type='meeting',
            start_time=self.start_time + timedelta(minutes=30),
            end_time=self.end_time - timedelta(minutes=30),
            participant_count=20
        )
        
        self.assertFalse(result['success'])
        self.assertIsNone(result['booking'])
        
        # 验证冲突类型
        booking_conflicts = [c for c in result['conflicts'] if c['type'] == 'booking']
        self.assertEqual(len(booking_conflicts), 1)


class CheckAvailabilityTest(BookingServiceTestCase):
    """检查可用性测试"""
    
    def test_check_availability_available(self):
        """测试场地可用"""
        result = BookingService.check_booking_availability(
            venue=self.venue,
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30
        )
        
        self.assertTrue(result['available'])
        self.assertEqual(len(result['conflicts']), 0)
    
    def test_check_availability_unavailable(self):
        """测试场地不可用"""
        # 创建冲突的预约
        existing_booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.user,
            title='已存在预约',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            status='approved'
        )
        
        result = BookingService.check_booking_availability(
            venue=self.venue,
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=20
        )
        
        self.assertFalse(result['available'])
        self.assertTrue(len(result['conflicts']) > 0)