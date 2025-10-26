from django.db import models
from django.contrib.auth.models import User, Group  # 导入Group用于权限管理
from django.db.models.signals import post_save
from django.dispatch import receiver

# 学生档案模型（增强版）
class StudentProfile(models.Model):
    user = models.OneToOneField(User, verbose_name="用户", on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField("真实姓名", max_length=100)
    student_id = models.CharField("学号", max_length=20, unique=True, default="000000")
    major = models.CharField("专业", max_length=50, default="未填写")
    grade = models.CharField("年级", max_length=20, default="2023级")
    class_name = models.CharField("班级", max_length=20, default="未填写")  # 新增班级字段
    email = models.EmailField("邮箱", max_length=100, blank=True)  # 新增邮箱字段
    phone = models.CharField("联系电话", max_length=20, blank=True)  # 新增电话字段
    total_score = models.FloatField("总加分", default=0)
    last_updated = models.DateTimeField("最后更新时间", auto_now=True)  # 新增更新时间

    def __str__(self):
        return f"{self.full_name}（{self.student_id} - {self.major}）"
    
    class Meta:
        verbose_name = '学生档案'
        verbose_name_plural = '学生档案'
    
    def save(self, *args, **kwargs):
        # 标记是否是新对象（之前没有主键）
        is_new = self.pk is None
        
        # 先调用父类的save方法保存对象到数据库
        super().save(*args, **kwargs)
        
        # 只有当对象已有主键时才计算总加分（已保存到数据库）
        if not is_new:
            approved_submissions = self.submissions.filter(status='approved')
            self.total_score = sum(sub.score_item.score for sub in approved_submissions)
            # 再次保存，但不触发递归
            super().save(update_fields=['total_score'])

# 加分项目模型（新增，只定义一次）
class ScoreItem(models.Model):
    CATEGORY_CHOICES = [
        ('competition', '竞赛'),
        ('thesis', '论文'),
        ('patent', '专利'),
        ('scholarship', '奖学金'),
        ('other', '其他'),
    ]
    name = models.CharField("项目名称", max_length=100)
    category = models.CharField("类别", max_length=20, choices=CATEGORY_CHOICES)
    level = models.CharField("级别", max_length=50)
    score = models.FloatField("对应分值")
    description = models.TextField("项目说明", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.category} - {self.level}（{self.score}分）"
    
    class Meta:
        verbose_name = '加分项目'
        verbose_name_plural = '加分项目'



# 信号处理函数：创建用户后自动添加到学生组
@receiver(post_save, sender=User)
def add_user_to_student_group(sender, instance, created, **kwargs):
    # 确保超级管理员账号不会被添加到学生组
    # 修改：只使用hasattr检查，不直接访问profile属性避免递归
    if created and hasattr(instance, 'profile') and not instance.is_superuser:
        # 使用try-except避免可能的异常
        try:
            # 延迟访问profile属性，避免信号处理时的递归问题
            # 或者更好的方法是直接通过StudentProfile查询
            if StudentProfile.objects.filter(user=instance).exists():
                # 添加到学生组
                student_group, _ = Group.objects.get_or_create(name='students')
                instance.groups.add(student_group)
        except Exception:
            # 如果出现问题，静默失败，避免影响用户创建
            pass

# 提交记录模型（增强版）
class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '审核通过'),
        ('rejected', '审核拒绝'),
        ('revoked', '已撤回'),
    ]
    student = models.ForeignKey(StudentProfile, verbose_name="学生", on_delete=models.CASCADE, related_name='submissions')
    score_item = models.ForeignKey(ScoreItem, verbose_name="加分项目", on_delete=models.CASCADE)
    proof_file = models.FileField("证明文件", upload_to='proofs/')
    additional_info = models.TextField("补充说明", blank=True)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField("提交时间", auto_now_add=True)
    reviewed_at = models.DateTimeField("审核时间", null=True, blank=True)
    reviewer = models.ForeignKey(User, verbose_name="审核人", on_delete=models.SET_NULL, null=True, blank=True)  # 确保引用User模型，以便与TeacherProfile关联
    reviewer_comment = models.TextField("审核意见", blank=True, null=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.score_item.name}（{self.get_status_display()}）"

    class Meta:
        verbose_name = '提交记录'
        verbose_name_plural = '提交记录'
        ordering = ['-submitted_at']  # 默认按提交时间降序排列


class StudentInfoChangeLog(models.Model):
    """
    学生信息变更日志模型，记录学生信息的编辑历史
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='info_change_logs')
    editor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_info_edits')
    field_name = models.CharField(max_length=50, verbose_name='修改字段')
    old_value = models.TextField(blank=True, null=True, verbose_name='修改前值')
    new_value = models.TextField(blank=True, null=True, verbose_name='修改后值')
    change_time = models.DateTimeField(auto_now_add=True, verbose_name='修改时间')
    
    def __str__(self):
        return f'{self.editor.username} 修改 {self.student.user.username} 的 {self.field_name} 字段'
    
    class Meta:
        verbose_name = '学生信息变更日志'
        verbose_name_plural = '学生信息变更日志'
        ordering = ['-change_time']