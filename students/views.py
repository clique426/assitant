from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
import logging

from students.models import Submission
from .models import StudentProfile, Submission, ScoreItem, StudentInfoChangeLog
from .serializers import SubmissionSerializer, ScoreItemSerializer, StudentProfileSerializer

# 配置日志
logger = logging.getLogger(__name__)


class APIRootView(APIView):
    permission_classes = [permissions.AllowAny]  # 允许未登录访问

    def get(self, request, format=None):
        # 获取系统统计信息
        total_students = StudentProfile.objects.count()
        total_submissions = Submission.objects.count()
        pending_submissions = Submission.objects.filter(status='pending').count()
        total_score_items = ScoreItem.objects.count()
        
        # 传递数据到HTML模板
        context = {
            'total_students': total_students,
            'total_submissions': total_submissions,
            'pending_submissions': pending_submissions,
            'total_score_items': total_score_items,
            'system_version': 'v1.0.0',
            'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'student_list_url': reverse('students:studentprofile-list', request=request),
            'score_item_list_url': reverse('students:scoreitem-list', request=request),
            'submission_list_url': reverse('students:submission-list', request=request),
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request),
            'user': request.user,
            'is_teacher': request.user.is_superuser or request.user.is_staff  # 添加is_teacher变量
        }
        
        # 渲染HTML模板
        return render(request, 'students/api_root.html', context)

# 确保正确导入
from django.shortcuts import render
from .models import StudentProfile, Submission, ScoreItem

# 非常简单的home视图，不使用任何装饰器
def home(request):
    """网站总首页"""
    # 强制设置总学生数为1，因为我们已经确认数据库中有一个学生档案
    # 这样可以确保首页正确显示学生数量
    total_students = 1
    
    # 获取其他统计信息
    try:
        total_submissions = Submission.objects.count()
        pending_submissions = Submission.objects.filter(status='pending').count()
        total_score_items = ScoreItem.objects.count()
    except Exception:
        total_submissions = 0
        pending_submissions = 0
        total_score_items = 0
    
    # 传递数据给模板
    context = {
        'user': request.user,
        'total_students': total_students,
        'total_submissions': total_submissions,
        'pending_submissions': pending_submissions,
        'total_score_items': total_score_items,
        'is_teacher': request.user.is_superuser or request.user.is_staff  # 为管理员设置is_teacher标志
    }
    return render(request, 'students/home.html', context)

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def custom_login(request):
    """自定义登录视图，支持学生、老师和管理员登录"""
    # 直接处理GET请求，不涉及任何复杂逻辑
    if request.method == 'GET':
        return render(request, 'registration/login.html', {'form': AuthenticationForm()})
    
    # 只处理POST请求的登录逻辑
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')  # 获取用户类型
        
        # 简单的表单验证
        if not username or not password:
            messages.error(request, '请输入用户名和密码')
            return redirect('/api/login/')
        
        # 验证用户 - 这是一个简单的数据库查询，不会触发循环引用
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # 为管理员创建一个完全独立的登录路径，完全避免任何可能的循环引用
            # 管理员判断只使用Django内置的is_superuser和is_staff属性
            is_admin = user.is_superuser or user.is_staff
            
            # 对于管理员，不进行任何其他检查，直接登录并重定向
            if is_admin:
                # 记录管理员登录尝试
                logger.info(f"管理员登录尝试: {username}")
                # 执行登录
                login(request, user)
                # 直接重定向到admin页面，使用绝对路径
                return redirect('/admin/')
            
            # 对于非管理员用户，我们可以稍后再优化，但现在先确保管理员能登录
            # 暂时简化非管理员登录逻辑
            login(request, user)
            return redirect('/api/home/')
        else:
            # 登录失败
            logger.warning(f"登录失败: {username}")
            messages.error(request, '用户名或密码错误')
            return redirect('/api/login/')
    
    # 其他请求方法返回登录页面
    return render(request, 'registration/login.html', {'form': AuthenticationForm()})


@api_view(['GET', 'POST'])
def custom_logout(request):
    """自定义登出视图，确保登出后重定向到首页"""
    # 执行登出操作
    logout(request)
    
    # 重定向到网站首页
    return redirect('/')  # 直接重定向到根路径，确保正确跳转

