#!/bin/bash
set -e

until python manage.py check > /dev/null 2>&1; do
  sleep 2
done

until python manage.py migrate --noinput; do
  echo "DB not ready, retrying migrations in 2s..."
  sleep 2
done

python manage.py collectstatic --noinput
mkdir -p /backend_static/
cp -r /app/collected_static/. /backend_static/ || true

exec "$@"
