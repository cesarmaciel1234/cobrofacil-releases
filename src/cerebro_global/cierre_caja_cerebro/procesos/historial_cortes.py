"""Historial de cortes registrados (CIERRE_TURNO / CIERRE_Z / CIERRE_AUTO) por día."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def listar_cortes_del_dia(
    fecha_str: str | None = None,
    caja_id: int | None = None,
    cajero: str | None = None,
    db: Any = None,
) -> list[dict]:
    """
    Cortes del día calendario, uno por fila (cada cajero / caja / hora).
    Parsea esperado/dif desde observaciones cuando existen.
    """
    if db is None:
        from src.base_de_datos.database import db_manager as db

    day = fecha_str or datetime.now().strftime("%Y-%m-%d")
    desde = f"{day} 00:00:00"
    hasta = f"{day} 23:59:59"

    cond = (
        "tipo IN ('CIERRE_TURNO', 'CIERRE_Z', 'CIERRE_AUTO') "
        "AND fecha >= ? AND fecha <= ?"
    )
    params: list = [desde, hasta]
    if caja_id is not None:
        cond += " AND caja_id = ?"
        params.append(int(caja_id))
    if cajero:
        cond += " AND usuario = ?"
        params.append(cajero)

    try:
        rows = (
            db.execute_query(
                f"SELECT id, fecha, tipo, monto, usuario, observaciones, caja_id "
                f"FROM movimientos_caja WHERE {cond} ORDER BY fecha ASC, id ASC",
                tuple(params),
            )
            or []
        )
    except Exception as e:
        print(f"Error listar_cortes_del_dia: {e}")
        return []

    out = []
    for r in rows:
        obs = str(r.get("observaciones") or "")
        esperado, dif, t_ventas = _parse_obs(obs)
        tipo = str(r.get("tipo") or "")
        out.append(
            {
                "id": r.get("id"),
                "fecha": str(r.get("fecha") or ""),
                "hora": _hora(str(r.get("fecha") or "")),
                "tipo": tipo,
                "tipo_label": _label_tipo(tipo),
                "usuario": str(r.get("usuario") or "—"),
                "caja_id": int(r.get("caja_id") or 1),
                "fisico": float(r.get("monto") or 0.0),
                "esperado": esperado,
                "diferencia": dif if dif is not None else (
                    float(r.get("monto") or 0.0) - esperado if esperado is not None else None
                ),
                "total_ventas": t_ventas,
                "observaciones": obs,
            }
        )
    return out


def resumen_cortes_por_cajero(
    fecha_str: str | None = None,
    caja_id: int | None = None,
    db: Any = None,
) -> list[dict]:
    """Agrupa cortes del día por cajero (suma físicos / cantidad de cortes)."""
    cortes = listar_cortes_del_dia(fecha_str=fecha_str, caja_id=caja_id, db=db)
    by_user: dict[str, dict] = {}
    for c in cortes:
        u = c["usuario"]
        slot = by_user.setdefault(
            u,
            {
                "usuario": u,
                "cortes": 0,
                "fisico_total": 0.0,
                "esperado_total": 0.0,
                "cajas": set(),
                "tipos": [],
                "detalle": [],
            },
        )
        slot["cortes"] += 1
        slot["fisico_total"] += float(c["fisico"] or 0)
        if c.get("esperado") is not None:
            slot["esperado_total"] += float(c["esperado"])
        slot["cajas"].add(c["caja_id"])
        slot["tipos"].append(c["tipo_label"])
        slot["detalle"].append(c)

    result = []
    for u, slot in sorted(by_user.items(), key=lambda x: x[0].lower()):
        result.append(
            {
                "usuario": u,
                "cortes": slot["cortes"],
                "fisico_total": slot["fisico_total"],
                "esperado_total": slot["esperado_total"],
                "cajas": sorted(slot["cajas"]),
                "tipos": slot["tipos"],
                "detalle": slot["detalle"],
            }
        )
    return result


def _label_tipo(tipo: str) -> str:
    t = (tipo or "").upper()
    if t == "CIERRE_TURNO":
        return "Turno"
    if t == "CIERRE_Z":
        return "Z día"
    if t == "CIERRE_AUTO":
        return "Auto"
    return t or "?"


def _hora(fecha: str) -> str:
    if " " in fecha:
        return fecha.split(" ", 1)[1][:8]
    if "T" in fecha:
        return fecha.split("T", 1)[1][:8]
    return fecha[-8:] if len(fecha) >= 8 else fecha


def _parse_obs(obs: str) -> tuple[float | None, float | None, float | None]:
    """Obs tipica: 'Cierre corte cajero. Esperado: 1,234.56. Dif: -10.00. Total ventas: 500.00'"""
    import re

    def _num(key: str) -> float | None:
        m = re.search(
            rf"{key}:\s*([-+]?\d{{1,3}}(?:,\d{{3}})*(?:\.\d+)?|[-+]?\d+(?:\.\d+)?)",
            obs,
            re.IGNORECASE,
        )
        if not m:
            # es-AR: 1.234,56
            m = re.search(
                rf"{key}:\s*([-+]?\d{{1,3}}(?:\.\d{{3}})*(?:,\d+)?)",
                obs,
                re.IGNORECASE,
            )
            if not m:
                return None
            try:
                return float(m.group(1).replace(".", "").replace(",", "."))
            except ValueError:
                return None
        raw = m.group(1).replace(",", "")
        try:
            return float(raw)
        except ValueError:
            return None

    return _num("Esperado"), _num("Dif"), _num("Total ventas")
