"""Montos de cobro: 2 decimales (Decimal, half-up)."""
from decimal import Decimal, ROUND_HALF_UP


def redondear_dinero(valor) -> float:
    try:
        d = Decimal(str(valor if valor is not None else 0))
        return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except (TypeError, ValueError, ArithmeticError):
        return 0.0


def redondear_items_carrito(items):
    out = []
    for it in items or []:
        fila = dict(it)
        cant = float(fila.get("cant") or 0)
        precio = redondear_dinero(fila.get("precio"))
        sub = fila.get("subtotal")
        if sub is None:
            sub = cant * precio
        fila["precio"] = precio
        fila["cant"] = cant
        fila["subtotal"] = redondear_dinero(sub)
        out.append(fila)
    return out
