from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', _('学生')
        TEACHER = 'TEACHER', _('老师')
        ADMIN = 'ADMIN', _('管理员')

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name="用户角色"
    )
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="学号")
    teacher_id = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="教职工号")
    rank_visible = models.BooleanField(default=False, verbose_name="排名显示开关")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def is_student(self):
        return self.role == self.Role.STUDENT

    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return f"{self.username}（{self.get_role_display()}）"


class AcademicScore(models.Model):
    application = models.ForeignKey(
        'ScoreApplication', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='academic_score',
        verbose_name="关联申请"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="academic_scores", verbose_name="关联学生")
    SCORE_TYPE = [("competition", "学业竞赛"), ("paper", "学术论文"), ("patent", "国家专利"),
                  ("innovation", "创新创业项目")]
    score_type = models.CharField("加分类型", max_length=20, choices=SCORE_TYPE)
    competition_level = models.CharField("竞赛级别", max_length=20,
                                         choices=[("national_a_plus", "国家级A+类"), ("national_a", "国家级A类"),
                                                  ("national_a_minus", "国家级A-类"), ("provincial_a", "省级A类")],
                                         blank=True, null=True)
    competition_rank = models.CharField("获奖等级", max_length=10,
                                        choices=[("first", "一等奖及以上"), ("second", "二等奖"), ("third", "三等奖")],
                                        blank=True, null=True)
    is_group = models.BooleanField("是否团体项目", default=False)
    PAPER_AUTHOR = [("independent", "独立作者"), ("first", "第一作者/队长"), ("second", "第二作者/队员")]
    group_role = models.CharField("团体角色", max_length=15, choices=PAPER_AUTHOR, blank=True, null=True)
    paper_level = models.CharField("论文级别", max_length=10,
                                   choices=[("a", "A类期刊/会议"), ("b", "B类期刊/会议"), ("c", "C类期刊/会议")],
                                   blank=True, null=True)
    paper_author = models.CharField("作者排名", max_length=15, choices=PAPER_AUTHOR, blank=True, null=True)
    remark = models.CharField("备注", max_length=200, blank=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}的{self.get_score_type_display()}加分"

    def calculate_score(self):
        score = 0
        if self.score_type == "competition" and self.competition_level and self.competition_rank:
            competition_score_map = {
                ("national_a_plus", "first"): 30, ("national_a_plus", "second"): 15,
                ("national_a_plus", "third"): 10, ("national_a", "first"): 15,
                ("national_a", "second"): 10, ("national_a", "third"): 5,
                ("national_a_minus", "first"): 10, ("national_a_minus", "second"): 5,
                ("national_a_minus", "third"): 2, ("provincial_a", "first"): 5,
                ("provincial_a", "second"): 2
            }
            base_score = competition_score_map.get((self.competition_level, self.competition_rank), 0)
            if self.is_group:
                if self.group_role == "first":
                    score = base_score * (1 / 3)
                elif self.group_role == "second":
                    score = base_score * (1 / 4)
                else:
                    score = base_score * (1 / 5)
            else:
                score = base_score * (1 / 3)
            return round(min(score, 15), 2)
        elif self.score_type == "paper" and self.paper_level and self.paper_author:
            paper_base_map = {"a": 10, "b": 6, "c": 1}
            base_score = paper_base_map[self.paper_level]
            author_ratio_map = {"independent": 1.0, "first": 0.8, "second": 0.2}
            score = base_score * author_ratio_map[self.paper_author]
            return round(min(score, 15), 2)
        elif self.score_type == "patent":
            return round(min(2 * 0.8, 15), 2)
        elif self.score_type == "innovation":
            return round(min(1.0, 15), 2)
        return 0


