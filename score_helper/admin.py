from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AcademicScore, PerformanceScore, ScoreApplication, ScoreClause

# 注册自定义用户模型（让管理员后台显示“用户”菜单）
class CustomUserAdmin(UserAdmin):
    # 后台列表页显示的字段
    list_display = ('username', 'role', 'student_id', 'teacher_id', 'is_active')
    # 编辑页的字段分组
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('角色与身份', {'fields': ('role', 'student_id', 'teacher_id')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

# 注册所有模型（让后台显示这些菜单）
admin.site.register(User, CustomUserAdmin)
admin.site.register(AcademicScore)
admin.site.register(PerformanceScore)
admin.site.register(ScoreApplication)
admin.site.register(ScoreClause)