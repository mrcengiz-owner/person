#!/bin/sh
# PostgreSQL yedeği (volume verisinin dışında ek güvenlik)
set -e

cd "$(dirname "$0")/.."

STAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$OUT_DIR"

FILE="$OUT_DIR/personel_${STAMP}.sql.gz"

echo "Yedek alınıyor: $FILE"
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-personel}" "${POSTGRES_DB:-personel}" | gzip > "$FILE"
echo "Tamam: $FILE"
