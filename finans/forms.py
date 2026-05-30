from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .kur import kur_try_al, tutar_try_hesapla
from .models import Kasa, KasaHareket, KasaHareketTipi, ParaBirimi


class KasaForm(forms.ModelForm):
    class Meta:
        model = Kasa
        fields = ["ad", "para_birimi", "aciklama", "aktif"]
        widgets = {
            "ad": forms.TextInput(attrs={"placeholder": "Örn. Ana Kasa, Binance Cüzdan"}),
            "aciklama": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["para_birimi"].disabled = True
            self.fields["para_birimi"].help_text = (
                "Para birimi kasa oluşturulduktan sonra değiştirilemez."
            )

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk:
            cleaned["para_birimi"] = self.instance.para_birimi
        return cleaned


class KasaHareketForm(forms.ModelForm):
    kur_try = forms.DecimalField(
        label="Kur (1 birim = X TRY)",
        max_digits=18,
        decimal_places=4,
        min_value=Decimal("0.0001"),
        required=False,
        help_text="Boş bırakılırsa işlem tarihindeki kur otomatik alınır.",
    )

    class Meta:
        model = KasaHareket
        fields = ["tip", "tutar", "tarih", "aciklama"]
        widgets = {
            "tarih": forms.DateInput(attrs={"type": "date"}),
            "aciklama": forms.TextInput(attrs={"placeholder": "Opsiyonel açıklama"}),
        }

    def __init__(self, *, kasa: Kasa, **kwargs):
        self.kasa = kasa
        super().__init__(**kwargs)
        self.fields["tip"].initial = KasaHareketTipi.GIRIS
        if not self.initial.get("tarih") and not self.data:
            self.fields["tarih"].initial = timezone.localdate()
        if kasa.para_birimi == ParaBirimi.TRY:
            self.fields["kur_try"].widget = forms.HiddenInput()
            self.fields["kur_try"].initial = Decimal("1")

    def clean_tarih(self):
        tarih = self.cleaned_data["tarih"]
        if tarih > timezone.localdate():
            raise ValidationError("İleri tarihli işlem kaydedilemez.")
        return tarih

    def clean(self):
        cleaned = super().clean()
        kur = cleaned.get("kur_try")
        tarih = cleaned.get("tarih")
        if self.kasa.para_birimi == ParaBirimi.TRY:
            cleaned["kur_try"] = Decimal("1")
        elif kur is None and tarih:
            otomatik = kur_try_al(self.kasa.para_birimi, tarih)
            if otomatik is None:
                raise ValidationError(
                    "Kur alınamadı. Lütfen kur alanını elle girin veya tarihi kontrol edin."
                )
            cleaned["kur_try"] = otomatik
        elif kur is None:
            raise ValidationError({"kur_try": "Kur zorunludur."})
        return cleaned

    def save(self, commit=True):
        hareket = super().save(commit=False)
        hareket.kasa = self.kasa
        hareket.kur_try = self.cleaned_data["kur_try"]
        hareket.tutar_try = tutar_try_hesapla(hareket.tutar, hareket.kur_try)
        if commit:
            hareket.save()
        return hareket
