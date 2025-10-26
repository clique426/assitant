from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import TeacherProfile
from students.models import Submission, ScoreItem

@login_required
def teacher_dashboard(request):
    # 确保只有老师或超级管理员可以访问
    if not hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        return redirect('home')
    
    # 获取待审核的提交记录
    pending_submissions = Submission.objects.filter(status='pending')
    
    # 获取最近审核的提交记录
    recent_reviews = Submission.objects.filter(status__in=['approved', 'rejected']).order_by('-reviewed_at')[:10]
    
    # 统计信息
    stats = {
        'pending_count': pending_submissions.count(),
        'total_submissions': Submission.objects.count(),
        'approved_count': Submission.objects.filter(status='approved').count(),
        'rejected_count': Submission.objects.filter(status='rejected').count(),
    }
    
    # 构建上下文，确保超级管理员账号被视为老师类型
    context = {
        'teacher': request.user.teacher_profile if hasattr(request.user, 'teacher_profile') else None,
        'pending_submissions': pending_submissions,
        'recent_reviews': recent_reviews,
        'stats': stats,
        'is_teacher': True,  # 标记为老师类型
        'user': request.user
    }
    
    return render(request, 'teachers/dashboard.html', context)

@login_required
def review_submission(request, submission_id):
    # 确保只有老师或超级管理员可以访问
    if not hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        return redirect('home')
    
    # 这里可以添加审核提交记录的逻辑
    # 暂时返回仪表盘
    return redirect('teacher_dashboard')

@login_required
def teacher_profile(request):
    # 确保只有老师或超级管理员可以访问
    if not hasattr(request.user, 'teacher_profile') and not request.user.is_superuser:
        return redirect('home')
    
    teacher = request.user.teacher_profile if hasattr(request.user, 'teacher_profile') else None
    
    context = {
        'teacher': teacher,
        'is_teacher': True,
        'user': request.user
    }
    
    return render(request, 'teachers/profile.html', context)