import calendar
from datetime import date, timedelta
from decimal import Decimal
from itertools import groupby

from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import IslemTipi, MuhasebeIslem, Personel

DONEM_GUNLUK = "gunluk"
DONEM_HAFTALIK = "haftalik"
DONEM_AYLIK = "aylik"
DONEM_VARSAYILAN = DONEM_AYLIK

DONEM_SECENEKLERI = (
    (DONEM_GUNLUK, "Günlük"),
    (DONEM_HAFTALIK, "Haftalık"),
    (DONEM_AYLIK, "Aylık"),
)

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


def donem_dogrula(donem: str) -> str:
    gecerli = {k for k, _ in DONEM_SECENEKLERI}
    return donem if donem in gecerli else DONEM_VARSAYILAN


def donem_tarih_araligi(
    donem: str,
    referans: date | None = None,
) -> tuple[date, date]:
    """Seçilen periyoda göre tarih aralığı (dahil)."""
    referans = referans or timezone.localdate()
    donem = donem_dogrula(donem)

    if donem == DONEM_GUNLUK:
        return referans, referans

    if donem == DONEM_HAFTALIK:
        baslangic = referans - timedelta(days=referans.weekday())
        return baslangic, baslangic + timedelta(days=6)

    baslangic = referans.replace(day=1)
    bitis = referans.replace(day=_ayin_son_gunu(referans.year, referans.month))
    return baslangic, bitis


def donem_araligi_metin(baslangic: date, bitis: date) -> str:
    if baslangic == bitis:
        return baslangic.strftime("%d.%m.%Y")
    return f"{baslangic.strftime('%d.%m.%Y')} – {bitis.strftime('%d.%m.%Y')}"


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
    return MuhasebeIslem.objects.select_related("personel", "kaydeden").order_by(
        "-tarih", "-olusturulma"
    )[:limit]


def anasayfa_ozet(referans: date | None = None) -> dict:
    """Anasayfa kartları için bu ayın finansal özeti."""
    referans = referans or timezone.localdate()
    baslangic, bitis = donem_tarih_araligi(DONEM_AYLIK, referans)
    qs = MuhasebeIslem.objects.filter(tarih__gte=baslangic, tarih__lte=bitis)
    sayim = qs.aggregate(
        kayit=Count("id"),
        toplam_masraf=Sum("tutar", filter=Q(tip=IslemTipi.MASRAF)),
        toplam_avans=Sum("tutar", filter=Q(tip=IslemTipi.AVANS)),
        toplam_maas=Sum("tutar", filter=Q(tip=IslemTipi.MAAS)),
    )
    toplam_masraf = sayim["toplam_masraf"] or Decimal("0")
    toplam_avans = sayim["toplam_avans"] or Decimal("0")
    toplam_maas = sayim["toplam_maas"] or Decimal("0")
    return {
        "bu_ay_etiket": f"{AY_ADLARI[referans.month]} {referans.year}",
        "donem_araligi": donem_araligi_metin(baslangic, bitis),
        "aylik_kayit": sayim["kayit"] or 0,
        "aylik_masraf": toplam_masraf,
        "aylik_avans": toplam_avans,
        "aylik_maas": toplam_maas,
        "aylik_toplam": toplam_masraf + toplam_avans + toplam_maas,
    }


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
