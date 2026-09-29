"""Copia de la tienda en la PC (src/jefe/nodo_portable/espejo)."""

import re
import sqlite3
from datetime import datetime, timedelta

import pymysql
import pytest

from src.jefe.nodo_portable import motor_nodo
from src.jefe.nodo_portable.espejo import copia, lector


class TiendaFalsa:
    """Imita la conexión pymysql (DictCursor, %s, SHOW TABLES) sobre SQLite."""

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.rota = False
        self.nombre = "MAESTRA-PRUEBA"
        self.db.executescript(
            """
            CREATE TABLE ventas (id INTEGER PRIMARY KEY, fecha TEXT, total REAL, estado TEXT,
                                 metodo_pago TEXT, descuento REAL DEFAULT 0, fecha_cancel TEXT, cancelado_por TEXT);
            CREATE TABLE detalles_ventas (id INTEGER PRIMARY KEY, id_venta INTEGER, id_producto TEXT,
                                          cantidad REAL, precio_unitario REAL, subtotal REAL);
            CREATE TABLE productos (id INTEGER PRIMARY KEY, nombre TEXT, precio REAL, costo REAL, stock REAL);
            CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT, deuda_actual REAL);
            CREATE TABLE movimientos_caja (id INTEGER PRIMARY KEY, fecha TEXT, tipo TEXT, monto REAL);
            CREATE TABLE gastos (id INTEGER PRIMARY KEY, fecha TEXT, categoria TEXT, descripcion TEXT, monto REAL, status TEXT);
            CREATE TABLE cuenta_corriente (id INTEGER PRIMARY KEY, cliente_id INTEGER, tipo TEXT, monto REAL, fecha TEXT);
            CREATE TABLE mp_pagos (payment_id TEXT PRIMARY KEY, venta_id INTEGER, monto REAL);
            CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre TEXT, rol TEXT);
            CREATE TABLE configuracion (clave TEXT PRIMARY KEY, valor TEXT);
            CREATE TABLE carteleria_media (nombre_archivo TEXT PRIMARY KEY, imagen_blob BLOB);
            CREATE TABLE terminales_activos (caja_id INTEGER PRIMARY KEY, visto TEXT);
            """
        )
        self.blob = {"carteleria_media"}

    def cursor(self):
        return _Cursor(self)

    def close(self):
        pass


