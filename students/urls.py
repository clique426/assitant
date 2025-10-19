from django.urls import path, include
from rest_framework import routers
from django.contrib.auth import views as auth_views
from . import views
from .views import APIRootView, StudentProfileViewSet, SubmissionViewSet, ScoreItemViewSet, register, upload_proof, personal_info, submission_history, custom_login, custom_logout, debug_profile

# 设置应用命名空间
app_name = 'students'

# 注册路由
router = routers.DefaultRouter()
router.register(r'students', StudentProfileViewSet, basename='studentprofile')
router.register(r'score-items', ScoreItemViewSet, basename='scoreitem')
router.register(r'submissions', SubmissionViewSet, basename='submission')

# 定义所有URL模式
urlpatterns = [
    # 首页 - 作为根路径，同时确保不带命名空间时也能找到
    path('', views.home, name='home'),
    # 确保不带命名空间时也能通过'home'找到首页
    path('home/', views.home, name='home'),
    
    # 认证相关
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', register, name='register'),
    
    # 密码重置相关URL
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # 学生功能
    path('personal-info/', personal_info, name='personal-info'),
    path('upload-proof/', upload_proof, name='upload-proof'),
    path('submission-history/', submission_history, name='submission-history'),
    # 调试视图
    path('debug-profile/', debug_profile, name='debug-profile'),
    
    # 直接添加logout路由到students命名空间下，确保/api/students/logout/能正常工作
    path('students/logout/', custom_logout, name='students-logout'),
    # API路由 - 直接包含router.urls，确保api-root能正确访问
    path('', include(router.urls)),
]