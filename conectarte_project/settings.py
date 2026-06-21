from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env', override=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['testserver', '127.0.0.1', 'localhost', '.onrender.com']

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'http://127.0.0.1',
    'http://localhost',
]

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'chat',
    'moderation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'conectarte_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': dj_database_url.config(default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
}
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-ni'

TIME_ZONE = 'America/Managua'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Supabase S3 Storage (producción) ---
if not DEBUG:
    SUPABASE_S3_ACCESS_KEY = os.getenv('SUPABASE_S3_ACCESS_KEY')
    SUPABASE_S3_SECRET_KEY = os.getenv('SUPABASE_S3_SECRET_KEY')
    SUPABASE_S3_BUCKET = os.getenv('SUPABASE_S3_BUCKET', 'conectarte-images')
    SUPABASE_S3_ENDPOINT = os.getenv('SUPABASE_S3_ENDPOINT', 'https://qwyhbkivnczcsamljrly.storage.supabase.co/storage/v1/s3')
    SUPABASE_S3_REGION = os.getenv('SUPABASE_S3_REGION', 'us-east-1')

    STORAGES['default'] = {
        'BACKEND': 'chat.storage.SupabasePublicStorage',
    }
    AWS_ACCESS_KEY_ID = SUPABASE_S3_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = SUPABASE_S3_SECRET_KEY
    AWS_STORAGE_BUCKET_NAME = SUPABASE_S3_BUCKET
    AWS_S3_REGION_NAME = SUPABASE_S3_REGION
    AWS_S3_ENDPOINT_URL = SUPABASE_S3_ENDPOINT
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
# --- Fin configuración S3 ---

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

import os
os.makedirs(MEDIA_ROOT / 'job_images', exist_ok=True)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login' 

