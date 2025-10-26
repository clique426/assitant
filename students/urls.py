from django.urls import path, include
from django.http import HttpResponse
from rest_framework import routers
from django.contrib.auth import views as auth_views
from . import views
from .views import APIRootView, StudentProfileViewSet, SubmissionViewSet, ScoreItemViewSet, register, upload_proof, personal_info, submission_history, custom_login, custom_logout, debug_profile, submission_revoke, submission_approve, submission_reject, student_detail
# from .views_debug import debug_student_data, debug_submission_data
# from .debug_all_students import debug_all_students
# from .simple_views import simple_student_list
# from .debug_template import debug_template
# from .json_debug_view import json_debug_students
# from .simple_html_view import simple_html_students

# 设置应用命名空间
app_name = 'students'

# 注册路由
router = routers.DefaultRouter()
router.register(r'students', StudentProfileViewSet, basename='studentprofile')
router.register(r'score-items', ScoreItemViewSet, basename='scoreitem')
router.register(r'submissions', SubmissionViewSet, basename='submission')

# 定义所有URL模式
urlpatterns = [
    # API路由 - 首先包含router.urls，确保命名空间视图能正确解析
    path('', include(router.urls)),
    
    # 首页 - 作为根路径，同时确保不带命名空间时也能找到
    path('', views.home, name='home'),
    # 确保不带命名空间时也能通过'home'找到首页
    path('home/', views.home, name='home'),
    
    # 认证相关 - 移到其他路由之前，避免与API路由冲突
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
    # 提交操作
    path('submission-revoke/<int:pk>/', submission_revoke, name='submission-revoke'),
    path('submission-approve/<int:pk>/', submission_approve, name='submission-approve'),
    path('submission-reject/<int:pk>/', submission_reject, name='submission-reject'),
    # 调试视图
    path('debug-profile/', debug_profile, name='debug-profile'),
    # 学生详情页面
    path('student-detail/<int:pk>/', student_detail, name='student-detail'),
    # 编辑学生信息页面
    path('edit-student-info/<int:student_id>/', views.edit_student_info, name='edit-student-info'),
    
    # 直接添加logout路由到students命名空间下，确保/api/students/logout/能正常工作
    path('students/logout/', custom_logout, name='students-logout'),
]