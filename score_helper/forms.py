from django import forms
from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField
from .models import User, AcademicScore, PerformanceScore, ScoreApplication


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'})
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )
    captcha = CaptchaField(label="验证码", error_messages={'invalid': '验证码错误或过期'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("用户名不存在")
        return username


# 学业加分表单
class AcademicScoreForm(forms.ModelForm):
    class Meta:
        model = AcademicScore
        fields = [
            'score_type', 'competition_level', 'competition_rank',
            'is_group', 'group_role', 'paper_level', 'paper_author', 'remark'
        ]
        widgets = {
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'score_type': forms.Select(attrs={'class': 'form-select'}),
            'competition_level': forms.Select(attrs={'class': 'form-select'}),
            'competition_rank': forms.Select(attrs={'class': 'form-select'}),
            'group_role': forms.Select(attrs={'class': 'form-select'}),
            'paper_level': forms.Select(attrs={'class': 'form-select'}),
            'paper_author': forms.Select(attrs={'class': 'form-select'}),
        }


# 表现加分表单
class PerformanceScoreForm(forms.ModelForm):
    class Meta:
        model = PerformanceScore
        fields = [
            'score_type', 'volunteer_hours', 'is_large_event',
            'cadre_role', 'cadre_score', 'honor_level', 'remark'
        ]
        widgets = {
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'score_type': forms.Select(attrs={'class': 'form-select'}),
            'volunteer_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'cadre_role': forms.Select(attrs={'class': 'form-select'}),
            'cadre_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'honor_level': forms.Select(attrs={'class': 'form-select'}),
        }


# 学生提交加分申请的表单
class ScoreApplicationForm(forms.ModelForm):
    class Meta:
        model = ScoreApplication
        fields = ['apply_type', 'score_item', 'self_score', 'proof_file']
        widgets = {
            'apply_type': forms.Select(
                attrs={'class': 'form-select', 'label': '申请类型'}
            ),
            'score_item': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请详细描述加分项目（如：国家级A类竞赛一等奖）'}
            ),
            'self_score': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '请填写自评分数'}
            ),
            'proof_file': forms.ClearableFileInput(
                attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.pdf'}  # 限制文件类型
            )
        }
        labels = {
            'apply_type': '申请类型',
            'score_item': '加分项目详情',
            'self_score': '自评分数',
            'proof_file': '证明文件'
        }


# 老师审批表单（通过/驳回）
class ApprovalForm(forms.Form):
    STATUS_CHOICES = [
        ('APPROVED', '通过'),
        ('REJECTED', '驳回')
    ]
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='审批结果'
    )
    approved_score = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='审批通过分数（仅通过时填写）'
    )
    reject_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='驳回理由（仅驳回时填写）'
    )

    # 验证：通过时必须填分数，驳回时必须填理由
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        approved_score = cleaned_data.get('approved_score')
        reject_reason = cleaned_data.get('reject_reason')

        if status == 'APPROVED' and approved_score is None:
            self.add_error('approved_score', '通过审批时必须填写通过分数')
        if status == 'REJECTED' and not reject_reason:
            self.add_error('reject_reason', '驳回时必须填写理由')
        return cleaned_data