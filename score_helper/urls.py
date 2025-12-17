from django.urls import path
from . import views

urlpatterns = [
    # 登录/退出
    path('logout/', views.logout_view, name='logout'),

    # 学生功能
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('apply/', views.student_apply, name='submit_application'),

    # 老师功能
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('approve/<int:app_id>/', views.approve_application, name='approve_application'),
    path('revoke/<int:app_id>/', views.revoke_application, name='revoke_application'),
]