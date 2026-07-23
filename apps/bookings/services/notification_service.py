"""
站内消息服务
"""
from apps.bookings.models import Notification, Booking
from django.conf import settings


class NotificationService:
    """站内消息服务"""
    
    @classmethod
    def send_notification(cls, user, title, content, notification_type='system', link=None):
        """
        发送消息
        
        Args:
            user: 接收用户
            title: 消息标题
            content: 消息内容
            notification_type: 消息类型
            link: 相关链接
        
        Returns:
            Notification: 消息对象
        """
        notification = Notification.objects.create(
            user=user,
            title=title,
            content=content,
            notification_type=notification_type,
            link=link
        )
        return notification
    
    @classmethod
    def send_booking_notification(cls, booking, action):
        """
        发送预约相关通知
        
        Args:
            booking: 预约对象
            action: 动作类型 ('created', 'approved', 'rejected', 'cancelled', 'reminder')
        """
        if action == 'created':
            # 通知管理员有新预约
            from apps.users.models import User
            admins = User.objects.filter(is_admin=True)
            
            for admin in admins:
                cls.send_notification(
                    user=admin,
                    title='新预约待审批',
                    content=f'用户 {booking.user.username} 提交了新预约：{booking.title}（{booking.venue.name}）',
                    notification_type=Notification.NotificationType.BOOKING,
                    link=f'/bookings/{booking.id}/'
                )
        
        elif action == 'approved':
            # 通知用户预约已通过
            cls.send_notification(
                user=booking.user,
                title='预约已通过',
                content=f'您的预约 {booking.booking_no} 已通过审批，场地：{booking.venue.name}，时间：{booking.start_time.strftime("%Y-%m-%d %H:%M")}',
                notification_type=Notification.NotificationType.APPROVAL,
                link=f'/bookings/{booking.id}/'
            )
        
        elif action == 'rejected':
            # 通知用户预约被拒绝
            cls.send_notification(
                user=booking.user,
                title='预约被拒绝',
                content=f'您的预约 {booking.booking_no} 被拒绝，场地：{booking.venue.name}',
                notification_type=Notification.NotificationType.APPROVAL,
                link=f'/bookings/{booking.id}/'
            )
        
        elif action == 'cancelled':
            # 通知用户预约已取消
            cls.send_notification(
                user=booking.user,
                title='预约已取消',
                content=f'您的预约 {booking.booking_no} 已取消',
                notification_type=Notification.NotificationType.BOOKING,
                link=f'/bookings/{booking.id}/'
            )
        
        elif action == 'reminder':
            # 提醒用户预约即将开始
            cls.send_notification(
                user=booking.user,
                title='预约即将开始',
                content=f'您的预约 {booking.booking_no} 将在30分钟后开始，场地：{booking.venue.name}',
                notification_type=Notification.NotificationType.REMINDER,
                link=f'/bookings/{booking.id}/'
            )
    
    @classmethod
    def get_user_notifications(cls, user, unread_only=False):
        """
        获取用户消息
        
        Args:
            user: 用户对象
            unread_only: 是否只获取未读消息
        
        Returns:
            QuerySet: 消息列表
        """
        queryset = Notification.objects.filter(user=user)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset
    
    @classmethod
    def get_unread_count(cls, user):
        """
        获取未读消息数量
        
        Args:
            user: 用户对象
        
        Returns:
            int: 未读消息数量
        """
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @classmethod
    def mark_all_as_read(cls, user):
        """
        标记所有消息为已读
        
        Args:
            user: 用户对象
        
        Returns:
            int: 更新的消息数量
        """
        return Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    
    @classmethod
    def send_system_broadcast(cls, title, content):
        """
        发送系统广播消息
        
        Args:
            title: 消息标题
            content: 消息内容
        
        Returns:
            int: 发送的消息数量
        """
        from apps.users.models import User
        users = User.objects.filter(is_active=True)
        
        count = 0
        for user in users:
            cls.send_notification(
                user=user,
                title=title,
                content=content,
                notification_type=Notification.NotificationType.SYSTEM
            )
            count += 1
        
        return count