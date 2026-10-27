"""Clasifica una fila de la auditoría. No pinta y no toca la base."""

_SIN_ID = ("", "—", "-", "F9 MANUAL")
_SIN_CUENTA = ("", "—", "-", "MP")

_ETIQUETAS = {
    "cruzado": "Cruzados",
    "ticket_sin_id": "Ticket sin id",
    "id_sin_ticket": "Id sin ticket",
}


def clase_cruce(fila) -> str:
    """cruzado, ticket_sin_id o id_sin_ticket. El id es el de Mercado Pago."""
    datos = fila or {}
    pid = str(datos.get("id") or "").strip()
    tiene_id = pid not in _SIN_ID
    tv = str(datos.get("ticket_venta") or "").strip()
    tc = str(datos.get("ticket_cobro") or "").strip()
    tiene_ticket = tv not in ("", "—", "-") or tc not in ("", "—", "-")
    if tiene_ticket and tiene_id:
        return "cruzado"
    if tiene_ticket:
        return "ticket_sin_id"
    if tiene_id:
        return "id_sin_ticket"
    return ""


def pasa(fila, cruce: str, cuenta: str) -> bool:
    if cruce and cruce != "Todos" and clase_cruce(fila) != cruce:
        return False
    if cuenta and str((fila or {}).get("cuenta") or "").strip() != cuenta:
        return False
    return True


def entra_en_reparto(fila) -> bool:
    return clase_cruce(fila) in ("cruzado", "id_sin_ticket")


def texto_boton(cruce: str, cuenta: str) -> str:
    partes = []
    if cruce in _ETIQUETAS:
        partes.append(_ETIQUETAS[cruce])
    if cuenta:
        partes.append(cuenta)
    if not partes:
        return "Filtros"
    return "Filtros · " + " · ".join(partes)


def sumar_cuentas(filas) -> list[tuple[str, float]]:
    """Monto MP por titular, en el orden en que aparecen. Sin id no suma."""
    acum = {}
    orden = []
    for fila in filas or []:
        if not entra_en_reparto(fila):
            continue
        cuenta = str((fila or {}).get("cuenta") or "").strip()
        if cuenta in _SIN_CUENTA:
            continue
        if cuenta not in acum:
            orden.append(cuenta)
            acum[cuenta] = 0.0
        acum[cuenta] += float((fila or {}).get("monto_mp") or 0)
    return [(nombre, acum[nombre]) for nombre in orden]
