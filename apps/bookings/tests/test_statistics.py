from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, datetime
from apps.venues.models import Building, Room
from apps.users.models import User
from apps.bookings.models import Booking
from apps.schedules.models import Schedule
from apps.bookings.services import StatisticsService


class StatisticsServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            role='student'
        )
        
        self.building = Building.objects.create(
            name='教学楼A',
            location='校区东侧',
            total_floors=5
        )
        
        self.room = Room.objects.create(
            name='教室A101',
            room_number='A101',
            building=self.building,
            capacity=50,
            venue_type='classroom',
            status='available'
        )
        
        self.now = timezone.now()
        self.start_date = (self.now - timedelta(days=7)).date()
        self.end_date = self.now.date()
    
    def test_no_data_no_error(self):
        """测试没有数据时不报错"""
        result = StatisticsService.get_venue_utilization(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['average'], 0)
        self.assertEqual(result['total_hours'], 0)
        self.assertEqual(len(result['venues']), 1)
        self.assertEqual(result['venues'][0]['used_hours'], 0)
        self.assertEqual(result['venues'][0]['utilization_rate'], 0)
        
        trend = StatisticsService.get_booking_trend(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(trend)
        self.assertEqual(trend['total'], 0)
        self.assertEqual(trend['approved'], 0)
        self.assertEqual(trend['rejected'], 0)
        self.assertEqual(len(trend['trend']), 0)
        
        status_dist = StatisticsService.get_status_distribution(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(status_dist)
        self.assertEqual(len(status_dist), 0)
    
    def test_single_data_chart_normal(self):
        """测试只有一条数据时图表正常"""
        start_time = self.now - timedelta(days=3, hours=-9)
        end_time = self.now - timedelta(days=3, hours=-11)
        
        booking = Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='测试预约',
            booking_type='meeting',
            start_time=start_time,
            end_time=end_time,
            participant_count=30,
            status='approved'
        )
        
        result = StatisticsService.get_venue_utilization(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result['venues']), 1)
        self.assertGreater(result['venues'][0]['used_hours'], 0)
        self.assertGreater(result['venues'][0]['utilization_rate'], 0)
        self.assertEqual(result['venues'][0]['booking_count'], 1)
        
        trend = StatisticsService.get_booking_trend(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(trend)
        self.assertEqual(trend['total'], 1)
        self.assertEqual(trend['approved'], 1)
        self.assertGreater(len(trend['trend']), 0)
        
        popular = StatisticsService.get_popular_venues(
            limit=10,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertEqual(len(popular), 1)
        self.assertEqual(popular[0]['venue_name'], '教室A101')
        self.assertEqual(popular[0]['booking_count'], 1)
    
    def test_cancelled_booking_not_counted(self):
        """测试已取消预约不计入有效利用率"""
        start_time = self.now - timedelta(days=3, hours=-9)
        end_time = self.now - timedelta(days=3, hours=-11)
        
        approved_booking = Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='有效预约',
            booking_type='meeting',
            start_time=start_time,
            end_time=end_time,
            participant_count=30,
            status='approved'
        )
        
        cancelled_booking = Booking.objects.create(
            booking_no='BK20260117000002',
            venue=self.room,
            user=self.user,
            title='已取消预约',
            booking_type='meeting',
            start_time=start_time + timedelta(days=1),
            end_time=end_time + timedelta(days=1),
            participant_count=30,
            status='cancelled'
        )
        
        result = StatisticsService.get_venue_utilization(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertEqual(result['venues'][0]['booking_count'], 1)
        
        popular = StatisticsService.get_popular_venues(
            limit=10,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertEqual(len(popular), 1)
        self.assertEqual(popular[0]['booking_count'], 1)
        
        status_dist = StatisticsService.get_status_distribution(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertEqual(status_dist.get('approved', 0), 1)
        self.assertEqual(status_dist.get('cancelled', 0), 1)
    
    def test_schedule_and_booking_separate_statistics(self):
        """测试固定课表和临时预约分别统计"""
        start_time = self.now - timedelta(days=3, hours=-9)
        end_time = self.now - timedelta(days=3, hours=-11)
        
        booking = Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='临时预约',
            booking_type='meeting',
            start_time=start_time,
            end_time=end_time,
            participant_count=30,
            status='approved'
        )
        
        schedule = Schedule.objects.create(
            venue=self.room,
            course_name='高等数学',
            teacher='张老师',
            day_of_week=1,
            period='1-2',
            start_week=1,
            end_week=16,
            semester='2025-2026-2'
        )
        
        result = StatisticsService.get_booking_type_statistics(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['temp_booking_count'], 1)
        self.assertEqual(result['schedule_count'], 1)
        self.assertEqual(result['total_count'], 2)
        
        self.assertIn('meeting', result['booking_types'])
        self.assertEqual(result['booking_types']['meeting'], 1)
    
    def test_booking_type_distribution(self):
        """测试不同预约类型的统计"""
        start_time = self.now - timedelta(days=3, hours=-9)
        end_time = self.now - timedelta(days=3, hours=-11)
        
        Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='教学预约',
            booking_type='teaching',
            start_time=start_time,
            end_time=end_time,
            participant_count=30,
            status='approved'
        )
        
        Booking.objects.create(
            booking_no='BK20260117000002',
            venue=self.room,
            user=self.user,
            title='会议预约',
            booking_type='meeting',
            start_time=start_time + timedelta(days=1),
            end_time=end_time + timedelta(days=1),
            participant_count=20,
            status='approved'
        )
        
        Booking.objects.create(
            booking_no='BK20260117000003',
            venue=self.room,
            user=self.user,
            title='活动预约',
            booking_type='activity',
            start_time=start_time + timedelta(days=2),
            end_time=end_time + timedelta(days=2),
            participant_count=40,
            status='approved'
        )
        
        result = StatisticsService.get_booking_type_statistics(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertEqual(result['temp_booking_count'], 3)
        self.assertIn('teaching', result['booking_types'])
        self.assertIn('meeting', result['booking_types'])
        self.assertIn('activity', result['booking_types'])
    
    def test_time_distribution(self):
        """测试时间段分布统计"""
        start_time = self.now - timedelta(days=3)
        start_time = start_time.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='上午预约',
            booking_type='meeting',
            start_time=start_time,
            end_time=end_time,
            participant_count=30,
            status='approved'
        )
        
        afternoon_start = start_time.replace(hour=14)
        afternoon_end = afternoon_start + timedelta(hours=2)
        
        Booking.objects.create(
            booking_no='BK20260117000002',
            venue=self.room,
            user=self.user,
            title='下午预约',
            booking_type='meeting',
            start_time=afternoon_start,
            end_time=afternoon_end,
            participant_count=20,
            status='approved'
        )
        
        result = StatisticsService.get_time_distribution(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        self.assertIn('08:00-10:00', result)
        self.assertIn('14:00-16:00', result)
    
    def test_building_statistics(self):
        """测试楼宇统计"""
        start_time = self.now - timedelta(days=3, hours=-9)
        end_time = self.now - timedelta(days=3, hours=-11)
        
        Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='测试预约',
            booking_type='meeting',
            start_time=start_time,
            end_time=end_time,
            participant_count=30,
            status='approved'
        )
        
        result = StatisticsService.get_building_statistics(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['building_name'], '教学楼A')
        self.assertEqual(result[0]['booking_count'], 1)
        self.assertEqual(result[0]['room_count'], 1)
    
    def test_granularity_options(self):
        """测试不同粒度的趋势统计"""
        start_time = self.now - timedelta(days=3, hours=-9)
        end_time = self.now - timedelta(days=3, hours=-11)
        
        Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='测试预约',
            booking_type='meeting',
            start_time=start_time,
            end_time=end_time,
            participant_count=30,
            status='approved'
        )
        
        trend_day = StatisticsService.get_booking_trend(
            start_date=self.start_date,
            end_date=self.end_date,
            granularity='day'
        )
        
        self.assertEqual(trend_day['granularity'], 'day')
        self.assertEqual(trend_day['total'], 1)
        
        trend_week = StatisticsService.get_booking_trend(
            start_date=self.start_date,
            end_date=self.end_date,
            granularity='week'
        )
        
        self.assertEqual(trend_week['granularity'], 'week')
        self.assertEqual(trend_week['total'], 1)
        
        trend_month = StatisticsService.get_booking_trend(
            start_date=self.start_date,
            end_date=self.end_date,
            granularity='month'
        )
        
        self.assertEqual(trend_month['granularity'], 'month')
        self.assertEqual(trend_month['total'], 1)