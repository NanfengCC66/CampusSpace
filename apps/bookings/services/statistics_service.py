"""
统计分析服务
"""
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from apps.bookings.models import Booking
from apps.schedules.models import Schedule
from apps.venues.models import Room, Building
from collections import defaultdict


class StatisticsService:
    """统计服务"""
    
    @classmethod
    def get_venue_utilization(cls, venue_id=None, start_date=None, end_date=None):
        """
        计算场地利用率
        
        Args:
            venue_id: 场地ID（可选，不传则统计所有场地）
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            dict: {
                'venues': [场地利用率列表],
                'average': 平均利用率,
                'total_hours': 总使用小时数
            }
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        venues = Room.objects.filter(status='available')
        if venue_id:
            venues = venues.filter(id=venue_id)
        
        venue_stats = []
        total_utilization = 0
        total_hours = 0
        
        for venue in venues:
            bookings = Booking.objects.filter(
                venue=venue,
                status__in=['approved', 'completed'],
                start_time__gte=start_datetime,
                end_time__lte=end_datetime
            )
            
            used_hours = 0
            for booking in bookings:
                duration = (booking.end_time - booking.start_time).total_seconds() / 3600
                used_hours += duration
            
            days = (end_date - start_date).days + 1
            available_hours_per_day = 14
            total_available_hours = days * available_hours_per_day
            
            utilization_rate = (used_hours / total_available_hours * 100) if total_available_hours > 0 else 0
            
            venue_stats.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'building_name': venue.building.name,
                'capacity': venue.capacity,
                'used_hours': round(used_hours, 2),
                'available_hours': total_available_hours,
                'utilization_rate': round(utilization_rate, 2),
                'booking_count': bookings.count()
            })
            
            total_utilization += utilization_rate
            total_hours += used_hours
        
        average_utilization = (total_utilization / len(venues)) if venues else 0
        
        return {
            'venues': venue_stats,
            'average': round(average_utilization, 2),
            'total_hours': round(total_hours, 2),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    
    @classmethod
    def get_booking_trend(cls, start_date=None, end_date=None, granularity='day'):
        """
        预约趋势统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            granularity: 粒度（day/week/month）
        
        Returns:
            dict: {
                'trend': [趋势数据],
                'total': 总预约数,
                'approved': 已通过数,
                'rejected': 已拒绝数
            }
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        bookings = Booking.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        trunc_func = TruncDate
        if granularity == 'week':
            trunc_func = TruncWeek
        elif granularity == 'month':
            trunc_func = TruncMonth
        
        trend_data = bookings.annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            total=Count('id'),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected')),
            pending=Count('id', filter=Q(status='pending')),
            cancelled=Count('id', filter=Q(status='cancelled'))
        ).order_by('period')
        
        trend_list = []
        for item in trend_data:
            trend_list.append({
                'period': item['period'].isoformat() if item['period'] else None,
                'total': item['total'],
                'approved': item['approved'],
                'rejected': item['rejected'],
                'pending': item['pending'],
                'cancelled': item['cancelled']
            })
        
        total_stats = bookings.aggregate(
            total=Count('id'),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected'))
        )
        
        return {
            'trend': trend_list,
            'total': total_stats['total'] or 0,
            'approved': total_stats['approved'] or 0,
            'rejected': total_stats['rejected'] or 0,
            'granularity': granularity
        }
    
    @classmethod
    def get_booking_type_statistics(cls, start_date=None, end_date=None):
        """
        按预约类型统计（固定课表 vs 临时预约）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            dict: {
                'booking_types': {类型: 数量},
                'schedule_count': 固定课表数量,
                'temp_booking_count': 临时预约数量
            }
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        bookings = Booking.objects.filter(
            status__in=['approved', 'completed'],
            start_time__gte=start_datetime,
            end_time__lte=end_datetime
        )
        
        booking_types = bookings.values('booking_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        type_stats = {}
        for item in booking_types:
            type_stats[item['booking_type']] = item['count']
        
        schedules = Schedule.objects.all()
        
        schedule_count = schedules.count()
        temp_booking_count = bookings.count()
        
        return {
            'booking_types': type_stats,
            'schedule_count': schedule_count,
            'temp_booking_count': temp_booking_count,
            'total_count': schedule_count + temp_booking_count
        }
    
    @classmethod
    def get_status_distribution(cls, start_date=None, end_date=None):
        """
        预约状态分布
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            dict: {状态: 数量}
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        bookings = Booking.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        status_stats = bookings.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        result = {}
        for item in status_stats:
            result[item['status']] = item['count']
        
        return result
    
    @classmethod
    def get_popular_venues(cls, limit=10, start_date=None, end_date=None):
        """
        热门场地排行
        
        Args:
            limit: 返回数量
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            list: [场地统计信息]
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        venue_stats = Booking.objects.filter(
            status__in=['approved', 'completed'],
            start_time__gte=start_datetime,
            end_time__lte=end_datetime
        ).values(
            'venue__id',
            'venue__name',
            'venue__building__name'
        ).annotate(
            booking_count=Count('id'),
            total_hours=Sum(
                F('end_time') - F('start_time')
            )
        ).order_by('-booking_count')[:limit]
        
        result = []
        for stat in venue_stats:
            hours = 0
            if stat['total_hours']:
                hours = stat['total_hours'].total_seconds() / 3600
            
            result.append({
                'venue_id': stat['venue__id'],
                'venue_name': stat['venue__name'],
                'building_name': stat['venue__building__name'],
                'booking_count': stat['booking_count'],
                'total_hours': round(hours, 2)
            })
        
        return result
    
    @classmethod
    def get_time_distribution(cls, start_date=None, end_date=None):
        """
        时间段分布统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            dict: {时间段: 预约数量}
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        bookings = Booking.objects.filter(
            status__in=['approved', 'completed'],
            start_time__gte=start_datetime,
            end_time__lte=end_datetime
        )
        
        time_slots = defaultdict(int)
        
        for booking in bookings:
            hour = booking.start_time.hour
            if 8 <= hour < 10:
                time_slots['08:00-10:00'] += 1
            elif 10 <= hour < 12:
                time_slots['10:00-12:00'] += 1
            elif 12 <= hour < 14:
                time_slots['12:00-14:00'] += 1
            elif 14 <= hour < 16:
                time_slots['14:00-16:00'] += 1
            elif 16 <= hour < 18:
                time_slots['16:00-18:00'] += 1
            elif 18 <= hour < 20:
                time_slots['18:00-20:00'] += 1
            else:
                time_slots['其他'] += 1
        
        return dict(time_slots)
    
    @classmethod
    def get_building_statistics(cls, start_date=None, end_date=None):
        """
        按楼宇统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            list: [楼宇统计信息]
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        buildings = Building.objects.all()
        result = []
        
        for building in buildings:
            bookings = Booking.objects.filter(
                venue__building=building,
                status__in=['approved', 'completed'],
                start_time__gte=start_datetime,
                end_time__lte=end_datetime
            )
            
            result.append({
                'building_id': building.id,
                'building_name': building.name,
                'room_count': building.rooms.count(),
                'booking_count': bookings.count(),
                'total_capacity': sum(r.capacity for r in building.rooms.all())
            })
        
        return sorted(result, key=lambda x: x['booking_count'], reverse=True)