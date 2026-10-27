import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from src.admin.auditoria_inventario.auditoria_main import AuditoriaMain
from src.utils.barcode_parser import BarcodeParser


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_auditoria_botones_automaticos_y_limpios(qapp, monkeypatch):
    """Verifica que los botones redundantes ya no estén y la auditoría sea continua y automática."""
    # Mock conector para no requerir base de datos real
    mock_conector = MagicMock()
    mock_conector.obtener_inventario_para_auditoria.return_value = [
        {"id": 1, "codigo": "779001", "nombre": "Coca Cola 1.5L", "departamento": "BEBIDAS", "stock": 24.0, "es_pesable": False, "unidad": "UN"},
        {"id": 2, "codigo": "779002", "nombre": "Alitas", "departamento": "CARNES", "stock": 15.5, "es_pesable": True, "unidad": "KG"},
    ]
    monkeypatch.setattr("src.admin.auditoria_inventario.auditoria_main.obtener_conector_auditoria", lambda: mock_conector)

    from src.config import config
    config.current_user = {"role": "admin", "nombre": "Admin Test"}
    widget = AuditoriaMain()

    # 1. Botones redundantes eliminados
    assert not hasattr(widget, "btn_editar") or widget.btn_editar is None
    assert not hasattr(widget, "btn_aplicar") or widget.btn_aplicar is None

    # 2. Botón Historial y Exportar presentes
    assert hasattr(widget, "btn_historial")
    assert "HISTORIAL" in widget.btn_historial.text()
    assert hasattr(widget, "btn_exportar")
    assert "EXPORTAR" in widget.btn_exportar.text()

    # 3. Badge de auditoría automática en vivo en modo admin
    assert hasattr(widget, "lbl_modo_auto")
    assert "Automática" in widget.lbl_modo_auto.text() or "Vivo" in widget.lbl_modo_auto.text()

    # 4. Modo consulta si es cajero
    config.current_user = {"role": "cajero", "nombre": "Cajero 1"}
    widget.aplicar_permisos_perfil()
    assert "Consulta" in widget.lbl_modo_auto.text() or "cajero" in widget.lbl_modo_auto.text().lower()


def test_auditoria_escaner_multiplicador(qapp, monkeypatch):
    """Verifica que escanear '10*779001' o '5*Alitas' extraiga el multiplicador correctamente."""
    cod, mult = BarcodeParser.parse_scan_text("10*779001")
    assert cod == "779001"
    assert mult == 10.0

    cod2, mult2 = BarcodeParser.parse_scan_text("5*Alitas")
    assert cod2 == "Alitas"
    assert mult2 == 5.0

    cod3, mult3 = BarcodeParser.parse_scan_text("779001")
    assert cod3 == "779001"
    assert mult3 == 1.0
