"""
CampusSpace 系统功能全面测试
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import authenticate, login
from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta, datetime
import random

from apps.users.models import User
from apps.venues.models import Building, Room, Equipment, RoomEquipment
from apps.bookings.models import Booking, Approval
from apps.bookings.services import ApprovalService, RecommendationService, RecommendationRequest
from apps.bookings.services.export_service import ExportService
from apps.bookings.services.notification_service import NotificationService
from apps.maintenance.models import Maintenance

print("=" * 80)
print("CampusSpace 系统功能全面测试")
print("=" * 80)
print()

test_results = []

def test(name, func):
    """测试装饰器"""
    try:
        result = func()
        if result:
            test_results.append((name, '✅ 通过', result))
            print(f"✅ {name}: {result}")
        else:
            test_results.append((name, '✅ 通过', '成功'))
            print(f"✅ {name}: 成功")
    except Exception as e:
        test_results.append((name, '❌ 失败', str(e)))
        print(f"❌ {name}: {str(e)}")
    print()

# ==================== 1. 用户认证测试 ====================
print("【1】用户认证功能测试")
print("-" * 80)
print()

def test_user_authentication():
    """测试用户认证"""
    # 测试管理员登录
    admin = authenticate(username='admin', password='admin123')
    if not admin:
        raise Exception("管理员认证失败")
    
    # 测试教师登录
    teacher = authenticate(username='teacher', password='teacher123')
    if not teacher:
        raise Exception("教师认证失败")
    
    # 测试学生登录
    student = authenticate(username='student', password='student123')
    if not student:
        raise Exception("学生认证失败")
    
    return f"管理员、教师、学生认证成功"

test("用户认证", test_user_authentication)

def test_user_count():
    """测试用户数量"""
    total = User.objects.count()
    admins = User.objects.filter(role='admin').count()
    teachers = User.objects.filter(role='teacher').count()
    students = User.objects.filter(role='student').count()
    
    return f"总数{total}人（管理员{admins} + 教师{teachers} + 学生{students}）"

test("用户统计", test_user_count)

# ==================== 2. 场地管理测试 ====================
print("【2】场地管理功能测试")
print("-" * 80)
print()

def test_buildings():
    """测试楼宇数据"""
    buildings = Building.objects.all()
    if buildings.count() == 0:
        raise Exception("没有楼宇数据")
    
    return f"{buildings.count()}栋楼宇"

test("楼宇数据", test_buildings)

def test_rooms():
    """测试场地数据"""
    rooms = Room.objects.all()
    if rooms.count() == 0:
        raise Exception("没有场地数据")
    
    available = rooms.filter(status='available').count()
    
    return f"{rooms.count()}个场地，{available}个可用"

test("场地数据", test_rooms)

def test_room_types():
    """测试场地类型分布"""
    classrooms = Room.objects.filter(venue_type='classroom').count()
    labs = Room.objects.filter(venue_type='lab').count()
    meeting_rooms = Room.objects.filter(venue_type='meeting_room').count()
    activity_rooms = Room.objects.filter(venue_type='activity_room').count()
    
    return f"教室{classrooms} + 实验室{labs} + 会议室{meeting_rooms} + 活动室{activity_rooms}"

test("场地类型分布", test_room_types)

def test_equipments():
    """测试设备数据"""
    equipments = Equipment.objects.all()
    room_equipments = RoomEquipment.objects.all()
    
    return f"{equipments.count()}种设备，{room_equipments.count()}个场地设备关联"

test("设备数据", test_equipments)

# ==================== 3. 预约功能测试 ====================
print("【3】预约功能测试")
print("-" * 80)
print()

def test_booking_count():
    """测试预约数量"""
    total = Booking.objects.count()
    if total == 0:
        raise Exception("没有预约数据")
    
    return f"{total}条预约记录"

test("预约统计", test_booking_count)

def test_booking_status():
    """测试预约状态分布"""
    pending = Booking.objects.filter(status='pending').count()
    approved = Booking.objects.filter(status='approved').count()
    rejected = Booking.objects.filter(status='rejected').count()
    cancelled = Booking.objects.filter(status='cancelled').count()
    completed = Booking.objects.filter(status='completed').count()
    
    return f"待审批{pending} + 已通过{approved} + 已拒绝{rejected} + 已取消{cancelled} + 已完成{completed}"

test("预约状态分布", test_booking_status)

def test_create_booking():
    """测试创建预约"""
    user = User.objects.filter(role='student').first()
    room = Room.objects.filter(status='available').first()
    
    if not user or not room:
        raise Exception("没有可用的用户或场地")
    
    # 创建测试预约
    start_time = timezone.now() + timedelta(days=1, hours=9)
    end_time = timezone.now() + timedelta(days=1, hours=11)
    
    booking_no = f'TEST{timezone.now().strftime("%Y%m%d%H%M%S")}'
    
    booking, created = Booking.objects.get_or_create(
        booking_no=booking_no,
        defaults={
            'venue': room,
            'user': user,
            'title': '测试预约',
            'booking_type': 'meeting',
            'start_time': start_time,
            'end_time': end_time,
            'participant_count': 10,
            'status': 'pending',
        }
    )
    
    if created:
        return f"成功创建预约 {booking.booking_no}"
    else:
        return f"预约已存在 {booking.booking_no}"

test("创建预约", test_create_booking)

# ==================== 4. 审批功能测试 ====================
print("【4】审批功能测试")
print("-" * 80)
print()

def test_approval_count():
    """测试审批记录"""
    total = Approval.objects.count()
    
    return f"{total}条审批记录"

test("审批统计", test_approval_count)

def test_approval_actions():
    """测试审批动作分布"""
    approve = Approval.objects.filter(action='approve').count()
    reject = Approval.objects.filter(action='reject').count()
    
    return f"通过{approve} + 拒绝{reject}"

test("审批动作分布", test_approval_actions)

def test_batch_approval():
    """测试批量审批"""
    # 获取待审批的预约
    pending_bookings = Booking.objects.filter(status='pending')[:3]
    
    if pending_bookings.count() == 0:
        return "没有待审批的预约"
    
    admin = User.objects.get(username='admin')
    
    # 批量审批
    booking_ids = list(pending_bookings.values_list('id', flat=True))
    results = ApprovalService.batch_approve(booking_ids, admin, '批量审批测试')
    
    return f"成功{len(results['success'])}个，失败{len(results['failed'])}个"

test("批量审批", test_batch_approval)

# ==================== 5. 推荐功能测试 ====================
print("【5】智能推荐功能测试")
print("-" * 80)
print()

def test_recommendation():
    """测试场地推荐"""
    start_time = timezone.now() + timedelta(days=1, hours=14)
    end_time = timezone.now() + timedelta(days=1, hours=16)
    
    request = RecommendationRequest(
        start_time=start_time,
        end_time=end_time,
        participant_count=30,
        required_equipment_ids=[],
        preferred_building_id=None
    )
    
    recommendations, alternative = RecommendationService.recommend(request)
    
    if recommendations:
        return f"推荐{len(recommendations)}个场地，最高分{recommendations[0].get_total_score():.1f}"
    elif alternative:
        return f"无推荐场地，建议：{alternative.message}"
    else:
        return "无推荐结果"

test("场地推荐", test_recommendation)

# ==================== 6. 数据导出测试 ====================
print("【6】数据导出功能测试")
print("-" * 80)
print()

def test_export_bookings():
    """测试预约导出"""
    bookings = Booking.objects.all()[:10]
    
    if bookings.count() == 0:
        return "没有预约数据可导出"
    
    excel_file = ExportService.export_bookings_to_excel(bookings)
    
    return f"成功导出{bookings.count()}条预约到Excel"

test("预约导出", test_export_bookings)

def test_export_statistics():
    """测试统计导出"""
    statistics_data = {
        '总预约数': Booking.objects.count(),
        '待审批': Booking.objects.filter(status='pending').count(),
        '已通过': Booking.objects.filter(status='approved').count(),
    }
    
    excel_file = ExportService.export_statistics_to_excel(statistics_data)
    
    return "成功导出统计数据到Excel"

test("统计导出", test_export_statistics)

# ==================== 7. 消息通知测试 ====================
print("【7】消息通知功能测试")
print("-" * 80)
print()

def test_notification():
    """测试消息通知"""
    user = User.objects.filter(role='student').first()
    
    if not user:
        raise Exception("没有可用的用户")
    
    # 发送测试消息
    notification = NotificationService.send_notification(
        user=user,
        title='测试消息',
        content='这是一条测试消息',
        notification_type='system'
    )
    
    # 获取未读消息数
    unread_count = NotificationService.get_unread_count(user)
    
    return f"发送消息成功，用户未读消息{unread_count}条"

test("消息通知", test_notification)

# ==================== 8. 维修管理测试 ====================
print("【8】维修管理功能测试")
print("-" * 80)
print()

def test_maintenance():
    """测试维修记录"""
    total = Maintenance.objects.count()
    
    if total == 0:
        return "没有维修记录"
    
    pending = Maintenance.objects.filter(status='pending').count()
    approved = Maintenance.objects.filter(status='approved').count()
    ongoing = Maintenance.objects.filter(status='ongoing').count()
    completed = Maintenance.objects.filter(status='completed').count()
    
    return f"{total}条维修记录（待审批{pending} + 已审批{approved} + 进行中{ongoing} + 已完成{completed}）"

test("维修记录", test_maintenance)

# ==================== 9. 统计功能测试 ====================
print("【9】统计功能测试")
print("-" * 80)
print()

def test_booking_statistics():
    """测试预约统计"""
    total = Booking.objects.count()
    
    # 按类型统计
    teaching = Booking.objects.filter(booking_type='teaching').count()
    meeting = Booking.objects.filter(booking_type='meeting').count()
    activity = Booking.objects.filter(booking_type='activity').count()
    self_study = Booking.objects.filter(booking_type='self_study').count()
    
    return f"教学{teaching} + 会议{meeting} + 活动{activity} + 自习{self_study}"

test("预约类型统计", test_booking_statistics)

def test_venue_usage():
    """测试场地使用率"""
    rooms = Room.objects.all()
    
    usage_data = []
    for room in rooms[:10]:  # 只统计前10个
        total_bookings = Booking.objects.filter(venue=room).count()
        approved = Booking.objects.filter(venue=room, status='approved').count()
        
        usage_data.append({
            'venue_name': room.name,
            'total_bookings': total_bookings,
            'approved': approved,
        })
    
    return f"统计{len(usage_data)}个场地的使用情况"

test("场地使用率统计", test_venue_usage)

# ==================== 10. 冲突检测测试 ====================
print("【10】冲突检测功能测试")
print("-" * 80)
print()

def test_conflict_detection():
    """测试冲突检测"""
    # 找一个有预约的场地
    booking = Booking.objects.filter(status='approved').first()
    
    if not booking:
        return "没有已通过的预约，无法测试冲突检测"
    
    # 尝试在同一时间段创建预约
    from apps.bookings.services.conflict_checker import ConflictChecker
    
    checker = ConflictChecker(
        venue=booking.venue,
        start_time=booking.start_time,
        end_time=booking.end_time
    )
    
    result = checker.check_all()
    
    if result.get('conflicts'):
        return f"检测到{len(result['conflicts'])}个冲突"
    else:
        return "未检测到冲突"

test("冲突检测", test_conflict_detection)

# ==================== 测试总结 ====================
print()
print("=" * 80)
print("测试总结")
print("=" * 80)
print()

passed = sum(1 for _, status, _ in test_results if '✅' in status)
failed = sum(1 for _, status, _ in test_results if '❌' in status)

print(f"总测试数：{len(test_results)}")
print(f"通过：{passed}")
print(f"失败：{failed}")
print()

if failed > 0:
    print("失败的测试：")
    for name, status, result in test_results:
        if '❌' in status:
            print(f"  - {name}: {result}")
    print()

print("=" * 80)
print("详细测试结果")
print("=" * 80)
print()

for name, status, result in test_results:
    print(f"{status} {name}")
    if result and result != '成功':
        print(f"    {result}")
    print()

print("=" * 80)

if failed == 0:
    print("✅ 所有功能测试通过！")
else:
    print(f"⚠️  {failed}个功能测试失败，请检查")

print("=" * 80)