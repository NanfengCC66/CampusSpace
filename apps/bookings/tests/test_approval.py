from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import PermissionDenied, ValidationError
from apps.venues.models import Building, Room
from apps.users.models import User
from apps.bookings.models import Booking, Approval
from apps.bookings.services import ApprovalService


class ApprovalServiceTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin',
            is_staff=True
        )
        
        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='teacher123',
            role='teacher'
        )
        
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='student123',
            role='student'
        )
        
        self.building = Building.objects.create(
            name='教学楼A',
            location='校区东侧',
            total_floors=5,
            description='主教学楼'
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
        self.start_time = self.now + timedelta(days=1, hours=9)
        self.end_time = self.now + timedelta(days=1, hours=11)
        
        self.booking = Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.student,
            title='测试预约',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            status=Booking.Status.PENDING
        )
    
    def test_approve_booking_success(self):
        result = ApprovalService.approve_booking(
            booking=self.booking,
            approver=self.admin,
            comment='同意使用'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['booking'].status, Booking.Status.APPROVED)
        self.assertEqual(result['approval'].action, Approval.Action.APPROVE)
        self.assertEqual(result['approval'].comment, '同意使用')
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.APPROVED)
    
    def test_approve_booking_wrong_status(self):
        self.booking.status = Booking.Status.APPROVED
        self.booking.save()
        
        with self.assertRaises(ValidationError) as context:
            ApprovalService.approve_booking(
                booking=self.booking,
                approver=self.admin,
                comment=''
            )
        
        self.assertIn('只能审批待审批状态', str(context.exception))
    
    def test_reject_booking_success(self):
        result = ApprovalService.reject_booking(
            booking=self.booking,
            approver=self.admin,
            reason='时间冲突'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['booking'].status, Booking.Status.REJECTED)
        self.assertEqual(result['approval'].action, Approval.Action.REJECT)
        self.assertEqual(result['approval'].comment, '时间冲突')
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.REJECTED)
    
    def test_reject_booking_without_reason(self):
        with self.assertRaises(ValidationError) as context:
            ApprovalService.reject_booking(
                booking=self.booking,
                approver=self.admin,
                reason=''
            )
        
        self.assertIn('拒绝原因不能为空', str(context.exception))
    
    def test_cancel_booking_by_user_success(self):
        self.booking.status = Booking.Status.APPROVED
        self.booking.save()
        
        result = ApprovalService.cancel_booking_by_user(
            booking=self.booking,
            user=self.student,
            reason='临时有事'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['booking'].status, Booking.Status.CANCELLED)
        self.assertEqual(result['booking'].cancel_reason, '临时有事')
        self.assertEqual(result['booking'].cancelled_by, self.student)
        self.assertIsNotNone(result['booking'].cancelled_at)
    
    def test_cancel_booking_by_other_user(self):
        with self.assertRaises(PermissionDenied):
            ApprovalService.cancel_booking_by_user(
                booking=self.booking,
                user=self.teacher,
                reason=''
            )
    
    def test_cancel_booking_wrong_status(self):
        self.booking.status = Booking.Status.COMPLETED
        self.booking.save()
        
        with self.assertRaises(ValidationError) as context:
            ApprovalService.cancel_booking_by_user(
                booking=self.booking,
                user=self.student,
                reason=''
            )
        
        self.assertIn('当前状态不可取消', str(context.exception))
    
    def test_cancel_booking_too_late(self):
        self.booking.status = Booking.Status.APPROVED
        self.booking.start_time = self.now + timedelta(hours=1)
        self.booking.save()
        
        with self.assertRaises(ValidationError) as context:
            ApprovalService.cancel_booking_by_user(
                booking=self.booking,
                user=self.student,
                reason=''
            )
        
        self.assertIn('预约开始前2小时内不能取消', str(context.exception))
    
    def test_cancel_booking_by_admin_success(self):
        self.booking.status = Booking.Status.APPROVED
        self.booking.save()
        
        result = ApprovalService.cancel_booking_by_admin(
            booking=self.booking,
            admin=self.admin,
            reason='场地维修'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['booking'].status, Booking.Status.CANCELLED)
        self.assertEqual(result['booking'].cancel_reason, '场地维修')
        self.assertEqual(result['booking'].cancelled_by, self.admin)
    
    def test_cancel_booking_by_non_admin(self):
        with self.assertRaises(PermissionDenied):
            ApprovalService.cancel_booking_by_admin(
                booking=self.booking,
                admin=self.teacher,
                reason='测试'
            )
    
    def test_get_pending_bookings(self):
        booking2 = Booking.objects.create(
            booking_no='BK20260117000002',
            venue=self.room,
            user=self.teacher,
            title='测试预约2',
            booking_type='teaching',
            start_time=self.start_time + timedelta(days=1),
            end_time=self.end_time + timedelta(days=1),
            participant_count=40,
            status=Booking.Status.PENDING
        )
        
        approved_booking = Booking.objects.create(
            booking_no='BK20260117000003',
            venue=self.room,
            user=self.student,
            title='已通过预约',
            booking_type='meeting',
            start_time=self.start_time + timedelta(days=2),
            end_time=self.end_time + timedelta(days=2),
            participant_count=20,
            status=Booking.Status.APPROVED
        )
        
        pending_bookings = ApprovalService.get_pending_bookings()
        
        self.assertEqual(pending_bookings.count(), 2)
        self.assertIn(self.booking, pending_bookings)
        self.assertIn(booking2, pending_bookings)
        self.assertNotIn(approved_booking, pending_bookings)
    
    def test_get_user_bookings(self):
        booking2 = Booking.objects.create(
            booking_no='BK20260117000002',
            venue=self.room,
            user=self.student,
            title='测试预约2',
            booking_type='meeting',
            start_time=self.start_time + timedelta(days=1),
            end_time=self.end_time + timedelta(days=1),
            participant_count=20,
            status=Booking.Status.APPROVED
        )
        
        teacher_booking = Booking.objects.create(
            booking_no='BK20260117000003',
            venue=self.room,
            user=self.teacher,
            title='教师预约',
            booking_type='teaching',
            start_time=self.start_time + timedelta(days=2),
            end_time=self.end_time + timedelta(days=2),
            participant_count=40,
            status=Booking.Status.PENDING
        )
        
        user_bookings = ApprovalService.get_user_bookings(self.student)
        
        self.assertEqual(user_bookings.count(), 2)
        self.assertIn(self.booking, user_bookings)
        self.assertIn(booking2, user_bookings)
        self.assertNotIn(teacher_booking, user_bookings)
    
    def test_get_user_bookings_with_status_filter(self):
        approved_booking = Booking.objects.create(
            booking_no='BK20260117000002',
            venue=self.room,
            user=self.student,
            title='已通过预约',
            booking_type='meeting',
            start_time=self.start_time + timedelta(days=1),
            end_time=self.end_time + timedelta(days=1),
            participant_count=20,
            status=Booking.Status.APPROVED
        )
        
        pending_bookings = ApprovalService.get_user_bookings(
            self.student, 
            status=Booking.Status.PENDING
        )
        
        self.assertEqual(pending_bookings.count(), 1)
        self.assertIn(self.booking, pending_bookings)
        self.assertNotIn(approved_booking, pending_bookings)


class BookingStatusColorTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            role='student'
        )
        
        self.building = Building.objects.create(
            name='教学楼B',
            location='校区西侧',
            total_floors=5,
            description='副教学楼'
        )
        
        self.room = Room.objects.create(
            name='教室B101',
            room_number='B101',
            building=self.building,
            capacity=50,
            venue_type='classroom',
            status='available'
        )
        
        self.now = timezone.now()
        self.start_time = self.now + timedelta(days=1, hours=9)
        self.end_time = self.now + timedelta(days=1, hours=11)
    
    def test_status_colors(self):
        booking = Booking.objects.create(
            booking_no='BK20260117000001',
            venue=self.room,
            user=self.user,
            title='测试',
            booking_type='meeting',
            start_time=self.start_time,
            end_time=self.end_time,
            participant_count=30,
            status=Booking.Status.PENDING
        )
        
        self.assertEqual(booking.get_status_color(), '#ffc107')
        self.assertEqual(booking.get_status_badge_class(), 'warning')
        
        booking.status = Booking.Status.APPROVED
        self.assertEqual(booking.get_status_color(), '#28a745')
        self.assertEqual(booking.get_status_badge_class(), 'success')
        
        booking.status = Booking.Status.REJECTED
        self.assertEqual(booking.get_status_color(), '#dc3545')
        self.assertEqual(booking.get_status_badge_class(), 'danger')
        
        booking.status = Booking.Status.CANCELLED
        self.assertEqual(booking.get_status_color(), '#6c757d')
        self.assertEqual(booking.get_status_badge_class(), 'secondary')
        
        booking.status = Booking.Status.COMPLETED
        self.assertEqual(booking.get_status_color(), '#17a2b8')
        self.assertEqual(booking.get_status_badge_class(), 'info')
        
        booking.status = Booking.Status.EXPIRED
        self.assertEqual(booking.get_status_color(), '#856404')
        self.assertEqual(booking.get_status_badge_class(), 'dark')