"""La alarma de reposición la define el inventario. Abastecimiento solo pregunta."""

import logging

from src.base_de_datos.database import db_manager

logger = logging.getLogger("alarma_inventario")

_SQL = """
    SELECT id, codigo, nombre, departamento, stock, stock_minimo, stock_maximo, costo, precio
    FROM productos
    WHERE LOWER(COALESCE(nombre, '')) NOT LIKE '%articulo comun%'
      AND LOWER(COALESCE(nombre, '')) NOT LIKE '%venta libre%'
      AND (
            COALESCE(stock, 0) <= 0
         OR (COALESCE(stock_minimo, 0) > 0 AND COALESCE(stock, 0) <= stock_minimo)
      )
    ORDER BY departamento ASC, nombre ASC
"""


def _fila(row) -> dict:
    if isinstance(row, dict):
        crudo = row
    elif hasattr(row, "keys"):
        crudo = {k: row[k] for k in row.keys()}
    else:
        return {}
    return {str(k).lower(): v for k, v in crudo.items()}


def productos_con_alarma_reposicion() -> list[dict]:
    """Productos que el inventario ya trata como alarma.

    Entra el stock crítico (existencia en cero o negativa) y el que perforó
    el piso cargado (`stock_minimo` > 0 y stock <= piso). No escribe productos.
    """
    try:
        filas = db_manager.execute_query(_SQL)
        error = str(getattr(db_manager, "last_error", "") or "").strip()
        if error:
            raise RuntimeError(error)
        filas = filas or []
    except Exception as e:
        logger.error("No se pudo leer la alarma de reposición: %s", e)
        raise

    try:
        from src.jefe.promedios.formula.intermediario import marcador
        fraccion = marcador(db_manager)
    except Exception:
        fraccion = lambda *_a, **_k: False

    alarma = []
    for cruda in filas:
        r = _fila(cruda)
        if not r:
            continue
        stock = float(r.get("stock") or 0.0)
        piso = float(r.get("stock_minimo") or 0.0)
        if piso > 0 and stock <= piso:
            motivo = "reposicion"
        elif stock <= 0:
            motivo = "critico"
        else:
            continue
        if fraccion(r.get("id"), r.get("nombre"), r.get("departamento")):
            continue
        alarma.append({
            "id": r.get("id"),
            "codigo": r.get("codigo") or "",
            "nombre": r.get("nombre") or "Sin Nombre",
            "departamento": (r.get("departamento") or "GENERAL").strip() or "GENERAL",
            "stock": stock,
            "stock_minimo": piso,
            "stock_maximo": float(r.get("stock_maximo") or 0.0),
            "costo": float(r.get("costo") or 0.0),
            "precio": float(r.get("precio") or 0.0),
            "motivo": motivo,
        })
    try:
        from src.proveedor_global.frontend.formula.motores.bulto_pedido import agrupar
        alarma = agrupar(db_manager, alarma)
    except Exception:
        logger.exception("La fórmula no pudo juntar el pedido.")
    logger.info("Inventario: %s productos con alarma de reposición.", len(alarma))
    return alarma


def _es_cajon(nombre) -> bool:
    try:
        from src.proveedor_global.frontend.formula.motores.verdad import es_formula
        return es_formula(nombre)
    except Exception:
        return False


def _sumar_cajon(alarma) -> None:
    """Un solo renglón. El pedido pregunta a la fórmula cuántos cajones quedan."""
    try:
        from src.proveedor_global.frontend.formula.motores.verdad import leer
        dato = leer(db_manager, "Huevo")
    except Exception:
        return
    cajones = float(dato.get("cajones") or 0)
    if cajones > 0:
        return
    alarma.append({
        "id": "formula:Huevo",
        "codigo": "",
        "nombre": "Cajón de huevo",
        "departamento": "Huevo",
        "stock": cajones,
        "stock_minimo": 0.0,
        "stock_maximo": 0.0,
        "costo": float(dato.get("costo") or 0),
        "precio": 0.0,
        "motivo": "critico",
    })
