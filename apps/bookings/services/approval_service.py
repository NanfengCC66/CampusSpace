from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from apps.bookings.models import Booking, Approval
from apps.bookings.services.conflict_checker import ConflictChecker


class ApprovalService:
    @classmethod
    @transaction.atomic
    def approve_booking(cls, booking, approver, comment=''):
        if booking.status != Booking.Status.PENDING:
            raise ValidationError('只能审批待审批状态的预约')
        
        checker = ConflictChecker(
            venue=booking.venue,
            start_time=booking.start_time,
            end_time=booking.end_time,
            exclude_booking_id=booking.id
        )
        result = checker.check_all()
        
        blocking_conflicts = [c for c in result.get('conflicts', []) if c.get('level') == 'error']
        if blocking_conflicts:
            raise ValidationError('时间冲突，无法通过审批')
        
        booking.status = Booking.Status.APPROVED
        booking.save()
        
        approval = Approval.objects.create(
            booking=booking,
            approver=approver,
            action=Approval.Action.APPROVE,
            comment=comment
        )
        
        return {
            'success': True,
            'booking': booking,
            'approval': approval
        }
    
    @classmethod
    @transaction.atomic
    def reject_booking(cls, booking, approver, reason):
        if booking.status != Booking.Status.PENDING:
            raise ValidationError('只能拒绝待审批状态的预约')
        
        if not reason or not reason.strip():
            raise ValidationError('拒绝原因不能为空')
        
        booking.status = Booking.Status.REJECTED
        booking.save()
        
        approval = Approval.objects.create(
            booking=booking,
            approver=approver,
            action=Approval.Action.REJECT,
            comment=reason
        )
        
        return {
            'success': True,
            'booking': booking,
            'approval': approval
        }
    
    @classmethod
    @transaction.atomic
    def cancel_booking_by_user(cls, booking, user, reason=''):
        if booking.user != user:
            raise PermissionDenied('只能取消自己的预约')
        
        if booking.status not in [Booking.Status.PENDING, Booking.Status.APPROVED]:
            raise ValidationError('当前状态不可取消')
        
        if booking.start_time <= timezone.now():
            raise ValidationError('已开始的预约不可取消')
        
        cancel_deadline = booking.start_time - timezone.timedelta(hours=2)
        if timezone.now() > cancel_deadline:
            raise ValidationError('预约开始前2小时内不能取消')
        
        booking.status = Booking.Status.CANCELLED
        booking.cancel_reason = reason
        booking.cancelled_by = user
        booking.cancelled_at = timezone.now()
        booking.save()
        
        return {
            'success': True,
            'booking': booking
        }
    
    @classmethod
    @transaction.atomic
    def cancel_booking_by_admin(cls, booking, admin, reason):
        if not admin.is_admin:
            raise PermissionDenied('需要管理员权限')
        
        if not reason or not reason.strip():
            raise ValidationError('取消原因不能为空')
        
        booking.status = Booking.Status.CANCELLED
        booking.cancel_reason = reason
        booking.cancelled_by = admin
        booking.cancelled_at = timezone.now()
        booking.save()
        
        return {
            'success': True,
            'booking': booking
        }
    
    @classmethod
    def get_pending_bookings(cls, venue_id=None, user_id=None):
        queryset = Booking.objects.filter(status=Booking.Status.PENDING)
        
        if venue_id:
            queryset = queryset.filter(venue_id=venue_id)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.select_related('venue', 'venue__building', 'user').order_by('start_time')
    
    @classmethod
    def get_user_bookings(cls, user, status=None):
        queryset = Booking.objects.filter(user=user)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('venue', 'venue__building').order_by('-created_at')
    
    @classmethod
    @transaction.atomic
    def batch_approve(cls, booking_ids, approver, comment=''):
        """批量审批通过"""
        results = {
            'success': [],
            'failed': []
        }
        
        bookings = Booking.objects.filter(
            id__in=booking_ids,
            status=Booking.Status.PENDING
        )
        
        for booking in bookings:
            try:
                checker = ConflictChecker(
                    venue=booking.venue,
                    start_time=booking.start_time,
                    end_time=booking.end_time,
                    exclude_booking_id=booking.id
                )
                result = checker.check_all()
                
                blocking_conflicts = [c for c in result.get('conflicts', []) if c.get('level') == 'error']
                if blocking_conflicts:
                    results['failed'].append({
                        'booking_id': booking.id,
                        'booking_no': booking.booking_no,
                        'reason': '时间冲突'
                    })
                    continue
                
                booking.status = Booking.Status.APPROVED
                booking.save()
                
                Approval.objects.create(
                    booking=booking,
                    approver=approver,
                    action=Approval.Action.APPROVE,
                    comment=comment
                )
                
                results['success'].append({
                    'booking_id': booking.id,
                    'booking_no': booking.booking_no
                })
                
            except Exception as e:
                results['failed'].append({
                    'booking_id': booking.id,
                    'booking_no': booking.booking_no,
                    'reason': str(e)
                })
        
        return results
    
    @classmethod
    @transaction.atomic
    def batch_reject(cls, booking_ids, approver, reason):
        """批量审批拒绝"""
        if not reason or not reason.strip():
            raise ValidationError('拒绝原因不能为空')
        
        results = {
            'success': [],
            'failed': []
        }
        
        bookings = Booking.objects.filter(
            id__in=booking_ids,
            status=Booking.Status.PENDING
        )
        
        for booking in bookings:
            try:
                booking.status = Booking.Status.REJECTED
                booking.save()
                
                Approval.objects.create(
                    booking=booking,
                    approver=approver,
                    action=Approval.Action.REJECT,
                    comment=reason
                )
                
                results['success'].append({
                    'booking_id': booking.id,
                    'booking_no': booking.booking_no
                })
                
            except Exception as e:
                results['failed'].append({
                    'booking_id': booking.id,
                    'booking_no': booking.booking_no,
                    'reason': str(e)
                })
        
        return results