#!/bin/sh
# Her container başlangıcında: şema güncelle, veriyi silme.
set -e

cd /app

wait_for_db() {
  if [ -z "$POSTGRES_HOST" ]; then
    return 0
  fi
  echo "PostgreSQL bekleniyor ($POSTGRES_HOST)..."
  i=0
  while [ "$i" -lt 60 ]; do
    if python -c "
import os, socket, sys
h = os.environ.get('POSTGRES_HOST', 'db')
p = int(os.environ.get('POSTGRES_PORT', '5432'))
s = socket.socket()
s.settimeout(2)
try:
    s.connect((h, p))
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
"; then
      echo "PostgreSQL hazır."
      return 0
    fi
    i=$((i + 1))
    sleep 1
  done
  echo "PostgreSQL bağlantısı zaman aşımı." >&2
  exit 1
}

wait_for_db

echo "Veritabanı şeması güncelleniyor (migrate --noinput)..."
python manage.py migrate --noinput

echo "Statik dosyalar toplanıyor..."
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser_if_missing 2>/dev/null || true
fi

echo "Uygulama başlatılıyor..."
exec "$@"