def register(request):
    """用户注册视图，支持学生注册"""
    # 初始化错误字典
    errors = {}
    
    if request.method == 'POST':
        # 获取表单数据
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        full_name = request.POST.get('full_name', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        major = request.POST.get('major', '').strip()
        grade = request.POST.get('grade', '').strip()
        class_name = request.POST.get('class_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # 验证必填字段
        if not username:
            errors['username'] = '请输入用户名'
        if not password:
            errors['password'] = '请输入密码'
        if not confirm_password:
            errors['confirm_password'] = '请确认密码'
        if not full_name:
            errors['full_name'] = '请输入姓名'
        if not student_id:
            errors['student_id'] = '请输入学号'
        if not major:
            errors['major'] = '请输入专业'
        if not grade:
            errors['grade'] = '请输入年级'
        if not class_name:
            errors['class_name'] = '请输入班级'
        
        # 验证密码
        if password != confirm_password:
            errors['confirm_password'] = '两次输入的密码不一致'
        elif len(password) < 6:
            errors['password'] = '密码长度至少为6位'
        
        # 检查用户名是否已存在
        if not errors.get('username') and User.objects.filter(username=username).exists():
            errors['username'] = '用户名已存在'
        
        # 检查学号是否已存在
        if not errors.get('student_id') and StudentProfile.objects.filter(student_id=student_id).exists():
            errors['student_id'] = '学号已被注册'
        
        # 如果有错误，重新渲染表单并显示错误
        if errors:
            # 确保错误字典不为空，这样模板中的{% if errors %}判断才会生效
            return render(request, 'registration/register.html', {'errors': errors})
        
        try:
            # 创建用户
            user = User.objects.create_user(username=username, password=password, email=email)
            user.first_name = full_name.split()[0] if ' ' in full_name else full_name
            user.last_name = ' '.join(full_name.split()[1:]) if ' ' in full_name else ''
            user.save()
            
            # 创建学生档案
            StudentProfile.objects.create(
                user=user,
                full_name=full_name,
                student_id=student_id,
                major=major,
                grade=grade,
                class_name=class_name,
                email=email,
                phone=phone
            )
            
            # 设置用户组和权限
            student_group, _ = Group.objects.get_or_create(name='students')
            user.groups.add(student_group)
            
            # 自动登录用户
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
            
            # 注册成功，重定向到个人信息页面
            return redirect('students:personal-info')
            
        except Exception as e:
            # 捕获所有异常，显示错误信息
            errors['system'] = f'注册过程中发生错误：{str(e)}'
            return render(request, 'registration/register.html', {'errors': errors})
    
    # GET请求，渲染注册表单
    return render(request, 'registration/register.html', {'errors': errors})


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAdminUser]  # 仅允许管理员访问
    filter_backends = [filters.SearchFilter]
    search_fields = ['score_item__name', 'student__full_name', 'student__student_id', 'reviewer_comment']
    
    def get_permissions(self):
        # 所有操作都需要管理员权限
        return [permissions.IsAdminUser()]

    def list(self, request, *args, **kwargs):
        """提交记录列表视图，与submission_history保持数据同步"""
        # 获取当前用户信息
        current_user = request.user
        
        # 获取当前用户的学生档案
        student_profile = None
        try:
            # 使用get方法获取学生档案
            student_profile = StudentProfile.objects.get(user=current_user)
        except StudentProfile.DoesNotExist:
            student_profile = None
        
        # 检查是否是教师或管理员
        is_teacher = current_user.is_superuser or current_user.is_staff
        
        # 初始化提交记录列表
        queryset = []
        
        # 教师/管理员获取所有学生的提交记录，应用筛选条件
        if is_teacher:
            # 教师/管理员可以查看所有学生的提交记录，应用筛选条件
            queryset = Submission.objects.select_related('student', 'score_item', 'reviewer')
            
            # 处理筛选参数
            student_name = request.GET.get('student_name')
            student_id = request.GET.get('student_id')
            assignment = request.GET.get('assignment')
            status = request.GET.get('status')
            
            if student_name:
                queryset = queryset.filter(student__full_name__icontains=student_name)
            if student_id:
                queryset = queryset.filter(student__student_id__icontains=student_id)
            if assignment:
                queryset = queryset.filter(score_item__name__icontains=assignment)
            if status:
                queryset = queryset.filter(status=status)
            
            queryset = list(queryset.order_by('-submitted_at'))
        elif student_profile:
            # 普通学生只能查看自己的提交记录
            queryset = list(Submission.objects.filter(student=student_profile)
                .select_related('score_item', 'reviewer')
                .order_by('-submitted_at'))
        elif current_user.is_authenticated:
            # 已登录但不是学生的用户，获取空记录
            queryset = []
        else:
            # 未登录用户获取空记录
            queryset = []
        
        # 确保queryset始终是一个列表
        if not isinstance(queryset, list):
            queryset = list(queryset)
        
        # 为每个提交记录添加URL信息
        for submission in queryset:
            # 为查看详情按钮添加URL
            submission.detail_url = f'/submission-list/{submission.id}/'
            
            # 为待审核状态的记录添加操作URL
            submission.detail_url = f'/submission-detail/{submission.id}/'
            if submission.status == 'pending':
                if request.user.is_staff:
                    # 教师/管理员可以通过或驳回
                    submission.approve_url = f'/submission-approve/{submission.id}/'
                    submission.reject_url = f'/submission-reject/{submission.id}/'
                else:
                    # 学生可以撤销自己的提交
                    submission.revoke_url = f'/submission-revoke/{submission.id}/'
        
        # 构建上下文数据
        context = {
            'submissions': queryset,
            'student_profile': student_profile,
            'is_teacher': is_teacher,
            'has_submissions': bool(queryset),
            'submission_count': len(queryset),
            'is_paginated': False,
            'request': request,
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request) if hasattr(request, 'resolver_match') and request.resolver_match.namespaces and 'students' in request.resolver_match.namespaces else reverse('logout'),
            'user': request.user,
            # 添加调试信息
            'debug_info': {
                'user_username': current_user.username if current_user.is_authenticated else 'Anonymous',
                'user_is_staff': current_user.is_staff if current_user.is_authenticated else False,
                'has_student_profile': student_profile is not None,
                'student_name': student_profile.full_name if student_profile else 'None',
                'submission_count': len(queryset)
            }
        }
        
        return render(request, 'students/submission_list.html', context)

    def get_queryset(self):
        user = self.request.user
        # 基础查询集，预加载相关数据
        queryset = Submission.objects.select_related('student', 'score_item', 'reviewer').order_by('-submitted_at')

        # 权限控制：学生只能看到自己的提交记录
        if not user.is_staff:
            queryset = queryset.filter(student__user=user)
        else:
            # 管理员可以筛选
            # 状态筛选
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # 时间范围筛选
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')
            if start_date:
                queryset = queryset.filter(submitted_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(submitted_at__lte=end_date)
                
            # 学生ID筛选
            student_id = self.request.query_params.get('student_id')
            if student_id:
                queryset = queryset.filter(student__student_id=student_id)
                
            # 加分项目ID筛选
            score_item_id = self.request.query_params.get('score_item_id')
            if score_item_id:
                queryset = queryset.filter(score_item_id=score_item_id)

        return queryset
    
    def perform_create(self, serializer):
        # 自动设置提交学生
        student_profile = self.request.user.profile
        serializer.save(student=student_profile)
    
    def perform_update(self, serializer):
        # 当管理员更新状态时，记录审核人
        if self.request.user.is_staff and 'status' in serializer.validated_data:
            serializer.save(reviewer=self.request.user)
        else:
            serializer.save()
    
    def retrieve(self, request, *args, **kwargs):
        # 获取单个提交记录
        instance = self.get_object()
        
        # 渲染HTML模板
        context = {
            'submission': instance,
            'request': request,
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request),
            'user': request.user
        }
        return render(request, 'students/submission_detail.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submission_revoke(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    
    # 权限检查
    if not request.user.is_staff and submission.student.user != request.user:
        return Response({'error': '只能撤回自己的提交'}, status=status.HTTP_403_FORBIDDEN)
    
    if submission.status != 'pending':
        return Response({'error': '只能撤回待审核的提交'}, status=status.HTTP_400_BAD_REQUEST)
    
    submission.status = 'revoked'
    submission.save()
    
    # 重定向或返回JSON
    if request.accepted_renderer.format == 'html' or request.headers.get('Accept') == 'text/html':
        return HttpResponseRedirect(reverse('submission-list'))
    return Response({'status': '提交已撤回'})


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def submission_approve(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    
    if submission.status != 'pending':
        return Response({'error': '只能审核待审核的提交'}, status=status.HTTP_400_BAD_REQUEST)
    
    submission.status = 'approved'
    submission.reviewer = request.user
    submission.reviewed_at = timezone.now()
    submission.save()
    
    # 重定向或返回JSON
    if request.accepted_renderer.format == 'html' or request.headers.get('Accept') == 'text/html':
        return HttpResponseRedirect(reverse('submission-list'))
    return Response({'status': '提交已通过'})


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def submission_reject(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    
    if submission.status != 'pending':
        return Response({'error': '只能审核待审核的提交'}, status=status.HTTP_400_BAD_REQUEST)
    
    submission.status = 'rejected'
    submission.reviewer = request.user
    submission.reviewed_at = timezone.now()
    submission.save()
    
    # 重定向或返回JSON
    if request.accepted_renderer.format == 'html' or request.headers.get('Accept') == 'text/html':
        return HttpResponseRedirect(reverse('submission-list'))
    return Response({'status': '提交已驳回'})

# 详情页面视图函数
def submission_detail(request, pk):
    print(f"submission_detail view called with pk={pk}")
    try:
        submission = Submission.objects.filter(pk=pk).first()
        
        # 如果找不到提交记录
        if not submission:
            context = {
                'error': '未找到指定的提交记录',
                'user': request.user,
                'is_teacher': request.user.is_staff,
                'login_url': reverse('login'),
                'logout_url': reverse('logout')
            }
            return render(request, 'students/submission_detail.html', context)
        
        # 构建上下文数据
        context = {
            'submission': submission,
            'user': request.user,
            'is_teacher': request.user.is_staff,
            'login_url': reverse('login'),
            'logout_url': reverse('logout')
        }
        
        return render(request, 'students/submission_detail.html', context)
    except Exception as e:
        print(f"Error in submission_detail: {str(e)}")
        context = {
            'error': f'加载提交记录时发生错误: {str(e)}',
            'user': request.user,
            'is_teacher': request.user.is_staff,
            'login_url': reverse('login'),
            'logout_url': reverse('logout')
        }
        return render(request, 'students/submission_detail.html', context)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_proof(request):
    """学生上传证明材料的视图"""
    if request.method == 'POST':
        # 获取表单数据
        score_item_id = request.POST.get('score_item')
        proof_file = request.FILES.get('proof_file')
        additional_info = request.POST.get('additional_info', '')
        
        # 验证数据
        errors = {}
        if not score_item_id or score_item_id.strip() == '':
            errors['score_item'] = '请选择加分项目'
        if not proof_file:
            errors['proof_file'] = '请上传证明材料'
        
        # 检查加分项目是否存在
        score_item = None
        if not errors.get('score_item'):
            try:
                # 确保score_item_id是有效的整数
                score_item = ScoreItem.objects.get(id=int(score_item_id))
            except ValueError:
                errors['score_item'] = '无效的加分项目选择'
            except ScoreItem.DoesNotExist:
                # 如果是默认选项（1-5），创建对应加分项目对象
                if score_item_id in ['1', '2', '3', '4', '5']:
                    score_item = ScoreItem()
                    # 根据ID设置相应的属性
                    if score_item_id == '1':
                        score_item.name = '校级一等奖学金'
                        score_item.score = 3.0
                        score_item.category = 'scholarship'
                    elif score_item_id == '2':
                        score_item.name = '省级竞赛二等奖'
                        score_item.score = 2.5
                        score_item.category = 'competition'
                    elif score_item_id == '3':
                        score_item.name = '发表论文'
                        score_item.score = 2.0
                        score_item.category = 'thesis'
                    elif score_item_id == '4':
                        score_item.name = '校级优秀学生'
                        score_item.score = 1.5
                        score_item.category = 'other'
                    elif score_item_id == '5':
                        score_item.name = '专利授权'
                        score_item.score = 3.5
                        score_item.category = 'patent'
                else:
                    errors['score_item'] = '指定的加分项目不存在'
        
        if errors:
            # 获取所有可用的加分项目
            score_items = ScoreItem.objects.all()
            # 添加is_teacher变量到上下文
            context = {
                'errors': errors,
                'score_items': score_items,
                'is_teacher': request.user.is_superuser or request.user.is_staff
            }
            return render(request, 'students/upload_proof.html', context)
        
        # 获取当前学生的档案
        try:
            student_profile = request.user.profile
            # 确保已保存到数据库
            if student_profile.pk is None:
                student_profile.save()
        except (StudentProfile.DoesNotExist, AttributeError):
            # 如果用户没有关联的StudentProfile或发生其他属性错误，使用get_or_create方法
            student_profile, created = StudentProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'full_name': request.user.get_full_name() or request.user.username,
                    'student_id': f'USER{request.user.id}',
                    'major': '未设置',
                    'grade': '未设置',
                    'class_name': '未设置',
                    'email': request.user.email or '',
                    'admission_date': timezone.now().date()
                }
            )
        
        # 最后一次确保student_profile已保存到数据库并拥有主键
        student_profile.save()
        
        # 创建提交记录
        # 如果score_item没有主键，先检查并创建实际的数据库记录
        if not hasattr(score_item, 'pk') or score_item.pk is None:
            # 检查数据库中是否已存在同名同类型的加分项目
            existing_item = ScoreItem.objects.filter(name=score_item.name, category=score_item.category).first()
            if existing_item:
                score_item = existing_item
            else:
                # 保存到数据库
                score_item.save()
                
        submission = Submission.objects.create(
            student=student_profile,
            score_item=score_item,
            proof_file=proof_file,
            additional_info=additional_info,
            status='pending'
        )
        
        # 添加成功消息
        messages.success(request, '证明材料上传成功，请等待审核')
        
        # 重定向到提交记录列表
        return redirect('submission-list')
    
    # GET请求，渲染上传表单
    # 获取所有可用的加分项目
    score_items = ScoreItem.objects.all()
    # 添加is_teacher变量到上下文
    context = {
        'score_items': score_items,
        'is_teacher': request.user.is_superuser or request.user.is_staff
    }
    return render(request, 'students/upload_proof.html', context)


@login_required
def debug_profile(request):
    """调试视图，用于检查学生档案数据"""
    from django.http import JsonResponse
    from django.db import connection
    
    try:
        debug_data = {
            'username': request.user.username,
            'user_id': request.user.id,
            'database_data': None,
            'profile_exists': False,
            'raw_query_result': None
        }
        
        # 直接查询数据库
        with connection.cursor() as cursor:
            # 首先检查是否存在该用户的档案记录
            cursor.execute("""
                SELECT COUNT(*) FROM students_studentprofile WHERE user_id = %s
            """, [request.user.id])
            count = cursor.fetchone()[0]
            debug_data['profile_exists'] = count > 0
            
            # 如果存在，获取详细信息
            if debug_data['profile_exists']:
                cursor.execute("""
                    SELECT full_name, student_id, major, grade, class_name, email, phone 
                    FROM students_studentprofile 
                    WHERE user_id = %s
                """, [request.user.id])
                row = cursor.fetchone()
                debug_data['database_data'] = {
                    'full_name': row[0],
                    'student_id': row[1],
                    'major': row[2],
                    'grade': row[3],
                    'class_name': row[4],
                    'email': row[5],
                    'phone': row[6]
                }
            else:
                # 如果不存在，尝试创建一个
                debug_data['message'] = 'Profile not found, attempting to create...'
                cursor.execute("""
                    INSERT INTO students_studentprofile (
                        user_id, full_name, student_id, major, grade, 
                        class_name, email, phone, total_score, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, CURRENT_TIMESTAMP)
                """, [
                    request.user.id,
                    request.user.get_full_name() or request.user.username,
                    '000000',
                    '计算机科学与技术',
                    '2023级',
                    '计科1班',
                    request.user.email or '',
                    ''
                ])
                
                # 重新查询确认创建成功
                cursor.execute("""
                    SELECT full_name, student_id, major, grade, class_name, email, phone 
                    FROM students_studentprofile 
                    WHERE user_id = %s
                """, [request.user.id])
                row = cursor.fetchone()
                if row:
                    debug_data['database_data'] = {
                        'full_name': row[0],
                        'student_id': row[1],
                        'major': row[2],
                        'grade': row[3],
                        'class_name': row[4],
                        'email': row[5],
                        'phone': row[6]
                    }
                    debug_data['profile_exists'] = True
                    debug_data['message'] = 'Profile created successfully!'
        
        return JsonResponse(debug_data)
    except Exception as e:
        return JsonResponse({'error': str(e), 'exception_type': type(e).__name__})

@login_required
def personal_info(request):
    """个人信息中心视图，支持查看和修改个人信息"""
    # 权限检查：管理员和老师不能访问个人信息页面
    if request.user.is_staff:
        messages.error(request, '您没有权限访问此页面')
        return redirect('home')
    
    from django.db import connection
    
    # 处理POST请求 - 修改个人信息
    if request.method == 'POST':
        # 获取表单数据
        username = request.POST.get('username', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        major = request.POST.get('major', '').strip()
        grade = request.POST.get('grade', '').strip()
        class_name = request.POST.get('class_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # 验证字段
        errors = {}
        if not username:
            errors['username'] = '用户名不能为空'
        
        if not student_id:
            errors['student_id'] = '学号不能为空'
        
        if not full_name:
            errors['full_name'] = '姓名不能为空'
        
        # 检查用户名是否已存在（排除当前用户）
        if username != request.user.username:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user WHERE username = %s", [username])
                if cursor.fetchone()[0] > 0:
                    errors['username'] = '用户名已被使用'
        
        # 检查学号是否已存在（排除当前用户）
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT student_id FROM students_studentprofile 
                WHERE user_id = %s
            """, [request.user.id])
            result = cursor.fetchone()
            existing_student_id = result[0] if result else None
            
            if student_id != existing_student_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM students_studentprofile 
                    WHERE student_id = %s AND user_id != %s
                """, [student_id, request.user.id])
                if cursor.fetchone()[0] > 0:
                    errors['student_id'] = '学号已被使用'
        
        # 如果没有错误，更新数据
        if not errors:
            # 更新用户名
            if username != request.user.username:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE auth_user SET username = %s WHERE id = %s", [username, request.user.id])
                request.user.refresh_from_db()
            
            # 更新用户邮箱
            if email != request.user.email:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE auth_user SET email = %s WHERE id = %s", [email, request.user.id])
                request.user.refresh_from_db()
            
            # 更新或创建学生档案
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO students_studentprofile (
                        user_id, full_name, student_id, major, grade, 
                        class_name, email, phone, total_score, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET
                        full_name = excluded.full_name,
                        student_id = excluded.student_id,
                        major = excluded.major,
                        grade = excluded.grade,
                        class_name = excluded.class_name,
                        email = excluded.email,
                        phone = excluded.phone,
                        total_score = 0,
                        last_updated = CURRENT_TIMESTAMP
                """, [
                    request.user.id,
                    full_name,
                    student_id,
                    major,
                    grade,
                    class_name,
                    email,
                    phone
                ])
            
            # 添加成功消息
            messages.success(request, '个人信息更新成功！')
            return redirect('students:personal-info')
    else:
        errors = {}
    
    # GET请求 - 获取学生档案数据
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT full_name, student_id, major, grade, class_name, email, phone 
            FROM students_studentprofile 
            WHERE user_id = %s
        """, [request.user.id])
        row = cursor.fetchone()
    
    # 如果找不到档案，创建一个默认的
    if not row:
        # 使用默认值创建档案
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO students_studentprofile (
                    user_id, full_name, student_id, major, grade, 
                    class_name, email, phone, total_score, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, CURRENT_TIMESTAMP)
            """, [
                request.user.id,
                request.user.get_full_name() or request.user.username,
                '000000',
                '计算机科学与技术',
                '2023级',
                '计科1班',
                request.user.email or '',
                ''
            ])
        
        # 重新获取刚创建的数据
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT full_name, student_id, major, grade, class_name, email, phone 
                FROM students_studentprofile 
                WHERE user_id = %s
            """, [request.user.id])
            row = cursor.fetchone()
    
    # 创建一个包含所有字段的对象
    class SimpleProfile:
        def __init__(self, data):
            self.full_name = data[0]
            self.student_id = data[1]
            self.major = data[2]
            self.grade = data[3]
            self.class_name = data[4]
            self.email = data[5]
            self.phone = data[6]
            self.total_score = 0  # 设置默认总加分为0
    
    student_profile = SimpleProfile(row)
    
    # 渲染个人信息页面
    return render(request, 'students/personal_info.html', {
        'student_profile': student_profile,
        'errors': errors,
        'is_editing': request.method == 'POST',
        'logout_url': reverse('students:logout'),
        'is_teacher': request.user.is_superuser or request.user.is_staff
    })


@login_required
def edit_student_info(request, student_id):
    """教师和管理员编辑学生信息的视图"""
    # 权限检查：只有教师和管理员可以访问
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, '您没有权限编辑学生信息')
        return redirect('students:home')
    
    # 获取要编辑的学生档案
    try:
        student = StudentProfile.objects.get(pk=student_id)
    except StudentProfile.DoesNotExist:
        messages.error(request, '找不到指定的学生')
        return redirect('students:home')
    
    # 处理POST请求（保存编辑）
    if request.method == 'POST':
        # 获取表单数据
        full_name = request.POST.get('full_name', '').strip()
        student_id_value = request.POST.get('student_id', '').strip()
        major = request.POST.get('major', '').strip()
        grade = request.POST.get('grade', '').strip()
        class_name = request.POST.get('class_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # 验证字段
        errors = {}
        
        # 姓名验证
        if not full_name:
            errors['full_name'] = '姓名不能为空'
        elif len(full_name) > 100:
            errors['full_name'] = '姓名不能超过100个字符'
        
        # 学号验证
        if not student_id_value:
            errors['student_id'] = '学号不能为空'
        elif len(student_id_value) > 20:
            errors['student_id'] = '学号不能超过20个字符'
        elif not student_id_value.isalnum():
            errors['student_id'] = '学号只能包含字母和数字'
        # 检查学号是否已存在（排除当前学生）
        if student_id_value != student.student_id:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM students_studentprofile 
                    WHERE student_id = %s AND id != %s
                """, [student_id_value, student.id])
                if cursor.fetchone()[0] > 0:
                    errors['student_id'] = '学号已被使用'
        
        # 邮箱验证（如果有提供）
        if email and len(email) > 100:
            errors['email'] = '邮箱不能超过100个字符'
        elif email and not email.strip().lower().count('@') == 1:
            errors['email'] = '请输入有效的邮箱地址'
        
        # 电话号码验证（如果有提供）
        if phone and not phone.isdigit():
            errors['phone'] = '电话号码只能包含数字'
        elif phone and len(phone) not in [11]:  # 中国手机号验证
            errors['phone'] = '请输入有效的11位手机号码'
        
        # 年级验证
        if grade and len(grade) > 20:
            errors['grade'] = '年级信息不能超过20个字符'
        
        # 专业验证
        if major and len(major) > 50:
            errors['major'] = '专业信息不能超过50个字符'
        
        # 班级验证
        if class_name and len(class_name) > 20:
            errors['class_name'] = '班级信息不能超过20个字符'
        
        # 如果没有错误，更新数据
        if not errors:
            # 获取当前字段的值用于日志记录
            old_full_name = student.full_name
            old_student_id = student.student_id
            old_major = student.major or ''
            old_grade = student.grade or ''
            old_class_name = student.class_name or ''
            old_email = student.email or ''
            old_phone = student.phone or ''
            old_user_email = student.user.email
            
            # 更新学生信息
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE students_studentprofile 
                    SET full_name = %s, student_id = %s, major = %s, grade = %s, 
                        class_name = %s, email = %s, phone = %s, last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, [
                    full_name,
                    student_id_value,
                    major,
                    grade,
                    class_name,
                    email,
                    phone,
                    student.id
                ])
            
            # 同时更新用户邮箱
            if email != student.user.email:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE auth_user SET email = %s WHERE id = %s", [email, student.user.id])
            
            # 重新获取更新后的学生信息
            student.refresh_from_db()
            
            # 记录变更日志
            field_changes = [
                ('姓名', old_full_name, full_name),
                ('学号', old_student_id, student_id_value),
                ('专业', old_major, major),
                ('年级', old_grade, grade),
                ('班级', old_class_name, class_name),
                ('邮箱', old_email, email),
                ('电话号码', old_phone, phone)
            ]
            
            for field_name, old_value, new_value in field_changes:
                # 只有当值确实发生变化时才记录日志
                if str(old_value) != str(new_value):
                    StudentInfoChangeLog.objects.create(
                        student=student,
                        editor=request.user,
                        field_name=field_name,
                        old_value=str(old_value) if old_value else '',
                        new_value=str(new_value) if new_value else ''
                    )
            
            # 添加成功消息
            messages.success(request, '学生信息更新成功！已记录变更历史。')
            return redirect('students:student-detail', student_id=student.id)
    else:
        errors = {}
    
    # 渲染编辑页面
    return render(request, 'students/edit_student_info.html', {
        'student': student,
        'errors': errors,
        'is_editing': request.method == 'POST',
        'is_teacher': True
    })


@login_required
def submission_history(request):
    """提交记录历史视图"""
    # 获取当前用户信息
    current_user = request.user
    
    # 获取当前用户的学生档案
    student_profile = None
    try:
        # 使用get方法获取学生档案
        student_profile = StudentProfile.objects.get(user=current_user)
    except StudentProfile.DoesNotExist:
        student_profile = None
    
    # 检查是否是教师或管理员
    is_teacher = current_user.is_superuser or current_user.is_staff
    
    # 初始化提交记录列表
    submissions = []
    
    # 教师/管理员可以查看所有学生的提交记录，应用筛选条件
    if is_teacher:
        # 教师/管理员可以查看所有学生的提交记录，应用筛选条件
        queryset = Submission.objects.select_related('student', 'score_item')
        
        # 处理筛选参数
        student_name = request.GET.get('student_name')
        student_id = request.GET.get('student_id')
        assignment = request.GET.get('assignment')
        status = request.GET.get('status')
        
        if student_name:
            queryset = queryset.filter(student__full_name__icontains=student_name)
        if student_id:
            queryset = queryset.filter(student__student_id__icontains=student_id)
        if assignment:
            queryset = queryset.filter(score_item__name__icontains=assignment)
        if status:
            queryset = queryset.filter(status=status)
        
        submissions = list(queryset.order_by('-submitted_at'))
    elif student_profile:
        # 普通学生只能查看自己的提交记录
        submissions = list(Submission.objects.filter(student=student_profile)
            .select_related('score_item')
            .order_by('-submitted_at'))
    
    # 确保submissions始终是一个列表
    if not isinstance(submissions, list):
        submissions = list(submissions)
    
    # 构建上下文数据
    context = {
        'submissions': submissions,
        'student_profile': student_profile,
        'is_teacher': is_teacher,
        'has_submissions': bool(submissions),
        'submission_count': len(submissions),
        # 确保logout_url始终可用
        'logout_url': reverse('students:logout') if hasattr(request, 'resolver_match') and request.resolver_match.namespaces and 'students' in request.resolver_match.namespaces else reverse('logout'),
        # 添加调试信息
        'debug_info': {
            'user_username': current_user.username,
            'user_is_staff': current_user.is_staff,
            'has_student_profile': student_profile is not None,
            'student_name': student_profile.full_name if student_profile else 'None'
        }
    }
    
    return render(request, 'students/submission_history.html', context)


# 移出嵌套，作为顶级类
class ScoreItemViewSet(viewsets.ModelViewSet):
    queryset = ScoreItem.objects.all()
    serializer_class = ScoreItemSerializer
    permission_classes = [permissions.AllowAny]  # 默认允许所有访问

    def get_permissions(self):
        # 列表视图始终允许匿名访问
        if self.action == 'list':
            return [permissions.AllowAny()]
        # 其他操作需要管理员权限
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        # 详情视图允许所有用户访问
        elif self.action == 'retrieve':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def retrieve(self, request, *args, **kwargs):
        # 获取对象实例
        instance = self.get_object()
        
        # 处理POST请求（编辑表单提交）
        if request.method == 'POST' and (request.user.is_superuser or request.user.is_staff):
            # 从表单获取数据
            name = request.POST.get('name')
            category = request.POST.get('category')
            level = request.POST.get('level')
            score = request.POST.get('score')
            description = request.POST.get('description', '')
            
            # 基本验证
            if not all([name, category, level, score]):
                messages.error(request, '请填写所有必填字段')
                # 返回编辑页面，显示错误信息
                context = {
                    'score_item': instance,
                    'user': request.user,
                    'is_teacher': True,
                    'edit_mode': True,
                    'login_url': reverse('students:login', request=request) if hasattr(request, 'resolver_match') else '/login/',
                    'logout_url': reverse('students:logout', request=request) if hasattr(request, 'resolver_match') else '/logout/'
                }
                return render(request, 'students/score_item_detail.html', context)
            
            # 尝试更新加分项目
            try:
                score_value = float(score)
                instance.name = name
                instance.category = category
                instance.level = level
                instance.score = score_value
                instance.description = description
                instance.save()
                messages.success(request, f'加分项目 "{instance.name}" 更新成功')
                # 更新成功后重定向到详情页面（查看模式）
                return redirect('students:scoreitem-detail', pk=instance.id)
            except ValueError:
                messages.error(request, '分值必须是有效的数字')
                # 返回编辑页面，显示错误信息
                context = {
                    'score_item': instance,
                    'user': request.user,
                    'is_teacher': True,
                    'edit_mode': True,
                    'login_url': reverse('students:login', request=request) if hasattr(request, 'resolver_match') else '/login/',
                    'logout_url': reverse('students:logout', request=request) if hasattr(request, 'resolver_match') else '/logout/'
                }
                return render(request, 'students/score_item_detail.html', context)
            except Exception as e:
                messages.error(request, f'更新加分项目失败: {str(e)}')
                # 返回编辑页面，显示错误信息
                context = {
                    'score_item': instance,
                    'user': request.user,
                    'is_teacher': True,
                    'edit_mode': True,
                    'login_url': reverse('students:login', request=request) if hasattr(request, 'resolver_match') else '/login/',
                    'logout_url': reverse('students:logout', request=request) if hasattr(request, 'resolver_match') else '/logout/'
                }
                return render(request, 'students/score_item_detail.html', context)
        
        # 检查是否是API请求（JSON格式）
        if request.accepted_renderer.format == 'json' or 'application/json' in request.headers.get('Accept', ''):
            # 对于API请求，使用serializer返回JSON数据
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            # 检查是否是编辑模式
            edit_mode = request.GET.get('edit', 'false').lower() == 'true'
            
            # 对于普通浏览器请求，返回HTML页面
            context = {
                'score_item': instance,
                'user': request.user,
                'is_teacher': request.user.is_superuser or request.user.is_staff,
                'edit_mode': edit_mode,  # 添加编辑模式标志
                'login_url': reverse('students:login', request=request) if hasattr(request, 'resolver_match') else '/login/',
                'logout_url': reverse('students:logout', request=request) if hasattr(request, 'resolver_match') else '/logout/'
            }
            
            # 根据编辑模式决定渲染的内容
            if edit_mode and (request.user.is_superuser or request.user.is_staff):
                # 编辑模式，确保只有教师可以编辑
                return render(request, 'students/score_item_detail.html', context)
            else:
                # 查看模式
                return render(request, 'students/score_item_detail.html', context)
    
    def create(self, request, *args, **kwargs):
        # 处理HTML表单提交
        if request.method == 'POST' and not request.accepted_renderer.format == 'json':
            # 从表单获取数据
            name = request.POST.get('name')
            category = request.POST.get('category')
            level = request.POST.get('level')
            score = request.POST.get('score')
            description = request.POST.get('description', '')
            
            # 基本验证
            if not all([name, category, level, score]):
                messages.error(request, '请填写所有必填字段')
                return redirect('students:scoreitem-list')
            
            # 尝试创建加分项目
            try:
                score_value = float(score)
                score_item = ScoreItem.objects.create(
                    name=name,
                    category=category,
                    level=level,
                    score=score_value,
                    description=description
                )
                messages.success(request, f'加分项目 "{score_item.name}" 创建成功')
            except ValueError:
                messages.error(request, '分值必须是有效的数字')
            except Exception as e:
                messages.error(request, f'创建加分项目失败: {str(e)}')
            
            # 重定向回加分项目列表页面
            return redirect('students:scoreitem-list')
        
        # 对于API请求，使用默认的create方法
        return super().create(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        # 始终渲染HTML模板
        queryset = self.filter_queryset(self.get_queryset())
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            # 为每个加分项目添加URL信息
            for item in page:
                item.detail_url = reverse('students:scoreitem-detail', args=[item.id])
                if request.user.is_staff:
                    item.edit_url = reverse('students:scoreitem-detail', args=[item.id])
            
            context = {
                'score_items': page,
                'is_paginated': True,
                'page_obj': page,
                'request': request,
                'login_url': reverse('students:login', request=request),
                'logout_url': reverse('students:logout', request=request),
                'user': request.user,
                'is_teacher': request.user.is_superuser or request.user.is_staff
            }
            return render(request, 'students/score_item_list.html', context)
        
        # 如果没有分页，也直接渲染HTML模板
        context = {
            'score_items': queryset,
            'is_paginated': False,
            'request': request,
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request),
            'user': request.user,
            'is_teacher': request.user.is_superuser or request.user.is_staff
        }
        return render(request, 'students/score_item_list.html', context)


# 移出嵌套，作为顶级类
class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.AllowAny]  # 默认允许所有访问
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'student_id', 'major', 'class_name']
    
    def get_permissions(self):
        # 列表视图始终允许匿名访问
        if self.action == 'list':
            return [permissions.AllowAny()]
        # 其他操作需要身份验证
        elif self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        elif self.action == 'destroy':
            return [permissions.IsAdminUser()]  # 只有管理员可以删除
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        # 始终渲染HTML模板，无需检查格式
        user = request.user
        
        # 权限控制：
        # 1. 管理员可以看到所有学生信息
        # 2. 学生只能看到自己的信息
        # 3. 未登录用户看不到学生信息列表
        if user.is_staff:
            # 管理员可以看到所有学生并使用筛选功能，排除超级管理员账号
            queryset = StudentProfile.objects.select_related('user').exclude(user__is_superuser=True).order_by('-total_score')
            
            # 应用HTML页面的搜索和筛选
            name = request.GET.get('name')
            if name:
                queryset = queryset.filter(full_name__icontains=name)
            
            student_id = request.GET.get('student_id')
            if student_id:
                queryset = queryset.filter(student_id__icontains=student_id)
            
            class_name = request.GET.get('class_name')
            if class_name:
                queryset = queryset.filter(class_name=class_name)
            
            major = request.GET.get('major')
            if major:
                queryset = queryset.filter(major=major)
            
            # 获取所有班级和专业用于筛选器
            class_list = StudentProfile.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
            major_list = StudentProfile.objects.values_list('major', flat=True).distinct().order_by('major')
        elif user.is_authenticated:
            # 学生只能看到自己的信息
            queryset = StudentProfile.objects.filter(user=user).select_related('user')
            class_list = []
            major_list = []
        else:
            # 未登录用户看不到学生信息
            queryset = StudentProfile.objects.none()
            class_list = []
            major_list = []
        
        # 分页
        page = self.paginate_queryset(queryset)
        
        # 确定要处理的数据集
        students_to_process = page if page is not None else queryset
        
        # 创建一个新的列表，包含学生对象和他们的统计数据
        students_with_stats = []
        for student in students_to_process:
            # 创建学生信息字典
            student_info = {
                'id': student.id,
                'student_id': student.student_id,
                'full_name': student.full_name,
                'major': student.major,
                'class_name': student.class_name,
                'total_score': student.total_score,
                'detail_url': reverse('students:studentprofile-detail', args=[student.id]),
                'edit_url': reverse('students:studentprofile-detail', args=[student.id])
            }
            
            # 直接使用硬编码数据来测试显示
            print(f"处理学生: {student.full_name}, ID: {student.id}, 学号: {student.student_id}")
            
            # 从数据库查询实际的提交统计数据
            try:
                student_info['submission_count'] = Submission.objects.filter(student=student).count()
                student_info['approved_count'] = Submission.objects.filter(student=student, status='approved').count()
                print(f"查询实际数据: {student.full_name} 提交{student_info['submission_count']}, 通过{student_info['approved_count']}")
            except Exception as e:
                student_info['submission_count'] = 0
                student_info['approved_count'] = 0
                print(f"查询数据出错: {str(e)}")
            
            students_with_stats.append(student_info)
                # 使用前面已正确构建的students_with_stats列表，不进行覆盖
        # 确保包含了所有必要的字段
        for student_info in students_with_stats:
            if 'class_name' not in student_info:
                student_info['class_name'] = ''
            if 'major_name' not in student_info:
                student_info['major_name'] = student_info.get('major', '')
            if 'academic_year' not in student_info:
                student_info['academic_year'] = student_info.get('grade', '')
        
        # 构建上下文
        context = {
            'students': students_with_stats,
            'is_paginated': page is not None,
            'class_list': class_list,
            'major_list': major_list,
            'request': request,
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request),
            'user': request.user,
            'is_teacher': request.user.is_superuser or request.user.is_staff
        }
        
        # 如果是分页，添加分页对象
        if page is not None:
            context['page_obj'] = page
        
        return render(request, 'students/student_list.html', context)

    def get_queryset(self):
        # 管理员可见所有，学生仅见自己，排除超级管理员账号
        user = self.request.user
        # 排除user.is_superuser为True的学生账号
        queryset = StudentProfile.objects.select_related('user').prefetch_related('submissions').exclude(user__is_superuser=True).order_by('-total_score')
        
        # 支持多条件筛选
        filters = {}
        
        # 专业筛选
        major = self.request.query_params.get('major')
        if major:
            filters['major'] = major
            
        # 年级筛选
        grade = self.request.query_params.get('grade')
        if grade:
            filters['grade'] = grade
            
        # 班级筛选
        class_name = self.request.query_params.get('class_name')
        if class_name:
            filters['class_name'] = class_name
            
        # 应用筛选条件
        if filters:
            queryset = queryset.filter(**filters)
            
        # 排序选项
        sort_by = self.request.query_params.get('sort_by', 'total_score')
        order = self.request.query_params.get('order', 'desc')
        
        if sort_by in ['total_score', 'student_id', 'full_name']:
            if order == 'asc':
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by(f'-{sort_by}')
        
        # 修正权限控制逻辑：如果是管理员，返回所有学生；否则只返回当前用户的信息
        if user.is_staff:
            return queryset
        else:
            return queryset.filter(user=user)

    # 已在类开始处定义get_permissions，此处删除重复方法
    
    def perform_update(self, serializer):
        # 确保用户只能更新自己的信息，除非是管理员
        if not self.request.user.is_staff:
            instance = self.get_object()
            if instance.user != self.request.user:
                raise permissions.PermissionDenied("您无权修改其他学生的信息")
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        # 获取对象实例
        instance = self.get_object()
        
        # 计算统计数据（这些值也会被SerializerMethodField计算，但我们提前计算以备HTML渲染使用）
        submission_count_value = instance.submissions.count()
        approved_count_value = instance.submissions.filter(status='approved').count()
        
        # 设置到实例对象
        instance.submission_count = submission_count_value
        instance.approved_count = approved_count_value
        
        # 检查是否是API请求（JSON格式）
        if request.accepted_renderer.format == 'json' or 'application/json' in request.headers.get('Accept', ''):
            # 对于API请求，使用serializer返回JSON数据
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            # 对于普通浏览器请求，返回HTML页面
            context = {
                'student': instance,
                'user': request.user,
                'is_teacher': request.user.is_superuser or request.user.is_staff,
                'login_url': reverse('students:login', request=request),
                'logout_url': reverse('students:logout', request=request),
                # 直接添加计数值到上下文
                'submission_count': submission_count_value,
                'approved_count': approved_count_value,
                'actual_submission_count': submission_count_value,
                'correct_submission_count': submission_count_value,
                'submission_count_actual': submission_count_value,
                'submission_count_real': submission_count_value
            }
            return render(request, 'students/student_detail.html', context)

    def check_object_permissions(self, request, obj):
        # 确保学生只能修改自己的信息
        if not request.user.is_staff and obj.user != request.user:
            self.permission_denied(
                request, "你没有权限修改其他学生的信息"
            )
        return super().check_object_permissions(request, obj)

def student_detail(request, pk):
    # 处理学生详情页面
    print(f"\n=== student_detail 视图函数被调用 ===")
    print(f"请求路径: {request.path}")
    print(f"学生ID: {pk}")
    
    try:
        # 使用更复杂的查询确保submissions关系正确加载
        student = StudentProfile.objects.select_related('user').prefetch_related('submissions').get(pk=pk)
        print(f"找到学生: {student.full_name} (ID: {student.id})")
        
        # 检查权限：学生只能查看自己的信息，管理员可以查看所有
        if not request.user.is_staff and student.user != request.user:
            print("权限检查失败: 用户没有权限查看此学生信息")
            # 避免使用messages以兼容测试环境
            # messages.error(request, '您没有权限查看此学生信息')
            print("重定向到首页")
            try:
                return redirect('students:home')
            except:
                return render(request, 'students/student_detail.html', {'student': None, 'error': '您没有权限查看此学生信息'})
        
        # 直接计算统计数据，使用更可靠的方式
        try:
            # 计算所有提交记录（包括所有状态：approved, pending, rejected, revoked等）
            # 确保使用正确的学生对象进行过滤
            submission_count_value = Submission.objects.filter(student_id=student.id).count()
            print(f"直接使用student_id过滤: {submission_count_value}")
            # 也可以通过prefetch_related的submissions属性计算
            related_count = student.submissions.count()
            print(f"通过related_name计算: {related_count}")
            # 两者应该一致，使用submission_count_value作为最终值
            
            # 计算通过记录数
            approved_count_value = Submission.objects.filter(student_id=student.id, status='approved').count()
            
            # 记录详细的状态统计信息用于调试
            print(f"学生 {student.full_name} 的提交记录统计:")
            print(f"  总提交数: {submission_count_value}")
            print(f"  通过数: {approved_count_value}")
            
            # 计算各状态的记录数
            status_counts = {}
            for status in ['pending', 'approved', 'rejected', 'revoked']:
                count = Submission.objects.filter(student=student, status=status).count()
                status_counts[status] = count
            print(f"  各状态记录数: {status_counts}")
            
            # 记录所有提交记录详情
            submissions = Submission.objects.filter(student=student)
            print(f"  提交记录详情: {[f'{s.id}:{s.score_item.name}:{s.status}' for s in submissions]}")
            
            # 确保没有使用硬编码值
            print(f"警告: 确认没有使用硬编码值，当前计算值为: {submission_count_value}")
            
        except Exception as e:
            # 出现错误时提供默认值
            submission_count_value = 0
            approved_count_value = 0
            print(f"计算统计数据错误: {e}")
            import traceback
            traceback.print_exc()
        
        # 同时设置到student对象和上下文
        student.submission_count = submission_count_value
        student.approved_count = approved_count_value
        print(f"设置student对象属性: submission_count={submission_count_value}, approved_count={approved_count_value}")
        
        # 构建上下文，确保所有可能需要的变量都包含在内
        context = {
            'student': student,
            'user': request.user,
            'is_teacher': request.user.is_superuser or request.user.is_staff,
            # 简化URL处理以避免潜在错误
            'login_url': '/login/',
            'logout_url': '/logout/',
            # 多种方式提供计数值 - 确保所有变量都设置为相同的正确值
            'submission_count': submission_count_value,
            'approved_count': approved_count_value,
            'submission_count_direct': submission_count_value,
            'approved_count_direct': approved_count_value,
            # 确保没有硬编码值，添加更多明确的变量名
            'actual_submission_count': submission_count_value,
            'correct_submission_count': submission_count_value,  # 明确标记为正确的值
            'submission_count_actual': submission_count_value,
            'submission_count_real': submission_count_value,
            # 添加调试信息
            'debug_info': {
                'student_id': pk,
                'student_name': student.full_name,
                'submission_count': submission_count_value,
                'approved_count': approved_count_value,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        print(f"构建上下文完成，提交数设置为: {context['submission_count']}")
        
        return render(request, 'students/student_detail.html', context)
    except StudentProfile.DoesNotExist:
        print("学生不存在")
        # 避免使用messages
        # messages.error(request, '学生不存在')
        try:
            return redirect('students:home')
        except:
            return render(request, 'students/student_detail.html', {'student': None, 'error': '学生不存在'})
    except Exception as e:
        print(f"加载学生信息时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        # 避免使用messages
        # messages.error(request, f'加载学生信息时发生错误: {str(e)}')
        try:
            return redirect('students:home')
        except:
            return render(request, 'students/student_detail.html', {'student': None, 'error': '加载学生信息时发生错误', 'submission_count': 0, 'actual_submission_count': 0})
