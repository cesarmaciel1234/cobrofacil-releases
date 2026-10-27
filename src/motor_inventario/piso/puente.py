"""Puente del piso y del techo. Escribe solo esas dos columnas. El stock no se entera."""

import logging

logger = logging.getLogger("piso_inventario")

_SQL = "UPDATE productos SET stock_minimo = ?, stock_maximo = ? WHERE id = ?"


def validar_piso_techo(filas: list[dict]) -> tuple[list[dict], str]:
    """Revisa toda la lista antes de escribir. Si una fila está mal, no se guarda ninguna."""
    limpios = []
    vistos = set()
    for cruda in filas or []:
        try:
            producto_id = int(cruda.get("id"))
            minimo = float(cruda.get("minimo"))
            maximo = float(cruda.get("maximo"))
        except (TypeError, ValueError):
            return [], "Hay un piso o un techo que no es un número."
        if producto_id <= 0 or producto_id in vistos:
            continue
        if minimo < 0 or maximo < 0:
            return [], "El piso y el techo no pueden ser negativos."
        if maximo > 0 and maximo < minimo:
            return [], "El techo no puede quedar debajo del piso."
        vistos.add(producto_id)
        limpios.append({"id": producto_id, "minimo": minimo, "maximo": maximo})
    return limpios, ""


def guardar_piso_techo(filas: list[dict]) -> tuple[bool, str]:
    """Graba mínimo y máximo. Si falla, el stock queda como estaba."""
    limpios, error = validar_piso_techo(filas)
    if error:
        return False, error
    if not limpios:
        return False, "No hay productos para guardar."
    from src.base_de_datos.database import db_manager

    for fila in limpios:
        try:
            ok = db_manager.execute_non_query(
                _SQL, (fila["minimo"], fila["maximo"], fila["id"])
            )
        except Exception as e:
            logger.error("Puente de piso caído en %s: %s", fila["id"], e)
            ok = False
        if not ok:
            return False, "No se pudo guardar el piso. El stock no se modificó."
    try:
        from src.motor_inventario.planilla.orquestador import MotorPlanilla

        MotorPlanilla.avisar()
    except Exception as e:
        logger.warning("El piso quedó guardado y la planilla se entera en su próximo pase: %s", e)
    return True, f"Se guardaron piso y techo de {len(limpios)} productos."
