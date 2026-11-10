import sqlite3
import json
from decimal import Decimal

from src.base_de_datos.repos.ventas import VentasRepoMixin
from src.clientes_fiado.oficina.cuenta.cancelacion import sincronizar_f3_offline
from src.clientes_fiado.oficina.cuenta.interes import descripcion_reverso
from src.clientes_fiado.oficina.huella import absorber


ESQUEMA = """
CREATE TABLE ventas (
    id INTEGER PRIMARY KEY, request_id TEXT UNIQUE, estado TEXT, caja_id INTEGER,
    usuario TEXT, total REAL, metodo_pago TEXT, pago_efectivo REAL, cambio REAL,
    cancelado_por TEXT, fecha_cancel TEXT, perfil_cancel TEXT, caja_cancel INTEGER
);
CREATE TABLE detalles_ventas (id_venta INTEGER, id_producto TEXT, cantidad REAL);
CREATE TABLE productos (id TEXT PRIMARY KEY, stock REAL);
CREATE TABLE movimientos_caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, tipo TEXT, monto REAL,
    usuario TEXT, observaciones TEXT, caja_id INTEGER
);
CREATE TABLE auditoria_cancelaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT, id_venta INTEGER, fecha TEXT, usuario TEXT,
    perfil TEXT, caja_origen INTEGER, caja_accion INTEGER, monto REAL, usuario_venta TEXT
);
CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT, deuda_actual REAL, uid TEXT);
CREATE TABLE cuenta_corriente (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    tipo TEXT, monto REAL, saldo_resultante REAL, descripcion TEXT, venta_id INTEGER
);
CREATE TABLE offline_cancelaciones (
    local_venta_id INTEGER PRIMARY KEY, request_id TEXT, cancelado_por TEXT,
    fecha_cancel TEXT, perfil_cancel TEXT, caja_cancel INTEGER,
    cuenta_monto REAL DEFAULT 0, cuenta_descripcion TEXT, movimientos_caja_json TEXT
);
"""


class RepoPrueba(VentasRepoMixin):
    def __init__(self, path, motor, maestra):
        self.path = str(path)
        self.db_engine_type = motor
        self.is_master = maestra
        self._forced_local_offline = False

    def get_connection(self, caer_si_maestra_caida=True):
        return sqlite3.connect(self.path)


def _base(path):
    con = sqlite3.connect(path)
    con.executescript(ESQUEMA)
    con.close()


def _fila(path, sql, params=()):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        return con.execute(sql, params).fetchone()
    finally:
        con.close()


def test_f3_offline_deja_cola_durable_y_restaura_stock(tmp_path):
    path = tmp_path / "local.db"
    _base(path)
    con = sqlite3.connect(path)
    con.execute(
        "INSERT INTO ventas (id, request_id, estado, caja_id, usuario, total, metodo_pago, "
        "pago_efectivo, cambio) VALUES (17, 'ticket-17', 'COMPLETADA', 1, 'cesar', 100, "
        "'Efectivo', 100, 0)"
    )
    con.execute("INSERT INTO productos (id, stock) VALUES ('P1', 3)")
    con.execute("INSERT INTO detalles_ventas (id_venta, id_producto, cantidad) VALUES (17, 'P1', 2)")
    con.commit()
    con.close()

    assert RepoPrueba(path, "sqlite", False).cancelar_venta_transaccional(17, "cesar")

    venta = _fila(path, "SELECT estado, cancelado_por, fecha_cancel FROM ventas WHERE id = 17")
    producto = _fila(path, "SELECT stock FROM productos WHERE id = 'P1'")
    cola = _fila(path, "SELECT * FROM offline_cancelaciones WHERE local_venta_id = 17")
    assert venta["estado"] == "CANCELADA"
    assert venta["cancelado_por"] == "cesar"
    assert venta["fecha_cancel"]
    assert producto["stock"] == 5
    assert cola["request_id"] == "ticket-17"
    assert cola["fecha_cancel"] == venta["fecha_cancel"]


