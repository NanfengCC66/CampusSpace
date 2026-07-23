"""
测试登录功能
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import authenticate
from apps.users.models import User

def test_login():
    """测试登录功能"""
    
    print("=" * 60)
    print("CampusSpace 登录功能测试")
    print("=" * 60)
    print()
    
    # 测试账号
    test_accounts = [
        ('admin', 'admin123', '管理员'),
        ('teacher_zhang', 'teacher123', '教师'),
        ('student001', 'student123', '学生'),
    ]
    
    print("【测试账号信息】")
    print()
    for username, password, role in test_accounts:
        print(f"  {role}: {username} / {password}")
    print()
    print("=" * 60)
    print()
    
    # 测试登录
    print("【登录测试结果】")
    print()
    
    for username, password, role in test_accounts:
        # 检查用户是否存在
        try:
            user = User.objects.get(username=username)
            print(f"✅ {role}用户存在: {username}")
            print(f"   - 姓名: {user.first_name}")
            print(f"   - 角色: {user.role}")
            print(f"   - 邮箱: {user.email}")
        except User.DoesNotExist:
            print(f"❌ {role}用户不存在: {username}")
            continue
        
        # 测试密码验证
        if user.check_password(password):
            print(f"✅ 密码验证成功")
        else:
            print(f"❌ 密码验证失败")
            continue
        
        # 测试认证
        authenticated_user = authenticate(username=username, password=password)
        if authenticated_user:
            print(f"✅ 认证成功: {authenticated_user.username}")
        else:
            print(f"❌ 认证失败")
        
        print()
    
    print("=" * 60)
    print()
    
    # 显示所有用户
    print("【所有用户列表】")
    print()
    users = User.objects.all().order_by('role', 'username')
    
    current_role = None
    for user in users:
        if user.role != current_role:
            current_role = user.role
            role_names = {'admin': '管理员', 'teacher': '教师', 'student': '学生'}
            print(f"\n{role_names.get(current_role, current_role)}:")
        
        print(f"  - {user.username} ({user.first_name})")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    test_login()