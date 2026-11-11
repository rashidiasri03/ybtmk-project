"""
Django settings for ybtmk_project project.
"""

import pymysql
pymysql.install_as_MySQLdb()

# Tambah 2 baris ini untuk mengabaikan semakan versi MySQL bagi TiDB
from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.check_database_version_supported = lambda self: None

# --- TAMBAH 3 BARIS INI UNTUK BYPASS RALAT 1109 BLUEHOST ---
from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.supports_column_check_constraints = False
DatabaseFeatures.can_introspect_check_constraints = False
# -----------------------------------------------------------

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# ==============================================================================
# 1. SUIS KAWALAN PERSEKITARAN
# ==============================================================================
DEBUG = False  # <--- BUKA KEPADA TRUE SEMENTARA UNTUK KESAN RALAT DI RENDER

if DEBUG:
    ALLOWED_HOSTS = ['*']
    CSRF_TRUSTED_ORIGINS = ['https://ybtmk.michma.com', 'https://ybtmk.healomic.com']
    
    # KITA PAKSA IA BERSAMBUNG KE BLUEHOST SUPAYA RALAT SEBENAR MUNCUL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'healomic_ybtmkdb',
            'USER': 'healomic_dbadmin',
            'PASSWORD': '@Hpu_ybtmk2026',
            'HOST': 'box5692.bluehost.com',
            'PORT': '3306',
        }
    }
else:
    ALLOWED_HOSTS = ['ybtmk.michma.com', 'ybtmk.healomic.com', 'localhost', '127.0.0.1']
    CSRF_TRUSTED_ORIGINS = ['https://ybtmk.michma.com', 'https://ybtmk.healomic.com']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'healomic_ybtmkdb',
            'USER': 'healomic_dbadmin',
            'PASSWORD': '@Hpu_ybtmk2026',
            'HOST': 'box5692.bluehost.com',
            'PORT': '3306',
        }
    }

# Jika berjalan di pelayan Render (Linux), kekalkan laluan fail sijil ini
#if os.environ.get('RENDER'):
#    DATABASES['default']['OPTIONS']['ssl']['ca'] = '/etc/ssl/certs/ca-certificates.crt'
# ==============================================================================


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'home',
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

ROOT_URLCONF = 'ybtmk_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'ybtmk_project.wsgi.application'

# Auth redirects
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/profiling/peta/'
LOGOUT_REDIRECT_URL = '/login/'

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'