def test_f3_offline_reproduce_movimientos_de_caja_originales_en_maestra(tmp_path, monkeypatch):
    from src.base_de_datos.offline_sync import OfflineSync
    from src.config import config

    local_path = tmp_path / "punpro.db"
    _base(local_path)
    con = sqlite3.connect(local_path)
    con.execute(
        "INSERT INTO ventas (id, request_id, estado, caja_id, usuario, total, metodo_pago, "
        "pago_efectivo, cambio) VALUES (17, 'ticket-17', 'COMPLETADA', 1, 'cesar', 100, "
        "'Efectivo', 100, 0)"
    )
    con.commit()
    con.close()
    monkeypatch.setitem(config.data, "caja_id", 2)

    assert RepoPrueba(local_path, "sqlite", False).cancelar_venta_transaccional(17, "cesar")
    movimientos_locales = json.loads(
        _fila(
            local_path,
            "SELECT movimientos_caja_json FROM offline_cancelaciones WHERE local_venta_id = 17",
        )["movimientos_caja_json"]
    )
    assert [(mov["tipo"], mov["monto"], mov["caja_id"]) for mov in movimientos_locales] == [
        ("RETIRO", 100.0, 2),
        ("INGRESO", 100.0, 1),
    ]

    tienda_path = tmp_path / "tienda.db"
    _base(tienda_path)
    con = sqlite3.connect(tienda_path)
    con.execute(
        "INSERT INTO ventas (id, request_id, estado, caja_id, usuario, total, metodo_pago, "
        "pago_efectivo, cambio) VALUES (99, 'ticket-17', 'COMPLETADA', 2, 'cesar', 50, "
        "'Efectivo', 50, 0)"
    )
    con.commit()
    con.close()

    sync = OfflineSync.__new__(OfflineSync)
    sync.base_path = str(tmp_path)
    assert sync.sync_cancelaciones_pendientes(
        RepoPrueba(tienda_path, "mariadb", False)
    ) == 1
    con = sqlite3.connect(tienda_path)
    movimientos_maestros = con.execute(
        "SELECT fecha, tipo, monto, usuario, observaciones, caja_id "
        "FROM movimientos_caja ORDER BY id"
    ).fetchall()
    con.close()
    assert movimientos_maestros == [
        (
            movimiento["fecha"],
            movimiento["tipo"],
            movimiento["monto"],
            movimiento["usuario"],
            movimiento["observaciones"],
            movimiento["caja_id"],
        )
        for movimiento in movimientos_locales
    ]


def test_f3_remoto_aplica_reversion_y_cancelacion_una_sola_vez(tmp_path):
    path = tmp_path / "tienda.db"
    _base(path)
    con = sqlite3.connect(path)
    con.execute(
        "INSERT INTO ventas (id, request_id, estado, caja_id, usuario, total, metodo_pago, "
        "pago_efectivo, cambio) VALUES (99, 'ticket-17', 'COMPLETADA', 1, 'cesar', 100, "
        "'Fiado', 0, 0)"
    )
    con.execute("INSERT INTO productos (id, stock) VALUES ('P1', 3)")
    con.execute("INSERT INTO detalles_ventas (id_venta, id_producto, cantidad) VALUES (99, 'P1', 2)")
    con.execute("INSERT INTO clientes (id, nombre, deuda_actual, uid) VALUES (1, 'Ana', 110, 'U1')")
    con.execute(
        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
        "VALUES (1, 'CARGO', 100, 100, 'Ticket fiado', 99)"
    )
    con.commit()
    con.close()
    descripcion = (
        "Ticket cancelado #17 (F3) · "
        + descripcion_reverso("V:17", Decimal("10"))
    )
    repo = RepoPrueba(path, "mariadb", False)

    assert sincronizar_f3_offline(
        repo,
        17, "ticket-17", "cesar", "2026-10-01 10:00:00", "jefe", 1, 110, descripcion
    )
    assert sincronizar_f3_offline(
        repo,
        17, "ticket-17", "cesar", "2026-10-01 10:00:00", "jefe", 1, 110, descripcion
    )

    venta = _fila(path, "SELECT estado FROM ventas WHERE id = 99")
    producto = _fila(path, "SELECT stock FROM productos WHERE id = 'P1'")
    cliente = _fila(path, "SELECT deuda_actual FROM clientes WHERE id = 1")
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    anulaciones = con.execute(
        "SELECT * FROM cuenta_corriente WHERE tipo = 'ANULACION' AND venta_id = 99"
    ).fetchall()
    con.close()
    cargo = _fila(path, "SELECT descripcion FROM cuenta_corriente WHERE venta_id = 99 AND tipo = 'CARGO'")
    assert venta["estado"] == "CANCELADA"
    assert producto["stock"] == 5
    assert cliente["deuda_actual"] == 0
    assert len(anulaciones) == 1
    assert "V:99" in anulaciones[0]["descripcion"]
    assert "V:17" not in anulaciones[0]["descripcion"]
    assert cargo["descripcion"].startswith("CANCELADO · ")


