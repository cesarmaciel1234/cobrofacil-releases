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
    params = tuple(str(i) for i in ids_venta)
    con_unidad = (
        "SELECT dv.nombre_producto, SUM(dv.cantidad) as total_cant, SUM(dv.subtotal) as total_monto, "
        "MAX(p.unidad) as unidad, MAX(p.es_pesable) as es_pesable, MAX(p.departamento) as departamento "
        "FROM detalles_ventas dv LEFT JOIN productos p ON dv.id_producto = p.id "
        f"WHERE dv.id_venta IN ({ph}) GROUP BY dv.nombre_producto ORDER BY total_cant DESC"
    )
    try:
        filas = db.execute_query(con_unidad, params)
        if filas:
            return filas
    except Exception:
        filas = None
    return (
        db.execute_query(
            "SELECT nombre_producto, SUM(cantidad) as total_cant, SUM(subtotal) as total_monto "
            f"FROM detalles_ventas WHERE id_venta IN ({ph}) "
            "GROUP BY nombre_producto ORDER BY total_cant DESC",
            params,
        )
        or []
    )
