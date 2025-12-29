from .base import *


# 
# when using production server change the asgi.py settings path
# 

SECRET_KEY = 'django-insecure-n^)kqh+c$%b90s@)7yxg4p)g9ct5+w4a^38f4-3fauwuvj_u$@'

DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1'
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# email settings
# start aiosmtpd with "python3 -m aiosmtpd -n -l localhost:8025"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = 'localhost'
EMAIL_PORT = 8025