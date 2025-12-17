from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

# 老师档案模型
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    full_name = models.CharField("真实姓名", max_length=100)
    teacher_id = models.CharField("工号", max_length=20, unique=True, default="000000")
    department = models.CharField("部门", max_length=50, default="未填写")
    email = models.EmailField("邮箱", max_length=100, blank=True)
    phone = models.CharField("联系电话", max_length=20, blank=True)
    last_updated = models.DateTimeField("最后更新时间", auto_now=True)

    def __str__(self):
        return f"{self.full_name}（{self.teacher_id} - {self.department}）"

# 信号处理函数：创建用户后自动添加到老师组
@receiver(post_save, sender=User)
def add_user_to_teacher_group(sender, instance, created, **kwargs):
    # 防止无限递归：检查是否已经在处理中
    if hasattr(instance, '_adding_to_group'):
        return
    
    try:
        # 标记为正在处理中
        instance._adding_to_group = True
        
        # 超级管理员账号处理
        if instance.is_superuser:
            # 添加到老师组并设为staff
            teacher_group, _ = Group.objects.get_or_create(name='teachers')
            # 只在需要时添加到组
            if not instance.groups.filter(name='teachers').exists():
                instance.groups.add(teacher_group)
            # 只在需要时设置is_staff
            if not instance.is_staff:
                instance.is_staff = True
                # 注意：这里不再调用instance.save()，避免触发递归
        # 对于普通用户
        elif created:
            try:
                # 通过TeacherProfile查询而不是直接访问属性
                if TeacherProfile.objects.filter(user=instance).exists():
                    # 添加到老师组并设为staff
                    teacher_group, _ = Group.objects.get_or_create(name='teachers')
                    if not instance.groups.filter(name='teachers').exists():
                        instance.groups.add(teacher_group)
                    if not instance.is_staff:
                        instance.is_staff = True
                        # 注意：这里不再调用instance.save()，避免触发递归
            except Exception:
                # 如果出现问题，静默失败
                pass
    finally:
        # 确保移除标记
        if hasattr(instance, '_adding_to_group'):
            del instance._adding_to_group