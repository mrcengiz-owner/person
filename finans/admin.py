from django.contrib import admin

from .models import Kasa, KasaHareket


class KasaHareketInline(admin.TabularInline):
    model = KasaHareket
    extra = 0
    readonly_fields = ("tutar_try", "olusturulma")
    fields = ("tip", "tutar", "kur_try", "tutar_try", "tarih", "aciklama", "kaydeden")


@admin.register(Kasa)
class KasaAdmin(admin.ModelAdmin):
    list_display = ("ad", "para_birimi", "aktif", "olusturulma")
    list_filter = ("para_birimi", "aktif")
    search_fields = ("ad", "aciklama")
    inlines = [KasaHareketInline]


@admin.register(KasaHareket)
class KasaHareketAdmin(admin.ModelAdmin):
    list_display = ("kasa", "tip", "tutar", "kur_try", "tutar_try", "tarih")
    list_filter = ("tip", "kasa__para_birimi", "tarih")
    search_fields = ("kasa__ad", "aciklama")
    date_hierarchy = "tarih"
    raw_id_fields = ("kasa",)
