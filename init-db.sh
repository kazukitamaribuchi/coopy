#!/usr/bin/bash

rm -rf ./blog/migrations
rm -rf db.sqlite3
python manage.py makemigrations blog
python manage.py migrate
python manage.py create_admin
python manage.py runserver 0.0.0.0:8000
