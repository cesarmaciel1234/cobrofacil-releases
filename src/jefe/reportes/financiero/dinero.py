"""Montos que se pueden firmar (AR)."""


def fmt_plata(n: float) -> str:
    try:
        v = float(n or 0)
    except (TypeError, ValueError):
        v = 0.0
    neg = v < 0
    v = abs(v)
    entero = int(v)
    dec = int(round((v - entero) * 100))
    if dec == 100:
        entero += 1
        dec = 0
    cuerpo = f"{entero:,}".replace(",", ".")
    txt = f"${cuerpo},{dec:02d}"
    return f"-{txt}" if neg else txt


def fmt_entero(n: int) -> str:
    return f"{int(n or 0):,}".replace(",", ".")


def pct_vs(actual: float, anterior: float) -> str:
    if anterior <= 0:
        if actual > 0:
            return "+100%"
        return "sin dato"
    d = (actual - anterior) / anterior * 100
    signo = "+" if d >= 0 else ""
    return f"{signo}{d:.1f}%"
