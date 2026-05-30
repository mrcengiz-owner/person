# Deploy ve veri güvenliği

Bu proje **PostgreSQL** kullanır. Personel, maaş ve işlem kayıtları veritabanında tutulur; her deploy’da **silinmez**.

## Özet

| Ne yapılır | Ne olur |
|------------|---------|
| `docker compose up -d` / `./scripts/deploy.sh` | Sadece kod + şema güncellenir, **veri kalır** |
| `migrate --noinput` (otomatik) | Eksik tablolar/kolonlar eklenir, mevcut satırlar korunur |
| `postgres_data` volume | Tüm PostgreSQL verisi burada; **korunmalı** |

| Ne yapılmaz | Sonuç |
|-------------|--------|
| `docker compose down -v` | Volume silinir → **tüm veri gider** |
| `flush`, `reset_db` | Tablolar boşalır |
| Sunucuda `makemigrations` | Migration dosyaları dağınık olur; sadece geliştiricide |

---

## İlk kurulum (sunucu veya VPS)

```bash
cd core
cp .env.example .env
# .env içinde DJANGO_SECRET_KEY ve POSTGRES_PASSWORD mutlaka değiştirin

chmod +x scripts/*.sh
docker compose up -d --build
```

- İlk açılışta `entrypoint.sh` otomatik: `migrate` + `collectstatic`
- İsteğe bağlı ilk admin (`.env`):

```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=guclu-sifre
DJANGO_SUPERUSER_EMAIL=admin@sirket.com
```

Uygulama: `http://sunucu:8000` (veya `WEB_PORT` ile değiştirin)

---

## Her yeniden deploy (güncelleme)

```bash
cd core
./scripts/deploy.sh
```

veya elle:

```bash
git pull
docker compose build web
docker compose up -d
```

**Yapmayın:** `docker compose down -v`

`web` konteyneri yeniden oluşur; `db` ve `postgres_data` volume aynı kalır → veriler durur.

---

## Geliştirme (bilgisayarınızda)

SQLite varsayılan (`.env` içinde `POSTGRES_HOST` yok):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Model değişikliği yaptıysanız **sadece geliştiricide**:

```bash
python manage.py makemigrations
python manage.py migrate
```

Oluşan `personel/migrations/00xx_*.py` dosyalarını **Git’e commit edin**. Sunucuda `makemigrations` çalıştırmayın.

---

## PostgreSQL ile yerel test (Docker)

```bash
cp .env.example .env
# POSTGRES_HOST=db, DJANGO_DEBUG=0 örneği .env.example ile uyumlu

docker compose up -d --build
```

---

## Yedek alma

```bash
./scripts/yedekle.sh
# backups/personel_YYYYMMDD_HHMMSS.sql.gz
```

Deploy öncesi veya otomatik cron ile kullanın.

---

## GitHub’a gönderme

```bash
cd core
git init
git add .
git commit -m "Personel takip: Django, PostgreSQL, Docker deploy"
git branch -M main
git remote add origin https://github.com/KULLANICI/personel-takip.git
git push -u origin main
```

Sunucuda:

```bash
git clone https://github.com/KULLANICI/personel-takip.git
cd personel-takip   # veya repo içindeki core klasörü
cp .env.example .env
./scripts/deploy.sh
```

---

## Ortam değişkenleri (.env)

| Değişken | Açıklama |
|----------|----------|
| `DJANGO_SECRET_KEY` | Zorunlu (üretim) |
| `DJANGO_DEBUG` | `0` üretimde |
| `DJANGO_ALLOWED_HOSTS` | `alanadi.com,www.alanadi.com` |
| `POSTGRES_*` | Veritabanı bağlantısı |
| `WEB_PORT` | Dış port (varsayılan 8000) |

---

## Sorun giderme

**Deploy sonrası 502 / DB hatası**  
`docker compose logs db web` — PostgreSQL ayakta mı, şifre `.env` ile uyumlu mu?

**Migration hatası**  
Geliştiricide `makemigrations` unutulmuş olabilir. Eksik migration dosyasını repoya ekleyip tekrar deploy.

**Veri kaybı yaşandıysa**  
`down -v` veya yeni boş volume kullanılmış olabilir. Son `backups/*.sql.gz` yedeğinden:

```bash
gunzip -c backups/personel_XXXXXX.sql.gz | docker compose exec -T db psql -U personel personel
```

---

## Teknik not

- Kalıcılık: Docker volume `postgres_data`
- Şema: `scripts/entrypoint.sh` → `python manage.py migrate --noinput`
- Üretim WSGI: Gunicorn (Dockerfile `CMD`)
- Statik: WhiteNoise + `collectstatic`
