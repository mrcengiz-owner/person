from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def kullanici_gorunen_ad(user) -> str:
    if not user:
        return "—"
    ad = user.get_full_name().strip()
    return ad or user.username


def islem_kaydi_ozeti(user, zaman=None, eylem: str = "Kaydeden") -> str:
    """Örn: Kaydeden: Ahmet Yılmaz — 30.05.2026 14:32"""
    if not user and not zaman:
        return "—"
    ad = kullanici_gorunen_ad(user)
    if zaman:
        if timezone.is_aware(zaman):
            zaman = timezone.localtime(zaman)
        tarih = zaman.strftime("%d.%m.%Y %H:%M")
        return f"{eylem}: {ad} — {tarih}"
    return f"{eylem}: {ad}"
