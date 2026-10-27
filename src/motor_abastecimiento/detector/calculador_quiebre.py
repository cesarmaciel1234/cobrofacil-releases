from src.logger import logger
from src.motor_abastecimiento.hilo.pregunta import preguntar_alarma


def obtener_productos_bajo_minimo():
    """Copia la planilla. La cantidad ya viene calculada. No la reinventa."""
    try:
        filas = preguntar_alarma()
    except Exception as e:
        logger.error("Abastecimiento no pudo leer la planilla: %s", e)
        return []

    faltantes = []
    for r in filas or []:
        stock_actual = float(r.get("stock") or 0.0)
        costo_unit = float(r.get("costo") or 0.0)
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
            "costo_estimado_total": round(cantidad_a_pedir * costo_unit, 2),
            "motivo": r.get("motivo") or "",
        })

    logger.info("Detector de abastecimiento: %s filas de la planilla.", len(faltantes))
    return faltantes
