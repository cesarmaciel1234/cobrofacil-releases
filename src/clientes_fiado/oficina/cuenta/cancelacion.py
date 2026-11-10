"""Reversos de cartera asociados a la cancelación F3 y su sincronización offline."""

import json
import re
from decimal import Decimal, ROUND_HALF_UP

from src.clientes_fiado.oficina.cuenta.interes import (
    clave_ticket,
    descripcion_reverso,
    proyectar_interes,
)
from src.clientes_fiado.oficina.cuenta.motor import (
    MARCA_CANCELADO,
    cargo_inactivo,
    fecha_activacion_cursor,
    fecha_db_cursor,
    movimientos_cursor,
)


def _celda(fila, clave, indice=0):
    if fila is None:
        return None
    try:
        return fila[clave]
    except (KeyError, TypeError, IndexError):
        try:
            return fila[indice]
        except (KeyError, TypeError, IndexError):
            return None


def _cargo_de_ticket(cursor, id_venta):
    cursor.execute(
        "SELECT id, cliente_id, monto, descripcion, venta_id FROM cuenta_corriente "
        "WHERE tipo = 'CARGO' AND venta_id IN (?, ?) ORDER BY id DESC LIMIT 1",
        (id_venta, str(id_venta)),
    )
    cargo = cursor.fetchone()
    if cargo:
        return cargo
    n = str(int(id_venta))
    cursor.execute(
        "SELECT id, cliente_id, monto, descripcion, venta_id FROM cuenta_corriente "
        "WHERE tipo = 'CARGO' AND (descripcion LIKE ? OR descripcion LIKE ? "
        "OR descripcion LIKE ? OR descripcion LIKE ?) ORDER BY id DESC LIMIT 1",
        (f"%Ticket #{n}", f"%Ticket #{n} %", f"%Ticket #{n} (%", f"%ticket #{n}"),
    )
    return cursor.fetchone()


def anular_cargo_f3(cursor, id_venta):
    """Revierte capital e interés del ticket, y registra el movimiento de cartera."""
    cargo = _cargo_de_ticket(cursor, id_venta)
    if not cargo:
        return
    cliente_id = _celda(cargo, "cliente_id", 1)
    cargo_id = _celda(cargo, "id", 0)
    descripcion_cargo = str(_celda(cargo, "descripcion", 3) or "").strip()
    try:
        monto = float(_celda(cargo, "monto", 2) or 0)
    except (TypeError, ValueError):
        monto = 0.0
    cursor.execute(
        "SELECT id FROM cuenta_corriente WHERE venta_id IN (?, ?) "
        "AND tipo = 'ANULACION' LIMIT 1",
        (id_venta, str(id_venta)),
    )
    ya_anulado = bool(cursor.fetchone())
    if ya_anulado or not cliente_id or monto <= 0:
        if cargo_id and not cargo_inactivo(descripcion_cargo):
            cursor.execute(
                "UPDATE cuenta_corriente SET descripcion = ? WHERE id = ?",
                (f"{MARCA_CANCELADO}{descripcion_cargo or f'Ticket #{id_venta}'}", cargo_id),
            )
        return

    bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
    cursor.execute(
        f"SELECT deuda_actual FROM clientes WHERE id = ?{bloqueo}",
        (cliente_id,),
    )
    deuda = float(_celda(cursor.fetchone(), "deuda_actual", 0) or 0)
    ahora = fecha_db_cursor(cursor)
    historial = movimientos_cursor(cursor, cliente_id)
    activacion = fecha_activacion_cursor(cursor, ahora=ahora, crear=True)
    proyeccion = proyectar_interes(historial, activacion, ahora=ahora)
    ticket = clave_ticket(cargo)
    estado_ticket = proyeccion["tickets"].get(ticket)
    if estado_ticket is None:
        raise ValueError(f"No se pudo verificar el ticket fiado #{id_venta}")
    interes_generado = Decimal(str(estado_ticket["interes_generado"]))
    anulacion = float(
        (Decimal(str(monto)) + interes_generado).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )
    nota = f"Ticket cancelado #{id_venta} (F3)"
    if interes_generado > 0:
        nota += " · " + descripcion_reverso(ticket, interes_generado)
    if cargo_id and not cargo_inactivo(descripcion_cargo):
        cursor.execute(
            "UPDATE cuenta_corriente SET descripcion = ? WHERE id = ?",
            (f"{MARCA_CANCELADO}{descripcion_cargo or f'Ticket #{id_venta}'}", cargo_id),
        )
    nuevo_saldo = deuda - anulacion
    cursor.execute(
        "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
        (nuevo_saldo, cliente_id),
    )
    cursor.execute(
        "INSERT INTO cuenta_corriente "
        "(cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
        "VALUES (?, 'ANULACION', ?, ?, ?, ?)",
        (cliente_id, anulacion, nuevo_saldo, nota, id_venta),
    )
    try:
        from src.clientes_fiado.oficina.huella.eventos import movimiento_en

        movimiento_en(
            cursor,
            "ANULACION",
            cliente_id,
            anulacion,
            nota,
            extra={"venta_id": id_venta, "cargo_id": cargo_id, "cancelacion_f3": True},
        )
    except Exception:
        pass


