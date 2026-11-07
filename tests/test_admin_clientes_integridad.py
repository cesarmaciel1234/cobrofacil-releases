import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def cuenta_db(tmp_path, monkeypatch):
    from src.base_de_datos.database import db_manager
    from src.clientes_fiado.oficina.barrial import mantenimiento
    from src.clientes_fiado.oficina.huella import eventos, tabla

    ruta = tmp_path / "cuenta_test.db"
    conn = sqlite3.connect(ruta)
    conn.executescript(
        """
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            dni TEXT,
            deuda_actual REAL NOT NULL DEFAULT 0,
            limite_credito REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE cuenta_corriente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            tipo TEXT NOT NULL,
            monto REAL NOT NULL,
            saldo_resultante REAL NOT NULL,
            descripcion TEXT,
            medio_pago TEXT,
            perfil TEXT,
            registrado_por TEXT,
            venta_id INTEGER
        );
        CREATE TABLE ventas (
            id INTEGER PRIMARY KEY,
            fecha TEXT,
            total REAL NOT NULL,
            metodo_pago TEXT NOT NULL,
            cliente_nombre TEXT,
            estado TEXT NOT NULL
        );
        INSERT INTO clientes (id, nombre, deuda_actual, limite_credito)
        VALUES (1, 'Ana', 100, 500);
        INSERT INTO ventas (id, fecha, total, metodo_pago, cliente_nombre, estado)
        VALUES (7, CURRENT_TIMESTAMP, 25, 'Fiado', 'Ana', 'COMPLETADA');
        """
    )
    conn.commit()
    conn.close()

    def conectar():
        db = sqlite3.connect(ruta, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    monkeypatch.setattr(db_manager, "get_connection", conectar)
    monkeypatch.setattr(tabla, "asegurar", lambda *_a, **_kw: True)
    monkeypatch.setattr(eventos, "movimiento_en", lambda *_a, **_kw: True)
    monkeypatch.setattr(mantenimiento, "porcentaje_base", lambda: 3.0)
    monkeypatch.setattr(mantenimiento, "porcentaje_apalancamiento", lambda: 5.0)
    return ruta


def _leer(ruta, sql, params=()):
    with sqlite3.connect(ruta) as conn:
        return conn.execute(sql, params).fetchall()


def test_abono_rechaza_montos_invalidos_sin_tocar_el_saldo(cuenta_db):
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

    motor = MotorCuenta()
    for monto in (0, -1, float("nan"), float("inf"), "no es monto"):
        assert motor.abonar(1, monto, "prueba") == (False, 0.0, "")
    assert _leer(cuenta_db, "SELECT deuda_actual FROM clientes WHERE id = 1") == [(100.0,)]
    assert _leer(cuenta_db, "SELECT COUNT(*) FROM cuenta_corriente") == [(0,)]


def test_fallo_al_guardar_abono_revierte_el_saldo(cuenta_db):
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

    with sqlite3.connect(cuenta_db) as conn:
        conn.execute(
            """
            CREATE TRIGGER rechazar_abono
            BEFORE INSERT ON cuenta_corriente
            WHEN NEW.tipo = 'ABONO'
            BEGIN
                SELECT RAISE(ABORT, 'fallo de prueba');
            END
            """
        )

    assert MotorCuenta().abonar(1, 25, "prueba")[0] is False
    assert _leer(cuenta_db, "SELECT deuda_actual FROM clientes WHERE id = 1") == [(100.0,)]
    assert _leer(cuenta_db, "SELECT COUNT(*) FROM cuenta_corriente") == [(0,)]


def test_mantenimiento_automatico_es_atomico_idempotente_y_usa_saldo_actual(
    cuenta_db,
):
    from src.clientes_fiado.oficina.barrial.reglas import MARCA_MANTENIMIENTO
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

    ahora = datetime.now()
    fecha_cargo = (ahora - timedelta(days=35)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(cuenta_db) as conn:
        conn.execute(
            "INSERT INTO cuenta_corriente "
            "(cliente_id, fecha, tipo, monto, saldo_resultante, descripcion) "
            "VALUES (1, ?, 'CARGO', 100, 100, 'Ticket de prueba')",
            (fecha_cargo,),
        )

    motor = MotorCuenta()
    primero = motor.aplicar_mantenimiento_automatico(1, ahora=ahora)
    segundo = motor.aplicar_mantenimiento_automatico(1, ahora=ahora)

    assert primero["estado"] == "aplicado"
    assert primero["monto"] == 8.0
    assert primero["saldo"] == 108.0
    assert segundo["estado"] == "omitido"
    assert _leer(cuenta_db, "SELECT deuda_actual FROM clientes WHERE id = 1") == [(108.0,)]
    cargos = _leer(
        cuenta_db,
        "SELECT COUNT(*) FROM cuenta_corriente "
        "WHERE tipo = 'CARGO' AND descripcion LIKE ?",
        (f"{MARCA_MANTENIMIENTO}%",),
    )
    assert cargos == [(1,)]


def test_dos_cajas_no_aplican_mantenimiento_dos_veces(cuenta_db):
    from src.clientes_fiado.oficina.barrial.reglas import MARCA_MANTENIMIENTO
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

    ahora = datetime.now()
    fecha_cargo = (ahora - timedelta(days=35)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(cuenta_db) as conn:
        conn.execute(
            "INSERT INTO cuenta_corriente "
            "(cliente_id, fecha, tipo, monto, saldo_resultante, descripcion) "
            "VALUES (1, ?, 'CARGO', 100, 100, 'Ticket de prueba')",
            (fecha_cargo,),
        )

    def aplicar():
        return MotorCuenta().aplicar_mantenimiento_automatico(1, ahora=ahora)["estado"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        estados = list(pool.map(lambda _n: aplicar(), range(2)))

    assert sorted(estados) == ["aplicado", "omitido"]
    assert _leer(cuenta_db, "SELECT deuda_actual FROM clientes WHERE id = 1") == [(108.0,)]
    assert _leer(
        cuenta_db,
        "SELECT COUNT(*) FROM cuenta_corriente WHERE descripcion LIKE ?",
        (f"{MARCA_MANTENIMIENTO}%",),
    ) == [(1,)]


def test_error_de_base_no_carga_mantenimiento_con_deuda_cacheada(monkeypatch):
    from src.base_de_datos.database import db_manager
    from src.clientes_fiado.oficina.barrial import mantenimiento

    monkeypatch.setattr(
        "src.clientes_fiado.oficina.huella.tabla.asegurar",
        lambda *_a, **_kw: True,
    )

    def sin_conexion():
        raise sqlite3.OperationalError("base de prueba no disponible")

    monkeypatch.setattr(db_manager, "get_connection", sin_conexion)
    resultado = mantenimiento.aplicar_automatico([(1, 100000, 90)])

    assert resultado["ok"] is False
    assert resultado["aplicados"] == 0
    assert resultado["fallos"] == 1
    assert resultado["detalle"] == []


def test_cuadre_rechaza_cargar_dos_veces_el_mismo_ticket(cuenta_db, monkeypatch):
    from src.base_de_datos.repos import ventas
    from src.clientes_fiado.oficina.cuenta import cuadre

    def aplicar_fiado(cursor, datos, venta_id):
        cliente_id = datos["cliente_id"]
        total = datos["total"]
        cursor.execute(
            "UPDATE clientes SET deuda_actual = deuda_actual + ? WHERE id = ?",
            (total, cliente_id),
        )
        cursor.execute(
            "INSERT INTO cuenta_corriente "
            "(cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
            "VALUES (?, 'CARGO', ?, 125, 'Cuadre prueba', ?)",
            (cliente_id, total, venta_id),
        )

    monkeypatch.setattr(ventas, "_aplicar_fiado", aplicar_fiado)

    assert cuadre.anotar(7) == (True, "Ana")
    assert cuadre.anotar(7) == (False, "Ese ticket ya está en la cuenta")
    assert _leer(cuenta_db, "SELECT deuda_actual FROM clientes WHERE id = 1") == [(125.0,)]
    assert _leer(
        cuenta_db,
        "SELECT COUNT(*) FROM cuenta_corriente WHERE venta_id = 7 AND tipo = 'CARGO'",
    ) == [(1,)]


def test_cuadre_muestra_error_si_no_puede_consultar(monkeypatch):
    from PyQt6.QtWidgets import QApplication

    from src.admin.clientes.componentes.dialogo_cuadre import DialogoCuadre
    from src.clientes_fiado.cerebro.cerebro import cerebro

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        cerebro,
        "ventas_sin_cargo",
        lambda: (_ for _ in ()).throw(sqlite3.OperationalError("sin conexión")),
    )
    dialogo = DialogoCuadre()

    assert dialogo._error_consulta is True
    assert dialogo.btn_cargar.isEnabled() is False
    assert dialogo.btn_reintentar.isHidden() is False
    assert "no se pudo consultar" in dialogo.lbl_estado.text().lower()
    dialogo.close()
    app.processEvents()


def test_hilo_consulta_se_conserva_hasta_terminar():
    import time

    from PyQt6.QtCore import QThread
    from PyQt6.QtWidgets import QApplication

    from src.admin.clientes.consulta.hilo import (
        _HILOS_ACTIVOS,
        iniciar_hilo_seguro,
    )

    app = QApplication.instance() or QApplication([])

    class HiloPrueba(QThread):
        def run(self):
            time.sleep(0.05)

    hilo = HiloPrueba()
    iniciar_hilo_seguro(hilo)
    assert hilo in _HILOS_ACTIVOS
    assert hilo.wait(1000)
    app.processEvents()
    assert hilo not in _HILOS_ACTIVOS
