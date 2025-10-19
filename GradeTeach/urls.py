from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt

# 临时视图函数处理提交撤回
@csrf_exempt
def submission_revoke(request, submission_id):
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect('/submission-history/')

# 从students应用导入视图函数
from students.views import home, custom_logout, personal_info, upload_proof, submission_history, debug_profile

# 根URL配置 - 简化版本
urlpatterns = [
    # 首页 - 最基本的配置
    path('', home, name='home'),
    path('home/', home, name='home'),
    
    # 基本认证URL - 直接使用自定义的logout视图
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),  # 直接使用自定义登出视图
    
    # 管理后台
    path('admin/', admin.site.urls),
    
    # 添加students应用的URLs，这样API路由和其他路由才能正确工作
    path('api/', include('students.urls')),
    
    # 添加基本视图的URL映射
    path('personal-info/', personal_info, name='personal-info'),
    path('submission-history/', submission_history, name='submission-history'),
    path('studentprofile-list/', TemplateView.as_view(template_name='students/student_list.html'), name='studentprofile-list'),
    path('submission-list/', TemplateView.as_view(template_name='students/submission_list.html'), name='submission-list'),
    path('scoreitem-list/', TemplateView.as_view(template_name='students/score_item_list.html'), name='scoreitem-list'),
    path('upload-proof/', upload_proof, name='upload-proof'),
    path('debug-profile/', debug_profile, name='debug-profile'),
    path('submission-revoke/<int:submission_id>/', submission_revoke, name='submission-revoke'),
]

# 处理静态文件和媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)