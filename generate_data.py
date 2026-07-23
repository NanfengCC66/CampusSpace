"""
分步生成演示数据
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
import random
from apps.venues.models import Building, Room, Equipment, RoomEquipment
from apps.bookings.models import Booking, Approval
from apps.schedules.models import Schedule
from apps.maintenance.models import Maintenance

User = get_user_model()

print("=" * 60)
print("CampusSpace 数据生成")
print("=" * 60)
print()

# 1. 创建用户
print("【1】创建用户...")
print()

# 管理员
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@campus.edu',
        'first_name': '系统',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin.set_password('admin123')
    admin.save()
print(f"  ✅ 管理员: admin / admin123")

# 简化演示账号
teacher, created = User.objects.get_or_create(
    username='teacher',
    defaults={
        'email': 'teacher@campus.edu',
        'first_name': '教师',
        'role': 'teacher',
        'department': '计算机学院',
    }
)
if created:
    teacher.set_password('teacher123')
    teacher.save()
print(f"  ✅ 教师: teacher / teacher123")

student, created = User.objects.get_or_create(
    username='student',
    defaults={
        'email': 'student@campus.edu',
        'first_name': '学生',
        'role': 'student',
        'department': '计算机学院',
    }
)
if created:
    student.set_password('student123')
    student.save()
print(f"  ✅ 学生: student / student123")

# 更多教师
departments = ['计算机学院', '数学学院', '物理学院', '外语学院', '化学学院']
teacher_count = 0
for i in range(1, 21):
    username = f'teacher{i:02d}'
    teacher, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f"{username}@campus.edu",
            'first_name': f'教师{i}',
            'role': 'teacher',
            'department': random.choice(departments),
        }
    )
    if created:
        teacher.set_password('teacher123')
        teacher.save()
        teacher_count += 1
print(f"  ✅ 创建 {teacher_count} 位教师")

# 更多学生
student_count = 0
for i in range(1, 51):
    username = f'student{i:03d}'
    student, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f"{username}@campus.edu",
            'first_name': f'学生{i}',
            'role': 'student',
            'department': random.choice(departments),
        }
    )
    if created:
        student.set_password('student123')
        student.save()
        student_count += 1
print(f"  ✅ 创建 {student_count} 位学生")

print()

# 2. 创建楼宇和场地
print("【2】创建楼宇和场地...")
print()

buildings_data = [
    {'name': '教学楼A', 'location': '校园东区', 'total_floors': 6},
    {'name': '教学楼B', 'location': '校园东区', 'total_floors': 5},
    {'name': '教学楼C', 'location': '校园西区', 'total_floors': 5},
    {'name': '实验楼', 'location': '校园北区', 'total_floors': 4},
    {'name': '行政楼', 'location': '校园中心区', 'total_floors': 3},
]

for data in buildings_data:
    Building.objects.get_or_create(name=data['name'], defaults=data)

rooms_data = []

# 教学楼A
for floor in range(1, 7):
    for room in range(1, 4):
        rooms_data.append({
            'name': f'A{floor}{room:02d}教室',
            'building': '教学楼A',
            'floor': floor,
            'room_number': f'{floor}{room:02d}',
            'venue_type': 'classroom',
            'capacity': random.choice([50, 60, 70]),
            'area': random.randint(80, 120)
        })

# 教学楼B
for floor in range(1, 6):
    for room in range(1, 4):
        rooms_data.append({
            'name': f'B{floor}{room:02d}教室',
            'building': '教学楼B',
            'floor': floor,
            'room_number': f'{floor}{room:02d}',
            'venue_type': 'classroom',
            'capacity': random.choice([50, 60, 70]),
            'area': random.randint(80, 120)
        })

# 教学楼C
for floor in range(1, 6):
    for room in range(1, 4):
        rooms_data.append({
            'name': f'C{floor}{room:02d}教室',
            'building': '教学楼C',
            'floor': floor,
            'room_number': f'{floor}{room:02d}',
            'venue_type': 'classroom',
            'capacity': random.choice([50, 60, 70]),
            'area': random.randint(80, 120)
        })

# 实验楼
for floor in range(1, 5):
    for i in range(1, 4):
        rooms_data.append({
            'name': f'实验室{floor}{i:02d}',
            'building': '实验楼',
            'floor': floor,
            'room_number': f'{floor}{i:02d}',
            'venue_type': 'lab',
            'capacity': random.choice([30, 40]),
            'area': random.randint(100, 150)
        })

# 行政楼（会议室）
for floor in range(1, 4):
    for room in range(1, 4):
        rooms_data.append({
            'name': f'会议室{floor}{room:02d}',
            'building': '行政楼',
            'floor': floor,
            'room_number': f'{floor}{room:02d}',
            'venue_type': 'meeting_room',
            'capacity': random.choice([20, 30, 40]),
            'area': random.randint(40, 80)
        })

room_count = 0
for data in rooms_data:
    building_name = data.pop('building')
    building = Building.objects.get(name=building_name)
    room, created = Room.objects.get_or_create(
        name=data['name'],
        building=building,
        defaults={**data, 'status': 'available', 'created_by': admin}
    )
    if created:
        room_count += 1

print(f"  ✅ 创建 {len(buildings_data)} 栋楼宇")
print(f"  ✅ 创建 {room_count} 个场地")
print()

# 3. 创建设备
print("【3】创建设备...")
print()

equipments_data = [
    {'name': '投影仪', 'code': 'projector'},
    {'name': '空调', 'code': 'air_conditioner'},
    {'name': '电脑', 'code': 'computer'},
    {'name': '白板', 'code': 'whiteboard'},
    {'name': '音响', 'code': 'speaker'},
    {'name': '麦克风', 'code': 'microphone'},
]

for data in equipments_data:
    Equipment.objects.get_or_create(name=data['name'], defaults=data)

print(f"  ✅ 创建 {len(equipments_data)} 种设备")
print()

# 4. 创建预约数据
print("【4】创建预约数据...")
print()

rooms = list(Room.objects.all())
users = list(User.objects.filter(role__in=['teacher', 'student']))

time_slots = [(8, 10), (10, 12), (14, 16), (16, 18), (19, 21)]
booking_types = ['teaching', 'meeting', 'activity', 'self_study']

count = 0
approval_count = 0

# 生成过去30天的预约
for days_ago in range(30, 0, -1):
    date = timezone.now().date() - timedelta(days=days_ago)
    
    daily_bookings = random.randint(5, 10)
    
    for _ in range(daily_bookings):
        room = random.choice(rooms)
        user = random.choice(users)
        start_hour, end_hour = random.choice(time_slots)
        
        start_time = timezone.make_aware(datetime.combine(date, datetime.min.time().replace(hour=start_hour)))
        end_time = timezone.make_aware(datetime.combine(date, datetime.min.time().replace(hour=end_hour)))
        
        if days_ago <= 2:
            status = random.choice(['pending', 'approved', 'rejected'])
        elif days_ago <= 7:
            status = random.choice(['approved', 'rejected', 'cancelled'])
        else:
            status = random.choice(['approved', 'rejected', 'cancelled', 'completed'])
        
        booking_no = f'BK{date.strftime("%Y%m%d")}{count+1:05d}'
        
        booking, created = Booking.objects.get_or_create(
            booking_no=booking_no,
            defaults={
                'venue': room,
                'user': user,
                'title': random.choice(['课程教学', '学术会议', '学生活动', '小组讨论', '考试安排']),
                'booking_type': random.choice(booking_types),
                'start_time': start_time,
                'end_time': end_time,
                'participant_count': random.randint(10, min(room.capacity, 50)),
                'status': status,
            }
        )
        
        if created:
            count += 1
            
            if status in ['approved', 'rejected']:
                Approval.objects.create(
                    booking=booking,
                    approver=admin,
                    action='approve' if status == 'approved' else 'reject',
                    comment='同意' if status == 'approved' else '时间冲突'
                )
                approval_count += 1

print(f"  ✅ 创建 {count} 条预约")
print(f"  ✅ 创建 {approval_count} 条审批记录")
print()

# 5. 创建维修记录
print("【5】创建维修记录...")
print()

maintenance_count = 0
for room in random.sample(rooms, min(5, len(rooms))):
    start_time = timezone.now() + timedelta(days=random.randint(-10, 10))
    end_time = start_time + timedelta(days=random.randint(1, 5))
    
    Maintenance.objects.get_or_create(
        venue=room,
        start_time=start_time,
        defaults={
            'reason': random.choice(['设备维修', '装修改造', '安全检查']),
            'end_time': end_time,
            'status': random.choice(['pending', 'approved', 'ongoing', 'completed']),
            'approval_status': 'approved',
            'approved_by': admin,
            'created_by': admin,
        }
    )
    maintenance_count += 1

print(f"  ✅ 创建 {maintenance_count} 条维修记录")
print()

print("=" * 60)
print("数据生成完成！")
print("=" * 60)
print()
print("数据统计：")
print(f"  用户总数：{User.objects.count()}")
print(f"  楼宇总数：{Building.objects.count()}")
print(f"  场地总数：{Room.objects.count()}")
print(f"  设备总数：{Equipment.objects.count()}")
print(f"  预约总数：{Booking.objects.count()}")
print(f"  审批总数：{Approval.objects.count()}")
print(f"  维修总数：{Maintenance.objects.count()}")
print()
print("=" * 60)
print()
print("演示账号：")
print("  管理员: admin / admin123")
print("  教师: teacher / teacher123")
print("  学生: student / student123")
print()
print("=" * 60)