def encolar_f3_offline(
    cursor,
    id_venta,
    username,
    request_id,
    cancelado_por,
    fecha_cancel,
    perfil_cancel,
    caja_cancel,
    movimientos_caja,
):
    """Guarda el reverso de cartera junto a la referencia de la venta para reintento."""
    cursor.execute(
        "SELECT monto, descripcion FROM cuenta_corriente "
        "WHERE venta_id IN (?, ?) AND tipo = 'ANULACION' ORDER BY id DESC LIMIT 1",
        (id_venta, str(id_venta)),
    )
    reversion = cursor.fetchone()
    cursor.execute(
        "INSERT OR REPLACE INTO offline_cancelaciones "
        "(local_venta_id, request_id, cancelado_por, fecha_cancel, perfil_cancel, "
        "caja_cancel, cuenta_monto, cuenta_descripcion, movimientos_caja_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            id_venta,
            request_id,
            cancelado_por or username,
            fecha_cancel,
            perfil_cancel,
            caja_cancel,
            _celda(reversion, "monto", 0) if reversion else 0,
            _celda(reversion, "descripcion", 1) if reversion else "",
            json.dumps(movimientos_caja, ensure_ascii=True, separators=(",", ":")),
        ),
    )


def sincronizar_f3_offline(
    db_manager,
    local_venta_id,
    request_id,
    username,
    fecha_cancel,
    perfil_cancel,
    caja_cancel,
    cuenta_monto=0,
    cuenta_descripcion="",
    movimientos_caja_json=None,
):
    """Aplica cartera y delega a ventas el estado, stock y caja en una transacción."""
    if (
        getattr(db_manager, "db_engine_type", "sqlite") != "mariadb"
        or getattr(db_manager, "_forced_local_offline", False)
    ):
        return False
    conn = None
    try:
        movimientos_caja = None
        if movimientos_caja_json is not None:
            movimientos_caja = (
                json.loads(movimientos_caja_json)
                if isinstance(movimientos_caja_json, str)
                else movimientos_caja_json
            )
            campos = ("fecha", "tipo", "monto", "usuario", "observaciones", "caja_id")
            if not isinstance(movimientos_caja, list) or any(
                not isinstance(movimiento, dict)
                or any(campo not in movimiento for campo in campos)
                for movimiento in movimientos_caja
            ):
                raise ValueError("Movimientos de caja offline inválidos")
        conn = db_manager.get_connection(caer_si_maestra_caida=False)
        cursor = conn.cursor()
        if request_id:
            cursor.execute("SELECT id, estado FROM ventas WHERE request_id = ?", (request_id,))
        else:
            cursor.execute("SELECT id, estado FROM ventas WHERE id = ?", (local_venta_id,))
        venta = cursor.fetchone()
        if not venta:
            return False
        venta_id = _celda(venta, "id", 0)
        estado = str(_celda(venta, "estado", 1) or "").upper()
        cancelada = estado in ("CANCELADA", "CANCELADO", "ANULADA", "ANULADO")
        cursor.execute(
            "SELECT id FROM cuenta_corriente WHERE tipo = 'ANULACION' "
            "AND venta_id IN (?, ?) LIMIT 1",
            (venta_id, str(venta_id)),
        )
        if not cursor.fetchone() and float(cuenta_monto or 0) > 0:
            cargo = _cargo_de_ticket(cursor, venta_id)
            if not cargo:
                conn.rollback()
                return False
            cliente_id = _celda(cargo, "cliente_id", 1)
            if not cliente_id:
                conn.rollback()
                return False
            cursor.execute("SELECT deuda_actual FROM clientes WHERE id = ?", (cliente_id,))
            deuda = float(_celda(cursor.fetchone(), "deuda_actual", 0) or 0)
            from src.clientes_fiado.oficina.huella.absorber import _remapear_reverso

            descripcion = str(cuenta_descripcion or f"Ticket cancelado #{local_venta_id}")
            descripcion = re.sub(
                rf"(?<!\d)#{re.escape(str(local_venta_id))}\b",
                f"#{venta_id}",
                descripcion,
            )
            descripcion = _remapear_reverso(
                descripcion,
                {f"V:{local_venta_id}": f"V:{venta_id}"},
            )
            cargo_id = _celda(cargo, "id", 0)
            cargo_desc = str(_celda(cargo, "descripcion", 3) or "")
            if not cargo_desc.startswith((MARCA_CANCELADO, "BORRADO · ")):
                cursor.execute(
                    "UPDATE cuenta_corriente SET descripcion = ? WHERE id = ?",
                    (f"{MARCA_CANCELADO}{cargo_desc or f'Ticket #{venta_id}'}", cargo_id),
                )
            nuevo_saldo = deuda - float(cuenta_monto)
            cursor.execute(
                "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                (nuevo_saldo, cliente_id),
            )
            cursor.execute(
                "INSERT INTO cuenta_corriente "
                "(cliente_id, fecha, tipo, monto, saldo_resultante, descripcion, venta_id) "
                "VALUES (?, ?, 'ANULACION', ?, ?, ?, ?)",
                (
                    cliente_id,
                    fecha_cancel,
                    cuenta_monto,
                    nuevo_saldo,
                    descripcion,
                    venta_id,
                ),
            )
        if not cancelada:
            from src.base_de_datos.repos.ventas import marcar_ticket_cancelado

            if not marcar_ticket_cancelado(
                cursor,
                venta_id,
                username,
                anular_cargo=False,
                devolver_stock=True,
                fecha_cancel=fecha_cancel,
                perfil_cancel=perfil_cancel,
                caja_cancel=caja_cancel,
                movimientos_caja=movimientos_caja,
            ):
                conn.rollback()
                return False
        conn.commit()
        return True
    except Exception as error:
        if conn:
            conn.rollback()
        from src.logger import logger

        logger.warning(
            "No se pudo sincronizar la cancelación F3 de cartera %s: %s",
            local_venta_id,
            error,
        )
        return False
    finally:
        if conn:
            conn.close()
