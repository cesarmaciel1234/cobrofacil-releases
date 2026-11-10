"""Lectura del historial de cuenta. No escribe. Si falla, devuelve lista vacía."""

from __future__ import annotations

from src.clientes_fiado.oficina.cuenta.motor import (
    MARCA_BORRADO, MARCA_CANCELADO, cargo_borrado, cargo_cancelado, _ficha, _celda,
)
from src.clientes_fiado.oficina.cuenta.interes import (
    MARCA_INTERES,
    clave_ticket,
)
from src.logger import logger


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
    es_venta = bool(venta_id and str(venta_id) not in ("0", "None", ""))
    es_manual = (tipo == "CARGO" and not es_venta)

    if tipo == "CARGO" and es_venta:
        if cancelado:
            etiqueta = "VENTA · CANCELADA"
        elif borrado:
            etiqueta = "VENTA · BORRADA"
        else:
            etiqueta = "VENTA"
    elif tipo == "CARGO" and es_manual:
        if cancelado:
            etiqueta = "CARGO MANUAL · CANCELADO"
        elif borrado:
            etiqueta = "CARGO MANUAL · BORRADO"
        else:
            etiqueta = "CARGO MANUAL"
    elif tipo == "ABONO":
        etiqueta = "COBRO"
    elif tipo == "ANULACION" and "cancelado" in desc.lower():
        etiqueta = "TICKET CANCELADO"
    elif tipo == "ANULACION":
        etiqueta = "ANULACIÓN"
    else:
        etiqueta = tipo or "—"
    ref = _referencia(tipo, venta_id, mov_id)
    ticket = clave_ticket(dato)
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
        "es_interes": tipo == "CARGO" and desc.startswith(MARCA_INTERES),
        "ticket_key": ticket,
        "interes_acumulado": 0.0,
        "interes_en_saldo": 0.0,
        "dias_interes": 0,
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
            logger.exception(
                "[Historial clientes] No se pudieron leer movimientos del cliente %s",
                cliente_id,
            )
            return []
        try:
            proyeccion = MotorCuenta().proyeccion_interes(crudas)
            tickets = proyeccion["tickets"]
            error_interes = ""
        except Exception as error:
            logger.exception(
                "[Historial clientes] No se pudo calcular interés del cliente %s",
                cliente_id,
            )
            tickets = {}
            error_interes = str(error)
        salida = []
        try:
            from src.clientes_fiado.oficina.barrial.mantenimiento import _deuda_escribible
            deuda_real = _deuda_escribible(cliente_id)
            if deuda_real is None:
                from src.clientes_fiado.cerebro.cerebro import cerebro
                deuda_real = float((cerebro.obtener(cliente_id) or {}).get("deuda_actual") or 0)
        except Exception:
            deuda_real = 0.0

        for fila in crudas:
            try:
                dato = armar_fila(fila)
                if "MANTENIMIENTO" in (dato.get("descripcion") or "").upper():
                    continue
                # Si el cliente ya pagó el total o tiene saldo a favor, no acumula interés
                if dato["ticket_key"] in tickets and deuda_real > 0.009:
                    interes = tickets[dato["ticket_key"]]
                    dato["interes_acumulado"] = interes["interes_acumulado"]
                    dato["interes_en_saldo"] = interes["interes_en_saldo"]
                    dato["dias_interes"] = interes["dias"]
                    if dato["tipo"] == "CARGO" and interes["interes_acumulado"] > 0:
                        dato["linea"] += (
                            f"  · interés nuevo ${interes['interes_acumulado']:,.2f}"
                            f" · {interes['dias']} d"
                        )
                else:
                    dato["interes_acumulado"] = 0.0
                    dato["interes_en_saldo"] = 0.0
                    dato["dias_interes"] = 0
                dato["error_interes"] = error_interes
                salida.append(dato)
            except Exception:
                logger.exception(
                    "[Historial clientes] No se pudo preparar un movimiento del cliente %s",
                    cliente_id,
                )
                continue
        return salida


motor_consulta_historial = MotorConsultaHistorial()
