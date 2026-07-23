"""
冲突检测测试
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.venues.models import Building, Room, Equipment, RoomEquipment
from apps.schedules.models import Schedule
from apps.maintenance.models import Maintenance
from apps.bookings.models import Booking
from apps.bookings.services.conflict_checker import ConflictChecker


class ConflictCheckerTestCase(TestCase):
    """冲突检测测试基类"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建用户
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
        
        # 创建楼宇和场地
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
        
        # 创建设备
        self.projector = Equipment.objects.create(name='投影仪')
        self.computer = Equipment.objects.create(name='电脑')
        
        RoomEquipment.objects.create(
            room=self.venue,
            equipment=self.projector,
            quantity=1,
            status='normal'
        )
        
        # 设置时间
        self.now = timezone.now()
        self.start_time = self.now + timedelta(days=1, hours=8)
        self.end_time = self.now + timedelta(days=1, hours=10)


class TimeValidityTest(ConflictCheckerTestCase):
    """时间有效性检测测试"""
    
    def test_start_before_end(self):
        """测试开始时间早于结束时间"""
        # 正常情况
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_all()
        
        time_conflicts = [c for c in result['conflicts'] if c['type'] == 'time_validity']
        self.assertEqual(len(time_conflicts), 0)
    
    def test_start_after_end(self):
        """测试开始时间晚于结束时间（应该报错）"""
        checker = ConflictChecker(
            self.venue,
            self.end_time,  # 开始时间晚于结束时间
            self.start_time
        )
        result = checker.check_all()
        
        time_conflicts = [c for c in result['conflicts'] if c['type'] == 'time_validity']
        self.assertEqual(len(time_conflicts), 1)
        self.assertIn('开始时间必须早于结束时间', time_conflicts[0]['message'])
    
    def test_start_in_past(self):
        """测试开始时间在过去（应该报错）"""
        past_start = self.now - timedelta(hours=1)
        past_end = self.now + timedelta(hours=1)
        
        checker = ConflictChecker(
            self.venue,
            past_start,
            past_end
        )
        result = checker.check_all()
        
        time_conflicts = [c for c in result['conflicts'] if c['type'] == 'time_validity']
        self.assertEqual(len(time_conflicts), 1)
        self.assertIn('开始时间必须在未来', time_conflicts[0]['message'])
    
    def test_duration_too_short(self):
        """测试预约时长过短（应该报错）"""
        start = self.now + timedelta(days=1)
        end = start + timedelta(minutes=20)  # 只有20分钟
        
        checker = ConflictChecker(self.venue, start, end)
        result = checker.check_all()
        
        time_conflicts = [c for c in result['conflicts'] if c['type'] == 'time_validity']
        self.assertTrue(len(time_conflicts) > 0)
        self.assertIn('不能少于', time_conflicts[0]['message'])
    
    def test_duration_too_long(self):
        """测试预约时长过长（应该报错）"""
        start = self.now + timedelta(days=1)
        end = start + timedelta(hours=10)  # 10小时
        
        checker = ConflictChecker(self.venue, start, end)
        result = checker.check_all()
        
        time_conflicts = [c for c in result['conflicts'] if c['type'] == 'time_validity']
        self.assertTrue(len(time_conflicts) > 0)
        self.assertIn('不能超过', time_conflicts[0]['message'])


class CapacityTest(ConflictCheckerTestCase):
    """容量检测测试"""
    
    def test_capacity_ok(self):
        """测试人数在容量范围内"""
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        checker.check_capacity(50)  # 场地容量60，预约50人
        
        capacity_conflicts = [c for c in checker.conflicts if c['type'] == 'capacity']
        self.assertEqual(len(capacity_conflicts), 0)
    
    def test_capacity_exceeded(self):
        """测试人数超过容量（应该报错）"""
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        checker.check_capacity(70)  # 场地容量60，预约70人
        
        capacity_conflicts = [c for c in checker.conflicts if c['type'] == 'capacity']
        self.assertEqual(len(capacity_conflicts), 1)
        self.assertIn('超过场地容量', capacity_conflicts[0]['message'])


