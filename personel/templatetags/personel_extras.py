from django import template

from personel.audit import islem_kaydi_ozeti, kullanici_gorunen_ad
from personel.formatting import format_para

register = template.Library()


@register.filter
def para(value):
    """Örnek: 30000 -> 30.000,00 ₺"""
    return format_para(value)


@register.filter
def kullanici_ad(user):
    return kullanici_gorunen_ad(user)


@register.filter
def kayit_ozeti(islem):
    if not islem:
        return "—"
    return islem_kaydi_ozeti(islem.kaydeden, islem.olusturulma)


@register.filter
def guncelleme_ozeti(islem):
    if not islem:
        return "—"
    return islem_kaydi_ozeti(islem.guncelleyen, islem.guncellenme, "Son güncelleyen")
