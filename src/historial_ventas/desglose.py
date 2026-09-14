def desglose(ids_venta: list) -> list:
    if not ids_venta:
        return []
    from src.base_de_datos.database import db_manager

    ph = ",".join("?" for _ in ids_venta)
    return (
        db_manager.execute_query(
            f"SELECT nombre_producto, SUM(cantidad) as total_cant, SUM(subtotal) as total_monto "
            f"FROM detalles_ventas WHERE id_venta IN ({ph}) "
            f"GROUP BY nombre_producto ORDER BY total_cant DESC",
            tuple(str(i) for i in ids_venta),
        )
        or []
    )
