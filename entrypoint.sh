#!/bin/bash

python manage.py collectstatic --settings=settings.settings.dev --noinput

python manage.py makemigrations --settings=settings.settings.dev --noinput 

python manage.py migrate --settings=settings.settings.dev --noinput 

exec "$@"