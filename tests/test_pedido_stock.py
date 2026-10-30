"""El suelto se pide con el stock medido, no con la compra vieja."""

from datetime import date

from src.proveedor_global.frontend.pedido.sugerir import _medir, decidir


def test_la_caida_a_cero_mide_la_venta_y_marca_corto():
    ritmo, corto, medido, _tasas = _medir([
        {"fecha": "2026-10-25", "stock": 10},
        {"fecha": "2026-10-30", "stock": 0},
    ])

    assert medido
    assert corto
    assert ritmo == 2


def test_sin_movimiento_no_pide():
    decision = decidir(
        8,
        [0, 2, 4],
        [
            {"fecha": "2026-10-25", "stock": 8},
            {"fecha": "2026-10-30", "stock": 8},
        ],
        date(2026, 10, 30),
    )

    assert decision["aplica"]
    assert decision["pedir"] == 0
    assert "Sin movimiento" in decision["porque"]


def test_en_cero_sin_dias_no_inventa_la_cantidad():
    decision = decidir(0, [], [{"fecha": "2026-10-30", "stock": 0}], date(2026, 10, 30))

    assert decision["aplica"] is False
    assert "cortos" in decision["porque"]


def test_en_cero_con_venta_medida_pide_la_cobertura():
    decision = decidir(
        0,
        [0, 2, 4],
        [
            {"fecha": "2026-10-25", "stock": 10},
            {"fecha": "2026-10-30", "stock": 0},
        ],
        date(2026, 10, 30),
    )

    assert decision["aplica"]
    assert decision["pedir"] == 4
    assert "cero" in decision["porque"]
