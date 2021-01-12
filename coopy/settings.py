import os
import logging
import environ

env = environ.Env()
env.read_env('.env')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ['SECRET_KEY']

if os.environ['DJANGO_ENV'] == 'production':
    print("本番環境")
    DEBUG = False
    SESSION_COOLIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    DEBUG = True

ALLOWED_HOSTS = ['*']

logging.basicConfig(
    level = logging.DEBUG,
    format = '''%(levelname)s %(asctime)s %(pathname)s:%(funcName)s 行数:%(lineno)s:%(lineno)s
    %(message)s'''
    # filename = 'logs/debug.log',
    # filemode = 'a'
)

logger = logging.getLogger(__name__)

INSTALLED_APPS = [
    'blog.apps.BlogConfig',
    'userblog.apps.UserblogConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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


ROOT_URLCONF = 'coopy.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'coopy.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# カスタムパスワードバリデーター
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'blog.password_validator.MyCommonPasswordValidator'
    },
]



LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ['SENDGRID_API_KEY']
EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
LOGIN_URL = 'blog:login'
LOGIN_REDIRECT_URL = 'blog:index'

AUTH_USER_MODEL = 'blog.MyUser'

if not DEBUG:
    import dj_database_url
    DATABASE_URL = os.environ.get('DATABASE_URL')
    db_from_env = dj_database_url.config(default=DATABASE_URL, ssl_require=True)
    DATABASES['default'].update(db_from_env)

    # import django_heroku
    # django_heroku.settings(locals())
    # del DATABASES['default']['OPTIONS']['sslmode']
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    INSTALLED_APPS += [
        'cloudinary',
        'cloudinary_storage',
    ]
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ['CLOUD_NAME'],
        'API_KEY':  os.environ['CLOUDINARY_API_KEY'],
        'API_SECRET': os.environ['CLOUDINARY_API_SECRET']
    }
