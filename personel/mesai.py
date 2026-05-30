"""24 saatlik çalışma periyodunda mesai hesapları (gece vardiyası dahil)."""

from datetime import time

GUN_DAKIKA = 24 * 60


def dakika_from_time(t: time) -> int:
    return t.hour * 60 + t.minute


def gece_vardiyasi(giris: time | None, cikis: time | None) -> bool:
    if not giris or not cikis:
        return False
    return dakika_from_time(cikis) <= dakika_from_time(giris)


def mesai_suresi_dakika(giris: time | None, cikis: time | None) -> int | None:
    if not giris or not cikis:
        return None
    g = dakika_from_time(giris)
    c = dakika_from_time(cikis)
    if c <= g:
        c += GUN_DAKIKA
    return c - g


def mesai_suresi_metin(giris: time | None, cikis: time | None) -> str:
    dakika = mesai_suresi_dakika(giris, cikis)
    if dakika is None:
        return "—"
    saat, dk = divmod(dakika, 60)
    if dakika == GUN_DAKIKA:
        return "24 saat"
    if dk:
        return f"{saat} saat {dk} dk"
    return f"{saat} saat"


def mesai_aralik_metin(giris: time | None, cikis: time | None) -> str:
    if not giris or not cikis:
        return "—"
    g = giris.strftime("%H:%M")
    c = cikis.strftime("%H:%M")
    if gece_vardiyasi(giris, cikis):
        return f"{g} – {c} (+1 gün)"
    return f"{g} – {c}"


def mesai_timeline_segmentleri(giris: time, cikis: time) -> list[dict[str, float]]:
    """
    24 saatlik çizelgede gösterim segmentleri.
    Gece vardiyasında iki parça: giriş → gece yarısı, gece yarısı → çıkış.
    """
    g = dakika_from_time(giris)
    c = dakika_from_time(cikis)
    gun = GUN_DAKIKA

    if g == c:
        return [{"sol": 0, "genislik": 100}]

    if c > g:
        return [
            {
                "sol": round(g / gun * 100, 2),
                "genislik": round(max((c - g) / gun * 100, 1.5), 2),
            }
        ]

    seg1 = (gun - g) / gun * 100
    seg2 = c / gun * 100
    return [
        {"sol": round(g / gun * 100, 2), "genislik": round(max(seg1, 1.5), 2)},
        {"sol": 0, "genislik": round(max(seg2, 1.5), 2)},
    ]


def mesai_gorsel_bilgi(giris: time | None, cikis: time | None) -> dict:
    if not giris or not cikis:
        return {
            "giris": giris,
            "cikis": cikis,
            "aralik": "—",
            "sure": "—",
            "dakika": None,
            "gece_vardiyasi": False,
            "segmentler": [],
            "baslangic_yuzde": 0,
            "genislik_yuzde": 0,
        }

    segmentler = mesai_timeline_segmentleri(giris, cikis)
    dakika = mesai_suresi_dakika(giris, cikis)

    return {
        "giris": giris,
        "cikis": cikis,
        "aralik": mesai_aralik_metin(giris, cikis),
        "sure": mesai_suresi_metin(giris, cikis),
        "dakika": dakika,
        "gece_vardiyasi": gece_vardiyasi(giris, cikis),
        "segmentler": segmentler,
        "baslangic_yuzde": segmentler[0]["sol"] if segmentler else 0,
        "genislik_yuzde": segmentler[0]["genislik"] if segmentler else 0,
    }
