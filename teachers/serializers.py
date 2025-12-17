from rest_framework import serializers
from .models import TeacherProfile
from django.contrib.auth.models import User
from students.models import Submission

# 用户序列化器
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

# 教师档案序列化器
class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    review_count = serializers.SerializerMethodField()  # 审核数量字段
    
    class Meta:
        model = TeacherProfile
        fields = ['id', 'user', 'full_name', 'teacher_id', 'department', 
                 'email', 'phone', 'last_updated', 'review_count']
        read_only_fields = ['last_updated', 'review_count']

    def get_review_count(self, obj):
        # 获取老师审核过的记录数
        return Submission.objects.filter(reviewer=obj.user).count()