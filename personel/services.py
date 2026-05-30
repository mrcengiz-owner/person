import calendar
from datetime import date
from decimal import Decimal
from itertools import groupby

from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import IslemTipi, MuhasebeIslem, Personel

AY_ADLARI = (
    "",
    "Ocak",
    "Şubat",
    "Mart",
    "Nisan",
    "Mayıs",
    "Haziran",
    "Temmuz",
    "Ağustos",
    "Eylül",
    "Ekim",
    "Kasım",
    "Aralık",
)


def _ayin_son_gunu(yil: int, ay: int) -> int:
    return calendar.monthrange(yil, ay)[1]


def maas_tarihi_hesapla(personel: Personel, referans: date | None = None) -> date:
    """Verilen tarihten sonraki ilk maaş ödeme gününü döner."""
    referans = referans or timezone.localdate()
    gun = min(personel.maas_gunu, _ayin_son_gunu(referans.year, referans.month))
    aday = date(referans.year, referans.month, gun)
    if aday < referans:
        if referans.month == 12:
            yil, ay = referans.year + 1, 1
        else:
            yil, ay = referans.year, referans.month + 1
        gun = min(personel.maas_gunu, _ayin_son_gunu(yil, ay))
        aday = date(yil, ay, gun)
    return aday


def maasa_kalan_gun(personel: Personel, referans: date | None = None) -> int:
    referans = referans or timezone.localdate()
    return (maas_tarihi_hesapla(personel, referans) - referans).days


def yaklasan_maas_personelleri(
    gun_limiti: int | None = None,
) -> list[dict]:
    """
    Maaş günü yaklaşan aktif personelleri döner.
    Her öğe: personel, sonraki_maas_tarihi, kalan_gun
    """
    limit = gun_limiti if gun_limiti is not None else getattr(settings, "MAAS_UYARI_GUN", 3)
    bugun = timezone.localdate()
    sonuclar = []

    for personel in Personel.objects.filter(aktif=True):
        kalan = maasa_kalan_gun(personel, bugun)
        if 0 <= kalan <= limit:
            sonuclar.append(
                {
                    "personel": personel,
                    "sonraki_maas": maas_tarihi_hesapla(personel, bugun),
                    "kalan_gun": kalan,
                }
            )

    sonuclar.sort(key=lambda x: x["kalan_gun"])
    return sonuclar


def personel_bakiye_ozeti(personel: Personel, yil: int | None = None, ay: int | None = None) -> dict:
    """Seçilen ay için avans ve maaş ödemelerinin özetini hesaplar."""
    bugun = timezone.localdate()
    yil = yil or bugun.year
    ay = ay or bugun.month

    islemler = MuhasebeIslem.objects.filter(
        personel=personel,
        tarih__year=yil,
        tarih__month=ay,
    )

    avans_toplam = (
        islemler.filter(tip=IslemTipi.AVANS).aggregate(t=Sum("tutar"))["t"]
        or Decimal("0")
    )
    maas_toplam = (
        islemler.filter(tip=IslemTipi.MAAS).aggregate(t=Sum("tutar"))["t"]
        or Decimal("0")
    )

    return {
        "avans_toplam": avans_toplam,
        "maas_toplam": maas_toplam,
        "net_beklenen": personel.maas - avans_toplam,
        "odenen_fark": maas_toplam - (personel.maas - avans_toplam),
    }


def son_islemler(limit: int = 8):
    return MuhasebeIslem.objects.select_related("personel", "kaydeden")[:limit]


def _onceki_ay(yil: int, ay: int) -> tuple[int, int]:
    if ay == 1:
        return yil - 1, 12
    return yil, ay - 1


def maas_odeme_durumu(personel: Personel, ozet: dict) -> dict:
    """Bu ayki maaş ödeme durumunu ve kalan tutarı hesaplar."""
    net = ozet["net_beklenen"]
    odenen = ozet["maas_toplam"]
    kalan = max(Decimal("0"), net - odenen)

    if odenen <= 0:
        durum = "bekliyor"
        etiket = "Ödeme bekleniyor"
        sinif = "badge-muted"
    elif odenen >= net:
        if odenen > personel.maas:
            durum = "fazla"
            etiket = "Fazla ödeme"
            sinif = "badge-info"
        else:
            durum = "tamam"
            etiket = "Ödeme tamamlandı"
            sinif = "badge-success"
    else:
        durum = "kismi"
        etiket = "Kısmi ödeme"
        sinif = "badge-warning"

    avans_oran = 0
    if personel.maas > 0:
        avans_oran = min(100, int((ozet["avans_toplam"] / personel.maas) * 100))

    return {
        "kod": durum,
        "etiket": etiket,
        "sinif": sinif,
        "kalan_odeme": kalan,
        "avans_oran": avans_oran,
        "odeme_oran": min(100, int((odenen / net * 100) if net > 0 else (100 if odenen > 0 else 0))),
    }


