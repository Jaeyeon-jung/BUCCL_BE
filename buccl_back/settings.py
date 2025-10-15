"""
Django settings for buccl_back project.
"""
import os, json, secretkey
from dotenv import load_dotenv
from datetime import timedelta
from pathlib import Path
import pymysql

# .env 파일 로드
load_dotenv()

# MySQL 드라이버 설정
pymysql.install_as_MySQLdb()

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent

# 시크릿 키 설정
secret_json = os.path.join(BASE_DIR, 'secrets.json')
with open(secret_json) as f:
    secrets_key = json.loads(f.read())
SECRET_KEY = secretkey.get_secret("SECRET_KEY", secrets_key)

# 결제 관련 NICEPAY 키 설정
NICEPAY_MERCHANT_KEY = secretkey.get_secret("NICEPAY_MERCHANT_KEY", secrets_key)
NICEPAY_MERCHANT_ID = secretkey.get_secret("NICEPAY_MERCHANT_ID", secrets_key)

# SMS인증 관련 NICEPAY 키 설정
NAVER_SENS_ACCESS_KEY = secretkey.get_secret("NAVER_SENS_ACCESS_KEY", secrets_key)
NAVER_SENS_SECRET_KEY = secretkey.get_secret("NAVER_SENS_SECRET_KEY", secrets_key)

# 환경 설정 (개발/운영)
DEBUG = os.getenv('DEBUG', 'True') == 'True'
# ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,211.234.108.37').split(',')
ENV = os.environ.get('ENV', 'dev').lower()

_LOG_LEVEL = {
    'dev': 'DEBUG',
    'prod': 'DEBUG' # TODO: 운영 시 log파일 크기 고려해. INFO 이상으로 변경가능.
}
log_level = _LOG_LEVEL[ENV]

# 어플리케이션 정의
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'buccl_user.apps.BucclUserConfig',
    'buccl_main.apps.BucclMainConfig',
    'drf_spectacular',
    'buccl_lessons.apps.BucclLessonsConfig',
]

# 미들웨어 설정
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# URL 및 템플릿 설정
ROOT_URLCONF = 'buccl_back.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

# WSGI 설정
WSGI_APPLICATION = 'buccl_back.wsgi.application'

# 데이터베이스 설정
USE_LEGACY_DB_TIMEZONE = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'dbdeeps_test'),
        'USER': os.getenv('DB_USER', 'moddy5000'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'moddy1213!'),
        'HOST': os.getenv('DB_HOST', '211.234.108.37'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET time_zone = '+09:00'",
            'charset': 'utf8mb4',
        }
    }
}

# 비밀번호 검증 설정
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 국제화 설정
LANGUAGE_CODE = 'ko'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = False

# 정적 파일 설정
STATIC_URL = os.getenv('STATIC_URL', '/server/static/')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, '.static')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URL 설정
APPEND_SLASH = True

# 사용자 모델 설정
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
AUTH_USER_MODEL = "buccl_user.User"

# 소셜 로그인 설정
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
SITE_ID = 1
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'user_id'

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': log_level, 
            'class': 'logging.StreamHandler', 
            'formatter': 'simple'
        },
        'file': {
            'level': log_level,
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'simple',
        },
    },
    'formatters': {
        # TODO: verbose에 request.META[REMOTE_ADDR] 옵션에러 발생으로 일단 사용하지 않음. 확인 후 삭제 가능
        'verbose': {
            'format': '{levelname} {asctime} {module} {message} {request.META[REMOTE_ADDR]}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': log_level,
            'propagate': False, # True로 변경 시 하위로그가 상위 로그로전달되어 console에 중복출력됨
        },
        'django.utils.autoreload': {    # 필요없는 autoreload log 제거
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': log_level,
            'propagate': False,
        },
        'root': {   # DEBUG LEVEL 로그가 나오지 않아 추가필요.
            'handlers': ['console', 'file'],
            'level': log_level,
        },
    },
}

# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # 세션 인증
        'rest_framework.authentication.TokenAuthentication',  # Token 인증
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS 설정
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 
    "https://www.moddy.net,https://moddy.net,https://www.bucketlistclass.com,"
    "https://bucketlistclass.com,https://www.buccl.co.kr,https://buccl.co.kr").split(',')

CORS_ALLOW_CREDENTIALS = True

# CSRF 설정
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS',
    "https://www.moddy.net,https://moddy.net,https://www.bucketlistclass.com,"
    "https://bucketlistclass.com,https://www.buccl.co.kr,https://buccl.co.kr").split(',')

CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True') == 'True'
CSRF_COOKIE_HTTPONLY = True  
CSRF_COOKIE_SAMESITE = 'Lax'  
CSRF_USE_SESSIONS = True  
SESSION_COOKIE_SECURE = True

# 프론트엔드 URL
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://moddy.net')

# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=int(os.getenv('ACCESS_TOKEN_DAYS', '1'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('REFRESH_TOKEN_DAYS', '1'))),
}

# 미디어 파일 설정
MEDIA_URL = os.getenv('MEDIA_URL', '/server/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Swagger 설정
SPECTACULAR_SETTINGS = {
    "TITLE": "Buccl API Document",
    "DESCRIPTION": "Buccl 서비스의 API 문서입니다.",
    "CONTACT": {"name": "Buccl", "email": "buccl@buccl.com"},
    "SWAGGER_UI_SETTINGS": {
        "dom_id": "#swagger-ui",
        "layout": "BaseLayout",
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,
        "defaultModelsExpandDepth": -1,
    },
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],    # Swagger 접근 권한 설정
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "//unpkg.com/swagger-ui-dist@3.38.0", # Swagger UI 버전을 조절.
    "SECURITY": [{  # 인증 방식 설정
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",  # JSON Web Token (JWT) 사용
        },
    }],
}