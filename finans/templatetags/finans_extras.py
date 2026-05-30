from django import template

from finans.models import PARA_BIRIMI_SEMBOL, ParaBirimi
from personel.formatting import format_para

register = template.Library()


@register.filter
def para_doviz(value, para_birimi="try"):
    """Para birimine göre formatlar."""
    sembol_map = {
        ParaBirimi.TRY: " ₺",
        ParaBirimi.USD: " $",
        ParaBirimi.EUR: " €",
    }
    suffix = sembol_map.get(para_birimi, f" {para_birimi.upper()}")
    decimals = 8 if para_birimi in {
        ParaBirimi.BTC,
        ParaBirimi.ETH,
        ParaBirimi.USDT,
        ParaBirimi.USDC,
        ParaBirimi.SOL,
        ParaBirimi.BNB,
        ParaBirimi.XRP,
        ParaBirimi.DOGE,
    } else 2
    if para_birimi == ParaBirimi.TRY:
        decimals = 2
    return format_para(value, decimals=decimals, suffix=suffix)


@register.filter
def para_birimi_etiket(value):
    return dict(ParaBirimi.choices).get(value, value)


@register.filter
def para_birimi_sembol(value):
    return PARA_BIRIMI_SEMBOL.get(value, value.upper())
