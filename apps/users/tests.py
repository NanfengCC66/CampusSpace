"""
CampusSpace 项目测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.venues.models import Building, Room, Equipment

User = get_user_model()


class UserModelTest(TestCase):
    """用户模型测试"""
    
    def test_create_student(self):
        """测试创建学生用户"""
        user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='test123',
            role='student'
        )
        self.assertEqual(user.role, 'student')
        self.assertTrue(user.is_student)
        self.assertFalse(user.is_teacher)
        self.assertFalse(user.is_admin)
    
    def test_create_teacher(self):
        """测试创建教师用户"""
        user = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='test123',
            role='teacher'
        )
        self.assertEqual(user.role, 'teacher')
        self.assertFalse(user.is_student)
        self.assertTrue(user.is_teacher)
        self.assertFalse(user.is_admin)
    
    def test_create_admin(self):
        """测试创建管理员用户"""
        user = User.objects.create_user(
            username='test_admin',
            email='admin@test.com',
            password='test123',
            role='admin'
        )
        self.assertEqual(user.role, 'admin')
        self.assertFalse(user.is_student)
        self.assertFalse(user.is_teacher)
        self.assertTrue(user.is_admin)
        self.assertTrue(user.is_staff)  # 管理员自动设置为staff


class BuildingModelTest(TestCase):
    """楼宇模型测试"""
    
    def test_create_building(self):
        """测试创建楼宇"""
        building = Building.objects.create(
            name='测试楼宇',
            location='测试位置',
            total_floors=5
        )
        self.assertEqual(building.name, '测试楼宇')
        self.assertEqual(building.total_floors, 5)
        self.assertEqual(building.room_count, 0)
    
    def test_building_str(self):
        """测试楼宇字符串表示"""
        building = Building.objects.create(name='测试楼宇')
        self.assertEqual(str(building), '测试楼宇')


class RoomModelTest(TestCase):
    """场地模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.building = Building.objects.create(
            name='测试楼宇',
            total_floors=5
        )
        self.user = User.objects.create_user(
            username='test_user',
            password='test123'
        )
    
    def test_create_room(self):
        """测试创建场地"""
        room = Room.objects.create(
            name='测试教室',
            venue_type='classroom',
            building=self.building,
            floor=1,
            room_number='101',
            capacity=60,
            created_by=self.user
        )
        self.assertEqual(room.name, '测试教室')
        self.assertEqual(room.capacity, 60)
        self.assertTrue(room.is_available)
    
    def test_room_full_name(self):
        """测试场地完整名称"""
        room = Room.objects.create(
            name='测试教室',
            building=self.building,
            floor=2,
            room_number='201',
            capacity=60
        )
        self.assertEqual(room.full_name, '测试楼宇-2楼-201')


class EquipmentModelTest(TestCase):
    """设备模型测试"""
    
    def test_create_equipment(self):
        """测试创建设备"""
        equipment = Equipment.objects.create(
            name='测试设备',
            code='test_equip',
            category='测试分类'
        )
        self.assertEqual(equipment.name, '测试设备')
        self.assertEqual(equipment.code, 'test_equip')
    
    def test_equipment_str(self):
        """测试设备字符串表示"""
        equipment = Equipment.objects.create(name='测试设备')
        self.assertEqual(str(equipment), '测试设备')