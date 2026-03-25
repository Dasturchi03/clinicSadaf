#!/usr/bin/env sh
set -e

if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT..."
  until nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
    sleep 1
  done
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Compiling translations..."
python manage.py compilemessages || true

echo "Collecting static..."
python manage.py collectstatic --noinput

echo "Starting web server..."
exec gunicorn clinicSADAF.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --reload
