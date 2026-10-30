def test_la_baja_saca_alitas_de_la_grilla(monkeypatch):
    from src.base_de_datos.offline_nutricion import offline_nutricion_manager
    from src.motor_inventario.procesos.buscador_productos import _fusionar_ediciones

    monkeypatch.setattr(
        offline_nutricion_manager,
        "productos_pendientes",
        lambda: [{"id": "9", "codigo": "ALI", "baja": True, "datos": {"id": "9"}}],
    )

    filas = _fusionar_ediciones([
        {"id": "9", "codigo": "ALI", "nombre": "Alitas"},
        {"id": "8", "codigo": "ALI2", "nombre": "Alitas"},
    ])

    assert [fila["id"] for fila in filas] == ["8"]
