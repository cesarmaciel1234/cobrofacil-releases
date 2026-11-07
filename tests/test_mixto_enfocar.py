"""En mixto vivo solo se ven efectivo y el medio digital."""

from PyQt6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])


def test_enfocar_qr_deja_efectivo_y_oculta_el_resto():
    from src.cajero.paso6_cobro.mixto_en_cobro.panel import PanelMixtoCobro

    panel = PanelMixtoCobro()
    panel._total = 100.0
    panel.txt_efectivo.setText("80")
    panel.txt_qr.setText("20")
    panel.cerrar_reparto()
    panel.enfocar("qr")

    assert not panel.txt_efectivo.isHidden()
    assert not panel.txt_qr.isHidden()
    assert panel.txt_tarjeta.isHidden()
    assert panel.txt_mercadopago.isHidden()
    assert panel.txt_cliente.isHidden()
    assert panel._marcas["efectivo"].text() == "✓"


def test_abrir_reparto_vuelve_a_mostrar_todas_las_filas():
    from src.cajero.paso6_cobro.mixto_en_cobro.panel import PanelMixtoCobro

    panel = PanelMixtoCobro()
    panel._total = 100.0
    panel.txt_efectivo.setText("80")
    panel.txt_qr.setText("20")
    panel.enfocar("qr")
    panel.abrir_reparto()

    assert not panel.txt_tarjeta.isHidden()
    assert not panel.txt_cliente.isHidden()
