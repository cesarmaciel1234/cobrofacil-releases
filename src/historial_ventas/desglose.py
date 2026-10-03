def _get_db():
    try:
        from src.jefe.nodo_portable import espejo
        if espejo.en_copia():
            return espejo.fuente()
        if espejo.copia.existe():
            from src.jefe.nodo_portable.espejo.lector import Lector
            return Lector(espejo.copia.ruta())
    except ImportError:
        pass
    from src.base_de_datos.database import db_manager
    return db_manager


def desglose(ids_venta: list) -> list:
    if not ids_venta:
        return []
    db = _get_db()

    ph = ",".join("?" for _ in ids_venta)
    return (
        db.execute_query(
            f"SELECT nombre_producto, SUM(cantidad) as total_cant, SUM(subtotal) as total_monto "
            f"FROM detalles_ventas WHERE id_venta IN ({ph}) "
            f"GROUP BY nombre_producto ORDER BY total_cant DESC",
            tuple(str(i) for i in ids_venta),
        )
        or []
    )
