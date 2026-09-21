def fmt_moneda(val):
    try:
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"${val}"


def fecha_a_texto(fecha_val):
    if fecha_val is None:
        return ""
    if hasattr(fecha_val, "strftime"):
        return fecha_val.strftime("%Y-%m-%d %H:%M:%S")
    return str(fecha_val)