def personel_islem_istatistik(personel: Personel) -> dict:
    qs = MuhasebeIslem.objects.filter(personel=personel)
    toplamlar = qs.aggregate(
        toplam_avans=Sum("tutar", filter=Q(tip=IslemTipi.AVANS)),
        toplam_maas=Sum("tutar", filter=Q(tip=IslemTipi.MAAS)),
        avans_adet=Count("id", filter=Q(tip=IslemTipi.AVANS)),
        maas_adet=Count("id", filter=Q(tip=IslemTipi.MAAS)),
    )
    son = qs.first()
    return {
        "toplam_islem": qs.count(),
        "toplam_avans": toplamlar["toplam_avans"] or Decimal("0"),
        "toplam_maas": toplamlar["toplam_maas"] or Decimal("0"),
        "avans_adet": toplamlar["avans_adet"] or 0,
        "maas_adet": toplamlar["maas_adet"] or 0,
        "son_islem": son,
    }


def islemler_aylik_gruplu(personel: Personel, limit: int = 40) -> list[dict]:
    islemler = list(
        personel.islemler.select_related("kaydeden", "guncelleyen").all()[:limit]
    )
    gruplar = []
    for (yil, ay), grup in groupby(islemler, key=lambda i: (i.tarih.year, i.tarih.month)):
        kayitlar = list(grup)
        avans = sum(i.tutar for i in kayitlar if i.tip == IslemTipi.AVANS)
        maas = sum(i.tutar for i in kayitlar if i.tip == IslemTipi.MAAS)
        gruplar.append(
            {
                "etiket": f"{AY_ADLARI[ay]} {yil}",
                "islemler": kayitlar,
                "avans_toplam": avans,
                "maas_toplam": maas,
                "islem_sayisi": len(kayitlar),
            }
        )
    return gruplar


def mesai_gorsel_bilgi(personel: Personel) -> dict:
    """Mesai saatleri için özet ve 24 saatlik çizelge segmentleri."""
    from .mesai import mesai_gorsel_bilgi as _mesai_gorsel

    return _mesai_gorsel(personel.mesai_giris, personel.mesai_cikis)


def personel_detay_context(personel: Personel) -> dict:
    """Personel detay ve modal sayfaları için ortak bağlam."""
    bugun = timezone.localdate()
    uyari_gun = getattr(settings, "MAAS_UYARI_GUN", 3)
    kalan = maasa_kalan_gun(personel, bugun)
    ozet = personel_bakiye_ozeti(personel)
    py, pa = _onceki_ay(bugun.year, bugun.month)
    gecmis_ozet = personel_bakiye_ozeti(personel, py, pa)

    from .audit import islem_kaydi_ozeti

    return {
        "personel": personel,
        "mesai": mesai_gorsel_bilgi(personel),
        "personel_olusturma": islem_kaydi_ozeti(
            personel.olusturan, personel.olusturulma, "Oluşturan"
        ),
        "personel_guncelleme": islem_kaydi_ozeti(
            personel.guncelleyen, personel.guncellenme, "Son güncelleyen"
        ),
        "bugun": bugun,
        "bu_ay_etiket": f"{AY_ADLARI[bugun.month]} {bugun.year}",
        "islemler": personel.islemler.select_related("kaydeden", "guncelleyen").all()[:20],
        "islemler_gruplu": islemler_aylik_gruplu(personel),
        "ozet": ozet,
        "gecmis_ozet": gecmis_ozet,
        "gecmis_ay_etiket": f"{AY_ADLARI[pa]} {py}",
        "odeme_durumu": maas_odeme_durumu(personel, ozet),
        "istatistik": personel_islem_istatistik(personel),
        "sonraki_maas": maas_tarihi_hesapla(personel, bugun),
        "kalan_gun": kalan,
        "yaklasiyor": personel.aktif and 0 <= kalan <= uyari_gun,
    }
