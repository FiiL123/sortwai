#!/bin/bash
set -euo pipefail

poetry run ./manage.py wait_for_database

if [ ${DEBUG:+1} ]; then
  poetry run ./manage.py migrate
  exec poetry run ./manage.py runserver 0.0.0.0:8001 --force-color
else
  poetry run ./manage.py migrate
  exec /base/gunicorn.sh sortwai.wsgi
fi
