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
    monkeypatch.setattr(
        "src.admin.clientes.componentes.dialogo_ticket.abrir_detalle_ticket",
        lambda ticket, parent: abiertos.append(ticket),
    )

    historial.DialogoHistorialCliente._abrir_ticket(
        SimpleNamespace(tabla=tabla),
        0,
        5,
    )
    app.processEvents()

    assert abiertos == ["10899983"]
