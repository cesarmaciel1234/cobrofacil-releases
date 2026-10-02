"""Líneas de detalle. Una consulta, todas las cajas."""

from __future__ import annotations

from src.jefe.reportes.financiero.periodo_previo import rango_igual_anterior
from src.jefe.reportes.periodo.sql import where_fecha, where_ventas


def _db():
    """La tienda en vivo; sin maestra, la copia de la tienda (`nodo_portable/espejo`)."""
    from src.jefe.nodo_portable.espejo import fuente
    return fuente()


_COLS = """
    SELECT
        v.id AS id_venta, v.fecha, v.usuario, dv.id_producto,
        dv.nombre_producto, dv.cantidad, dv.precio_unitario, dv.subtotal,
        v.metodo_pago, v.estado, COALESCE(p.departamento, p.categoria) as departamento,
        p.unidad AS unidad_medida, p.es_pesable,
        v.total, v.pago_efectivo, v.cambio, v.pago_otro
    FROM detalles_ventas dv
    JOIN ventas v ON dv.id_venta = v.id
    LEFT JOIN productos p ON dv.id_producto = p.id
"""

METODOS = ("Todos", "Efectivo", "Transferencia", "Tarjeta", "QR", "Mixto", "Fiado", "Clientes")

_BUSCA_EN = (
    "dv.nombre_producto", "dv.id_producto", "v.metodo_pago", "v.usuario",
    "v.estado", "p.departamento", "p.categoria",
)


def filtro(texto: str = "", metodo: str = "") -> tuple[str, list]:
    """Texto libre + método exacto. Devuelve ' AND …' listo para pegar."""
    sql = ""
    params: list = []
    t = (texto or "").strip()
    if t:
        ors = [f"{c} LIKE ?" for c in _BUSCA_EN]
        params += [f"%{t}%"] * len(_BUSCA_EN)
        if t.lstrip("#").isdigit():
            ors.append("v.id = ?")
            params.append(int(t.lstrip("#")))
        sql += " AND (" + " OR ".join(ors) + ")"
    m = (metodo or "").strip()
    if m and m.upper() != "TODOS":
        if m.upper() == "EFECTIVO":
            sql += " AND (v.metodo_pago IS NULL OR TRIM(v.metodo_pago) = '' OR UPPER(TRIM(v.metodo_pago)) = ? OR UPPER(TRIM(v.metodo_pago)) LIKE 'MIXTO%')"
        elif m.upper() in ("FIADO", "CLIENTES"):
            sql += " AND (UPPER(TRIM(v.metodo_pago)) = ? OR UPPER(TRIM(v.metodo_pago)) LIKE '%MIXTO (CLIENTE)%')"
        else:
            sql += " AND (UPPER(TRIM(v.metodo_pago)) = ? OR (UPPER(TRIM(v.metodo_pago)) LIKE 'MIXTO%' AND UPPER(TRIM(v.metodo_pago)) NOT LIKE '%CLIENTE%'))"
        params.append(m.upper())
    return sql, params


def listar_lineas(start_str: str, end_str: str, texto: str = "", metodo: str = "") -> list[dict]:
    db = _db()
    try:
        db.asegurar_lectura_tienda()
    except Exception:
        pass
    extra, params = filtro(texto, metodo)
    sql_f, p_f = where_fecha("v.fecha", start_str, end_str)
    params = params + list(p_f)
    q = f"{_COLS} WHERE 1=1{extra} AND {sql_f} ORDER BY v.fecha DESC"
    filas = db.execute_query(q, tuple(params)) or []
    out = []
    for r in filas:
        unidad = str(r["unidad_medida"] or "UN").strip().upper()
        pesable = bool(r["es_pesable"]) if "es_pesable" in r.keys() else unidad == "KG"
        out.append({
            "id_venta": r["id_venta"],
            "fecha": r["fecha"],
            "usuario": r["usuario"],
            "nombre_producto": r["nombre_producto"],
            "depto": str(r["departamento"] or "sin departamento").strip(),
            "cantidad": float(r["cantidad"] or 0),
            "precio_unitario": float(r["precio_unitario"] or 0),
            "subtotal": float(r["subtotal"] or 0),
            "metodo_pago": r["metodo_pago"] or "Efectivo",
            "estado": r["estado"] or "COMPLETADA",
            "unidad": "KG" if pesable or unidad == "KG" else "UN",
        })
    return out


def totales(filas: list[dict]) -> dict:
    monto = 0.0
    un = 0.0
    kg = 0.0
    deptos: dict[str, float] = {}
    tickets = set()
    for r in filas:
        monto += r["subtotal"]
        if r["unidad"] == "KG":
            kg += r["cantidad"]
        else:
            un += r["cantidad"]
        d = (r["depto"] or "sin departamento").strip().upper()
        if d in ("", "S/D", "SD", "ALMACEN", "GENERAL"):
            d = "SIN DEPARTAMENTO"
        deptos[d] = deptos.get(d, 0.0) + r["subtotal"]
        tickets.add(r["id_venta"])
    ranking = sorted(deptos.items(), key=lambda x: x[1], reverse=True)
    top1 = ranking[0] if ranking else ("—", 0.0)
    top2 = ranking[1] if len(ranking) > 1 else ("—", 0.0)
    otros = sum(v for _, v in ranking[2:])
    return {
        "monto": monto,
        "unidades": un,
        "kilos": kg,
        "lineas": len(filas),
        "tickets": len(tickets),
        "top1": top1,
        "top2": top2,
        "otros": otros,
    }


def _suma(db, start_str: str, end_str: str, texto: str, metodo: str) -> float:
    w, p = where_ventas("v", start_str, end_str)
    extra, pf = filtro(texto, metodo)
    
    m = (metodo or "").strip().upper()
    if m and m != "TODOS" and m != "MIXTO":
        # Proporción para MIXTO
        if m == "EFECTIVO":
            sum_expr = "SUM(CASE WHEN UPPER(TRIM(v.metodo_pago)) LIKE 'MIXTO%' THEN dv.subtotal * ((COALESCE(v.pago_efectivo, 0) - COALESCE(v.cambio, 0)) / CASE WHEN COALESCE(v.total, 1) = 0 THEN 1 ELSE v.total END) ELSE dv.subtotal END)"
        else:
            sum_expr = "SUM(CASE WHEN UPPER(TRIM(v.metodo_pago)) LIKE 'MIXTO%' THEN dv.subtotal * (COALESCE(v.pago_otro, 0) / CASE WHEN COALESCE(v.total, 1) = 0 THEN 1 ELSE v.total END) ELSE dv.subtotal END)"
    else:
        sum_expr = "SUM(dv.subtotal)"
        
    q = (
        f"SELECT {sum_expr} as tot FROM detalles_ventas dv "
        "JOIN ventas v ON dv.id_venta = v.id "
        "LEFT JOIN productos p ON dv.id_producto = p.id "
        f"WHERE {w}{extra}"
    )
    r = db.execute_query(q, tuple(list(p) + pf))
    return float(r[0]["tot"] or 0) if r and r[0] else 0.0


def comparativa(start_str: str, end_str: str, texto: str = "", metodo: str = "") -> tuple[float, float]:
    db = _db()
    prev_s, prev_e = rango_igual_anterior(start_str, end_str)
    curr_m = _suma(db, start_str, end_str, texto, metodo)
    prev_m = _suma(db, prev_s, prev_e, texto, metodo)
    if prev_m == 0:
        diff = 100.0 if curr_m > 0 else 0.0
    else:
        diff = ((curr_m - prev_m) / prev_m) * 100.0
    return curr_m, diff




