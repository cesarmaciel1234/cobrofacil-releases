"""Tres números. No se mezclan.

Ticket de venta  → `ventas.id`                   ej. 1090135     qué se vendió
Ticket de cobro  → COB-{cuenta_corriente.id}     ej. COB-98      abono F6
Id de pago       → Mercado Pago, o F9 MANUAL     ej. 1826789…    cómo entró la plata
"""


def ticket_venta(nro):
    texto = str(nro or "").strip()
    if not texto or texto in ("—", "-") or texto.upper().startswith("COB-"):
        return ""
    return texto


def ticket_cobro(nro):
    texto = str(nro or "").strip()
    if not texto or texto in ("—", "-"):
        return ""
    if texto.upper().startswith("COB-"):
        return "COB-" + texto.split("-", 1)[-1]
    return f"COB-{texto}"


def es_cobro(codigo):
    return str(codigo or "").upper().startswith("COB-")


def id_pago(pago_id, f9=False):
    pid = str(pago_id or "").strip()
    if pid and pid not in ("—", "-", "F9 MANUAL"):
        return pid
    if f9:
        return "F9 MANUAL"
    return ""
