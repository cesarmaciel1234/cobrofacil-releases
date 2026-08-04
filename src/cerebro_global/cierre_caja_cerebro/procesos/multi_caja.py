"""Resumen multi-caja (estilo cadena: una caja = un arqueo)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.cerebro_global.cierre_caja_cerebro.procesos.totales import obtener_datos_cierre


def listar_caja_ids(db: Any = None, max_fallback: int = 10) -> list[int]:
    """IDs de caja vistos en movimientos/ventas + config local."""
    if db is None:
        from src.base_de_datos.database import db_manager as db

    found: set[int] = set()
    try:
        from src.config import config

        found.add(int(config.get("caja_id", 1) or 1))
    except Exception:
        found.add(1)

    for sql in (
        "SELECT DISTINCT caja_id FROM movimientos_caja WHERE caja_id IS NOT NULL",
        "SELECT DISTINCT caja_id FROM ventas WHERE caja_id IS NOT NULL",
    ):
        try:
            rows = db.execute_query(sql, ()) or []
            for r in rows:
                try:
                    cid = int(r.get("caja_id") or 0)
                    if cid > 0:
                        found.add(cid)
                except (TypeError, ValueError):
                    continue
        except Exception:
            continue

    if not found:
        found = set(range(1, min(max_fallback, 3) + 1))
    return sorted(found)


def estado_caja(caja_id: int, db: Any = None) -> dict:
    """ABIERTA si el último mov relevante es APERTURA; si no, CERRADA."""
    if db is None:
        from src.base_de_datos.database import db_manager as db

    row = db.execute_query(
        "SELECT tipo, usuario, fecha, monto FROM movimientos_caja "
        "WHERE caja_id = ? AND tipo IN ('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO', 'CIERRE_TURNO') "
        "ORDER BY id DESC LIMIT 1",
        (int(caja_id),),
    )
    if not row:
        return {
            "caja_id": int(caja_id),
            "estado": "SIN_MOV",
            "usuario": None,
            "fecha": None,
            "fondo": 0.0,
        }
    tipo = str(row[0].get("tipo") or "")
    abierta = tipo == "APERTURA"
    return {
        "caja_id": int(caja_id),
        "estado": "ABIERTA" if abierta else "CERRADA",
        "usuario": row[0].get("usuario"),
        "fecha": row[0].get("fecha"),
        "fondo": float(row[0].get("monto") or 0.0) if abierta else 0.0,
        "ultimo_tipo": tipo,
    }


def resumen_multi_caja(fecha_str: str | None = None, db: Any = None) -> dict:
    """
    Consolidado de tienda + desglose por caja (solo lectura / supervisión).
    El arqueo físico se hace caja por caja (nunca un solo conteo para todas).
    """
    if db is None:
        from src.base_de_datos.database import db_manager as db

    day = fecha_str or datetime.now().strftime("%Y-%m-%d")
    cajas = listar_caja_ids(db)
    filas = []
    agg = {
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
        "multi_caja": True,
        "por_caja": [],
        "cajas_abiertas": 0,
        "cajas_cerradas": 0,
    }

    for cid in cajas:
        st = estado_caja(cid, db=db)
        datos = obtener_datos_cierre(fecha_str=day, cajero=None, caja_id=cid, db=db)
        fila = {
            **st,
            "v_efectivo": datos.get("v_efectivo", 0.0),
            "v_totales": datos.get("v_totales", 0.0),
            "v_caja_total": datos.get("v_caja_total", 0.0),
            "entradas_efectivo": datos.get("entradas_efectivo", 0.0),
            "salidas_efectivo": datos.get("salidas_efectivo", 0.0),
            "pendiente_cierre": st["estado"] == "ABIERTA"
            or float(datos.get("v_totales") or 0) > 0,
        }
        filas.append(fila)
        if st["estado"] == "ABIERTA":
            agg["cajas_abiertas"] += 1
        elif st["estado"] == "CERRADA":
            agg["cajas_cerradas"] += 1

        for k in (
            "fondo",
            "v_efectivo",
            "v_tarjeta",
            "v_trans",
            "v_credito",
            "v_totales",
            "v_caja_total",
            "ganancia_estimada",
            "entradas_efectivo",
            "salidas_efectivo",
        ):
            agg[k] = float(agg.get(k, 0) or 0) + float(datos.get(k, 0) or 0)

    agg["por_caja"] = filas
    agg["apertura_fecha"] = day
    return agg
