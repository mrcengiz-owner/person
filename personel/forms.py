from django import forms
from django.db.models import Q

from .models import IslemTipi, MuhasebeIslem, Personel

MESAI_ONAYARLARI = [
    ("09:00", "18:00", "09:00 – 18:00", "Gündüz"),
    ("08:00", "17:00", "08:00 – 17:00", "Standart"),
    ("08:30", "17:30", "08:30 – 17:30", "Esnek"),
    ("10:00", "19:00", "10:00 – 19:00", "Geç giriş"),
    ("22:00", "06:00", "22:00 – 06:00", "Gece vardiyası"),
    ("23:00", "07:00", "23:00 – 07:00", "Gece vardiyası"),
    ("00:00", "08:00", "00:00 – 08:00", "Gece vardiyası"),
    ("16:00", "00:00", "16:00 – 00:00", "Akşam → gece"),
]


class PersonelForm(forms.ModelForm):
    class Meta:
        model = Personel
        fields = [
            "ad_soyad",
            "maas",
            "maas_gunu",
            "mesai_giris",
            "mesai_cikis",
            "telefon",
            "notlar",
            "aktif",
        ]
        widgets = {
            "ad_soyad": forms.TextInput(attrs={"placeholder": "Örn. Ahmet Yılmaz"}),
            "maas": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "maas_gunu": forms.NumberInput(attrs={"min": "1", "max": "28"}),
            "mesai_giris": forms.TimeInput(
                attrs={"type": "time", "class": "mesai-time-input", "id": "id_mesai_giris"}
            ),
            "mesai_cikis": forms.TimeInput(
                attrs={"type": "time", "class": "mesai-time-input", "id": "id_mesai_cikis"}
            ),
            "telefon": forms.TextInput(attrs={"placeholder": "05xx xxx xx xx"}),
            "notlar": forms.Textarea(attrs={"rows": 3}),
        }

class MuhasebeIslemForm(forms.ModelForm):
    class Meta:
        model = MuhasebeIslem
        fields = ["personel", "tip", "tutar", "tarih", "aciklama"]
        widgets = {
            "tutar": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "tarih": forms.DateInput(attrs={"type": "date"}),
            "aciklama": forms.TextInput(attrs={"placeholder": "İsteğe bağlı not"}),
        }

    def __init__(self, *args, tip=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["personel"].queryset = Personel.objects.filter(
                Q(aktif=True) | Q(pk=self.instance.personel_id)
            )
        else:
            self.fields["personel"].queryset = Personel.objects.filter(aktif=True)
        if tip:
            self.fields["tip"].initial = tip
            self.fields["tip"].widget = forms.HiddenInput()
        else:
            self.fields["tip"].widget = forms.Select()


class AvansForm(MuhasebeIslemForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tip=IslemTipi.AVANS, **kwargs)


class MaasOdemeForm(MuhasebeIslemForm):
    def __init__(self, *args, personel=None, **kwargs):
        super().__init__(*args, tip=IslemTipi.MAAS, **kwargs)
        if personel and not self.instance.pk:
            self.fields["tutar"].initial = personel.maas
