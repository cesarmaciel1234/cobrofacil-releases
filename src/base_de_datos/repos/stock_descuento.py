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
    if config.get("opt_stock_negativo", False):
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
