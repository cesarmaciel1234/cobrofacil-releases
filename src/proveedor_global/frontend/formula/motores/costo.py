"""Costo de compra de cada fórmula. Lo trae la reposición. No mira el precio de venta."""


def de_reposicion(db, rendimiento, precio_bulto: float = 0) -> dict:
    """El costo del cajón llega de la reposición o del precio del bulto. Cada fórmula es ese costo dividido por lo que sale."""
    from src.proveedor_global.frontend.formula.motores.carga import stock_cajon
    from src.proveedor_global.frontend.formula.motores.consulta import _emparejar, _productos

    cajon = stock_cajon(db)
    costo = _numero(precio_bulto)
    if costo <= 0 and cajon.get("hallado"):
        costo = _costo_de(db, cajon.get("id"))
    productos = _productos(db, "Huevo")
    lineas = []
    for item in rendimiento or []:
        try:
            salen = float(item.get("salen") or 0)
        except (TypeError, ValueError):
            salen = 0.0
        prod = _emparejar(productos, item.get("huevos"), item.get("nombre"))
        if costo > 0:
            unitario = _parte(costo, salen)
        else:
            unitario = float(prod.get("costo") or 0) if prod else 0.0
        lineas.append({
            "nombre": item.get("nombre") or "",
            "producto": prod,
            "salen": salen,
            "stock": float(prod.get("stock") or 0) if prod else 0.0,
            "costo_compra": unitario,
        })
    return {"costo_cajon": costo, "cajon": cajon, "lineas": lineas}


def para_pedido(db) -> dict:
    """Id del producto y su costo de compra. Vacío si la reposición todavía no tiene costo."""
    try:
        from src.proveedor_global.frontend.formula.motores.carga import de_un_cajon
        from src.proveedor_global.frontend.formula.motores.lectura import leer

        cortes = leer(db, "Huevo") or [
            ("Maple 30 huevos", 30),
            ("Maple 15 huevos", 15),
            ("Maple 10 huevos", 10),
            ("Maple 6 huevos", 6),
        ]
        cuenta = de_reposicion(db, de_un_cajon(cortes))
    except Exception:
        return {}
    if float(cuenta.get("costo_cajon") or 0) <= 0 and not any(
        float(linea.get("costo_compra") or 0) > 0 for linea in cuenta.get("lineas") or []
    ):
        return {}
    salida = {}
    for linea in cuenta.get("lineas") or []:
        prod = linea.get("producto") or {}
        if prod.get("id") and linea.get("costo_compra"):
            salida[str(prod["id"])] = float(linea["costo_compra"])
    return salida


def _numero(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _parte(costo_cajon, salen) -> float:
    try:
        costo_cajon = float(costo_cajon or 0)
        salen = float(salen or 0)
    except (TypeError, ValueError):
        return 0.0
    if costo_cajon <= 0 or salen <= 0:
        return 0.0
    return round(costo_cajon / salen, 2)


def _costo_de(db, producto_id) -> float:
    if not producto_id:
        return 0.0
    try:
        filas = db.execute_query(
            "SELECT costo FROM productos WHERE id = ? LIMIT 1",
            (producto_id,),
        ) or []
    except Exception:
        return 0.0
    if not filas:
        return 0.0
    fila = filas[0]
    if isinstance(fila, dict):
        valor = fila.get("costo")
    else:
        try:
            valor = fila[0]
        except Exception:
            return 0.0
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
