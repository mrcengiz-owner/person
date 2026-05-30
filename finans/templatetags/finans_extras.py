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


PARA_BIRIMI_SINIF = {
    ParaBirimi.TRY: "kasa-currency-try",
    ParaBirimi.USD: "kasa-currency-usd",
    ParaBirimi.EUR: "kasa-currency-eur",
    ParaBirimi.BTC: "kasa-currency-btc",
    ParaBirimi.ETH: "kasa-currency-eth",
    ParaBirimi.USDT: "kasa-currency-usdt",
    ParaBirimi.USDC: "kasa-currency-usdc",
    ParaBirimi.SOL: "kasa-currency-sol",
    ParaBirimi.BNB: "kasa-currency-bnb",
    ParaBirimi.XRP: "kasa-currency-xrp",
    ParaBirimi.DOGE: "kasa-currency-doge",
}


@register.filter
def para_birimi_sinif(value):
    return PARA_BIRIMI_SINIF.get(value, "kasa-currency-default")


@register.filter
def para_birimi_sembol(value):
    return PARA_BIRIMI_SEMBOL.get(value, value.upper())
