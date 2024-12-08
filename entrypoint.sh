#!/bin/bash
set -euo pipefail

poetry run ./manage.py wait_for_database

type="${1:-prod}"

if [ "$type" = "dev" ]; then
  poetry run ./manage.py migrate
  exec poetry run ./manage.py runserver 0.0.0.0:8000 --force-color
else
  poetry run ./manage.py migrate
  exec /base/gunicorn.sh seminare.wsgi
fi
