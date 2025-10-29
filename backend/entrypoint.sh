#!/bin/bash
set -e

until python manage.py check > /dev/null 2>&1; do sleep 2; done

python manage.py migrate --noinput
python manage.py collectstatic --noinput
cp -r /app/collected_static/. /backend_static/static/

exec "$@"
