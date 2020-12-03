import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print('★★環境変数1★★')
print(os.environ)

if os.environ['DJANGO_ENV'] == 'production':
    print("本番環境")
    DEBUG = False
    import dj_database_url
    db_from_env = dj_database_url.config()
    DATABASES = {
        'default' : dj_database_url.config()
    }
    SESSION_COOLIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    DEBUG = True
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

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

if not DEBUG:
    import django_heroku
    django_heroku.settings(locals())
    # del DATABASES['default']['OPTIONS']['sslmode']

print('★★環境変数2★★')
print(os.environ)

SECRET_KEY = os.environ['SECRET_KEY']


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

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
LOGIN_URL = 'blog:login'
LOGIN_REDIRECT_URL = 'blog:index'

AUTH_USER_MODEL = 'blog.MyUser'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

if not DEBUG:
    del DATABASES['default']['OPTIONS']['sslmode']
