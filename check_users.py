import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GradeTeach.settings')
django.setup()

# 导入User模型
from django.contrib.auth.models import User

# 获取所有用户
users = User.objects.all()

# 打印所有用户
print('所有用户:')
for u in users:
    print(f'- {u.username} (超级用户: {u.is_superuser}, 员工: {u.is_staff})')

# 检查admin用户是否存在
admin_exists = User.objects.filter(username='admin').exists()
print(f'\nadmin用户是否存在: {admin_exists}')

if admin_exists:
    admin_user = User.objects.get(username='admin')
    print(f'admin用户详情: 超级用户={admin_user.is_superuser}, 员工={admin_user.is_staff}')