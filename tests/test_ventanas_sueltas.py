from src.admin.ventanas_sueltas.gestor import MAX_SUELTAS, se_puede
from src.navigation.screen_indices import Screen


def test_cajero_no_se_desancla():
    ok, _ = se_puede(Screen.CAJERO, {})
    assert ok is False


def test_tope_tres_modulos():
    abiertas = {Screen.INVENTARIO: 1, Screen.CLIENTES: 1, Screen.MERCADO_PAGO: 1}
    assert len(abiertas) == MAX_SUELTAS
    ok, msg = se_puede(Screen.ETIQUETAS, abiertas)
    assert ok is False
    assert "3" in msg


def test_clientes_si_sale_a_otro_monitor():
    ok, _ = se_puede(Screen.CLIENTES, {})
    assert ok is True
