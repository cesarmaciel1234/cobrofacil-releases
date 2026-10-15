"""Lectura del historial de cuenta. No escribe. Si falla, devuelve lista vacía."""

from __future__ import annotations

from src.clientes_fiado.oficina.cuenta.motor import (
    MARCA_BORRADO, MARCA_CANCELADO, cargo_borrado, cargo_cancelado, _ficha, _celda,
)


def _fila_cruda(fila) -> dict:
    ficha = _ficha(fila)
    if ficha:
        return ficha
    claves = ("id", "fecha", "tipo", "monto", "saldo_resultante", "descripcion", "venta_id")
    try:
        return dict(zip(claves, fila))
    except Exception:
        return {}


def _float(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _referencia(tipo: str, venta_id, mov_id) -> str:
    if venta_id not in (None, "", 0, "0"):
        return f"#{venta_id}"
    if tipo == "ABONO" and mov_id:
        try:
            from src.motor_auditoria_digital.consultas.ids import ticket_cobro

            return ticket_cobro(mov_id)
        except Exception:
            return f"COB-{mov_id}"
    return ""


def armar_fila(fila) -> dict:
    dato = _fila_cruda(fila)
    tipo = str(dato.get("tipo") or _celda(fila, "tipo", 2) or "").upper()
    desc = str(dato.get("descripcion") or "").strip()
    borrado = tipo == "CARGO" and cargo_borrado(desc)
    cancelado = tipo == "CARGO" and cargo_cancelado(desc)
    mov_id = dato.get("id")
    if mov_id is None:
        mov_id = _celda(fila, "id", 0)
    venta_id = dato.get("venta_id")
    if venta_id is None:
        venta_id = _celda(fila, "venta_id", 6)
    if tipo == "CARGO" and cancelado:
        etiqueta = "CARGO · CANCELADO"
    elif tipo == "CARGO" and borrado:
        etiqueta = "CARGO · BORRADO"
    elif tipo == "ANULACION" and "cancelado" in desc.lower():
        etiqueta = "TICKET CANCELADO"
    elif tipo == "ANULACION":
        etiqueta = "ANULACIÓN"
    else:
        etiqueta = tipo or "—"
    ref = _referencia(tipo, venta_id, mov_id)
    return {
        "id": mov_id,
        "fecha": str(dato.get("fecha") or ""),
        "tipo": tipo,
        "monto": _float(dato.get("monto")),
        "saldo_resultante": _float(dato.get("saldo_resultante")),
        "descripcion": desc,
        "venta_id": str(venta_id) if venta_id not in (None, "", 0, "0") else "",
        "borrado": borrado,
        "cancelado": cancelado,
        "manual": tipo == "CARGO" and not venta_id,
        "referencia": ref,
        "etiqueta": etiqueta,
        "linea": (
            f"{etiqueta} ${_float(dato.get('monto')):,.2f}"
            + (f"  {ref}" if ref else "")
            + ("  · queda en el historial" if (borrado or cancelado) else "")
        ),
        "marca_borrado": MARCA_BORRADO,
        "marca_cancelado": MARCA_CANCELADO,
    }


class MotorConsultaHistorial:
    """Pregunta al libro de cuenta. Un fallo acá no tumba cobro ni ficha."""

    def movimientos(self, cliente_id) -> list[dict]:
        if not cliente_id:
            return []
        try:
            from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

            crudas = MotorCuenta().movimientos(cliente_id) or []
        except Exception:
            return []
        salida = []
        for fila in crudas:
            try:
                salida.append(armar_fila(fila))
            except Exception:
                continue
        return salida


motor_consulta_historial = MotorConsultaHistorial()
