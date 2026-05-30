from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
class Personel(models.Model):
    ad_soyad = models.CharField("Ad Soyad", max_length=120)
    maas = models.DecimalField(
        "Aylık Maaş",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    maas_gunu = models.PositiveSmallIntegerField(
        "Maaş Günü",
        help_text="Her ay maaşın ödeneceği gün (1-28)",
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        default=1,
    )
    telefon = models.CharField("Telefon", max_length=20, blank=True)
    mesai_giris = models.TimeField(
        "Mesai Giriş",
        default="09:00",
        help_text="24 saatlik periyotta işe giriş (ör. 22:00)",
    )
    mesai_cikis = models.TimeField(
        "Mesai Çıkış",
        default="18:00",
        help_text="Çıkış saati; girişten küçük/eşitse ertesi güne sarkar (ör. 06:00)",
    )
    notlar = models.TextField("Notlar", blank=True)
    aktif = models.BooleanField("Aktif", default=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="olusturdugu_personeller",
        verbose_name="Oluşturan",
    )
    guncelleyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guncelledigi_personeller",
        verbose_name="Son güncelleyen",
    )
    olusturulma = models.DateTimeField(auto_now_add=True)
    guncellenme = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ad_soyad"]
        verbose_name = "Personel"
        verbose_name_plural = "Personeller"

    def __str__(self):
        return self.ad_soyad

    def mesai_suresi_dakika(self) -> int | None:
        from .mesai import mesai_suresi_dakika

        return mesai_suresi_dakika(self.mesai_giris, self.mesai_cikis)

    def mesai_suresi_metin(self) -> str:
        from .mesai import mesai_suresi_metin

        return mesai_suresi_metin(self.mesai_giris, self.mesai_cikis)


class IslemTipi(models.TextChoices):
    AVANS = "avans", "Avans"
    MAAS = "maas", "Maaş Ödemesi"


class MuhasebeIslem(models.Model):
    personel = models.ForeignKey(
        Personel,
        on_delete=models.CASCADE,
        related_name="islemler",
        verbose_name="Personel",
    )
    tip = models.CharField(
        "İşlem Tipi",
        max_length=10,
        choices=IslemTipi.choices,
    )
    tutar = models.DecimalField(
        "Tutar",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    tarih = models.DateField("Tarih")
    aciklama = models.CharField("Açıklama", max_length=255, blank=True)
    kaydeden = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kaydettigi_muhasebe_islemleri",
        verbose_name="Kaydeden",
    )
    guncelleyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guncelledigi_muhasebe_islemleri",
        verbose_name="Son güncelleyen",
    )
    olusturulma = models.DateTimeField(auto_now_add=True)
    guncellenme = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-tarih", "-olusturulma"]
        verbose_name = "Muhasebe İşlemi"
        verbose_name_plural = "Muhasebe İşlemleri"

    def __str__(self):
        return f"{self.get_tip_display()} - {self.personel.ad_soyad} - {self.tutar}"
