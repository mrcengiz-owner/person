from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def format_para(value, *, decimals: int = 2, suffix: str = " ₺") -> str:
    """Türkçe para biçimi: 30000 -> 30.000,00 ₺"""
    if value is None or value == "":
        return "—"

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)

    sign = ""
    if amount < 0:
        sign = "− "
        amount = abs(amount)

    quant = Decimal("1").scaleb(-decimals)
    amount = amount.quantize(quant, rounding=ROUND_HALF_UP)

    parts = f"{amount:.{decimals}f}".split(".")
    integer = parts[0]
    fractional = parts[1] if len(parts) > 1 else ("0" * decimals)

    if len(integer) > 3:
        groups = []
        while integer:
            groups.append(integer[-3:])
            integer = integer[:-3]
        integer = ".".join(reversed(groups))

    formatted = f"{integer},{fractional}"
    if suffix:
        formatted += suffix
    return sign + formatted
