# Personel Takip

Django tabanlı personel, maaş ve muhasebe işlem takibi.

## Özellikler

- Personel yönetimi, mesai (24 saat / gece vardiyası)
- Avans ve maaş ödemeleri, aylık hareket geçmişi
- Giriş zorunlu, kullanıcı iz kaydı
- Açık / koyu tema

## Hızlı başlangıç (geliştirme)

```bash
cd core
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Üretim (PostgreSQL + Docker)

**Deploy ve veri güvenliği için mutlaka okuyun:** [DEPLOY.md](DEPLOY.md)

```bash
cp .env.example .env
# .env düzenleyin
docker compose up -d --build
```

Her güncellemede: `./scripts/deploy.sh` — veriler `postgres_data` volume’ünde kalır.

## Yapı

```
core/
├── manage.py
├── docker-compose.yml
├── DEPLOY.md          ← deploy, migrate, yedek
├── scripts/
│   ├── entrypoint.sh  ← otomatik migrate (veri silmez)
│   ├── deploy.sh
│   └── yedekle.sh
├── personel/
├── accounts/
└── finans/
```
