# students/admin.py
from django.contrib import admin
from .models import StudentProfile, Submission, ScoreItem  # 导入你的模型


# 学生档案管理
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'student_id', 'major', 'grade', 'class_name', 'email', 'phone', 'total_score', 'last_updated')
    search_fields = ('full_name', 'student_id', 'major', 'class_name', 'email')
    list_filter = ('major', 'grade', 'class_name')
    ordering = ('-total_score',)  # 按总加分降序
    readonly_fields = ('total_score', 'last_updated')
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'full_name', 'student_id', 'email', 'phone')
        }),
        ('学业信息', {
            'fields': ('major', 'grade', 'class_name', 'admission_date')
        }),
        ('加分信息', {
            'fields': ('total_score', 'last_updated')
        })
    )
    # 添加中文名称
    verbose_name = '学生档案'
    verbose_name_plural = '学生档案'

# 加分项目管理（新增）
@admin.register(ScoreItem)
class ScoreItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'level', 'score', 'created_at')
    list_filter = ('category', 'level')
    search_fields = ('name', 'description')
    # 添加中文名称
    verbose_name = '加分项目'
    verbose_name_plural = '加分项目'

# 提交记录管理（增强版）
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'student', 
        'score_item',
        'status',
        'submitted_at',
        'reviewed_at',
        'reviewer'
    )
    list_filter = ('status', 'submitted_at', 'reviewed_at', 'score_item__category', 'reviewer')
    search_fields = ('student__full_name', 'student__student_id', 'score_item__name', 'reviewer_comment', 'additional_info')
    readonly_fields = ('submitted_at', 'reviewed_at')
    ordering = ('-submitted_at',)
    actions = ['approve_submissions', 'reject_submissions']
    # 添加中文名称
    verbose_name = '提交记录'
    verbose_name_plural = '提交记录'
    
    # 批量审核通过
    def approve_submissions(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='approved', 
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
        # 重新计算相关学生的总分
        for submission in queryset.filter(status='approved'):
            submission.student.save()
        self.message_user(request, f"已成功批准 {updated} 条申请")
    approve_submissions.short_description = "批量批准所选申请"
    
    # 批量审核驳回
    def reject_submissions(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='rejected', 
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"已成功驳回 {updated} 条申请")
    reject_submissions.short_description = "批量驳回所选申请"
    
    fieldsets = (
        ('申请信息', {
            'fields': ('student', 'score_item', 'additional_info', 'proof_file')
        }),
        ('审核信息', {
            'fields': ('status', 'reviewer_comment', 'reviewer')
        }),
        ('时间信息', {
            'fields': ('submitted_at', 'reviewed_at')
        })
    )