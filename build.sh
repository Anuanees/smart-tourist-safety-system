#!/usr/bin/env bash
# build.sh — runs on Render/Railway during the build phase
set -o errexit   # exit on error

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
