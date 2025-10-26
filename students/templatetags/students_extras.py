from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='approved_count')
def approved_count(submissions):
    """计算通过的提交记录数"""
    try:
        return submissions.filter(status='approved').count()
    except:
        return 0

@register.filter(name='get_status_color')
def get_status_color(status):
    """
    根据提交状态返回对应的Bootstrap徽章颜色类
    """
    status_colors = {
        'pending': 'warning',  # 待审核 - 黄色
        'approved': 'success',  # 已通过 - 绿色
        'rejected': 'danger',   # 已驳回 - 红色
        'revoked': 'secondary', # 已撤回 - 灰色
    }
    return status_colors.get(status, 'info')  # 默认返回info颜色

@register.filter(name='get_category_display')
def get_category_display(category):
    """
    根据加分项目类别返回中文显示名称
    """
    category_display = {
        'scholarship': '奖学金',
        'competition': '竞赛',
        'thesis': '论文发表',
        'patent': '专利',
        'other': '其他',
    }
    return category_display.get(category, category)  # 默认返回原始类别