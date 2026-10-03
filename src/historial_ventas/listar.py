from __future__ import annotations

from datetime import datetime


def iso_dia(f_raw) -> str:
    if f_raw is None:
        return ""
    if hasattr(f_raw, "strftime"):
        return f_raw.strftime("%Y-%m-%d")
    s = str(f_raw).strip()
    dt = _parse_fecha(s)
    if dt:
        return dt.strftime("%Y-%m-%d")
    if len(s) >= 10 and s[4] == "-":
        return s[:10]
    return ""


def _get_db():
    try:
        from src.jefe.nodo_portable import espejo
        if espejo.en_copia():
            return espejo.fuente()
        if espejo.copia.existe():
            from src.jefe.nodo_portable.espejo.lector import Lector
            return Lector(espejo.copia.ruta())
    except ImportError:
        pass
    from src.base_de_datos.database import db_manager
    return db_manager


def listar_tickets(
    *,
    texto: str = "",
    metodo: str = "TODOS",
    fecha_iso: str | None = None,
    ver_todo: bool = False,
    hora_desde: str | None = None,
    hora_hasta: str | None = None,
    solo_caja: bool = False,
    usuario: str = "",
    caja_id: int | None = None,
    caja_filtro: int | None = None,
):
    db = _get_db()

    sql_tail = " FROM ventas v LEFT JOIN detalles_ventas dv ON dv.id_venta = v.id "
    params: list = []
    where = ""
    clauses = []
    if solo_caja and usuario:
        clauses.append("LOWER(v.usuario) = LOWER(?)")
        params.append(usuario)
        if caja_id is not None:
            clauses.append("v.caja_id = ?")
            params.append(caja_id)
    usar_dia = (not ver_todo) and bool(fecha_iso)
    if usar_dia:
        try:
            from src.jefe.reportes.periodo.sql import where_fecha

            sql_f, p_f = where_fecha("v.fecha", fecha_iso, fecha_iso)
            clauses.append(sql_f)
            params.extend(p_f)
        except Exception:
            clauses.append("v.fecha >= ? AND v.fecha < ?")
            params.extend([f"{fecha_iso} 00:00:00", f"{fecha_iso} 23:59:59"])
    if clauses:
        where = "WHERE " + " AND ".join(clauses) + " "
    group = "GROUP BY v.id ORDER BY v.id DESC LIMIT 4000"
    cols_full = (
        "SELECT v.id, v.fecha, v.total, v.usuario, v.estado, v.metodo_pago, "
        "v.descuento, v.recargo, v.pago_con, v.cambio, v.caja_id, v.cliente_nombre, "
        "v.cancelado_por, v.fecha_cancel, v.perfil_cancel, v.caja_cancel, "
        "v.pago_efectivo, v.pago_otro, "
        "IFNULL(SUM(dv.cantidad), 0) as cant_arts, "
        "GROUP_CONCAT(dv.nombre_producto, ' ') as prod_names"
    )
    cols_min = (
        "SELECT v.id, v.fecha, v.total, v.usuario, v.estado, v.metodo_pago, "
        "v.descuento, v.recargo, v.pago_con, v.cambio, v.caja_id, v.cliente_nombre, "
        "v.pago_efectivo, v.pago_otro, "
        "IFNULL(SUM(dv.cantidad), 0) as cant_arts, "
        "GROUP_CONCAT(dv.nombre_producto, ' ') as prod_names"
    )
    cols_fallback = (
        "SELECT v.id, v.fecha, v.total, v.usuario, v.estado, v.metodo_pago, "
        "v.descuento, v.recargo, v.pago_con, v.cambio, v.caja_id, v.cliente_nombre, "
        "IFNULL(SUM(dv.cantidad), 0) as cant_arts, "
        "GROUP_CONCAT(dv.nombre_producto, ' ') as prod_names"
    )
    
    rows = _traer(db, cols_full, cols_min, cols_fallback, sql_tail, where, group, params)
    if usar_dia and not rows:
        rows = _traer(db, cols_full, cols_min, cols_fallback, sql_tail, "", group, [])

    txt = (texto or "").strip().lower()
    metodo_u = (metodo or "TODOS").upper()
    m0 = _a_minutos(hora_desde)
    m1 = _a_minutos(hora_hasta)
    filtrar_hora = m0 is not None and m1 is not None and not (m0 == 0 and m1 >= 23 * 60 + 59)
    filtradas = []
    total_ok = 0.0
    for r in rows:
        f_raw = r["fecha"]
        f_str = f_raw.strftime("%Y-%m-%d %H:%M:%S") if hasattr(f_raw, "strftime") else str(f_raw or "")
        dia = iso_dia(f_raw)
        if usar_dia and dia != fecha_iso:
            continue
        if filtrar_hora:
            dt = _parse_fecha(f_str) if not hasattr(f_raw, "hour") else f_raw
            if dt is None:
                dt = _parse_fecha(f_str)
            if dt is not None:
                mins = int(dt.hour) * 60 + int(dt.minute)
                if not (m0 <= mins <= m1):
                    continue
        pago = str(r["metodo_pago"] or "").upper()
        
        aporte_parcial = None
        if metodo_u == "REDONDEO":
            try: desc = float(r["descuento"]) if r["descuento"] else 0.0
            except: desc = 0.0
            if desc <= 0: continue
        elif metodo_u == "RECARGO":
            try: rec = float(r["recargo"]) if r["recargo"] else 0.0
            except: rec = 0.0
            if rec <= 0: continue
        elif metodo_u != "TODOS":
            if pago.startswith("MIXTO"):
                # Si el filtro es Efectivo, se permite y suma la porciÃ³n en efectivo.
                # Si el filtro es distinto de Efectivo (ej. Transferencia, Tarjeta), suma la porciÃ³n digital.
                try: 
                    pe = float(r.get("pago_efectivo") or 0.0)
                    cambio = float(r.get("cambio") or 0.0)
                    po = float(r.get("pago_otro") or 0.0)
                except Exception:
                    pe, cambio, po = 0.0, 0.0, 0.0
                
                if metodo_u == "EFECTIVO":
                    aporte_parcial = pe - cambio
                else:
                    if metodo_u in ("FIADO", "CLIENTES") and "CLIENTE" not in pago:
                        continue
                    if metodo_u not in ("FIADO", "CLIENTES", "EFECTIVO", "TODOS") and "CLIENTE" in pago:
                        continue
                    aporte_parcial = po
                
                if aporte_parcial <= 0:
                    continue  # Si no aporta nada a este filtro, se salta.
            elif metodo_u not in pago:
                continue
        if caja_filtro is not None:
            try:
                if int(r["caja_id"] or 1) != int(caja_filtro):
                    continue
            except (TypeError, ValueError, KeyError):
                pass
        if txt:
            pool = (
                f"{r['id']} {r['usuario']} {f_str} {r['metodo_pago']} "
                f"{r['total']} {r['prod_names'] or ''}"
            ).lower()
            if txt not in pool:
                continue
        filtradas.append(r)
        if not str(r["estado"] or "").upper().startswith("CANCELAD"):
            if aporte_parcial is not None:
                total_ok += aporte_parcial
            else:
                total_ok += float(r["total"] or 0)
    return filtradas, total_ok


def _a_minutos(hm: str | None):
    if not hm:
        return None
    try:
        partes = str(hm).strip().replace(".", ":").split(":")
        return int(partes[0]) * 60 + int(partes[1] if len(partes) > 1 else 0)
    except (TypeError, ValueError, IndexError):
        return None


def _traer(db_manager, cols_full, cols_min, cols_fallback, sql_tail, where, group, params):
    rows = db_manager.execute_query(cols_full + sql_tail + where + group, tuple(params)) or []
    err = str(getattr(db_manager, "last_error", "") or "").lower()
    if (not rows) and ("cancelado" in err or "unknown column" in err or "no such column" in err):
        rows = db_manager.execute_query(cols_min + sql_tail + where + group, tuple(params)) or []
        err = str(getattr(db_manager, "last_error", "") or "").lower()
        if (not rows) and ("unknown column" in err or "no such column" in err):
            rows = db_manager.execute_query(cols_fallback + sql_tail + where + group, tuple(params)) or []
    return rows


def _parse_fecha(f_str: str):
    s = (f_str or "").replace("T", " ").strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ):
        try:
            pieza = s[:19] if len(s) >= 19 else s
            return datetime.strptime(pieza, fmt)
        except ValueError:
            continue
    return None

