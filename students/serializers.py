# students/serializers.py
from rest_framework import serializers
from .models import StudentProfile, Submission, ScoreItem
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    rank = serializers.SerializerMethodField()  # 排名字段
    submission_count = serializers.SerializerMethodField()  # 新增提交数量字段
    approved_count = serializers.SerializerMethodField()  # 新增通过数量字段
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'full_name', 'student_id', 'major', 'grade',
                 'class_name', 'email', 'phone', 'total_score', 
                 'rank', 'submission_count', 'approved_count', 'last_updated']
        read_only_fields = ['total_score', 'rank', 'submission_count', 'approved_count', 'last_updated']

    def get_rank(self, obj):
        # 计算排名
        all_students = StudentProfile.objects.all().order_by('-total_score')
        ranks = {student.id: idx+1 for idx, student in enumerate(all_students)}
        return ranks.get(obj.id, None)
    
    def get_submission_count(self, obj):
        # 获取学生提交记录总数
        return obj.submissions.count()
    
    def get_approved_count(self, obj):
        # 获取学生通过的记录数
        return obj.submissions.filter(status='approved').count()

class ScoreItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreItem
        fields = ['id', 'name', 'category', 'level', 'score', 'description']


class SubmissionSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)
    score_item = ScoreItemSerializer(read_only=True)
    reviewer = serializers.SerializerMethodField()  # 使用SerializerMethodField自定义处理
    score_item_id = serializers.PrimaryKeyRelatedField(
        queryset=ScoreItem.objects.all(),
        source='score_item',
        write_only=True
    )
    proof_file_url = serializers.SerializerMethodField()  # 证明文件URL
    status_display = serializers.CharField(source='get_status_display', read_only=True)  # 状态显示文本

    class Meta:
        model = Submission
        fields = ['id', 'student', 'score_item', 'score_item_id', 'proof_file',
                  'proof_file_url', 'additional_info', 'status', 'status_display',
                  'reviewer_comment', 'reviewer', 'submitted_at', 'reviewed_at']
        read_only_fields = ['status', 'reviewer', 'reviewed_at', 'proof_file_url', 'status_display']

    def get_reviewer(self, obj):
        # 自定义获取审核人信息，如果有审核人且是老师，则返回老师档案信息
        if obj.reviewer:
            try:
                teacher_profile = TeacherProfile.objects.get(user=obj.reviewer)
                return TeacherProfileSerializer(teacher_profile, context=self.context).data
            except TeacherProfile.DoesNotExist:
                # 如果审核人不是老师，则返回用户基本信息
                return UserSerializer(obj.reviewer, context=self.context).data
        return None

    def get_proof_file_url(self, obj):
        if obj.proof_file and hasattr(obj.proof_file, 'url'):
            return self.context['request'].build_absolute_uri(obj.proof_file.url)
        return None
    
    def update(self, instance, validated_data):
        # 允许学生撤回待审核的申请
        if 'status' in validated_data and validated_data['status'] == 'revoked':
            if instance.status == 'pending':
                instance.status = 'revoked'
                return instance
            else:
                raise serializers.ValidationError("只能撤回待审核的申请")
        return super().update(instance, validated_data)