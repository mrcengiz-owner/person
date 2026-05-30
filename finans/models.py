from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce


class ParaBirimi(models.TextChoices):
    TRY = "try", "TRY — Türk Lirası"
    USD = "usd", "USD — Amerikan Doları"
    EUR = "eur", "EUR — Euro"
    BTC = "btc", "BTC — Bitcoin"
    ETH = "eth", "ETH — Ethereum"
    USDT = "usdt", "USDT — Tether"
    USDC = "usdc", "USDC — USD Coin"
    SOL = "sol", "SOL — Solana"
    BNB = "bnb", "BNB — Binance Coin"
    XRP = "xrp", "XRP — Ripple"
    DOGE = "doge", "DOGE — Dogecoin"


PARA_BIRIMI_SEMBOL = {
    ParaBirimi.TRY: "₺",
    ParaBirimi.USD: "$",
    ParaBirimi.EUR: "€",
    ParaBirimi.BTC: "₿",
    ParaBirimi.ETH: "Ξ",
    ParaBirimi.USDT: "USDT",
    ParaBirimi.USDC: "USDC",
    ParaBirimi.SOL: "SOL",
    ParaBirimi.BNB: "BNB",
    ParaBirimi.XRP: "XRP",
    ParaBirimi.DOGE: "Ð",
}


class Kasa(models.Model):
    ad = models.CharField("Kasa Adı", max_length=120)
    para_birimi = models.CharField(
        "Para Birimi",
        max_length=10,
        choices=ParaBirimi.choices,
        default=ParaBirimi.TRY,
    )
    aciklama = models.TextField("Açıklama", blank=True)
    aktif = models.BooleanField("Aktif", default=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="olusturdugu_kasalar",
        verbose_name="Oluşturan",
    )
    guncelleyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guncelledigi_kasalar",
        verbose_name="Son güncelleyen",
    )
    olusturulma = models.DateTimeField(auto_now_add=True)
    guncellenme = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "Kasa"
        verbose_name_plural = "Kasalar"

    def __str__(self):
        return f"{self.ad} ({self.get_para_birimi_display()})"

    @property
    def sembol(self) -> str:
        return PARA_BIRIMI_SEMBOL.get(self.para_birimi, self.para_birimi.upper())

    @property
    def bakiye(self) -> Decimal:
        from .services import kasa_bakiye

        return kasa_bakiye(self)

    @property
    def bakiye_try(self) -> Decimal:
        from .kur import guncel_kur_try

        if self.para_birimi == ParaBirimi.TRY:
            return self.bakiye
        kur = guncel_kur_try(self.para_birimi)
        if kur is None:
            return Decimal("0")
        return (self.bakiye * kur).quantize(Decimal("0.01"))


class KasaHareketTipi(models.TextChoices):
    GIRIS = "giris", "Giriş"
    CIKIS = "cikis", "Çıkış"


class KasaHareket(models.Model):
    kasa = models.ForeignKey(
        Kasa,
        on_delete=models.CASCADE,
        related_name="hareketler",
        verbose_name="Kasa",
    )
    tip = models.CharField(
        "Hareket Tipi",
        max_length=10,
        choices=KasaHareketTipi.choices,
    )
    tutar = models.DecimalField(
        "Tutar",
        max_digits=18,
        decimal_places=8,
        validators=[MinValueValidator(Decimal("0.00000001"))],
        help_text="Kasanın para biriminde tutar",
    )
    kur_try = models.DecimalField(
        "Kur (TRY)",
        max_digits=18,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        help_text="1 birim = X TRY (işlem tarihindeki kur)",
    )
    tutar_try = models.DecimalField(
        "TL Karşılığı",
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    tarih = models.DateField("Tarih")
    aciklama = models.CharField("Açıklama", max_length=255, blank=True)
    kaydeden = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kaydettigi_kasa_hareketleri",
        verbose_name="Kaydeden",
    )
    guncelleyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guncelledigi_kasa_hareketleri",
        verbose_name="Son güncelleyen",
    )
    olusturulma = models.DateTimeField(auto_now_add=True)
    guncellenme = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-tarih", "-olusturulma"]
        verbose_name = "Kasa Hareketi"
        verbose_name_plural = "Kasa Hareketleri"

    def __str__(self):
        isaret = "+" if self.tip == KasaHareketTipi.GIRIS else "−"
        return f"{isaret}{self.tutar} {self.kasa.para_birimi.upper()} — {self.kasa.ad}"

    def clean(self):
        super().clean()
        if self.kasa_id and self.tip == KasaHareketTipi.CIKIS:
            from .services import kasa_bakiye

            mevcut = kasa_bakiye(self.kasa, haric=self.pk)
            if self.tutar > mevcut:
                raise ValidationError(
                    {"tutar": f"Yetersiz bakiye. Mevcut: {mevcut} {self.kasa.para_birimi.upper()}"}
                )

    def save(self, *args, **kwargs):
        self.tutar_try = (self.tutar * self.kur_try).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)


def kasa_hareket_bakiye_aggregate():
    """Giriş − çıkış; queryset annotate için."""
    sifir = Value(Decimal("0"), output_field=DecimalField(max_digits=18, decimal_places=8))
    return Coalesce(
        Sum(
            Case(
                When(tip=KasaHareketTipi.GIRIS, then=F("tutar")),
                When(tip=KasaHareketTipi.CIKIS, then=F("tutar") * Value(-1)),
                default=sifir,
                output_field=DecimalField(max_digits=18, decimal_places=8),
            )
        ),
        sifir,
    )
