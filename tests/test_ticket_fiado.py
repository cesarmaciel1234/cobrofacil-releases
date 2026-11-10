import os
import sqlite3
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from src.clientes_fiado.oficina.ticket.motor import MotorTicket


class BaseTicket:
    def __init__(self, with_ticket=True):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE ventas (
                id INTEGER PRIMARY KEY, fecha TEXT, total REAL,
                metodo_pago TEXT, estado TEXT
            );
            CREATE TABLE detalles_ventas (
                id INTEGER PRIMARY KEY, id_venta INTEGER, nombre_producto TEXT,
                cantidad REAL, precio_unitario REAL, subtotal REAL
            );
            """
        )
        if with_ticket:
            self.db.execute(
                "INSERT INTO ventas VALUES (10899983, '2026-09-29 14:00:00', 3150, 'Fiado', 'COMPLETADA')"
            )
            self.db.execute(
                "INSERT INTO detalles_ventas VALUES (1, 10899983, 'Roast Beef', 0.41, 19000, 3150)"
            )
            self.db.commit()

    def execute_query(self, query, params=()):
        return [dict(row) for row in self.db.execute(query, params).fetchall()]


def test_detalle_ticket_devuelve_venta_y_articulos(monkeypatch):
    base = BaseTicket()
    monkeypatch.setattr(
        "src.clientes_fiado.oficina.ticket.motor._fuentes",
        lambda: [(base, "Maestra")],
    )

    resultado = MotorTicket().detalle("10899983")

    assert resultado["venta"]["metodo_pago"] == "Fiado"
    assert resultado["venta"]["total"] == 3150
    assert resultado["items"] == [{
        "cantidad": 0.41,
        "nombre_producto": "Roast Beef",
        "precio_unitario": 19000,
        "subtotal": 3150,
    }]
    assert resultado["origen"] == "Maestra"


def test_detalle_ticket_busca_en_la_siguiente_fuente(monkeypatch):
    sin_venta = BaseTicket(with_ticket=False)
    con_venta = BaseTicket()
    monkeypatch.setattr(
        "src.clientes_fiado.oficina.ticket.motor._fuentes",
        lambda: [(sin_venta, "Base local"), (con_venta, "Copia portable")],
    )

    resultado = MotorTicket().detalle(10899983)

    assert resultado["origen"] == "Copia portable"
    assert resultado["items"][0]["nombre_producto"] == "Roast Beef"


@pytest.mark.parametrize("ticket", ["", "abono", "0", "-12", "12.4", None])
def test_detalle_ticket_rechaza_referencias_sin_numero(ticket):
    assert MotorTicket().detalle(ticket) is None


def test_ticket_no_encontrado_devuelve_none(monkeypatch):
    base = BaseTicket(with_ticket=False)
    monkeypatch.setattr(
        "src.clientes_fiado.oficina.ticket.motor._fuentes",
        lambda: [(base, "Maestra")],
    )

    assert MotorTicket().detalle("10899983") is None


def test_click_en_ticket_de_cargo_abre_su_desglose(monkeypatch):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

    from src.admin.clientes.componentes import dialogo_historial_cliente as historial

    app = QApplication.instance() or QApplication([])
    tabla = QTableWidget(1, 6)
    tabla.setItem(0, 1, QTableWidgetItem("CARGO"))
    item_ticket = QTableWidgetItem("#10899983")
    item_ticket.setData(Qt.ItemDataRole.UserRole, "10899983")
    tabla.setItem(0, 5, item_ticket)
    abiertos = []
    historial.DialogoHistorialCliente._abrir_ticket(
        SimpleNamespace(
            tabla=tabla,
            _mostrar_ticket=lambda ticket: abiertos.append(ticket),
            panel_ticket=SimpleNamespace(mensaje=lambda *_a, **_k: None),
        ),
        0,
        5,
    )
    app.processEvents()

    assert abiertos == ["10899983"]


def test_historial_adapta_cabecera_y_espacio_de_descripciones(monkeypatch):
    from PyQt6.QtWidgets import QApplication, QHeaderView
    from PyQt6.QtTest import QTest

    from src.admin.clientes.componentes import dialogo_historial_cliente as historial

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        historial.cerebro,
        "obtener",
        lambda _cliente_id: {
            "nombre": "Cliente de prueba",
            "dni": "12345678",
            "tipo_cliente": "regular",
            "limite_credito": 1000,
            "deuda_actual": 125,
            "telefono": "555-0100",
        },
    )
    monkeypatch.setattr(historial.cerebro, "credito_disponible", lambda _cliente: 875)
    monkeypatch.setattr(historial, "iniciar_hilo_seguro", lambda _hilo: None)

    dialogo = historial.DialogoHistorialCliente(1)
    movimientos = [
        {
            "id": fila + 1,
            "tipo": "CARGO",
            "fecha": "2026-09-29 14:00:00",
            "monto": 125,
            "saldo_resultante": 125,
            "descripcion": "Descripción completa del cargo de prueba",
        }
        for fila in range(250)
    ]
    dialogo._pintar_movimientos(movimientos)
    assert dialogo._indice_pintado == 100
    assert not dialogo.tabla.isEnabled()
    for _ in range(5000):
        if dialogo._indice_pintado == len(movimientos):
            break
        QTest.qWait(1)
    app.processEvents()

    assert dialogo._indice_pintado == len(movimientos)
    assert dialogo.tabla.isEnabled()
    assert dialogo.tabla.rowCount() == len(movimientos)
    assert dialogo._totales["cargos"] == 125 * len(movimientos)
    area = dialogo.screen().availableGeometry()
    assert dialogo.width() <= min(1400, int(area.width() * 0.94))
    assert dialogo.height() <= min(920, int(area.height() * 0.90))
    assert dialogo.lbl_meta.wordWrap()
    assert "\n" in dialogo.lbl_meta.text()
    assert (
        dialogo.tabla.horizontalHeader().sectionResizeMode(4)
        == QHeaderView.ResizeMode.Stretch
    )
    assert dialogo.tabla.item(0, 4).toolTip() == "Descripción completa del cargo de prueba"
    dialogo.tabla.setRowCount(251)
    dialogo._pintar_fila(250, {
        "id": 251,
        "tipo": "CARGO",
        "venta_id": "9001",
        "monto": 125,
        "saldo_resultante": 125,
        "descripcion": "Ticket de prueba",
        "interes_acumulado": 12.5,
        "interes_en_saldo": 3,
        "dias_interes": 30,
    })
    assert dialogo.tabla.item(250, 6).text() == "30 d"
    assert dialogo.tabla.item(250, 7).text() == "$12.50"
    assert "$3.00" in dialogo.tabla.item(250, 7).toolTip()
    assert not historial.DialogoHistorialCliente._puede_borrar(
        dialogo,
        {"id": 1, "tipo": "CARGO", "es_interes": True},
    )
    assert (
        dialogo.panel_ticket.tabla.horizontalHeader().sectionResizeMode(1)
        == QHeaderView.ResizeMode.Stretch
    )
    dialogo.close()


def test_mantenimiento_muestra_descripcion_corta_y_conserva_auditoria():
    from PyQt6.QtWidgets import QApplication

    from src.admin.clientes.componentes.dialogo_ticket import PanelDetalleTicket

    app = QApplication.instance() or QApplication([])
    descripcion = (
        "MANTENIMIENTO · 3% gestión de cuenta · cargado en CESAR-CD85 "
        "por admin el 2026-11-06 10:15:01"
    )
    panel = PanelDetalleTicket()
    panel.mostrar_cargo({
        "tipo": "CARGO",
        "fecha": "2026-11-06 10:15:01",
        "monto": 5416.98,
        "saldo_resultante": 148274.48,
        "descripcion": descripcion,
    })
    app.processEvents()

    assert "cargado en" not in panel.resumen.text()
    assert panel.resumen.toolTip() == descripcion
    assert panel.tabla.item(0, 1).text() == "MANTENIMIENTO · 3% gestión de cuenta"
    assert panel.tabla.item(0, 1).toolTip() == descripcion
    panel.close()
