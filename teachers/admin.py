# teachers/admin.py
from django.contrib import admin
from .models import TeacherProfile  # 导入老师档案模型

# 老师档案管理
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'teacher_id', 'department', 'email', 'phone', 'last_updated')
    search_fields = ('full_name', 'teacher_id', 'department', 'email')
    list_filter = ('department',)
    readonly_fields = ('last_updated',)
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'full_name', 'teacher_id', 'email', 'phone')
        }),
        ('工作信息', {
            'fields': ('department',)
        }),
        ('时间信息', {
            'fields': ('last_updated',)
        })
    )
    # 添加中文名称
    verbose_name = '教师档案'
    verbose_name_plural = '教师档案'