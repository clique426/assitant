from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
# 导入需要的模型
from students.models import StudentProfile



# 从students应用导入视图函数
from students.views import home, custom_logout, custom_login, personal_info, upload_proof, submission_history, debug_profile, APIRootView, SubmissionViewSet, ScoreItemViewSet, submission_approve, submission_reject, submission_revoke, submission_detail
from students.views import StudentProfileViewSet
# 注释掉不存在的模块导入
# from students.views_debug import debug_student_data
# 注释掉不存在的模块导入
# from students.debug_all_students import debug_all_students
# from students.simple_views import simple_student_list

# 学生详情页面视图函数
def student_detail_view(request, pk):
    print(f"\n=== student_detail_view (urls.py) 函数被调用 ===")
    print(f"请求路径: {request.path}")
    print(f"学生ID: {pk}")
    
    # 导入必要的模型
    from students.models import Submission
    # 获取学生信息
    student = StudentProfile.objects.select_related('user').get(pk=pk) if StudentProfile.objects.filter(pk=pk).exists() else None
    print(f"找到学生: {student.full_name if student else 'None'} (ID: {pk})")
    
    # 计算提交记录数和通过记录数
    submission_count_value = 0
    approved_count_value = 0
    if student:
        try:
            # 计算所有提交记录（包括所有状态）
            submission_count_value = Submission.objects.filter(student=student).count()
            # 计算通过记录数
            approved_count_value = Submission.objects.filter(student=student, status='approved').count()
            
            # 记录所有提交记录详情
            submissions = Submission.objects.filter(student=student)
            print(f"学生 {student.full_name} 的提交记录详情:")
            for s in submissions:
                print(f"  - ID: {s.id}, 项目: {s.score_item.name}, 状态: {s.status}")
            
            # 记录详细的状态统计信息用于调试
            print(f"学生 {student.full_name} 的提交记录统计:")
            print(f"  总提交数: {submission_count_value}")
            print(f"  通过数: {approved_count_value}")
            
            # 确保没有硬编码值
            print(f"警告: 确认没有使用硬编码值，当前计算值为: {submission_count_value}")
            
        except Exception as e:
            print(f"计算学生提交记录数时出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 渲染模板并传递所有必要的变量
    context = {
        'student': student,
        'user': request.user,
        'is_teacher': request.user.is_superuser or request.user.is_staff,
        'login_url': '/login/',
        'logout_url': '/logout/',
        'submission_count': submission_count_value,  # 传递提交记录数
        'approved_count': approved_count_value,      # 传递通过记录数
        # 添加额外的明确变量名以避免冲突
        'actual_submission_count': submission_count_value,
        'submission_count_calculated': submission_count_value
    }
    print(f"传递给模板的上下文变量:")
    print(f"  submission_count: {context['submission_count']}")
    print(f"  actual_submission_count: {context['actual_submission_count']}")
    
    return render(request, 'students/student_detail.html', context)

# 根URL配置 - 简化版本
urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    # 学生列表页面，使用简单视图绕过ViewSet复杂性
    # 注释掉不存在的视图
    # path('studentprofile-list/', simple_student_list, name='studentprofile-list'),
    # API路由入口
    path('api/', include('students.urls')),
    # 保留原ViewSet路径作为备用
    path('api/studentprofile-list/', StudentProfileViewSet.as_view({'get': 'list'}), name='api-studentprofile-list'),
    # 首页 - 最基本的配置
    path('', home, name='home'),
    path('home/', home, name='home'),
    
    # 基本认证URL - 使用自定义的登录和登出视图
    path('login/', custom_login, name='login'),  # 直接使用自定义登录视图
    path('logout/', custom_logout, name='logout'),  # 直接使用自定义登出视图
    
    # 添加基本视图的URL映射
    path('personal-info/', personal_info, name='personal-info'),
    path('submission-history/', submission_history, name='submission-history'),
    path('submission-list/', SubmissionViewSet.as_view({'get': 'list'}), name='submission-list'),
    # 移除直接定义的scoreitem-list路由，避免与students应用中的router路由冲突
    path('upload-proof/', upload_proof, name='upload-proof'),
    path('debug-profile/', debug_profile, name='debug-profile'),
    path('submission-revoke/<int:pk>/', submission_revoke, name='submission-revoke'),
    path('submission-approve/<int:pk>/', submission_approve, name='submission-approve'),
    path('submission-reject/<int:pk>/', submission_reject, name='submission-reject'),
    path('submission-detail/<int:pk>/', submission_detail, name='submission-detail'),
    # 学生详情页面URL配置
    path('students/student-detail/<int:pk>/', student_detail_view, name='student-detail'),
]

# 处理静态文件和媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)