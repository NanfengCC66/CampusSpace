"""
冲突检测服务
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from apps.venues.models import Room, Equipment
from apps.schedules.models import Schedule
from apps.maintenance.models import Maintenance
from apps.bookings.models import Booking


class ConflictChecker:
    """冲突检测器"""
    
    # 时间间隔要求（分钟）
    TIME_INTERVAL_MINUTES = 10
    
    # 预约时长限制（分钟）
    MIN_DURATION_MINUTES = 30
    MAX_DURATION_MINUTES = 8 * 60  # 8小时
    
    def __init__(self, venue, start_time, end_time, user=None, exclude_booking_id=None):
        """
        初始化冲突检测器
        
        Args:
            venue: 场地对象
            start_time: 开始时间
            end_time: 结束时间
            user: 用户对象（可选）
            exclude_booking_id: 排除的预约ID（用于修改场景）
        """
        self.venue = venue
        self.start_time = start_time
        self.end_time = end_time
        self.user = user
        self.exclude_booking_id = exclude_booking_id
        self.conflicts = []
    
    def check_all(self):
        """
        执行所有冲突检测
        
        Returns:
            dict: {
                'has_conflict': bool,
                'conflicts': list
            }
        """
        # 按优先级顺序检测
        self.check_time_validity()
        self.check_capacity()
        self.check_maintenance_conflict()
        self.check_schedule_conflict()
        self.check_booking_conflict()
        self.check_user_time_conflict()
        self.check_time_interval()
        
        return {
            'has_conflict': len(self.conflicts) > 0,
            'conflicts': self.conflicts
        }
    
    def check_time_validity(self):
        """检测时间有效性"""
        now = timezone.now()
        
        # 检查开始时间是否早于结束时间
        if self.start_time >= self.end_time:
            self.conflicts.append({
                'type': 'time_validity',
                'message': '开始时间必须早于结束时间',
                'detail': {
                    'start_time': self.start_time,
                    'end_time': self.end_time
                }
            })
            return
        
        # 检查开始时间是否在未来
        if self.start_time <= now:
            self.conflicts.append({
                'type': 'time_validity',
                'message': '开始时间必须在未来',
                'detail': {
                    'start_time': self.start_time,
                    'now': now
                }
            })
            return
        
        # 检查预约时长
        duration_minutes = (self.end_time - self.start_time).total_seconds() / 60
        
        if duration_minutes < self.MIN_DURATION_MINUTES:
            self.conflicts.append({
                'type': 'time_validity',
                'message': f'预约时长不能少于{self.MIN_DURATION_MINUTES}分钟',
                'detail': {
                    'duration': f'{int(duration_minutes)}分钟',
                    'min_duration': f'{self.MIN_DURATION_MINUTES}分钟'
                }
            })
        
        if duration_minutes > self.MAX_DURATION_MINUTES:
            self.conflicts.append({
                'type': 'time_validity',
                'message': f'预约时长不能超过{self.MAX_DURATION_MINUTES // 60}小时',
                'detail': {
                    'duration': f'{int(duration_minutes)}分钟',
                    'max_duration': f'{self.MAX_DURATION_MINUTES}分钟'
                }
            })
    
    def check_capacity(self, participant_count=None):
        """
        检测场地容量
        
        Args:
            participant_count: 参与人数（可选）
        """
        if participant_count and participant_count > self.venue.capacity:
            self.conflicts.append({
                'type': 'capacity',
                'message': f'参与人数({participant_count}人)超过场地容量({self.venue.capacity}人)',
                'detail': {
                    'participant_count': participant_count,
                    'capacity': self.venue.capacity
                }
            })
    
    def check_equipment(self, required_equipment_ids=None):
        """
        检测设备要求
        
        Args:
            required_equipment_ids: 所需设备ID列表
        
        Returns:
            dict: {
                'has_missing': bool,
                'missing_equipments': list,
                'warning': str
            }
        """
        if not required_equipment_ids:
            return {'has_missing': False, 'missing_equipments': [], 'warning': None}
        
        # 获取场地设备
        venue_equipment_ids = set(
            self.venue.room_equipments.filter(
                status='normal'
            ).values_list('equipment_id', flat=True)
        )
        
        required_ids = set(required_equipment_ids)
        missing_ids = required_ids - venue_equipment_ids
        
        if missing_ids:
            missing_equipments = Equipment.objects.filter(id__in=missing_ids)
            missing_names = [eq.name for eq in missing_equipments]
            
            return {
                'has_missing': True,
                'missing_equipments': missing_names,
                'warning': f'场地缺少以下设备，请自备：{", ".join(missing_names)}'
            }
        
        return {'has_missing': False, 'missing_equipments': [], 'warning': None}
    
    def check_maintenance_conflict(self):
        """检测维修停用冲突（优先级最高）"""
        # 查询进行中和已审批的维修记录
        maintenances = Maintenance.objects.filter(
            venue=self.venue,
            status__in=['approved', 'ongoing']
        )
        
        for maintenance in maintenances:
            if self._has_time_overlap(
                self.start_time, self.end_time,
                maintenance.start_time, maintenance.end_time
            ):
                self.conflicts.append({
                    'type': 'maintenance',
                    'message': f'场地在{maintenance.start_time.strftime("%Y-%m-%d %H:%M")}至{maintenance.end_time.strftime("%Y-%m-%d %H:%M")}维修停用',
                    'detail': {
                        'reason': maintenance.reason,
                        'start_time': maintenance.start_time,
                        'end_time': maintenance.end_time,
                        'status': maintenance.get_status_display()
                    }
                })
    
    def check_schedule_conflict(self):
        """检测固定课表冲突（优先级高）"""
        # 将预约时间转换为周次和星期
        start_week, start_day = self._get_week_and_day(self.start_time)
        end_week, end_day = self._get_week_and_day(self.end_time)
        
        # 查询课表
        schedules = Schedule.objects.filter(venue=self.venue)
        
        for schedule in schedules:
            # 检查星期是否匹配
            if schedule.day_of_week != start_day:
                continue
            
            # 检查周次是否重叠
            if not self._has_week_overlap(
                start_week, end_week,
                schedule.start_week, schedule.end_week
            ):
                continue
            
            # 检查节次是否重叠
            if self._has_period_overlap(self.start_time, self.end_time, schedule.period):
                self.conflicts.append({
                    'type': 'schedule',
                    'message': f'场地在此时段有课程：{schedule.course_name}',
                    'detail': {
                        'course_name': schedule.course_name,
                        'teacher': schedule.teacher,
                        'day': schedule.get_day_display(),
                        'period': schedule.period,
                        'weeks': schedule.week_range
                    }
                })
    
    def check_booking_conflict(self):
        """检测已批准预约冲突（优先级中）"""
        # 查询已批准的预约
        bookings = Booking.objects.filter(
            venue=self.venue,
            status='approved'
        )
        
        # 排除指定预约（用于修改场景）
        if self.exclude_booking_id:
            bookings = bookings.exclude(id=self.exclude_booking_id)
        
        for booking in bookings:
            if self._has_time_overlap(
                self.start_time, self.end_time,
                booking.start_time, booking.end_time
            ):
                # 转换为本地时间显示
                local_start = timezone.localtime(booking.start_time)
                local_end = timezone.localtime(booking.end_time)
                self.conflicts.append({
                    'type': 'booking',
                    'message': f'场地在{local_start.strftime("%Y-%m-%d %H:%M")}至{local_end.strftime("%Y-%m-%d %H:%M")}已被预约',
                    'detail': {
                        'booking_no': booking.booking_no,
                        'title': booking.title,
                        'start_time': booking.start_time,
                        'end_time': booking.end_time
                    }
                })
    
    def check_user_time_conflict(self):
        """检测用户时间冲突"""
        if not self.user:
            return
        
        # 查询用户的其他预约
        user_bookings = Booking.objects.filter(
            user=self.user,
            status__in=['pending', 'approved']
        )
        
        # 排除指定预约
        if self.exclude_booking_id:
            user_bookings = user_bookings.exclude(id=self.exclude_booking_id)
        
        for booking in user_bookings:
            if self._has_time_overlap(
                self.start_time, self.end_time,
                booking.start_time, booking.end_time
            ):
                # 转换为本地时间显示
                local_start = timezone.localtime(booking.start_time)
                local_end = timezone.localtime(booking.end_time)
                self.conflicts.append({
                    'type': 'user_conflict',
                    'message': f'您在{local_start.strftime("%Y-%m-%d %H:%M")}至{local_end.strftime("%Y-%m-%d %H:%M")}已有预约',
                    'detail': {
                        'booking_no': booking.booking_no,
                        'venue': booking.venue.name,
                        'title': booking.title,
                        'start_time': booking.start_time,
                        'end_time': booking.end_time
                    }
                })
    
    def check_time_interval(self):
        """检测时间间隔（强制）"""
        # 查询前后预约
        bookings = Booking.objects.filter(
            venue=self.venue,
            status='approved'
        )
        
        if self.exclude_booking_id:
            bookings = bookings.exclude(id=self.exclude_booking_id)
        
        interval = timedelta(minutes=self.TIME_INTERVAL_MINUTES)
        
        for booking in bookings:
            # 检查前一个预约
            if booking.end_time <= self.start_time:
                if booking.end_time + interval > self.start_time:
                    self.conflicts.append({
                        'type': 'interval',
                        'message': f'与前一个预约间隔不足{self.TIME_INTERVAL_MINUTES}分钟',
                        'detail': {
                            'booking_no': booking.booking_no,
                            'end_time': booking.end_time,
                            'required_interval': f'{self.TIME_INTERVAL_MINUTES}分钟'
                        }
                    })
            
            # 检查后一个预约
            if booking.start_time >= self.end_time:
                if self.end_time + interval > booking.start_time:
                    self.conflicts.append({
                        'type': 'interval',
                        'message': f'与后一个预约间隔不足{self.TIME_INTERVAL_MINUTES}分钟',
                        'detail': {
                            'booking_no': booking.booking_no,
                            'start_time': booking.start_time,
                            'required_interval': f'{self.TIME_INTERVAL_MINUTES}分钟'
                        }
                    })
    
    def _has_time_overlap(self, start1, end1, start2, end2):
        """判断两个时间段是否重叠"""
        return max(start1, start2) < min(end1, end2)
    
    def _has_week_overlap(self, start_week1, end_week1, start_week2, end_week2):
        """判断两个周次范围是否重叠"""
        return max(start_week1, start_week2) <= min(end_week1, end_week2)
    
    def _has_period_overlap(self, start_time, end_time, period):
        """判断时间是否与节次重叠"""
        # 简化处理：假设预约时间在一天内
        # 将节次转换为时间范围
        period_time_map = {
            '1-2': (8, 0, 9, 40),
            '3-4': (10, 0, 11, 40),
            '5-6': (14, 0, 15, 40),
            '7-8': (16, 0, 17, 40),
            '9-10': (19, 0, 20, 40),
        }
        
        if period not in period_time_map:
            return False
        
        start_h, start_m, end_h, end_m = period_time_map[period]
        
        # 获取预约时间的日期
        booking_date = start_time.date()
        period_start = timezone.datetime(
            booking_date.year, booking_date.month, booking_date.day,
            start_h, start_m, tzinfo=timezone.get_current_timezone()
        )
        period_end = timezone.datetime(
            booking_date.year, booking_date.month, booking_date.day,
            end_h, end_m, tzinfo=timezone.get_current_timezone()
        )
        
        return self._has_time_overlap(start_time, end_time, period_start, period_end)
    
    def _get_week_and_day(self, datetime_obj):
        """获取日期对应的周次和星期"""
        # 简化处理：假设学期从2025年9月1日开始
        # 实际应用中应该从配置或学期表中获取
        semester_start = timezone.datetime(2025, 9, 1, tzinfo=timezone.get_current_timezone())
        
        days = (datetime_obj.date() - semester_start.date()).days
        week = days // 7 + 1
        day_of_week = datetime_obj.isoweekday()
        
        return week, day_of_week