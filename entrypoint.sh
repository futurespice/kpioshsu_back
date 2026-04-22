#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
until python -c "import socket,sys; s=socket.socket(); s.settimeout(2); s.connect(('${DB_HOST}', int('${DB_PORT}'))); s.close()" 2>/dev/null; do
  sleep 1
done
echo "Database is up."

python manage.py migrate --noinput

exec "$@"
