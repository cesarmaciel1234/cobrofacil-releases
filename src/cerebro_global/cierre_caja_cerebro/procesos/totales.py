"""Consultas de totales COMPLETADA para el panel de cierre.

Este módulo calcula los totales de ventas, pagos y movimientos de caja
para el panel de cierre de caja (cierre Z/X).

Funciones principales:
    - obtener_datos_cierre: Totales completos del turno
    - _ultima_apertura: Fecha y monto de la última apertura de caja
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _empty() -> dict:
    return {
        "fondo": 0.0,
        "v_efectivo": 0.0,
        "v_tarjeta": 0.0,
        "v_trans": 0.0,
        "v_credito": 0.0,
        "v_vales": 0.0,
        "v_cheque": 0.0,
        "v_totales": 0.0,
        "v_caja_total": 0.0,
        "ganancia_estimada": 0.0,
        "entradas_efectivo": 0.0,
        "salidas_efectivo": 0.0,
        "abonos_efectivo": 0.0,
        "devoluciones_efectivo": 0.0,
        "apertura_fecha": None,
    }


def _ultima_apertura(
    db: Any,
    caja_id: int | None = None,
    cajero: str | None = None,
) -> tuple[float, str | None]:
    cond = "tipo='APERTURA'"
    params: list = []
    if cajero:
        cond += " AND usuario = ?"
        params.append(cajero)
    if caja_id is not None:
        cond += " AND caja_id = ?"
        params.append(caja_id)
    row = db.execute_query(
        f"SELECT monto, fecha FROM movimientos_caja WHERE {cond} ORDER BY id DESC LIMIT 1",
        tuple(params),
    )
    if not row:
        return 0.0, None
    return float(row[0].get("monto") or 0.0), str(row[0].get("fecha") or "") or None


def obtener_datos_cierre(
    fecha_str: str | None = None,
    cajero: str | None = None,
    caja_id: int | None = None,
    db: Any = None,
) -> dict:
    """
    Totales de ventas COMPLETADA del turno (desde última APERTURA).
    Si no hay apertura, filtra por día calendario (fecha_str).
    Esperado de arqueo (v_caja_total) = get_efectivo_en_caja cuando hay caja_id.
    """
    if db is None:
        from src.base_de_datos.database import db_manager as db

    try:
        from src.cerebro_global.cierre_caja_cerebro.procesos.esperado import (
            efectivo_esperado_caja,
            movimientos_turno,
        )
        from src.cerebro_global.cierre_caja_cerebro.procesos.diferencias import (
            calcular_diferencia_mes,
            calcular_diferencia_historica,
        )

        target_day = fecha_str or datetime.now().strftime("%Y-%m-%d")
        fondo, apertura_fecha = _ultima_apertura(db, caja_id=caja_id, cajero=cajero)

        # Ventas pendientes de cierre:
        # - Si se selecciona una fecha específica, usar esa fecha (ignorar apertura)
        # - Si no hay fecha específica (hoy), usar desde apertura o inicio del día
        if fecha_str and fecha_str != datetime.now().strftime("%Y-%m-%d"):
            # Fecha específica seleccionada: usar todo el día (incluye CERRADAS para historial)
            desde = f"{target_day} 00:00:00"
            hasta = f"{target_day} 23:59:59"
            v_cond = "estado IN ('COMPLETADA', 'CERRADA') AND fecha >= ? AND fecha <= ?"
            v_params: list = [desde, hasta]
        else:
            # Hoy o sin fecha: desde apertura o inicio del día (solo COMPLETADAS para cierre activo)
            desde = apertura_fecha or f"{target_day} 00:00:00"
            v_cond = "estado = 'COMPLETADA' AND fecha >= ?"
            v_params: list = [desde]
        if cajero:
            v_cond += " AND usuario = ?"
            v_params.append(cajero)
        if caja_id is not None:
            v_cond += " AND caja_id = ?"
            v_params.append(caja_id)

        # Efectivo neto en cajón: bruto recibido − vuelto (solo Efectivo/Mixto)
        v_efectivo = float(
            db.execute_scalar(
                f"""SELECT SUM(
                    CASE
                        WHEN metodo_pago IN ('Efectivo', 'Mixto')
                             OR UPPER(COALESCE(metodo_pago, '')) LIKE '%EFECTIVO%'
                        THEN COALESCE(pago_efectivo, 0)
                             - CASE WHEN COALESCE(cambio, 0) > 0 THEN COALESCE(cambio, 0) ELSE 0 END
                        ELSE 0
                    END
                ) FROM ventas WHERE {v_cond}""",
                tuple(v_params),
            )
            or 0.0
        )

        v_tarjeta = float(
            db.execute_scalar(
                f"SELECT SUM(total) FROM ventas WHERE {v_cond} AND metodo_pago LIKE '%Tarjeta%'",
                tuple(v_params),
            )
            or 0.0
        )
        # Parte no-efectivo de Mixto (suele ser tarjeta/QR)
        v_mixto_otro = float(
            db.execute_scalar(
                f"SELECT SUM(COALESCE(pago_otro, 0)) FROM ventas WHERE {v_cond} AND metodo_pago = 'Mixto'",
                tuple(v_params),
            )
            or 0.0
        )
        v_tarjeta += v_mixto_otro

        v_trans = float(
            db.execute_scalar(
                f"SELECT SUM(total) FROM ventas WHERE {v_cond} AND metodo_pago = 'Transferencia'",
                tuple(v_params),
            )
            or 0.0
        )

        v_credito = float(
            db.execute_scalar(
                f"SELECT SUM(total) FROM ventas WHERE {v_cond} AND metodo_pago = 'Fiado'",
                tuple(v_params),
            )
            or 0.0
        )

        v_totales = float(
            db.execute_scalar(
                f"SELECT SUM(total) FROM ventas WHERE {v_cond}",
                tuple(v_params),
            )
            or 0.0
        )

        entradas, salidas = movimientos_turno(caja_id, desde, db=db)

        # Abonos de clientes desglosados por método de pago
        pago_cond = "tipo = 'INGRESO' AND observaciones LIKE ? AND fecha >= ?"
        pago_params: list = ["Pago de clientes%", desde]
        if caja_id is not None:
            pago_cond += " AND caja_id = ?"
            pago_params.append(caja_id)

        # Total abonos
        abonos_efectivo = float(
            db.execute_scalar(
                f"SELECT SUM(monto) FROM movimientos_caja WHERE {pago_cond}",
                tuple(pago_params),
            )
            or 0.0
        )

        # Abonos por método de pago (desde observaciones del movimiento)
        abonos_transferencia = float(
            db.execute_scalar(
                f"SELECT SUM(monto) FROM movimientos_caja WHERE {pago_cond} AND (observaciones LIKE '%Transferencia%' OR observaciones LIKE '%Transf%')",
                tuple(pago_params),
            )
            or 0.0
        )

        abonos_digital = float(
            db.execute_scalar(
                f"SELECT SUM(monto) FROM movimientos_caja WHERE {pago_cond} AND (observaciones LIKE '%QR%' OR observaciones LIKE '%Digital%' OR observaciones LIKE '%MercadoPago%')",
                tuple(pago_params),
            )
            or 0.0
        )

        # El resto de abonos se asume efectivo
        abonos_efectivo_detalle = abonos_efectivo - abonos_transferencia - abonos_digital

        dev_cond = "tipo = 'RETIRO' AND observaciones LIKE ? AND fecha >= ?"
        dev_params: list = ["Devolución ticket #%", desde]
        if caja_id is not None:
            dev_cond += " AND caja_id = ?"
            dev_params.append(caja_id)
        devoluciones_efectivo = float(
            db.execute_scalar(
                f"SELECT SUM(monto) FROM movimientos_caja WHERE {dev_cond}",
                tuple(dev_params),
            )
            or 0.0
        )

        if caja_id is not None:
            v_caja_total = efectivo_esperado_caja(caja_id, db=db)
        else:
            v_caja_total = fondo + v_efectivo + entradas - salidas

        ganancia_estimada = v_totales * 0.30

        # Calcular diferencias del mes e histórica usando el módulo especializado
        diferencia_mes = calcular_diferencia_mes(caja_id=caja_id, db=db)
        diferencia_historica = calcular_diferencia_historica(caja_id=caja_id, db=db)

        return {
            "fondo": fondo,
            "v_efectivo": v_efectivo,
            "v_tarjeta": v_tarjeta,
            "v_trans": v_trans,
            "v_credito": v_credito,
            "v_vales": 0.0,
            "v_cheque": 0.0,
            "v_totales": v_totales,
            "v_caja_total": v_caja_total,
            "ganancia_estimada": ganancia_estimada,
            "entradas_efectivo": entradas,
            "salidas_efectivo": salidas,
            "abonos_efectivo": abonos_efectivo,
            "abonos_efectivo_detalle": abonos_efectivo_detalle,
            "abonos_transferencia": abonos_transferencia,
            "abonos_digital": abonos_digital,
            "devoluciones_efectivo": devoluciones_efectivo,
            "apertura_fecha": apertura_fecha or desde,
            "diferencia_mes": diferencia_mes,
            "diferencia_historica": diferencia_historica,
        }
    except Exception as e:
        print(f"Error en totales cierre: {e}")
        return _empty()
