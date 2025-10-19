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
    if created and hasattr(instance, 'teacher_profile') and instance.teacher_profile is not None:
        # 添加到老师组并设为staff
        teacher_group, _ = Group.objects.get_or_create(name='teachers')
        instance.groups.add(teacher_group)
        instance.is_staff = True
        instance.save()