def test_f3_remoto_registra_devolucion_en_caja_origen_y_caja_de_accion(tmp_path):
    path = tmp_path / "tienda_efectivo.db"
    _base(path)
    con = sqlite3.connect(path)
    con.execute(
        "INSERT INTO ventas (id, request_id, estado, caja_id, usuario, total, metodo_pago, "
        "pago_efectivo, cambio) VALUES (99, 'ticket-efectivo', 'COMPLETADA', 1, 'cesar', "
        "100, 'Efectivo', 100, 0)"
    )
    con.commit()
    con.close()

    repo = RepoPrueba(path, "mariadb", False)
    assert sincronizar_f3_offline(
        repo,
        17, "ticket-efectivo", "cesar", "2026-10-01 10:00:00", "jefe", 2
    )
    assert sincronizar_f3_offline(
        repo,
        17, "ticket-efectivo", "cesar", "2026-10-01 10:00:00", "jefe", 2
    )

    con = sqlite3.connect(path)
    movimientos = con.execute(
        "SELECT fecha, tipo, monto, caja_id FROM movimientos_caja ORDER BY id"
    ).fetchall()
    con.close()
    assert movimientos == [
        ("2026-10-01 10:00:00", "RETIRO", 100.0, 2),
        ("2026-10-01 10:00:00", "INGRESO", 100.0, 1),
    ]


def test_huella_difiere_el_reverso_f3_mientras_existe_en_outbox(tmp_path):
    path = tmp_path / "punpro.db"
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE offline_cancelaciones (local_venta_id INTEGER, request_id TEXT)"
    )
    con.execute(
        "INSERT INTO offline_cancelaciones VALUES (17, 'ticket-17')"
    )
    con.commit()
    con.close()
    eventos = [
        {
            "accion": "ANULACION",
            "detalle": json.dumps({
                "venta_id": 17,
                "venta_request_id": "ticket-17",
                "cancelacion_f3": True,
            }),
        },
        {"accion": "ABONO", "detalle": "{}"},
    ]

    filtrados = absorber.filtrar_cancelaciones_pendientes(eventos, str(path))

    assert filtrados == [eventos[1]]


def test_offline_sync_conserva_outbox_hasta_confirmar(tmp_path):
    from src.base_de_datos.offline_sync import OfflineSync

    local_path = tmp_path / "punpro.db"
    _base(local_path)
    con = sqlite3.connect(local_path)
    con.execute(
        "INSERT INTO offline_cancelaciones "
        "(local_venta_id, request_id, cancelado_por, fecha_cancel, perfil_cancel, caja_cancel) "
        "VALUES (17, 'ticket-17', 'cesar', '2026-10-01 10:00:00', 'jefe', 2)"
    )
    con.commit()
    con.close()
    sync = OfflineSync.__new__(OfflineSync)
    sync.base_path = str(tmp_path)

    class Fallida:
        db_engine_type = "sqlite"

    assert sync.obtener_cancelaciones_pendientes() == 1
    assert sync.sync_cancelaciones_pendientes(Fallida()) == 0
    assert sync.obtener_cancelaciones_pendientes() == 1

    tienda_path = tmp_path / "tienda.db"
    _base(tienda_path)
    con = sqlite3.connect(tienda_path)
    con.execute(
        "INSERT INTO ventas (id, request_id, estado, caja_id, usuario, total, metodo_pago, "
        "pago_efectivo, cambio) VALUES (99, 'ticket-17', 'COMPLETADA', 1, 'cesar', 100, "
        "'Efectivo', 100, 0)"
    )
    con.commit()
    con.close()
    assert sync.sync_cancelaciones_pendientes(
        RepoPrueba(tienda_path, "mariadb", False)
    ) == 1
    assert sync.obtener_cancelaciones_pendientes() == 0
    assert _fila(tienda_path, "SELECT estado FROM ventas WHERE id = 99")["estado"] == "CANCELADA"
