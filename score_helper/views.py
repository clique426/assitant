from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, ScoreApplication, AcademicScore, PerformanceScore, ScoreRecord
from .forms import (
    LoginForm, ScoreApplicationForm,
    AcademicScoreForm, PerformanceScoreForm, ApprovalForm
)
from django.contrib.auth import login

# 登录视图（保持不变）
# 登录视图（修复后）
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_student():
            return redirect('student_dashboard')
        elif request.user.is_teacher():
            return redirect('teacher_dashboard')
        else:
            return redirect('admin:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            # 关键修复：直接通过form获取已验证的用户，无需再调用authenticate
            user = form.get_user()
            if user.is_student() or user.is_teacher() or user.is_admin_user():
                login(request, user)  # 直接登录
                messages.success(request, f'登录成功，欢迎回来，{user.username}！')
                if user.is_student():
                    return redirect('student_dashboard')
                elif user.is_teacher():
                    return redirect('teacher_dashboard')
                else:
                    return redirect('admin:index')
            else:
                messages.error(request, '该用户无访问权限')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

# 退出登录（保持不变）
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, '已成功退出登录')
    return redirect('login')


# 学生主页（保持不变）
@login_required(login_url='login')
def student_dashboard(request):
    if not request.user.is_student():
        messages.error(request, '没有权限访问学生主页')
        return redirect('login')

    applications = ScoreApplication.objects.filter(student=request.user).order_by('-created_time')

    academic_records = AcademicScore.objects.filter(
        application__student=request.user,
        application__status='APPROVED'
    ).order_by('-application__updated_time')

    performance_records = PerformanceScore.objects.filter(
        application__student=request.user,
        application__status='APPROVED'
    ).order_by('-application__updated_time')

    academic_total = sum(record.calculate_score() for record in academic_records)
    performance_total = sum(record.calculate_score() for record in performance_records)
    total = academic_total + performance_total

    context = {
        'student': request.user,
        'applications': applications,
        'academic_total': round(academic_total, 2),
        'performance_total': round(performance_total, 2),
        'total': round(total, 2),
        'academic_records': academic_records,
        'performance_records': performance_records,
    }

    return render(request, 'student/dashboard.html', context)


# 学生提交加分申请（完善被截断的代码）
@login_required(login_url='login')
def student_apply(request):
    if not request.user.is_student():
        messages.error(request, '没有权限提交申请')
        return redirect('login')

    if request.method == 'POST':
        form = ScoreApplicationForm(request.POST, request.FILES)
        academic_form = AcademicScoreForm(request.POST)
        performance_form = PerformanceScoreForm(request.POST)  # 已修复拼写

        if form.is_valid():
            apply_type = form.cleaned_data['apply_type']
            application = form.save(commit=False)
            application.student = request.user
            application.status = 'PENDING'  # 与模型中Status选项一致（全大写）
            application.save()

            # 根据申请类型保存对应详情
            if apply_type == 'academic':
                if academic_form.is_valid():
                    academic = academic_form.save(commit=False)
                    academic.user = request.user
                    academic.application = application  # 关联申请
                    academic.save()
                else:
                    application.delete()  # 表单无效时回滚
                    messages.error(request, '学业加分详情填写错误，请检查')
                    return render(request, 'student/apply.html', {
                        'form': form, 'academic_form': academic_form, 'performance_form': performance_form
                    })
            elif apply_type == 'performance':
                if performance_form.is_valid():
                    performance = performance_form.save(commit=False)
                    performance.user = request.user
                    performance.application = application  # 关联申请
                    performance.save()
                else:
                    application.delete()  # 表单无效时回滚
                    messages.error(request, '表现加分详情填写错误，请检查')
                    return render(request, 'student/apply.html', {
                        'form': form, 'academic_form': academic_form, 'performance_form': performance_form
                    })

            messages.success(request, '加分申请已提交，等待老师审批！')
            return redirect('student_dashboard')
    else:
        form = ScoreApplicationForm()
        academic_form = AcademicScoreForm()
        performance_form = PerformanceScoreForm()

    return render(request, 'student/apply.html', {
        'form': form,
        'academic_form': academic_form,
        'performance_form': performance_form
    })


# 补充缺失的老师审批中心视图（关键修复）
@login_required(login_url='login')
def teacher_dashboard(request):
    if not request.user.is_teacher():
        messages.error(request, '没有权限访问老师审批中心')
        return redirect('login')

    # 筛选不同状态的申请（与模型中Status选项一致，全大写）
    pending = ScoreApplication.objects.filter(status='PENDING').order_by('-created_time')
    approved = ScoreApplication.objects.filter(status='APPROVED').order_by('-updated_time')
    rejected = ScoreApplication.objects.filter(status='REJECTED').order_by('-updated_time')

    context = {
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
    }
    return render(request, 'teacher/dashboard.html', context)


# 补充缺失的老师处理审批视图（关键修复）
@login_required(login_url='login')
def approve_application(request, app_id):
    if not request.user.is_teacher():
        messages.error(request, '没有权限处理审批')
        return redirect('login')

    application = get_object_or_404(ScoreApplication, id=app_id)

    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            application.approved_by = request.user
            application.updated_time = timezone.now()  # 更新时间

            if status == 'APPROVED':
                application.status = 'APPROVED'
                application.approved_score = form.cleaned_data['approved_score']
                application.save()

                # 创建加分记录
                ScoreRecord.objects.create(
                    student=application.student,
                    application=application,
                    type=application.apply_type,
                    score=application.approved_score
                )
                messages.success(request, '申请已批准')
            else:
                application.status = 'REJECTED'
                application.reject_reason = form.cleaned_data['reject_reason']
                application.save()
                messages.success(request, '申请已驳回')

            return redirect('teacher_dashboard')
    else:
        form = ApprovalForm()

    context = {'application': application, 'form': form}
    return render(request, 'teacher/approve.html', context)


# 补充缺失的老师撤回审批视图（关键修复）
@login_required(login_url='login')
def revoke_application(request, app_id):
    if not request.user.is_teacher():
        messages.error(request, '没有权限撤回审批')
        return redirect('login')

    application = get_object_or_404(ScoreApplication, id=app_id)
    if application.status in ['APPROVED', 'REJECTED']:
        # 恢复为待审批状态
        application.status = 'PENDING'
        application.approved_by = None
        application.approved_score = None
        application.reject_reason = None
        application.updated_time = timezone.now()
        application.save()

        # 删除关联的加分记录
        ScoreRecord.objects.filter(application=application).delete()
        messages.success(request, '已撤回审批，申请恢复为待审批状态')
    else:
        messages.error(request, '只能撤回已审批的申请')

    return redirect('teacher_dashboard')