class EquipmentTest(ConflictCheckerTestCase):
    """设备检测测试"""
    
    def test_equipment_available(self):
        """测试设备可用"""
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_equipment([self.projector.id])
        
        self.assertFalse(result['has_missing'])
        self.assertIsNone(result['warning'])
    
    def test_equipment_missing(self):
        """测试设备缺失（应该提示）"""
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_equipment([self.computer.id])  # 场地没有电脑
        
        self.assertTrue(result['has_missing'])
        self.assertIn('电脑', result['warning'])
        self.assertIn('请自备', result['warning'])


class MaintenanceConflictTest(ConflictCheckerTestCase):
    """维修停用冲突检测测试"""
    
    def test_maintenance_conflict(self):
        """测试维修冲突（应该报错）"""
        # 创建维修记录
        maintenance = Maintenance.objects.create(
            venue=self.venue,
            reason='空调维修',
            start_time=self.start_time - timedelta(hours=1),
            end_time=self.end_time + timedelta(hours=1),
            status='ongoing'
        )
        
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_all()
        
        maintenance_conflicts = [c for c in result['conflicts'] if c['type'] == 'maintenance']
        self.assertEqual(len(maintenance_conflicts), 1)
        self.assertIn('维修停用', maintenance_conflicts[0]['message'])
    
    def test_no_maintenance_conflict(self):
        """测试无维修冲突"""
        # 创建不重叠的维修记录
        maintenance = Maintenance.objects.create(
            venue=self.venue,
            reason='空调维修',
            start_time=self.end_time + timedelta(hours=1),
            end_time=self.end_time + timedelta(hours=3),
            status='ongoing'
        )
        
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_all()
        
        maintenance_conflicts = [c for c in result['conflicts'] if c['type'] == 'maintenance']
        self.assertEqual(len(maintenance_conflicts), 0)


class BookingConflictTest(ConflictCheckerTestCase):
    """已批准预约冲突检测测试"""
    
    def test_booking_conflict(self):
        """测试预约冲突（应该报错）"""
        # 创建已批准的预约
        existing_booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.teacher,
            title='测试预约',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            status='approved'
        )
        
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_all()
        
        booking_conflicts = [c for c in result['conflicts'] if c['type'] == 'booking']
        self.assertEqual(len(booking_conflicts), 1)
        self.assertIn('已被预约', booking_conflicts[0]['message'])
    
    def test_no_booking_conflict(self):
        """测试无预约冲突"""
        # 创建不重叠的预约
        existing_booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.teacher,
            title='测试预约',
            booking_type='meeting',
            start_time=self.end_time + timedelta(hours=1),
            end_time=self.end_time + timedelta(hours=3),
            participant_count=30,
            status='approved'
        )
        
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_all()
        
        booking_conflicts = [c for c in result['conflicts'] if c['type'] == 'booking']
        self.assertEqual(len(booking_conflicts), 0)


class UserTimeConflictTest(ConflictCheckerTestCase):
    """用户时间冲突检测测试"""
    
    def test_user_time_conflict(self):
        """测试用户时间冲突（应该报错）"""
        # 创建用户的其他预约
        user_booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.student,
            title='我的预约',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            status='approved'
        )
        
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time,
            user=self.student
        )
        result = checker.check_all()
        
        user_conflicts = [c for c in result['conflicts'] if c['type'] == 'user_conflict']
        self.assertEqual(len(user_conflicts), 1)
        self.assertIn('已有预约', user_conflicts[0]['message'])


class TimeIntervalTest(ConflictCheckerTestCase):
    """时间间隔检测测试"""
    
    def test_interval_conflict(self):
        """测试时间间隔不足（应该报错）"""
        # 创建前一个预约
        prev_booking = Booking.objects.create(
            booking_no='BK20260717000001',
            venue=self.venue,
            user=self.teacher,
            title='前一个预约',
            booking_type='meeting',
            start_time=self.start_time - timedelta(hours=2),
            end_time=self.start_time - timedelta(minutes=5),  # 结束后只间隔5分钟
            participant_count=30,
            status='approved'
        )
        
        checker = ConflictChecker(
            self.venue,
            self.start_time,
            self.end_time
        )
        result = checker.check_all()
        
        interval_conflicts = [c for c in result['conflicts'] if c['type'] == 'interval']
        self.assertEqual(len(interval_conflicts), 1)
        self.assertIn('间隔不足', interval_conflicts[0]['message'])