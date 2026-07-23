"""
预约服务
"""
from django.utils import timezone
from django.db import transaction
from apps.bookings.models import Booking
from .conflict_checker import ConflictChecker


class BookingService:
    """预约服务"""
    
    @staticmethod
    def generate_booking_no():
        """
        生成预约编号
        格式：BK + YYYYMMDD + 6位序号（每天重置）
        
        Returns:
            str: 预约编号
        """
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        
        # 查询今天的最大序号
        prefix = f'BK{date_str}'
        last_booking = Booking.objects.filter(
            booking_no__startswith=prefix
        ).order_by('-booking_no').first()
        
        if last_booking:
            # 提取序号并加1
            last_no = int(last_booking.booking_no[-6:])
            new_no = last_no + 1
        else:
            new_no = 1
        
        # 格式化为6位序号
        return f'{prefix}{new_no:06d}'
    
    @staticmethod
    @transaction.atomic
    def create_booking(user, venue, title, booking_type, start_time, end_time,
                       participant_count, required_equipments=None,
                       contact_name=None, contact_phone=None, remark=None):
        """
        创建预约
        
        Args:
            user: 用户对象
            venue: 场地对象
            title: 使用目的
            booking_type: 预约用途
            start_time: 开始时间
            end_time: 结束时间
            participant_count: 参与人数
            required_equipments: 所需设备ID列表
            contact_name: 联系人
            contact_phone: 联系电话
            remark: 备注
        
        Returns:
            dict: {
                'success': bool,
                'booking': Booking对象或None,
                'conflicts': list,
                'equipment_warning': str或None
            }
        """
        # 1. 执行冲突检测
        checker = ConflictChecker(venue, start_time, end_time, user)
        
        # 检测容量
        checker.check_capacity(participant_count)
        
        # 检测设备
        equipment_result = checker.check_equipment(required_equipments)
        
        # 执行所有其他检测
        conflict_result = checker.check_all()
        
        # 如果有冲突，返回冲突信息
        if conflict_result['has_conflict']:
            return {
                'success': False,
                'booking': None,
                'conflicts': conflict_result['conflicts'],
                'equipment_warning': equipment_result.get('warning')
            }
        
        # 2. 生成预约编号
        booking_no = BookingService.generate_booking_no()
        
        # 3. 创建预约记录
        booking = Booking.objects.create(
            booking_no=booking_no,
            venue=venue,
            user=user,
            title=title,
            booking_type=booking_type,
            start_time=start_time,
            end_time=end_time,
            participant_count=participant_count,
            required_equipments=required_equipments or [],
            contact_name=contact_name,
            contact_phone=contact_phone,
            remark=remark,
            status=Booking.Status.PENDING
        )
        
        # 4. 发送通知给管理员（后续实现）
        # NotificationService.send_booking_notification(booking)
        
        return {
            'success': True,
            'booking': booking,
            'conflicts': [],
            'equipment_warning': equipment_result.get('warning')
        }
    
    @staticmethod
    def check_booking_availability(venue, start_time, end_time, user=None,
                                    participant_count=None, required_equipments=None):
        """
        检查预约可用性（不创建预约）
        
        Returns:
            dict: {
                'available': bool,
                'conflicts': list,
                'equipment_warning': str或None
            }
        """
        checker = ConflictChecker(venue, start_time, end_time, user)
        
        # 检测容量
        if participant_count:
            checker.check_capacity(participant_count)
        
        # 检测设备
        equipment_result = checker.check_equipment(required_equipment_ids=required_equipments)
        
        # 执行所有其他检测
        conflict_result = checker.check_all()
        
        return {
            'available': not conflict_result['has_conflict'],
            'conflicts': conflict_result['conflicts'],
            'equipment_warning': equipment_result.get('warning')
        }