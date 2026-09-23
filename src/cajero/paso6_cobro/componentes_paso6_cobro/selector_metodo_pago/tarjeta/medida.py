"""Tamaño de la tarjeta y de la hoja. El gris de afuera no se toca."""

BARRA = 72
PIE = 88
SEPARACION = 24
AIRE = 44
RELLENO = 56
HOLGURA = 16


def medida_hoja(panel_w, panel_h):
    """La hoja deja aire alrededor de las tarjetas para que el borde no se corte."""
    tope_w = max(680, panel_w - 24)
    tope_h = max(540, panel_h - 16)
    ancho = min(280, (tope_w - RELLENO * 2 - SEPARACION * 2 - HOLGURA) // 3)
    alto = min(220, (tope_h - BARRA - PIE - AIRE * 2 - SEPARACION - HOLGURA) // 2)
    ancho = max(180, ancho)
    alto = max(160, alto)

    hoja_w = RELLENO * 2 + ancho * 3 + SEPARACION * 2 + HOLGURA
    hoja_h = BARRA + AIRE + alto + SEPARACION + alto + AIRE + PIE + HOLGURA
    if hoja_w > tope_w:
        ancho = max(160, (tope_w - RELLENO * 2 - SEPARACION * 2 - HOLGURA) // 3)
        hoja_w = RELLENO * 2 + ancho * 3 + SEPARACION * 2 + HOLGURA
    if hoja_h > tope_h:
        alto = max(148, (tope_h - BARRA - PIE - AIRE * 2 - SEPARACION - HOLGURA) // 2)
        hoja_h = BARRA + AIRE + alto + SEPARACION + alto + AIRE + PIE + HOLGURA

    return {
        "ancho": ancho,
        "alto": alto,
        "sep": SEPARACION,
        "aire": AIRE,
        "hoja_w": hoja_w,
        "hoja_h": hoja_h,
    }
