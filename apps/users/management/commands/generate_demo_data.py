from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
import random
from apps.venues.models import Building, Room, Equipment, RoomEquipment
from apps.bookings.models import Booking, Approval
from apps.schedules.models import Schedule
from apps.maintenance.models import Maintenance

User = get_user_model()


class Command(BaseCommand):
    help = '生成大量演示数据'
    
    def handle(self, *args, **options):
        self.stdout.write('开始生成大量演示数据...')
        
        # 1. 创建用户
        self.create_users()
        
        # 2. 创建楼宇和场地
        self.create_buildings_and_rooms()
        
        # 3. 创建设备
        self.create_equipments()
        
        # 4. 创建固定课表
        self.create_schedules()
        
        # 5. 创建预约数据
        self.create_bookings()
        
        # 6. 创建维修停用数据
        self.create_maintenance()
        
        self.stdout.write(self.style.SUCCESS('\n演示数据生成完成！'))
        self.print_summary()
    
    def create_users(self):
        self.stdout.write('创建用户...')
        
        # 管理员
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@campus.edu',
                'first_name': '系统',
                'last_name': '管理员',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        
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
        
        # 更多教师（30位）
        departments = ['计算机学院', '数学学院', '物理学院', '外语学院', '化学学院', '生物学院', '经济学院', '管理学院']
        teacher_names = ['张', '李', '王', '赵', '刘', '陈', '杨', '黄', '周', '吴', '郑', '孙', '马', '朱', '胡', '林', '何', '高', '郭', '徐', '唐', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕']
        
        for i, name in enumerate(teacher_names):
            username = f'teacher_{i+1:02d}'
            teacher, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@campus.edu",
                    'first_name': name + '老师',
                    'role': 'teacher',
                    'department': random.choice(departments),
                    'phone': f"138{random.randint(10000000, 99999999)}",
                }
            )
            if created:
                teacher.set_password('teacher123')
                teacher.save()
        
        self.stdout.write(self.style.SUCCESS(f'  创建 {len(teacher_names) + 1} 位教师'))
        
        # 更多学生（100位）
        for i in range(1, 101):
            username = f'student{i:03d}'
            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@campus.edu",
                    'first_name': f'学生{i}',
                    'role': 'student',
                    'department': random.choice(departments),
                    'phone': f"139{random.randint(10000000, 99999999)}",
                }
            )
            if created:
                student.set_password('student123')
                student.save()
        
        self.stdout.write(self.style.SUCCESS(f'  创建 100 位学生'))
    
    def create_buildings_and_rooms(self):
        self.stdout.write('创建楼宇和场地...')
        
        buildings_data = [
            {'name': '教学楼A', 'location': '校园东区', 'total_floors': 6, 'description': '主要教学楼'},
            {'name': '教学楼B', 'location': '校园东区', 'total_floors': 5, 'description': '理工科教学楼'},
            {'name': '教学楼C', 'location': '校园西区', 'total_floors': 5, 'description': '文科教学楼'},
            {'name': '教学楼D', 'location': '校园西区', 'total_floors': 4, 'description': '艺术教学楼'},
            {'name': '实验楼', 'location': '校园北区', 'total_floors': 4, 'description': '实验室'},
            {'name': '行政楼', 'location': '校园中心区', 'total_floors': 3, 'description': '行政办公'},
            {'name': '图书馆', 'location': '校园中心区', 'total_floors': 5, 'description': '图书馆及自习室'},
        ]
        
        for data in buildings_data:
            Building.objects.get_or_create(name=data['name'], defaults=data)
        
        admin = User.objects.get(username='admin')
        
        rooms_data = []
        
        # 教学楼A（每层3个教室）
        for floor in range(1, 7):
            for room in range(1, 4):
                rooms_data.append({
                    'name': f'A{floor}{room:02d}教室',
                    'building': '教学楼A',
                    'floor': floor,
                    'room_number': f'{floor}{room:02d}',
                    'venue_type': 'classroom',
                    'capacity': random.choice([50, 60, 70, 80]),
                    'area': random.randint(80, 120)
                })
        
        # 教学楼B（每层3个教室）
        for floor in range(1, 6):
            for room in range(1, 4):
                rooms_data.append({
                    'name': f'B{floor}{room:02d}教室',
                    'building': '教学楼B',
                    'floor': floor,
                    'room_number': f'{floor}{room:02d}',
                    'venue_type': 'classroom',
                    'capacity': random.choice([50, 60, 70, 80]),
                    'area': random.randint(80, 120)
                })
        
        # 教学楼C（每层3个教室）
        for floor in range(1, 6):
            for room in range(1, 4):
                rooms_data.append({
                    'name': f'C{floor}{room:02d}教室',
                    'building': '教学楼C',
                    'floor': floor,
                    'room_number': f'{floor}{room:02d}',
                    'venue_type': 'classroom',
                    'capacity': random.choice([50, 60, 70, 80]),
                    'area': random.randint(80, 120)
                })
        
        # 实验楼（实验室）
        lab_names = ['计算机', '物理', '化学', '生物', '电子']
        for floor in range(1, 5):
            for i, lab_name in enumerate(lab_names):
                rooms_data.append({
                    'name': f'{lab_name}实验室{floor}{i+1}',
                    'building': '实验楼',
                    'floor': floor,
                    'room_number': f'{floor}{i+1:02d}',
                    'venue_type': 'lab',
                    'capacity': random.choice([30, 40, 50]),
                    'area': random.randint(100, 150)
                })
        
        # 行政楼（会议室）
        for floor in range(1, 4):
            for room in range(1, 4):
                rooms_data.append({
                    'name': f'第{floor}{room}会议室',
                    'building': '行政楼',
                    'floor': floor,
                    'room_number': f'{floor}{room:02d}',
                    'venue_type': 'meeting_room',
                    'capacity': random.choice([20, 30, 40, 50]),
                    'area': random.randint(40, 80)
                })
        
        # 图书馆（自习室）
        for floor in range(1, 6):
            rooms_data.append({
                'name': f'{floor}楼自习室',
                'building': '图书馆',
                'floor': floor,
                'room_number': f'{floor}01',
                'venue_type': 'activity_room',
                'capacity': random.choice([100, 150, 200]),
                'area': random.randint(200, 400)
            })
        
        # 报告厅
        rooms_data.append({
            'name': '大报告厅',
            'building': '行政楼',
            'floor': 1,
            'room_number': '001',
            'venue_type': 'activity_room',
            'capacity': 500,
            'area': 800
        })
        
        rooms_data.append({
            'name': '小报告厅',
            'building': '行政楼',
            'floor': 2,
            'room_number': '201',
            'venue_type': 'activity_room',
            'capacity': 200,
            'area': 300
        })
        
        for data in rooms_data:
            building_name = data.pop('building')
            building = Building.objects.get(name=building_name)
            Room.objects.get_or_create(
                name=data['name'],
                building=building,
                defaults={**data, 'status': 'available', 'created_by': admin}
            )
        
        self.stdout.write(self.style.SUCCESS(f'  创建 {len(rooms_data)} 个场地'))
    
    def create_equipments(self):
        self.stdout.write('创建设备...')
        
        equipments_data = [
            {'name': '投影仪', 'code': 'projector', 'category': '教学设备'},
            {'name': '空调', 'code': 'air_conditioner', 'category': '环境设备'},
            {'name': '电脑', 'code': 'computer', 'category': '计算设备'},
            {'name': '白板', 'code': 'whiteboard', 'category': '教学设备'},
            {'name': '音响', 'code': 'speaker', 'category': '音响设备'},
            {'name': '麦克风', 'code': 'microphone', 'category': '音响设备'},
            {'name': '激光笔', 'code': 'laser_pointer', 'category': '教学设备'},
            {'name': '视频会议系统', 'code': 'video_conf', 'category': '会议设备'},
            {'name': '智能黑板', 'code': 'smart_board', 'category': '教学设备'},
            {'name': '实验台', 'code': 'lab_bench', 'category': '实验设备'},
        ]
        
        for data in equipments_data:
            Equipment.objects.get_or_create(name=data['name'], defaults=data)
        
        # 为场地随机分配设备
        rooms = Room.objects.all()
        equipments = list(Equipment.objects.all())
        
        for room in rooms:
            # 每个场地随机分配2-5个设备
            num_equipments = random.randint(2, 5)
            selected_equipments = random.sample(equipments, min(num_equipments, len(equipments)))
            
            for equipment in selected_equipments:
                RoomEquipment.objects.get_or_create(
                    room=room,
                    equipment=equipment,
                    defaults={'quantity': random.randint(1, 3), 'status': 'normal'}
                )
        
        self.stdout.write(self.style.SUCCESS(f'  创建 {len(equipments_data)} 种设备'))
    
    def create_schedules(self):
        self.stdout.write('创建固定课表...')
        
        rooms = list(Room.objects.filter(venue_type='classroom'))
        teachers = list(User.objects.filter(role='teacher'))
        
        courses = [
            ('高等数学', '1-2'),
            ('线性代数', '3-4'),
            ('程序设计', '1-2'),
            ('数据结构', '3-4'),
            ('计算机网络', '5-6'),
            ('操作系统', '7-8'),
            ('大学物理', '1-2'),
            ('大学化学', '3-4'),
            ('大学英语', '5-6'),
            ('大学语文', '7-8'),
            ('离散数学', '1-2'),
            ('概率论', '3-4'),
            ('算法设计', '5-6'),
            ('数据库原理', '7-8'),
        ]
        
        semester = '2025-2026-2'
        admin = User.objects.get(username='admin')
        
        count = 0
        for room in rooms[:20]:  # 只为前20个教室创建课表
            for day in range(1, 6):  # 周一到周五
                for _ in range(random.randint(2, 4)):  # 每天2-4节课
                    course_name, period = random.choice(courses)
                    teacher = random.choice(teachers)
                    
                    Schedule.objects.get_or_create(
                        venue=room,
                        day_of_week=day,
                        period=period,
                        semester=semester,
                        defaults={
                            'course_name': course_name,
                            'teacher': teacher.first_name,
                            'start_week': 1,
                            'end_week': 16,
                            'class_name': f'{random.choice(["计科", "软工", "数学", "物理"])}{random.randint(1, 4)}班',
                            'student_count': random.randint(30, 60),
                            'created_by': admin,
                        }
                    )
                    count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  创建 {count} 条固定课表'))
    
    def create_bookings(self):
        self.stdout.write('创建预约数据...')
        
        rooms = list(Room.objects.all())
        users = list(User.objects.filter(role__in=['teacher', 'student']))
        admin = User.objects.get(username='admin')
        
        booking_types = ['teaching', 'meeting', 'activity', 'self_study']
        time_slots = [
            (8, 10), (9, 11), (10, 12),
            (14, 16), (15, 17), (16, 18),
            (19, 21), (20, 22)
        ]
        
        status_weights = [
            ('pending', 15),
            ('approved', 40),
            ('rejected', 15),
            ('cancelled', 10),
            ('completed', 15),
            ('expired', 5),
        ]
        
        count = 0
        approval_count = 0
        
        # 生成过去60天的预约
        for days_ago in range(60, 0, -1):
            date = timezone.now().date() - timedelta(days=days_ago)
            
            # 每天生成8-15个预约
            daily_bookings = random.randint(8, 15)
            
            for _ in range(daily_bookings):
                room = random.choice(rooms)
                user = random.choice(users)
                start_hour, end_hour = random.choice(time_slots)
                
                start_time = timezone.make_aware(datetime.combine(date, datetime.min.time().replace(hour=start_hour)))
                end_time = timezone.make_aware(datetime.combine(date, datetime.min.time().replace(hour=end_hour)))
                
                # 根据日期选择状态
                if days_ago <= 2:
                    status = random.choices([s for s, w in status_weights[:3]], weights=[w for s, w in status_weights[:3]])[0]
                elif days_ago <= 7:
                    status = random.choices([s for s, w in status_weights[:4]], weights=[w for s, w in status_weights[:4]])[0]
                else:
                    status = random.choices([s for s, w in status_weights], weights=[w for s, w in status_weights])[0]
                
                booking_no = f'BK{date.strftime("%Y%m%d")}{count+1:05d}'
                
                booking, created = Booking.objects.get_or_create(
                    booking_no=booking_no,
                    defaults={
                        'venue': room,
                        'user': user,
                        'title': random.choice(['课程教学', '学术会议', '学生活动', '小组讨论', '考试安排', '社团活动', '答辩会议']),
                        'booking_type': random.choice(booking_types),
                        'start_time': start_time,
                        'end_time': end_time,
                        'participant_count': random.randint(10, room.capacity),
                        'status': status,
                        'contact_name': user.first_name,
                        'contact_phone': user.phone or '',
                    }
                )
                
                if created:
                    count += 1
                    
                    # 创建审批记录
                    if status in ['approved', 'rejected']:
                        Approval.objects.create(
                            booking=booking,
                            approver=admin,
                            action='approve' if status == 'approved' else 'reject',
                            comment='同意' if status == 'approved' else '时间冲突'
                        )
                        approval_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  创建 {count} 条预约'))
        self.stdout.write(self.style.SUCCESS(f'  创建 {approval_count} 条审批记录'))
    
    def create_maintenance(self):
        self.stdout.write('创建维修停用数据...')
        
        rooms = list(Room.objects.all())
        admin = User.objects.get(username='admin')
        
        reasons = ['设备维修', '装修改造', '安全检查', '管道维修', '电路检修']
        count = 0
        
        for room in random.sample(rooms, min(10, len(rooms))):
            start_time = timezone.now() + timedelta(days=random.randint(-30, 30))
            end_time = start_time + timedelta(days=random.randint(1, 7))
            
            Maintenance.objects.get_or_create(
                venue=room,
                start_time=start_time,
                defaults={
                    'reason': random.choice(reasons),
                    'end_time': end_time,
                    'status': random.choice(['pending', 'approved', 'ongoing', 'completed']),
                    'approval_status': 'approved',
                    'approved_by': admin,
                    'approved_at': start_time - timedelta(days=1),
                    'created_by': admin,
                }
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  创建 {count} 条维修记录'))
    
    def print_summary(self):
        self.stdout.write('\n数据统计：')
        self.stdout.write(f'  用户总数：{User.objects.count()}')
        self.stdout.write(f'  楼宇总数：{Building.objects.count()}')
        self.stdout.write(f'  场地总数：{Room.objects.count()}')
        self.stdout.write(f'  设备总数：{Equipment.objects.count()}')
        self.stdout.write(f'  预约总数：{Booking.objects.count()}')
        self.stdout.write(f'  审批总数：{Approval.objects.count()}')
        self.stdout.write(f'  课表总数：{Schedule.objects.count()}')
        self.stdout.write(f'  维修总数：{Maintenance.objects.count()}')
