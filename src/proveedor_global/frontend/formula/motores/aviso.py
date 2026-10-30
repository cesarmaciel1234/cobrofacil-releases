"""Le pide al servidor que nutra. No escribe stock y no baja el catálogo."""


def consultar() -> dict:
    """Si la recepción quedó en cola, el servidor la aplica. Si el stock ya está, solo avisa."""
    recepciones = 0
    try:
        from src.base_de_datos.offline_nutricion import offline_nutricion_manager

        resumen = offline_nutricion_manager.obtener_resumen_pendientes() or {}
        recepciones = int(resumen.get("recepciones") or 0)
        if recepciones:
            from src.base_de_datos.database import db_manager

            offline_nutricion_manager.nutrir_maestra(db_manager)
    except Exception:
        recepciones = 0
    try:
        from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos

        avisar_datos_nuevos()
    except Exception:
        pass
    return {"recepciones": recepciones}
