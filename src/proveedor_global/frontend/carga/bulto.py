"""Un bulto de una fórmula. El remito es bultos × el costo del base.

Al elegir la fórmula se lista cada fracción con el stock que tiene ahora.
Al escribir 1 o 2 cajones, el stock que quedaría sale de 12 maples × 30 huevos.
Esas filas no se compran sueltas.
"""


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def listar_bultos(db) -> list:
    """Solo las fórmulas guardadas, una por producto base."""
    try:
        from src.jefe.promedios.formula.motor import listar
        filas = listar(db) or []
    except Exception:
        return []
    grupos = {}
    for fila in filas:
        if str(fila.get("alcance") or "") != "producto":
            continue
        nombre = str(fila.get("base_nombre") or "").strip()
        if not nombre:
            continue
        clave = nombre.upper()
        grupo = grupos.get(clave)
        if grupo is None:
            grupo = {
                "nombre": nombre,
                "base_id": str(fila.get("base_id") or "").strip(),
                "piezas_base": _num(fila.get("piezas_base")),
                "lineas": [],
            }
            grupos[clave] = grupo
        piezas = _num(fila.get("piezas_venta"))
        venta = str(fila.get("nombre_venta") or "").strip()
        if venta and piezas > 0:
            grupo["lineas"].append({
                "nombre": venta,
                "piezas_venta": piezas,
                "clave": str(fila.get("clave") or "").strip(),
                "stock_inv": _stock_fraccion(db, str(fila.get("clave") or "").strip(), venta),
            })
    salida = []
    for grupo in grupos.values():
        if not grupo["lineas"] or grupo["piezas_base"] <= 0:
            continue
        grupo.update(_costo_base(db, grupo))
        salida.append(grupo)
    salida.sort(key=lambda g: g["nombre"].upper())
    return salida


def _costo_base(db, grupo) -> dict:
    """El costo del bulto entero, el que está en el inventario."""
    vacio = {"id": grupo.get("base_id") or "", "codigo": "", "costo": 0.0, "stock": 0.0, "departamento": ""}
    consulta = (
        "SELECT id, codigo, nombre, costo, stock, departamento FROM productos WHERE id = ? LIMIT 1",
        (grupo.get("base_id"),),
    )
    fila = None
    if grupo.get("base_id"):
        fila = _uno(db, consulta[0], consulta[1])
    if not fila:
        fila = _uno(
            db,
            "SELECT id, codigo, nombre, costo, stock, departamento FROM productos "
            "WHERE UPPER(nombre) = UPPER(?) LIMIT 1",
            (grupo.get("nombre"),),
        )
    if not fila:
        return vacio
    grupo["nombre"] = fila.get("nombre") or grupo["nombre"]
    return {
        "id": str(fila.get("id") or ""),
        "codigo": str(fila.get("codigo") or fila.get("id") or ""),
        "costo": _num(fila.get("costo")),
        "stock": _num(fila.get("stock")),
        "departamento": fila.get("departamento") or "",
    }


def _uno(db, sql, params):
    try:
        filas = db.execute_query(sql, params) or []
    except Exception:
        return None
    if not filas:
        return None
    fila = filas[0]
    if isinstance(fila, dict):
        return fila
    try:
        return {k: fila[k] for k in fila.keys()}
    except Exception:
        return None


def _stock_fraccion(db, clave, nombre):
    """El stock guardado de esa fracción, si el producto existe."""
    if clave:
        fila = _uno(db, "SELECT stock FROM productos WHERE id = ? LIMIT 1", (clave,))
        if fila is not None and "stock" in fila:
            return _num(fila.get("stock"))
    fila = _uno(
        db,
        "SELECT stock FROM productos WHERE UPPER(nombre) = UPPER(?) LIMIT 1",
        (nombre,),
    )
    if fila is not None and "stock" in fila:
        return _num(fila.get("stock"))
    return None


def armar(grupo, bultos: float) -> dict:
    """Cada fracción: huevos, maples, lo que sale de 1 cajón, stock de ahora y el que quedaría."""
    try:
        bultos = float(bultos or 0)
    except (TypeError, ValueError):
        bultos = 0.0
    if bultos < 0:
        bultos = 0.0
    from src.proveedor_global.frontend.formula.motores.carga import (
        stock_de,
        texto_maples,
        huevos_en,
        texto_total_maples,
        cerrar,
    )

    costo = _num(grupo.get("costo"))
    base = _num(grupo.get("piezas_base"))
    cajon = _num(grupo.get("stock"))
    queda_cajon = cajon + bultos
    es_huevo = abs(base - 12) < 1e-6
    lineas = []
    salen = []
    for item in grupo.get("lineas") or []:
        piezas = _num(item.get("piezas_venta"))
        if piezas <= 0 or base <= 0:
            continue
        huevos = _pieza(base, piezas)
        if es_huevo:
            de_uno = stock_de(1, huevos)
            actual_formula = stock_de(cajon, huevos)
            quedaria = stock_de(queda_cajon, huevos)
            maples = texto_maples(huevos)
        else:
            de_uno = cerrar(base / piezas)
            actual_formula = cerrar(cajon * de_uno)
            quedaria = cerrar(queda_cajon * de_uno)
            maples = ""
        guardado = item.get("stock_inv")
        lineas.append({
            "nombre": item.get("nombre"),
            "huevos": huevos,
            "maples": maples,
            "salen": de_uno,
            "stock_actual": actual_formula if guardado is None else guardado,
            "quedaria": quedaria,
            "costo": round(costo * (piezas / base), 2),
        })
        salen.append({"nombre": item.get("nombre"), "salen": de_uno})
    lineas.sort(key=lambda f: (-_num(f.get("huevos")), str(f.get("nombre") or "")))
    return {
        "bultos": bultos,
        "costo": costo,
        "total": round(bultos * costo, 2),
        "cajon": cajon,
        "queda_cajon": queda_cajon,
        "huevos": huevos_en(queda_cajon) if es_huevo else 0,
        "maples_txt": texto_total_maples(huevos_en(queda_cajon)) if es_huevo else "",
        "es_huevo": es_huevo,
        "lineas": lineas,
        "salen": salen,
    }


def _pieza(piezas_base, piezas_venta) -> float:
    """En el huevo, 12 maples: la pieza se lee en huevos (30, 15, 10, 6)."""
    if abs(piezas_base - 12) < 1e-6:
        huevos = piezas_venta * 30
        if abs(huevos - round(huevos)) < 1e-4:
            return float(int(round(huevos)))
        return round(huevos, 2)
    if abs(piezas_venta - round(piezas_venta)) < 1e-4:
        return float(int(round(piezas_venta)))
    return round(piezas_venta, 2)


def aplicar_stock(db, items) -> None:
    """Después de sumar el bulto al inventario, reparte el stock de la fórmula."""
    if not items:
        return
    try:
        from src.proveedor_global.frontend.formula.motores.inventario import enviar
    except Exception:
        return
    vistos = set()
    for item in items:
        if not item.get("es_bulto"):
            continue
        base = str(item.get("id") or "").strip()
        if not base or base in vistos:
            continue
        vistos.add(base)
        try:
            enviar(db, base, item.get("bulto_salen") or [])
        except Exception:
            continue