class _Cursor:
    def __init__(self, tienda):
        self.t = tienda
        self.filas = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        if self.t.rota:
            raise pymysql.err.InternalError(1877, "Table punpro_db/ventas is corrupted.")
        if sql.startswith("SELECT @@hostname"):
            self.filas = [{"h": self.t.nombre}]
            return
        if "information_schema" in sql:
            nombres = [r[0] for r in self.t.db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            if "KEY_COLUMN_USAGE" in sql:
                self.filas = [
                    {"t": n, "c": col[1]}
                    for n in nombres
                    for col in self.t.db.execute(f'PRAGMA table_info("{n}")')
                    if col[5]
                ]
            elif "COLUMNS" in sql:
                self.filas = [{"t": n} for n in nombres if n in self.t.blob]
            else:
                self.filas = [{"t": n} for n in nombres]
            return
        m = re.match(r"SHOW TABLES LIKE '(\w+)'", sql)
        if m:
            sql, params = "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (m.group(1),)
        try:
            cur = self.t.db.execute(sql.replace("%s", "?"), params)
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                raise pymysql.err.ProgrammingError(1146, str(e))
            raise
        self.filas = [dict(r) for r in cur.fetchall()]

    def fetchall(self):
        return self.filas


def _hoy(h="10:00:00"):
    return f"{datetime.now():%Y-%m-%d} {h}"


@pytest.fixture
def tienda(tmp_path, monkeypatch):
    monkeypatch.setattr(copia, "carpeta", lambda: str(tmp_path / "espejo"))
    monkeypatch.setattr(copia, "_salud", {"hasta": 0.0, "rota": ""})
    t = TiendaFalsa()
    t.db.executemany(
        "INSERT INTO ventas (id, fecha, total, estado, metodo_pago) VALUES (?,?,?,?,?)",
        [(1, "2026-08-01 10:00:00", 100, "CERRADA", "Efectivo"), (2, _hoy(), 250, "COMPLETADA", "QR")],
    )
    t.db.execute("INSERT INTO detalles_ventas VALUES (1, 2, 'A1', 2, 125, 250)")
    t.db.execute("INSERT INTO productos VALUES (1, 'Pan', 125, 80, 10)")
    t.db.execute("INSERT INTO clientes VALUES (1, 'Ana', 500)")
    t.db.execute("INSERT INTO gastos VALUES (1, ?, 'Mercadería / Stock', 'Proveedor: Frigorífico', 1000, 'Pendiente')", (_hoy(),))
    t.db.execute("INSERT INTO cuenta_corriente VALUES (1, 1, 'ABONO', 30, ?)", (_hoy(),))
    t.db.execute("INSERT INTO mp_pagos VALUES ('987654321', 2, 250)")
    t.db.execute("INSERT INTO usuarios VALUES (1, 'jefe', 'ADMIN')")
    t.db.execute("INSERT INTO configuracion VALUES ('nombre_negocio', 'Carniceria')")
    t.db.execute("INSERT INTO carteleria_media VALUES ('oferta.png', ?)", (b"\x89PNG",))
    t.db.execute("INSERT INTO terminales_activos VALUES (1, 'ahora')")
    t.db.commit()
    monkeypatch.setattr(copia, "_conectar_tienda", lambda: t)
    return t


def _sin_red(monkeypatch):
    monkeypatch.setattr(lector, "_hay_tienda", lambda: False)
    monkeypatch.setattr(lector, "_ruta_lectura", lambda: copia.ruta())


def test_copia_entera_y_lectura_sin_red(tienda, monkeypatch):
    res = copia.refrescar()
    assert res["estado"] == "ok" and res["completo"]
    assert res["ventas"] == 2 and res["cuenta_corriente"] == 1

    _sin_red(monkeypatch)
    from src.jefe.vitrina import metricas

    assert metricas.tickets() == (1, 250.0)
    assert metricas.pagos_clientes() == 30.0
    assert metricas.deuda_clientes() == 500.0
    assert metricas.inventario_costo() == 800.0
    assert metricas.digitales() == (0, 1)
    assert "Sin red" in lector.leyenda()


def test_copia_trae_toda_la_tienda(tienda):
    copia.refrescar()
    conn = sqlite3.connect(copia.ruta())
    assert conn.execute("SELECT nombre FROM usuarios").fetchone()[0] == "jefe"
    assert conn.execute("SELECT valor FROM configuracion WHERE clave='nombre_negocio'").fetchone()[0] == "Carniceria"
    assert conn.execute("SELECT imagen_blob FROM carteleria_media").fetchone()[0] == b"\x89PNG"
    assert not conn.execute("SELECT name FROM sqlite_master WHERE name='terminales_activos'").fetchone()
    conn.close()
    assert copia.meta()["completa"] == "1"

    tienda.db.execute("INSERT INTO carteleria_media VALUES ('nueva.png', x'00')")
    tienda.db.execute("UPDATE configuracion SET valor='Carniceria Don Luis'")
    tienda.db.commit()
    res = copia.refrescar()
    assert not res["completo"] and res["carteleria_media"] == 0 and res["configuracion"] == 1
    conn = sqlite3.connect(copia.ruta())
    assert conn.execute("SELECT valor FROM configuracion").fetchone()[0] == "Carniceria Don Luis"
    conn.close()


def test_con_tienda_lee_en_vivo(tienda, monkeypatch):
    copia.refrescar()
    monkeypatch.setattr(lector, "_hay_tienda", lambda: True)
    assert lector.en_copia() == ""
    assert lector.leyenda() == ""


def test_incremental_trae_nuevas_y_cancelaciones(tienda, monkeypatch):
    copia.refrescar()
    tienda.db.execute("INSERT INTO ventas (id, fecha, total, estado) VALUES (3, ?, 40, 'COMPLETADA')", (_hoy("11:00:00"),))
    tienda.db.execute("UPDATE ventas SET estado='CANCELADA', fecha_cancel=?, cancelado_por='jefe' WHERE id=2", (_hoy("12:00:00"),))
    tienda.db.commit()
    res = copia.refrescar()
    assert not res["completo"]

    _sin_red(monkeypatch)
    from src.jefe.vitrina import metricas

    assert metricas.tickets() == (1, 40.0)
    c = metricas.cancelaciones()
    assert c["cant"] == 1 and c["usuario"] == "jefe"


def test_copia_actualiza_estado_de_gasto_viejo(tienda, monkeypatch):
    monkeypatch.setattr(copia, "GRANDE", 0)
    copia.refrescar()
    tienda.db.execute("UPDATE gastos SET status='Pagado' WHERE id=1")
    tienda.db.commit()

    res = copia.refrescar()

    assert not res["completo"]
    assert res["gastos"] == 1
    conn = sqlite3.connect(copia.ruta())
    assert conn.execute("SELECT status FROM gastos WHERE id=1").fetchone()[0] == "Pagado"
    conn.close()


def test_tienda_rota_no_toca_la_copia(tienda):
    copia.refrescar()
    antes = copia.meta()["ultima_copia"]
    tienda.rota = True
    res = copia.refrescar()
    assert res["estado"] == "error"
    assert copia.meta()["ultima_copia"] == antes
    conn = sqlite3.connect(copia.ruta())
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 2
    conn.close()


def test_maestra_conectada_pero_danada_lee_la_copia(tienda, monkeypatch):
    copia.refrescar()
    monkeypatch.setattr(lector, "_hay_tienda", lambda: True)
    monkeypatch.setattr(lector, "_ruta_lectura", lambda: copia.ruta())
    tienda.rota = True
    monkeypatch.setattr(copia, "_salud", {"hasta": 0.0, "rota": ""})

    assert lector.en_copia() == copia.ruta()
    assert "tablas dañadas" in lector.leyenda()
    from src.jefe.vitrina import metricas

    assert metricas.tickets() == (1, 250.0)

    tienda.rota = False
    monkeypatch.setattr(copia, "_salud", {"hasta": 0.0, "rota": ""})
    assert lector.en_copia() == ""


def test_tienda_que_vuelve_atras_guarda_la_copia_vieja(tienda, tmp_path):
    copia.refrescar()
    tienda.db.execute("DELETE FROM ventas WHERE id = 2")
    tienda.db.commit()
    res = copia.refrescar()
    assert res["estado"] == "ok"
    viejas = list((tmp_path / "espejo").glob("espejo_tienda_hasta_*.db"))
    assert len(viejas) == 1
    conn = sqlite3.connect(viejas[0])
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 2
    conn.close()


def test_otra_maestra_no_mezcla_copias(tienda, tmp_path):
    copia.refrescar()
    tienda.nombre = "MAESTRA-NEGOCIO"
    tienda.db.execute("DELETE FROM ventas")
    tienda.db.execute("INSERT INTO ventas (id, fecha, total, estado) VALUES (900, ?, 5, 'COMPLETADA')", (_hoy(),))
    tienda.db.commit()
    res = copia.refrescar()
    assert res["estado"] == "ok" and res["completo"]
    assert len(list((tmp_path / "espejo").glob("espejo_tienda_hasta_*.db"))) == 1
    conn = sqlite3.connect(copia.ruta())
    assert [r[0] for r in conn.execute("SELECT id FROM ventas")] == [900]
    conn.close()
    assert copia.meta()["servidor"] == "MAESTRA-NEGOCIO"


def test_sin_tienda_no_crea_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(copia, "carpeta", lambda: str(tmp_path / "espejo"))
    monkeypatch.setattr(copia, "_conectar_tienda", lambda: None)
    assert copia.refrescar()["estado"] == "sin_tienda"
    assert not copia.existe()


def test_pendrive_es_copia_y_guarda_eventos_sueltos(tienda, tmp_path, monkeypatch):
    from src.clientes_fiado.oficina.huella import absorber, tabla
    from src.admin.mercadopago.historial import archivo
    from src.cajero.paso6_cobro.vinculo_mp import libro

    monkeypatch.setattr(motor_nodo, "_hay_tienda", lambda: False)
    monkeypatch.setattr(absorber, "llevar_al_nodo", lambda *a, **k: 0)
    monkeypatch.setattr(archivo, "RUTA", str(tmp_path / "local" / "reportes" / "mercado_pago_sync.csv"))
    monkeypatch.setattr(libro, "RUTA", str(tmp_path / "local" / "reportes" / "mp_vinculos.json"))
    copia.refrescar()

    root = tmp_path / "USB" / "CobroFacil_Nodo"
    root.mkdir(parents=True)
    neg = root / "nodo_negocio.db"
    conn = sqlite3.connect(neg)
    conn.execute(tabla.DDL_EVENTOS)
    conn.execute(
        "INSERT INTO clientes_auditoria (evento, fecha, accion, cliente_uid, nombre, pc, base) "
        "VALUES ('CASA-1-20260926-0001', '2026-09-26 23:00:00', 'ALTA', 'CASA-1-x', 'Beto', 'CASA-1', 'LOCAL')"
    )
    conn.commit()
    conn.close()

    motor_nodo._llevar_al_pendrive(str(root), None)

    conn = sqlite3.connect(neg)
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM clientes_auditoria WHERE base='LOCAL'").fetchone()[0] == 1
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    conn.close()


def test_nodo_actualiza_deudas_aplicadas_antes_de_volcar(tienda, tmp_path, monkeypatch):
    from src.clientes_fiado.oficina.huella import absorber
    from src.admin.mercadopago.historial import archivo
    from src.cajero.paso6_cobro.vinculo_mp import libro

    copia.refrescar()
    monkeypatch.setattr(archivo, "RUTA", str(tmp_path / "local" / "reportes" / "mercado_pago_sync.csv"))
    monkeypatch.setattr(libro, "RUTA", str(tmp_path / "local" / "reportes" / "mp_vinculos.json"))
    root = tmp_path / "USB" / "CobroFacil_Nodo"
    root.mkdir(parents=True)
    nodo_db = root / "nodo_negocio.db"
    copia.volcar_a(str(nodo_db))

    def aplicar_movimiento_pendiente(_path):
        tienda.db.execute("UPDATE clientes SET deuda_actual=650 WHERE id=1")
        tienda.db.execute(
            "INSERT INTO cuenta_corriente VALUES (2, 1, 'CARGO', 150, ?)",
            (_hoy("11:00:00"),),
        )
        tienda.db.commit()
        return {"aplicado": 1, "repetido": 0, "pendiente": 0, "error": 0}

    monkeypatch.setattr(motor_nodo, "_chupar_antes", aplicar_movimiento_pendiente)
    monkeypatch.setattr(absorber, "llevar_al_nodo", lambda *a, **k: 0)

    motor_nodo._llevar_al_pendrive(str(root), None)

    conn = sqlite3.connect(nodo_db)
    assert conn.execute("SELECT deuda_actual FROM clientes WHERE id=1").fetchone()[0] == 650
    assert conn.execute("SELECT monto FROM cuenta_corriente WHERE id=2").fetchone()[0] == 150
    conn.close()


def test_nodo_refresca_copia_si_movimiento_ya_se_habia_aplicado(tienda, tmp_path, monkeypatch):
    from src.clientes_fiado.oficina.huella import absorber
    from src.admin.mercadopago.historial import archivo
    from src.cajero.paso6_cobro.vinculo_mp import libro

    copia.refrescar()
    monkeypatch.setattr(archivo, "RUTA", str(tmp_path / "local" / "reportes" / "mercado_pago_sync.csv"))
    monkeypatch.setattr(libro, "RUTA", str(tmp_path / "local" / "reportes" / "mp_vinculos.json"))
    root = tmp_path / "USB" / "CobroFacil_Nodo"
    root.mkdir(parents=True)
    nodo_db = root / "nodo_negocio.db"
    copia.volcar_a(str(nodo_db))

    def repetir_movimiento(_path):
        tienda.db.execute("UPDATE clientes SET deuda_actual=725 WHERE id=1")
        tienda.db.commit()
        return {"aplicado": 0, "repetido": 1, "pendiente": 0, "error": 0}

    monkeypatch.setattr(motor_nodo, "_chupar_antes", repetir_movimiento)
    monkeypatch.setattr(absorber, "llevar_al_nodo", lambda *a, **k: 0)

    motor_nodo._llevar_al_pendrive(str(root), None)

    conn = sqlite3.connect(nodo_db)
    assert conn.execute("SELECT deuda_actual FROM clientes WHERE id=1").fetchone()[0] == 725
    conn.close()


def test_copia_se_puede_leer_desde_pendrive(tienda, tmp_path, monkeypatch):
    copia.refrescar()
    destino = tmp_path / "nodo_negocio.db"
    copia.volcar_a(str(destino))
    monkeypatch.setattr(lector, "_hay_tienda", lambda: False)
    monkeypatch.setattr(lector, "_ruta_lectura", lambda: str(destino))
    assert lector.fuente().execute_query("SELECT COUNT(*) AS n FROM ventas")[0]["n"] == 2
    assert "pendrive" in lector.leyenda()
    assert lector.fuente().execute_query("SELECT * FROM tabla_que_no_existe") == []
