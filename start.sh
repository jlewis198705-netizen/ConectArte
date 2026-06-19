#!/bin/bash

python manage.py migrate --noinput
python manage.py collectstatic --noinput

gunicorn conectarte_project.wsgi:application
