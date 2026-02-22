from .base import *


# 
# when using production server change the asgi.py settings path
# 

SECRET_KEY = 'django-insecure-n^)kqh+c$%b90s@)7yxg4p)g9ct5+w4a^38f4-3fauwuvj_u$@'

DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'user'
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}


# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# email settings
# start aiosmtpd with "python3 -m aiosmtpd -n -l localhost:8025"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = 'localhost'
EMAIL_PORT = 8025