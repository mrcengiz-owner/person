from django.contrib import admin

from .models import MuhasebeIslem, Personel


class MuhasebeIslemInline(admin.TabularInline):
    model = MuhasebeIslem
    extra = 0
    fields = ("tip", "tutar", "tarih", "aciklama")


@admin.register(Personel)
class PersonelAdmin(admin.ModelAdmin):
    list_display = (
        "ad_soyad",
        "mesai_giris",
        "mesai_cikis",
        "maas",
        "maas_gunu",
        "aktif",
        "olusturan",
        "guncellenme",
    )
    list_filter = ("aktif",)
    search_fields = ("ad_soyad", "telefon")
    inlines = [MuhasebeIslemInline]


@admin.register(MuhasebeIslem)
class MuhasebeIslemAdmin(admin.ModelAdmin):
    list_display = ("personel", "tip", "tutar", "tarih", "kaydeden", "olusturulma")
    readonly_fields = ("olusturulma", "guncellenme", "kaydeden", "guncelleyen")
    list_filter = ("tip", "tarih")
    search_fields = ("personel__ad_soyad", "aciklama")
