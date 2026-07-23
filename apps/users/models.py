from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """自定义用户模型"""
    
    class Role(models.TextChoices):
        STUDENT = 'student', _('学生')
        TEACHER = 'teacher', _('教师')
        ADMIN = 'admin', _('管理员')
    
    role = models.CharField(
        _('角色'),
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('用户角色：学生、教师或管理员')
    )
    
    phone = models.CharField(
        _('联系电话'),
        max_length=20,
        blank=True,
        null=True
    )
    
    department = models.CharField(
        _('院系/部门'),
        max_length=100,
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'users_user'
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        """判断是否为管理员"""
        return self.role == self.Role.ADMIN or self.is_staff
    
    @property
    def is_teacher(self):
        """判断是否为教师"""
        return self.role == self.Role.TEACHER
    
    @property
    def is_student(self):
        """判断是否为学生"""
        return self.role == self.Role.STUDENT
    
    def save(self, *args, **kwargs):
        """保存时自动设置is_staff"""
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)