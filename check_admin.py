from django.contrib.auth.models import User
try:
    user = User.objects.get(username='admin')
    print(f'用户存在: {user.username}, 超级用户: {user.is_superuser}, 员工: {user.is_staff}')
except User.DoesNotExist:
    print('admin用户不存在')