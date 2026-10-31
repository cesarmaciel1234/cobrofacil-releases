def test_el_check_y_el_cobro_quedan_invertidos(monkeypatch):
    from src.config import config
    from src.motor_inventario.unidad_medida import (
        bloquear_venta_sin_stock,
        guardar_bloqueo_venta_sin_stock,
        permitir_cobro_sin_stock,
    )

    monkeypatch.setitem(config.data, "opt_stock_negativo", True)
    assert permitir_cobro_sin_stock() is True
    assert bloquear_venta_sin_stock() is False

    guardar_bloqueo_venta_sin_stock(True)
    assert config.data["opt_stock_negativo"] is False
    assert permitir_cobro_sin_stock() is False
    assert bloquear_venta_sin_stock() is True

    guardar_bloqueo_venta_sin_stock(False)
    assert config.data["opt_stock_negativo"] is True
    assert permitir_cobro_sin_stock() is True
