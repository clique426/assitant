# users/admin.py
from django.contrib import admin
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.contenttypes.models import ContentType

# 自定义UserAdmin，增强用户管理功能
class UserAdmin(DefaultUserAdmin):
    # 添加自定义列表显示字段
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'last_login')
    # 添加用户类型过滤器
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    # 增强搜索功能
    search_fields = ('username', 'first_name', 'last_name', 'email')
    # 调整编辑表单布局
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('权限', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    # 调整添加用户表单
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    # 添加中文名称
    verbose_name = '用户管理'
    verbose_name_plural = '用户管理'

# 自定义GroupAdmin，增强权限组管理
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'permissions_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    # 添加权限数量统计
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = '权限数量'
    
    # 添加中文名称
    verbose_name = '权限组'
    verbose_name_plural = '权限组管理'

# 注册自定义管理类
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

# 注册ContentType和Permission模型，方便管理员查看和管理权限
@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ('app_label', 'model', 'name')
    search_fields = ('app_label', 'model', 'name')
    list_filter = ('app_label',)
    verbose_name = '内容类型'
    verbose_name_plural = '内容类型管理'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'codename')
    search_fields = ('name', 'codename', 'content_type__model')
    list_filter = ('content_type',)
    verbose_name = '权限管理'
    verbose_name_plural = '权限管理'