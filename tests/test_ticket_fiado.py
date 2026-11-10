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
        == QHeaderView.ResizeMode.ResizeToContents
    )
    assert (
        dialogo.tabla.horizontalHeader().sectionResizeMode(5)
        == QHeaderView.ResizeMode.Stretch
    )
    assert dialogo.tabla.item(0, 5).toolTip() == "Descripción completa del cargo de prueba"
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


def test_orden_columnas_historial_y_descripcion_armoniosa(monkeypatch):
    from PyQt6.QtWidgets import QApplication, QHeaderView
    from src.admin.clientes.componentes import dialogo_historial_cliente as historial

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        historial.cerebro,
        "obtener",
        lambda _cid: {
            "nombre": "Ruben",
            "dni": "12345678",
            "tipo_cliente": "regular",
            "limite_credito": 500000,
            "deuda_actual": 277715.50,
            "telefono": "555-0100",
        },
    )
    monkeypatch.setattr(historial.cerebro, "credito_disponible", lambda _c: 222284.50)
    monkeypatch.setattr(historial, "iniciar_hilo_seguro", lambda _h: None)

    dialogo = historial.DialogoHistorialCliente(1)
    
    # 1. Cabeceras en orden exacto: Ticket antes de Descripción
    headers = [dialogo.tabla.horizontalHeaderItem(i).text() for i in range(8)]
    assert headers == [
        "Fecha", "Tipo", "Monto", "Saldo", "Ticket / cobro", "Descripción",
        "Días", "Mantenimiento",
    ]
    
    # 2. Modos de redimensionamiento
    assert dialogo.tabla.horizontalHeader().sectionResizeMode(4) == QHeaderView.ResizeMode.ResizeToContents
    assert dialogo.tabla.horizontalHeader().sectionResizeMode(5) == QHeaderView.ResizeMode.Stretch
    
    # 3. Renglones: venta con excepción admin, venta normal, cobro con transferencia manual, cargo manual
    movs = [
        {
            "id": 1,
            "tipo": "CARGO",
            "venta_id": "1091372",
            "referencia": "#1091372",
            "fecha": "2026-10-17 16:41:52",
            "monto": 78555.00,
            "saldo_resultante": 142492.50,
            "descripcion": "Venta a crédito #1091372 (excepción admin)",
        },
        {
            "id": 2,
            "tipo": "CARGO",
            "venta_id": "1092895",
            "referencia": "#1092895",
            "fecha": "2026-11-08 11:19:26",
            "monto": 84728.00,
            "saldo_resultante": 283132.48,
            "descripcion": "Venta a crédito #1092895",
        },
        {
            "id": 3,
            "tipo": "ABONO",
            "referencia": "COB-180",
            "fecha": "2026-09-30 18:54:33",
            "monto": 307838.50,
            "saldo_resultante": 0.00,
            "descripcion": "Cobro a cuenta (Transferencia: F9 MANUAL)",
        },
        {
            "id": 4,
            "tipo": "CARGO",
            "referencia": "—",
            "fecha": "2026-09-28 18:35:50",
            "monto": 284833.00,
            "saldo_resultante": 307838.50,
            "descripcion": "Cargo manual desde panel Admin",
        },
    ]
    
    dialogo.tabla.setRowCount(4)
    for idx, m in enumerate(movs):
        dialogo._pintar_fila(idx, m)
    
    # Fila 0: Venta con excepción: col 4 es ticket, col 5 es descripción limpia sin emoji ni alerta chillona
    assert dialogo.tabla.item(0, 4).text() == "#1091372"
    assert dialogo.tabla.item(0, 5).text() == "Excepción admin"
    assert "⚠️" not in dialogo.tabla.item(0, 5).text()
    
    # Fila 1: Venta normal sin excepción: col 4 es ticket, col 5 es guión limpio
    assert dialogo.tabla.item(1, 4).text() == "#1092895"
    assert dialogo.tabla.item(1, 5).text() == "—"
    
    # Fila 2: Cobro: col 4 es COB-180, col 5 es Transferencia limpia (sin 'F9 MANUAL' ni signos raros)
    assert dialogo.tabla.item(2, 4).text() == "COB-180"
    assert dialogo.tabla.item(2, 5).text() == "Transferencia"
    assert "F9 MANUAL" not in dialogo.tabla.item(2, 5).text()
    
    # Fila 3: Cargo manual: col 4 es —, col 5 es Cargo manual desde panel Admin
    assert dialogo.tabla.item(3, 4).text() == "—"
    assert dialogo.tabla.item(3, 5).text() == "Cargo manual desde panel Admin"

    dialogo.close()
