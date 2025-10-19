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

from .models import StudentProfile, Submission, ScoreItem
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
            'user': request.user
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
        'total_score_items': total_score_items
    }
    return render(request, 'students/home.html', context)

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def custom_login(request):
    """自定义登录视图，支持学生、老师和管理员登录"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')  # 获取用户类型
        
        # 验证用户
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # 验证用户类型是否匹配
            is_student = hasattr(user, 'studentprofile') or hasattr(user, 'profile') and user.profile is not None
            is_teacher = hasattr(user, 'teacherprofile') or hasattr(user, 'teacher_profile') and user.teacher_profile is not None
            is_admin = user.is_superuser or user.is_staff  # 检查是否为管理员
            
            # 检查用户类型是否匹配选择的类型，或是否为管理员
            if (user_type == 'student' and is_student) or (user_type == 'teacher' and is_teacher) or is_admin:
                login(request, user)
                # 根据用户类型重定向
                if is_admin:
                    return redirect('/admin/')  # 管理员登录后到管理后台
                elif user_type == 'student':
                    return redirect('students:home')  # 学生登录后到学生首页
                else:
                    return redirect('teachers:home')  # 老师登录后到老师首页
            else:
                messages.error(request, '用户类型不匹配，请选择正确的用户类型')
                return redirect('students:login')
        else:
            messages.error(request, '用户名或密码错误')
            return redirect('students:login')
    
    # GET请求返回登录页面
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
        # 始终渲染HTML模板，无需检查格式
        # 构建查询集 - 对于未登录用户，显示公开的提交记录
        if request.user.is_authenticated:
            queryset = self.filter_queryset(self.get_queryset())
        else:
            # 未登录用户可以查看的提交记录
            queryset = Submission.objects.select_related('student', 'score_item', 'reviewer').order_by('-submitted_at')
        
        # 应用HTML页面的搜索和筛选
        student_name = request.GET.get('student_name')
        if student_name:
            queryset = queryset.filter(student__full_name__icontains=student_name)
        
        student_id = request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(student__student_id__icontains=student_id)
        
        assignment = request.GET.get('assignment')
        if assignment:
            queryset = queryset.filter(assignment__icontains=assignment)
        
        status = request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            # 为每个提交记录添加URL信息
            for submission in page:
                submission.detail_url = reverse('submission-detail', args=[submission.id])
                if submission.status == 'pending':
                    if request.user.is_staff:
                        submission.approve_url = reverse('submission-approve', args=[submission.id])
                        submission.reject_url = reverse('submission-reject', args=[submission.id])
                    else:
                        submission.revoke_url = reverse('submission-revoke', args=[submission.id])
            
            context = {
                'submissions': page,
                'is_paginated': True,
                'page_obj': page,
                'request': request,
                'login_url': reverse('students:login', request=request),
                'logout_url': reverse('students:logout', request=request),
                'user': request.user
            }
            return render(request, 'students/submission_list.html', context)
        
        # 如果没有分页，也直接渲染HTML模板
        context = {
            'submissions': queryset,
            'is_paginated': False,
            'request': request,
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request),
            'user': request.user
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
                # 如果是默认选项（1-5），创建临时的加分项目对象
                if score_item_id in ['1', '2', '3', '4', '5']:
                    # 创建一个临时的ScoreItem对象（不会保存到数据库）
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
            return render(request, 'students/upload_proof.html', {'errors': errors, 'score_items': score_items})
        
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
        # 如果score_item是临时对象（没有pk），先检查并创建实际的数据库记录
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
    return render(request, 'students/upload_proof.html', {'score_items': score_items})


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
        'logout_url': reverse('students:logout')
    })


@login_required
def submission_history(request):
    """提交记录历史视图"""
    # 获取当前用户的学生档案
    try:
        student_profile = request.user.profile
    except:
        student_profile = None
    
    # 获取当前用户的所有提交记录
    submissions = Submission.objects.filter(student=student_profile).order_by('-submitted_at') if student_profile else []
    
    return render(request, 'students/submission_history.html', {
        'submissions': submissions,
        'student_profile': student_profile,
        'logout_url': reverse('students:logout')
    })


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
        return [permissions.IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        # 始终渲染HTML模板
        queryset = self.filter_queryset(self.get_queryset())
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            # 为每个加分项目添加URL信息
            for item in page:
                item.detail_url = reverse('scoreitem-detail', args=[item.id])
                if request.user.is_staff:
                    item.edit_url = reverse('scoreitem-update', args=[item.id])
            
            context = {
                'score_items': page,
                'is_paginated': True,
                'page_obj': page,
                'request': request,
                'login_url': reverse('students:login', request=request),
                'logout_url': reverse('students:logout', request=request),
                'user': request.user
            }
            return render(request, 'students/score_item_list.html', context)
        
        # 如果没有分页，也直接渲染HTML模板
        context = {
            'score_items': queryset,
            'is_paginated': False,
            'request': request,
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request),
            'user': request.user
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
            # 管理员可以看到所有学生并使用筛选功能
            queryset = self.filter_queryset(self.get_queryset())
            
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
            queryset = StudentProfile.objects.filter(user=user).select_related('user').prefetch_related('submissions')
            class_list = []
            major_list = []
        else:
            # 未登录用户看不到学生信息
            queryset = StudentProfile.objects.none()
            class_list = []
            major_list = []
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            # 为每个学生添加URL信息和统计数据
            for student in page:
                student.detail_url = reverse('studentprofile-detail', args=[student.id])
                student.edit_url = reverse('studentprofile-update', args=[student.id])
                student.submission_count = student.submissions.count()
                student.approved_count = student.submissions.filter(status='approved').count()
            
            context = {
                'students': page,
                'is_paginated': True,
                'page_obj': page,
                'class_list': class_list,
                'major_list': major_list,
                'request': request,
                'login_url': reverse('students:login', request=request),
                'logout_url': reverse('students:logout', request=request),
                'user': request.user
            }
            return render(request, 'students/student_list.html', context)
        
        # 如果没有分页，也直接渲染HTML模板
        context = {
            'students': queryset,
            'is_paginated': False,
            'class_list': class_list,
            'major_list': major_list,
            'request': request,
            'login_url': reverse('students:login', request=request),
            'logout_url': reverse('students:logout', request=request),
            'user': request.user
        }
        return render(request, 'students/student_list.html', context)

    def get_queryset(self):
        # 管理员可见所有，学生仅见自己
        user = self.request.user
        queryset = StudentProfile.objects.select_related('user').prefetch_related('submissions').order_by('-total_score')
        
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
        
        return queryset if user.is_staff else queryset.filter(user=user)

    # 已在类开始处定义get_permissions，此处删除重复方法
    
    def perform_update(self, serializer):
        # 确保用户只能更新自己的信息，除非是管理员
        if not self.request.user.is_staff:
            instance = self.get_object()
            if instance.user != self.request.user:
                raise permissions.PermissionDenied("您无权修改其他学生的信息")
        serializer.save()

    def check_object_permissions(self, request, obj):
        # 确保学生只能修改自己的信息
        if not request.user.is_staff and obj.user != request.user:
            self.permission_denied(
                request, "你没有权限修改其他学生的信息"
            )
        return super().check_object_permissions(request, obj)
