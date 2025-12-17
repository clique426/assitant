from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # 用于媒体文件访问
from score_helper import views  # 导入应用视图

urlpatterns = [
    path('admin/', admin.site.urls),  # 管理员后台（用于管理用户/数据）
    path('', views.login_view, name='login'),  # 首页默认跳转登录
    path('login/', views.login_view, name='login'),  # 登录页路由
    path('captcha/', include('captcha.urls')),  # 验证码路由（必须，否则验证码不显示）
    path('student/', include('score_helper.urls')),  # 学生功能路由（如/student/dashboard）
    path('teacher/', include('score_helper.urls')),  # 老师功能路由（如/teacher/dashboard）
]

# 开发环境下允许访问媒体文件（学生上传的证明）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)