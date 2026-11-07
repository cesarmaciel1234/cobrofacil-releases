"""Promesa de pago barrial: una fecha acordada + nota corta."""

from datetime import datetime


def _parse_fecha(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    texto = str(valor).strip()[:10]
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def fecha_de(cliente):
    if not cliente:
        return None
    ficha = dict(cliente) if not isinstance(cliente, dict) else cliente
    return _parse_fecha(ficha.get("promesa_fecha"))


def nota_de(cliente) -> str:
    if not cliente:
        return ""
    ficha = dict(cliente) if not isinstance(cliente, dict) else cliente
    return str(ficha.get("promesa_nota") or "").strip()


def vencida(cliente, hoy=None) -> bool:
    """True si hay promesa con fecha anterior a hoy."""
    fecha = fecha_de(cliente)
    if fecha is None:
        return False
    if hoy is None:
        hoy = datetime.now().date()
    elif isinstance(hoy, datetime):
        hoy = hoy.date()
    return fecha < hoy


def fijar(cliente_id, fecha, nota="") -> bool:
    """Guarda promesa. `fecha` = YYYY-MM-DD o date/datetime. Auditoría PROMESA."""
    from src.clientes_fiado.oficina.huella.eventos import editar, limpio

    dt = _parse_fecha(fecha)
    if dt is None:
        return False
    return bool(
        editar(
            cliente_id,
            {
                "promesa_fecha": dt.strftime("%Y-%m-%d"),
                "promesa_nota": limpio(nota, 120) or None,
            },
            accion="PROMESA",
        )
    )


def limpiar(cliente_id) -> bool:
    """Quita promesa. Auditoría PROMESA."""
    from src.clientes_fiado.oficina.huella.eventos import editar

    return bool(
        editar(
            cliente_id,
            {"promesa_fecha": None, "promesa_nota": None},
            accion="PROMESA",
        )
    )
