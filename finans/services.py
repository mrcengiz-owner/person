from decimal import Decimal

from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce

from .kur import guncel_kur_try, kur_try_al
from .models import Kasa, KasaHareket, KasaHareketTipi, ParaBirimi, kasa_hareket_bakiye_aggregate


def kasa_bakiye(kasa: Kasa, *, haric: int | None = None) -> Decimal:
    qs = kasa.hareketler.all()
    if haric:
        qs = qs.exclude(pk=haric)
    sifir = Decimal("0")
    result = qs.aggregate(bakiye=kasa_hareket_bakiye_aggregate())["bakiye"]
    return result if result is not None else sifir


def kasa_liste_ozet() -> dict:
    """Tüm kasalar + bakiye ve güncel TL karşılığı."""
    kasalar = Kasa.objects.all().order_by("ad")
    toplam_try = Decimal("0")
    satirlar = []

    for kasa in kasalar:
        bakiye = kasa_bakiye(kasa)
        if kasa.para_birimi == ParaBirimi.TRY:
            bakiye_try = bakiye.quantize(Decimal("0.01"))
            kur = Decimal("1")
        else:
            kur = guncel_kur_try(kasa.para_birimi)
            bakiye_try = (
                (bakiye * kur).quantize(Decimal("0.01"))
                if kur is not None
                else None
            )
        if bakiye_try is not None:
            toplam_try += bakiye_try
        satirlar.append(
            {
                "kasa": kasa,
                "bakiye": bakiye,
                "kur": kur,
                "bakiye_try": bakiye_try,
            }
        )

    return {
        "kasalar": satirlar,
        "toplam_try": toplam_try,
        "aktif_sayisi": sum(1 for s in satirlar if s["kasa"].aktif),
    }


def kasa_detay_context(kasa: Kasa) -> dict:
    hareketler = kasa.hareketler.select_related("kaydeden").all()
    bakiye = kasa_bakiye(kasa)
    kur = guncel_kur_try(kasa.para_birimi) if kasa.para_birimi != ParaBirimi.TRY else Decimal("1")
    bakiye_try = (
        (bakiye * kur).quantize(Decimal("0.01"))
        if kur is not None and kasa.para_birimi != ParaBirimi.TRY
        else bakiye.quantize(Decimal("0.01"))
        if kasa.para_birimi == ParaBirimi.TRY
        else None
    )
    toplam_giris_try = hareketler.filter(tip=KasaHareketTipi.GIRIS).aggregate(
        t=Coalesce(Sum("tutar_try"), Value(Decimal("0"), output_field=DecimalField()))
    )["t"]
    toplam_cikis_try = hareketler.filter(tip=KasaHareketTipi.CIKIS).aggregate(
        t=Coalesce(Sum("tutar_try"), Value(Decimal("0"), output_field=DecimalField()))
    )["t"]

    return {
        "kasa": kasa,
        "hareketler": hareketler,
        "bakiye": bakiye,
        "guncel_kur": kur,
        "bakiye_try": bakiye_try,
        "toplam_giris_try": toplam_giris_try,
        "toplam_cikis_try": toplam_cikis_try,
    }


def hareket_kur_onizleme(kasa: Kasa, tutar: Decimal, tarih) -> dict:
    kur = kur_try_al(kasa.para_birimi, tarih)
    tutar_try = None
    if kur is not None:
        tutar_try = (tutar * kur).quantize(Decimal("0.01"))
    return {"kur_try": kur, "tutar_try": tutar_try}
