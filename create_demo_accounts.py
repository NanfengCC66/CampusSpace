"""
创建简化演示账号
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("创建简化演示账号")
print("=" * 60)
print()

# 创建teacher用户
if not User.objects.filter(username='teacher').exists():
    teacher = User.objects.create_user(
        username='teacher',
        email='teacher@campus.edu',
        first_name='教师',
        role='teacher',
        department='计算机学院'
    )
    teacher.set_password('teacher123')
    teacher.save()
    print('✅ 创建 teacher 用户成功')
    print(f'   用户名: teacher')
    print(f'   密码: teacher123')
    print(f'   角色: 教师')
else:
    print('⚠️  teacher 用户已存在')

print()

# 创建student用户
if not User.objects.filter(username='student').exists():
    student = User.objects.create_user(
        username='student',
        email='student@campus.edu',
        first_name='学生',
        role='student',
        department='计算机学院'
    )
    student.set_password('student123')
    student.save()
    print('✅ 创建 student 用户成功')
    print(f'   用户名: student')
    print(f'   密码: student123')
    print(f'   角色: 学生')
else:
    print('⚠️  student 用户已存在')

print()
print("=" * 60)
print()
print("演示账号信息")
print("=" * 60)
print()
print("管理员: admin / admin123")
print("教师: teacher / teacher123")
print("学生: student / student123")
print()
print("=" * 60)