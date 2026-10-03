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


def detalle(id_venta: int):
    db = _get_db()
    # Si es el cajero usando su punpro.db local, o si hay conexión, usamos el controller original
    is_online = hasattr(db, "is_connected") and db.is_connected()
    is_cajero = getattr(db, "db_engine_type", "sqlite") == "sqlite" and not hasattr(db, "ruta")
    if is_online or is_cajero:
        from src.historial_ventas.caja import controller
        return controller().get_detalle_venta(int(id_venta))
    
    # Lectura offline desde el espejo del jefe
    filas = db.execute_query("SELECT * FROM ventas WHERE id = ?", (id_venta,))
    if not filas:
        return None, None
    venta = dict(filas[0])
    lineas = db.execute_query("SELECT * FROM detalles_ventas WHERE id_venta = ?", (id_venta,)) or []
    return venta, [dict(l) for l in lineas]


def cancelar(id_venta: int, username: str) -> bool:
    return controller().cancelar_venta(int(id_venta), username)


def reimprimir(id_venta: int) -> None:
    controller().reimprimir_ticket(int(id_venta))
