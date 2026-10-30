"""El inventario escribe. El módulo que pregunta recibe falso si no se pudo."""

import logging

logger = logging.getLogger("inventario_puerta")


def alta(datos) -> bool:
    """Crea el producto. Falso si el código ya está o si la base falló."""
    try:
        from src.motor_inventario.procesos.editor_productos import (
            comprobar_si_codigo_existe,
            guardar_producto_en_db,
        )
        codigo = str((datos or {}).get("codigo") or "").strip()
        if codigo and comprobar_si_codigo_existe(codigo):
            return False
        ok, _msg = guardar_producto_en_db(datos or {})
        return bool(ok)
    except Exception as e:
        logger.error("Inventario no dio de alta: %s", e)
        return False


def fijar(db, codigo, stock, ofertas=None) -> bool:
    """Deja el stock en ese número. Falso si no está o si la base falló."""
    try:
        from src.proveedor_global.frontend.formula.motores.inventario import fijar as _fijar
        return bool(_fijar(db, codigo, stock, ofertas))
    except Exception as e:
        logger.error("Inventario no fijó %s: %s", codigo, e)
        return False


def sumar(db, codigo, cantidad, costo=0) -> bool:
    """Suma al stock de ese código. Falso si no está o si la base falló."""
    conn = None
    try:
        from src.proveedor_global.frontend.formula.motores.inventario import aceptar
        conn = db.get_connection()
        cur = conn.cursor()
        escritos = aceptar(cur, [{
            "codigo": str(codigo or "").strip(),
            "nombre": "",
            "kilos": cantidad,
            "costo": costo or 0,
        }])
        conn.commit()
        return int(escritos or 0) > 0
    except Exception as e:
        logger.error("Inventario no sumó %s: %s", codigo, e)
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def borrar(producto_id) -> bool:
    """Saca ese id. Falso si no se pudo."""
    try:
        from src.motor_inventario.base.productos_db import eliminar_producto_de_db
        ok, _msg = eliminar_producto_de_db(producto_id)
        return bool(ok)
    except Exception as e:
        logger.error("Inventario no borró %s: %s", producto_id, e)
        return False
