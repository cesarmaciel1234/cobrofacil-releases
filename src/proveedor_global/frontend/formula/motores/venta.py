"""Qué queda si se vende una porción. No carga el cajón."""

from src.proveedor_global.frontend.formula.motores.carga import (
    HUEVOS_POR_CAJON,
    HUEVOS_POR_MAPLE,
    MAPLES_POR_CAJON,
    cerrar,
    huevos_en,
    stock_de,
    texto_se_va,
    texto_total_maples,
)


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def si_vende_huevos(rendimiento, cajones, huevos_venta) -> dict:
    """Vende huevos del cajón, una sola vez. Cada fórmula muestra el stock que queda."""
    try:
        huevos_venta = int(round(float(huevos_venta or 0)))
    except (TypeError, ValueError):
        huevos_venta = 0
    if huevos_venta < 0:
        huevos_venta = 0
    ahora = huevos_en(cajones)
    queda_huevos = ahora - huevos_venta
    if queda_huevos < 0:
        queda_huevos = 0
    queda = queda_huevos / HUEVOS_POR_CAJON
    lineas = []
    for item in rendimiento or []:
        huevos = _num(item.get("huevos"))
        if huevos <= 0:
            continue
        lineas.append({
            "nombre": item.get("nombre"),
            "ahora": stock_de(cajones, huevos),
            "queda": stock_de(queda, huevos) if queda_huevos else 0,
        })
    return {
        "vendidos": huevos_venta,
        "ahora_huevos": ahora,
        "ahora_maples": texto_total_maples(ahora),
        "queda_huevos": queda_huevos,
        "queda_maples": texto_total_maples(queda_huevos),
        "queda_cajones": queda,
        "lineas": lineas,
    }


def con_reajuste(rendimiento, cajones, movimientos) -> list:
    """Cada fórmula: lo vendido en el período y el reajuste que sale del total de huevos."""
    queda_huevos = huevos_en(cajones)
    maples = texto_total_maples(queda_huevos)
    huevos_movidos = 0
    vendidos = {}
    for mov in movimientos or []:
        try:
            huevos = int(round(float(mov.get("huevos") or 0)))
            cantidad = abs(float(mov.get("cantidad") or 0))
        except (TypeError, ValueError):
            continue
        huevos_movidos += huevos
        if str(mov.get("tipo") or "") != "venta" or cantidad <= 0 or huevos <= 0:
            continue
        unidad = int(round(huevos / cantidad))
        vendidos[unidad] = vendidos.get(unidad, 0) + cantidad
    filas = []
    for item in rendimiento or []:
        huevos = int(round(_num(item.get("huevos"))))
        if huevos <= 0:
            continue
        filas.append({
            "nombre": item.get("nombre"),
            "vendido": vendidos.get(huevos, 0),
            "reajuste": -(huevos_movidos / huevos) if huevos_movidos else 0,
            "maples": maples,
            "huevos": queda_huevos,
            "queda": stock_de(cajones, huevos),
        })
    return filas


def si_vende_uno(rendimiento, cajones: float) -> list:
    """Por cada corte: vender 1 y el stock que le quedaría, en maples y huevos."""
    filas = []
    for item in rendimiento or []:
        huevos = _num(item.get("huevos"))
        if huevos <= 0:
            continue
        consumo = huevos / HUEVOS_POR_CAJON
        queda = float(cajones) - consumo
        if queda < 0:
            queda = 0.0
        queda_huevos = huevos_en(queda)
        porciones = []
        for otra in rendimiento:
            huevos_otra = _num(otra.get("huevos"))
            if huevos_otra <= 0:
                continue
            porciones.append({
                "nombre": otra.get("nombre"),
                "stock": stock_de(queda, huevos_otra),
            })
        filas.append({
            "nombre": item.get("nombre"),
            "venta": 1,
            "se_va": texto_se_va(huevos),
            "queda_cajon": cerrar(queda),
            "queda_maples": texto_total_maples(queda_huevos),
            "queda_huevos": queda_huevos,
            "stock": stock_de(queda, huevos),
            "porciones": porciones,
        })
    return filas


def _filas(cursor, sql, params):
    cursor.execute(sql, params)
    crudas = cursor.fetchall() or []
    cols = [d[0] for d in (cursor.description or [])]
    salida = []
    for fila in crudas:
        if isinstance(fila, dict):
            salida.append(fila)
        else:
            salida.append({cols[i]: fila[i] for i in range(min(len(cols), len(fila)))})
    return salida


def repartir(cursor, base_id) -> int:
    """Después de vender, reescribe el stock de las porciones. Si falla, la venta ya está hecha."""
    if not base_id:
        return 0
    try:
        base = _filas(cursor, "SELECT stock FROM productos WHERE id = ?", (base_id,))
        formulas = _filas(
            cursor,
            "SELECT clave, nombre_venta, piezas_base, piezas_venta FROM formula_desglose "
            "WHERE alcance = ? AND base_id = ?",
            ("producto", str(base_id)),
        )
    except Exception:
        return 0
    if not base or not formulas:
        return 0
    cajones = _num(base[0].get("stock"))
    escritos = 0
    for formula in formulas:
        piezas_base = _num(formula.get("piezas_base"))
        piezas_venta = _num(formula.get("piezas_venta"))
        if piezas_base <= 0 or piezas_venta <= 0:
            continue
        if abs(piezas_base - MAPLES_POR_CAJON) < 1e-6:
            stock = stock_de(cajones, piezas_venta * HUEVOS_POR_MAPLE)
        else:
            stock = cerrar(cajones * (piezas_base / piezas_venta))
        clave = str(formula.get("clave") or "").strip()
        nombre = str(formula.get("nombre_venta") or "").strip()
        try:
            if clave and clave != str(base_id):
                cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (stock, clave))
            elif nombre:
                cursor.execute(
                    "UPDATE productos SET stock = ? WHERE UPPER(nombre) = UPPER(?)",
                    (stock, nombre),
                )
            else:
                continue
            escritos += 1
        except Exception:
            continue
    return escritos
