from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.venues.models import Building, Room, Equipment, RoomEquipment

User = get_user_model()


class Command(BaseCommand):
    help = '初始化演示数据'
    
    def handle(self, *args, **options):
        self.stdout.write('开始初始化演示数据...')
        
        # 创建用户
        self.stdout.write('创建用户...')
        users_data = [
            {
                'username': 'admin',
                'password': 'admin123',
                'email': 'admin@campus.edu',
                'first_name': '系统管理员',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'teacher',
                'password': 'teacher123',
                'email': 'teacher@campus.edu',
                'first_name': '张老师',
                'role': 'teacher',
                'department': '计算机学院',
                'phone': '13800138000',
            },
            {
                'username': 'student',
                'password': 'student123',
                'email': 'student@campus.edu',
                'first_name': '李同学',
                'role': 'student',
                'department': '计算机学院',
                'phone': '13900139000',
            },
        ]
        
        for user_data in users_data:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  创建用户: {user.username}'))
            else:
                self.stdout.write(f'  用户已存在: {user.username}')
        
        # 创建楼宇
        self.stdout.write('创建楼宇...')
        buildings_data = [
            {'name': '教学楼A', 'location': '校园东区', 'total_floors': 6, 'description': '主要教学楼，配备现代化教学设施'},
            {'name': '教学楼B', 'location': '校园东区', 'total_floors': 5, 'description': '理工科教学楼'},
            {'name': '实验楼', 'location': '校园北区', 'total_floors': 4, 'description': '实验室和科研场所'},
            {'name': '行政楼', 'location': '校园中心区', 'total_floors': 3, 'description': '行政办公和会议室'},
        ]
        
        for building_data in buildings_data:
            building, created = Building.objects.get_or_create(
                name=building_data['name'],
                defaults=building_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  创建楼宇: {building.name}'))
            else:
                self.stdout.write(f'  楼宇已存在: {building.name}')
        
        # 创建设备类型
        self.stdout.write('创建设备类型...')
        equipments_data = [
            {'name': '投影仪', 'code': 'projector', 'category': '教学设备'},
            {'name': '空调', 'code': 'air_conditioner', 'category': '环境设备'},
            {'name': '电脑', 'code': 'computer', 'category': '计算设备'},
            {'name': '白板', 'code': 'whiteboard', 'category': '教学设备'},
            {'name': '音响', 'code': 'speaker', 'category': '音响设备'},
            {'name': '麦克风', 'code': 'microphone', 'category': '音响设备'},
        ]
        
        for equip_data in equipments_data:
            equipment, created = Equipment.objects.get_or_create(
                name=equip_data['name'],
                defaults=equip_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  创建设备: {equipment.name}'))
            else:
                self.stdout.write(f'  设备已存在: {equipment.name}')
        
        # 创建场地
        self.stdout.write('创建场地...')
        admin_user = User.objects.get(username='admin')
        
        rooms_data = [
            # 教学楼A
            {'name': 'A101教室', 'building': '教学楼A', 'floor': 1, 'room_number': '101', 
             'venue_type': 'classroom', 'capacity': 60, 'area': 100, 'manager': '王老师', 'manager_phone': '13800000001'},
            {'name': 'A201教室', 'building': '教学楼A', 'floor': 2, 'room_number': '201', 
             'venue_type': 'classroom', 'capacity': 80, 'area': 120, 'manager': '李老师', 'manager_phone': '13800000002'},
            {'name': 'A301教室', 'building': '教学楼A', 'floor': 3, 'room_number': '301', 
             'venue_type': 'classroom', 'capacity': 100, 'area': 150, 'manager': '张老师', 'manager_phone': '13800000003'},
            {'name': 'A401会议室', 'building': '教学楼A', 'floor': 4, 'room_number': '401', 
             'venue_type': 'meeting_room', 'capacity': 30, 'area': 60, 'manager': '赵老师', 'manager_phone': '13800000004'},
            
            # 教学楼B
            {'name': 'B101教室', 'building': '教学楼B', 'floor': 1, 'room_number': '101', 
             'venue_type': 'classroom', 'capacity': 50, 'area': 80, 'manager': '刘老师', 'manager_phone': '13800000005'},
            {'name': 'B201教室', 'building': '教学楼B', 'floor': 2, 'room_number': '201', 
             'venue_type': 'classroom', 'capacity': 70, 'area': 100, 'manager': '陈老师', 'manager_phone': '13800000006'},
            
            # 实验楼
            {'name': '计算机实验室1', 'building': '实验楼', 'floor': 1, 'room_number': '101', 
             'venue_type': 'lab', 'capacity': 40, 'area': 120, 'manager': '周老师', 'manager_phone': '13800000007'},
            {'name': '物理实验室', 'building': '实验楼', 'floor': 2, 'room_number': '201', 
             'venue_type': 'lab', 'capacity': 30, 'area': 100, 'manager': '吴老师', 'manager_phone': '13800000008'},
            
            # 行政楼
            {'name': '第一会议室', 'building': '行政楼', 'floor': 1, 'room_number': '101', 
             'venue_type': 'meeting_room', 'capacity': 50, 'area': 80, 'manager': '郑老师', 'manager_phone': '13800000009'},
            {'name': '报告厅', 'building': '行政楼', 'floor': 2, 'room_number': '201', 
             'venue_type': 'activity_room', 'capacity': 200, 'area': 300, 'manager': '孙老师', 'manager_phone': '13800000010'},
        ]
        
        for room_data in rooms_data:
            building_name = room_data.pop('building')
            building = Building.objects.get(name=building_name)
            room, created = Room.objects.get_or_create(
                name=room_data['name'],
                building=building,
                defaults={**room_data, 'created_by': admin_user}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  创建场地: {room.name}'))
            else:
                self.stdout.write(f'  场地已存在: {room.name}')
        
        # 为部分场地添加设备
        self.stdout.write('为场地添加设备...')
        projector = Equipment.objects.get(name='投影仪')
        air_conditioner = Equipment.objects.get(name='空调')
        computer = Equipment.objects.get(name='电脑')
        whiteboard = Equipment.objects.get(name='白板')
        
        # 为所有场地添加基础设备
        for room in Room.objects.all():
            # 投影仪
            RoomEquipment.objects.get_or_create(
                room=room, equipment=projector,
                defaults={'quantity': 1, 'status': 'normal'}
            )
            # 空调
            RoomEquipment.objects.get_or_create(
                room=room, equipment=air_conditioner,
                defaults={'quantity': 2, 'status': 'normal'}
            )
            # 白板
            RoomEquipment.objects.get_or_create(
                room=room, equipment=whiteboard,
                defaults={'quantity': 1, 'status': 'normal'}
            )
        
        # 为实验室添加电脑
        for room in Room.objects.filter(venue_type='lab'):
            RoomEquipment.objects.get_or_create(
                room=room, equipment=computer,
                defaults={'quantity': 40, 'status': 'normal'}
            )
        
        self.stdout.write(self.style.SUCCESS('\n演示数据初始化完成！'))
        self.stdout.write('\n演示账号：')
        self.stdout.write('  管理员: admin / admin123')
        self.stdout.write('  教师: teacher / teacher123')
        self.stdout.write('  学生: student / student123')