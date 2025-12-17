import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥（替换为你的密钥）
SECRET_KEY = 'django-insecure-你的密钥（例如：abc123...）'

# 开发模式（调试开启）
DEBUG = True
ALLOWED_HOSTS = []

# 已安装应用（含验证码和自定义应用）
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'score_helper',  # 自定义应用
    'captcha',       # 验证码应用（必须）
]

# 自定义用户模型（关键：替换默认用户表）
AUTH_USER_MODEL = 'score_helper.User'

# 中间件（默认保留）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 主路由配置
ROOT_URLCONF = 'GradeTeachProject.urls'

# 模板配置（自动识别应用内的templates目录）
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'GradeTeachProject.wsgi.application'

# 数据库配置（SQLite，无需额外安装）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 密码验证规则
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 语言和时区（中文+上海时间）
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件配置（关键：指定图片等静态资源路径）
STATIC_URL = 'static/'  # 浏览器访问路径（如http://.../static/图片）
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'score_helper/static')  # 本地存放路径
]

# 媒体文件配置（用户上传的证明文件）
MEDIA_URL = '/media/'  # 访问路径
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 本地存放路径

# 默认主键类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'