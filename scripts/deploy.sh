#!/bin/sh
# Güvenli yeniden deploy: veri volume'üne dokunmaz, sadece uygulama imajını yeniler.
set -e

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Hata: .env dosyası yok. Önce: cp .env.example .env" >&2
  exit 1
fi

echo "=== Güvenli deploy başlıyor ==="
echo "NOT: postgres_data volume korunur; veriler silinmez."

git pull --ff-only 2>/dev/null || echo "(git pull atlandı veya uzak yok)"

docker compose build web
docker compose up -d

echo "=== Deploy tamam ==="
docker compose ps
echo ""
echo "Şema güncellemesi entrypoint içinde otomatik yapıldı (migrate --noinput)."
echo "Loglar: docker compose logs -f web"
