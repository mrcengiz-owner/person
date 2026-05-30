"""Günlük TRY kuru — kripto için CoinGecko, fiat için Frankfurter."""

from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache
from django.utils import timezone

from .models import ParaBirimi

logger = logging.getLogger(__name__)

COINGECKO_ID = {
    ParaBirimi.BTC: "bitcoin",
    ParaBirimi.ETH: "ethereum",
    ParaBirimi.USDT: "tether",
    ParaBirimi.USDC: "usd-coin",
    ParaBirimi.SOL: "solana",
    ParaBirimi.BNB: "binancecoin",
    ParaBirimi.XRP: "ripple",
    ParaBirimi.DOGE: "doge-coin",
}

KRIPTO_PARA_BIRIMLERI = frozenset(COINGECKO_ID.keys())
FIAT_DISI = frozenset({ParaBirimi.USD, ParaBirimi.EUR})


def _http_json(url: str, *, timeout: float = 8.0) -> dict | list | None:
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "CoreMuhasebe/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning("Kur API hatası (%s): %s", url, exc)
        return None


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _cache_key(para_birimi: str, tarih: date) -> str:
    return f"kur_try:{para_birimi}:{tarih.isoformat()}"


def _cache_get(para_birimi: str, tarih: date) -> Decimal | None:
    val = cache.get(_cache_key(para_birimi, tarih))
    return _decimal(val) if val is not None else None


def _cache_set(para_birimi: str, tarih: date, kur: Decimal) -> None:
    bugun = timezone.localdate()
    if tarih >= bugun:
        ttl = 3600
    else:
        ttl = 86400 * 30
    cache.set(_cache_key(para_birimi, tarih), str(kur), ttl)


def _coingecko_canli(coin_id: str) -> Decimal | None:
    qs = urlencode({"ids": coin_id, "vs_currencies": "try"})
    data = _http_json(f"https://api.coingecko.com/api/v3/simple/price?{qs}")
    if not isinstance(data, dict):
        return None
    coin = data.get(coin_id) or {}
    return _decimal(coin.get("try"))


def _binance_canli(sembol: str) -> Decimal | None:
    qs = urlencode({"symbol": sembol})
    data = _http_json(f"https://api.binance.com/api/v3/ticker/price?{qs}")
    if not isinstance(data, dict):
        return None
    return _decimal(data.get("price"))


BINANCE_TRY = {
    ParaBirimi.BTC: "BTCTRY",
    ParaBirimi.ETH: "ETHTRY",
    ParaBirimi.USDT: "USDTTRY",
    ParaBirimi.USDC: "USDTTRY",
    ParaBirimi.SOL: "SOLTRY",
    ParaBirimi.BNB: "BNBTRY",
    ParaBirimi.XRP: "XRPTRY",
    ParaBirimi.DOGE: "DOGETRY",
}


def _kripto_kur(coin_id: str, para_birimi: str, tarih: date) -> Decimal | None:
    bugun = timezone.localdate()
    kur: Decimal | None = None
    if tarih >= bugun:
        kur = _coingecko_canli(coin_id)
        if kur is None and para_birimi in BINANCE_TRY:
            kur = _binance_canli(BINANCE_TRY[para_birimi])
    else:
        kur = _coingecko_tarihli(coin_id, tarih)
        if kur is None:
            kur = _coingecko_canli(coin_id)
        if kur is None and para_birimi in BINANCE_TRY:
            kur = _binance_canli(BINANCE_TRY[para_birimi])
    return kur


def _coingecko_tarihli(coin_id: str, tarih: date) -> Decimal | None:
    tarih_str = tarih.strftime("%d-%m-%Y")
    qs = urlencode({"date": tarih_str, "localization": "false"})
    data = _http_json(f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?{qs}")
    if not isinstance(data, dict):
        return None
    market = data.get("market_data") or {}
    current = market.get("current_price") or {}
    return _decimal(current.get("try"))


def _frankfurter(para_birimi: str, tarih: date) -> Decimal | None:
    kod = para_birimi.upper()
    qs = urlencode({"from": kod, "to": "TRY"})
    if tarih >= timezone.localdate():
        url = f"https://api.frankfurter.app/latest?{qs}"
    else:
        url = f"https://api.frankfurter.app/{tarih.isoformat()}?{qs}"
    data = _http_json(url)
    if not isinstance(data, dict):
        return None
    rates = data.get("rates") or {}
    return _decimal(rates.get("TRY"))


def kur_try_al(para_birimi: str, tarih: date | None = None) -> Decimal | None:
    """1 birim para biriminin TRY karşılığını döner."""
    if para_birimi == ParaBirimi.TRY:
        return Decimal("1")

    if tarih is None:
        tarih = timezone.localdate()

    cached = _cache_get(para_birimi, tarih)
    if cached is not None:
        return cached

    kur: Decimal | None = None

    if para_birimi in KRIPTO_PARA_BIRIMLERI:
        coin_id = COINGECKO_ID[para_birimi]
        kur = _kripto_kur(coin_id, para_birimi, tarih)
    elif para_birimi in FIAT_DISI:
        kur = _frankfurter(para_birimi, tarih)

    if kur is not None and kur > 0:
        _cache_set(para_birimi, tarih, kur)
    return kur


def guncel_kur_try(para_birimi: str) -> Decimal | None:
    return kur_try_al(para_birimi, timezone.localdate())


def kur_bilgisi(para_birimi: str, tarih: date | None = None) -> dict:
    """Form/JSON için kur özeti."""
    if tarih is None:
        tarih = timezone.localdate()
    kur = kur_try_al(para_birimi, tarih)
    return {
        "para_birimi": para_birimi,
        "para_birimi_label": dict(ParaBirimi.choices).get(para_birimi, para_birimi),
        "tarih": tarih.isoformat(),
        "kur_try": str(kur) if kur is not None else None,
        "kaynak": _kur_kaynak(para_birimi),
        "basari": kur is not None,
    }


def _kur_kaynak(para_birimi: str) -> str:
    if para_birimi == ParaBirimi.TRY:
        return "sabit"
    if para_birimi in KRIPTO_PARA_BIRIMLERI:
        return "coingecko / binance"
    if para_birimi in FIAT_DISI:
        return "frankfurter"
    return "bilinmiyor"


def tutar_try_hesapla(tutar: Decimal, kur_try: Decimal) -> Decimal:
    return (tutar * kur_try).quantize(Decimal("0.01"))
