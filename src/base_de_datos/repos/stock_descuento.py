"""Descuenta stock de una venta. Sin la opción, dos cajas no se llevan el mismo resto."""


class SinStock(Exception):
    def __init__(self, producto_id):
        self.producto_id = producto_id
        super().__init__(f"Sin stock para el producto {producto_id}")


def descontar_stock(cursor, producto_id, cantidad) -> None:
    if not producto_id or str(producto_id).strip() in ("000", ""):
        return
    from src.config import config

    cant = cantidad or 0
    try:
        from src.proveedor_global.frontend.formula.motores.pieza import original_id
        destino = original_id(cursor, producto_id)
    except Exception:
        destino = None
    if destino:
        producto_id = destino
    if _consumir_formula(cursor, producto_id, cant):
        return
    if config.get("opt_stock_negativo", True):
        cursor.execute(
            "UPDATE productos SET stock = stock - ? WHERE id = ?",
            (cant, producto_id),
        )
        return
    cursor.execute(
        "UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?",
        (cant, producto_id, cant),
    )
    if getattr(cursor, "rowcount", None) == 0:
        raise SinStock(producto_id)


def _consumir_formula(cursor, producto_id, cantidad) -> bool:
    try:
        from src.jefe.promedios.formula.motor import consumir_base
        if consumir_base(cursor, producto_id, cantidad):
            return True
    except SinStock:
        raise
    except Exception:
        pass
    try:
        from src.proveedor_global.frontend.formula.motores.verdad import consumir
        return bool(consumir(cursor, producto_id, cantidad))
    except SinStock:
        raise
    except Exception:
        return False