class PerformanceScore(models.Model):
    application = models.ForeignKey(
        'ScoreApplication', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='performance_score',
        verbose_name="关联申请"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="performance_scores", verbose_name="关联学生")
    SCORE_TYPE = [("volunteer", "志愿服务"), ("cadre", "学生干部"), ("honor", "荣誉称号")]
    score_type = models.CharField("加分类型", max_length=20, choices=SCORE_TYPE)
    volunteer_hours = models.FloatField("志愿服务时长（小时）", default=0, blank=True, null=True)
    is_large_event = models.BooleanField("是否大型赛会/支教（工时减半）", default=False)
    CADRE_ROLE = [("monitor", "班长/团支书"), ("minister", "院学生会部长"), ("member", "班委/委员")]
    cadre_role = models.CharField("职务", max_length=20, choices=CADRE_ROLE, blank=True, null=True)
    cadre_score = models.IntegerField("辅导员打分（0-100）", default=0, blank=True, null=True)
    HONOR_LEVEL = [("national", "国家级"), ("provincial", "省级"), ("school", "校级")]
    honor_level = models.CharField("荣誉级别", max_length=20, choices=HONOR_LEVEL, blank=True, null=True)
    remark = models.CharField("备注", max_length=200, blank=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}的{self.get_score_type_display()}加分"

    def calculate_score(self):
        score = 0
        if self.score_type == "volunteer" and self.volunteer_hours:
            actual_hours = self.volunteer_hours / 2 if self.is_large_event else self.volunteer_hours
            if actual_hours >= 200:
                extra = ((actual_hours - 200) / 2) * 0.05
                score = 1 + extra
            score = min(score, 1)
        elif self.score_type == "cadre" and self.cadre_role and self.cadre_score:
            cadre_coefficient_map = {"monitor": 1.0, "minister": 0.75, "member": 0.5}
            coefficient = cadre_coefficient_map[self.cadre_role]
            score = coefficient * (self.cadre_score / 100)
            score = min(score, 2)
        elif self.score_type == "honor" and self.honor_level:
            honor_score_map = {"national": 2, "provincial": 1, "school": 0.2}
            score = honor_score_map[self.honor_level]
        return round(score, 2)


class ScoreApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('待审批')
        APPROVED = 'APPROVED', _('已通过')
        REJECTED = 'REJECTED', _('已驳回')

    APPLY_TYPE = [("academic", "学业加分"), ("performance", "表现加分")]
    apply_type = models.CharField("申请类型", max_length=20, choices=APPLY_TYPE)

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='applications',
        limit_choices_to={'role': User.Role.STUDENT}, verbose_name="申请人"
    )
    self_score = models.FloatField(verbose_name="自评分数")
    score_item = models.CharField(max_length=200, verbose_name="加分项目详情")
    proof_file = models.FileField(upload_to='proofs/%Y/%m/%d/', verbose_name="证明文件（图片/文档）")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, verbose_name="审批状态")
    approved_score = models.FloatField(null=True, blank=True, verbose_name="审批通过分数")
    reject_reason = models.TextField(null=True, blank=True, verbose_name="驳回理由")
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_applications', verbose_name="审批人"
    )
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "加分申请"
        verbose_name_plural = "加分申请"
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.student.username}的{self.get_apply_type_display()}申请（{self.get_status_display()}）"


# 新增：补充缺失的 ScoreRecord 模型（用于记录最终通过的加分）
class ScoreRecord(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='score_records',
        limit_choices_to={'role': User.Role.STUDENT}, verbose_name="学生"
    )
    application = models.OneToOneField(
        ScoreApplication, on_delete=models.CASCADE, related_name='score_record',
        verbose_name="关联申请"
    )
    type = models.CharField(
        max_length=20, choices=ScoreApplication.APPLY_TYPE,
        verbose_name="加分类型"  # 与申请类型保持一致
    )
    score = models.FloatField(verbose_name="最终加分值")  # 即审批通过的分数
    created_time = models.DateTimeField(default=timezone.now, verbose_name="记录时间")

    class Meta:
        verbose_name = "加分记录"
        verbose_name_plural = "加分记录"
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.student.username}的{self.get_type_display()}记录（{self.score}分）"


class ScoreClause(models.Model):
    category = models.CharField(max_length=100, verbose_name="条款类别")
    content = models.TextField(verbose_name="条款内容")
    score_range = models.CharField(max_length=50, verbose_name="加分范围")
    sort_order = models.IntegerField(default=0, verbose_name="排序号")

    class Meta:
        verbose_name = "加分条款"
        verbose_name_plural = "加分条款"
        ordering = ['category', 'sort_order']

    def __str__(self):
        return f"{self.category}：{self.content[:20]}..."