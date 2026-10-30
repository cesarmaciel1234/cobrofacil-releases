from src.logger import logger
from src.motor_abastecimiento.hilo.pregunta import preguntar_alarma


def _plata(ids) -> dict:
    """Costo y precio del catálogo, por id. No decide quién está en falta."""
    limpios = [i for i in ids if i is not None and i != ""]
    if not limpios:
        return {}
    try:
        from src.motor_inventario.puerta import precios
        return precios(limpios)
    except Exception as e:
        logger.error("Abastecimiento no pudo leer el precio: %s", e)
        return {}


def obtener_productos_bajo_minimo():
    """Copia la planilla. La cantidad ya viene calculada. No la reinventa."""
    try:
        filas = preguntar_alarma()
    except Exception as e:
        logger.error("Abastecimiento no pudo leer la planilla: %s", e)
        return []

    filas = list(filas or [])
    plata = _plata(r.get("id") for r in filas)
    try:
        from src.base_de_datos.database import db_manager
        from src.proveedor_global.frontend.formula.motores.costo import para_pedido
        costo_formula = para_pedido(db_manager) or {}
    except Exception:
        costo_formula = {}
    faltantes = []
    for r in filas:
        stock_actual = float(r.get("stock") or 0.0)
        costo_planilla = float(r.get("costo") or 0.0)
        costo_cat, precio = plata.get(str(r.get("id")), (0.0, 0.0))
        costo_unit = costo_planilla if costo_planilla > 0 else costo_cat
        de_formula = float(costo_formula.get(str(r.get("id"))) or 0)
        if de_formula > 0 and costo_unit <= 0:
            costo_unit = de_formula
        base = costo_unit if costo_unit > 0 else precio
        cantidad_a_pedir = float(r.get("cantidad_sugerida") or 0)
        faltantes.append({
            "id": r.get("id"),
            "codigo": r.get("codigo") or "",
            "nombre": r.get("nombre") or "Sin Nombre",
            "departamento": (r.get("departamento") or "GENERAL").strip(),
            "stock_actual": stock_actual,
            "stock_minimo": float(r.get("stock_minimo") or 0.0),
            "stock_maximo": float(r.get("stock_maximo") or 0.0),
            "cantidad_a_pedir": cantidad_a_pedir,
            "costo_unitario": costo_unit,
            "precio_unitario": precio,
            "valor_unitario": base,
            "costo_estimado_total": round(cantidad_a_pedir * costo_unit, 2),
            "presupuesto_linea": round(cantidad_a_pedir * base, 2),
            "motivo": r.get("motivo") or "",
        })

    try:
        from src.base_de_datos.database import db_manager
        from src.proveedor_global.frontend.formula.motores.bulto_pedido import agrupar
        faltantes = agrupar(db_manager, faltantes)
    except Exception:
        logger.exception("El pedido no pudo juntar las fórmulas.")

    logger.info("Detector de abastecimiento: %s filas de la planilla.", len(faltantes))
    return faltantes
